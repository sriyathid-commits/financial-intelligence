from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.websocket.manager import dashboard_summary
router=APIRouter(prefix="/dashboard",tags=["dashboard"])
@router.get("/summary")
def summary(db: Session=Depends(get_db)): return dashboard_summary(db)
