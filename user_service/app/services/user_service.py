from app.models.user import User, UserCreate
from app.repositories.local_user_repo import UserRepo


class UserService:
    """Бизнес-логика пользователей. Не знает, где хранятся данные."""

    def __init__(self, repo: UserRepo = None) -> None:
        self.repo = repo or UserRepo()

    def register_user(self, data: UserCreate) -> User:
        user = User(email=data.email, full_name=data.full_name)
        return self.repo.create_user(user)

    def get_user(self, user_id: int) -> User:
        return self.repo.get_by_id(user_id)

    def delete_user(self, user_id: int) -> User:
        return self.repo.delete_user(user_id)
