import os
from pathlib import Path
from dotenv import load_dotenv
from loguru import logger

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")


class Config:
    BASE_DIR: Path = BASE_DIR
    DATA_DIR: Path = BASE_DIR / "data"
    ASSETS_DIR: Path = BASE_DIR / "assets"

    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "groq")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")

    RESEND_API_KEY: str = os.getenv("RESEND_API_KEY", "")
    EMAIL_FROM: str = os.getenv("EMAIL_FROM", "captacion@oresna.es")
    EMAIL_FROM_NAME: str = os.getenv("EMAIL_FROM_NAME", "ORESNA Inmobiliaria")

    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR}/captador.db")

    EMPRESA_NOMBRE: str = os.getenv("EMPRESA_NOMBRE", "ORESNA Inmobiliaria")
    EMPRESA_ZONA: str = os.getenv("EMPRESA_ZONA", "Navarra")
    EMPRESA_TELEFONO: str = os.getenv("EMPRESA_TELEFONO", "")
    EMPRESA_WEB: str = os.getenv("EMPRESA_WEB", "")

    SCRAPING_DELAY: int = int(os.getenv("SCRAPING_DELAY_SECONDS", "2"))
    SCRAPING_HEADLESS: bool = os.getenv("SCRAPING_HEADLESS", "true").lower() == "true"
    MAX_CONTACTOS: int = int(os.getenv("MAX_CONTACTOS_POR_SESION", "50"))

    SCHEDULER_HORA: str = os.getenv("SCHEDULER_HORA", "08:00")
    SCHEDULER_ACTIVO: bool = os.getenv("SCHEDULER_ACTIVO", "false").lower() == "true"

    APP_ENV: str = os.getenv("APP_ENV", "development")
    IS_DEV: bool = APP_ENV == "development"

    @classmethod
    def get_llm_api_key(cls) -> str:
        if cls.LLM_PROVIDER == "openai":
            return cls.OPENAI_API_KEY
        return cls.GROQ_API_KEY

    @classmethod
    def validate(cls) -> list[str]:
        issues = []
        if not cls.get_llm_api_key():
            issues.append(f"Falta la clave API para {cls.LLM_PROVIDER.upper()}")
        if not cls.RESEND_API_KEY:
            issues.append("Falta RESEND_API_KEY - el envio de emails estara desactivado")
        if not cls.DATA_DIR.exists():
            cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
            logger.info(f"Directorio de datos creado: {cls.DATA_DIR}")
        return issues


config = Config()
