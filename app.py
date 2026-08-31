import streamlit as st
import json
import plotly.graph_objects as go
import pandas as pd
from groq import Groq

st.set_page_config(page_title="Supplier Risk Intelligence", page_icon="⚠️", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
*, body { font-family: 'Inter', sans-serif; }
.stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"], .block-container
    { background: #f8fafc !important; }
section[data-testid="stSidebar"], section[data-testid="stSidebar"] > div
    { background: #ffffff !important; border-right: 1px solid #e2e8f0 !important; }
#MainMenu, footer, header { visibility: hidden; }
p, div, span, label { color: #1e293b !important; }
h1,h2,h3 { color: #0f172a !important; }

.stTextInput input { background:#fff !important; color:#0f172a !important; border:1.5px solid #cbd5e1 !important; border-radius:8px !important; }
.stNumberInput input { background:#fff !important; color:#0f172a !important; border:1.5px solid #cbd5e1 !important; border-radius:8px !important; }
.stSelectbox > div > div { background:#fff !important; border:1.5px solid #cbd5e1 !important; border-radius:8px !important; color:#0f172a !important; }
.stSlider label, .stCheckbox span, .stSelectbox label, .stTextInput label, .stNumberInput label { color:#374151 !important; font-weight:500 !important; font-size:0.82rem !important; }
.stButton > button { background:#dc2626 !important; color:#fff !important; border:none !important; border-radius:8px !important; font-weight:600 !important; padding:11px !important; }
.stButton > button:hover { background:#b91c1c !important; }
.stTabs [data-baseweb="tab-list"] { background:#f1f5f9 !important; border-radius:10px !important; padding:3px !important; }
.stTabs [data-baseweb="tab"] { background:transparent !important; color:#64748b !important; border-radius:7px !important; font-size:0.875rem !important; font-weight:500 !important; }
.stTabs [aria-selected="true"] { background:#ffffff !important; color:#0f172a !important; }
hr { border-color:#e2e8f0 !important; }

.card { background:#fff; border:1px solid #e2e8f0; border-radius:12px; padding:18px 22px; margin-bottom:12px; box-shadow:0 1px 3px rgba(0,0,0,.04); }
.metric-lbl { font-size:0.68rem; font-weight:700; text-transform:uppercase; letter-spacing:.09em; color:#64748b; margin-bottom:5px; }
.metric-val { font-size:1.7rem; font-weight:700; }
.banner { border-radius:10px; padding:16px 22px; text-align:center; font-size:1.1rem; font-weight:700; margin-bottom:16px; }
.row { border-radius:7px; padding:10px 14px; margin-bottom:7px; font-size:0.84rem; line-height:1.55; }
.row-red    { background:#fff1f2; border-left:3px solid #dc2626; color:#7f1d1d; }
.row-green  { background:#f0fdf4; border-left:3px solid #16a34a; color:#14532d; }
.row-blue   { background:#eff6ff; border-left:3px solid #2563eb; color:#1e3a5f; }
.section-lbl { font-size:0.68rem; font-weight:700; text-transform:uppercase; letter-spacing:.1em; color:#94a3b8; margin:16px 0 8px; }
</style>
""", unsafe_allow_html=True)

COUNTRIES  = ['China','India','Vietnam','Bangladesh','Mexico','Germany','USA','South Korea','Taiwan','Brazil']
INDUSTRIES = ['Electronics','Textiles','Automotive','Chemicals','Food Processing','Pharmaceuticals','Steel','Plastics']
TIERS      = ['Tier 1','Tier 2','Tier 3']

def get_client():
    try: return Groq(api_key=st.secrets["GROQ_API_KEY"])
    except: st.error("Add GROQ_API_KEY to Streamlit Secrets."); st.stop()

def parse_json(raw: str) -> dict:
    raw = raw.strip()
    if "```" in raw:
        parts = raw.split("```")
        for part in parts:
            part = part.lstrip("json").strip()
            if part.startswith("{"): raw = part; break
    s, e = raw.find("{"), raw.rfind("}")
    if s != -1 and e != -1: raw = raw[s:e+1]
    return json.loads(raw)

def assess(p: dict) -> dict:
    client = get_client()
    system = ("You are an expert supply chain risk analyst. "
              "Always respond with ONLY a valid raw JSON object, no markdown, no explanation.")
    user = f"""Analyze this supplier and return ONLY JSON:

Supplier: {p['supplier_name']} | Country: {p['country']} | Industry: {p['industry']} | Tier: {p['supplier_tier']}
Revenue: ${p['annual_revenue_m']}M | Years Active: {p['years_active']} | Certifications: {p['n_certifications']}
Customer Concentration Risk: {p['concentration_risk']} | Revenue Growth: {p['revenue_growth']}%
News Sentiment: {p['news_sentiment_score']} (0=positive,1=negative) | News Volume 30d: {p['news_volume_30d']}
Regulatory News: {p['regulatory_news']} | Labour Unrest: {p['labour_unrest_signal']}
DPO Trend: {p['dpo_trend']}d | Credit Change: {p['credit_change']} | Payment Delay: {p['payment_delay_days']}d
OTD Rate: {p['otd_rate']} | Lead Time Variance: {p['lead_time_variance']}d | Port Congestion: {p['port_congestion']}
Shipping Cost Change: {p['shipping_cost_change']}% | Climate Severity: {p['climate_severity']} | Natural Disaster: {p['nat_disaster_flag']}

Return exactly:
{{
  "disruption_probability": <float 0.0-1.0>,
  "risk_tier": "Low" | "Medium" | "High" | "Critical",
  "risk_score": <integer 0-100>,
  "monitoring_frequency": "Daily" | "Weekly" | "Monthly",
  "recommended_action": "specific 2-sentence action for procurement team",
  "top_risk_drivers": [
    {{"factor": "factor name", "impact": <float 0.01-0.30>}},
    {{"factor": "factor name", "impact": <float 0.01-0.30>}},
    {{"factor": "factor name", "impact": <float 0.01-0.30>}}
  ],
  "top_protective_factors": [
    {{"factor": "factor name", "protection": <float 0.01-0.20>}},
    {{"factor": "factor name", "protection": <float 0.01-0.20>}}
  ],
  "financial_risk": <integer 0-100>,
  "operational_risk": <integer 0-100>,
  "geopolitical_risk": <integer 0-100>,
  "climate_risk": <integer 0-100>,
  "summary": "2-3 sentence risk summary"
}}

Tier: Critical>=0.70, High>=0.50, Medium>=0.30, Low<0.30. Monitoring: Critical=Daily, High=Weekly, else Monthly."""

    raw = client.chat.completions.create(
        model="qwen/qwen3.6-27b",
        messages=[{"role":"system","content":system},{"role":"user","content":user}],
        temperature=0.1, max_tokens=1200
    ).choices[0].message.content
    return parse_json(raw)

def score_color(s):
    return "#16a34a" if s<=30 else "#d97706" if s<=60 else "#dc2626"

def metric_card(label, value, color="#0f172a"):
    st.markdown(f'<div class="card"><div class="metric-lbl">{label}</div>'
                f'<div class="metric-val" style="color:{color};">{value}</div></div>',
                unsafe_allow_html=True)


# ── header ──
st.markdown("## Supplier Risk Intelligence System")
st.caption("AI-powered supply chain disruption analysis · Powered by Groq")
st.divider()

tab1, tab2 = st.tabs(["🔍 Assess Supplier", "📊 Risk Scorecard"])

# ─────────────────────────────────
# TAB 1 — ASSESS
# ─────────────────────────────────
with tab1:
    col_form, col_result = st.columns([1, 1], gap="large")

    with col_form:
        st.markdown("**Supplier Profile**")

        supplier_name = st.text_input("Supplier Name", "Acme Supplier Co.", key="sname")
        supplier_id   = st.number_input("Supplier ID", 0, 9999, 1, key="sid")
        c1, c2 = st.columns(2)
        with c1: country  = st.selectbox("Country",  COUNTRIES,  key="country")
        with c2: industry = st.selectbox("Industry", INDUSTRIES, key="industry")
        tier = st.selectbox("Supplier Tier", TIERS, key="tier")

        st.markdown('<div class="section-lbl">Company Profile</div>', unsafe_allow_html=True)
        revenue      = st.number_input("Annual Revenue ($M)", 0.1, 500.0, 25.0, key="rev")
        c1, c2 = st.columns(2)
        with c1: years_active = st.slider("Years Active",           1, 30,  8,    key="years")
        with c2: n_certs      = st.slider("Certifications",         0,  5,  2,    key="certs")
        concentration = st.slider("Customer Concentration Risk", 0.0, 1.0, 0.4, 0.05, key="conc")

        st.markdown('<div class="section-lbl">News & Sentiment</div>', unsafe_allow_html=True)
        news_score   = st.slider("News Sentiment (0=positive, 1=negative)", 0.0, 1.0, 0.3, 0.05, key="news_score")
        news_volume  = st.slider("News Mentions (30d)", 0, 50, 5, key="news_vol")
        c1, c2 = st.columns(2)
        with c1: reg_news     = st.checkbox("Regulatory News",  False, key="reg")
        with c2: labour_unrest= st.checkbox("Labour Unrest",    False, key="labour")

        st.markdown('<div class="section-lbl">Financial Signals</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1: dpo_trend    = st.slider("DPO Trend (days)",       -10.0, 20.0,  2.0, 0.5,  key="dpo")
        with c2: pay_delay    = st.slider("Payment Delay (days)",     0.0, 45.0,  3.0, 0.5,  key="payd")
        credit_change = st.selectbox("Credit Rating Change", [-2,-1,0,1,2], index=2,
                                     format_func=lambda x:{-2:"--",-1:"-",0:"Stable",1:"+",2:"++"}[x], key="credit")
        rev_growth    = st.slider("Revenue Growth %", -30.0, 50.0, 5.0, 1.0, key="revg")

        st.markdown('<div class="section-lbl">Operations & Logistics</div>', unsafe_allow_html=True)
        otd_rate  = st.slider("On-Time Delivery Rate", 0.5, 1.0, 0.92, 0.01, key="otd")
        c1, c2 = st.columns(2)
        with c1: lead_var  = st.slider("Lead Time Variance (days)", 0.0, 20.0, 3.0, 0.5, key="lead")
        with c2: port_cong = st.slider("Port Congestion (0-10)",    0.0, 10.0, 3.0, 0.5, key="port")
        ship_cost = st.slider("Shipping Cost Change %", -30.0, 50.0, 5.0, 1.0, key="ship")

        st.markdown('<div class="section-lbl">Climate & External</div>', unsafe_allow_html=True)
        climate_sev  = st.slider("Climate Event Severity (0-10)", 0.0, 10.0, 1.5, 0.5, key="climate")
        nat_disaster = st.checkbox("Natural Disaster Reported", False, key="nat")

        st.markdown("<br>", unsafe_allow_html=True)
        assess_btn = st.button(" Assess Supplier Risk", use_container_width=True, key="assess")

    with col_result:
        if assess_btn:
            payload = {
                "supplier_id": supplier_id, "supplier_name": supplier_name,
                "country": country, "industry": industry, "supplier_tier": tier,
                "annual_revenue_m": revenue, "years_active": years_active,
                "n_certifications": n_certs, "concentration_risk": concentration,
                "news_sentiment_score": news_score, "news_volume_30d": news_volume,
                "regulatory_news": int(reg_news), "labour_unrest_signal": int(labour_unrest),
                "dpo_trend": dpo_trend, "credit_change": credit_change,
                "payment_delay_days": pay_delay, "revenue_growth": rev_growth,
                "otd_rate": otd_rate, "lead_time_variance": lead_var,
                "port_congestion": port_cong, "shipping_cost_change": ship_cost,
                "climate_severity": climate_sev, "nat_disaster_flag": int(nat_disaster),
            }

            with st.spinner("Analyzing supplier risk…"):
                try:
                    r = assess(payload)
                except json.JSONDecodeError:
                    st.error("Could not parse AI response. Try again."); st.stop()
                except Exception as e:
                    st.error(f"Error: {e}"); st.stop()

            rt    = r.get("risk_tier","Unknown")
            prob  = r.get("disruption_probability", 0)
            bcolors = {"Critical":("#fff1f2","#dc2626","#fecaca"),
                       "High":    ("#fff7ed","#ea580c","#fed7aa"),
                       "Medium":  ("#fefce8","#ca8a04","#fde68a"),
                       "Low":     ("#f0fdf4","#16a34a","#bbf7d0")}
            bg, tc, bc = bcolors.get(rt, ("#f8fafc","#64748b","#e2e8f0"))

            st.markdown(f"""
            <div style="background:{bg};border:1px solid {bc};border-left:4px solid {tc};
                 border-radius:10px;padding:16px 22px;margin-bottom:16px;text-align:center;">
                <div style="font-size:1.2rem;font-weight:700;color:{tc};">⚠ RISK TIER: {rt}</div>
                <div style="font-size:0.85rem;color:{tc};margin-top:4px;opacity:.8;">
                    {prob*100:.1f}% Disruption Probability</div>
            </div>
            """, unsafe_allow_html=True)

            # KPI cards
            m1, m2, m3 = st.columns(3)
            with m1: metric_card("Disruption Prob", f"{prob*100:.1f}%", tc)
            with m2: metric_card("Risk Score",      f"{r.get('risk_score',0)}", score_color(r.get('risk_score',0)))
            with m3: metric_card("Monitoring",      r.get("monitoring_frequency","—"))

            # recommendation
            st.markdown(f"""
            <div style="background:#eff6ff;border:1px solid #bfdbfe;border-left:4px solid #2563eb;
                 border-radius:10px;padding:14px 18px;font-size:0.875rem;color:#1e3a5f;line-height:1.65;margin-bottom:16px;">
            📋 {r.get("recommended_action","")}</div>
            """, unsafe_allow_html=True)

            # gauge
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=round(prob * 100, 1),
                number={"suffix":"%","font":{"size":32,"color":"#0f172a"}},
                gauge={
                    "axis": {"range":[0,100],"tickcolor":"#94a3b8"},
                    "bar":  {"color":tc,"thickness":0.25},
                    "bgcolor": "#f8fafc",
                    "steps": [
                        {"range":[0,30],  "color":"#f0fdf4"},
                        {"range":[30,50], "color":"#fefce8"},
                        {"range":[50,70], "color":"#fff7ed"},
                        {"range":[70,100],"color":"#fff1f2"},
                    ],
                    "threshold":{"line":{"color":"#0f172a","width":3},"value":prob*100}
                }
            ))
            fig.update_layout(height=240, margin=dict(t=20,b=10,l=20,r=20),
                              paper_bgcolor="#ffffff", plot_bgcolor="#ffffff")
            st.plotly_chart(fig, use_container_width=True)

            # sub-scores
            st.markdown("**Risk Breakdown**")
            sub_scores = [
                ("Financial Risk",    r.get("financial_risk",0)),
                ("Operational Risk",  r.get("operational_risk",0)),
                ("Geopolitical Risk", r.get("geopolitical_risk",0)),
                ("Climate Risk",      r.get("climate_risk",0)),
            ]
            for lbl, val in sub_scores:
                c = score_color(val)
                st.markdown(f"""
                <div style="margin-bottom:10px;">
                    <div style="display:flex;justify-content:space-between;font-size:0.78rem;margin-bottom:4px;">
                        <span style="font-weight:600;color:#374151;">{lbl}</span>
                        <span style="font-weight:700;color:{c};">{val}/100</span>
                    </div>
                    <div style="background:#e2e8f0;border-radius:4px;height:6px;">
                        <div style="width:{val}%;background:{c};border-radius:4px;height:6px;"></div>
                    </div>
                </div>""", unsafe_allow_html=True)

            # drivers + protectors
            d1, d2 = st.columns(2)
            with d1:
                st.markdown("**🔴 Top Risk Drivers**")
                for d in r.get("top_risk_drivers",[]):
                    st.markdown(f'<div class="row row-red"><b>{d["factor"]}</b><br>'
                                f'<span style="font-size:.75rem;">Impact: +{d["impact"]:.3f}</span></div>',
                                unsafe_allow_html=True)
            with d2:
                st.markdown("**🟢 Protective Factors**")
                for p in r.get("top_protective_factors",[]):
                    st.markdown(f'<div class="row row-green"><b>{p["factor"]}</b><br>'
                                f'<span style="font-size:.75rem;">Protection: -{p["protection"]:.3f}</span></div>',
                                unsafe_allow_html=True)

            # summary
            st.markdown(f"""
            <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;
                 padding:14px 18px;font-size:0.85rem;color:#475569;line-height:1.7;margin-top:8px;">
            {r.get("summary","")}</div>
            """, unsafe_allow_html=True)

        else:
            st.markdown("""
            <div style="text-align:center;padding:80px 32px;border:1px dashed #e2e8f0;border-radius:12px;">
                <div style="font-size:2.5rem;margin-bottom:12px;">⚠️</div>
                <div style="font-size:1rem;font-weight:600;color:#475569;">No assessment yet</div>
                <div style="font-size:0.85rem;color:#94a3b8;margin-top:6px;">
                    Fill in supplier signals and click Assess Supplier Risk</div>
            </div>
            """, unsafe_allow_html=True)

# ─────────────────────────────────
# TAB 2 — SCORECARD
# ─────────────────────────────────
with tab2:
    st.markdown("**Sample Supplier Risk Scorecard**")
    st.caption("Showing demo data — connect your supplier database to populate live scores.")

    demo = pd.DataFrame([
        {"Supplier":"Alpha Tech","Country":"China","Industry":"Electronics","Tier":"Tier 1","Disruption %":72,"Risk Tier":"Critical"},
        {"Supplier":"BetaFab","Country":"Vietnam","Industry":"Textiles","Tier":"Tier 2","Disruption %":58,"Risk Tier":"High"},
        {"Supplier":"GammaChem","Country":"India","Industry":"Chemicals","Tier":"Tier 1","Disruption %":44,"Risk Tier":"Medium"},
        {"Supplier":"Delta Auto","Country":"Germany","Industry":"Automotive","Tier":"Tier 1","Disruption %":21,"Risk Tier":"Low"},
        {"Supplier":"Epsilon Steel","Country":"Brazil","Industry":"Steel","Tier":"Tier 2","Disruption %":63,"Risk Tier":"High"},
        {"Supplier":"ZetaPharma","Country":"USA","Industry":"Pharmaceuticals","Tier":"Tier 1","Disruption %":18,"Risk Tier":"Low"},
        {"Supplier":"EtaPlastics","Country":"Mexico","Industry":"Plastics","Tier":"Tier 3","Disruption %":35,"Risk Tier":"Medium"},
        {"Supplier":"ThetaFood","Country":"Bangladesh","Industry":"Food Processing","Tier":"Tier 2","Disruption %":81,"Risk Tier":"Critical"},
    ])

    tc = demo["Risk Tier"].value_counts()
    m1,m2,m3,m4 = st.columns(4)
    with m1: st.markdown(f'<div class="card"><div class="metric-lbl">🔴 Critical</div><div class="metric-val" style="color:#dc2626;">{tc.get("Critical",0)}</div></div>', unsafe_allow_html=True)
    with m2: st.markdown(f'<div class="card"><div class="metric-lbl">🟠 High</div><div class="metric-val" style="color:#ea580c;">{tc.get("High",0)}</div></div>', unsafe_allow_html=True)
    with m3: st.markdown(f'<div class="card"><div class="metric-lbl">🟡 Medium</div><div class="metric-val" style="color:#ca8a04;">{tc.get("Medium",0)}</div></div>', unsafe_allow_html=True)
    with m4: st.markdown(f'<div class="card"><div class="metric-lbl">🟢 Low</div><div class="metric-val" style="color:#16a34a;">{tc.get("Low",0)}</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    color_map = {"Critical":"#dc2626","High":"#ea580c","Medium":"#ca8a04","Low":"#16a34a"}
    fig = go.Figure()
    for tier, color in color_map.items():
        sub = demo[demo["Risk Tier"]==tier]
        if not sub.empty:
            fig.add_trace(go.Bar(
                x=sub["Disruption %"], y=sub["Supplier"],
                orientation="h", name=tier,
                marker_color=color,
                marker_line_width=0,
            ))
    fig.update_layout(
        barmode="stack", height=320,
        paper_bgcolor="#ffffff", plot_bgcolor="#f8fafc",
        margin=dict(t=20,b=20,l=10,r=20),
        font=dict(family="Inter", color="#374151", size=12),
        legend=dict(orientation="h", y=1.08),
        xaxis=dict(title="Disruption Probability %", gridcolor="#e2e8f0"),
        yaxis=dict(gridcolor="#e2e8f0"),
    )
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(demo, use_container_width=True, hide_index=True)
