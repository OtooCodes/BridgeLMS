from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status, Depends
from typing import Annotated, List
import cloudinary
import cloudinary.uploader
import os
from db import resources_collection, courses_collection, enrollments_collection
from bson.objectid import ObjectId
from utils import replace_mongo_id
from dependencies.authn import is_authenticated, authenticated_user
from dependencies.authz import has_roles
from datetime import datetime, timezone

resources_router = APIRouter(tags=["Learning Resources"])

@resources_router.post("/resources", dependencies=[Depends(has_roles(["admin", "tutor"]))])
def upload_resource(
    title: Annotated[str, Form()],
    description: Annotated[str, Form()],
    course_id: Annotated[str, Form()],
    resource_type: Annotated[str, Form()],  # pdf, video, link, document
    user: Annotated[dict, Depends(authenticated_user)],
    file: UploadFile = File(None),
    external_url: Annotated[str, Form()] = None
):
    # Verify user has access to the course
    course = courses_collection.find_one({"_id": ObjectId(course_id)})
    if not course or course["tutor_id"] != user["id"]:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Access denied to this course")
    
    resource_data = {
        "title": title,
        "description": description,
        "course_id": course_id,
        "resource_type": resource_type,
        "uploaded_by": user["id"],
        "uploaded_at": datetime.now(tz=timezone.utc),
        "file_url": None,
        "external_url": None
    }
    
    if resource_type in ["pdf", "document", "video"] and file:
        # Upload to Cloudinary
        upload_result = cloudinary.uploader.upload(file.file)
        resource_data["file_url"] = upload_result["secure_url"]
        resource_data["file_name"] = file.filename
    elif resource_type == "link" and external_url:
        resource_data["external_url"] = external_url
    else:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid resource type or missing file/URL")
    
    result = resources_collection.insert_one(resource_data)
    return {"message": "Resource uploaded successfully!", "resource_id": str(result.inserted_id)}

@resources_router.get("/resources/course/{course_id}")
def get_course_resources(
    course_id: str,
    user: Annotated[dict, Depends(authenticated_user)]
):
    if not ObjectId.is_valid(course_id):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Invalid course ID")
    
    # Check if user is enrolled or is the tutor
    course = courses_collection.find_one({"_id": ObjectId(course_id)})
    if not course:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Course not found")
    
    if user["role"] == "learner":
        enrollment = enrollments_collection.find_one({
            "course_id": course_id,
            "learner_id": user["id"]
        })
        if not enrollment:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Not enrolled in this course")
    
    resources = list(resources_collection.find({"course_id": course_id}).sort("uploaded_at", -1))
    return {"data": list(map(replace_mongo_id, resources))}