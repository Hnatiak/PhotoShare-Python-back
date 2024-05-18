from fastapi import Request, Depends, HTTPException, status

from src.entity.models import User, Role
from src.services.auth import auth_service

class RoleAccess():
    def __init__(self, allowed_roles: list[Role]):
        self.allowed_roles = allowed_roles

    def __call__(self, request: Request, user: User = Depends(auth_service.get_current_user)):
        if user.role not in self.allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail='Access forbidden')


admin_access = RoleAccess([Role.admin, Role.moderator])
moderator_access = RoleAccess([Role.moderator])