from app.models.user import User

# локальное хранилище: список объектов в памяти процесса
_users: list[User] = []
_next_id = 42  # идентификаторы начинаются с 42 - как в примерах отчёта ПР N5


class UserRepo:
    def get_users(self) -> list[User]:
        return _users

    def get_by_id(self, user_id: int) -> User:
        for user in _users:
            if user.id == user_id:
                return user
        raise KeyError(f"User {user_id} not found")

    def create_user(self, user: User) -> User:
        global _next_id
        if any(u.email == user.email for u in _users):
            raise ValueError(f"User with email {user.email} already exists")
        user.id = _next_id
        _next_id += 1
        _users.append(user)
        return user

    def delete_user(self, user_id: int) -> User:
        user = self.get_by_id(user_id)
        _users.remove(user)
        return user
