import logging
import warnings

from fastapi import FastAPI
from src.routes.routes import router


def _silence_noisy_warnings() -> None:
    # Local dev noise on macOS when Python links against LibreSSL.
    warnings.filterwarnings("ignore", message=".*NotOpenSSLWarning.*")

    warnings.filterwarnings("ignore", category=FutureWarning, module=r"google\..*")


_silence_noisy_warnings()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)

app = FastAPI()

app.include_router(router)