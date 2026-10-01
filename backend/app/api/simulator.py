from fastapi import APIRouter
from pydantic import BaseModel, Field
from app.simulator.event_generator import simulator
router=APIRouter(prefix="/simulator",tags=["simulator"])
class StartRequest(BaseModel): interval_seconds: float=Field(default=2.0,ge=0.5,le=60.0)
@router.post("/start")
def start(payload: StartRequest):
    started=simulator.start(payload.interval_seconds)
    return {**simulator.status(),"started":started}
@router.post("/stop")
def stop():
    simulator.stop()
    return {**simulator.status(),"stopped":True}
@router.get("/status")
def status(): return simulator.status()
