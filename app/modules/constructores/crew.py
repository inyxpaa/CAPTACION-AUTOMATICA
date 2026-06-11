"""
ORESNA CAPTADOR — Pipeline multi-agente para Módulo 1: Constructoras
Orquesta los tres agentes de IA para buscar, analizar y redactar
emails personalizados para constructoras en Navarra.
"""

from crewai import Crew, Task, Process
from crewai import LLM
from loguru import logger
from datetime import datetime

from app.core.config import config
from app.core.db import db_session, Contacto, Campana
from app.core.email_service import email_service, plantilla_constructora
from app.agents.scraper_agent import crear_agente_rastreador
from app.agents.analyst_agent import crear_agente_analista
from app.agents.writer_agent import crear_agente_redactor, parsear_respuesta_email


def crear_llm():
    """Crea el LLM usando el wrapper nativo de CrewAI 1.x."""
    if config.LLM_PROVIDER == "openai":
        return LLM(
            model=f"openai/{config.LLM_MODEL}",
            api_key=config.OPENAI_API_KEY,
            temperature=0.7,
        )
    else:
        return LLM(
            model=f"groq/{config.LLM_MODEL}",
            api_key=config.GROQ_API_KEY,
            temperature=0.7,
        )


def ejecutar_pipeline_constructoras(
    localidad: str = "Navarra",
    enviar_emails: bool = False,
    nombre_campana: str = "",
    callback_progreso=None,
) -> dict:
    """
    Ejecuta el pipeline completo para el módulo de constructoras.
    
    Args:
        localidad: Zona geográfica a rastrear
        enviar_emails: Si True, envía los emails generados
        nombre_campana: Nombre para la campaña en BD
        callback_progreso: Función llamada con (paso, mensaje) para actualizar UI
    
    Returns:
        dict con resultados: contactos guardados, emails generados, errores
    """
    resultados = {
        "contactos_encontrados": 0,
        "contactos_guardados": 0,
        "emails_generados": 0,
        "emails_enviados": 0,
        "errores": [],
        "contactos": [],
        "campana_id": None,
    }

    def progreso(paso: str, mensaje: str):
        logger.info(f"[{paso}] {mensaje}")
        if callback_progreso:
            callback_progreso(paso, mensaje)

    try:
        # ── 1. Crear LLM y agentes ──────────────────────────────────────────
        progreso("INICIO", f"Iniciando pipeline de constructoras en {localidad}")
        llm = crear_llm()
        agente_rastreador = crear_agente_rastreador(llm)
        agente_analista = crear_agente_analista(llm)
        agente_redactor = crear_agente_redactor(llm)

        # ── 2. Definir tareas ───────────────────────────────────────────────
        tarea_rastreo = Task(
            description=f"""
            Busca constructoras y promotoras inmobiliarias activas en {localidad}.
            Usa la herramienta buscar_constructoras_navarra para obtener la lista.
            Devuelve todos los datos disponibles de cada empresa: nombre, email, web, teléfono, localidad.
            Localidad objetivo: {localidad}
            """,
            expected_output="Lista estructurada de constructoras con todos sus datos de contacto disponibles",
            agent=agente_rastreador,
        )

        tarea_analisis = Task(
            description="""
            Analiza cada una de las constructoras encontradas por el Agente Rastreador.
            Para cada empresa:
            1. Determina el tipo de obra que realizan
            2. Estima el tamaño de la empresa
            3. Identifica puntos de sinergia con ORESNA Inmobiliaria
            4. Asigna una prioridad de contacto (ALTA/MEDIA/BAJA)
            5. Define el tono del email (formal o cercano)
            Devuelve un análisis detallado por empresa.
            """,
            expected_output="Análisis detallado de cada empresa con perfil, prioridad y estrategia de contacto",
            agent=agente_analista,
            context=[tarea_rastreo],
        )

        tarea_redaccion = Task(
            description="""
            Para cada empresa analizada (especialmente las de prioridad ALTA y MEDIA),
            redacta un email comercial personalizado usando la herramienta redactar_email_constructora.
            
            Reglas importantes:
            - Máximo 180 palabras por email
            - El asunto debe incluir algo específico de la empresa
            - Menciona la localidad o el tipo de obra en el primer párrafo
            - CTA: proponer una llamada de 15 minutos
            - Devuelve el email en formato: ASUNTO: ... / CUERPO_HTML: ...
            """,
            expected_output="Email personalizado por cada empresa con ASUNTO y CUERPO_HTML claramente separados",
            agent=agente_redactor,
            context=[tarea_rastreo, tarea_analisis],
        )

        # ── 3. Ejecutar Crew ────────────────────────────────────────────────
        progreso("AGENTES", "Ejecutando pipeline de agentes IA...")
        crew = Crew(
            agents=[agente_rastreador, agente_analista, agente_redactor],
            tasks=[tarea_rastreo, tarea_analisis, tarea_redaccion],
            process=Process.sequential,
            verbose=config.IS_DEV,
        )

        resultado_crew = crew.kickoff()
        progreso("AGENTES", "Pipeline de agentes completado ✅")

        # ── 4. Extraer y guardar contactos en BD ────────────────────────────
        progreso("BD", "Guardando contactos en base de datos...")

        # Obtener los datos del rastreo (primer task)
        from app.modules.constructores.scraper import ConstructoraScraper
        scraper = ConstructoraScraper()
        empresas_raw = scraper.buscar(localidad=localidad)
        resultados["contactos_encontrados"] = len(empresas_raw)

        contactos_bd = []
        with db_session() as db:
            # Crear campaña si se van a enviar emails
            campana = None
            if enviar_emails:
                campana = Campana(
                    nombre=nombre_campana or f"Constructoras {localidad} {datetime.now().strftime('%d/%m/%Y')}",
                    modulo="constructores",
                    descripcion=f"Campaña automática — {localidad}",
                )
                db.add(campana)
                db.flush()
                resultados["campana_id"] = campana.id

            for empresa_data in empresas_raw:
                # Verificar si ya existe
                existente = db.query(Contacto).filter(
                    Contacto.email == empresa_data.get("email"),
                    Contacto.empresa == empresa_data.get("empresa"),
                ).first()

                if existente:
                    logger.debug(f"  Contacto ya existe: {empresa_data.get('empresa')}")
                    continue

                contacto = Contacto(
                    nombre=empresa_data.get("nombre") or empresa_data.get("empresa", ""),
                    empresa=empresa_data.get("empresa", ""),
                    email=empresa_data.get("email", ""),
                    telefono=empresa_data.get("telefono", ""),
                    web=empresa_data.get("web", ""),
                    localidad=empresa_data.get("localidad", localidad),
                    descripcion=empresa_data.get("descripcion", ""),
                    modulo="constructores",
                    tipo_empresa=empresa_data.get("tipo_empresa", "Constructora"),
                    fuente=empresa_data.get("fuente", ""),
                    estado="nuevo",
                )
                db.add(contacto)
                db.flush()
                contactos_bd.append(contacto)
                resultados["contactos_guardados"] += 1

        resultados["contactos"] = [
            {"empresa": c.empresa, "email": c.email, "localidad": c.localidad}
            for c in contactos_bd
        ]
        progreso("BD", f"{resultados['contactos_guardados']} contactos nuevos guardados")

        # ── 5. Generar y enviar emails ──────────────────────────────────────
        if enviar_emails and contactos_bd:
            progreso("EMAIL", f"Generando y enviando emails a {len(contactos_bd)} contactos...")
            
            # Parsear email generado por la IA (último resultado del crew)
            email_ia = parsear_respuesta_email(str(resultado_crew))
            
            with db_session() as db:
                for contacto in contactos_bd:
                    if not contacto.email:
                        continue

                    # Construir HTML completo con plantilla
                    html_final = plantilla_constructora(
                        nombre_empresa=contacto.empresa,
                        tipo_obra=contacto.tipo_empresa or "Construcción",
                        localidad=contacto.localidad or localidad,
                        cuerpo_ia=email_ia["cuerpo_html"],
                    )

                    contacto_db = db.get(Contacto, contacto.id)
                    if contacto_db:
                        res = email_service.enviar_email(
                            contacto=contacto_db,
                            asunto=email_ia["asunto"],
                            cuerpo_html=html_final,
                            campana_id=resultados.get("campana_id"),
                        )
                        if res["exito"]:
                            resultados["emails_enviados"] += 1
                        else:
                            resultados["errores"].append(
                                f"{contacto.empresa}: {res['mensaje']}"
                            )

            resultados["emails_generados"] = len(contactos_bd)
            progreso("EMAIL", f"{resultados['emails_enviados']} emails enviados ✅")

    except Exception as e:
        logger.error(f"Error en pipeline de constructoras: {e}")
        resultados["errores"].append(str(e))

    return resultados
