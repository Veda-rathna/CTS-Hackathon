"""SQLAlchemy model for States.

Maps state_id to state_code and state_name.
"""
from __future__ import annotations

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class State(Base):
    __tablename__ = "states"

    state_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    state_code: Mapped[str] = mapped_column(String(10), index=True)
    state_name: Mapped[str] = mapped_column(String(100))
