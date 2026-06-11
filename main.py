import sys
import subprocess
from pathlib import Path

from loguru import logger
from app.core.config import config
from app.core.db import init_db


def main():
    logger.info("=" * 60)
    logger.info("ORESNA CAPTADOR — Sistema de Captacion B2B con IA")
    logger.info("=" * 60)

    warnings = config.validate()
    if warnings:
        logger.warning("Advertencias de configuracion:")
        for w in warnings:
            logger.warning(f"  {w}")
        logger.warning("  Configura las claves en el archivo .env antes de usar el sistema")
    else:
        logger.success("Configuracion validada correctamente")

    logger.info("Inicializando base de datos...")
    init_db()

    logger.info("Arrancando panel de control...")
    ui_path = Path(__file__).parent / "app" / "ui" / "main.py"

    subprocess.run([
        sys.executable, "-m", "streamlit", "run",
        str(ui_path),
        "--server.port=8501",
        "--server.headless=false",
        "--theme.base=dark",
        "--theme.primaryColor=#e2c36b",
        "--theme.backgroundColor=#0a0e1a",
        "--theme.secondaryBackgroundColor=#111827",
        "--theme.textColor=#f1f5f9",
        "--browser.gatherUsageStats=false",
    ])


if __name__ == "__main__":
    main()
