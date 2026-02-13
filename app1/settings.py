from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
  mariadb_user: str = "root"
  mariadb_password: str = "aiedu"
  mariadb_host: str = "db.quadecologics.cloud"
  mariadb_database: str = "mini"
  mariadb_port: int = "5053"

  kafka_topic: str = "miniProject2"
  kafka_server: str = "192.168.0.171:9094"

  redis_host: str = "localhost"
  redis_port: int = 6379
  redis_db: int = 0

  secret_key: str = "your-extremely-secure-random-secret-key"
  algorithm: str = "HS256"
  access_token_expire_minutes: int = 30

  model_config = SettingsConfigDict(
    env_file=".env",
    env_file_encoding="utf-8",
  )

settings = Settings()
