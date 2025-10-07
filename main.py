from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from route.users import users_router
from route.courses import courses_router
from route.resources import resources_router
from route.calendar import calendar_router
from route.attendance import attendance_router
from route.announcements import announcements_router
import os
from dotenv import load_dotenv

load_dotenv()

tags_metadata = [
    {
        "name": "Authentication",
        "description": "User registration, login, and profile management",
    },
    {
        "name": "Courses",
        "description": "Course management, enrollment, and tutor assignments",
    },
    {
        "name": "Learning Resources",
        "description": "Upload, manage, and access course materials",
    },
    {
        "name": "Calendar & Events",
        "description": "Manage schedules, deadlines, and reminders",
    },
    {
        "name": "Attendance",
        "description": "Learner check-ins and tutor verification",
    },
    {
        "name": "Announcements",
        "description": "Course updates and notifications",
    },
]

app = FastAPI(
    title="BridgeLMS API",
    description="A lightweight Learning Management System connecting learners and tutors",
    version="1.0.0",
    openapi_tags=tags_metadata
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Homepage
@app.get("/")
def get_home():
    return {"message": "Welcome to BridgeLMS - Connecting Learners and Tutors"}

# Include routers
app.include_router(users_router)
app.include_router(courses_router)
app.include_router(resources_router)
app.include_router(calendar_router)
app.include_router(attendance_router)
app.include_router(announcements_router)