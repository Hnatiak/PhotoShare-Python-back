import logging
from typing import Any, Dict, List

from fastapi import Depends, HTTPException, status, Request
import uvicorn

from src.entity.models import User, Role
from src.schemas.schemas import Operation
from src.services.auth import auth_service

logger = logging.getLogger(uvicorn.logging.__name__)
       

class AccessRule:
    def __init__(self, operation: Operation, roles: List[Role]):
        self.operation = operation
        self.roles = roles
        self.context_user:User = None

    def get_rule(self, current_user: User = Depends(auth_service.get_current_user)):
        self.context_user = current_user
        yield self

    def is_context_user_allowed(self, allowed_entity_owner: User | None = None, current_user: User | None = None) -> bool:    
        current_user = current_user or self.context_user
        if current_user.role == Role.admin:
            return True
        if allowed_entity_owner and current_user.id == allowed_entity_owner.id:
            return True                       
        return current_user.role in self.roles


class Authorization:
    def __init__(self, access_rules: List[AccessRule]) -> None:
        self.access_rules = access_rules
        self.context_user:User = None
    
    def authorize(self, current_user: User = Depends(auth_service.get_current_user)):
        self.context_user = current_user
        yield self
    
    def check_entity_permissions(self, entity_owner: User | None = None) -> tuple[bool, list[str]]:
        is_allowed: bool = True
        denied_operations: list[str] = []
        for rule in self.access_rules:
            if not rule.is_context_user_allowed(allowed_entity_owner=entity_owner, current_user=self.context_user):
                is_allowed = False
                denied_operations.append(rule.operation.value)
        return (is_allowed, denied_operations)