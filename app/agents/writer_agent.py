from crewai import Agent
from crewai_tools import tool
from app.core.config import config


@tool("redactar_email_constructora")
def redactar_email_constructora(perfil_empresa: str, datos_contacto: str) -> str:
    """
    Redacta un email comercial personalizado para una constructora o promotora en Navarra.
    El email propone a ORESNA como la inmobiliaria de referencia para vender sus inmuebles.
    Sigue las mejores practicas de email comercial B2B: asunto atractivo, cuerpo conciso,
    propuesta de valor clara y CTA especifico.
    """
    return f"""
Redacta un email comercial profesional y personalizado en castellano para la siguiente empresa constructora.

DATOS DE LA EMPRESA:
{datos_contacto}

PERFIL ANALIZADO:
{perfil_empresa}

INFORMACION DE ORESNA:
- Nombre: {config.EMPRESA_NOMBRE}
- Zona: {config.EMPRESA_ZONA}
- Web: {config.EMPRESA_WEB}
- Telefono: {config.EMPRESA_TELEFONO}

INSTRUCCIONES ESTRICTAS:
1. Escribe UN asunto del email (maximo 8 palabras, con dato especifico de la empresa)
2. Escribe el cuerpo del email en HTML limpio (parrafos <p>, sin CSS inline)
3. El email debe tener MAXIMO 180 palabras en el cuerpo
4. Menciona un dato especifico de la empresa en el primer parrafo (localidad, tipo de obra o nombre)
5. Propuesta de valor: ORESNA se encarga de vender/alquilar los inmuebles que ellos construyen
6. CTA claro: proponer una llamada o reunion breve (15 minutos)
7. Tono: profesional pero cercano, directo, sin florituras
8. NO uses frases genericas como "Me pongo en contacto" o "Espero que este email le encuentre bien"

FORMATO DE RESPUESTA (sigue exactamente este formato):
ASUNTO: [asunto aqui]
---
CUERPO_HTML:
[cuerpo HTML aqui]
"""


@tool("redactar_email_alianza")
def redactar_email_alianza(perfil_empresa: str, datos_contacto: str) -> str:
    """
    Redacta una propuesta de alianza B2B para empresas de reformas, mudanzas, gestorias u otras.
    Propone un acuerdo de derivacion mutua de clientes, 100% legal y sin coste.
    """
    return f"""
Redacta un email de propuesta de alianza comercial para la siguiente empresa.

DATOS DE LA EMPRESA:
{datos_contacto}

PERFIL ANALIZADO:
{perfil_empresa}

INFORMACION DE ORESNA:
- Nombre: {config.EMPRESA_NOMBRE}
- Zona: {config.EMPRESA_ZONA}
- Web: {config.EMPRESA_WEB}
- Telefono: {config.EMPRESA_TELEFONO}

INSTRUCCIONES ESTRICTAS:
1. Escribe UN asunto del email (maximo 8 palabras, menciona "alianza" o "colaboracion")
2. Escribe el cuerpo en HTML limpio (parrafos <p>, sin CSS inline)
3. El email debe tener MAXIMO 160 palabras
4. Empieza reconociendo la actividad de la empresa (reformas/mudanzas/etc.) con un dato especifico
5. Explica la sinergia: sus clientes compran/venden casas; ORESNA puede ayudarles
6. Propuesta concreta: derivacion mutua sin coste, sin exclusividad, sin compromiso
7. CTA: una llamada de 10 minutos para explorar la colaboracion
8. Tono: entre colegas del sector, colaborativo, sin presion comercial
9. NO hagas referencia a competencia ni menciones precios ni comisiones

FORMATO DE RESPUESTA (sigue exactamente este formato):
ASUNTO: [asunto aqui]
---
CUERPO_HTML:
[cuerpo HTML aqui]
"""


def crear_agente_redactor(llm) -> Agent:
    return Agent(
        role="Redactor Comercial Especializado en B2B Inmobiliario",
        goal=(
            "Redactar emails comerciales que consigan respuesta. "
            "Cada email debe ser unico, hiper-personalizado y con propuesta de valor clara. "
            "Para constructoras: ofrecer a ORESNA como canal de ventas de sus inmuebles. "
            "Para alianzas: proponer derivacion mutua de clientes de forma natural y atractiva."
        ),
        backstory=(
            "Especializado en ventas B2B para el sector inmobiliario. "
            "Con experiencia en emails comerciales con altas tasas de apertura. "
            "Cada email parece escrito a mano, nunca generico. Siempre menciona "
            "algo especifico de la empresa destinataria en las primeras lineas. "
            "Los emails son cortos, directos y con un unico CTA claro."
        ),
        tools=[redactar_email_constructora, redactar_email_alianza],
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=2,
    )


def parsear_respuesta_email(respuesta_ia: str) -> dict:
    import re

    asunto = ""
    cuerpo_html = ""

    match_asunto = re.search(r"ASUNTO:\s*(.+?)(?:\n|---)", respuesta_ia, re.DOTALL)
    if match_asunto:
        asunto = match_asunto.group(1).strip()

    match_cuerpo = re.search(r"CUERPO_HTML:\s*(.+)", respuesta_ia, re.DOTALL)
    if match_cuerpo:
        cuerpo_html = match_cuerpo.group(1).strip()

    if not asunto:
        asunto = "Propuesta de colaboracion — ORESNA Inmobiliaria"
    if not cuerpo_html:
        cuerpo_html = f"<p>{respuesta_ia}</p>"

    return {"asunto": asunto, "cuerpo_html": cuerpo_html}
