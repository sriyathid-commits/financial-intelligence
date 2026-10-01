import hmac, os
from fastapi import Request
from fastapi.responses import JSONResponse

def configured_roles():
    roles={}
    for role,env_name in (("analyst","API_KEY_ANALYST"),("operator","API_KEY_OPERATOR")):
        value=os.getenv(env_name,"")
        if value: roles[value]=role
    return roles

async def security_middleware(request:Request,call_next):
    signed_partner_event=request.url.path=="/api/v1/partner-events"
    protected_path=request.url.path.startswith("/api/v1") or request.url.path=="/metrics"
    if os.getenv("AUTH_REQUIRED","false").lower()=="true" and protected_path and not signed_partner_event and request.method!="OPTIONS":
        auth=request.headers.get("authorization","")
        token=auth[7:] if auth.lower().startswith("bearer ") else ""
        role=None
        for candidate,configured in configured_roles().items():
            if hmac.compare_digest(token,candidate): role=configured
        if role is None:
            return JSONResponse({"detail":"Valid bearer token required"},status_code=401,headers={"WWW-Authenticate":"Bearer"})
        analyst_query=request.url.path=="/api/v1/queries/transactions" and request.method=="POST"
        if request.method in {"POST","PUT","PATCH","DELETE"} and not (role=="operator" or (role=="analyst" and analyst_query)):
            return JSONResponse({"detail":"Operator role required"},status_code=403)
        request.state.principal={"role":role}
    else:
        request.state.principal={"role":"demo"}
    return await call_next(request)

def validate_security_configuration():
    if os.getenv("AUTH_REQUIRED","false").lower()!="true": return
    analyst=os.getenv("API_KEY_ANALYST","");operator=os.getenv("API_KEY_OPERATOR","")
    if len(analyst)<32 or len(operator)<32 or hmac.compare_digest(analyst,operator):
        raise RuntimeError("AUTH_REQUIRED needs distinct API_KEY_ANALYST and API_KEY_OPERATOR values of at least 32 characters")
