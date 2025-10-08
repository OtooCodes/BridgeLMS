from dependencies.authn import authenticated_user
from fastapi import Depends, HTTPException, status
from typing import Annotated
from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    TUTOR = "tutor"
    LEARNER = "learner"

permissions = [
    {
        "role": "admin",
        "permissions": ["*"]
    },
    {
        "role": "tutor",
        "permissions": [
            "create_course",
            "manage_own_courses",
            "upload_resources",
            "create_events",
            "verify_attendance",
            "post_announcements",
            "view_learners"
        ]
    },
    {
        "role": "learner",
        "permissions": [
            "enroll_courses",
            "access_resources",
            "view_calendar",
            "check_attendance",
            "view_announcements",
            "set_reminders"
        ]
    }
]

def has_roles(roles):
    def check_roles(user: Annotated[any, Depends(authenticated_user)]):
        if user["role"] not in roles:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN, "Access denied!"
            )
    return check_roles

def has_permission(permission):
    def check_permission(user: Annotated[any, Depends(authenticated_user)]):
        role = user.get("role")
        for entry in permissions:
            if entry["role"] == role:
                perms = entry.get("permissions", [])
                if "*" in perms or permission in perms:
                    return user
                break
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Permission denied")
    return check_permission