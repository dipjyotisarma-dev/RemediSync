"""Application configuration and environment settings for RemediSync API."""

import os
from typing import List


class Settings:
    """Central configuration for RemediSync REST API service."""

    PROJECT_NAME: str = "RemediSync REST API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # CORS Origins
    _raw_cors = os.getenv("CORS_ORIGINS", "")
    if _raw_cors:
        CORS_ORIGINS: List[str] = [origin.strip() for origin in _raw_cors.split(",")]
    else:
        CORS_ORIGINS: List[str] = [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]


settings = Settings()
