from fastapi import APIRouter, Request, Form, Depends, HTTPException, FastAPI
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import pandas as pd
import pandas.errors
import numpy as np
from models import Componente, ComponenteActualizado, ComponenteConId, Orden
from operations.operations import create_user
from typing import Optional
from operations import operations   
from fastapi.responses import RedirectResponse
templates = Jinja2Templates(directory="templates")
router = APIRouter()
csv_file = "componentes.csv"
prueba_file = "pruebas.csv"
csv_eliminados = "eliminados.csv"

def get_current_user(request: Request):
    return request.session.get("correo")

@router.get("/homeAutenticacion", response_class=HTMLResponse)
async def ver_homeAutenticacion(request: Request):
    username = get_current_user(request)
    if not username:
        return RedirectResponse(url="/login", status_code=303)
    mensaje = request.session.pop("mensaje", None)
    return templates.TemplateResponse("homeAutenticacion.html", {"request": request, "mensaje": mensaje, "username": username})
@router.get("/home", response_class=HTMLResponse)
async def ver_homeAutenticacion(request: Request):
    mensaje = request.session.pop("mensaje", None)
    return templates.TemplateResponse("home.html", {"request": request, "mensaje": mensaje})

@router.get("/", response_class=HTMLResponse)
async def ver_home(request: Request):
    username = request.session.get("correo")  # obtiene usuario de la sesión
    if username:
        # Si ya está autenticado, mostrar el home autenticado
        return RedirectResponse(url="/homeAutenticacion", status_code=303)
    else:
        # Si no ha iniciado sesión, enviar al login
        return RedirectResponse(url="/home", status_code=303)

@router.get("/info", response_class=HTMLResponse)
async def leer_info(request:Request):
    username = get_current_user(request)
    if not username:
        return RedirectResponse(url="/login", status_code=303)
    
    csv_file = "componentes.csv"
    sesiones = pd.read_csv(csv_file)
    sesiones["id"] = sesiones.index
    lista = sesiones.to_dict(orient="records")
    return templates.TemplateResponse("info.html",{"request":request, "sesiones":lista, "titulo":"Datos en tabla"})

@router.get("/ver_eliminados", response_class=HTMLResponse)
async def ver_eliminados(request: Request):
    username = get_current_user(request)
    if not username:
        return RedirectResponse(url="/login", status_code=303)
    
    orden_file = "eliminados.csv"

    try:
        df = pd.read_csv(orden_file)
    except FileNotFoundError:
        df = pd.DataFrame(columns=["orden", "id", "nombre", "tipo", "marca", "modelo"])

    ordenes_agrupadas = {}
    for _, row in df.iterrows():
        nombre_orden = row["orden"]
        if nombre_orden not in ordenes_agrupadas:
            ordenes_agrupadas[nombre_orden] = []
        ordenes_agrupadas[nombre_orden].append(row.to_dict())

    return templates.TemplateResponse(
        "ver_eliminados.html",
        {"request": request, "ordenes": ordenes_agrupadas}
    )

@router.get("/comparacion", response_class=HTMLResponse)
async def mostrar_componentes(request: Request):
    username = get_current_user(request)
    if not username:
        return RedirectResponse(url="/login", status_code=303)
    
    csv_file = "componentes.csv"
    sesiones = pd.read_csv(csv_file)
    sesiones["id"] = sesiones.index  
    lista = sesiones.to_dict(orient="records")
    return templates.TemplateResponse(
        "comparacion.html",
        {"request": request, "sesiones": lista, "titulo": "Comparación de Componentes"}
    )

@router.post("/comparar", response_class=HTMLResponse)
async def comparar_componentes(request: Request, seleccionados: list[int] = Form(...)):

    username = get_current_user(request)
    if not username:
        return RedirectResponse(url="/login", status_code=303)
    csv_file = "componentes.csv"
    sesiones = pd.read_csv(csv_file)
    sesiones["id"] = sesiones.index

    seleccionados_df = sesiones[sesiones["id"].isin(seleccionados)]
    lista_seleccionados = seleccionados_df.to_dict(orient="records")

    return templates.TemplateResponse(
        "comparacion_seleccionada.html",
        {"request": request, "sesiones": lista_seleccionados, "titulo": "Componentes Seleccionados"}
    )

