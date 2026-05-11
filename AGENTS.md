# AGENTS.md — Reglas Duras de Operación y Desarrollo

Este documento define las reglas obligatorias para cualquier agente (humano o IA) que modifique u opere **Netty Prospect Scanner**.

## 1) Principios no negociables
1. **Scraping ético primero**: no saturar servidores, no comportamiento destructivo.
2. **Cumplimiento técnico**: respetar `robots.txt` cuando aplique y límites de concurrencia/delay.
3. **No inventar datos**: todo dato persistido/exportado debe provenir de escaneo real o fuente explícita.
4. **Separación de responsabilidades**:
   - scraping/detección en `app/scanner/`
   - scoring en `app/scoring/`
   - IA comercial en `app/ai/`
5. **IA no sustituye scraping**: la IA solo puede analizar/comunicar hallazgos comerciales.

## 2) Reglas duras de scraping/crawling
1. Usar `httpx` + `BeautifulSoup` como vía principal.
2. Usar Playwright **solo fallback** para render JS.
3. Mantener user-agent responsable configurable (`.env`).
4. Respetar límites:
   - `MAX_CONCURRENCY`
   - `REQUEST_DELAY_SECONDS`
   - `REQUEST_TIMEOUT_SECONDS`
5. Ante fallos de red, degradar con manejo de errores y registrar estado (`load_ok`, `http_code`).
6. No ejecutar ataques de fuerza bruta de rutas ni crawling masivo no acotado.

## 3) Reglas de datos y persistencia
1. `domain` es único (evitar duplicados).
2. Toda inserción debe ser `upsert` por dominio.
3. SQLite para MVP; diseño compatible con PostgreSQL.
4. Cambios de esquema deben pasar por Alembic (`alembic/versions`).

## 4) Reglas de scoring
1. El score debe permanecer en rango `[0,100]`.
2. Clasificación oficial:
   - 80–100 Caliente
   - 60–79 Bueno
   - 40–59 Medio
   - 0–39 Bajo
3. Si el sitio está caído/inaccesible, score máximo 20.
4. Cambios de reglas deben documentarse en `bitacora.md` y `README.md`.

## 5) Reglas de API y dashboard
1. Todo endpoint nuevo debe:
   - validar inputs (Pydantic/Query)
   - manejar errores explícitos
   - devolver JSON consistente
2. El dashboard no debe contener lógica crítica de negocio (solo consumo de API).
3. El pipeline debe soportar trazabilidad (`job_id`, estado, timestamps).

## 6) Reglas de exportación
1. Exportaciones oficiales mínimas: CSV y XLSX.
2. No exportar columnas inexistentes; manejar faltantes sin romper flujo.
3. Los archivos deben guardarse en `data/exports/`.

## 7) Reglas de calidad y verificación
1. Antes de cerrar cambios:
   - `python -m compileall app dashboard tests`
   - `pytest`
2. No dejar código muerto ni TODOs ambiguos en producción.
3. Toda incidencia/bug corregido debe registrarse en `bitacora.md`.

## 8) Reglas de seguridad
1. No commitear secretos reales (`.env` fuera de control de versiones).
2. Usar `.env.example` como plantilla.
3. En IA externa, manejar errores y timeouts; no exponer API keys en logs.
4. Bloquear objetivos SSRF/locales en crawling (localhost, loopback, redes privadas/link-local).
5. Restringir entrada de archivos CSV a directorios permitidos (`data/`) y extensión `.csv`.
6. Para IA con API keys, solo permitir endpoints HTTPS (`AI_BASE_URL` no debe ser HTTP).

## 9) Reglas de documentación viva
1. `README.md` debe reflejar el estado funcional real.
2. `bitacora.md` debe incluir:
   - fecha
   - cambios
   - decisiones
   - errores
   - pendientes
   - próximos pasos
3. Cualquier módulo nuevo debe quedar mencionado en README/bitácora.

## 10) Definición de "Done" por cambio
Un cambio se considera terminado solo si:
- compila,
- pasa tests,
- mantiene compatibilidad con funcionalidades existentes,
- y queda documentado.

# NETTY SALES ENGINE — PRINCIPIOS FUNDAMENTALES

## IDENTIDAD DEL SISTEMA

Netty es el producto principal:
un asistente inteligente de ventas, soporte, automatización y captación de leads.

El sistema que estamos construyendo NO es Netty en sí.
Es el ecosistema autónomo de prospección, análisis, ventas y seguimiento diseñado para vender Netty.

Este ecosistema debe operar continuamente y demostrar capacidades reales de inteligencia artificial aplicada.

---

# PRINCIPIO CENTRAL

El ecosistema Netty debe demostrar sus propias capacidades operando sobre sí mismo.

Todo prospecto debe entender claramente que:
- fue descubierto,
- analizado,
- auditado,
- clasificado,
- contactado,
- y seguido automáticamente

