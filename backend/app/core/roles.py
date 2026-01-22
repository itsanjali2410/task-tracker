"""
Role Constants and Permission Helpers
Centralized role management for backward-compatible role extensions
"""

# All valid roles in the system
# IMPORTANT: Do not remove existing roles, only add new ones
VALID_ROLES = [
    "admin",
    "manager",
    "team_member",  # Legacy role - kept for backward compatibility
    "sales",
    "operations", 
    "marketing",
    "accounts"
]

# Role groups for permission checks
ADMIN_ROLES = ["admin"]
MANAGER_ROLES = ["admin", "manager"]

# Staff roles - can create tasks, comments, attachments, participate in chats
STAFF_ROLES = [
    "admin", 
    "manager", 
    "team_member",
    "sales",
    "operations",
    "marketing",
    "accounts"
]

# Roles that can view all tasks (not just their own)
ALL_TASKS_VIEW_ROLES = [
    "admin",
    "manager",
    "sales",
    "operations",
    "marketing", 
    "accounts"
]

# Roles that cannot assign tasks to admins
NON_ADMIN_ROLES = [
    "team_member",
    "sales",
    "operations",
    "marketing",
    "accounts"
]

# Roles that can access reports
REPORTS_ACCESS_ROLES = ["admin", "manager"]

# Roles that can access audit logs
AUDIT_ACCESS_ROLES = ["admin", "manager"]

# Roles that can manage users (CRUD)
USER_MANAGEMENT_ROLES = ["admin"]


def is_valid_role(role: str) -> bool:
    """Check if a role is valid"""
    return role in VALID_ROLES


def can_assign_to_admin(user_role: str) -> bool:
    """Check if user can assign tasks to admin"""
    return user_role in ADMIN_ROLES or user_role in MANAGER_ROLES


def get_assignable_roles_for_user(user_role: str) -> list:
    """Get list of roles that a user can assign tasks to"""
    if user_role in ["admin", "manager"]:
        return VALID_ROLES
    else:
        # Non-admin/manager roles cannot assign to admins
        return [r for r in VALID_ROLES if r != "admin"]
