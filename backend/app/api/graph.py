from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.engines.graph_engine import transaction_graph
router=APIRouter(prefix="/graph",tags=["financial event graph"])
@router.get("/transactions/{transaction_id}")
def get_graph(transaction_id:str,limit:int=Query(default=100,ge=1,le=500),db:Session=Depends(get_db)):
    graph=transaction_graph(db,transaction_id,limit)
    if graph is None: raise HTTPException(404,"Transaction not found")
    return graph
