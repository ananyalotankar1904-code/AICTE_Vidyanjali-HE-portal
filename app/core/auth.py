from typing import Optional, List, Callable
from fastapi import Header, HTTPException, status, Depends
from pydantic import BaseModel


class UserIdentity(BaseModel):
    user_id: str
    role: str


def get_current_user(
    x_user_role: Optional[str] = Header(None, alias="X-User-Role", description="Role under which request is executed"),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id", description="Identifier of the executing user")
) -> UserIdentity:
    """
    Lightweight dependency for role-based authorization.
    Reads X-User-Role and X-User-Id headers.
    Provides sensible defaults for interactive testing.
    """
    role = x_user_role.strip() if x_user_role else "Institution Admin"
    user_id = x_user_id.strip() if x_user_id else "demo_user_01"
    return UserIdentity(user_id=user_id, role=role)


def require_roles(*allowed_roles: str) -> Callable[[UserIdentity], UserIdentity]:
    """Dependency factory enforcing permitted user roles."""
    def role_checker(current_user: UserIdentity = Depends(get_current_user)) -> UserIdentity:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Access denied for role '{current_user.role}'. "
                    f"Action requires one of: {list(allowed_roles)}"
                )
            )
        return current_user

    return role_checker
