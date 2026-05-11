import pandas as pd
import requests
import streamlit as st

API_BASE = st.sidebar.text_input("API Base URL", value="http://localhost:8000")

st.title("Netty Prospect Scanner Dashboard")

if st.button("Refrescar resumen"):
    st.rerun()

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

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total sitios", summary.get("total_sites", 0))
c2.metric("Sin chatbot", summary.get("without_chatbot", 0))
c3.metric("Con WhatsApp", summary.get("with_whatsapp", 0))
c4.metric("Con eCommerce", summary.get("with_ecommerce", 0))

st.subheader("Actividad multiagente")
a1, a2, a3, a4 = st.columns(4)
a1.metric("Runs agentes", agent_summary.get("total_agent_runs", 0))
a2.metric("HOT runs", agent_summary.get("hot_agent_runs", 0))
a3.metric("HOT %", agent_summary.get("hot_ratio_pct", 0))
a4.metric("OK %", agent_summary.get("ok_ratio_pct", 0))

st.write("Top agentes por actividad")
st.dataframe(pd.DataFrame(agent_summary.get("top_agents", [])), use_container_width=True)

st.write("Actividad diaria (7 días)")
st.dataframe(pd.DataFrame(agent_activity.get("activity", [])), use_container_width=True)

st.subheader("Embudo operativo (Etapa 3)")
f1, f2, f3, f4, f5, f6 = st.columns(6)
f1.metric("Discovered", funnel.get("discovered", 0))
f2.metric("Load OK", funnel.get("loaded_ok", 0))
f3.metric("Scored", funnel.get("scored", 0))
f4.metric("Agent Run", funnel.get("with_agent_run", 0))
f5.metric("HOT", funnel.get("hot", 0))
f6.metric("Queue Ready", funnel.get("queue_ready", 0))

st.write("Conversiones de embudo (%)")
st.write(funnel.get("conversions", {}))

st.subheader("Pipeline por estados")
st.write("Estados")
st.write(pipeline_states.get("status_counts", {}))
st.write("Fases")
st.write(pipeline_states.get("phase_counts", {}))
st.dataframe(pd.DataFrame(pipeline_states.get("items", [])), use_container_width=True)

st.subheader("Aging pipeline")
st.write(aging.get("aging", {}))
st.dataframe(pd.DataFrame(aging.get("stale_items", [])), use_container_width=True)

st.subheader("Alertas HOT")
st.write("Severidad SLA")
st.write(hot_alerts.get("severity", {}))
alerts_df = pd.DataFrame(hot_alerts.get("alerts", []))
if not alerts_df.empty:
    st.dataframe(alerts_df, use_container_width=True)
else:
    st.info("Sin alertas HOT por ahora")

st.subheader("Tecnologías (%)")
st.write(
    {
        "WordPress": summary.get("pct_wordpress", 0),
        "Shopify": summary.get("pct_shopify", 0),
        "Magento": summary.get("pct_magento", 0),
        "HTML estático": summary.get("pct_html_estatico", 0),
    }
)

st.subheader("Filtros CRM")
technology = st.text_input("Tecnología (cms/ecommerce/frontend)", value="")
min_score, max_score = st.slider("Score", 0, 100, (0, 100))
rubro = st.text_input("Rubro", value="")
provincia = st.text_input("Provincia", value="")
sin_chatbot = st.checkbox("Solo sin chatbot")
tiene_whatsapp = st.checkbox("Solo con WhatsApp")
con_actividad = st.checkbox("Solo con actividad de agentes")
hot_combo = st.checkbox("HOT + sin chatbot + con WhatsApp")
sin_run_horas = st.number_input("Sin run reciente (horas)", min_value=0, max_value=720, value=0, step=1)

params = {
    "min_score": min_score,
    "max_score": max_score,
}
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
st.subheader("Ranking prospectos")
if not df.empty and "netty_fit_score" in df.columns:
    st.dataframe(df.sort_values("netty_fit_score", ascending=False), use_container_width=True)
else:
    st.info("Sin resultados")

st.subheader("Detalle de prospecto")
prospect_id = st.number_input("ID prospecto", min_value=1, step=1)
if st.button("Ver detalle"):
    detail = requests.get(f"{API_BASE}/dashboard/prospects/{int(prospect_id)}", timeout=10).json()
    st.json(detail)

if st.button("Ver vista comercial consolidada"):
    commercial = requests.get(f"{API_BASE}/dashboard/prospects/{int(prospect_id)}/commercial-view", timeout=10).json()
    st.json(commercial)

if st.button("Ver Next Best Action (NBA)"):
    nba = requests.get(f"{API_BASE}/dashboard/prospects/{int(prospect_id)}/next-best-action", timeout=10).json()
    st.json(nba)

st.subheader("Sales Queue (cola operativa vendedor)")
sq1, sq2, sq3 = st.columns(3)
sq_limit = sq1.number_input("Límite queue", min_value=1, max_value=500, value=50, step=1)
sq_min_score = sq2.number_input("Score mínimo queue", min_value=0, max_value=100, value=60, step=1)
sq_stale = sq3.number_input("Stale horas", min_value=1, max_value=720, value=24, step=1)

queue_resp = requests.get(
    f"{API_BASE}/dashboard/sales-queue",
    params={"limit": int(sq_limit), "min_score": int(sq_min_score), "stale_hours": int(sq_stale)},
    timeout=20,
).json()
queue_df = pd.DataFrame(queue_resp.get("items", []))
if not queue_df.empty:
    st.dataframe(queue_df, use_container_width=True)
else:
    st.info("Sales queue vacía con parámetros actuales")

