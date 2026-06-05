from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    AWS_REGION: str = "us-east-1"
    JIRA_BASE_URL: str = ""
    JIRA_API_TOKEN: str = ""
    JIRA_EMAIL: str = ""
    JIRA_WEBHOOK_SECRET: str = ""
    MLFLOW_TRACKING_URI: str = "http://localhost:5000"
    VERIFY_SIGNATURES: bool = True
    SLACK_WEBHOOK_URL: str = ""
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"

settings = Settings()
