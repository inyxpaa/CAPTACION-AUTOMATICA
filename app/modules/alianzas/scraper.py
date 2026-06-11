"""
ORESNA CAPTADOR — Módulo 2: Scraper de Empresas Aliadas B2B
Extrae empresas de reformas, mudanzas, gestorías y servicios afines
que pueden convertirse en socios de derivación mutua de clientes para ORESNA.
100% legal — solo contacta personas jurídicas (empresas), no particulares.
"""

import asyncio
import random
from typing import Optional
from loguru import logger
from playwright.async_api import async_playwright, Browser

from app.core.config import config


# Mapa de tipos de empresa a términos de búsqueda
TIPOS_BUSQUEDA = {
    "reformas": ["empresas de reformas", "reformas del hogar", "reforma integral"],
    "mudanzas": ["empresas de mudanzas", "mudanzas y transportes", "servicios de mudanza"],
    "gestoria": ["gestorías", "asesoría fiscal", "administradores de fincas"],
    "abogados": ["abogados inmobiliario", "despachos abogados", "abogado herencias"],
    "inmobiliaria": ["inmobiliarias", "agencias inmobiliarias"],  # para análisis de mercado
}


class AlianzaScraper:
    """
    Scraper para empresas potencialmente aliadas con ORESNA.
    Busca en Páginas Amarillas y Yelp empresas que traten con
    propietarios/compradores de inmuebles de forma habitual.
    """

    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36",
    ]

    def __init__(self):
        self.delay = config.SCRAPING_DELAY
        self.headless = config.SCRAPING_HEADLESS
        logger.info("🤝 AlianzaScraper inicializado")

    def buscar(
        self,
        tipo: str = "reformas",
        localidad: str = "Navarra",
        max_resultados: int = 50,
    ) -> list[dict]:
        """Punto de entrada síncrono."""
        return asyncio.run(self._buscar_async(tipo, localidad, max_resultados))

    async def _buscar_async(self, tipo: str, localidad: str, max_resultados: int) -> list[dict]:
        """Búsqueda asíncrona principal."""
        empresas = []
        terminos = TIPOS_BUSQUEDA.get(tipo, [tipo])

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=self.headless,
                args=["--no-sandbox", "--disable-blink-features=AutomationControlled"]
            )
            try:
                for termino in terminos:
                    if len(empresas) >= max_resultados:
                        break
                    
                    nuevas = await self._scrape_paginas_amarillas_alianza(
                        browser, termino, localidad
                    )
                    empresas.extend(nuevas)
                    logger.info(f"  '{termino}' → {len(nuevas)} empresas")
                    await asyncio.sleep(self.delay)

            except Exception as e:
                logger.error(f"Error en AlianzaScraper: {e}")
            finally:
                await browser.close()

        # Deduplicar
        vistos = set()
        resultado = []
        for e in empresas:
            clave = e.get("telefono") or e.get("empresa", "")
            if clave and clave not in vistos:
                vistos.add(clave)
                resultado.append(e)

        logger.info(f"✅ Alianzas — {len(resultado)} empresas únicas encontradas para '{tipo}'")
        return resultado[:max_resultados]

    async def _scrape_paginas_amarillas_alianza(
        self, browser: Browser, termino: str, localidad: str
    ) -> list[dict]:
        """Scraping de Páginas Amarillas para un término de búsqueda dado."""
        empresas = []
        ua = random.choice(self.USER_AGENTS)
        context = await browser.new_context(user_agent=ua)
        page = await context.new_page()

        try:
            termino_url = termino.replace(" ", "+")
            localidad_url = localidad.lower().replace(" ", "-")
            url = f"https://www.paginasamarillas.es/search/{termino_url}/all-mcp/{localidad_url}/all-aut/all-prov/all-isla/all-com/1"

            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(self.delay + random.uniform(0.5, 1.5))

            try:
                await page.wait_for_selector(".elem-list-item", timeout=10000)
            except Exception:
                return []

            items = await page.query_selector_all(".elem-list-item")
            for item in items[:25]:
                empresa = await self._extraer_datos_empresa(item, termino, localidad)
                if empresa:
                    empresas.append(empresa)

        except Exception as e:
            logger.warning(f"  Error scraping '{termino}': {e}")
        finally:
            await context.close()

        return empresas

    async def _extraer_datos_empresa(self, item, tipo_busqueda: str, localidad: str) -> Optional[dict]:
        """Extrae datos de un elemento de lista de Páginas Amarillas."""
        try:
            nombre = await self._texto_seguro(item, ".elem-name")
            if not nombre:
                return None

            direccion = await self._texto_seguro(item, ".direction-item")
            telefono = await self._texto_seguro(item, ".phone-item")
            web = await self._atributo_seguro(item, "a.web-item", "href")
            descripcion = await self._texto_seguro(item, ".elem-slogan")

            ciudad = ""
            if direccion:
                partes = direccion.split(",")
                ciudad = partes[-1].strip() if partes else localidad

            # Determinar tipo de empresa desde el término de búsqueda
            tipo_empresa = self._clasificar_tipo(tipo_busqueda)

            return {
                "empresa": nombre,
                "nombre": nombre,
                "email": "",
                "telefono": telefono,
                "web": web,
                "localidad": ciudad or localidad,
                "descripcion": descripcion or f"Empresa de {tipo_empresa} en {ciudad or localidad}",
                "fuente": "Páginas Amarillas",
                "tipo_empresa": tipo_empresa,
                "modulo": "alianzas",
            }
        except Exception:
            return None

    def _clasificar_tipo(self, termino: str) -> str:
        """Clasifica el tipo de empresa según el término de búsqueda."""
        termino = termino.lower()
        if "reforma" in termino:
            return "Empresa de Reformas"
        elif "mudanza" in termino:
            return "Empresa de Mudanzas"
        elif "gestor" in termino or "asesor" in termino or "finca" in termino:
            return "Gestoría / Administrador"
        elif "abogad" in termino or "herencia" in termino:
            return "Despacho Legal"
        return "Empresa Aliada"

    async def _texto_seguro(self, elemento, selector: str) -> str:
        """Extrae texto de forma segura."""
        try:
            nodo = await elemento.query_selector(selector)
            if nodo:
                return (await nodo.inner_text()).strip()
        except Exception:
            pass
        return ""

    async def _atributo_seguro(self, elemento, selector: str, atributo: str) -> str:
        """Extrae un atributo de forma segura."""
        try:
            nodo = await elemento.query_selector(selector)
            if nodo:
                valor = await nodo.get_attribute(atributo)
                return valor or ""
        except Exception:
            pass
        return ""
