from enum import Enum
from fastapi import APIRouter, Depends, HTTPException, status, Form
from typing import Annotated
from pydantic import EmailStr, BaseModel
from db import users_collection
from bson import ObjectId
import bcrypt
import jwt
import os
from datetime import datetime, timezone, timedelta
from dependencies.authn import is_authenticated, authenticated_user
from dependencies.authz import has_roles


class UserRole(str, Enum):
    ADMIN = "admin"
    TUTOR = "tutor"
    LEARNER = "learner"


class RegisterUserRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: UserRole = UserRole.LEARNER
    phone: str | None = None
    bio: str | None = None


class LoginUserRequest(BaseModel):
    email: EmailStr
    password: str


class UpdateProfileRequest(BaseModel):
    username: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    bio: str | None = None

users_router = APIRouter(tags=["Authentication"])

@users_router.post("/users/register")
def register_user(request: RegisterUserRequest):
    if request.role == UserRole.ADMIN:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Cannot register as admin! Admin role is assigned manually.",
        )

    user_count = users_collection.count_documents(filter={"email": request.email})
    if user_count > 0:
        raise HTTPException(status.HTTP_409_CONFLICT, "User already exists")

    hashed_password = bcrypt.hashpw(request.password.encode("utf-8"), bcrypt.gensalt())

    users_collection.insert_one({
        "username": request.username,
        "email": request.email,
        "password": hashed_password,
        "role": request.role,
        "phone": request.phone or "",
        "bio": request.bio or "",
        "created_at": datetime.now(tz=timezone.utc)
    })

    return {"message": "User registered successfully!"}

@users_router.post("/users/login")
def login_user(request: LoginUserRequest):
    user_in_db = users_collection.find_one(filter={"email": request.email})

    if not user_in_db:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User does not exist!")

    hashed_password_in_db = user_in_db["password"]
    correct_password = bcrypt.checkpw(request.password.encode("utf-8"), hashed_password_in_db)

    if not correct_password:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect email or password")

    encoded_jwt = jwt.encode(
        {
            "id": str(user_in_db["_id"]),
            "role": user_in_db["role"],
            "exp": datetime.now(tz=timezone.utc) + timedelta(hours=24),
        },
        os.getenv("JWT_SECRET_KEY"),
        "HS256",
    )

    return {
        "message": "User logged in successfully!",
        "access_token": encoded_jwt,
        "role": user_in_db["role"],
        "user_id": str(user_in_db["_id"])
    }

@users_router.get("/users/profile", dependencies=[Depends(is_authenticated)])
def get_profile(user: Annotated[dict, Depends(authenticated_user)]):
    return {"data": user}

@users_router.put("/users/profile", dependencies=[Depends(is_authenticated)])
def update_profile(
    user: Annotated[dict, Depends(authenticated_user)],
    username: str = Form(None),
    email: str = Form(None),
    phone: str = Form(None),
    bio: str = Form(None),
):
    update_fields = {}
    if username is not None:
        update_fields['username'] = username
    if email is not None:
        update_fields['email'] = email
    if phone is not None:
        update_fields['phone'] = phone
    if bio is not None:
        update_fields['bio'] = bio

    if update_fields:
        users_collection.update_one(
            {"_id": ObjectId(user["id"])},
            {"$set": update_fields}
        )

    return {"message": "Profile updated successfully!"}