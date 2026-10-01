import asyncio, hashlib, os, threading, time
from collections import defaultdict
from fastapi import Request
from fastapi.responses import JSONResponse

_local=defaultdict(lambda:(0,0.0));_lock=threading.Lock()
async def rate_limit_middleware(request:Request,call_next):
    if not request.url.path.startswith("/api/v1") or request.method=="OPTIONS": return await call_next(request)
    limit=int(os.getenv("RATE_LIMIT_PER_MINUTE","120"))
    if limit>0:
        redis_client=None
        try:
            from app.websocket.manager import event_hub
            redis_client=event_hub.redis
        except Exception: pass
        identity=request.headers.get("authorization","") or (request.client.host if request.client else "unknown")
        key="finintel:rate:"+hashlib.sha256(identity.encode()).hexdigest()[:24]
        allowed=True
        try:
            if redis_client:
                count=await asyncio.to_thread(redis_client.incr,key)
                if count==1: await asyncio.to_thread(redis_client.expire,key,60)
                allowed=count<=limit
            else:
                now=time.monotonic()
                with _lock:
                    count,expires=_local[key]
                    if now>=expires: count,expires=0,now+60
                    count+=1;_local[key]=(count,expires)
                    allowed=count<=limit
        except Exception:
            allowed=True
        if not allowed: return JSONResponse({"detail":"Rate limit exceeded; retry later"},status_code=429,headers={"Retry-After":"60"})
    return await call_next(request)
