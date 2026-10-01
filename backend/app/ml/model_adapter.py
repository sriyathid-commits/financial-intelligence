from dataclasses import dataclass
from typing import Callable, Protocol

class RiskModel(Protocol):
    def predict(self, features: dict[str,float]) -> float: ...
    def explain(self, features: dict[str,float]) -> list[dict]: ...

@dataclass
class ModelAssessment:
    status: str
    score: float | None
    model_name: str | None
    explanation_type: str
    explanation: list[dict]

class ScikitLearnRiskModel:
    """Adapter for an already-trained sklearn-compatible estimator; never fits on synthetic events."""
    def __init__(self, estimator, model_name: str="configured-risk-model", explainer: Callable | None=None):
        if not callable(getattr(estimator,"predict_proba",None)):
            raise TypeError("Estimator must expose predict_proba")
        self.estimator=estimator
        self.model_name=model_name
        self.explainer=explainer
        classes=list(getattr(estimator,"classes_",[0,1]))
        self.positive_index=classes.index(1) if 1 in classes else len(classes)-1
    def predict(self,features:dict[str,float])->float:
        ordered=list(features.values())
        probabilities=self.estimator.predict_proba([ordered])[0]
        score=float(probabilities[self.positive_index])
        if not 0.0 <= score <= 1.0: raise ValueError("Model probability must be between zero and one")
        return score
    def explain(self,features:dict[str,float])->list[dict]:
        if self.explainer is None: return []
        raw=self.explainer(features)
        return [{"feature":str(row["feature"]),"impact":float(row["impact"]),"direction":"INCREASES" if float(row["impact"])>0 else "DECREASES" if float(row["impact"])<0 else "NEUTRAL"} for row in raw]

class ModelAdapter:
    def __init__(self,model:RiskModel|None=None): self.model=model
    def assess(self,features:dict[str,float])->dict:
        if self.model is None:
            return ModelAssessment("NOT_CONFIGURED",None,None,"NOT_AVAILABLE",[]).__dict__
        explanation=self.model.explain(features)
        return ModelAssessment("AVAILABLE",self.model.predict(features),getattr(self.model,"model_name",type(self.model).__name__),"MODEL_EXPLAINER" if explanation else "NOT_AVAILABLE",explanation).__dict__

risk_model=ModelAdapter()
