from crewai import Agent
from crewai_tools import tool
from loguru import logger
from typing import Optional, Any
from app.core.config import config


@tool("buscar_constructoras_navarra")
def buscar_constructoras_navarra(localidad: str = "Navarra") -> str:
    """
    Busca constructoras activas en Navarra consultando paginas web publicas.
    Devuelve una lista de empresas con sus datos de contacto.
    """
    from app.modules.constructores.scraper import ConstructoraScraper
    scraper = ConstructoraScraper()
    resultados = scraper.buscar(localidad=localidad, max_resultados=config.MAX_CONTACTOS)
    if not resultados:
        return "No se encontraron constructoras en esta busqueda."

    texto = f"Constructoras encontradas en {localidad}:\n\n"
    for i, empresa in enumerate(resultados, 1):
        texto += f"{i}. {empresa.get('empresa', 'N/D')}\n"
        texto += f"   Email: {empresa.get('email', 'N/D')}\n"
        texto += f"   Web: {empresa.get('web', 'N/D')}\n"
        texto += f"   Localidad: {empresa.get('localidad', 'N/D')}\n"
        texto += f"   Descripcion: {empresa.get('descripcion', 'N/D')}\n\n"
    return texto


@tool("buscar_empresas_aliadas")
def buscar_empresas_aliadas(tipo: str = "reformas", localidad: str = "Navarra") -> str:
    """
    Busca empresas de reformas, mudanzas, gestorias u otras en Navarra.
    El tipo puede ser: reformas, mudanzas, gestoria, abogados.
    Devuelve datos de contacto estructurados.
    """
    from app.modules.alianzas.scraper import AlianzaScraper
    scraper = AlianzaScraper()
    resultados = scraper.buscar(tipo=tipo, localidad=localidad, max_resultados=config.MAX_CONTACTOS)
    if not resultados:
        return f"No se encontraron empresas de {tipo} en {localidad}."

    texto = f"Empresas de {tipo} encontradas en {localidad}:\n\n"
    for i, empresa in enumerate(resultados, 1):
        texto += f"{i}. {empresa.get('empresa', 'N/D')}\n"
        texto += f"   Email: {empresa.get('email', 'N/D')}\n"
        texto += f"   Web: {empresa.get('web', 'N/D')}\n"
        texto += f"   Telefono: {empresa.get('telefono', 'N/D')}\n"
        texto += f"   Localidad: {empresa.get('localidad', 'N/D')}\n\n"
    return texto


def crear_agente_rastreador(llm: Any) -> Agent:
    return Agent(
        role="Especialista en busqueda y extraccion de datos empresariales",
        goal=(
            "Localizar datos completos de constructoras y empresas aliadas en Navarra "
            "para la inmobiliaria ORESNA. Prioriza empresas con email de contacto disponible."
        ),
        backstory=(
            "Llevas anos investigando el tejido empresarial de Navarra. Conoces bien "
            "el sector de la construccion y los servicios afines. Tu trabajo es encontrar "
            "exactamente las empresas que ORESNA necesita contactar con datos completos y verificables."
        ),
        tools=[buscar_constructoras_navarra, buscar_empresas_aliadas],
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=3,
    )
