from pydantic import BaseModel
from typing import Optional

class ErrorResponse(BaseModel):
    status: str
    message: str
    code: str
    details: Optional[dict] = None