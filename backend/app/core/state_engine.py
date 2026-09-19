from typing import Tuple, Optional
from app.schemas.state import SecurityState, ConnectivityState, PowerState
from app.core.exceptions import InvalidStateTransitionError


# Allowed Security State Transitions:
# NORMAL -> PROTECTED, STOLEN
# PROTECTED -> NORMAL, STOLEN
# STOLEN -> RECOVERY, NORMAL (Requires owner/admin authorization)
# RECOVERY -> NORMAL, STOLEN (Requires owner/admin authorization)
VALID_SECURITY_TRANSITIONS = {
    SecurityState.NORMAL: {SecurityState.PROTECTED, SecurityState.STOLEN},
    SecurityState.PROTECTED: {SecurityState.NORMAL, SecurityState.STOLEN},
    SecurityState.STOLEN: {SecurityState.RECOVERY, SecurityState.NORMAL},
    SecurityState.RECOVERY: {SecurityState.NORMAL, SecurityState.STOLEN},
}


def validate_security_state_transition(
    current: SecurityState,
    target: SecurityState,
    is_authorized_actor: bool = True
) -> bool:
    """
    Validates whether transitioning from `current` to `target` is allowable under policy.
    Raises InvalidStateTransitionError if illegal.
    """
    if current == target:
        return True

    allowed = VALID_SECURITY_TRANSITIONS.get(current, set())
    if target not in allowed:
        raise InvalidStateTransitionError(
            f"Illegal security state transition: {current.value} -> {target.value}. Allowed transitions: {[s.value for s in allowed]}"
        )

    # Returning to NORMAL from STOLEN/RECOVERY requires explicit authorization check
    if current in {SecurityState.STOLEN, SecurityState.RECOVERY} and target == SecurityState.NORMAL:
        if not is_authorized_actor:
            raise InvalidStateTransitionError("Transition from STOLEN/RECOVERY back to NORMAL requires owner/admin authorization.")

    return True


def determine_power_state_from_battery(battery_level: Optional[int], is_charging: bool = False) -> PowerState:
    """
    Derives PowerState dimension dynamically based on battery level percentage.
    """
    if is_charging or battery_level is None:
        return PowerState.NORMAL
    if battery_level < 10:
        return PowerState.CRITICAL
    if battery_level <= 20:
        return PowerState.LOW
    return PowerState.NORMAL
