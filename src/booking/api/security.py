from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Annotated
from booking.domain.models import UserId

_bearer = HTTPBearer(auto_error=False)

class CurrentUser:
    def __init__(self, id: UserId, role: str):
        self.id = id
        self.role = role

async def require_user(credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)]) -> CurrentUser:
    if credentials is None:
        raise HTTPException(status_code=401, detail="No token")
    return CurrentUser(id=UserId("test-user"), role="visitor")
