from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Адрес брокера сообщений RabbitMQ
    amqp_url: str = "amqp://guest:guest@localhost:5672/"

    # Подключение к PostgreSQL (хранение заказов)
    postgres_url: str = "postgresql://myuser:pgpwd@localhost:5432/orders_db"

    # Адрес Catalog Service для синхронных HTTP-запросов
    catalog_url: str = "http://localhost:8002/api"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
