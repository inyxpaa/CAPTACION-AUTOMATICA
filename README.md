# ORESNA CAPTADOR 🏠

**Plataforma de Captación B2B con Inteligencia Artificial para ORESNA Inmobiliaria (Navarra)**

---

## ¿Qué hace este sistema?

ORESNA CAPTADOR automatiza la búsqueda y contacto con dos tipos de socios comerciales en Navarra:

- **Módulo 1 · Constructoras**: Detecta empresas constructoras y promotoras activas. Genera emails personalizados para ofrecerles a ORESNA como canal de ventas de sus inmuebles.
- **Módulo 2 · Alianzas B2B**: Localiza empresas de reformas, mudanzas, gestorías y despachos legales. Propone acuerdos de derivación mutua de clientes (100% legal, sin riesgo RGPD).

### Arquitectura
```
3 Agentes de IA (CrewAI) → Rastreador + Analista + Redactor
Scraping web → Playwright (anti-detección)
Emails profesionales → Resend API
Panel visual → Streamlit
Base de datos → SQLite local
```

---

## Instalación y uso

### Opción A: Arranque automático (recomendado)
```
Doble clic en: arrancar_captador.bat
```
El script instala todo automáticamente en la primera ejecución.

### Opción B: Manual
```bash
# 1. Crear y activar entorno virtual
python -m venv venv
venv\Scripts\activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Instalar navegador para scraping
playwright install chromium

# 4. Configurar variables de entorno
copy .env.example .env
# → Edita .env con tus claves API

# 5. Arrancar el sistema
python main.py
```

---

## Configuración (.env)

| Variable | Descripción | Obligatoria |
|---|---|---|
| `GROQ_API_KEY` | Clave API de Groq (gratuita) | ✅ (o OpenAI) |
| `OPENAI_API_KEY` | Clave API de OpenAI | ✅ (o Groq) |
| `LLM_PROVIDER` | `groq` o `openai` | ✅ |
| `RESEND_API_KEY` | Clave de Resend para emails | ⚠️ Opcional |
| `EMAIL_FROM` | Email de remitente verificado | Si usas Resend |
| `EMPRESA_TELEFONO` | Teléfono de ORESNA | Recomendado |
| `EMPRESA_WEB` | Web de ORESNA | Recomendado |

### Obtener claves gratuitas
- **Groq**: https://console.groq.com (gratuito, 14.400 req/día)
- **Resend**: https://resend.com (gratuito, 3.000 emails/mes)

---

## Estructura del proyecto
```
CAPTADOR/
├── app/
│   ├── agents/              # Agentes de IA (CrewAI)
│   │   ├── scraper_agent.py  # Agente Rastreador
│   │   ├── analyst_agent.py  # Agente Analista
│   │   └── writer_agent.py   # Agente Redactor
│   ├── modules/
│   │   ├── constructores/    # Módulo 1
│   │   └── alianzas/         # Módulo 2
│   ├── core/
│   │   ├── config.py         # Configuración central
│   │   ├── db.py             # Modelos SQLAlchemy
│   │   └── email_service.py  # Servicio Resend
│   └── ui/
│       ├── main.py           # Panel Streamlit
│       └── pages/            # Páginas del panel
├── data/                     # Base de datos SQLite
├── .env                      # Claves API (NO subir a git)
├── .env.example              # Plantilla de configuración
├── requirements.txt          # Dependencias
├── main.py                   # Punto de entrada
└── arrancar_captador.bat     # Script de arranque
```

---

## Notas legales

- **RGPD**: El sistema solo contacta **personas jurídicas** (empresas), nunca particulares. Las comunicaciones entre empresas (B2B) están fuera del ámbito del RGPD.
- **Scraping**: Se respetan los delays entre peticiones. Solo se rastrean sitios web públicos.
- **Opt-out**: Todas las plantillas de email incluyen un aviso de baja conforme a la normativa española.

---

## Soporte

Desarrollado para ORESNA Inmobiliaria · Navarra, España · 2026
