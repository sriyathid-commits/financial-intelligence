from decimal import Decimal

def transaction_features(tx, context: dict) -> dict[str, float]:
    amount=Decimal(tx.amount)
    evidence=context["evidence"][0]
    ratio=Decimal(evidence["current_vs_average_ratio"]) if evidence.get("current_vs_average_ratio") else Decimal(0)
    mandate=context.get("mandate",{})
    expected=Decimal(mandate["expected_amount"]) if mandate.get("expected_amount") else Decimal(0)
    deviation=(abs(amount-expected)/expected*Decimal(100)) if expected else Decimal(0)
    return {
        "amount":float(amount),
        "user_history_count":float(context["user"]["historical_transaction_count"]),
        "amount_to_user_average_ratio":float(ratio),
        "user_transactions_previous_24h":float(context["user"]["frequency_last_24h"]),
        "merchant_seen_before":float(context["merchant"]["seen_before_by_user"]),
        "device_known":float(context["device"]["known_device"]),
        "beneficiary_known":float(context["beneficiary"]["known_beneficiary"]),
        "mandate_amount_deviation_percent":float(deviation),
        "is_unknown_state":float(tx.status=="UNKNOWN"),
        "is_reconciling_state":float(tx.status=="RECONCILING"),
    }
