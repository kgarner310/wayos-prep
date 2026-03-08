"""Authentication dependency for FastAPI routes.

Re-exports the JWT verification dependencies from app.api.deps.
Use `require_auth` as the standard dependency for protected routes.

Pattern:
    Authorization: Bearer <token>
    Returns HTTP 401 if missing or invalid.
    Decodes using JWT_SECRET_KEY from settings.
"""

from app.api.deps import (
    get_current_user,
    get_optional_user,
    require_role,
    CurrentUser,
)

# Alias for clarity in route definitions
require_auth = get_current_user

__all__ = [
    "require_auth",
    "get_current_user",
    "get_optional_user",
    "require_role",
    "CurrentUser",
]
