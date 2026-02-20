from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
  mariadb_user: str
  mariadb_password: str
  mariadb_host: str
  mariadb_database: str
  mariadb_port: int
  vite_react_url: str
  react_url: str
  kafka_topic: str
  kafka_server: str
  redis_host: str
  redis_port: int
  redis_db: int
  secret_key: str
  algorithm: str
  access_token_expire_minutes: int

  model_config = SettingsConfigDict(
    env_file=".env",
    env_file_encoding="utf-8",
  )

settings = Settings()