por el mismo ecosistema de inteligencia artificial que impulsa Netty.

Esto NO es opcional.
Es un principio arquitectónico, comercial y psicológico fundamental del sistema.

---

# OBJETIVO DEL ECOSISTEMA

El objetivo del sistema es:

1. Descubrir negocios potenciales en Panamá.
2. Analizar sus sitios web.
3. Detectar oportunidades de automatización.
4. Calcular probabilidad de conversión.
5. Generar auditorías automáticas.
6. Generar propuestas comerciales personalizadas.
7. Realizar seguimiento comercial.
8. Asistir en el cierre de ventas.
9. Alimentar un CRM inteligente.
10. Demostrar las capacidades reales de Netty.

---

# FILOSOFÍA DE COMUNICACIÓN

El sistema NUNCA debe presentarse como:
- un simple chatbot,
- un plugin básico,
- una herramienta experimental,
- una demo teórica.

El sistema debe proyectar:
- autonomía,
- inteligencia operativa,
- análisis real,
- automatización real,
- capacidad comercial,
- infraestructura IA activa.

Toda comunicación debe reforzar que:
- Netty utiliza IA real,
- Netty opera activamente,
- Netty utiliza su propio ecosistema IA para venderse,
- Netty no es teoría,
- Netty está funcionando en producción.

---

# PRINCIPIO DE META-DEMONSTRACIÓN

El ecosistema Netty debe demostrar sus capacidades usando sus propias capacidades.

Ejemplos:
- El sistema encuentra prospectos automáticamente.
- El sistema analiza sitios automáticamente.
- El sistema genera auditorías automáticamente.
- El sistema prepara propuestas automáticamente.
- El sistema realiza seguimiento automáticamente.

Esto debe comunicarse claramente a los prospectos porque genera:
- confianza,
- credibilidad,
- diferenciación,
- autoridad tecnológica.

---

# REGLAS GLOBALES DE LOS AGENTES

Todos los agentes del ecosistema Netty deben:

1. Mantener coherencia arquitectónica.
2. Respetar la estructura modular.
3. Registrar cambios en bitacora.md.
4. No romper funcionalidades existentes.
5. Operar con enfoque comercial real.
6. Mantener trazabilidad de decisiones.
7. Generar resultados auditables.
8. Priorizar estabilidad y continuidad.
9. Trabajar con datos reales.
10. Evitar simulaciones falsas en producción.

---

# AGENTES PRINCIPALES DEL ECOSISTEMA

## 1. Prospect Discovery Agent
Descubre negocios potenciales automáticamente usando motores de búsqueda y análisis web.

## 2. Panama Validation Agent
Determina si el negocio pertenece realmente a Panamá usando señales locales.

## 3. Technology Fingerprint Agent
Detecta CMS, ecommerce, chatbot, WhatsApp y stack tecnológico.

## 4. Website Audit Agent
Analiza debilidades comerciales y oportunidades de automatización.

## 5. Commercial Qualification Agent
Calcula el Netty Fit Score y probabilidad de conversión.

## 6. Netty Solution Architect Agent
Determina específicamente cómo Netty podría ayudar a ese negocio.

## 7. Proposal Generator Agent
Genera auditorías, propuestas, correos y pitches personalizados.

## 8. Outreach Agent
Gestiona contacto inicial por email y otros canales.

## 9. Follow-Up Agent
Gestiona seguimiento inteligente de prospectos.

## 10. CRM Intelligence Agent
Mantiene actualizado el pipeline comercial y analytics.

---

# ARQUITECTURA GENERAL

El sistema debe operar como una plataforma modular.

NO construir:
- un script gigante,
- un monolito desordenado,
- automatizaciones rígidas.

Construir:
- módulos desacoplados,
- workers independientes,
- agentes especializados,
- servicios reutilizables,
- arquitectura extensible.

---

# PRIORIDADES TÉCNICAS

Prioridad absoluta:
1. estabilidad,
2. trazabilidad,
3. modularidad,
4. persistencia de datos,
5. dashboard funcional,
6. continuidad operacional,
7. automatización progresiva.

---

# DASHBOARD PRINCIPAL

El dashboard debe funcionar como:
- centro de operaciones,
- CRM IA,
- monitor comercial,
- sistema de analytics,
- panel operativo 24/7.

Debe mostrar:
- prospectos,
- scores,
- tecnologías detectadas,
- auditorías,
- outreach,
- seguimiento,
- conversiones,
- alertas HOT,
- métricas de rendimiento.

---

# OPERACIÓN 24/7

El sistema debe diseñarse para operar continuamente en una mini desktop Debian local con:
- consumo moderado,
- workers controlados,
- concurrencia limitada,
- estabilidad prolongada,
- persistencia de datos,
- recuperación automática.

---

# PRINCIPIO FINAL

Netty debe vender Netty.

El ecosistema completo debe actuar como demostración viva de las capacidades reales de automatización e inteligencia comercial de Netty.
