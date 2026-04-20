import json
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional, List
import requests
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# ----------------------------
# Config
# ----------------------------
st.set_page_config(page_title="AI Due Diligence Dashboard", layout="wide")

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
    r = requests.request(
        method=method,
        url=url,
        headers=api_headers(cfg),
        json=payload,
        timeout=timeout
    )
    # error detail
    try:
        data = r.json()
    except Exception:
        data = {"raw": r.text}
    if not r.ok:
        raise RuntimeError(f"HTTP {r.status_code} {r.reason} - {data}")
    return data

def badge_color(numeric_value: Optional[float], passed: Optional[bool]) -> str:
    # priority: explicit failure -> red
    if passed is False:
        return "#dc2626"
    if numeric_value is None:
        return "#f59e0b"  # unknown -> orange
    if numeric_value >= 0.70:
        return "#16a34a"
    if numeric_value >= 0.50:
        return "#f59e0b"
    return "#dc2626"

def badge_text(numeric_value: Optional[float], passed: Optional[bool]) -> str:
    if passed is False:
        return "RISK"
    if numeric_value is None:
        return "UNKNOWN"
    if numeric_value >= 0.70:
        return "GOOD"
    if numeric_value >= 0.50:
        return "MEDIUM"
    return "RISK"

def percent(numeric_value: Optional[float]) -> str:
    if numeric_value is None:
        return "N/A"
    return f"{round(numeric_value * 100)}%"

# ----------------------------
# Sidebar - API settings
# ----------------------------
st.sidebar.title("Settings")

base_url = st.sidebar.text_input("FastAPI base URL", value="http://127.0.0.1:8000")
api_key = st.sidebar.text_input("API Key (x-api-key)", value="", type="password")
cfg = ApiConfig(base_url=base_url.rstrip("/"), api_key=api_key)

st.sidebar.markdown("---")
st.sidebar.caption("If your backend requires API key, provide it here.")

# ----------------------------
# Main UI - Input form
# ----------------------------
st.title("AI Due Diligence Dashboard")
st.caption("Streamlit UI for your FastAPI pipeline: intake → assessment → report")

with st.form("intake_form"):
    col1, col2 = st.columns(2)
    with col1:
        company_name = st.text_input("Company Name", value="olindias")
        website = st.text_input("Website URL", value="https://www.olindias.com/")
    with col2:
        extra_urls_str = st.text_area("Extra URLs (one per line)", value="", height=100)

    run_btn = st.form_submit_button("Run Full Assessment")

