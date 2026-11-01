import enum
from datetime import datetime

from pydantic import BaseModel, Field


class UserRole(str, enum.Enum):
    USER = "USER"
    MANAGER = "MANAGER"
    ADMIN = "ADMIN"


class User(BaseModel):
    """Анемичная модель пользователя: только данные, без поведения."""

    id: int = 0  # назначается репозиторием при создании
    email: str
    full_name: str
    role: UserRole = UserRole.USER
    created_at: datetime = Field(default_factory=datetime.now)


class UserCreate(BaseModel):
    email: str
    full_name: str
