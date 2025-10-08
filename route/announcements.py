from fastapi import APIRouter, Form, HTTPException, status, Depends
from typing import Annotated
from db import announcements_collection, courses_collection
from bson.objectid import ObjectId
from dependencies.authn import authenticated_user
from dependencies.authz import has_roles
from datetime import datetime, timezone

announcements_router = APIRouter(tags=["Announcements"])

@announcements_router.post("/announcements", dependencies=[Depends(has_roles(["admin", "tutor"]))])
def create_announcement(
    title: Annotated[str, Form()],
    content: Annotated[str, Form()],
    course_id: Annotated[str, Form()],
    user: Annotated[dict, Depends(authenticated_user)],
    is_important: Annotated[bool, Form()] = False
):
    if not ObjectId.is_valid(course_id):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Invalid course ID")
    
    course = courses_collection.find_one({"_id": ObjectId(course_id), "is_active": True})
    if not course:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Course not found")
    
    announcement_data = {
        "title": title,
        "content": content,
        "course_id": course_id,
        "created_by": user["id"],
        "created_by_name": user["username"],
        "is_important": is_important,
        "created_at": datetime.now(tz=timezone.utc)
    }
    
    result = announcements_collection.insert_one(announcement_data)
    return {"message": "Announcement created successfully!", "announcement_id": str(result.inserted_id)}