from typing import List

from fastapi import Depends, HTTPException, status, Request

from src.entity.models import User, Role
from src.services.auth import auth_service


class RoleChecker:
    def __init__(self, allowed_roles: List[Role]):
        self.allowed_roles = allowed_roles

    async def __call__(self, request: Request, current_user: User = Depends(auth_service.get_current_user)):
        if current_user.role not in self.allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operation forbidden")

admin_access = RoleChecker([Role.admin])
moderator_access = RoleChecker([Role.moderator, Role.admin])

async def is_owner(current_user: User, item_owner_id: int):
    return current_user.id == item_owner_id