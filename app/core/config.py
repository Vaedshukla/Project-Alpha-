from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Project Alpha"
    api_prefix: str = "/api"
    env: str = "development"
    debug: bool = True

    database_url: str = "postgresql+asyncpg://alpha_user:alpha_pass@localhost:5432/alpha_db"

    jwt_secret: str = "change_me"
    jwt_algorithm: str = "HS256"
    jwt_access_expires_minutes: int = 30
    jwt_refresh_expires_days: int = 7
    agent_shared_secret: str = "agent_secret_change_me"

    cors_allow_origins: str = "*"

    email_host: str = "smtp.example.com"
    email_port: int = 587
    email_user: str = ""
    email_pass: str = ""
    email_from: str = "alerts@example.com"
    email_rate_limit_minutes: int = 15
    sendgrid_api_key: str = ""  # Optional SendGrid API key

    admin_default_name: str = "Admin User"
    admin_default_email: str = "admin@example.com"
    admin_default_password: str = "ChangeMe123!"
    
    log_retention_days: int = 30
    model_refresh_days: int = 1
    sendgrid_api_key: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

