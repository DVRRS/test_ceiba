import logging
import traceback

from fastapi import APIRouter, HTTPException
from google.api_core.exceptions import GoogleAPICallError

from src.config import get_settings

from src.models.itemModel import CleanRunRequest, DatamartRunRequest
from src.services.clean_service import run_clean_incremental
from src.services.datamart_service import run_datamart_build


router = APIRouter()
logger = logging.getLogger("api")

@router.post("/clean/run")
async def run_clean(request: CleanRunRequest):
    try:
        return run_clean_incremental(run_dq=request.run_dq)
    except GoogleAPICallError as e:
        # BigQuery/Google client errors: keep message, but always log full traceback.
        logger.exception("BigQuery call failed")
        detail = str(e)
        if get_settings().debug:
            detail = {"message": str(e), "traceback": traceback.format_exc()}
        raise HTTPException(status_code=502, detail=detail)
    except Exception as e:
        logger.exception("Unhandled error in /clean/run")
        detail = "Internal error"
        if get_settings().debug:
            detail = {"message": str(e), "traceback": traceback.format_exc()}
        raise HTTPException(status_code=500, detail=detail)


@router.post("/datamart/run")
async def run_datamart(_: DatamartRunRequest):
    try:
        return run_datamart_build()
    except GoogleAPICallError as e:
        logger.exception("BigQuery call failed in datamart")
        detail = str(e)
        if get_settings().debug:
            detail = {"message": str(e), "traceback": traceback.format_exc()}
        raise HTTPException(status_code=502, detail=detail)
    except Exception as e:
        logger.exception("Unhandled error in /datamart/run")
        detail = "Internal error"
        if get_settings().debug:
            detail = {"message": str(e), "traceback": traceback.format_exc()}
        raise HTTPException(status_code=500, detail=detail)
