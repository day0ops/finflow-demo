"""OpenAI-compatible BaseLlm adapter for google-adk — no LiteLLM required.

openai is already in the bundle via kagent-adk's dependency, so no extra
package cost. This keeps the Lambda zip well under the 750 MB AgentCore limit.
"""

import json
import logging
import os
from functools import cached_property
from typing import AsyncGenerator, Optional

_log = logging.getLogger(__name__)

from google.adk.models import BaseLlm
from google.adk.models.llm_response import LlmResponse
from google.genai import types
from pydantic import Field


def _openai_role(adk_role: Optional[str]) -> str:
    return "assistant" if adk_role in ("model", "assistant") else "user"


def _schema_to_dict(schema) -> dict:
    """Recursively convert google.genai Schema → plain dict (renames type_ → type, lowercases type values)."""
    if schema is None:
        return {"type": "object", "properties": {}}
    if isinstance(schema, dict):
        result = {}
        for k, v in schema.items():
            key = "type" if k == "type_" else k
            if key == "type" and isinstance(v, str):
                result[key] = v.lower()
            elif isinstance(v, dict):
                result[key] = _schema_to_dict(v)
            else:
                result[key] = v
        return {k: v for k, v in result.items() if v is not None}
    if hasattr(schema, "model_dump"):
        return _schema_to_dict(schema.model_dump(exclude_none=True, mode="json"))
    return {}


def _contents_to_messages(contents, system_text: Optional[str] = None) -> list:
    msgs = []
    if system_text:
        msgs.append({"role": "system", "content": system_text})
    for c in (contents or []):
        parts = c.parts or []
        tool_calls, tool_results, texts = [], [], []
        for p in parts:
            fc = getattr(p, "function_call", None)
            fr = getattr(p, "function_response", None)
            if fc:
                tool_calls.append({
                    "id": getattr(fc, "id", None) or f"call_{fc.name}",
                    "type": "function",
                    "function": {
                        "name": fc.name,
                        "arguments": json.dumps(dict(fc.args) if fc.args else {}),
                    },
                })
            elif fr:
                tool_results.append({
                    "role": "tool",
                    "tool_call_id": getattr(fr, "id", None) or f"call_{fr.name}",
                    "content": json.dumps(fr.response) if fr.response else "",
                })
            elif getattr(p, "text", None):
                texts.append(p.text)
        if tool_results:
            msgs.extend(tool_results)
        elif tool_calls:
            msg: dict = {"role": "assistant", "tool_calls": tool_calls}
            if texts:
                msg["content"] = " ".join(texts)
            msgs.append(msg)
        else:
            msgs.append({"role": _openai_role(c.role), "content": " ".join(texts)})
    return msgs


def _tools_to_openai(config) -> Optional[list]:
    if not config:
        return None
    tools_config = getattr(config, "tools", None)
    if not tools_config:
        return None
    result = []
    for tool in tools_config:
        for fd in getattr(tool, "function_declarations", []) or []:
            result.append({
                "type": "function",
                "function": {
                    "name": fd.name,
                    "description": getattr(fd, "description", "") or "",
                    "parameters": _schema_to_dict(getattr(fd, "parameters", None)),
                },
            })
    return result or None


def _system_text(config) -> Optional[str]:
    if not config:
        return None
    si = getattr(config, "system_instruction", None)
    if not si:
        return None
    if isinstance(si, str):
        return si
    if hasattr(si, "parts"):
        texts = [p.text for p in (si.parts or []) if getattr(p, "text", None)]
        return "\n".join(texts) if texts else None
    return None


class OpenAICompatibleLlm(BaseLlm):
    """Thin OpenAI-compatible adapter for google-adk. No LiteLLM dependency."""

    model: str
    base_url: Optional[str] = None
    api_key: Optional[str] = Field(default=None, exclude=True)
    max_tokens: int = 4096

    @classmethod
    def supported_models(cls) -> list[str]:
        return []  # direct instantiation only, not looked up by name

    @cached_property
    def _client(self):
        import openai  # in bundle via kagent-adk
        return openai.AsyncOpenAI(
            base_url=self.base_url or os.getenv("LLM_BASE_URL", "http://agentgateway.finflow.svc/v1"),
            api_key=self.api_key or os.getenv("LLM_API_KEY", "demo"),
        )

    async def generate_content_async(
        self,
        llm_request,
        stream: bool = False,
    ) -> AsyncGenerator[LlmResponse, None]:
        config = getattr(llm_request, "config", None)
        messages = _contents_to_messages(
            getattr(llm_request, "contents", []),
            _system_text(config),
        )
        tools = _tools_to_openai(config)
        kwargs: dict = {
            "model": getattr(llm_request, "model", None) or self.model,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "stream": False,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
        _log.info("LLM request: model=%s msgs=%d tools=%s payload=%s",
                  kwargs["model"], len(messages),
                  len(kwargs.get("tools") or []),
                  json.dumps(kwargs, default=str))
        try:
            response = await self._client.chat.completions.create(**kwargs)
            choice = response.choices[0]
            msg = choice.message
            parts = []
            if getattr(msg, "tool_calls", None):
                for tc in msg.tool_calls:
                    try:
                        args = json.loads(tc.function.arguments) if tc.function.arguments else {}
                    except (json.JSONDecodeError, TypeError):
                        args = {}
                    parts.append(types.Part(
                        function_call=types.FunctionCall(
                            id=tc.id, name=tc.function.name, args=args,
                        )
                    ))
            if getattr(msg, "content", None):
                parts.append(types.Part(text=msg.content))
            yield LlmResponse(content=types.Content(role="model", parts=parts))
        except Exception as exc:
            yield LlmResponse(error_message=str(exc))
