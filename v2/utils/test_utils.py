"""
Test utilities for school management system tests.
Provides helpers to create DummyRequest with correct user roles and to patch require_role for handler tests.
"""
from unittest.mock import MagicMock, patch

# Helper to create a dummy user with a specific role
def make_user(role="admin", user_id=1):
    user = MagicMock()
    user.id = user_id
    user.role.value = role
    return user

# Helper to create a DummyRequest with the correct user role
def make_request(DummyRequestClass, *args, role="admin", user_id=1, **kwargs):
    user = make_user(role=role, user_id=user_id)
    return DummyRequestClass(*args, user=user, role=role, **kwargs)

# Context manager to patch require_role to always allow in tests
def always_allow_require_role():
    return patch("utils.auth.require_role", lambda roles: (lambda f: f))
