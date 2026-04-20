from pydantic import BaseModel


class CleanRunRequest(BaseModel):
    run_dq: bool = True


class DatamartRunRequest(BaseModel):
    # Placeholder for future datamart parameters
    run: bool = True