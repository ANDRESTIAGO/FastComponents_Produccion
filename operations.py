from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.models import *
from datetime import datetime
from typing import List, Optional

async def crear_componente(comp: Componente, session: AsyncSession) -> Componente:
    session.add(comp)
    await session.commit()
    await session.refresh(comp)
    return comp

async def obtener_componentes(session: AsyncSession) -> List[Componente]:
    result = await session.exec(select(Componente))
    return result.all()

async def obtener_componente(id: int, session: AsyncSession) -> Optional[Componente]:
    return await session.get(Componente, id)

async def buscar_componente(tipo: str, modelo: str, session: AsyncSession) -> Optional[Componente]:
    result = await session.exec(select(Componente).where(Componente.tipo == tipo, Componente.modelo == modelo))
    return result.first()

async def actualizar_componente(id: int, datos: ComponenteActualizado, session: AsyncSession) -> Optional[Componente]:
    componente = await session.get(Componente, id)
    if not componente:
        return None
    for k, v in datos.dict(exclude_unset=True).items():
        setattr(componente, k, v)
    componente.fecha_modificacion = datetime.utcnow()
    session.add(componente)
    await session.commit()
    await session.refresh(componente)
    return componente

async def eliminar_componente(id: int, session: AsyncSession) -> Optional[Componente]:
    comp = await session.get(Componente, id)
    if not comp:
        return None
    await session.delete(comp)
    await session.commit()
    return comp

async def crear_distribuidor(distri: Distribuidores, session: AsyncSession) -> Distribuidores:
    session.add(distri)
    await session.commit()
    await session.refresh(distri)
    return distri

async def obtener_distribuidores(session: AsyncSession) -> List[Distribuidores]:
    result = await session.exec(select(Distribuidores))
    return result.all()

async def obtener_distribuidor(id: int, session: AsyncSession) -> Optional[Distribuidores]:
    return await session.get(Distribuidores, id)

async def buscar_distribuidor(nombre: str, session: AsyncSession) -> Optional[Distribuidores]:
    result = await session.exec(select(Distribuidores).where(Distribuidores.nombre == nombre))
    return result.first()

async def actualizar_distribuidor(id: int, datos: DistriActualizado, session: AsyncSession) -> Optional[Distribuidores]:
    distribuidor = await session.get(Distribuidores, id)
    if not distribuidor:
        return None
    for k, v in datos.dict(exclude_unset=True).items():
        setattr(distribuidor, k, v)
    session.add(distribuidor)
    await session.commit()
    await session.refresh(distribuidor)
    return distribuidor

async def eliminar_distribuidor(id: int, session: AsyncSession) -> Optional[Distribuidores]:
    dist = await session.get(Distribuidores, id)
    if not dist:
        return None
    await session.delete(dist)
    await session.commit()
    return dist
