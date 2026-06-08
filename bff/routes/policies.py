from fastapi import APIRouter
from models import PolicyState, PolicyUpdate

router = APIRouter()

# In-memory demo state — single shared instance per process
_state = PolicyState()


@router.get("/api/policies", response_model=PolicyState)
def get_policies() -> PolicyState:
    return _state


@router.post("/api/policies", response_model=PolicyState)
def update_policies(update: PolicyUpdate) -> PolicyState:
    if update.rbac is not None:
        _state.rbac = update.rbac
    if update.elicitation is not None:
        _state.elicitation = update.elicitation
    if update.rate_limit is not None:
        _state.rate_limit = update.rate_limit
    if update.guardrails is not None:
        _state.guardrails = update.guardrails
    return _state
