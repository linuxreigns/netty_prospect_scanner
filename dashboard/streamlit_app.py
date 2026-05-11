import pandas as pd
import requests
import streamlit as st

st.set_page_config(
    page_title="Netty Sales Engine",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

API_BASE = st.sidebar.text_input("API Base URL", value="http://localhost:8000")
st.sidebar.markdown("---")
st.sidebar.caption("🤖 Netty Sales Engine — Centro Operativo IA")
st.sidebar.caption("Descubrimiento · Auditoría · Propuesta · CRM")

st.title("Netty Sales Engine")
st.caption(
    "Centro Operativo IA · Cada prospecto fue descubierto, analizado, auditado y clasificado "
    "automáticamente por el ecosistema que impulsa Netty."
)

if st.button("Refrescar", type="primary"):
    st.rerun()

# ── Cargar datos ────────────────────────────────────────────────────────────────
try:
    summary = requests.get(f"{API_BASE}/dashboard/summary", timeout=10).json()
    agent_summary = requests.get(f"{API_BASE}/dashboard/agents/summary", timeout=10).json()
    agent_activity = requests.get(f"{API_BASE}/dashboard/agents/activity", params={"days": 7}, timeout=10).json()
    funnel = requests.get(f"{API_BASE}/dashboard/funnel", timeout=10).json()
    pipeline_states = requests.get(f"{API_BASE}/dashboard/pipeline-states", params={"limit": 200}, timeout=10).json()
    aging = requests.get(f"{API_BASE}/dashboard/pipeline-aging", params={"hours_threshold": 24}, timeout=10).json()
    hot_alerts = requests.get(
        f"{API_BASE}/dashboard/hot-alerts", params={"limit": 20, "stale_hours": 24}, timeout=10
    ).json()
    queue_metrics = requests.get(
        f"{API_BASE}/dashboard/commercial/queue-metrics", params={"hours_threshold": 24}, timeout=10
    ).json()
except Exception as exc:
    st.error(f"No se pudo conectar con la API: {exc}")
    st.stop()

# ── 1. Alertas HOT (arriba del pliegue) ────────────────────────────────────────
severity = hot_alerts.get("severity", {})
critical = severity.get("CRITICAL", 0)
high_sev = severity.get("HIGH", 0)
if critical > 0:
    st.error(f"CRÍTICO — {critical} prospecto(s) HOT sin seguimiento. Acción inmediata requerida.")
elif high_sev > 0:
    st.warning(f"ALTO — {high_sev} prospecto(s) HOT con más de 48 h sin contacto.")

# ── 2. Métricas del ecosistema ─────────────────────────────────────────────────
st.divider()
q_counts = queue_metrics.get("counts", {})
eco1, eco2, eco3, eco4, eco5 = st.columns(5)
eco1.metric("Descubiertos", summary.get("total_sites", 0), help="Prospectos en base de datos")
eco2.metric("Auditados", funnel.get("with_agent_run", 0), help="Analizados por cadena de agentes")
eco3.metric("HOT leads", funnel.get("hot", 0), help="Score ≥ 80")
eco4.metric("Cola pendiente", q_counts.get("pending", 0), help="Propuestas esperando aprobación")
eco5.metric("Sin chatbot", summary.get("without_chatbot", 0), help="Oportunidad directa para Netty")

# ── 3. Funnel visual ───────────────────────────────────────────────────────────
st.divider()
st.subheader("Embudo operativo")
stages = {
    "Descubiertos": funnel.get("discovered", 0),
    "Carga OK": funnel.get("loaded_ok", 0),
    "Clasificados": funnel.get("scored", 0),
    "Agentes": funnel.get("with_agent_run", 0),
    "HOT": funnel.get("hot", 0),
    "Cola lista": funnel.get("queue_ready", 0),
}
f_top = stages["Descubiertos"] or 1
fcols = st.columns(len(stages))
for i, (label, val) in enumerate(stages.items()):
    pct = round((val / f_top) * 100)
    fcols[i].metric(label, val, delta=f"{pct}% del total", delta_color="off")

conv = funnel.get("conversions", {})
if conv:
    st.caption(
        f"Discover → Load OK: {conv.get('discover_to_load_ok_pct', 0)}%  |  "
        f"Scored → HOT: {conv.get('scored_to_hot_pct', 0)}%  |  "
        f"HOT → Cola: {conv.get('hot_to_queue_ready_pct', 0)}%"
    )

# ── 4. Actividad diaria ────────────────────────────────────────────────────────
st.divider()
st.subheader("Actividad de agentes — 7 días")
activity_rows = agent_activity.get("activity", [])
if activity_rows:
    act_df = pd.DataFrame(activity_rows).set_index("date")
    st.bar_chart(act_df[["runs", "hot"]])
    a1, a2, a3, a4 = st.columns(4)
    a1.metric("Total runs", agent_summary.get("total_agent_runs", 0))
    a2.metric("HOT runs", agent_summary.get("hot_agent_runs", 0))
    a3.metric("HOT %", agent_summary.get("hot_ratio_pct", 0))
    a4.metric("OK %", agent_summary.get("ok_ratio_pct", 0))
    with st.expander("Top agentes por ejecuciones"):
        st.dataframe(pd.DataFrame(agent_summary.get("top_agents", [])), use_container_width=True)
else:
    st.info("Sin actividad de agentes en los últimos 7 días")

# ── 5. Señales comerciales + tecnologías ───────────────────────────────────────
st.divider()
st.subheader("Señales comerciales")
s1, s2, s3, s4, s5, s6 = st.columns(6)
s1.metric("Total sitios", summary.get("total_sites", 0))
s2.metric("Con WhatsApp", summary.get("with_whatsapp", 0))
s3.metric("Con eCommerce", summary.get("with_ecommerce", 0))
s4.metric("WordPress %", f"{summary.get('pct_wordpress', 0)}%")
s5.metric("Shopify %", f"{summary.get('pct_shopify', 0)}%")
s6.metric("HTML estático %", f"{summary.get('pct_html_estatico', 0)}%")

# ── 6. Pipeline de jobs ────────────────────────────────────────────────────────
sc = pipeline_states.get("status_counts", {})
ag = aging.get("aging", {})
js1, js2, js3, js4, js5 = st.columns(5)
js1.metric("Jobs en cola", sc.get("queued", 0))
js2.metric("Ejecutando", sc.get("running", 0))
js3.metric("Completados", sc.get("done", 0))
js4.metric("Con error", sc.get("error", 0))
js5.metric("Sin run (prospectos)", ag.get("no_run", 0))

with st.expander("Jobs detalle + aging"):
    st.dataframe(pd.DataFrame(pipeline_states.get("items", [])), use_container_width=True)
    ac1, ac2, ac3 = st.columns(3)
    ac1.metric("Sin run", ag.get("no_run", 0))
    ac2.metric("Run stale >24h", ag.get("stale_run", 0))
    ac3.metric("Run fresco", ag.get("fresh_run", 0))
    st.dataframe(pd.DataFrame(aging.get("stale_items", [])), use_container_width=True)

# ── 7. Alertas HOT detalladas ──────────────────────────────────────────────────
st.divider()
st.subheader("Alertas HOT")
al1, al2, al3, al4 = st.columns(4)
al1.metric("CRÍTICO", severity.get("CRITICAL", 0))
al2.metric("ALTO", severity.get("HIGH", 0))
al3.metric("MEDIO", severity.get("MEDIUM", 0))
al4.metric("BAJO", severity.get("LOW", 0))

alerts_df = pd.DataFrame(hot_alerts.get("alerts", []))
if not alerts_df.empty:
    priority_cols = [
        c
        for c in ["domain", "score", "alert_level", "alert_reason", "age_hours", "sla_bucket"]
        if c in alerts_df.columns
    ]
    st.dataframe(alerts_df[priority_cols], use_container_width=True)
else:
    st.success("Sin alertas HOT activas")

# ── 8. Cola CRM operativa ──────────────────────────────────────────────────────
st.divider()
st.subheader("Cola CRM operativa")
qc1, qc2, qc3, qc4, qc5 = st.columns(5)
qc1.metric("Pendiente", q_counts.get("pending", 0))
qc2.metric("Aprobado", q_counts.get("approved", 0))
qc3.metric("Rechazado", q_counts.get("rejected", 0))
qc4.metric("Enviado", q_counts.get("sent", 0))
qc5.metric("Aprobación avg (h)", queue_metrics.get("approval_time_avg_hours") or "—")

q1, q2 = st.columns(2)
queue_status = q1.selectbox("Estado", ["pending", "approved", "rejected", "sent"], index=0)
queue_limit = q2.number_input("Límite", min_value=1, max_value=500, value=50, step=1, key="qlimit")

queue_ops = requests.get(
    f"{API_BASE}/commercial/queue", params={"status": queue_status, "limit": int(queue_limit)}, timeout=20
).json()
queue_ops_df = pd.DataFrame(queue_ops.get("items", []))
if not queue_ops_df.empty:
    st.dataframe(queue_ops_df, use_container_width=True)
else:
    st.info("Sin ítems en cola para el estado seleccionado")

with st.expander("Acciones de aprobación"):
    st.write("**Aprobación individual**")
    qa1, qa2, qa3 = st.columns(3)
    queue_item_id = qa1.text_input("Queue item ID")
    queue_actor = qa2.text_input("Actor", value="ops_user")
    queue_approve = qa3.checkbox("Aprobar (sin check = rechazar)", value=True)
    if st.button("Aplicar aprobación") and queue_item_id:
        r = requests.post(
            f"{API_BASE}/commercial/queue/{queue_item_id}/approval",
            json={"approve": bool(queue_approve), "actor": queue_actor or "ops_user"},
            timeout=20,
        )
        st.json(r.json())

    st.write("**Despacho**")
    qd1, qd2 = st.columns(2)
    dispatch_item_id = qd1.text_input("Queue item ID aprobado")
    dispatch_actor = qd2.text_input("Actor dispatch", value="ops_dispatcher")
    if st.button("Simular dispatch") and dispatch_item_id:
        r = requests.post(
            f"{API_BASE}/commercial/queue/{dispatch_item_id}/simulate-dispatch",
            json={"actor": dispatch_actor or "ops_dispatcher"},
            timeout=20,
        )
        st.json(r.json())

    st.write("**Aprobación / Rechazo masivo**")
    qb1, qb2, qb3, qb4 = st.columns(4)
    bulk_actor = qb1.text_input("Actor bulk", value="ops_manager")
    bulk_channel = qb2.selectbox("Canal", ["", "email", "whatsapp"], index=0)
    bulk_max = qb3.number_input("Max items", min_value=1, max_value=500, value=50, step=1)
    bulk_approve = qb4.checkbox("Bulk approve", value=False)
    if st.button("Ejecutar bulk"):
        r = requests.post(
            f"{API_BASE}/commercial/queue/bulk-approval",
            json={
                "approve": bool(bulk_approve),
                "actor": bulk_actor or "ops_manager",
                "status_filter": "pending",
                "channel": bulk_channel or None,
                "max_items": int(bulk_max),
            },
            timeout=30,
        )
        st.json(r.json())

with st.expander("Auditoría de cola"):
    audit_limit = st.number_input("Límite auditoría", min_value=1, max_value=500, value=100, step=1)
    audit_qid = st.text_input("Filtrar por queue_item_id", value="")
    audit_params: dict = {"limit": int(audit_limit)}
    if audit_qid:
        audit_params["queue_item_id"] = audit_qid
    audit = requests.get(f"{API_BASE}/commercial/queue/audit", params=audit_params, timeout=20).json()
    st.dataframe(pd.DataFrame(audit.get("items", [])), use_container_width=True)

# ── 9. Sales Queue ─────────────────────────────────────────────────────────────
st.divider()
st.subheader("Sales Queue")
sq1, sq2, sq3 = st.columns(3)
sq_limit = sq1.number_input("Límite", min_value=1, max_value=500, value=50, step=1, key="sq_limit")
sq_min_score = sq2.number_input("Score mínimo", min_value=0, max_value=100, value=60, step=1)
sq_stale = sq3.number_input("Stale (horas)", min_value=1, max_value=720, value=24, step=1)

queue_resp = requests.get(
    f"{API_BASE}/dashboard/sales-queue",
    params={"limit": int(sq_limit), "min_score": int(sq_min_score), "stale_hours": int(sq_stale)},
    timeout=20,
).json()
queue_df = pd.DataFrame(queue_resp.get("items", []))
if not queue_df.empty:
    sort_col = "score" if "score" in queue_df.columns else None
    st.dataframe(queue_df.sort_values(sort_col, ascending=False) if sort_col else queue_df, use_container_width=True)
else:
    st.info("Sales queue vacía con los parámetros actuales")

sqe1, sqe2 = st.columns(2)
sq_export_params = {"limit": int(sq_limit), "min_score": int(sq_min_score), "stale_hours": int(sq_stale)}
if sqe1.button("Exportar CSV"):
    st.write(requests.get(f"{API_BASE}/export/sales-queue-csv", params=sq_export_params, timeout=30).json())
if sqe2.button("Exportar XLSX"):
    st.write(requests.get(f"{API_BASE}/export/sales-queue-xlsx", params=sq_export_params, timeout=30).json())

# ── 10. Ranking prospectos ─────────────────────────────────────────────────────
st.divider()
st.subheader("Ranking prospectos")

with st.expander("Filtros CRM", expanded=False):
    fc1, fc2, fc3 = st.columns(3)
    technology = fc1.text_input("Tecnología (CMS/ecommerce/frontend)", value="")
    rubro = fc2.text_input("Rubro", value="")
    provincia = fc3.text_input("Provincia", value="")
    min_score, max_score = st.slider("Score Netty Fit", 0, 100, (0, 100))
    fx1, fx2, fx3, fx4 = st.columns(4)
    sin_chatbot = fx1.checkbox("Solo sin chatbot")
    tiene_whatsapp = fx2.checkbox("Solo con WhatsApp")
    con_actividad = fx3.checkbox("Con actividad agentes")
    hot_combo = fx4.checkbox("HOT + sin chatbot + WA")
    sin_run_horas = st.number_input("Sin run reciente (horas)", min_value=0, max_value=720, value=0, step=1)

params: dict = {"min_score": min_score, "max_score": max_score}
if technology:
    params["technology"] = technology
if rubro:
    params["rubro"] = rubro
if provincia:
    params["provincia"] = provincia
if sin_chatbot:
    params["sin_chatbot"] = True
if tiene_whatsapp:
    params["tiene_whatsapp"] = True
if con_actividad:
    params["con_actividad_agentes"] = True
if hot_combo:
    params["hot_sin_chatbot_con_whatsapp"] = True
if sin_run_horas > 0:
    params["sin_run_reciente_horas"] = int(sin_run_horas)

prospects = requests.get(f"{API_BASE}/dashboard/prospects", params=params, timeout=20).json()
df = pd.DataFrame(prospects)
if not df.empty and "netty_fit_score" in df.columns:
    st.dataframe(df.sort_values("netty_fit_score", ascending=False), use_container_width=True)
else:
    st.info("Sin resultados con los filtros actuales")

with st.expander("Detalle de prospecto"):
    prospect_id = st.number_input("ID prospecto", min_value=1, step=1)
    dc1, dc2, dc3 = st.columns(3)
    if dc1.button("Ver detalle"):
        st.json(requests.get(f"{API_BASE}/dashboard/prospects/{int(prospect_id)}", timeout=10).json())
    if dc2.button("Vista comercial"):
        st.json(requests.get(f"{API_BASE}/dashboard/prospects/{int(prospect_id)}/commercial-view", timeout=10).json())
    if dc3.button("Next Best Action"):
        st.json(requests.get(f"{API_BASE}/dashboard/prospects/{int(prospect_id)}/next-best-action", timeout=10).json())

# ── 11. Pipeline comercial ─────────────────────────────────────────────────────
st.divider()
with st.expander("Pipeline comercial (discover → scan → export)"):
    cp1, cp2, cp3, cp4 = st.columns(4)
    p_rubro = cp1.text_input("Rubro", value="restaurantes")
    p_prov = cp2.text_input("Provincia", value="Panamá")
    p_limit = cp3.number_input("Límite", min_value=1, max_value=500, value=20, step=1, key="pl")
    p_hot = cp4.number_input("Score hot", min_value=0, max_value=100, value=80, step=1)
    pl_payload = {
        "rubro": p_rubro or None,
        "provincia": p_prov or None,
        "limit": int(p_limit),
        "min_hot_score": int(p_hot),
    }
    cpa, cpb = st.columns(2)
    if cpa.button("Ejecutar (sync)"):
        st.json(requests.post(f"{API_BASE}/pipeline/discover-scan-export", json=pl_payload, timeout=300).json())
    if cpb.button("Ejecutar (async)"):
        st.json(requests.post(f"{API_BASE}/pipeline/discover-scan-export/async", json=pl_payload, timeout=30).json())
    job_id = st.text_input("Consultar job_id")
    if st.button("Ver estado job") and job_id:
        st.json(requests.get(f"{API_BASE}/pipeline/jobs/{job_id}", timeout=30).json())

# ── 12. Exportaciones ──────────────────────────────────────────────────────────
st.divider()
st.subheader("Exportaciones")
col1, col2, col3 = st.columns(3)
if col1.button("Exportar CSV"):
    st.write(requests.get(f"{API_BASE}/export/csv", timeout=30).json())
if col2.button("Exportar XLSX"):
    st.write(requests.get(f"{API_BASE}/export/xlsx", timeout=30).json())
if col3.button("Exportar PDF resumen"):
    st.write(requests.get(f"{API_BASE}/export/pdf-summary", timeout=30).json())
