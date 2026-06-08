import { useRef, KeyboardEvent } from "react";

interface Props {
  onSend: (text: string) => void;
  disabled: boolean;
}

export default function ChatInput({ onSend, disabled }: Props) {
  const ref = useRef<HTMLTextAreaElement>(null);

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  }

  function submit() {
    const text = ref.current?.value.trim();
    if (!text || disabled) return;
    onSend(text);
    if (ref.current) ref.current.value = "";
  }

  return (
    <>
      <textarea
        ref={ref}
        className="chat-input"
        placeholder="Ask about your portfolio, request a trade…"
        rows={1}
        onKeyDown={handleKeyDown}
        disabled={disabled}
        aria-label="Chat input"
      />
      <button className="btn-send" onClick={submit} disabled={disabled} aria-label="Send">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <path
            d="M2 8h12M10 4l4 4-4 4"
            stroke="#fff"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </button>
    </>
  );
}