sqe1, sqe2 = st.columns(2)
if sqe1.button("Exportar Sales Queue CSV"):
    st.write(
        requests.get(
            f"{API_BASE}/export/sales-queue-csv",
            params={"limit": int(sq_limit), "min_score": int(sq_min_score), "stale_hours": int(sq_stale)},
            timeout=30,
        ).json()
    )
if sqe2.button("Exportar Sales Queue XLSX"):
    st.write(
        requests.get(
            f"{API_BASE}/export/sales-queue-xlsx",
            params={"limit": int(sq_limit), "min_score": int(sq_min_score), "stale_hours": int(sq_stale)},
            timeout=30,
        ).json()
    )

st.subheader("Pipeline comercial (discover → scan → export)")
cp1, cp2, cp3, cp4 = st.columns(4)
p_rubro = cp1.text_input("Rubro pipeline", value="restaurantes")
p_prov = cp2.text_input("Provincia pipeline", value="Panamá")
p_limit = cp3.number_input("Límite", min_value=1, max_value=500, value=20, step=1)
p_hot = cp4.number_input("Score hot", min_value=0, max_value=100, value=80, step=1)

payload = {"rubro": p_rubro or None, "provincia": p_prov or None, "limit": int(p_limit), "min_hot_score": int(p_hot)}

cpa, cpb = st.columns(2)
if cpa.button("Ejecutar pipeline (sync)"):
    r = requests.post(f"{API_BASE}/pipeline/discover-scan-export", json=payload, timeout=300)
    st.json(r.json())

if cpb.button("Ejecutar pipeline (async)"):
    r = requests.post(f"{API_BASE}/pipeline/discover-scan-export/async", json=payload, timeout=30)
    st.json(r.json())

job_id = st.text_input("Consultar job_id")
if st.button("Ver estado job") and job_id:
    r = requests.get(f"{API_BASE}/pipeline/jobs/{job_id}", timeout=30)
    st.json(r.json())

st.subheader("Operación comercial (Etapa 4)")

st.write("Métricas SLA de cola")
qm1, qm2, qm3 = st.columns(3)
qm1.metric("Pending", queue_metrics.get("counts", {}).get("pending", 0))
qm2.metric("Approval avg (h)", queue_metrics.get("approval_time_avg_hours") or "n/a")
qm3.metric("Bulk efficiency %", queue_metrics.get("bulk_efficiency_pct", 0))
st.write(queue_metrics.get("pending_aging", {}))

q1, q2 = st.columns(2)
queue_status = q1.selectbox("Estado cola", ["pending", "approved", "rejected", "sent"], index=0)
queue_limit = q2.number_input("Límite cola", min_value=1, max_value=500, value=50, step=1)

queue_ops = requests.get(
    f"{API_BASE}/commercial/queue", params={"status": queue_status, "limit": int(queue_limit)}, timeout=20
).json()
queue_ops_df = pd.DataFrame(queue_ops.get("items", []))
if not queue_ops_df.empty:
    st.dataframe(queue_ops_df, use_container_width=True)
else:
    st.info("Sin ítems en cola para el estado seleccionado")

st.write("Aprobación individual")
qa1, qa2, qa3 = st.columns(3)
queue_item_id = qa1.text_input("Queue item ID")
queue_actor = qa2.text_input("Actor aprobación", value="ops_user")
queue_approve = qa3.checkbox("Aprobar (si no, rechaza)", value=True)
if st.button("Aplicar aprobación individual") and queue_item_id:
    r = requests.post(
        f"{API_BASE}/commercial/queue/{queue_item_id}/approval",
        json={"approve": bool(queue_approve), "actor": queue_actor or "ops_user"},
        timeout=20,
    )
    st.json(r.json())

st.write("Simulación de dispatch (sin envío real)")
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

st.write("Aprobación/Rechazo masivo")
qb1, qb2, qb3, qb4 = st.columns(4)
bulk_actor = qb1.text_input("Actor bulk", value="ops_manager")
bulk_channel = qb2.selectbox("Canal bulk", ["", "email", "whatsapp"], index=0)
bulk_max = qb3.number_input("Max items bulk", min_value=1, max_value=500, value=50, step=1)
bulk_approve = qb4.checkbox("Bulk approve (si no, bulk reject)", value=False)

if st.button("Ejecutar bulk"):
    payload_bulk = {
        "approve": bool(bulk_approve),
        "actor": bulk_actor or "ops_manager",
        "status_filter": "pending",
        "channel": bulk_channel or None,
        "max_items": int(bulk_max),
    }
    r = requests.post(f"{API_BASE}/commercial/queue/bulk-approval", json=payload_bulk, timeout=30)
    st.json(r.json())

st.write("Auditoría de cola")
audit_limit = st.number_input("Límite auditoría", min_value=1, max_value=500, value=100, step=1)
audit_qid = st.text_input("Filtrar auditoría por queue_item_id", value="")
audit_params = {"limit": int(audit_limit)}
if audit_qid:
    audit_params["queue_item_id"] = audit_qid

audit = requests.get(f"{API_BASE}/commercial/queue/audit", params=audit_params, timeout=20).json()
st.dataframe(pd.DataFrame(audit.get("items", [])), use_container_width=True)

st.subheader("Exportaciones")
col1, col2, col3 = st.columns(3)
if col1.button("Exportar CSV"):
    st.write(requests.get(f"{API_BASE}/export/csv", timeout=30).json())
if col2.button("Exportar XLSX"):
    st.write(requests.get(f"{API_BASE}/export/xlsx", timeout=30).json())
if col3.button("Exportar PDF resumen"):
    st.write(requests.get(f"{API_BASE}/export/pdf-summary", timeout=30).json())
