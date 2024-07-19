# run server - uvicorn app.main:app --reload

from fastapi import Body, FastAPI
from . import models
from .database import engine
from .routers import Group, Location, Place, User, Auth

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(Location.router)
app.include_router(Place.router)
app.include_router(User.router)
app.include_router(Auth.router)
app.include_router(Group.router)