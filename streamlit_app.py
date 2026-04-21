import time
from dataclasses import dataclass
from typing import Dict, Any, Optional, List

import requests
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title="AI Due Diligence Dashboard V2", layout="wide", initial_sidebar_state="expanded")

# ---------------------------
# API helpers
# ---------------------------
@dataclass
class ApiConfig:
    base_url: str
    api_key: str

def api_headers(cfg: ApiConfig) -> Dict[str, str]:
    h = {"Content-Type": "application/json"}
    if cfg.api_key.strip():
        h["x-api-key"] = cfg.api_key.strip()
    return h

def call_json(method: str, url: str, cfg: ApiConfig, payload: Optional[dict] = None, timeout: int = 60) -> Dict[str, Any]:
    r = requests.request(method=method, url=url, headers=api_headers(cfg), json=payload, timeout=timeout)
    try:
        data = r.json()
    except Exception:
        data = {"raw": r.text}
    if not r.ok:
        raise RuntimeError(f"HTTP {r.status_code} {r.reason} - {data}")
    return data

# ---------------------------
# UI helpers (styling)
# ---------------------------
def decision_style(decision: str):
    d = (decision or "").upper()
    if d == "ALLOW":
        return ("ALLOW", "#16a34a", "#dcfce7")
    if d == "REVIEW":
        return ("REVIEW", "#f59e0b", "#fef3c7")
    if d == "BLOCK":
        return ("BLOCK", "#dc2626", "#fee2e2")
    return (d or "UNKNOWN", "#6b7280", "#f3f4f6")

def risk_color(level: str):
    lv = (level or "").upper()
    if lv == "LOW":
        return "#16a34a"
    if lv == "MEDIUM":
        return "#f59e0b"
    if lv == "HIGH":
        return "#dc2626"
    return "#6b7280"

