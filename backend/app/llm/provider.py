from typing import Protocol

class LLMProvider(Protocol):
    """Provider boundary: implementations receive verified structured evidence only."""
    def summarize(self,evidence:dict)->str: ...

class UnconfiguredLLMProvider:
    def summarize(self,evidence:dict)->str:
        raise RuntimeError("No LLM provider is configured")

class EvidenceSummaryProvider:
    """Deterministic fallback; renders facts without inference or external model calls."""
    def summarize(self,evidence:dict)->str:
        tx=evidence["transaction"]
        risk=evidence["risk"]
        pieces=[f"Transaction {tx['transaction_id']} is {tx['status']} for {tx['currency']} {tx['amount']}."]
        if tx.get("merchant_id"): pieces.append(f"Recorded merchant: {tx['merchant_id']}.")
        pieces.append(f"The advisory heuristic score is {risk['overall_score']} ({risk['risk_band']}); confidence indicator {risk['confidence_percent']}%.")
        if risk["explanation"]: pieces.append("Recorded signals: " + " ".join(risk["explanation"]))
        rec=evidence["reconciliation"]
        pieces.append(f"Reconciliation status: {rec['status']}.")
        if rec.get("evidence"): pieces.append(f"Reconciliation evidence {rec['evidence'].get('type')} reference {rec['evidence'].get('reference')}.")
        pieces.append("This summary restates stored synthetic evidence; it is not an independent fraud or payment decision.")
        return " ".join(pieces)

def summarize_investigation(evidence:dict,provider:LLMProvider|None=None)->dict:
    if provider is None:
        provider=EvidenceSummaryProvider()
        provider_name="deterministic_evidence_fallback"
    else:
        provider_name=type(provider).__name__
    return {"summary":provider.summarize(evidence),"provider":provider_name,"llm_used":not isinstance(provider,EvidenceSummaryProvider),"grounding":"Transaction, rules, timeline, and reconciliation fields supplied by the platform","environment":"SYNTHETIC"}
