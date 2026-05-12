# Netty Prospect Scanner — Mejoras implementadas

## 1. Propuestas y outreach con IA (`app/agents/agents.py`, `app/ai/`)

`ProposalGeneratorAgent` y `OutreachAgent` ahora llaman a la IA (OpenAI/DeepSeek) para generar contenido personalizado antes de caer al template estático.

- `generate_proposal_with_ai(ctx)` → JSON con `audit_summary`, `value_proposition`, `pitch`, `plan_recommendation`, `plan_justification`, `meta_note`
- `generate_outreach_with_ai(ctx)` → JSON con `whatsapp_draft`, `email_subject`, `email_body`
- Si la IA no está configurada o falla, se usa el template como fallback sin interrupciones.
- El campo `ai_generated: True/False` indica en cada resultado si vino de IA o template.

**Archivos:** `app/ai/commercial_analysis.py`, `app/ai/prompts.py`

---

## 2. Auditoría web más profunda (`app/agents/agents.py`)

`WebsiteAuditAgent` detecta ~10 oportunidades vs. las 5 originales:

| Señal | Oportunidad detectada |
|---|---|
| Formulario sin CRM integrado | Leads sin captura automática |
| Sin meta descripción o < 50 chars | Visibilidad en Google subóptima |
| Sin H1 | Estructura SEO deficiente |
| Sin tags Open Graph | No apto para compartir en redes |
| Sin schema markup | Sin rich results en Google |
| Velocidad `slow` o `very_slow` | UX lenta ahuyenta clientes |
| < 2 redes sociales | Presencia digital débil |
| Sin CTA claro | Sin llamada a la acción visible |

---

## 3. Dashboard CRM operativo (`dashboard/streamlit_app.py`)

- **Alertas HOT** en la parte superior: banners rojos/amarillos para prospectos calientes con más de 48 h sin contacto.
- **Funnel visual** con `st.metric` + delta porcentual en cada etapa.
- **Gráfico de barras diario** (`runs` vs `hot`) para actividad de agentes.
- **Cola de ventas** con 5 conteos de estado (pending / approved / rejected / sent / avg_hours).
- **Acciones de aprobación** en expander compacto.
- **Filtros CRM** en expander colapsado para no ocupar pantalla.
- **Tabla de prospectos** reordenada: columnas de contacto al frente (teléfonos, emails, WhatsApp, redes sociales).

---

## 4. Scraper mejorado (`app/scanner/`)

### robots.txt con seguimiento de redirects (`robots.py`)

El módulo original usaba `RobotFileParser.read()` que no sigue redirects HTTP → falsos bloqueos para sitios como `degustapanama.com` (redirige a `www.`).

**Solución:** usa `httpx.get(..., follow_redirects=True)` y parsea el contenido manualmente. También verifica `can_fetch("*", url)` además del agente específico para evitar falsos bloqueos.

### Fallbacks SSL e HTTP (`crawler.py`)

Orden de intento para cada URL:
1. HTTPS con verificación SSL
2. HTTPS sin verificación (`verify=False`) si hay error de certificado
3. HTTP plano si HTTPS falla completamente

Los resultados exitosos marcan `ssl_bypass: True` o `http_fallback: True` para trazabilidad.

### Clasificación de errores

Cada fallo tiene un `fail_reason` específico en lugar del genérico `fetch_error`:

| Código | Causa |
|---|---|
| `dns_error` | Dominio no resuelve |
| `timeout` | Tiempo de espera excedido |
| `ssl_error` | Certificado inválido no recuperable |
| `connection_refused` | Puerto cerrado |
| `robots_disallowed` | robots.txt bloquea el crawler |
| `ssrf_blocked` | IP privada/local bloqueada por seguridad |

### Helper `_fail_data()`

Reemplaza 3 bloques de 25 líneas idénticos por una función centralizada que aplica el score engine incluso en fallos.

---

## 5. Extracción de datos de contacto reales (`app/scanner/detector.py`)

El scraper ahora extrae los valores concretos, no solo booleanos:

| Campo nuevo | Contenido |
|---|---|
| `phone_numbers` | Teléfonos encontrados en el texto (hasta 5, comma-separated) |
| `email_addresses` | Emails encontrados en el HTML (hasta 5, filtrando imágenes/assets) |
| `whatsapp_number` | Número extraído de links `wa.me` o `api.whatsapp.com` |
| `facebook_url` | URL real del perfil de Facebook (excluye pixels, sharer, fbml) |
| `instagram_url` | URL real del perfil de Instagram |
| `linkedin_url` | URL del perfil/empresa en LinkedIn |
| `twitter_url` | URL del perfil en Twitter/X |
| `youtube_url` | URL del canal de YouTube |

**Regex de teléfonos:** detecta formatos panameños (+507, (507), 4-4 dígitos) hasta 15 dígitos.  
**Regex de Facebook:** excluye `fb.com/tr` (pixel), `2008/fbml` (namespace), `sharer`, `dialog`, `plugins`.

**Nueva migración Alembic:** `0007_add_contact_extraction_fields.py`  
**Modelo actualizado:** `app/models.py` — 8 columnas nuevas en `prospects`.  
**API actualizada:** `routes_dashboard.py` — `/prospects` y `/sales-queue` incluyen los nuevos campos.

---

## 6. Señales SEO y sociales adicionales (`app/scanner/detector.py`, `fingerprints.py`)

Nuevas señales detectadas en cada sitio:

| Señal | Descripción |
|---|---|
| `title_length` | Longitud del `<title>` |
| `meta_desc_length` | Longitud de la meta descripción |
| `has_h1` | Presencia de etiqueta H1 |
| `has_og_tags` | Open Graph tags (`og:title`, etc.) |
| `has_schema_markup` | JSON-LD schema.org |
| `has_tiktok` | Enlace a TikTok |
| `has_youtube` | Enlace a YouTube |
| `has_linkedin` | Enlace a LinkedIn |
| `has_twitter` | Enlace a Twitter/X |
| `social_count` | Total de redes detectadas (0–6) |
| `has_crm_form` | Formulario CRM embebido |
| `crm_form_vendor` | HubSpot / Typeform / Gravity Forms / etc. |

---

## 7. Score engine actualizado (`app/scoring/score_engine.py`)

Nuevos criterios añadidos al puntaje Netty Fit:

| Condición | Puntos |
|---|---|
| Velocidad `slow` o `very_slow` | +7 (penalización) |
| Sin meta descripción SEO | +5 (oportunidad) |
| Formulario sin CRM integrado | +7 (oportunidad) |
| Cuenta social < 2 redes | +5 (oportunidad) |

---

## Cómo arrancar

```bash
# API
source venv/bin/activate
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/netty-api.log 2>&1 &

# Dashboard
streamlit run dashboard/streamlit_app.py --server.port 8501 &

# Aplicar migraciones (solo una vez)
alembic upgrade head
```

## Cómo escanear un lote de sitios

```bash
curl -X POST http://localhost:8000/scan/urls \
  -H "Content-Type: application/json" \
  -d '{"urls": ["sitio1.com", "sitio2.com.pa"], "rubro": "retail", "provincia": "Panamá"}'
```

O subir un CSV desde el dashboard → sección "Pipeline comercial".
