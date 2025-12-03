import os
import pandas as pd
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.middleware.sessions import SessionMiddleware
import shutil
from pathlib import Path

# importa tu router y operaciones
from app import home
from operations import operations

@pytest.fixture(scope="function")
def tmp_project_dir(tmp_path, monkeypatch):
    """
    Cambia el cwd a un tmp dir para que los archivos CSV se creen ahí
    y no toquen tus archivos reales. Devuelve la ruta (Path).
    """
    # crear estructura mínima (templates pueden omitirse si no se renderiza)
    p = tmp_path
    (p / "templates").mkdir()
    # cambiar cwd para que todas las lecturas relativas vayan aquí
    monkeypatch.chdir(p)
    yield p
    # cleanup no necesario; pytest borra tmp_path automáticamente

@pytest.fixture(scope="function")
def client(tmp_project_dir):
    """
    Crea el TestClient con tu router y SessionMiddleware.
    Además crea CSVs mínimos necesarios (usuarios.csv, componentes.csv, orden.csv).
    """
    # preparar archivos CSV mínimos para pruebas
    # usuarios.csv vacío con cabeceras
    usuarios = pd.DataFrame(columns=["id", "nombre_usuario", "correo", "contraseña_hash"])
    usuarios.to_csv("usuarios.csv", index=False)

    # componentes.csv con algunos componentes de ejemplo (Motherboard, CPU, RAM, GPU, HDD)
    componentes = pd.DataFrame([
        # id debe ser entero (compatibilidad por socket y tipo_ram)
        {"id": 1, "nombre": "MB-1", "tipo": "Motherboard", "socket": "AM4", "tipo_ram": "DDR4", "marca":"MSI", "modelo":"MB-1"},
        {"id": 2, "nombre": "CPU-AM4-1", "tipo": "CPU", "socket": "AM4", "tipo_ram": "", "marca":"AMD", "modelo":"Ryzen"},
        {"id": 3, "nombre": "RAM-DDR4-8GB", "tipo": "RAM", "socket": "", "tipo_ram": "DDR4", "marca":"Corsair", "modelo":"8GB"},
        {"id": 4, "nombre": "GPU-1", "tipo": "GPU", "socket": "", "tipo_ram": "", "marca":"NVIDIA", "modelo":"GTX"},
        {"id": 5, "nombre": "HDD-1", "tipo": "HDD", "socket": "", "tipo_ram": "", "marca":"Seagate", "modelo":"HDD1"},
        # Un CPU incompatible (otro socket)
        {"id": 6, "nombre": "CPU-INT", "tipo": "CPU", "socket": "LGA1200", "tipo_ram": "", "marca":"Intel", "modelo":"i5"},
        # RAM incompatible (DDR3)
        {"id": 7, "nombre": "RAM-DDR3", "tipo": "RAM", "socket": "", "tipo_ram": "DDR3", "marca":"Kingston", "modelo":"4GB"}
    ])
    componentes.to_csv("componentes.csv", index=False)

    # orden.csv vacío con cabeceras
    orden = pd.DataFrame(columns=["correo_usuario", "orden", "id", "nombre", "tipo", "marca", "modelo"])
    orden.to_csv("orden.csv", index=False)

    # eliminados.csv (vacío)
    pd.DataFrame(columns=["orden", "id", "nombre", "tipo", "marca", "modelo"]).to_csv("eliminados.csv", index=False)

    # montar la app con tu router
    app = FastAPI()
    # SessionMiddleware requerido porque tu código usa request.session
    app.add_middleware(SessionMiddleware, secret_key="testsecret")
    app.include_router(home.router)

    client = TestClient(app)
    yield client

    # cleanup (archivos creados en tmp_path serán borrados por pytest)

