from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from ..db import Base


def get_or_404(db: Session, model: type[Base], obj_id: int, name: str):
    obj = db.get(model, obj_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{name} not found")
    return obj
