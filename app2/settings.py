from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
  kafka_topic: str
  kafka_server: str

  mail_username: str
  mail_password: str
  mail_from: str
  mail_port: int
  mail_server: str
  mail_from_name: str
  mail_starttls: bool = True
  mail_ssl_tls: bool = False

  use_credentials: bool = True
  validate_certs: bool = True
  
  redis_host: str
  redis_port: int
  redis_db: int

  model_config = SettingsConfigDict(
    env_file=".env",
    env_file_encoding="utf-8",
  )

settings = Settings()
