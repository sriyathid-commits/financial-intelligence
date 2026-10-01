import asyncio, json, logging, threading, uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, func
from app.db.database import SessionLocal
from sqlalchemy.orm import Session
from app.models.transaction import Transaction

logger=logging.getLogger(__name__)
class EventHub:
    def __init__(self):
        self.loop=None
        self.subscribers=set()
        self.redis=None
        self.redis_pubsub=None
        self.instance_id=str(uuid.uuid4())
        self.redis_thread=None
        self.redis_stop=threading.Event()
    def start(self):
        self.loop=asyncio.get_running_loop()
        try:
            import redis
            from app.core.config import REDIS_URL
            self.redis=redis.Redis.from_url(REDIS_URL,socket_connect_timeout=0.25,socket_timeout=0.25)
            self.redis.ping()
            self.redis_pubsub=self.redis.pubsub()
            self.redis_pubsub.subscribe("financial.transaction.events")
            self.redis_stop.clear()
            self.redis_thread=threading.Thread(target=self._listen_redis,name="redis-event-relay",daemon=True)
            self.redis_thread.start()
        except Exception:
            self.redis=None
            logger.info("Redis unavailable; using in-process WebSocket delivery")
    def _listen_redis(self):
        try:
            for message in self.redis_pubsub.listen():
                if self.redis_stop.is_set(): break
                if message.get("type") != "message": continue
                payload=json.loads(message["data"])
                if payload.pop("_origin",None) == self.instance_id: continue
                if self.loop and not self.loop.is_closed(): self.loop.call_soon_threadsafe(self._deliver,payload)
        except Exception:
            if not self.redis_stop.is_set(): logger.warning("Redis subscription ended; local WebSocket delivery remains active")
    def stop(self):
        self.redis_stop.set()
        if self.redis_pubsub:
            try: self.redis_pubsub.close()
            except Exception: pass
        if self.redis_thread and self.redis_thread.is_alive(): self.redis_thread.join(timeout=1)
    def subscribe(self):
        queue=asyncio.Queue(maxsize=100)
        self.subscribers.add(queue)
        return queue
    def unsubscribe(self,queue): self.subscribers.discard(queue)
    def _deliver(self,payload):
        for queue in tuple(self.subscribers):
            if queue.full():
                try: queue.get_nowait()
                except asyncio.QueueEmpty: pass
            queue.put_nowait(payload)
    def publish(self,payload:dict):
        loop=self.loop
        if loop and not loop.is_closed(): loop.call_soon_threadsafe(self._deliver,payload)
        if self.redis:
            try: self.redis.publish("financial.transaction.events",json.dumps({**payload,"_origin":self.instance_id},default=str))
            except Exception:
                logger.warning("Redis publish failed; local delivery remains active")
                self.redis=None
    def publish_transaction(self,tx,event_type="TRANSACTION_UPDATED"):
        self.publish({"event_type":event_type,"transaction_id":tx.transaction_id,"status":tx.status,"amount":str(tx.amount),"currency":tx.currency,"merchant_id":tx.merchant_id,"environment":"SYNTHETIC","occurred_at":tx.occurred_at.isoformat()})

event_hub=EventHub()

def dashboard_summary(db: Session):
    counts=dict(db.execute(select(Transaction.status,func.count()).group_by(Transaction.status)).all())
    start=datetime.combine(datetime.now(timezone.utc).date(),datetime.min.time(),tzinfo=timezone.utc)
    end=start+timedelta(days=1)
    today_count=db.scalar(select(func.count()).select_from(Transaction).where(Transaction.created_at>=start,Transaction.created_at<end)) or 0
    total=db.scalar(select(func.count()).select_from(Transaction)) or 0
    return {"environment":"SYNTHETIC","transactions_today":today_count,"successful":counts.get("SUCCESS",0)+counts.get("SETTLED",0),"failed":counts.get("FAILED",0),"unknown":counts.get("UNKNOWN",0),"under_reconciliation":counts.get("RECONCILING",0),"total_transactions":total,"generated_at":datetime.now(timezone.utc).isoformat()}
