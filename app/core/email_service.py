import resend
from datetime import datetime
from loguru import logger
from typing import Optional

from app.core.config import config
from app.core.db import db_session, EmailLog, Contacto, Campana


class EmailService:

    def __init__(self):
        if config.RESEND_API_KEY:
            resend.api_key = config.RESEND_API_KEY
            self._disponible = True
            logger.info("Resend configurado")
        else:
            self._disponible = False
            logger.warning("Sin clave Resend - modo simulacion activo")

    @property
    def disponible(self) -> bool:
        return self._disponible

    def enviar_email(
        self,
        contacto: Contacto,
        asunto: str,
        cuerpo_html: str,
        cuerpo_texto: str = "",
        campana_id: Optional[int] = None,
    ) -> dict:
        if not contacto.email:
            return {"exito": False, "mensaje": "El contacto no tiene email"}

        log_entry = EmailLog(
            contacto_id=contacto.id,
            campana_id=campana_id,
            asunto=asunto,
            cuerpo_html=cuerpo_html,
            cuerpo_texto=cuerpo_texto,
            estado="pendiente",
            fecha_envio=datetime.utcnow(),
        )

        if not self._disponible:
            logger.info(f"[Simulacion] Email a {contacto.email} - Asunto: {asunto}")
            with db_session() as db:
                log_entry.estado = "enviado"
                log_entry.resend_id = "sim_" + datetime.utcnow().strftime("%Y%m%d%H%M%S")
                db.add(log_entry)
                contacto_db = db.get(Contacto, contacto.id)
                if contacto_db:
                    contacto_db.estado = "email_enviado"
            return {"exito": True, "mensaje": "Email simulado (sin clave Resend)"}

        try:
            respuesta = resend.Emails.send({
                "from": f"{config.EMAIL_FROM_NAME} <{config.EMAIL_FROM}>",
                "to": [contacto.email],
                "subject": asunto,
                "html": cuerpo_html,
                "text": cuerpo_texto or self._html_a_texto(cuerpo_html),
            })

            with db_session() as db:
                log_entry.estado = "enviado"
                log_entry.resend_id = respuesta.get("id", "")
                db.add(log_entry)
                contacto_db = db.get(Contacto, contacto.id)
                if contacto_db:
                    contacto_db.estado = "email_enviado"

            logger.info(f"Email enviado a {contacto.email} - ID: {respuesta.get('id')}")
            return {"exito": True, "mensaje": f"Email enviado (ID: {respuesta.get('id')})"}

        except Exception as e:
            logger.error(f"Error enviando email a {contacto.email}: {e}")
            with db_session() as db:
                log_entry.estado = "error"
                log_entry.error_msg = str(e)
                db.add(log_entry)
            return {"exito": False, "mensaje": str(e)}

    def _html_a_texto(self, html: str) -> str:
        import re
        texto = re.sub(r"<br\s*/?>", "\n", html)
        texto = re.sub(r"</p>", "\n\n", texto)
        texto = re.sub(r"<[^>]+>", "", texto)
        return texto.strip()