@router.get("/compatiblesi", response_class=HTMLResponse)
async def ver_componentes_compatibles(request: Request, socket: str, tipo_ram: Optional[str] = None):
    username = get_current_user(request)
    if not username:
        return RedirectResponse(url="/login", status_code=303)
    csv_file = "componentes.csv"
    df = pd.read_csv(csv_file)

    cpus = df[(df["tipo"] == "CPU") & (df["socket"] == socket)].to_dict(orient="records")
    ram = []
    if tipo_ram:
        ram = df[(df["tipo"] == "RAM") & (df["tipo_ram"] == tipo_ram)].to_dict(orient="records")
    gpus = df[df["tipo"] == "GPU"].to_dict(orient="records")
    fuentes = df[df["tipo"] == "Power Supply"].to_dict(orient="records")

    return templates.TemplateResponse(
        "compatibles.html",
        {"request": request, "cpus": cpus, "ram": ram, "gpus": gpus, "fuentes": fuentes}
    )

@router.get("/orden", response_class=HTMLResponse)
async def ver_orden(request: Request):
    username = get_current_user(request)
    if not username:
        return RedirectResponse(url="/login", status_code=303)
    
    orden_file = "orden.csv"

    try:
        orden = pd.read_csv(orden_file)
    except FileNotFoundError:
        orden = pd.DataFrame()

    if orden.empty:
        componentes = []
    else:
        componentes = orden.to_dict(orient="records")

    return templates.TemplateResponse(
        "orden.html", {"request": request, "componentes": componentes}
    )
#-----------------------------------------------------------------------------------------------------

@router.get("/add", response_class=HTMLResponse)
async def ver_add(request: Request, motherboard_id: int = None, nombre_orden: str = None):
    """
    Paso 1: si no hay motherboard seleccionada, muestra solo las placas madre.
    Paso 2: si se seleccionó una motherboard, filtra los componentes compatibles.
    """
    correo = get_current_user(request)
    if not correo:
        return RedirectResponse(url="/login", status_code=303)

    df = pd.read_csv("componentes.csv")

    #Paso 1: seleccionar la placa madre
    if motherboard_id is None:
        motherboards = df[df["tipo"] == "Motherboard"].to_dict(orient="records")
        return templates.TemplateResponse("add.html", {
            "request": request,
            "motherboards": motherboards,
            "nombre_orden": nombre_orden or "",
            "step": 1,
            "correo": correo
        })

    #Paso 2: ya se eligió una motherboard → filtrar componentes compatibles
    mb = df[df["id"] == motherboard_id].iloc[0]
    socket_mb = mb["socket"]
    tipo_ram_mb = mb["tipo_ram"]

    cpus = df[(df["tipo"] == "CPU") & (df["socket"] == socket_mb)].to_dict(orient="records")
    rams = df[(df["tipo"] == "RAM") & (df["tipo_ram"] == tipo_ram_mb)].to_dict(orient="records")
    gpus = df[df["tipo"] == "GPU"].to_dict(orient="records")
    discos = df[df["tipo"].isin(["HDD", "SSD"])].to_dict(orient="records")

    return templates.TemplateResponse("add.html", {
        "request": request,
        "motherboard_id": motherboard_id,
        "nombre_orden": nombre_orden or "",
        "motherboard": mb.to_dict(),
        "cpus": cpus,
        "rams": rams,
        "gpus": gpus,
        "discos": discos,
        "step": 2,
        "correo": correo
    })




