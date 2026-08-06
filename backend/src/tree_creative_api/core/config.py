from functools import lru_cache
from typing import Literal, Self

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["development", "test", "uat", "production"]
_INSECURE_SESSION_SECRET = "change-me-before-deployment"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "tree-creative-api"
    app_env: Environment = "development"
    debug: bool = False
    log_level: str = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_v1_prefix: str = "/api/v1"
    docs_enabled: bool = True
    allowed_origins: list[str] = Field(default_factory=lambda: ["http://localhost:8000"])
    allowed_hosts: list[str] = Field(
        default_factory=lambda: ["localhost", "127.0.0.1", "testserver"]
    )

    mysql_url: str = "mysql+asyncmy://tree_creative:tree_creative@localhost:3306/tree_creative"
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"
    langgraph_redis_url: str = "redis://localhost:6379/3"

    minio_endpoint: str = "localhost:9000"
    minio_access_key: SecretStr = SecretStr("tree-creative")
    minio_secret_key: SecretStr = SecretStr("change-me-minio-secret")
    minio_secure: bool = False
    minio_bucket: str = "tree-creative"

    session_secret: SecretStr = SecretStr(_INSECURE_SESSION_SECRET)
    frontend_base_url: str = "http://localhost:8080"
    wps_gateway_base_url: str = "https://wps-sso.shueho.com"
    wps_gateway_client_service: str = "tree-creative"
    wps_gateway_client_secret: SecretStr = SecretStr("")
    wps_gateway_redirect_uri: str = "http://localhost:8000/api/oauth/callback"
    auth_session_cookie_name: str = "tree_creative_session"
    auth_session_ttl_seconds: int = 28_800
    auth_login_state_ttl_seconds: int = 600
    auth_token_verify_interval_seconds: int = 300
    auth_token_refresh_leeway_seconds: int = 120

    @model_validator(mode="after")
    def reject_insecure_production_defaults(self) -> Self:
        if (
            self.app_env == "production"
            and self.session_secret.get_secret_value() == _INSECURE_SESSION_SECRET
        ):
            raise ValueError("SESSION_SECRET must be replaced in production")
        if self.app_env == "production" and not self.wps_gateway_client_secret.get_secret_value():
            raise ValueError("WPS_GATEWAY_CLIENT_SECRET is required in production")
        return self

    @property
    def auth_session_cookie_secure(self) -> bool:
        return self.app_env == "production"

    @property
    def auth_redis_key_prefix(self) -> str:
        return f"tree-creative:{self.app_env}:auth"


@lru_cache
def get_settings() -> Settings:
    return Settings()
