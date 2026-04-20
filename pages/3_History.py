import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.markdown("# Health Assessment History")

if "history" not in st.session_state or st.session_state.history.empty:
    st.info("ℹ️ No assessment history available yet. Complete a health assessment to start tracking your progress.")
    st.markdown("""
    <div class="card">
    <h4>How to get started:</h4>
    <ol>
        <li>Navigate to the <strong>Health Assessment</strong> page</li>
        <li>Fill in your health information</li>
        <li>Generate your personalized report</li>
        <li>Return here to view trends over time</li>
    </ol>
    </div>
    """, unsafe_allow_html=True)
else:
    history_df = st.session_state.history.copy()
    history_df['date'] = pd.to_datetime(history_df['date'])
    history_df = history_df.sort_values('date')

    st.success(f"📊 Found {len(history_df)} assessment(s) in your history.")

    # Summary Statistics
    st.markdown("## Summary Statistics")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Assessments", len(history_df))
    with col2:
        avg_overall = history_df['overall_risk'].mean()
        st.metric("Average Overall Risk", f"{avg_overall:.1%}")
    with col3:
        latest = history_df.iloc[-1]['overall_risk']
        st.metric("Latest Overall Risk", f"{latest:.1%}")
    with col4:
        improvement = (history_df.iloc[0]['overall_risk'] - latest) / history_df.iloc[0]['overall_risk'] * 100 if len(history_df) > 1 else 0
        st.metric("Risk Change", f"{improvement:+.1f}%")

    # Risk Trends Over Time
    st.markdown("## Risk Trends Over Time")
    fig = go.Figure()

    diseases = ['diabetes_risk', 'hypertension_risk', 'heart_disease_risk', 'obesity_risk', 'stress_risk']
    disease_names = ['Diabetes', 'Hypertension', 'Heart Disease', 'Obesity', 'Stress']

    for disease, name in zip(diseases, disease_names):
        fig.add_trace(go.Scatter(
            x=history_df['date'],
            y=history_df[disease] * 100,
            mode='lines+markers',
            name=name,
            line=dict(width=3)
        ))

    fig.add_trace(go.Scatter(
        x=history_df['date'],
        y=history_df['overall_risk'] * 100,
        mode='lines+markers',
        name='Overall Risk',
        line=dict(width=4, dash='dash')
    ))

    fig.update_layout(
        title="Health Risk Trends",
        xaxis_title="Date",
        yaxis_title="Risk Percentage (%)",
        hovermode="x unified"
    )
    st.plotly_chart(fig, width='stretch')

    # Detailed History Table
    st.markdown("## Detailed Assessment History")
    display_df = history_df.copy()
    display_df['date'] = display_df['date'].dt.strftime('%Y-%m-%d %H:%M')
    display_df[['diabetes_risk', 'hypertension_risk', 'heart_disease_risk', 'obesity_risk', 'stress_risk', 'overall_risk']] = \
        display_df[['diabetes_risk', 'hypertension_risk', 'heart_disease_risk', 'obesity_risk', 'stress_risk', 'overall_risk']].round(3)
    display_df = display_df.rename(columns={
        'diabetes_risk': 'Diabetes Risk',
        'hypertension_risk': 'Hypertension Risk',
        'heart_disease_risk': 'Heart Disease Risk',
        'obesity_risk': 'Obesity Risk',
        'stress_risk': 'Stress Risk',
        'overall_risk': 'Overall Risk'
    })
    st.dataframe(display_df, width='stretch')

    # Export Option
    csv = history_df.to_csv(index=False)
    st.download_button(
        label="📥 Download History as CSV",
        data=csv,
        file_name="health_assessment_history.csv",
        mime="text/csv"
    )

    # Recommendations based on trends
    st.markdown("## Insights from Your History")
    if len(history_df) > 1:
        latest_risks = history_df.iloc[-1][diseases]
        prev_risks = history_df.iloc[-2][diseases]

        improving = []
        worsening = []

        for disease, name, latest, prev in zip(diseases, disease_names, latest_risks, prev_risks):
            change = latest - prev
            if change < -0.05:  # Improved by more than 5%
                improving.append(name)
            elif change > 0.05:  # Worsened by more than 5%
                worsening.append(name)

        if improving:
            st.success(f"🎉 Great progress! Your risk has decreased for: {', '.join(improving)}")
        if worsening:
            st.warning(f"⚠️ Attention needed: Your risk has increased for: {', '.join(worsening)}")

        if not improving and not worsening:
            st.info("📊 Your health risks are relatively stable. Keep up the good work!")
    else:
        st.info("Complete more assessments to see trend insights.")