def plantilla_constructora(
    nombre_empresa: str,
    tipo_obra: str,
    localidad: str,
    cuerpo_ia: str,
) -> str:
    return f"""
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<style>
  body {{ font-family: 'Helvetica Neue', Arial, sans-serif; background: #f4f4f4; margin: 0; padding: 0; }}
  .wrapper {{ max-width: 620px; margin: 30px auto; background: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
  .header {{ background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%); padding: 32px 40px; }}
  .header h1 {{ color: #e2c36b; margin: 0; font-size: 22px; font-weight: 700; letter-spacing: 1px; }}
  .header p {{ color: #a0b4cc; margin: 6px 0 0; font-size: 13px; }}
  .body {{ padding: 36px 40px; color: #333; line-height: 1.7; font-size: 15px; }}
  .badge {{ display: inline-block; background: #eef4ff; color: #1a5dc8; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; margin-bottom: 20px; }}
  .cta {{ display: inline-block; margin-top: 24px; background: linear-gradient(135deg, #1a5dc8, #0f3460); color: white; padding: 14px 28px; border-radius: 6px; text-decoration: none; font-weight: 600; font-size: 15px; }}
  .footer {{ background: #f8f9fa; padding: 20px 40px; text-align: center; font-size: 12px; color: #888; border-top: 1px solid #eee; }}
</style>
</head>
<body>
<div class="wrapper">
  <div class="header">
    <h1>ORESNA Inmobiliaria</h1>
    <p>Especialistas en Navarra - Propuesta de colaboracion</p>
  </div>
  <div class="body">
    <span class="badge">{tipo_obra} - {localidad}</span>
    {cuerpo_ia}
    <br><br>
    <a class="cta" href="mailto:{config.EMAIL_FROM}">Responder a esta propuesta</a>
  </div>
  <div class="footer">
    {config.EMPRESA_NOMBRE} - {config.EMPRESA_TELEFONO} - {config.EMPRESA_WEB}<br>
    Si no desea recibir mas comunicaciones, responda con BAJA en el asunto.
  </div>
</div>
</body>
</html>
"""


def plantilla_alianza(
    nombre_empresa: str,
    tipo_empresa: str,
    localidad: str,
    cuerpo_ia: str,
) -> str:
    return f"""
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<style>
  body {{ font-family: 'Helvetica Neue', Arial, sans-serif; background: #f4f4f4; margin: 0; padding: 0; }}
  .wrapper {{ max-width: 620px; margin: 30px auto; background: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
  .header {{ background: linear-gradient(135deg, #0d3b2e 0%, #1a5c45 50%, #2e7d5c 100%); padding: 32px 40px; }}
  .header h1 {{ color: #a8e6cf; margin: 0; font-size: 22px; font-weight: 700; letter-spacing: 1px; }}
  .header p {{ color: #7ec8a0; margin: 6px 0 0; font-size: 13px; }}
  .body {{ padding: 36px 40px; color: #333; line-height: 1.7; font-size: 15px; }}
  .badge {{ display: inline-block; background: #edfff5; color: #1a5c45; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; margin-bottom: 20px; }}
  .propuesta {{ background: #f0fff8; border-left: 4px solid #2e7d5c; padding: 16px 20px; border-radius: 0 6px 6px 0; margin: 20px 0; font-size: 14px; color: #1a3d2e; }}
  .cta {{ display: inline-block; margin-top: 24px; background: linear-gradient(135deg, #1a5c45, #0d3b2e); color: white; padding: 14px 28px; border-radius: 6px; text-decoration: none; font-weight: 600; font-size: 15px; }}
  .footer {{ background: #f8f9fa; padding: 20px 40px; text-align: center; font-size: 12px; color: #888; border-top: 1px solid #eee; }}
</style>
</head>
<body>
<div class="wrapper">
  <div class="header">
    <h1>ORESNA Inmobiliaria</h1>
    <p>Propuesta de alianza estrategica - {tipo_empresa} en {localidad}</p>
  </div>
  <div class="body">
    <span class="badge">{tipo_empresa} - {localidad}</span>
    {cuerpo_ia}
    <div class="propuesta">
      <strong>La propuesta en resumen:</strong><br>
      Derivacion mutua de clientes sin coste ni compromiso. Cuando uno de nuestros clientes
      necesite sus servicios, le recomendaremos directamente. A cambio, si algun cliente suyo
      necesita vender o comprar en Navarra, nos lo hace llegar.
    </div>
    <a class="cta" href="mailto:{config.EMAIL_FROM}">Hablar sobre esta propuesta</a>
  </div>
  <div class="footer">
    {config.EMPRESA_NOMBRE} - {config.EMPRESA_TELEFONO} - {config.EMPRESA_WEB}<br>
    Esta comunicacion es una propuesta B2B entre empresas. Para solicitar la baja, responda con BAJA en el asunto.
  </div>
</div>
</body>
</html>
"""


email_service = EmailService()
