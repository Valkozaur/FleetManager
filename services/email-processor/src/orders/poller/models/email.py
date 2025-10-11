from pydantic import BaseModel
from typing import List
from datetime import datetime

class Attachment(BaseModel):
    filename: str
    mime_type: str
    size: int
    data: bytes

class Email(BaseModel):
    id: str
    subject: str
    sender: str
    body: str
    received_at: datetime
    attachments: List[Attachment] = []