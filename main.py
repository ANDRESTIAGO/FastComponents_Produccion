from fastapi import FastAPI, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from starlette.middleware.sessions import SessionMiddleware
from app.home import router as auth_router
from app.home import router as core_router 
from app import home

app = FastAPI()


app.mount("/static", StaticFiles(directory="static"), name="static")
app.add_middleware(SessionMiddleware,secret_key="FastComponents2025")

app.include_router(home.router)
app.include_router(auth_router)
app.include_router(core_router)

templates = Jinja2Templates(directory="templates")
