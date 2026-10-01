import random, threading, time
from decimal import Decimal
from datetime import datetime, timezone
from app.db.database import SessionLocal
from app.schemas.transactions import TransactionCreate
from app.services.transaction_service import create_transaction, transition_transaction
from app.engines.state_engine import TransactionStatus
from app.websocket.manager import event_hub

AMOUNTS=[Decimal(x) for x in ("49.00","99.00","199.00","499.00","649.00","999.00","2000.00","5000.00","49999.00")]
MERCHANTS=[("fictional-streamco","Fictional StreamCo"),("fictional-market","Fictional Market"),("fictional-utilities","Fictional Utilities")]
class Simulator:
    def __init__(self): self.stop_event=threading.Event(); self.thread=None; self.generated=0; self.interval=2.0
    @property
    def running(self): return bool(self.thread and self.thread.is_alive())
    def start(self,interval_seconds=2.0):
        self.interval=interval_seconds
        if self.running: return False
        self.stop_event.clear()
        self.thread=threading.Thread(target=self._run,name="synthetic-event-generator",daemon=True)
        self.thread.start()
        return True
    def stop(self):
        self.stop_event.set()
        if self.thread and self.thread.is_alive(): self.thread.join(timeout=3)
    def status(self): return {"running":self.running,"generated":self.generated,"environment":"SYNTHETIC","interval_seconds":self.interval}
    def _run(self):
        while not self.stop_event.is_set():
            db=SessionLocal()
            try:
                merchant_id,_=random.choice(MERCHANTS)
                amount=random.choice(AMOUNTS)
                tx=create_transaction(db,TransactionCreate(user_id=f"demo-user-{random.randint(1,8)}",amount=amount,merchant_id=merchant_id,device_id=f"demo-device-{random.randint(1,5)}",occurred_at=datetime.now(timezone.utc)))
                for state in (TransactionStatus.AUTHORIZED,TransactionStatus.PROCESSING,TransactionStatus.DEBITED):
                    tx=transition_transaction(db,tx,state,"SIMULATED_STATE_TRANSITION","Synthetic simulator event")
                    event_hub.publish_transaction(tx)
                if amount==Decimal("49999.00"):
                    tx=transition_transaction(db,tx,TransactionStatus.UNKNOWN,"MERCHANT_CONFIRMATION_MISSING","Synthetic unknown outcome scenario")
                else:
                    tx=transition_transaction(db,tx,TransactionStatus.SUCCESS,"SYNTHETIC_SUCCESS","Synthetic settlement outcome")
                event_hub.publish_transaction(tx)
                self.generated+=1
            except Exception:
                db.rollback()
            finally: db.close()
            self.stop_event.wait(self.interval)

simulator=Simulator()
