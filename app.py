import streamlit as st
import requests
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="Supplier Risk Intelligence",
    page_icon="⚠️",
    layout="wide"
)

st.title(" Supplier Risk Intelligence System")

COUNTRIES  = ['China','India','Vietnam','Bangladesh','Mexico',
              'Germany','USA','South Korea','Taiwan','Brazil']
INDUSTRIES = ['Electronics','Textiles','Automotive','Chemicals',
              'Food Processing','Pharmaceuticals','Steel','Plastics']
TIERS      = ['Tier 1','Tier 2','Tier 3']

#  Tabs 
tab1, tab2 = st.tabs(["🔍 Assess Supplier", "📊 Risk Scorecard"])

with tab1:
    col_form, col_result = st.columns([1, 1])

    with col_form:
        st.subheader("Supplier Signals")

        supplier_id   = st.number_input("Supplier ID", 0, 9999, 1)
        supplier_name = st.text_input("Supplier Name", "Acme Supplier Co.")
        country       = st.selectbox("Country", COUNTRIES)
        industry      = st.selectbox("Industry", INDUSTRIES)
        tier          = st.selectbox("Supplier Tier", TIERS)

        st.markdown("**📋 Company Profile**")
        revenue       = st.number_input("Annual Revenue ($M)", 0.1, 500.0, 25.0)
        years_active  = st.slider("Years Active", 1, 30, 8)
        n_certs       = st.slider("Number of Certifications", 0, 5, 2)
        concentration = st.slider("Customer Concentration Risk", 0.0, 1.0, 0.4, 0.05)

        st.markdown("**📰 News & Sentiment**")
        news_score    = st.slider("News Sentiment Score (0=positive, 1=negative)", 0.0, 1.0, 0.3, 0.05)
        news_volume   = st.slider("News Mentions (30d)", 0, 50, 5)
        reg_news      = st.checkbox("Regulatory/Compliance News", False)
        labour_unrest = st.checkbox("Labour Unrest Signal", False)

        st.markdown("**💰 Financial Signals**")
        dpo_trend     = st.slider("DPO Trend (days)", -10.0, 20.0, 2.0, 0.5)
        credit_change = st.selectbox("Credit Rating Change",
                                      [-2,-1,0,1,2],
                                      index=2,
                                      format_func=lambda x:
                                      {-2:"--",-1:"-",0:"Stable",1:"+",2:"++"}[x])
        pay_delay     = st.slider("Payment Delay (days)", 0.0, 45.0, 3.0, 0.5)
        rev_growth    = st.slider("Revenue Growth %", -30.0, 50.0, 5.0, 1.0)

        st.markdown("**🚢 Operations & Logistics**")
        otd_rate      = st.slider("On-Time Delivery Rate", 0.5, 1.0, 0.92, 0.01)
        lead_var      = st.slider("Lead Time Variance (days)", 0.0, 20.0, 3.0, 0.5)
        port_cong     = st.slider("Port Congestion Index (0-10)", 0.0, 10.0, 3.0, 0.5)
        ship_cost     = st.slider("Shipping Cost Change %", -30.0, 50.0, 5.0, 1.0)

        st.markdown("**🌦️ Climate & External**")
        climate_sev   = st.slider("Climate Event Severity (0-10)", 0.0, 10.0, 1.5, 0.5)
        nat_disaster  = st.checkbox("Natural Disaster Reported", False)

        assess_btn = st.button("Assess Supplier Risk",
                                type="primary", use_container_width=True)

    with col_result:
        if assess_btn:
            payload = {
                "supplier_id":          supplier_id,
                "supplier_name":        supplier_name,
                "country":              country,
                "industry":             industry,
                "supplier_tier":        tier,
                "annual_revenue_m":     revenue,
                "years_active":         years_active,
                "n_certifications":     n_certs,
                "concentration_risk":   concentration,
                "news_sentiment_score": news_score,
                "news_volume_30d":      news_volume,
                "regulatory_news":      int(reg_news),
                "labour_unrest_signal": int(labour_unrest),
                "dpo_trend":            dpo_trend,
                "credit_change":        credit_change,
                "payment_delay_days":   pay_delay,
                "revenue_growth":       rev_growth,
                "otd_rate":             otd_rate,
                "lead_time_variance":   lead_var,
                "port_congestion":      port_cong,
                "shipping_cost_change": ship_cost,
                "climate_severity":     climate_sev,
                "nat_disaster_flag":    int(nat_disaster),
            }

            with st.spinner("Assessing supplier risk..."):
                try:
                    resp   = requests.post(f"{API_URL}/assess", json=payload)
                    result = resp.json()
                except Exception as e:
                    st.error(f"API error: {e}")
                    st.stop()

            # Risk banner
            tier_colors = {
                "Critical": "#e74c3c",
                "High":     "#e67e22",
                "Medium":   "#f39c12",
                "Low":      "#27ae60"
            }
            rt    = result['risk_tier']
            color = tier_colors.get(rt, "gray")

            st.markdown(
                f"<div style='background:{color};padding:16px;"
                f"border-radius:10px;text-align:center;"
                f"color:white;font-size:22px;font-weight:600'>"
                f"RISK TIER: {rt} — "
                f"{result['disruption_probability']*100:.1f}% Disruption Probability"
                f"</div>", unsafe_allow_html=True
            )
            st.markdown("")

            c1, c2, c3 = st.columns(3)
            c1.metric("Disruption Probability",
                      f"{result['disruption_probability']*100:.1f}%")
            c2.metric("Monitoring Frequency", result['monitoring_frequency'])
            c3.metric("Risk Tier", rt)

            st.info(f"**Action:** {result['recommended_action']}")

            # Risk gauge
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=round(result['disruption_probability'] * 100, 1),
                number={"suffix": "%"},
                gauge={
                    "axis": {"range": [0, 100]},
                    "bar":  {"color": color},
                    "steps": [
                        {"range": [0,  30], "color": "#d5f5e3"},
                        {"range": [30, 50], "color": "#fef9e7"},
                        {"range": [50, 70], "color": "#fdebd0"},
                        {"range": [70,100], "color": "#fadbd8"},
                    ],
                    "threshold": {"line": {"color":"black","width":3},
                                  "value": 40}
                }
            ))
            fig.update_layout(height=250, margin=dict(t=20,b=10))
            st.plotly_chart(fig, use_container_width=True)

            col_d, col_p = st.columns(2)
            with col_d:
                st.markdown("**🔴 Top Risk Drivers**")
                for d in result['top_risk_drivers']:
                    st.markdown(f"- `{d['factor']}` +{d['impact']:.4f}")
            with col_p:
                st.markdown("**🟢 Protective Factors**")
                for p in result['top_protective_factors']:
                    st.markdown(f"- `{p['factor']}` -{p['protection']:.4f}")
        else:
            st.info("Fill in supplier signals and click **Assess Supplier Risk**.")

