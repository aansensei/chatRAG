"""Single source of truth for department/role-based access control.

Both write authority (ingest: upload/rename/delete) and read authority (chat:
query/list) must agree on who counts as "in" a department or "privileged" —
importing from here instead of duplicating the checks is what keeps them from
drifting apart.
"""

# Real department folders under AanJSC_Documents/ — anything else (default,
# ad-hoc project folders, misc shared resources) is not department-owned and
# stays open to every authenticated user. Keep in sync with the frontend's
# DEPARTMENT_OPTIONS values.
RESTRICTED_DEPARTMENTS = {"Engineering", "Executive", "Finance", "HR", "IT", "Marketing", "Sales"}

CONFIDENTIAL_LEVELS = {"confidential", "secret"}


def department_of(collection: str) -> str:
    return collection.rsplit("/", 1)[-1]


def is_admin_or_leadership(user: dict) -> bool:
    return user["role"] == "admin" or user.get("department") == "Ban Giám đốc"


def has_write_authority(user: dict, collection: str) -> bool:
    """Admins and Ban Giám đốc can add/delete anywhere. A department head can do
    the same, but only within their own department's folder — everyone else has
    to go through the request/approval flow instead."""
    if is_admin_or_leadership(user):
        return True
    return bool(user.get("is_department_head")) and user.get("department") == department_of(collection)


def can_read_collection(user: dict, collection: str) -> bool:
    """Shared/general folders (not named after a real department) stay open to
    every authenticated user. A real department's folder is only readable by
    members of that department (or admin/Ban Giám đốc)."""
    dept = department_of(collection)
    if dept not in RESTRICTED_DEPARTMENTS:
        return True
    if is_admin_or_leadership(user):
        return True
    return user.get("department") == dept


def can_see_confidential(user: dict) -> bool:
    """CONFIDENTIAL/SECRET documents are visible to admin, Ban Giám đốc, and
    department heads only — regardless of which folder they're filed under."""
    return is_admin_or_leadership(user) or bool(user.get("is_department_head"))
