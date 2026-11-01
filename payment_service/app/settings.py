from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Адрес брокера сообщений RabbitMQ
    amqp_url: str = "amqp://guest:guest@localhost:5672/"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
