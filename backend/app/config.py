from dotenv import load_dotenv
import os

load_dotenv()


class Settings:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    MONGO_URL = os.getenv("MONGO_URL")
    MONGO_URL_local = os.getenv("MONGO_URL_local")
    DB_NAME = os.getenv("DB_NAME", "Studypack_generator")
    NEWS_API_KEY = os.getenv("NEWS_API_KEY")
    CLERK_PUBLISHABLE_KEY = os.getenv("CLERK_PUBLISHABLE_KEY")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES = 15
    REFRESH_TOKEN_EXPIRE_DAYS = 7
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

    # LangSmith Observability & Tracing
    LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY") or os.getenv("LANGSMITH_API_KEY")
    LANGCHAIN_PROJECT = os.getenv("LANGCHAIN_PROJECT") or os.getenv("LANGSMITH_PROJECT") or "studypack-generator"
    LANGCHAIN_ENDPOINT = os.getenv("LANGCHAIN_ENDPOINT") or os.getenv("LANGSMITH_ENDPOINT") or "https://api.smith.langchain.com"
    LANGCHAIN_TRACING_V2 = os.getenv("LANGCHAIN_TRACING_V2") or os.getenv("LANGSMITH_TRACING") or ("true" if os.getenv("LANGCHAIN_API_KEY") or os.getenv("LANGSMITH_API_KEY") else "false")

    @property
    def is_langsmith_enabled(self) -> bool:
        return bool(self.LANGCHAIN_API_KEY and self.LANGCHAIN_TRACING_V2.lower() == "true")


settings = Settings()

# Synchronize LangSmith settings with os.environ for native LangChain/LangGraph automatic tracing
if settings.LANGCHAIN_API_KEY:
    os.environ["LANGCHAIN_API_KEY"] = settings.LANGCHAIN_API_KEY
    os.environ["LANGSMITH_API_KEY"] = settings.LANGCHAIN_API_KEY
    os.environ["LANGCHAIN_TRACING_V2"] = settings.LANGCHAIN_TRACING_V2
    os.environ["LANGSMITH_TRACING"] = settings.LANGCHAIN_TRACING_V2
    os.environ["LANGCHAIN_PROJECT"] = settings.LANGCHAIN_PROJECT
    os.environ["LANGSMITH_PROJECT"] = settings.LANGCHAIN_PROJECT
    os.environ["LANGCHAIN_ENDPOINT"] = settings.LANGCHAIN_ENDPOINT
    os.environ["LANGSMITH_ENDPOINT"] = settings.LANGCHAIN_ENDPOINT

