from .state import CatState


class CatBehavior:
    def __init__(self, initial_state: CatState = CatState.IDLE, on_state_change=None):
        self._state = initial_state
        self._on_state_change = on_state_change

    @property
    def state(self) -> CatState:
        return self._state

    def request_state(self, new_state: CatState) -> bool:
        if not isinstance(new_state, CatState):
            return False
        if new_state == self._state:
            return False
        if not self._is_transition_allowed(self._state, new_state):
            return False
        old_state = self._state
        self._state = new_state
        if callable(self._on_state_change):
            self._on_state_change(new_state, old_state)
        return True

    def _is_transition_allowed(self, current: CatState, new: CatState) -> bool:
        # SLEEP can wake directly to IDLE or through WAKE
        if current == CatState.SLEEP:
            return new in (CatState.WAKE, CatState.IDLE)
        # WAKE can return to IDLE
        if current == CatState.WAKE:
            return new == CatState.IDLE
        # IDLE allows broad transitions
        if current == CatState.IDLE:
            return True
        # Temporary interaction states can return to IDLE or previous state
        if current in (CatState.DRAGGED, CatState.DRAG, CatState.PET):
            return True
        # Default: allow transition
        return True
