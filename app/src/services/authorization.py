import logging
from typing import List
from fastapi import Depends
import uvicorn
from src.entity.models import User, Role
from src.schemas.schemas import Operation
from src.services.auth import auth_service

logger = logging.getLogger(uvicorn.logging.__name__)
       

class AccessRule:
    """
    Represents a rule for access control based on operation and roles.

    This class defines an access rule that specifies an operation and a list of allowed roles.
    An additional attribute `context_user` is used internally to store the current user during permission checks.
    """
    def __init__(self, operation: Operation, roles: List[Role]):
        self.operation = operation
        self.roles = roles
        self.context_user:User = None

    def get_rule(self, current_user: User = Depends(auth_service.get_current_user)):
        """
        Provides access to the AccessRule instance with the current user set for permission checks.

        This method is a generator that yields itself (`self`). It sets the `context_user` attribute
        with the current user retrieved from the dependency injection function `auth_service.get_current_user`.

        Args:
            current_user (User, optional): The current user. Defaults to the value retrieved from the dependency.
        Yields:
            AccessRule: The current AccessRule instance with the context user set.
        """
        self.context_user = current_user
        yield self

    def is_context_user_allowed(self, allowed_entity_owner: User | None = None, current_user: User | None = None) -> bool:    
        """
        Checks if the current user is allowed to perform the associated operation.

        This method determines if the current user (stored in `context_user`) has the necessary permissions
        based on the defined operation and roles. It prioritizes admin role, then ownership of the entity,
        and finally checks if the user's role is included in the allowed roles list.

        Args:
            allowed_entity_owner (User, optional): The owner of the entity being accessed. Defaults to None.
            current_user (User, optional): The current user. Defaults to None (uses the context user).
        Returns:
            bool: True if the current user is allowed, False otherwise.
        """
        current_user = current_user or self.context_user
        if current_user.role == Role.admin:
            return True
        if allowed_entity_owner and current_user.id == allowed_entity_owner.id:
            return True                       
        return current_user.role in self.roles


class Authorization:
    """
    Provides methods for authorization checks based on access rules.

    This class manages a list of access rules and offers methods to authorize requests
    and check permissions for specific entities. An internal `context_user` attribute is used
    to store the current user during permission checks.
    """
    def __init__(self, access_rules: List[AccessRule]) -> None:
        self.access_rules = access_rules
        self.context_user:User = None
    
    def authorize(self, current_user: User = Depends(auth_service.get_current_user)):
        """
        Provides access to the Authorization instance with the current user set for permission checks.

        This method is a generator that yields itself (`self`). It sets the `context_user` attribute
        with the current user retrieved from the dependency injection function `auth_service.get_current_user`.

        Args:
            current_user (User, optional): The current user. Defaults to the value retrieved from the dependency.
        Yields:
            Authorization: The current Authorization instance with the context user set.
        """
        self.context_user = current_user
        yield self
    
    def check_entity_permissions(self, entity_owner: User | None = None) -> tuple[bool, list[str]]:
        """
        Checks if the current user has permissions to access a specific entity.

        This method iterates through the defined access rules and checks if the current user
        (stored in `context_user`) has permission for each operation based on the entity owner.
        It builds a list of denied operations if any access rule fails.

        Args:
            entity_owner (User, optional): The owner of the entity being accessed. Defaults to None.
        Returns:
            tuple[bool, list[str]]: A tuple containing a flag indicating overall permission (True if all allowed, False otherwise)
                                     and a list of operation names that are denied.
        """
        is_allowed: bool = True
        denied_operations: list[str] = []
        for rule in self.access_rules:
            if not rule.is_context_user_allowed(allowed_entity_owner=entity_owner, current_user=self.context_user):
                is_allowed = False
                denied_operations.append(rule.operation.value)
        return (is_allowed, denied_operations)