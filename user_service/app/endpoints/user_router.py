from fastapi import APIRouter, Depends, HTTPException

from app.models.user import User, UserCreate
from app.rabbitmq import publish_event
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


def get_service() -> UserService:
    return UserService()


@router.post("", response_model=User, status_code=201, summary="Регистрация пользователя")
async def register_user(data: UserCreate, service: UserService = Depends(get_service)) -> User:
    """Создаёт учётную запись и публикует событие user.registered
    (fanout notifications - для уведомлений, topic users - для других сервисов)."""
    try:
        user = service.register_user(data)
    except ValueError as exc:
        raise HTTPException(400, str(exc))

    payload = {
        "event": "user.registered",
        "user_id": user.id,
        "email": user.email,
        "role": user.role.value,
    }
    await publish_event("notifications", "fanout", "", payload)
    await publish_event("users", "topic", "user.registered", payload)
    return user


@router.get("/{user_id}", response_model=User, summary="Получить пользователя")
def get_user(user_id: int, service: UserService = Depends(get_service)) -> User:
    try:
        return service.get_user(user_id)
    except KeyError as exc:
        raise HTTPException(404, str(exc))


@router.delete("/{user_id}", response_model=User, summary="Удалить пользователя")
async def delete_user(user_id: int, service: UserService = Depends(get_service)) -> User:
    """Удаляет учётную запись и публикует user.deleted
    (другие сервисы анонимизируют связанные данные)."""
    try:
        user = service.delete_user(user_id)
    except KeyError as exc:
        raise HTTPException(404, str(exc))

    await publish_event(
        "users",
        "topic",
        "user.deleted",
        {"event": "user.deleted", "user_id": user.id},
    )
    return user