def render_decision_badge(decision: str):
    label, bg, _ = decision_style(decision)
    st.markdown(
        f"""
        <div style="display:inline-block;padding:10px 20px;border-radius:999px;
        background:{bg};color:white;font-weight:800;font-size:18px;text-align:center;">
            {label}
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_reason_chips(reasons: List[str]):
    if not reasons:
        st.info("No reasons provided.")
        return
    html = '<div style="display:flex;flex-wrap:wrap;gap:8px;">'
    for r in reasons:
        html += f'<span style="background:#1e293b;color:#e2e8f0;padding:6px 12px;border-radius:20px;font-size:13px;">{r}</span>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

def contribution_gauge(risk_score: float, risk_level: str):
    """Affiche un indicateur circulaire pour le risque."""
    color = risk_color(risk_level)
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = risk_score,
        title = {'text': "Risk Score", 'font': {'size': 20}},
        gauge = {
            'axis': {'range': [0, 1], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': color},
            'steps': [
                {'range': [0, 0.4], 'color': "#dcfce7"},
                {'range': [0.4, 0.7], 'color': "#fef3c7"},
                {'range': [0.7, 1], 'color': "#fee2e2"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': risk_score
            }
        }
    ))
    fig.update_layout(height=250, margin=dict(l=30, r=30, t=50, b=30))
    return fig

def plot_contributions(contributions: List[Dict]):
    """Graphique à barres horizontales des contributions pondérées."""
    if not contributions:
        return None
    df = pd.DataFrame(contributions)
    df["color"] = df["component"].apply(lambda x: "#3b82f6" if "reduction" not in x else "#ef4444")
    fig = px.bar(df, x="contribution", y="component", orientation='h', 
                 text="contribution", title="Feature Contributions (weighted)",
                 color="color", color_discrete_map="identity")
    fig.update_traces(texttemplate='%{text:.3f}', textposition='outside')
    fig.update_layout(height=300, xaxis_title="Contribution to Risk Score", yaxis_title="")
    return fig

# ---------------------------
# Sidebar
# ---------------------------
st.sidebar.title("⚙️ Settings")
base_url = st.sidebar.text_input("FastAPI Base URL", "http://127.0.0.1:8000")
api_key = st.sidebar.text_input("API Key (x-api-key)", "super-secret-key", type="password")
cfg = ApiConfig(base_url=base_url.rstrip("/"), api_key=api_key)

st.sidebar.markdown("---")
st.sidebar.caption("Workflow: Create service → Run assessment → Poll status → Display result + history")
st.sidebar.markdown("---")
st.sidebar.info("Use the form to assess an AI SaaS provider. Results include risk score, decision, and explainability.")

# ---------------------------
# Main layout
# ---------------------------
st.title("🛡️ AI Due Diligence Dashboard V2")
st.caption("Zero-Trust Assessment for AI SaaS/API providers")

# Formulaire en deux colonnes avec des onglets ou non (ici simple)
with st.form("service_form", clear_on_submit=False):
    col1, col2 = st.columns(2)
    with col1:
        service_name = st.text_input("Service Name", "Mock AI SaaS")
        service_url = st.text_input("Service URL", "https://example.com")
        service_type = st.selectbox("Service Type", ["AI API", "SaaS", "Cloud Tool", "Other"], index=0)
        provider = st.text_input("Provider", "Mock Inc")
        auth_method = st.selectbox("Auth Method", ["api_key", "oauth", "none", "basic"], index=0)
    with col2:
        num_vuln = st.number_input("Known Vulnerabilities", min_value=0, max_value=999, value=2, step=1)
        encryption_present = st.checkbox("Encryption Present", value=False)
        reputation_score_external = st.slider("Reputation Score External", 0.0, 1.0, 0.2, 0.01)
        blacklist_flag = st.checkbox("Blacklist Flag", value=False)
        gdpr_compliant = st.checkbox("GDPR Compliant", value=False)
    submitted = st.form_submit_button("🚀 Run Full Assessment", use_container_width=True)

if submitted:
    logs = []
    def log(msg: str):
        logs.append(f"[{time.strftime('%H:%M:%S')}] {msg}")

    try:
        payload = {
            "service_name": service_name,
            "service_url": service_url,
            "service_type": service_type,
            "provider": provider,
            "auth_method": auth_method,
            "num_known_vulnerabilities": int(num_vuln),
            "encryption_present": encryption_present,
            "reputation_score_external": float(reputation_score_external),
            "blacklist_flag": blacklist_flag,
            "gdpr_compliant": gdpr_compliant,
        }

        # 1. Create service
        log("Creating service...")
        created = call_json("POST", f"{cfg.base_url}/assessment/service", cfg, payload=payload, timeout=60)
        service_id = created["service_id"]
        log(f"Service created. service_id={service_id}")

        # 2. Run assessment
        log("Starting assessment...")
        run = call_json("POST", f"{cfg.base_url}/assessment/run/{service_id}", cfg, timeout=60)
        assessment_id = run["assessment_id"]
        log(f"Assessment started. assessment_id={assessment_id}")

        # 3. Poll status
        log("Polling assessment status...")
        details = None
        for _ in range(60):
            details = call_json("GET", f"{cfg.base_url}/assessment/{assessment_id}", cfg, timeout=60)
            if details.get("status") in ("done", "failed"):
                break
            time.sleep(1)

        if not details:
            raise RuntimeError("No details returned from assessment endpoint.")

        # 4. Fetch raw data for contributions and policy
        raw = call_json("GET", f"{cfg.base_url}/assessment/raw/{assessment_id}", cfg, timeout=60)

        # ---- Display results in a structured way ----
        st.success("Assessment completed successfully!")

        # Row 1: Key metrics
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Assessment ID", details.get("assessment_id"))
        col2.metric("Risk Score", f"{details.get('risk_score'):.4f}")
        col3.metric("Risk Level", details.get("risk_level"))
        col4.metric("Confidence", f"{details.get('confidence', 0):.2%}")

        # Row 2: Decision badge and reasons
        st.markdown("### 🧭 Final Decision")
        render_decision_badge(details.get("decision"))
        st.markdown("### 🧾 Justifications")
        render_reason_chips(details.get("reasons", []))

        # Row 3: Policy engine details
        with st.expander("Policy Engine Details", expanded=False):
            st.markdown(f"**Policy ID:** `{raw.get('policy_id')}`")
            st.markdown(f"**Policy Reason:** {raw.get('policy_reason')}")
            policy_matches = raw.get("policy_matches", [])
            if policy_matches:
                st.dataframe(pd.DataFrame(policy_matches), use_container_width=True)

        # Row 4: Gauge + Contributions side by side
        st.markdown("### 📊 Risk Analysis")
        left, right = st.columns([1, 1.5])
        with left:
            gauge = contribution_gauge(details.get("risk_score"), details.get("risk_level"))
            st.plotly_chart(gauge, use_container_width=True)
        with right:
            contributions = raw.get("contributions", [])
            if contributions:
                fig_contrib = plot_contributions(contributions)
                if fig_contrib:
                    st.plotly_chart(fig_contrib, use_container_width=True)
            else:
                st.info("No contribution data available.")

        # Row 5: Feature contribution table (detailed)
        st.markdown("### 📋 Detailed Feature Contributions")
        contrib_df = pd.DataFrame(contributions) if contributions else pd.DataFrame()
        if not contrib_df.empty:
            st.dataframe(contrib_df.style.format({
                "value": "{:.4f}",
                "weight": "{:.4f}",
                "contribution": "{:.4f}"
            }).background_gradient(subset=["contribution"], cmap="RdYlGn", vmin=-0.2, vmax=0.2), use_container_width=True)
        else:
            st.info("No contribution details found.")

        # Row 6: History with trend chart
        st.markdown("### 🕓 Assessment History")
        history = call_json("GET", f"{cfg.base_url}/assessment/history/{service_id}", cfg, timeout=60)
        items = history.get("items", [])
        if items:
            hist_df = pd.DataFrame(items)
            if "created_at" in hist_df.columns:
                hist_df["created_at"] = pd.to_datetime(hist_df["created_at"], errors="coerce")
            # Afficher les colonnes pertinentes
            display_cols = ["assessment_id", "created_at", "status", "risk_score", "risk_level", "decision", "confidence"]
            hist_df_display = hist_df[display_cols].copy()
            hist_df_display["risk_score"] = hist_df_display["risk_score"].round(4)
            st.dataframe(hist_df_display, use_container_width=True)
            # Tendance
            fig_trend = go.Figure()
            fig_trend.add_trace(go.Scatter(x=hist_df["assessment_id"], y=hist_df["risk_score"],
                                           mode="lines+markers", name="Risk Score",
                                           line=dict(color="#3b82f6", width=2),
                                           marker=dict(size=8)))
            fig_trend.update_layout(title="Risk Score Evolution Over Assessments",
                                    xaxis_title="Assessment ID",
                                    yaxis_title="Risk Score",
                                    yaxis=dict(range=[0, 1]),
                                    height=400)
            st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.info("No previous assessments for this service.")

        # Raw outputs (expander)
        with st.expander("🔍 Raw API Outputs (for debugging)"):
            st.json({
                "create_service": created,
                "run": run,
                "assessment": details,
                "assessment_raw": raw
            })

        with st.expander("📜 Execution Logs"):
            st.code("\n".join(logs), language="text")

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        with st.expander("Execution Logs"):
            st.code("\n".join(logs), language="text")

































# import time
# from dataclasses import dataclass
# from typing import Dict, Any, Optional, List

# import requests
# import streamlit as st
# import pandas as pd
# import plotly.graph_objects as go


# st.set_page_config(page_title="AI Due Diligence Dashboard V2", layout="wide")


# # ---------------------------
# # API helpers
# # ---------------------------
# @dataclass
# class ApiConfig:
#     base_url: str
#     api_key: str


# def api_headers(cfg: ApiConfig) -> Dict[str, str]:
#     h = {"Content-Type": "application/json"}
#     if cfg.api_key.strip():
#         h["x-api-key"] = cfg.api_key.strip()
#     return h


# def call_json(method: str, url: str, cfg: ApiConfig, payload: Optional[dict] = None, timeout: int = 60) -> Dict[str, Any]:
#     r = requests.request(method=method, url=url, headers=api_headers(cfg), json=payload, timeout=timeout)
#     try:
#         data = r.json()
#     except Exception:
#         data = {"raw": r.text}
#     if not r.ok:
#         raise RuntimeError(f"HTTP {r.status_code} {r.reason} - {data}")
#     return data


# # ---------------------------
# # UI helpers
# # ---------------------------
# def decision_style(decision: str):
#     d = (decision or "").upper()
#     if d == "ALLOW":
#         return ("ALLOW", "#16a34a")
#     if d == "REVIEW":
#         return ("REVIEW", "#f59e0b")
#     if d == "BLOCK":
#         return ("BLOCK", "#dc2626")
#     return (d or "UNKNOWN", "#6b7280")


# def risk_color(level: str):
#     lv = (level or "").upper()
#     if lv == "LOW":
#         return "#16a34a"
#     if lv == "MEDIUM":
#         return "#f59e0b"
#     if lv == "HIGH":
#         return "#dc2626"
#     return "#6b7280"


# def render_decision_badge(decision: str):
#     label, color = decision_style(decision)
#     st.markdown(
#         f"""
#         <div style="display:inline-block;padding:8px 14px;border-radius:999px;
#         background:{color};color:white;font-weight:800;font-size:14px;">
#             {label}
#         </div>
#         """,
#         unsafe_allow_html=True,
#     )


# def render_reason_chips(reasons: List[str]):
#     if not reasons:
#         st.info("No reasons provided.")
#         return
#     html = ""
#     for r in reasons:
#         html += f"""
#         <span style="
#             display:inline-block;
#             margin:4px;
#             padding:6px 10px;
#             border-radius:999px;
#             background:#111827;
#             color:#e5e7eb;
#             font-size:12px;
#             border:1px solid #374151;">
#             {r}
#         </span>
#         """
#     st.markdown(html, unsafe_allow_html=True)


# def contribution_table(features: Dict[str, Any]) -> pd.DataFrame:
#     # Approximate contribution table based on your scoring logic:
#     # risk = w_vulnerabilities*vulnerability_risk + w_config*config_risk + w_reputation*reputation_risk - compliance bonus effect
#     vuln = float(features.get("vulnerability_risk", 0.0) or 0.0)
#     conf = float(features.get("config_risk", 0.0) or 0.0)
#     rep = float(features.get("reputation_risk", 0.0) or 0.0)
#     comp = float(features.get("compliance_bonus", 0.0) or 0.0)

#     # default weights mirrored from backend defaults (can tune manually)
#     w_vuln, w_conf, w_rep = 0.40, 0.30, 0.30

#     rows = [
#         {"component": "vulnerability_risk", "value": vuln, "weight": w_vuln, "weighted": vuln * w_vuln},
#         {"component": "config_risk", "value": conf, "weight": w_conf, "weighted": conf * w_conf},
#         {"component": "reputation_risk", "value": rep, "weight": w_rep, "weighted": rep * w_rep},
#         {"component": "compliance_bonus (reduction)", "value": comp, "weight": -0.10, "weighted": -(comp * 0.10)},
#     ]
#     df = pd.DataFrame(rows)
#     df["value"] = df["value"].round(4)
#     df["weight"] = df["weight"].round(4)
#     df["weighted"] = df["weighted"].round(4)
#     return df


# # ---------------------------
# # Sidebar
# # ---------------------------
# st.sidebar.title("⚙️ Settings")
# base_url = st.sidebar.text_input("FastAPI Base URL", "http://127.0.0.1:8000")
# api_key = st.sidebar.text_input("API Key (x-api-key)", "super-secret-key", type="password")

# cfg = ApiConfig(base_url=base_url.rstrip("/"), api_key=api_key)

# st.sidebar.markdown("---")
# st.sidebar.caption("Workflow: Create service → Run assessment → Poll status → Display result + history")


# # ---------------------------
# # Main layout
# # ---------------------------
# st.title("🛡️ AI Due Diligence Dashboard V2")
# st.caption("Zero-Trust Assessment for AI SaaS/API providers")

# with st.form("service_form", clear_on_submit=False):
#     c1, c2 = st.columns(2)

#     with c1:
#         service_name = st.text_input("Service Name", "Mock AI SaaS")
#         service_url = st.text_input("Service URL", "https://example.com")
#         service_type = st.selectbox("Service Type", ["AI API", "SaaS", "Cloud Tool", "Other"], index=0)
#         provider = st.text_input("Provider", "Mock Inc")
#         auth_method = st.selectbox("Auth Method", ["api_key", "oauth", "none", "basic"], index=0)

#     with c2:
#         num_vuln = st.number_input("Known Vulnerabilities", min_value=0, max_value=999, value=2, step=1)
#         encryption_present = st.checkbox("Encryption Present", value=False)
#         reputation_score_external = st.slider("Reputation Score External", 0.0, 1.0, 0.2, 0.01)
#         blacklist_flag = st.checkbox("Blacklist Flag", value=False)
#         gdpr_compliant = st.checkbox("GDPR Compliant", value=False)

#     submitted = st.form_submit_button("🚀 Run Full Assessment")


# if submitted:
#     logs = []

#     def log(msg: str):
#         logs.append(f"[{time.strftime('%H:%M:%S')}] {msg}")

#     try:
#         payload = {
#             "service_name": service_name,
#             "service_url": service_url,
#             "service_type": service_type,
#             "provider": provider,
#             "auth_method": auth_method,
#             "num_known_vulnerabilities": int(num_vuln),
#             "encryption_present": encryption_present,
#             "reputation_score_external": float(reputation_score_external),
#             "blacklist_flag": blacklist_flag,
#             "gdpr_compliant": gdpr_compliant,
#         }

#         log("Creating service...")
#         created = call_json("POST", f"{cfg.base_url}/assessment/service", cfg, payload=payload, timeout=60)
#         service_id = created["service_id"]
#         log(f"Service created. service_id={service_id}")

#         log("Starting assessment...")
#         run = call_json("POST", f"{cfg.base_url}/assessment/run/{service_id}", cfg, timeout=60)
#         assessment_id = run["assessment_id"]
#         log(f"Assessment started. assessment_id={assessment_id}")

#         log("Polling assessment status...")
#         details = None
#         for _ in range(60):
#             details = call_json("GET", f"{cfg.base_url}/assessment/{assessment_id}", cfg, timeout=60)
#             if details.get("status") in ("done", "failed"):
#                 break
#             time.sleep(1)

        

#         # ---- NEW: raw explainability/policy/contributions ----
#         raw = call_json("GET", f"{cfg.base_url}/assessment/raw/{assessment_id}", cfg, timeout=60)

#         st.markdown("### 🧩 Policy Engine")
#         st.write(f"**Policy ID:** {raw.get('policy_id')}")
#         st.write(f"**Policy Reason:** {raw.get('policy_reason')}")

#         policy_matches = raw.get("policy_matches", [])
#         if policy_matches:
#             st.dataframe(pd.DataFrame(policy_matches), use_container_width=True)

#         st.markdown("### 📊 Feature Contributions")
#         contrib = raw.get("contributions", [])
#         if contrib:
#             st.dataframe(pd.DataFrame(contrib), use_container_width=True)
#         else:
#             st.info("No contributions found.")







#         if not details:
#             raise RuntimeError("No details returned from assessment endpoint.")

#         # Cards
#         top1, top2, top3, top4 = st.columns(4)
#         top1.metric("Assessment ID", details.get("assessment_id"))
#         top2.metric("Risk Score", details.get("risk_score"))
#         top3.metric("Risk Level", details.get("risk_level"))
#         top4.metric("Confidence", details.get("confidence"))

#         st.markdown("### 🧭 Decision")
#         render_decision_badge(details.get("decision"))

#         st.markdown("### 🧾 Reasons")
#         render_reason_chips(details.get("reasons", []))

#         # Pull full report JSON for features/explainability if available
#         report = call_json("GET", f"{cfg.base_url}/report/json/{assessment_id}", cfg, timeout=60)

#         # We need features for contribution table. If /report/json doesn't include it,
#         # we'll try a raw endpoint fallback pattern (optional).
#         features = {}
#         try:
#             # Optional endpoint if you add later:
#             raw = call_json("GET", f"{cfg.base_url}/assessment/raw/{assessment_id}", cfg, timeout=60)
#             features = raw.get("features_json", {})
#         except Exception:
#             # fallback: approximate from known result only
#             features = {}

#         st.markdown("### 📊 Feature Contribution Table")
#         if features:
#             df = contribution_table(features)
#             st.dataframe(df, use_container_width=True)
#         else:
#             st.info("Feature details endpoint not available yet. Showing minimal result only.")












#         # History
#         st.markdown("### 🕓 Assessment History (per service)")
#         history = call_json("GET", f"{cfg.base_url}/assessment/history/{service_id}", cfg, timeout=60)
#         items = history.get("items", [])

#         if items:
#             hist_df = pd.DataFrame(items)
#             if "created_at" in hist_df.columns:
#                 hist_df["created_at"] = pd.to_datetime(hist_df["created_at"], errors="coerce")
#             st.dataframe(
#                 hist_df[["assessment_id", "created_at", "status", "risk_score", "risk_level", "decision", "confidence"]],
#                 use_container_width=True
#             )

#             # Trend chart
#             chart_df = hist_df.sort_values("assessment_id")
#             fig = go.Figure()
#             fig.add_trace(go.Scatter(
#                 x=chart_df["assessment_id"],
#                 y=chart_df["risk_score"],
#                 mode="lines+markers",
#                 name="Risk Score",
#             ))
#             fig.update_layout(
#                 title="Risk Score Trend",
#                 xaxis_title="Assessment ID",
#                 yaxis_title="Risk Score",
#                 yaxis=dict(range=[0, 1]),
#                 height=350
#             )
#             st.plotly_chart(fig, use_container_width=True)
#         else:
#             st.info("No history found for this service yet.")

#         # Raw outputs
#         with st.expander("Raw API Outputs"):
#             # st.json({"create_service": created, "run": run, "assessment": details, "report_json": report})
#             st.json({
#             "create_service": created,
#             "run": run,
#             "assessment": details,
#             "assessment_raw": raw,   # add this
#             "report_json": report
#             })


#         with st.expander("Execution Logs"):
#             st.code("\n".join(logs), language="text")

#     except Exception as e:
#         st.error(str(e))
#         with st.expander("Execution Logs"):
#             st.code("\n".join(logs), language="text")