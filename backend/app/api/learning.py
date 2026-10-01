from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.outcome import OutcomeFeedback
router=APIRouter(prefix="/learning",tags=["outcome learning loop"])
@router.get("/summary")
def learning_summary(db:Session=Depends(get_db)):
    rows=db.execute(select(OutcomeFeedback.outcome_label,OutcomeFeedback.verification_status,func.count()).group_by(OutcomeFeedback.outcome_label,OutcomeFeedback.verification_status)).all()
    verified=list(db.scalars(select(OutcomeFeedback).where(OutcomeFeedback.verification_status=="VERIFIED")))
    labels={"CONFIRMED_UNAUTHORIZED":1,"CONFIRMED_LEGITIMATE":0}
    confusion={"true_positive":0,"false_positive":0,"true_negative":0,"false_negative":0}
    evaluated=0
    for item in verified:
        truth=labels.get(item.outcome_label)
        if truth is None: continue
        prediction=int(item.risk_snapshot.get("overall_score",0)>=70)
        evaluated+=1
        if prediction and truth: confusion["true_positive"]+=1
        elif prediction and not truth: confusion["false_positive"]+=1
        elif not prediction and not truth: confusion["true_negative"]+=1
        else: confusion["false_negative"]+=1
    return {"environment":"SYNTHETIC","feedback_counts":[{"label":label,"verification_status":status,"count":count} for label,status,count in rows],"verified_evaluations":{"sample_size":evaluated,"demo_high_risk_threshold":70,"confusion_counts":confusion if evaluated else None},"model_training_enabled":False,"note":"Only separately verified legitimate/unauthorized labels are compared with the stored risk snapshot. This reports an illustrative retrospective count; it does not validate a model or train/update one."}
