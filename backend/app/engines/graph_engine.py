from sqlalchemy import or_, select
from sqlalchemy.orm import Session
from app.models.transaction import Transaction

RELATIONS=(("user_id","USER","INVOLVES_USER"),("merchant_id","MERCHANT","PAID_MERCHANT"),("device_id","DEVICE","USED_DEVICE"),("beneficiary_id","BENEFICIARY","PAID_BENEFICIARY"),("mandate_id","MANDATE","USES_MANDATE"))
def transaction_graph(db:Session,transaction_id:str,limit:int=100)->dict:
    target=db.get(Transaction,transaction_id)
    if target is None: return None
    conditions=[getattr(Transaction,field)==getattr(target,field) for field,_,_ in RELATIONS if getattr(target,field)]
    peer_limit=max(0,limit-1)
    peers=list(db.scalars(select(Transaction).where(or_(*conditions),Transaction.transaction_id!=transaction_id).order_by(Transaction.created_at.desc()).limit(peer_limit))) if conditions and peer_limit else []
    peers.append(target)
    nodes={};edges=set()
    for tx in peers:
        tid=f"transaction:{tx.transaction_id}"
        nodes[tid]={"id":tid,"kind":"TRANSACTION","label":tx.transaction_id,"attributes":{"amount":str(tx.amount),"currency":tx.currency,"status":tx.status,"environment":tx.environment}}
        for field,kind,edge_type in RELATIONS:
            value=getattr(tx,field)
            if not value: continue
            nid=f"{kind.lower()}:{value}"
            nodes[nid]={"id":nid,"kind":kind,"label":value,"attributes":{}}
            edges.add((tid,nid,edge_type))
    return {"root_transaction_id":transaction_id,"nodes":list(nodes.values()),"edges":[{"source":a,"target":b,"type":c} for a,b,c in sorted(edges)],"limits":{"transactions":limit},"environment":"SYNTHETIC","limitations":["Relationships reflect shared IDs in recorded synthetic data and do not establish common ownership, wrongdoing, or causality."]}
