from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from app import home

app = FastAPI()

# Montar carpeta static
app.mount("/static", StaticFiles(directory="static"), name="static")

# Middleware de sesión
app.add_middleware(SessionMiddleware, secret_key="FastComponents2025")

# Registrar router UNA sola vez
app.include_router(home.router)

# Cargar plantillas
templates = Jinja2Templates(directory="templates")
