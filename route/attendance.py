from fastapi import APIRouter, HTTPException, status, Depends
from typing import Annotated
from db import attendance_collection, courses_collection, enrollments_collection
from bson.objectid import ObjectId
from utils import replace_mongo_id
from dependencies.authn import is_authenticated, authenticated_user
from dependencies.authz import has_roles
from datetime import datetime, timezone

attendance_router = APIRouter(tags=["Attendance"])

@attendance_router.post("/attendance/checkin/{course_id}", dependencies=[Depends(has_roles(["learner"]))])
def checkin_attendance(
    course_id: str,
    user: Annotated[dict, Depends(authenticated_user)]
):
    if not ObjectId.is_valid(course_id):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Invalid course ID")
    
    # Verify enrollment
    enrollment = enrollments_collection.find_one({
        "course_id": course_id,
        "learner_id": user["id"],
        "status": "active"
    })
    
    if not enrollment:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not enrolled in this course")
    
    # Check if already checked in today
    today = datetime.now(tz=timezone.utc).date()
    existing_checkin = attendance_collection.find_one({
        "course_id": course_id,
        "learner_id": user["id"],
        "date": {"$gte": datetime.combine(today, datetime.min.time().replace(tzinfo=timezone.utc))}
    })
    
    if existing_checkin:
        raise HTTPException(status.HTTP_409_CONFLICT, "Already checked in today")
    
    attendance_data = {
        "course_id": course_id,
        "learner_id": user["id"],
        "learner_name": user["username"],
        "date": datetime.now(tz=timezone.utc),
        "status": "present"
    }
    
    result = attendance_collection.insert_one(attendance_data)
    return {"message": "Attendance recorded successfully!", "attendance_id": str(result.inserted_id)}

@attendance_router.get("/attendance/course/{course_id}", dependencies=[Depends(has_roles(["admin", "tutor"]))])
def get_course_attendance(
    course_id: str,
    user: Annotated[dict, Depends(authenticated_user)]
):
    if not ObjectId.is_valid(course_id):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Invalid course ID")
    
    # Verify tutor access
    course = courses_collection.find_one({"_id": ObjectId(course_id)})
    if not course:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Course not found")
    
    if user["role"] == "tutor" and course["tutor_id"] != user["id"]:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Access denied to this course")
    
    attendance_records = list(attendance_collection.find({"course_id": course_id}).sort("date", -1))
    return {"data": list(map(replace_mongo_id, attendance_records))}

@attendance_router.get("/attendance/my-attendance", dependencies=[Depends(is_authenticated)])
def get_my_attendance(user: Annotated[dict, Depends(authenticated_user)]):
    if user["role"] == "learner":
        attendance_records = list(attendance_collection.find({"learner_id": user["id"]}).sort("date", -1))
    else:
        # For tutors, get attendance for all their courses
        courses = list(courses_collection.find({"tutor_id": user["id"]}))
        course_ids = [str(course["_id"]) for course in courses]
        attendance_records = list(attendance_collection.find({"course_id": {"$in": course_ids}}).sort("date", -1))
    
    return {"data": list(map(replace_mongo_id, attendance_records))}