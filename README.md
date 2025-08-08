# Bot de Monitoreo de Ofertas — Twitter/X poster

**Resumen rápido**  
Proyecto listo para ejecutar en GitHub Actions (gratis en repositorios públicos).  
Monitorea páginas de "ofertas / chollos" en varios comercios (Amazon.es, PcComponentes, Fnac, MediaMarkt) y publica un tweet cuando detecta:
- Precio por debajo de un umbral (configurable)
- Producto que vuelve a estar en stock

**¿Qué necesitas hacer?**
1. Subir este proyecto a un repo público en GitHub.
2. En Settings → Secrets del repo, añade las credenciales de Twitter/X:
   - `TWITTER_API_KEY`
   - `TWITTER_API_SECRET`
   - `TWITTER_ACCESS_TOKEN`
   - `TWITTER_ACCESS_SECRET`
   *(Si usas OAuth2 App-only, adapta `twitter_poster.py` por la variante que prefieras.)*
3. Opcional: Ajusta `config.yaml` (intervalos, tiendas, umbrales, keywords).
4. Activar GitHub Actions (el workflow incluido ejecuta `main.py` cada hora).

**Cómo funciona (alto nivel)**
- `main.py` lee `config.yaml`, ejecuta scrapers por tienda (deals / búsquedas por keyword).
- Compara con registros en `data/state.json`.
- Si hay cambio relevante, publica en Twitter usando `twitter_poster.py` y actualiza `state.json`.

**Limitaciones y notas**
- Scraping de Amazon puede ser frágil (estructura HTML cambiante, bloqueos). El código contiene heurísticas de extracción; si falla, habilita un headless browser (Playwright) y actualiza el workflow para instalar dependencias.
- Usa este bot respetando términos de uso de cada web. Para un uso más estable en Amazon, considera Product Advertising API.
- Este repo no "ejecuta" automáticamente hasta que lo subas a GitHub y configures los secrets.

