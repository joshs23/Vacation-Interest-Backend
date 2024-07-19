from sqlalchemy import Column, Integer, String
from sqlalchemy.sql.expression import text
from sqlalchemy.sql.sqltypes import TIMESTAMP
from .database import Base

class Location(Base):
    __tablename__ = "LOCATION"

    Location_id = Column(Integer, primary_key=True, nullable=False)
    Named = Column(String, nullable=False)
    Created_at = Column(TIMESTAMP(), server_default=text('now()'))