from fastapi import APIRouter
from data.models.events.event_model import UserEventModal
from data.models.user.user_model import UserModal

user_router = APIRouter(
    prefix="/user",
    tags=["User"],
)


@user_router.post("/event/")
def capture_user_event(event: UserEventModal):
    event.save()
    return 200


@user_router.post("/{user_id}/")
def upsert_user_id(user_id: str):
    user_id = user_id.strip().lower().replace(" ", "_")
    existing_user = UserModal.find(UserModal.username == user_id)
    is_new_user = False
    if not existing_user.count():
        existing_user = UserModal(username=user_id).save()
        is_new_user = True
    else:
        existing_user = existing_user.first()
    return {
        "user": existing_user.model_dump(),
        "is_new_user": is_new_user,
    }
