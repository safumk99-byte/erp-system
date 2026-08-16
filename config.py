import os

from dotenv import load_dotenv


# =========================================================
# Environment
# =========================================================

load_dotenv()


# =========================================================
# Security
# =========================================================

SECRET_KEY = os.getenv(
    "SECRET_KEY"
)

if not SECRET_KEY:

    raise RuntimeError(
        "SECRET_KEY is not configured. "
        "Please set SECRET_KEY in the environment."
    )


# =========================================================
# Database
# =========================================================

DATABASE_URL = os.getenv(
    "DATABASE_URL"
)

if not DATABASE_URL:

    raise RuntimeError(
        "DATABASE_URL is not configured. "
        "Please set DATABASE_URL in the environment."
    )