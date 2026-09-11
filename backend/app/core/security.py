from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import base64, hashlib, hmac, json
from app.core.config import settings
from app.data.synthetic import USERS
bearer = HTTPBearer(auto_error=False)
def _b64(data: bytes) -> str: return base64.urlsafe_b64encode(data).rstrip(b'=').decode()
def _unb64(data: str) -> bytes: return base64.urlsafe_b64decode(data + '=' * (-len(data) % 4))
def authenticate(email: str, password: str):
    user = USERS.get(email)
    if not user or user["password"] != password: return None
    return {"email": email, "role": user["role"], "display_name": user["display_name"]}
def create_token(user: dict):
    header={"alg":"HS256","typ":"JWT"}; payload={"sub":user["email"],"role":user["role"],"name":user["display_name"],"exp":int((datetime.now(timezone.utc)+timedelta(minutes=settings.token_exp_minutes)).timestamp())}
    h=_b64(json.dumps(header,separators=(',',':')).encode()); p=_b64(json.dumps(payload,separators=(',',':')).encode()); sig=hmac.new(settings.jwt_secret.encode(),f"{h}.{p}".encode(),hashlib.sha256).digest()
    return f"{h}.{p}.{_b64(sig)}"
def decode_token(token: str):
    try:
        h,p,s=token.split('.'); expected=hmac.new(settings.jwt_secret.encode(),f"{h}.{p}".encode(),hashlib.sha256).digest()
        if not hmac.compare_digest(expected,_unb64(s)): raise ValueError('bad signature')
        payload=json.loads(_unb64(p))
        if int(payload['exp']) < int(datetime.now(timezone.utc).timestamp()): raise ValueError('expired')
        return payload
    except Exception as exc: raise HTTPException(401,"Invalid or expired token") from exc
def current_user(creds: HTTPAuthorizationCredentials | None = Depends(bearer)):
    if not creds: raise HTTPException(401,"Missing bearer token")
    return decode_token(creds.credentials)