@router.post("/add")
async def enviar_add(
    request: Request,
    nombre_orden: str = Form(...),
    motherboard_id: int = Form(...),
    cpu_id: int = Form(...),
    ram_id: int = Form(...),
    gpu_id: int = Form(...),
    disco_id: int = Form(...)
):
    correo = get_current_user(request)
    if not correo:
        return RedirectResponse(url="/login", status_code=303)

    df = pd.read_csv("componentes.csv")
    orden_file = "orden.csv"

    mb = df[df["id"] == motherboard_id].iloc[0]
    cpu = df[df["id"] == cpu_id].iloc[0]
    ram = df[df["id"] == ram_id].iloc[0]
    gpu = df[df["id"] == gpu_id].iloc[0]
    disco = df[df["id"] == disco_id].iloc[0]

    #Verificación de compatibilidad
    if cpu["socket"] != mb["socket"]:
        return RedirectResponse(url="/cpu-incompa", status_code=303)
    if "tipo_ram" in mb and "tipo_ram" in ram and ram["tipo_ram"] != mb["tipo_ram"]:
        return RedirectResponse(url="/ram-incompa", status_code=303)

    # Cargar archivo de órdenes
    try:
        orden = pd.read_csv(orden_file)
    except FileNotFoundError:
        orden = pd.DataFrame(columns=[
            "correo_usuario", "orden", "id", "nombre", "tipo", "marca", "modelo"
        ])

    #Agregar componentes seleccionados
    seleccionados = pd.DataFrame([
        {"correo_usuario": correo, "orden": nombre_orden, **mb.to_dict()},
        {"correo_usuario": correo, "orden": nombre_orden, **cpu.to_dict()},
        {"correo_usuario": correo, "orden": nombre_orden, **ram.to_dict()},
        {"correo_usuario": correo, "orden": nombre_orden, **gpu.to_dict()},
        {"correo_usuario": correo, "orden": nombre_orden, **disco.to_dict()}
    ])

    orden = pd.concat([orden, seleccionados], ignore_index=True)
    orden.to_csv(orden_file, index=False)

    return RedirectResponse(url="/ordenes", status_code=303)




@router.post("/add_con_usuario")
async def enviar_add_con_usuario(request: Request,
    nombre_orden: str = Form(...),
    motherboard_id: int = Form(...),
    cpu_id: int = Form(...),
    ram_id: int = Form(...),
    gpu_id: int = Form(...),
    disco_id: int = Form(...)
):
    # Verificar sesion
    username = get_current_user(request)
    if not username:
        return RedirectResponse(url="/login", status_code=303)

    df = pd.read_csv("componentes.csv")
    orden_file = ORDEN_CSV

    # buscar componentes por 'id' (si tu archivo componentes.csv no incluye 'id' debes adaptarlo)
    mb = df[df["id"] == motherboard_id].iloc[0]
    cpu = df[df["id"] == cpu_id].iloc[0]
    ram = df[df["id"] == ram_id].iloc[0]
    gpu = df[df["id"] == gpu_id].iloc[0]
    disco = df[df["id"] == disco_id].iloc[0]

    # compatibilidad (igual que antes)
    if cpu["socket"] != mb["socket"]:
        return RedirectResponse(url="/cpu-incompa", status_code=303)
    if "tipo_ram" in mb and "tipo_ram" in ram and ram["tipo_ram"] != mb["tipo_ram"]:
        return RedirectResponse(url="/ram-incompa", status_code=303)

    # asegurar orden.csv con columna 'usuario'
    try:
        orden = pd.read_csv(orden_file)
    except FileNotFoundError:
        orden = pd.DataFrame(columns=["usuario","orden", "id", "nombre", "tipo", "marca", "modelo"])

    seleccionados = pd.DataFrame([
        {"usuario": username, "orden": nombre_orden, **mb.to_dict()},
        {"usuario": username, "orden": nombre_orden, **cpu.to_dict()},
        {"usuario": username, "orden": nombre_orden, **ram.to_dict()},
        {"usuario": username, "orden": nombre_orden, **gpu.to_dict()},
        {"usuario": username, "orden": nombre_orden, **disco.to_dict()}
    ])

    orden = pd.concat([orden, seleccionados], ignore_index=True)
    orden.to_csv(orden_file, index=False)

    return RedirectResponse(url="/orden", status_code=303)

@router.get("/orden_usuario", response_class=HTMLResponse)
async def ver_orden_usuario(request: Request):
    username = get_current_user(request)
    if not username:
        return RedirectResponse(url="/login", status_code=303)

    orden_file = ORDEN_CSV
    try:
        df = pd.read_csv(orden_file)
    except FileNotFoundError:
        df = pd.DataFrame(columns=["usuario","orden", "id", "nombre", "tipo", "marca", "modelo"])

    # filtrar por usuario
    df_user = df[df["usuario"] == username]
    ordenes_agrupadas = {}
    for _, row in df_user.iterrows():
        nombre_orden = row["orden"]
        if nombre_orden not in ordenes_agrupadas:
            ordenes_agrupadas[nombre_orden] = []
        # convertir row a dict y quitar 'usuario' si no quieres mostrarlo
        d = row.to_dict()
        ordenes_agrupadas[nombre_orden].append(d)

    return templates.TemplateResponse("ordenes_usuario.html", {"request": request, "ordenes": ordenes_agrupadas})

