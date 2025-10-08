from fastapi import APIRouter, Form, HTTPException, status, Depends
from typing import Annotated, List
from db import courses_collection, enrollments_collection, users_collection
from bson.objectid import ObjectId
from utils import replace_mongo_id
from dependencies.authn import is_authenticated, authenticated_user
from dependencies.authz import has_roles, has_permission
from datetime import datetime, timezone

courses_router = APIRouter(tags=["Courses"])

@courses_router.post("/courses", dependencies=[Depends(has_roles(["admin", "tutor"]))])
def create_course(
    user: Annotated[dict, Depends(authenticated_user)],
    title: Annotated[str, Form()],
    description: Annotated[str, Form()],
    category: Annotated[str, Form()],
    max_students: Annotated[int, Form()] = 50,
    is_public: Annotated[bool, Form()] = True
):
    course_data = {
        "title": title,
        "description": description,
        "category": category,
        "max_students": max_students,
        "is_public": is_public,
        "tutor_id": user["id"],
        "tutor_name": user["username"],
        "created_at": datetime.now(tz=timezone.utc),
        "is_active": True
    }
    
    result = courses_collection.insert_one(course_data)
    return {"message": "Course created successfully!", "course_id": str(result.inserted_id)}

@courses_router.get("/courses")
def get_courses(
    category: str | None = None,
    search: str | None = None,
    limit: int = 20,
    skip: int = 0
):
    query_filter = {"is_active": True}
    
    if category:
        query_filter["category"] = {"$regex": f"^{category}$", "$options": "i"}
    
    if search:
        query_filter["$or"] = [
            {"title": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}}
        ]
    
    courses = list(courses_collection.find(filter=query_filter, limit=limit, skip=skip))
    return {"data": list(map(replace_mongo_id, courses))}

@courses_router.post("/courses/{course_id}/enroll", dependencies=[Depends(has_roles(["learner"]))])
def enroll_course(
    course_id: str,
    user: Annotated[dict, Depends(authenticated_user)]
):
    if not ObjectId.is_valid(course_id):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Invalid course ID")
    
    course = courses_collection.find_one({"_id": ObjectId(course_id), "is_active": True})
    if not course:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Course not found")
    
    # Check if already enrolled
    existing_enrollment = enrollments_collection.find_one({
        "course_id": course_id,
        "learner_id": user["id"]
    })
    
    if existing_enrollment:
        raise HTTPException(status.HTTP_409_CONFLICT, "Already enrolled in this course")
    
    # Check course capacity
    current_enrollments = enrollments_collection.count_documents({"course_id": course_id})
    if current_enrollments >= course["max_students"]:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Course is full")
    
    enrollment_data = {
        "course_id": course_id,
        "learner_id": user["id"],
        "learner_name": user["username"],
        "enrolled_at": datetime.now(tz=timezone.utc),
        "status": "active"
    }
    
    enrollments_collection.insert_one(enrollment_data)
    return {"message": "Successfully enrolled in course!"}

@courses_router.get("/courses/my-courses", dependencies=[Depends(is_authenticated)])
def get_my_courses(user: Annotated[dict, Depends(authenticated_user)]):
    if user["role"] in ["admin", "tutor"]:
        # Get courses taught by the user
        courses = list(courses_collection.find({"tutor_id": user["id"]}))
    else:
        # Get courses enrolled by the learner
        enrollments = list(enrollments_collection.find({"learner_id": user["id"]}))
        course_ids = [enrollment["course_id"] for enrollment in enrollments]
        courses = list(courses_collection.find({"_id": {"$in": [ObjectId(cid) for cid in course_ids]}}))
    
    return {"data": list(map(replace_mongo_id, courses))}

@courses_router.get("/courses/{course_id}/tutor")
def get_course_tutor(course_id: str):
    if not ObjectId.is_valid(course_id):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Invalid course ID")
    
    course = courses_collection.find_one({"_id": ObjectId(course_id)})
    if not course:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Course not found")
    
    tutor = users_collection.find_one({"_id": ObjectId(course["tutor_id"])})
    if not tutor:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tutor not found")
    
    return {
        "tutor_name": tutor["username"],
        "tutor_email": tutor["email"],
        "tutor_phone": tutor.get("phone", ""),
        "tutor_bio": tutor.get("bio", "")
    }