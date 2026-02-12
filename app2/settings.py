from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
  kafka_topic: str = "miniProject2"
  kafka_server: str = "kafka:9092"

  mail_username: str = "메일"
  mail_password: str = "2차비번"
  mail_from: str = "메일"
  mail_port: int = 587
  mail_server: str = "smtp.gmail.com"
  mail_from_name: str = "Team3"
  mail_starttls: bool = True
  mail_ssl_tls: bool = False

  use_credentials: bool = True
  validate_certs: bool = True
  
  redis_host: str = "redis"
  redis_port: int = 6379
  redis_db: int = 0

  model_config = SettingsConfigDict(
    env_file=".env",
    env_file_encoding="utf-8",
  )

settings = Settings()