@router.get("/cpu-incompa", response_class=HTMLResponse)
async def ver_cpu_incompa(request: Request):
    username = get_current_user(request)
    if not username:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse("cpu-incompa.html", {"request": request})

@router.get("/ram-incompa", response_class=HTMLResponse)
async def ver_ram_incompa(request: Request):
    username = get_current_user(request)
    if not username:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse("ram-incompa.html", {"request": request})

@router.get("/modificar", response_class=HTMLResponse)
async def ver_modificar_orden(request: Request):
    correo = get_current_user(request)
    if not correo:
        return RedirectResponse(url="/login", status_code=303)

    try:
        df_orden = pd.read_csv("orden.csv")
        df_componentes = pd.read_csv("componentes.csv")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="No se encontraron archivos de orden o componentes")

    # Filtrar solo las órdenes del usuario actual
    df_usuario = df_orden[df_orden["correo_usuario"] == correo]
    if df_usuario.empty:
        return templates.TemplateResponse("modificar_orden.html", {
            "request": request,
            "mensaje": "No tienes órdenes registradas aún.",
            "ordenes": [],
            "componentes_por_orden": {},
            "todos_componentes": []
        })

    # Agrupar componentes por orden
    ordenes = df_usuario["orden"].unique().tolist()
    componentes_por_orden = {}
    for nombre in ordenes:
        df_orden_actual = df_usuario[df_usuario["orden"] == nombre]

        # Identificar la motherboard de esa orden
        mb = df_orden_actual[df_orden_actual["tipo"] == "Motherboard"].iloc[0]
        socket_mb = mb["socket"]
        tipo_ram_mb = mb.get("tipo_ram", None)

        # Filtrar componentes compatibles con esta motherboard
        compatibles = {
            "CPU": df_componentes[(df_componentes["tipo"] == "CPU") & (df_componentes["socket"] == socket_mb)],
            "RAM": df_componentes[
                (df_componentes["tipo"] == "RAM")
                & (df_componentes["tipo_ram"] == tipo_ram_mb)
            ],
            "GPU": df_componentes[df_componentes["tipo"] == "GPU"],
            "HDD": df_componentes[df_componentes["tipo"].isin(["HDD", "SSD"])],
            "SSD": df_componentes[df_componentes["tipo"].isin(["HDD", "SSD"])],
            "Power Supply": df_componentes[df_componentes["tipo"] == "Power Supply"],
        }

        componentes_por_orden[nombre] = {
            "componentes_actuales": df_orden_actual.to_dict(orient="records"),
            "compatibles": {k: v.to_dict(orient="records") for k, v in compatibles.items()}
        }

    return templates.TemplateResponse("modificar_orden.html", {
        "request": request,
        "ordenes": ordenes,
        "componentes_por_orden": componentes_por_orden,
        "correo": correo
    })



