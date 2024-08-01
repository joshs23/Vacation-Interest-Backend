# run server - uvicorn app.main:app --reload

from fastapi import Body, FastAPI
from . import models
from .database import engine
from .routers import Group, Location, Place, User, Auth, Feature
from fastapi.middleware.cors import CORSMiddleware

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:8080",
    "https://vacation-interest-api.com"

]

app.add_middleware(
    CORSMiddleware, 
    allow_origins=origins, 
    allow_credentials=True, 
    allow_methods=["*"], 
    allow_headers= ["*"],
)

app.include_router(Location.router)
app.include_router(Place.router)
app.include_router(User.router)
app.include_router(Auth.router)
app.include_router(Group.router)
app.include_router(Feature.router)

@app.get("/")
def root():
    return {"message": "Hello World"}