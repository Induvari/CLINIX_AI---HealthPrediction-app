import streamlit as st

st.markdown(
    """
    <h1 style='text-align: center;'>🏥 CLINIXA AI</h1>
    <h3 style='text-align: center; color: #D9DDDC;'>
    AI-Powered Health Risk Prediction & Personalized Clinical Insights
    </h3>
    """,
    unsafe_allow_html=True
)

st.markdown("""
<div class="info-box">
<h3 style='text-align: center; color: #29465B;'>Welcome to Your Personal Health Companion!</h3>
<h4>AI-Powered Health Risk Prediction & Personalized Clinical Insights</h4>
<p>This advanced AI-powered system analyzes your health data to predict risks for major conditions including DIABETES, HYPERTENSION, HEART DISEASE, OBESITY, and STRESS DISORDERS. </br> Designed for clinical decision support and personal health education.</p>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class="card feature-card">
    <h3>🔍 What We Analyze</h3>
    <ul>
        <li><strong>Vital Signs:</strong> Blood pressure, heart rate, glucose levels</li>
        <li><strong>Body Metrics:</strong> BMI, weight, height</li>
        <li><strong>Lifestyle Factors:</strong> Sleep, exercise, diet, stress</li>
        <li><strong>Blood Profile:</strong> Cholesterol levels, triglycerides</li>
        <li><strong>Personal History:</strong> Age, gender</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="card feature-card">
    <h3>🎯 Key Features</h3>
    <ul>
        <li><strong>Comprehensive Assessment:</strong> Multi-disease risk prediction</li>
        <li><strong>Personalized Insights:</strong> Tailored recommendations</li>
        <li><strong>Progress Tracking:</strong> Monitor health trends over time</li>
        <li><strong>Professional Reports:</strong> Download detailed PDF reports</li>
        <li><strong>User-Friendly Interface:</strong> Intuitive and accessible design</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)

st.markdown("""
<div class="card disclaimer-card">
<h3>⚠️ Important Disclaimer</h3>
<p>This tool is for educational and informational purposes only. It is not a substitute for professional medical advice, diagnosis, or treatment. Always consult with qualified healthcare providers for medical concerns and before making health-related decisions.</p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")
st.markdown("### Get Started")
st.markdown("Navigate to the **Health Assessment** page to input your data and receive personalized health insights.")