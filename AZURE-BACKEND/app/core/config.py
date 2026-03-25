import os


class Settings:
    app_name: str = "Device Login API"
    app_env: str = os.getenv("APP_ENV", "development").lower()
    mongo_uri: str = os.getenv("MONGO_URI", "")
    login_db_name: str = os.getenv("LOGIN_DB_NAME", "User_Data")
    login_collection: str = os.getenv("LOGIN_COLLECTION", "user_login")
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "change-this-secret")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    jwt_expires_minutes: int = int(os.getenv("JWT_EXPIRES_MINUTES", "60"))
    jwt_issuer: str = os.getenv("JWT_ISSUER", "device-login-api")
    jwt_audience: str = os.getenv("JWT_AUDIENCE", "device-login-clients")
    realtime_db_name: str = os.getenv("REALTIME_DB_NAME", "realtime_data")
    sop_db_name: str = os.getenv("SOP_DB_NAME", "User_Data")
    sop_collection_name: str = os.getenv("SOP_COLLECTION_NAME", "Crop_SOP")
    planner_collection_name: str = os.getenv(
        "PLANNER_COLLECTION_NAME", "user_vatavaran_planner"
    )
    device_data_fetch_limit: int = int(os.getenv("DEVICE_DATA_FETCH_LIMIT", "100"))
    reset_password_collection: str = os.getenv(
        "RESET_PASSWORD_COLLECTION", "reset_password"
    )
    reset_token_expiry_minutes: int = int(os.getenv("RESET_TOKEN_EXPIRY_MINUTES", "15"))
    password_reset_base_url: str = os.getenv(
        "PASSWORD_RESET_BASE_URL", "http://127.0.0.1:8000"
    )
    smtp_host: str = os.getenv("SMTP_HOST", "")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_username: str = os.getenv("SMTP_USERNAME", "")
    smtp_password: str = os.getenv("SMTP_PASSWORD", "")
    smtp_from_email: str = os.getenv("SMTP_FROM_EMAIL", "contact@ezebuddies.com")
    smtp_use_tls: bool = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
    smtp_use_ssl: bool = os.getenv("SMTP_USE_SSL", "false").lower() == "true"
    bcrypt_rounds: int = int(os.getenv("BCRYPT_ROUNDS", "10"))
    mongo_server_selection_timeout_ms: int = int(
        os.getenv("MONGO_SERVER_SELECTION_TIMEOUT_MS", "5000")
    )
    mongo_connect_timeout_ms: int = int(os.getenv("MONGO_CONNECT_TIMEOUT_MS", "10000"))
    mongo_socket_timeout_ms: int = int(os.getenv("MONGO_SOCKET_TIMEOUT_MS", "10000"))
    cors_allowed_origins_raw: str = os.getenv("CORS_ALLOWED_ORIGINS", "*")
    mqtt_host: str = os.getenv("MQTT_HOST", "")
    mqtt_port: int = int(os.getenv("MQTT_PORT", "1883"))
    mqtt_username: str = os.getenv("MQTT_USERNAME", "")
    mqtt_password: str = os.getenv("MQTT_PASSWORD", "")
    mqtt_client_id: str = os.getenv("MQTT_CLIENT_ID", "ezebuddies-backend")
    mqtt_keepalive: int = int(os.getenv("MQTT_KEEPALIVE", "60"))
    mqtt_qos: int = int(os.getenv("MQTT_QOS", "1"))

    def validate(self) -> None:
        if not self.mongo_uri:
            raise RuntimeError("MONGO_URI environment variable is required")

        if self.jwt_expires_minutes <= 0:
            raise RuntimeError("JWT_EXPIRES_MINUTES must be greater than 0")

        if self.device_data_fetch_limit < 0:
            raise RuntimeError("DEVICE_DATA_FETCH_LIMIT cannot be negative")

        if self.app_env == "production" and self.jwt_secret_key == "change-this-secret":
            raise RuntimeError("Set a strong JWT_SECRET_KEY in production")

        if self.reset_token_expiry_minutes <= 0:
            raise RuntimeError("RESET_TOKEN_EXPIRY_MINUTES must be greater than 0")

        if self.bcrypt_rounds < 4 or self.bcrypt_rounds > 16:
            raise RuntimeError("BCRYPT_ROUNDS should be between 4 and 16")

        if not self.smtp_host:
            raise RuntimeError("SMTP_HOST environment variable is required")

        if not self.smtp_username:
            raise RuntimeError("SMTP_USERNAME environment variable is required")

        if not self.smtp_password:
            raise RuntimeError("SMTP_PASSWORD environment variable is required")

        if self.smtp_use_tls and self.smtp_use_ssl:
            raise RuntimeError("Use either SMTP_USE_TLS or SMTP_USE_SSL, not both")

    @property
    def cors_allowed_origins(self) -> list[str]:
        raw = self.cors_allowed_origins_raw.strip()
        if not raw:
            return ["*"]
        return [item.strip() for item in raw.split(",") if item.strip()]


settings = Settings()
