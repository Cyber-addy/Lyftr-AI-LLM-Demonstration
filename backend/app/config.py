import os
from pathlib import Path

from dotenv import load_dotenv


# ============================================================
# PATHS
# ============================================================

# config.py:
# lyftr-ai-assignment/backend/app/config.py
#
# Go up three levels to reach:
# lyftr-ai-assignment/

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ENV_FILE = PROJECT_ROOT / ".env"


# Load ONLY the root .env file.
# override=True prevents old shell variables from overriding it.
load_dotenv(
    dotenv_path=ENV_FILE,
    override=True,
)


# ============================================================
# SETTINGS
# ============================================================

class Settings:

    def __init__(self):

        # ----------------------------------------------------
        # DATABASE
        # ----------------------------------------------------

        self.database_url = os.getenv(
            "DATABASE_URL",
            "sqlite:///./app.db",
        )


        # ----------------------------------------------------
        # CORS
        # ----------------------------------------------------

        self.allowed_origins = [
            origin.strip()
            for origin in os.getenv(
                "ALLOWED_ORIGINS",
                "http://localhost:3000",
            ).split(",")
            if origin.strip()
        ]


        # ----------------------------------------------------
        # FAILURE SIMULATION
        # ----------------------------------------------------

        self.enable_failure_simulation = (
            os.getenv(
                "ENABLE_FAILURE_SIMULATION",
                "false",
            ).lower()
            == "true"
        )


        # ----------------------------------------------------
        # MODEL
        # ----------------------------------------------------

        self.llm_model = os.getenv(
            "LLM_MODEL",
            "gemini/gemini-flash-lite-latest",
        )


        # ----------------------------------------------------
        # API KEY POOL
        # ----------------------------------------------------

        raw_keys = os.getenv(
            "LLM_API_KEYS",
            "",
        )

        self.llm_api_keys = [
            key.strip()
            for key in raw_keys.split(",")
            if key.strip()
        ]


settings = Settings()