@router.post("/modificar", response_class=HTMLResponse)
async def aplicar_modificacion(
    request: Request,
    orden: str = Form(...),
    componente_id_original: int = Form(...),
    nuevo_id: int = Form(...)
):
    correo = get_current_user(request)
    if not correo:
        return RedirectResponse(url="/login", status_code=303)

    df_orden = pd.read_csv("orden.csv")
    df_componentes = pd.read_csv("componentes.csv")

    #Verificar que la orden pertenece al usuario
    df_usuario = df_orden[df_orden["correo_usuario"] == correo]
    if orden not in df_usuario["orden"].values:
        raise HTTPException(status_code=403, detail="No tienes permiso para modificar esta orden.")

    # Obtener la placa madre de esa orden
    orden_actual = df_usuario[df_usuario["orden"] == orden]
    mb = orden_actual[orden_actual["tipo"] == "Motherboard"].iloc[0]
    socket_mb = mb["socket"]
    tipo_ram_mb = mb.get("tipo_ram", None)

    # Componente original
    original = orden_actual[orden_actual["id"] == componente_id_original]
    if original.empty:
        raise HTTPException(status_code=404, detail="Componente original no encontrado.")
    tipo_original = original.iloc[0]["tipo"]

    # Nuevo componente
    nuevo = df_componentes[df_componentes["id"] == nuevo_id]
    if nuevo.empty:
        raise HTTPException(status_code=404, detail="Nuevo componente no encontrado.")
    tipo_nuevo = nuevo.iloc[0]["tipo"]

    #No se puede cambiar la placa madre
    if tipo_original == "Motherboard":
        raise HTTPException(status_code=400, detail="No puedes modificar la placa madre de la orden.")

    #Validación de tipo
    # Permitir intercambio HDD <-> SSD, pero exigir mismo tipo para los demás
    if not (
        (tipo_original in ["HDD", "SSD"] and tipo_nuevo in ["HDD", "SSD"])
        or tipo_original == tipo_nuevo
    ):
        raise HTTPException(status_code=400, detail="Solo puedes cambiar componentes del mismo tipo (excepto HDD ↔ SSD).")

    # 🧩 Validar compatibilidad según el tipo
    if tipo_nuevo == "CPU" and nuevo.iloc[0]["socket"] != socket_mb:
        raise HTTPException(status_code=400, detail="El CPU seleccionado no es compatible con la placa madre.")
    if tipo_nuevo == "RAM" and tipo_ram_mb and nuevo.iloc[0]["tipo_ram"] != tipo_ram_mb:
        raise HTTPException(status_code=400, detail="La RAM seleccionada no es compatible con la placa madre.")

    #plicar el cambio en el CSV
    index = df_orden[
        (df_orden["orden"] == orden)
        & (df_orden["id"] == componente_id_original)
        & (df_orden["correo_usuario"] == correo)
    ].index

    for col in nuevo.columns:
        df_orden.loc[index, col] = nuevo.iloc[0][col]

    df_orden.to_csv("orden.csv", index=False)

    return RedirectResponse(url="/ordenes", status_code=303)





@router.get("/eliminar", response_class=HTMLResponse)
async def mostrar_ordenes_para_eliminar(request: Request):
    correo = get_current_user(request)
    if not correo:
        return RedirectResponse(url="/login", status_code=303)

    try:
        df = pd.read_csv("orden.csv")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="No hay órdenes registradas")

    # Filtrar solo las órdenes del usuario logueado
    df_usuario = df[df["correo_usuario"] == correo]

    if df_usuario.empty:
        return templates.TemplateResponse("eliminar.html", {
            "request": request,
            "ordenes": [],
            "mensaje": "No tienes órdenes registradas para eliminar."
        })

    nombres_ordenes = df_usuario["orden"].unique().tolist()

    return templates.TemplateResponse("eliminar.html", {
        "request": request,
        "ordenes": nombres_ordenes
    })


@router.post("/eliminar", response_class=HTMLResponse)
async def mover_orden_a_eliminados(request: Request, orden: str = Form(...)):
    correo = get_current_user(request)
    if not correo:
        return RedirectResponse(url="/login", status_code=303)

    orden_file = "orden.csv"
    eliminados_file = "eliminados.csv"

    try:
        df = pd.read_csv(orden_file)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="No hay órdenes registradas")

    #Verificar que la orden pertenezca al usuario
    filas_usuario = df[(df["orden"] == orden) & (df["correo_usuario"] == correo)]
    if filas_usuario.empty:
        raise HTTPException(status_code=403, detail="No tienes permiso para eliminar esta orden.")

    #Mover las filas del usuario a eliminados.csv
    try:
        df_eliminados = pd.read_csv(eliminados_file)
        df_eliminados = pd.concat([df_eliminados, filas_usuario], ignore_index=True)
    except (FileNotFoundError, pd.errors.EmptyDataError):
        df_eliminados = filas_usuario.copy()

    df_eliminados.to_csv(eliminados_file, index=False)

    #Eliminar solo las filas del usuario y esa orden
    df = df[~((df["orden"] == orden) & (df["correo_usuario"] == correo))]
    df.to_csv(orden_file, index=False)

    return RedirectResponse(url="/ordenes", status_code=303)