# ----------------------------
# Run flow
# ----------------------------
if run_btn:
    logs = []
    def log(msg: str):
        logs.append(f"[{time.strftime('%H:%M:%S')}] {msg}")

    try:
        extra_urls = [u.strip() for u in extra_urls_str.splitlines() if u.strip()]
        log("Submitting intake...")

        intake = call_json(
            "POST",
            f"{cfg.base_url}/intake/company",
            cfg,
            payload={
                "company_name": company_name,
                "website": website,
                "extra_urls": extra_urls
            },
            timeout=60
        )
        company_id = intake["company"]["id"]
        log(f"Intake OK. company_id={company_id}")

        log("Starting assessment...")
        run = call_json("POST", f"{cfg.base_url}/report/run/{company_id}", cfg, payload=None, timeout=120)
        assessment_id = run.get("assessment_id") or run.get("id") or run.get("assessment", {}).get("id")
        if not assessment_id:
            raise RuntimeError(f"Could not find assessment_id in response: {run}")
        log(f"Assessment started. assessment_id={assessment_id}")

        # If you implemented background workers/status, polling is needed.
        # We'll poll for status if present; otherwise fetch once.
        details_url = f"{cfg.base_url}/assessment/{assessment_id}"

        log("Fetching assessment details...")
        # details = call_json("GET", details_url, cfg, payload=None, timeout=60)


        
        # NEW
        candidate_paths = [
            f"/assessment/{assessment_id}",
            f"/report/{assessment_id}",
            f"/report/details/{assessment_id}",
            f"/report/result/{assessment_id}",
            ]
        details = None
        last_err = None

        for p in candidate_paths:
            try:
                details = call_json("GET", f"{cfg.base_url}{p}", cfg, payload=None, timeout=60)
                log(f"Details endpoint found: {p}")
                break
            except Exception as e:
                last_err = e

        if details is None:
            raise RuntimeError(f"No details endpoint matched. Last error: {last_err}")



        # If status exists and not done, poll a bit
        if "status" in details:
            for _ in range(40):  # ~40 seconds max
                status = details.get("status")
                if status in ("done", "failed"):
                    break
                time.sleep(1)
                details = call_json("GET", details_url, cfg, payload=None, timeout=60)

        # ----------------------------
        # Render Dashboard
        # ----------------------------
        score = details.get("score", 0)
        confidence = details.get("confidence", 0)
        status = details.get("status", "done")
        signals = details.get("signals", []) or []

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Credibility Score", f"{score}/100")
        k2.metric("Confidence", f"{confidence}%")
        k3.metric("Signals", str(len(signals)))
        k4.metric("Status", str(status))

        left, right = st.columns([1.2, 1])

        # Signal cards
        with left:
            st.subheader("Signal Cards")

            if not signals:
                st.info("No signals available.")
            else:
                # show as grid
                ncols = 3
                rows = (len(signals) + ncols - 1) // ncols
                for r in range(rows):
                    cols = st.columns(ncols)
                    for c in range(ncols):
                        i = r * ncols + c
                        if i >= len(signals):
                            break
                        s = signals[i]
                        color = badge_color(s.get("numeric_value"), s.get("passed"))
                        label = badge_text(s.get("numeric_value"), s.get("passed"))

                        with cols[c]:
                            st.markdown(
                                f"""
                                <div style="
                                  border:1px solid rgba(0,0,0,0.08);
                                  border-radius:14px;
                                  padding:12px;
                                  background: #ffffff;
                                  ">
                                  <div style="
                                    display:inline-block;
                                    padding:3px 10px;
                                    border-radius:999px;
                                    background:{color};
                                    color:white;
                                    font-weight:700;
                                    font-size:12px;
                                    ">
                                    {label}
                                  </div>
                                  <div style="margin-top:8px;font-weight:800;">{s.get("key")}</div>
                                  <div style="color:#555;font-size:12px;margin-top:6px;">
                                    Normalized: <b>{percent(s.get("numeric_value"))}</b><br/>
                                    Weight: <b>{s.get("weight")}</b>
                                  </div>
                                  <div style="color:#666;font-size:12px;margin-top:8px;">
                                    {s.get("rationale") or ""}
                                  </div>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )

        # Radar chart
        with right:
            st.subheader("Radar Chart")

            if signals:
                labels = [s["key"] for s in signals]
                values = [(s.get("numeric_value") if s.get("numeric_value") is not None else 0.35) for s in signals]
                # Close the polygon
                labels_closed = labels + [labels[0]]
                values_closed = values + [values[0]]

                fig = go.Figure()
                fig.add_trace(go.Scatterpolar(
                    r=values_closed,
                    theta=labels_closed,
                    fill="toself",
                    name="Signal strength"
                ))
                fig.update_layout(
                    polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
                    showlegend=False,
                    margin=dict(l=20, r=20, t=20, b=20),
                    height=420
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No data for radar chart.")

            st.subheader("Reports")
            st.markdown(f"- Markdown: `{cfg.base_url}/report/markdown/{assessment_id}`")
            st.markdown(f"- PDF: `{cfg.base_url}/report/pdf/{assessment_id}`")
            c1, c2 = st.columns(2)
            with c1:
                st.link_button("Open Markdown Report", f"{cfg.base_url}/report/markdown/{assessment_id}")
            with c2:
                st.link_button("Download PDF Report", f"{cfg.base_url}/report/pdf/{assessment_id}")

        st.markdown("---")
        st.subheader("Raw JSON")
        st.json({"intake": intake, "run": run, "details": details})

        st.subheader("Logs")
        st.code("\n".join(logs), language="text")

    except Exception as e:
        st.error(str(e))
        st.subheader("Logs")
        st.code("\n".join(logs) if "logs" in locals() else "", language="text")