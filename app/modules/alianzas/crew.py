"""
ORESNA CAPTADOR — Pipeline multi-agente para Módulo 2: Alianzas B2B
Orquesta los agentes de IA para encontrar y contactar empresas
de reformas, mudanzas y gestorías para propuestas de alianza.
"""

from crewai import Crew, Task, Process
from loguru import logger
from datetime import datetime

from app.core.config import config
from app.core.db import db_session, Contacto, Campana
from app.core.email_service import email_service, plantilla_alianza
from app.agents.scraper_agent import crear_agente_rastreador
from app.agents.analyst_agent import crear_agente_analista
from app.agents.writer_agent import crear_agente_redactor, parsear_respuesta_email
from app.modules.constructores.crew import crear_llm


TIPOS_EMPRESA_ALIANZA = ["reformas", "mudanzas", "gestoria", "abogados"]


def ejecutar_pipeline_alianzas(
    tipos: list[str] = None,
    localidad: str = "Navarra",
    enviar_emails: bool = False,
    nombre_campana: str = "",
    callback_progreso=None,
) -> dict:
    """
    Ejecuta el pipeline de alianzas B2B.
    
    Args:
        tipos: Lista de tipos de empresa a rastrear. Default: todos.
        localidad: Zona geográfica
        enviar_emails: Si True, envía propuestas de alianza
        nombre_campana: Nombre de la campaña
        callback_progreso: Función para actualizar progreso en UI
    
    Returns:
        dict con estadísticas del resultado
    """
    if tipos is None:
        tipos = TIPOS_EMPRESA_ALIANZA

    resultados = {
        "contactos_encontrados": 0,
        "contactos_guardados": 0,
        "emails_generados": 0,
        "emails_enviados": 0,
        "errores": [],
        "contactos": [],
        "campana_id": None,
        "por_tipo": {},
    }

    def progreso(paso: str, mensaje: str):
        logger.info(f"[{paso}] {mensaje}")
        if callback_progreso:
            callback_progreso(paso, mensaje)

    try:
        progreso("INICIO", f"Iniciando pipeline de alianzas B2B en {localidad}")
        llm = crear_llm()
        agente_rastreador = crear_agente_rastreador(llm)
        agente_analista = crear_agente_analista(llm)
        agente_redactor = crear_agente_redactor(llm)

        tipos_str = ", ".join(tipos)

        tarea_rastreo = Task(
            description=f"""
            Busca empresas aliadas en {localidad} de los siguientes tipos: {tipos_str}.
            
            Para cada tipo, usa la herramienta buscar_empresas_aliadas con el tipo correspondiente.
            Obtén datos de contacto completos: nombre empresa, email, teléfono, web, localidad.
            
            Tipos a rastrear: {tipos_str}
            Localidad: {localidad}
            """,
            expected_output="Lista completa de empresas aliadas con datos de contacto por tipo de empresa",
            agent=agente_rastreador,
        )

        tarea_analisis = Task(
            description="""
            Analiza cada empresa aliada encontrada:
            1. Confirma que es una empresa (no un particular) — esto es crucial para RGPD
            2. Evalúa el potencial de sinergia con ORESNA:
               - Reformas: sus clientes suelen estar en proceso de compraventa
               - Mudanzas: sus clientes están cambiando de domicilio
               - Gestorías: manejan carteras de propietarios
               - Abogados: gestionan herencias y divorcios con inmuebles
            3. Clasifica prioridad: ALTA / MEDIA / BAJA
            4. Define el argumento de sinergia más relevante por tipo
            """,
            expected_output="Análisis de potencial de alianza con argumento de sinergia personalizado por empresa",
            agent=agente_analista,
            context=[tarea_rastreo],
        )

        tarea_redaccion = Task(
            description="""
            Para las empresas de prioridad ALTA y MEDIA, redacta propuestas de alianza B2B
            usando la herramienta redactar_email_alianza.
            
            La propuesta debe ser:
            - Breve (máximo 160 palabras)
            - Mencionar el tipo de actividad específico de la empresa
            - Explicar la sinergia con ejemplos concretos según el tipo:
              * Reformas: "Cuando un cliente nuestro compra piso, necesita reformarlo"
              * Mudanzas: "Cada compraventa genera una mudanza"
              * Gestorías: "Coordinamos gestiones fiscales de nuestros clientes"
            - Proponer derivación mutua sin coste ni exclusividad
            - CTA: llamada de 10 minutos
            
            Formato requerido: ASUNTO: ... / CUERPO_HTML: ...
            """,
            expected_output="Propuesta de alianza personalizada por cada empresa con ASUNTO y CUERPO_HTML",
            agent=agente_redactor,
            context=[tarea_rastreo, tarea_analisis],
        )

        # Ejecutar Crew
        progreso("AGENTES", "Ejecutando pipeline de agentes IA...")
        crew = Crew(
            agents=[agente_rastreador, agente_analista, agente_redactor],
            tasks=[tarea_rastreo, tarea_analisis, tarea_redaccion],
            process=Process.sequential,
            verbose=config.IS_DEV,
        )
        resultado_crew = crew.kickoff()
        progreso("AGENTES", "Pipeline completado ✅")

        # Guardar contactos en BD
        progreso("BD", "Guardando empresas aliadas en base de datos...")
        from app.modules.alianzas.scraper import AlianzaScraper
        scraper = AlianzaScraper()

        todas_empresas = []
        for tipo in tipos:
            empresas_tipo = scraper.buscar(tipo=tipo, localidad=localidad)
            resultados["por_tipo"][tipo] = len(empresas_tipo)
            todas_empresas.extend(empresas_tipo)

        resultados["contactos_encontrados"] = len(todas_empresas)
        contactos_bd = []

        with db_session() as db:
            campana = None
            if enviar_emails:
                campana = Campana(
                    nombre=nombre_campana or f"Alianzas B2B {localidad} {datetime.now().strftime('%d/%m/%Y')}",
                    modulo="alianzas",
                    descripcion=f"Campaña alianzas — {', '.join(tipos)} — {localidad}",
                )
                db.add(campana)
                db.flush()
                resultados["campana_id"] = campana.id

            for empresa_data in todas_empresas:
                existente = db.query(Contacto).filter(
                    Contacto.empresa == empresa_data.get("empresa"),
                    Contacto.modulo == "alianzas",
                ).first()

                if existente:
                    continue

                contacto = Contacto(
                    nombre=empresa_data.get("nombre") or empresa_data.get("empresa", ""),
                    empresa=empresa_data.get("empresa", ""),
                    email=empresa_data.get("email", ""),
                    telefono=empresa_data.get("telefono", ""),
                    web=empresa_data.get("web", ""),
                    localidad=empresa_data.get("localidad", localidad),
                    descripcion=empresa_data.get("descripcion", ""),
                    modulo="alianzas",
                    tipo_empresa=empresa_data.get("tipo_empresa", "Empresa Aliada"),
                    fuente=empresa_data.get("fuente", ""),
                    estado="nuevo",
                )
                db.add(contacto)
                db.flush()
                contactos_bd.append(contacto)
                resultados["contactos_guardados"] += 1

        resultados["contactos"] = [
            {"empresa": c.empresa, "tipo": c.tipo_empresa, "localidad": c.localidad}
            for c in contactos_bd
        ]
        progreso("BD", f"{resultados['contactos_guardados']} empresas aliadas guardadas")

        # Enviar propuestas
        if enviar_emails and contactos_bd:
            progreso("EMAIL", f"Enviando propuestas a {len(contactos_bd)} empresas...")
            email_ia = parsear_respuesta_email(str(resultado_crew))

            with db_session() as db:
                for contacto in contactos_bd:
                    if not contacto.email:
                        continue

                    html_final = plantilla_alianza(
                        nombre_empresa=contacto.empresa,
                        tipo_empresa=contacto.tipo_empresa or "Empresa Aliada",
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
            progreso("EMAIL", f"{resultados['emails_enviados']} propuestas enviadas ✅")

    except Exception as e:
        logger.error(f"Error en pipeline de alianzas: {e}")
        resultados["errores"].append(str(e))

    return resultados