@router.get("/menu", response_class=HTMLResponse)
async def ver_menu(request: Request):
    username = get_current_user(request)
    if not username:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse("menu.html", {"request": request})

@router.get("/ordenes", response_class=HTMLResponse)
async def ver_ordenes(request: Request):

    correo = get_current_user(request)
    if not correo:
        return RedirectResponse(url="/login", status_code=303)

    orden_file = "orden.csv"

    try:
        df = pd.read_csv(orden_file)
    except FileNotFoundError:
        df = pd.DataFrame(columns=[
            "correo_usuario", "orden", "id", "nombre", "tipo", "marca", "modelo"
        ])

    df_usuario = df[df["correo_usuario"] == correo]


    ordenes_agrupadas = {}
    for _, row in df_usuario.iterrows():
        nombre_orden = row["orden"]
        if nombre_orden not in ordenes_agrupadas:
            ordenes_agrupadas[nombre_orden] = []
        ordenes_agrupadas[nombre_orden].append(row.to_dict())


    return templates.TemplateResponse(
        "orden.html",
        {
            "request": request,
            "ordenes": ordenes_agrupadas,
            "correo": correo, 
        }
    )


#----------------------LOGIN-----------------------
@router.get("/registro", response_class=HTMLResponse)
async def ver_registro(request: Request):
    return templates.TemplateResponse("registro.html", {"request": request})

@router.post("/registro")
async def procesar_registro(request: Request,
                            nombre_usuario: str = Form(...),
                            correo: str = Form(...),
                            contraseña: str = Form(...),
                            contraseña2: str = Form(...)):
    # validaciones simples
    if contraseña != contraseña2:
        return templates.TemplateResponse("registro.html", {"request": request, "error": "Las contraseñas no coinciden."})
    try:
        create_user(nombre_usuario.strip(), correo.strip(), contraseña)
    except ValueError as e:
        return templates.TemplateResponse("registro.html", {"request": request, "error": str(e)})
    # auto-login tras registro
    request.session["correo"] = correo.strip()
    request.session["mensaje"] = "Se registro correctamente"
    return RedirectResponse(url="/homeAutenticacion", status_code=303)

@router.get("/login", response_class=HTMLResponse)
async def ver_login(request: Request):
    # si ya está logueado, redirige al home autenticado
    if get_current_user(request):
        return RedirectResponse(url="/homeAutenticacion", status_code=303)
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
async def procesar_login(request: Request, correo: str = Form(...), contraseña: str = Form(...)):
    usuario = get_user_by_username(correo.strip())
    if not usuario:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Correo o contraseña incorrectos."})
    if not verify_password(contraseña, usuario["contraseña_hash"]):
        return templates.TemplateResponse("login.html", {"request": request, "error": "Correo o contraseña incorrectos."})
    # guardar sesión
    request.session["correo"] = correo.strip()
    return RedirectResponse(url="/homeAutenticacion", status_code=303)

@router.get("/logout")
async def logout(request: Request):

    request.session.pop("correo", None)
    request.session["mensaje"] = "Session cerrada correctamente"
    return RedirectResponse(url="/home", status_code=303)

@router.get("/cambiar_contraseña", response_class=HTMLResponse)
async def ver_cambiar_contrasena(request: Request):
    if not get_current_user(request):
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse("cambiar_contraseña.html", {"request": request})

@router.post("/cambiar_contraseña")
async def procesar_cambiar_contrasena(request: Request,
                                     current_password: str = Form(...),
                                     new_password: str = Form(...),
                                     new_password2: str = Form(...)):
    username = get_current_user(request)
    if not username:
        return RedirectResponse(url="/login", status_code=303)
    user = get_user_by_username(username)
    if not verify_password(current_password, user["contraseña_hash"]):
        return templates.TemplateResponse("cambiar_contraseña.html", {"request": request, "error": "La contraseña actual es incorrecta."})
    if new_password != new_password2:
        return templates.TemplateResponse("cambiar_contraseña.html", {"request": request, "error": "Las contraseñas nuevas no coinciden."})
    update_user_password(username, new_password)
    return templates.TemplateResponse("cambiar_contraseña.html", {"request": request, "success": "Contraseña actualizada correctamente."})