with tab2:
    st.subheader("Live Supplier Risk Scorecard")
    try:
        sc_resp = requests.get(f"{API_URL}/scorecard")
        sc_data = sc_resp.json()
        sc_df   = pd.DataFrame(sc_data)

        # Summary metrics
        tier_counts = sc_df['risk_tier'].value_counts()
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("🔴 Critical", tier_counts.get('Critical', 0))
        c2.metric("🟠 High",     tier_counts.get('High', 0))
        c3.metric("🟡 Medium",   tier_counts.get('Medium', 0))
        c4.metric("🟢 Low",      tier_counts.get('Low', 0))

        # Chart
        fig = px.bar(
            sc_df.head(30).sort_values('disruption_prob', ascending=True),
            x='disruption_prob', y='supplier_id',
            color='risk_tier',
            orientation='h',
            color_discrete_map={
                'Critical':'#e74c3c','High':'#e67e22',
                'Medium':'#f1c40f','Low':'#27ae60'
            },
            title="Top 30 Suppliers by Disruption Probability"
        )
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)

        # Table
        st.dataframe(
            sc_df[['supplier_id','country','industry','supplier_tier',
                   'disruption_prob','risk_tier']].head(30),
            use_container_width=True
        )

    except Exception as e:
        st.error(f"Could not load scorecard: {e}")