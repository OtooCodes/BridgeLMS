from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

# Connect to MongoDB
mongo_client = MongoClient(os.getenv("MONGO_URI"))
bridgelms_db = mongo_client["bridgelms_db"]

# Collections
users_collection = bridgelms_db["users"]
courses_collection = bridgelms_db["courses"]
enrollments_collection = bridgelms_db["enrollments"]
resources_collection = bridgelms_db["resources"]
events_collection = bridgelms_db["events"]
calendar_collection = bridgelms_db["calendar"]
attendance_collection = bridgelms_db["attendance"]
announcements_collection = bridgelms_db["announcements"]
reminders_collection = bridgelms_db["reminders"]