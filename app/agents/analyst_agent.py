from crewai import Agent
from crewai_tools import tool


@tool("analizar_perfil_empresa")
def analizar_perfil_empresa(datos_empresa: str) -> str:
    """
    Analiza los datos de una empresa y determina su perfil:
    actividad principal, tamano estimado, zona de actuacion
    y argumentos de venta relevantes para ORESNA.
    """
    return f"""
Analiza la siguiente empresa para orientar la propuesta comercial de ORESNA:

{datos_empresa}

Determina:
1. Tipo de empresa y actividad principal
2. Tamano estimado (micropyme / pyme / empresa mediana)
3. Zona de actuacion en Navarra
4. Tipo de clientes que atiende habitualmente
5. Puntos de sinergia concretos con ORESNA Inmobiliaria
6. Tono recomendado para el email: formal o cercano
7. Dato especifico de la empresa para personalizar el primer parrafo
"""


@tool("clasificar_prioridad_contacto")
def clasificar_prioridad_contacto(perfil_empresa: str) -> str:
    """
    Clasifica la prioridad del contacto como ALTA, MEDIA o BAJA
    segun el perfil analizado.
    ALTA: activa en Navarra, email disponible, relacion directa con inmuebles.
    MEDIA: potencial indirecto o sin email confirmado.
    BAJA: fuera de zona, actividad muy alejada o datos incompletos.
    """
    return f"""
Clasifica la prioridad de contacto segun este perfil:

{perfil_empresa}

- ALTA: empresa activa, email disponible, relacion directa con compraventa o reforma
- MEDIA: potencial de derivacion pero conexion indirecta
- BAJA: micropyme sin email, fuera de zona o actividad muy alejada

Justifica brevemente la clasificacion.
"""


def crear_agente_analista(llm) -> Agent:
    return Agent(
        role="Analista de perfil empresarial y estrategia comercial",
        goal=(
            "Analizar cada empresa encontrada por el agente rastreador. "
            "Entender su actividad, tamano y potencial de colaboracion con ORESNA. "
            "Clasificar los contactos por prioridad y definir el enfoque del email."
        ),
        backstory=(
            "Llevas anos como consultor comercial en el sector inmobiliario de Navarra. "
            "Conoces bien como funcionan las constructoras locales y los negocios de servicios. "
            "Sabes que argumentos funcionan con cada tipo de empresa y como adaptar el mensaje."
        ),
        tools=[analizar_perfil_empresa, clasificar_prioridad_contacto],
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=3,
    )
