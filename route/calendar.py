from fastapi import APIRouter

calendar_router = APIRouter(tags=["Calendar & Events"])

@calendar_router.get("/calendar/events")
def get_events():
    return {"data": [], "message": "Calendar functionality coming soon"}