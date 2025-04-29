from pydantic import BaseModel
from typing import Any, Optional

class ErrorResponse(BaseModel):
    message: str

class SuccessResponse(BaseModel):
    message: str
    data: Optional[Any] = []