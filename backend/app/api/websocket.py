import hmac, os
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.websocket.manager import event_hub
router=APIRouter()
@router.websocket("/ws/transactions")
async def transaction_stream(websocket: WebSocket):
    if os.getenv("AUTH_REQUIRED","false").lower()=="true":
        candidates=[value for value in (os.getenv("API_KEY_ANALYST",""),os.getenv("API_KEY_OPERATOR","")) if value]
        offered=websocket.scope.get("subprotocols",[])
        bearer=next((item[7:] for item in offered if item.startswith("bearer.")),"")
        if not any(hmac.compare_digest(bearer,key) for key in candidates):
            await websocket.close(code=1008,reason="Valid bearer subprotocol required")
            return
        await websocket.accept(subprotocol="finintel.events.v1")
    else:
        await websocket.accept()
    queue=event_hub.subscribe()
    try:
        await websocket.send_json({"event_type":"CONNECTED","environment":"SYNTHETIC"})
        while True: await websocket.send_json(await queue.get())
    except WebSocketDisconnect: pass
    finally: event_hub.unsubscribe(queue)
