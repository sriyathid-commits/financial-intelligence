from enum import StrEnum

class TransactionStatus(StrEnum):
    INITIATED = "INITIATED"
    AUTHORIZED = "AUTHORIZED"
    PROCESSING = "PROCESSING"
    DEBITED = "DEBITED"
    SUCCESS = "SUCCESS"
    UNKNOWN = "UNKNOWN"
    RECONCILING = "RECONCILING"
    SETTLED = "SETTLED"
    REVERSED = "REVERSED"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"

TRANSITIONS = {
    TransactionStatus.INITIATED: {TransactionStatus.AUTHORIZED, TransactionStatus.FAILED},
    TransactionStatus.AUTHORIZED: {TransactionStatus.PROCESSING, TransactionStatus.FAILED},
    TransactionStatus.PROCESSING: {TransactionStatus.DEBITED, TransactionStatus.FAILED, TransactionStatus.UNKNOWN},
    TransactionStatus.DEBITED: {TransactionStatus.SUCCESS, TransactionStatus.UNKNOWN},
    TransactionStatus.UNKNOWN: {TransactionStatus.RECONCILING},
    TransactionStatus.RECONCILING: {TransactionStatus.SETTLED, TransactionStatus.REVERSED},
    TransactionStatus.SUCCESS: {TransactionStatus.REFUNDED},
}

def validate_transition(current: TransactionStatus | str, target: TransactionStatus | str) -> None:
    current, target = TransactionStatus(current), TransactionStatus(target)
    if target not in TRANSITIONS.get(current, set()):
        raise ValueError(f"Invalid transaction transition: {current.value} -> {target.value}")
