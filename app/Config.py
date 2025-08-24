from dotenv import load_dotenv
import os


class Config:
    """Configuration management with validation"""

    def __init__(self):
        load_dotenv()

        self.db_host = os.getenv("DB_HOST", "localhost")
        self.db_name = os.getenv("DB_NAME")
        self.db_user = os.getenv("DB_USER")
        self.db_password = os.getenv("DB_PASS")

        self.alpha_api_key = os.getenv("ALPHA_API_KEY")
        self.data_source = os.getenv("DATA_SOURCE", "yf").lower()  # main source
        self.fallback_source = os.getenv("FALLBACK_SOURCE", "yf").lower()  # <-- NEW

        self.symbols = ["GOOGL", "NVDA", "MSFT"]
        self.api_timeout = 30
