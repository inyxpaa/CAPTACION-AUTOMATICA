"""
ORESNA CAPTADOR — Módulo 1: Scraper de Constructoras en Navarra
Extrae datos de constructoras y promotoras desde fuentes públicas web:
- Páginas Amarillas (empresas de construcción en Navarra)
- Google Maps (búsqueda de constructoras)
- Infocif / Infoempresa (datos empresariales)
"""

import asyncio
import time
import random
from typing import Optional
from loguru import logger
from playwright.async_api import async_playwright, Page, Browser

from app.core.config import config


class ConstructoraScraper:
    """
    Extrae datos de constructoras en Navarra usando Playwright.
    Implementa delays anti-detección y rotación de User-Agent.
    """

    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    ]

    def __init__(self):
        self.delay = config.SCRAPING_DELAY
        self.headless = config.SCRAPING_HEADLESS
        logger.info("🔍 ConstructoraScraper inicializado")

    def buscar(self, localidad: str = "Navarra", max_resultados: int = 50) -> list[dict]:
        """
        Punto de entrada síncrono. Ejecuta la búsqueda asíncrona con asyncio.
        """
        return asyncio.run(self._buscar_async(localidad, max_resultados))

    async def _buscar_async(self, localidad: str, max_resultados: int) -> list[dict]:
        """Búsqueda asíncrona principal."""
        empresas = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=self.headless,
                args=[
                    "--no-sandbox",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-infobars",
                ]
            )

            try:
                # Fuente 1: Páginas Amarillas
                logger.info("📌 Rastreando Páginas Amarillas...")
                amarillas = await self._scrape_paginas_amarillas(browser, localidad)
                empresas.extend(amarillas)
                logger.success(f"   → {len(amarillas)} empresas encontradas en Páginas Amarillas")

                if len(empresas) < max_resultados:
                    # Fuente 2: Busca directa en web
                    logger.info("📌 Rastreando fuentes adicionales...")
                    adicionales = await self._scrape_busqueda_general(browser, localidad)
                    empresas.extend(adicionales)
                    logger.success(f"   → {len(adicionales)} empresas adicionales")

            except Exception as e:
                logger.error(f"Error durante el scraping: {e}")
            finally:
                await browser.close()

        # Eliminar duplicados por email
        vistos = set()
        sin_duplicados = []
        for e in empresas:
            clave = e.get("email") or e.get("empresa", "")
            if clave and clave not in vistos:
                vistos.add(clave)
                sin_duplicados.append(e)

        logger.info(f"✅ Total empresas únicas encontradas: {len(sin_duplicados)}")
        return sin_duplicados[:max_resultados]

    async def _scrape_paginas_amarillas(self, browser: Browser, localidad: str) -> list[dict]:
        """
        Extrae constructoras de Páginas Amarillas España.
        URL base: https://www.paginasamarillas.es/search/constructoras/
        """
        empresas = []
        ua = random.choice(self.USER_AGENTS)
        context = await browser.new_context(user_agent=ua)
        page = await context.new_page()

        try:
            # Codificar localidad para URL
            localidad_url = localidad.lower().replace(" ", "-")
            url = f"https://www.paginasamarillas.es/search/constructoras/all-mcp/{localidad_url}/all-aut/all-prov/all-isla/all-com/1"

            logger.debug(f"  Accediendo: {url}")
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await self._delay_humano()

            # Esperar resultados
            try:
                await page.wait_for_selector(".elem-list-item", timeout=10000)
            except Exception:
                logger.warning("  No se encontraron resultados en Páginas Amarillas")
                return []

            # Extraer número de páginas
            total_paginas = await self._obtener_total_paginas(page)
            total_paginas = min(total_paginas, 5)  # Máximo 5 páginas

            for num_pagina in range(1, total_paginas + 1):
                if num_pagina > 1:
                    url_pagina = url.replace("/1", f"/{num_pagina}")
                    await page.goto(url_pagina, wait_until="domcontentloaded", timeout=30000)
                    await self._delay_humano()

                items = await page.query_selector_all(".elem-list-item")
                for item in items:
                    empresa = await self._extraer_datos_item_amarillas(item)
                    if empresa:
                        empresa["fuente"] = "Páginas Amarillas"
                        empresa["tipo_empresa"] = "Constructora"
                        empresa["modulo"] = "constructores"
                        empresas.append(empresa)

            logger.debug(f"  Páginas Amarillas: {len(empresas)} empresas extraídas")

        except Exception as e:
            logger.error(f"  Error en Páginas Amarillas: {e}")
        finally:
            await context.close()

        return empresas

    async def _extraer_datos_item_amarillas(self, item) -> Optional[dict]:
        """Extrae los datos de un elemento de lista de Páginas Amarillas."""
        try:
            nombre = await self._texto_seguro(item, ".elem-name")
            if not nombre:
                return None

            direccion = await self._texto_seguro(item, ".direction-item")
            telefono = await self._texto_seguro(item, ".phone-item")
            web = await self._atributo_seguro(item, "a.web-item", "href")

            # Extraer localidad de la dirección
            localidad = ""
            if direccion:
                partes = direccion.split(",")
                localidad = partes[-1].strip() if partes else direccion

            return {
                "empresa": nombre,
                "nombre": nombre,
                "email": "",  # Páginas Amarillas no muestra emails directamente
                "telefono": telefono,
                "web": web,
                "localidad": localidad,
                "descripcion": f"Constructora en {localidad}",
            }
        except Exception:
            return None

    async def _scrape_busqueda_general(self, browser: Browser, localidad: str) -> list[dict]:
        """
        Búsqueda complementaria en Europages para constructoras navarras.
        """
        empresas = []
        ua = random.choice(self.USER_AGENTS)
        context = await browser.new_context(user_agent=ua)
        page = await context.new_page()

        try:
            url = f"https://www.europages.es/empresas/{localidad}/constructoras.html"
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await self._delay_humano()

            items = await page.query_selector_all(".ep-p_card")
            for item in items[:20]:
                try:
                    nombre = await self._texto_seguro(item, ".ep-p_card-title")
                    desc = await self._texto_seguro(item, ".ep-p_card-desc")
                    ciudad = await self._texto_seguro(item, ".ep-p_card-city")

                    if nombre:
                        empresas.append({
                            "empresa": nombre,
                            "nombre": nombre,
                            "email": "",
                            "telefono": "",
                            "web": "",
                            "localidad": ciudad or localidad,
                            "descripcion": desc or "",
                            "fuente": "Europages",
                            "tipo_empresa": "Constructora",
                            "modulo": "constructores",
                        })
                except Exception:
                    continue

        except Exception as e:
            logger.warning(f"  Europages no disponible: {e}")
        finally:
            await context.close()

        return empresas

    async def _obtener_total_paginas(self, page: Page) -> int:
        """Intenta obtener el número total de páginas de resultados."""
        try:
            paginador = await page.query_selector(".pagination")
            if not paginador:
                return 1
            items = await paginador.query_selector_all("li")
            numeros = []
            for item in items:
                texto = await item.inner_text()
                if texto.strip().isdigit():
                    numeros.append(int(texto.strip()))
            return max(numeros) if numeros else 1
        except Exception:
            return 1

    async def _texto_seguro(self, elemento, selector: str) -> str:
        """Extrae texto de un selector de forma segura."""
        try:
            nodo = await elemento.query_selector(selector)
            if nodo:
                return (await nodo.inner_text()).strip()
        except Exception:
            pass
        return ""

    async def _atributo_seguro(self, elemento, selector: str, atributo: str) -> str:
        """Extrae un atributo de un selector de forma segura."""
        try:
            nodo = await elemento.query_selector(selector)
            if nodo:
                valor = await nodo.get_attribute(atributo)
                return valor or ""
        except Exception:
            pass
        return ""

    async def _delay_humano(self):
        """Pausa aleatoria para simular comportamiento humano y evitar bloqueos."""
        espera = self.delay + random.uniform(0.5, 1.5)
        await asyncio.sleep(espera)
