import streamlit as st
import pandas as pd
import numpy as np
import joblib
import plotly.express as px
import plotly.graph_objects as go
import io
import datetime

import app_helpers
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

st.markdown("# Health Risk Assessment")

# ---------------- LOAD MODEL ----------------
@st.cache_resource
def load():
    model = joblib.load("model.pkl")
    scaler = joblib.load("scaler.pkl")
    columns = joblib.load("columns.pkl")
    return model, scaler, columns

model, scaler, columns = load()

# ---------------- INDICATOR FUNCTION ----------------
def indicator(value, low, high):
    if value < low:
        return "Low"
    elif value > high:
        return "High"
    return "Normal"

def color_map(status):
    if status == "Normal":
        return "green"
    elif status == "Low":
        return "orange"
    return "red"

# ---------------- FEATURE ENGINEERING ----------------
def feature_engineering(df):
    df = df.copy()

    df["bmi"] = df["weight"] / (df["height"] ** 2)

    df["metabolic_risk"] = (
        df["bmi"] * 0.3 +
        df["glucose"] * 0.3 +
        df["ldl"] * 0.2 +
        df["triglycerides"] * 0.2
    )

    df["ldl_hdl_ratio"] = df["ldl"] / (df["hdl"] + 1e-5)

    df["pulse_pressure"] = df["systolic_bp"] - df["diastolic_bp"]

    df["map"] = (df["systolic_bp"] + 2 * df["diastolic_bp"]) / 3

    df["glucose_insulin_ratio"] = df["glucose"] / (df["insulin"] + 1e-5)

    df["bmi_age_risk"] = df["bmi"] * df["age"]

    df["bp_stress_index"] = df["stress_level"] * df["systolic_bp"]

    return df

def age_group(age):
    if age < 30:
        return "young"
    elif age < 50:
        return "adult"
    elif age < 65:
        return "middle_aged"
    else:
        return "senior"

def preprocess(data):
    df = pd.DataFrame([data])

    # feature engineering FIRST
    df = feature_engineering(df)

    # categorical features used in training
    if "age_group" in df.columns:
        df["age_group"] = df["age"].apply(age_group)

    # one-hot encoding
    df = pd.get_dummies(df)

    # ALIGN EXACTLY with training columns (CRITICAL FIX)
    df = df.reindex(columns=columns, fill_value=0)

    # scale AFTER alignment
    return scaler.transform(df)

def predict(user):
    X = preprocess(user)

    probs = model.predict_proba(X)

    # MultiOutputClassifier returns list of arrays
    probs = [p[0][1] for p in probs]

    diseases = ["Diabetes", "Hypertension", "Heart Disease", "Obesity", "Stress"]

    return diseases, np.clip(probs, 0.01, 0.99)

# ---------------- RISK CLASSIFICATION ----------------
def classify_risk(prob):
    if prob < 0.4:
        return "Low Risk"
    elif prob < 0.7:
        return "Moderate Risk"
    return "High Risk"

def risk_color(level):
    if level == "High Risk":
        return "#e74c3c"
    elif level == "Moderate Risk":
        return "#f39c12"
    return "#27ae60"

# ---------------- INSIGHTS ENGINE ----------------
def generate_insights(user, diseases, results):
    insights = []

    for d, r in zip(diseases, results):
        level = classify_risk(r)
        reasons = []
        recommendations = []

        # --- REASONS ---
        if user["glucose"] > 140:
            reasons.append("Elevated glucose levels")
        if user["systolic_bp"] > 140 or user["diastolic_bp"] > 90:
            reasons.append("High blood pressure")
        if user["ldl"] > 130:
            reasons.append("High LDL cholesterol")
        bmi = user["weight"] / (user["height"] ** 2)
        if bmi > 30:
            reasons.append("High BMI (Obesity)")
        if user["stress_level"] > 7:
            reasons.append("High stress levels")
        if user["sleep_hours"] < 6:
            reasons.append("Insufficient sleep")
        if user["daily_steps"] < 4000:
            reasons.append("Low physical activity")

        # --- RECOMMENDATIONS ---
        if classify_risk(r) == "High Risk":
            recommendations.append("Consult a healthcare professional immediately")
            recommendations.append("Schedule comprehensive medical check-up")
        if user["daily_steps"] < 4000:
            recommendations.append("Aim for 7,000-10,000 steps daily")
        if user["sleep_hours"] < 6:
            recommendations.append("Maintain 7-9 hours of sleep per night")
        if bmi > 25:
            recommendations.append("Focus on weight management through diet and exercise")
        if user["stress_level"] > 5:
            recommendations.append("Practice stress-reduction techniques (meditation, exercise)")
        recommendations.append("Maintain regular health check-ups")

        insights.append({
            "disease": d,
            "risk": level,
            "probability": int(r * 100),
            "reasons": reasons if reasons else ["All indicators within normal ranges"],
            "recommendations": recommendations
        })

    return insights

def generate_pdf(user, insights, results, diseases):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=(8.5*72, 11*72), topMargin=0.5*inch, bottomMargin=0.5*inch)
    styles = getSampleStyleSheet()
    story = []

    # Custom Styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=28,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#34495e'),
        spaceAfter=18,
        spaceBefore=12,
        fontName='Helvetica-Bold',
        borderColor=colors.HexColor('#3498db'),
        borderWidth=2,
        borderPadding=12,
        borderRadius=0
    )

    # Title
    story.append(Paragraph("🏥 Clinixa AI - Health Risk Assessment Report", title_style))
    story.append(Spacer(1, 6))
    story.append(Paragraph(f"<font size=10 color='#7f8c8d'>Generated on {datetime.datetime.now().strftime('%B %d, %Y at %H:%M')}</font>", styles["Normal"]))
    story.append(Spacer(1, 18))

    # Patient Information Section
    story.append(Paragraph("Patient Information", heading_style))
    
    user_display = [
        ("Age", str(user["age"])),
        ("Gender", user["gender"]),
        ("Weight (kg)", str(user["weight"])),
        ("Height (m)", str(user["height"])),
        ("Systolic BP (mmHg)", str(user["systolic_bp"])),
        ("Diastolic BP (mmHg)", str(user["diastolic_bp"])),
        ("Glucose (mg/dL)", str(user["glucose"])),
        ("Heart Rate (bpm)", str(user["heart_rate"])),
        ("Smoking", user["smoking"]),
        ("Alcohol", user["alcohol"]),
        ("Sleep Hours", str(user["sleep_hours"])),
        ("Daily Steps", str(user["daily_steps"])),
        ("Exercise Hours", str(user["training_hours"])),
        ("LDL Cholesterol", str(user["ldl"])),
        ("HDL Cholesterol", str(user["hdl"])),
        ("Triglycerides", str(user["triglycerides"])),
        ("Stress Level", str(user["stress_level"])),
        ("Diet Type", user["diet_type"])
    ]
    
    table_data = []
    for i in range(0, len(user_display), 2):
        row = []
        cell1_text = Paragraph(f"<b>{user_display[i][0]}:</b> {user_display[i][1]}", styles["Normal"])
        row.append(cell1_text)
        if i+1 < len(user_display):
            cell2_text = Paragraph(f"<b>{user_display[i+1][0]}:</b> {user_display[i+1][1]}", styles["Normal"])
            row.append(cell2_text)
        table_data.append(row)
    
    patient_table = Table(table_data, colWidths=[3.5*inch, 3.5*inch])
    patient_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#ecf0f1')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2c3e50')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('PADDING', (0, 0), (-1, -1), 12),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LINEABOVE', (0, 0), (-1, -1), 1.5, colors.HexColor('#95a5a6')),
        ('LINEBELOW', (0, 0), (-1, -1), 1.5, colors.HexColor('#95a5a6')),
        ('LINELEFT', (0, 0), (-1, -1), 1.5, colors.HexColor('#95a5a6')),
        ('LINERIGHT', (0, 0), (-1, -1), 1.5, colors.HexColor('#95a5a6')),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.HexColor('#ecf0f1'), colors.HexColor('#ffffff')])
    ]))
    story.append(patient_table)
    story.append(Spacer(1, 18))

    # Overall Risk Assessment
    overall_risk = np.mean(results)
    overall_risk_level = classify_risk(overall_risk)
    
    risk_color_map = {
        "Low Risk": colors.HexColor('#27ae60'),
        "Moderate Risk": colors.HexColor('#f39c12'),
        "High Risk": colors.HexColor('#e74c3c')
    }
    
    story.append(Paragraph("Overall Patient Risk Assessment", heading_style))
    story.append(Spacer(1, 12))
    
    risk_style = ParagraphStyle(
        'RiskLabel',
        parent=styles['Normal'],
        fontSize=14,
        textColor=colors.white,
        fontName='Helvetica-Bold'
    )
    
    risk_table = Table([
        [Paragraph("Overall Risk Level", risk_style), 
         Paragraph(f"{overall_risk_level} ({int(overall_risk*100)}%)", risk_style)]
    ], colWidths=[3*inch, 4*inch])
    
    risk_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), risk_color_map[overall_risk_level]),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('PADDING', (0, 0), (-1, -1), 15),
        ('LEFTPADDING', (0, 0), (-1, -1), 15),
        ('RIGHTPADDING', (0, 0), (-1, -1), 15),
        ('LINEABOVE', (0, 0), (-1, -1), 2, colors.white),
        ('LINEBELOW', (0, 0), (-1, -1), 2, colors.white),
        ('LINELEFT', (0, 0), (-1, -1), 2, colors.white),
        ('LINERIGHT', (0, 0), (-1, -1), 2, colors.white),
    ]))
    story.append(risk_table)
    story.append(Spacer(1, 18))

    # Health Risk Overview
    story.append(Paragraph("Health Risk Overview", heading_style))
    
    risk_overview_data = [["Condition", "Risk Percentage", "Risk Level"]]
    for disease, prob in zip(diseases, results):
        level = classify_risk(prob)
        risk_overview_data.append([disease, f"{int(prob*100)}%", level])
    
    overview_table = Table(risk_overview_data, colWidths=[2.2*inch, 2.2*inch, 2.2*inch])
    overview_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LINEABOVE', (0, 0), (-1, -1), 1.5, colors.HexColor('#95a5a6')),
        ('LINEBELOW', (0, 0), (-1, -1), 1.5, colors.HexColor('#95a5a6')),
        ('LINELEFT', (0, 0), (-1, -1), 1.5, colors.HexColor('#95a5a6')),
        ('LINERIGHT', (0, 0), (-1, -1), 1.5, colors.HexColor('#95a5a6')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#ecf0f1'), colors.HexColor('#ffffff')])
    ]))
    story.append(overview_table)
    story.append(Spacer(1, 18))

    # Collect all reasons and recommendations
    all_reasons = set()
    all_recs = set()
    
    for item in insights:
        for reason in item["reasons"]:
            if reason != "All indicators within normal ranges":
                all_reasons.add(reason)
        for rec in item["recommendations"]:
            all_recs.add(rec)

    # Key Risk Factors
    story.append(Paragraph("Key Risk Factors", heading_style))
    if all_reasons:
        for reason in sorted(all_reasons):
            story.append(Paragraph(f"<bullet>•</bullet> {reason}", styles["Normal"]))
    else:
        normal_indicator = ParagraphStyle(
            'NormalIndicator',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#27ae60'),
            fontName='Helvetica-Bold'
        )
        story.append(Paragraph("✓ All indicators within normal ranges", normal_indicator))
    
    story.append(Spacer(1, 18))

    # Recommendations
    story.append(Paragraph("Recommendations", heading_style))
    for rec in sorted(all_recs):
        story.append(Paragraph(f"<bullet>•</bullet> {rec}", styles["Normal"]))
    
    story.append(Spacer(1, 18))

    # Important Disclaimer
    disclaimer_style = ParagraphStyle(
        'Disclaimer',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#856404'),
        borderColor=colors.HexColor('#ffc107'),
        borderWidth=2,
        borderPadding=14,
        borderRadius=0,
        alignment=TA_LEFT,
        spaceAfter=12,
        spaceBefore=12
    )
    
    story.append(Paragraph("!! Important Disclaimer !!", heading_style))
    story.append(Spacer(1, 12))
    disclaimer_text = """
    <b>This assessment is for educational and informational purposes only.</b><br/><br/>
    This report is NOT a substitute for professional medical advice, diagnosis, or treatment. 
    Please consult with qualified healthcare professionals (doctors, nurses, or medical specialists) 
    to interpret these results and receive proper medical guidance.<br/><br/>
    Always seek professional medical advice before making any health-related decisions or changes 
    to your lifestyle or treatment.
    """
    story.append(Paragraph(disclaimer_text, disclaimer_style))

    doc.build(story)
    buffer.seek(0)
    return buffer



# ---------------- UI ----------------

st.markdown("### Enter Your Health Information")

tab1, tab2, tab3, tab4 = st.tabs(["👤 Personal", "❤️ Vitals", "🏃 Lifestyle", "🩸 Blood Profile"])

with tab1:
    col1, col2 = st.columns(2)
    with col1:
        age = st.number_input("Age", min_value=0, max_value=120, value=0, help="Enter age in years")
        gender = st.selectbox("Gender", ["", "male", "female", "other"], format_func=lambda x: "Select gender" if x == "" else x)
    with col2:
        weight = st.number_input("Weight (kg)", min_value=0.0, max_value=200.0, value=0.0, help="Enter weight in kg")
        height = st.number_input("Height (m)", min_value=0.0, max_value=2.5, value=0.0, help="Enter height in meters")

with tab2:
    col1, col2 = st.columns(2)
    with col1:
        sys = st.number_input("Systolic BP (mmHg)", min_value=0, max_value=200, value=0, help="Enter systolic blood pressure")
        dia = st.number_input("Diastolic BP (mmHg)", min_value=0, max_value=130, value=0, help="Enter diastolic blood pressure")
    with col2:
        glucose = st.number_input("Glucose (mg/dL)", min_value=0, max_value=300, value=0, help="Enter glucose level")
        heart_rate = st.number_input("Heart Rate (bpm)", min_value=0, max_value=120, value=0, help="Enter heart rate")

with tab3:
    col1, col2 = st.columns(2)
    with col1:
        smoking = st.selectbox("Smoking Status", ["", "no", "yes"], format_func=lambda x: "Select smoking status" if x == "" else x)
        alcohol = st.selectbox("Alcohol Consumption", ["", "none", "moderate", "high"], format_func=lambda x: "Select alcohol intake" if x == "" else x)
        diet = st.selectbox("Diet Type", ["", "omnivore", "vegan", "vegetarian"], format_func=lambda x: "Select diet type" if x == "" else x)
        sleep = st.number_input("Sleep Hours/Night", min_value=0.0, max_value=12.0, value=0.0, help="Enter sleep hours")
    with col2:
        steps = st.number_input("Daily Steps", min_value=0, max_value=20000, value=0, help="Enter daily steps")
        exercise = st.number_input("Exercise Hours/Week", min_value=0.0, max_value=20.0, value=0.0)
        screen_time = st.number_input("Screen Time Hours/Day", min_value=0.0, max_value=24.0, value=0.0, help="Enter daily screen time")
        meals_per_day = st.number_input("Meals Per Day", min_value=1, max_value=10, value=1, help="Enter number of meals per day")
        mental_health_score = st.slider("Mental Health Score (1-10)", 1, 10, 1, help="1=poor mental health, 10=excellent mental health")

with tab4:
    col1, col2 = st.columns(2)
    with col1:
        ldl = st.number_input("LDL Cholesterol (mg/dL)", min_value=0, max_value=300, value=0, help="Enter LDL cholesterol")
        hdl = st.number_input("HDL Cholesterol (mg/dL)", min_value=0, max_value=100, value=0, help=">40 healthy")
    with col2:
        triglycerides = st.number_input("Triglycerides (mg/dL)", min_value=0, max_value=400, value=0, help="Enter triglycerides")
        stress = st.slider("Stress Level (0-10)", 0, 10, 0, help="0=not selected, 10=very high")

    st.markdown("---")

    form_complete = (
        age > 0 and weight > 0 and height > 0 and sys > 0 and dia > 0 and glucose > 0 and heart_rate > 0 and
        sleep > 0 and steps > 0 and exercise > 0 and ldl > 0 and hdl > 0 and triglycerides > 0 and stress > 0 and
        screen_time >= 0 and meals_per_day > 0 and mental_health_score > 0 and
        gender != "" and smoking != "" and alcohol != "" and diet != ""
    )

    submitted = st.button(
        "🔍 Generate Health Report",
        width='stretch',
        disabled=not form_complete
    )

    if not form_complete:
        st.info("Please complete all fields above to enable report generation.")

if submitted:
    user = {
        "age": age,
        "gender": gender,
        "weight": weight,
        "height": height,
        "systolic_bp": sys,
        "diastolic_bp": dia,
        "glucose": glucose,
        "ldl": ldl,
        "hdl": hdl,
        "smoking": smoking,
        "alcohol": alcohol,
        "sleep_hours": sleep,
        "daily_steps": steps,
        "stress_level": stress,
        "mental_health_score": mental_health_score,
        "diet_type": diet,
        "training_hours": exercise,
        "triglycerides": triglycerides,
        "family_history": "no",
        "screen_time": screen_time,
        "sugar_intake": 50,
        "heart_rate": heart_rate,
        "insulin": 10,
        "meals_per_day": meals_per_day,
        "total_cholesterol": 200
    }

    diseases, results = predict(user)
    insights = generate_insights(user, diseases, results)

    st.success("✅ Assessment Complete! Review your results below.")

    # Overall Risk Classification
    overall_risk = np.mean(results)
    overall_risk_level = classify_risk(overall_risk)
    
    st.markdown("## Overall Patient Risk Assessment")
    risk_color_val = risk_color(overall_risk_level)
    st.markdown(f"""
    <div style="background-color: {risk_color_val}; color: white; padding: 20px; border-radius: 12px; text-align: center; font-size: 18px; font-weight: bold;">
    Overall Risk Level: {overall_risk_level} ({int(overall_risk*100)}%)
    </div>
    """, unsafe_allow_html=True)

    # Overview Metrics
    st.markdown("## Health Risk Overview")
    cols = st.columns(5)
    for i, (disease, prob) in enumerate(zip(diseases, results)):
        with cols[i]:
            level = classify_risk(prob)
            st.metric(disease, f"{int(prob*100)}%", level)

    # Risk Visualization
    st.markdown("## Risk Breakdown")
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=diseases,
        y=[r * 100 for r in results],
        marker_color=[risk_color(classify_risk(r)) for r in results],
        text=[f"{int(r*100)}%" for r in results],
        textposition='auto'
    ))
    fig.update_layout(
        title="Health Risk Probabilities",
        xaxis_title="Condition",
        yaxis_title="Risk Percentage (%)",
        showlegend=False
    )
    st.plotly_chart(fig, width='stretch')

    # Collect all reasons and recommendations
    all_reasons = set()
    all_recs = set()
    
    for item in insights:
        for reason in item["reasons"]:
            if reason != "All indicators within normal ranges":
                all_reasons.add(reason)
        for rec in item["recommendations"]:
            all_recs.add(rec)

    # Key Risk Factors
    st.markdown("## Key Risk Factors")
    if all_reasons:
        for reason in sorted(all_reasons):
            st.markdown(f"• {reason}")
    else:
        st.markdown("✅ All indicators within normal ranges")

    # Overall Recommendations
    st.markdown("## Recommendations")
    for rec in sorted(all_recs):
        st.markdown(f"• {rec}")

    # Important Disclaimer
    st.markdown("---")
    st.markdown("""
    <div style="background-color: #fff3cd; color: #856404; padding: 20px; border-radius: 12px; border-left: 5px solid #ffc107;">
    <h4>⚠️ Important Disclaimer</h4>
    <p><strong>This assessment is for educational and informational purposes only.</strong></p>
    <p>This report is NOT a substitute for professional medical advice, diagnosis, or treatment. Please consult with qualified healthcare professionals (doctors, nurses, or medical specialists) to interpret these results and receive proper medical guidance.</p>
    <p>Always seek professional medical advice before making any health-related decisions or changes to your lifestyle or treatment.</p>
    </div>
    """, unsafe_allow_html=True)

    # Save to history
    if "history" not in st.session_state:
        st.session_state.history = pd.DataFrame()
    new_entry = pd.DataFrame([{
        "date": datetime.datetime.now(),
        "diabetes_risk": results[0],
        "hypertension_risk": results[1],
        "heart_disease_risk": results[2],
        "obesity_risk": results[3],
        "stress_risk": results[4],
        "overall_risk": np.mean(results)
    }])
    st.session_state.history = pd.concat([st.session_state.history, new_entry], ignore_index=True)

    if not st.session_state.guest:
        app_helpers.save_history(st.session_state.user_email, st.session_state.history)

    # Download Report
    st.markdown("---")
    st.markdown("### 📥 Export Your Report")
    pdf = generate_pdf(user, insights, results, diseases)
    st.download_button(
        label="📄 Download Full Report as PDF",
        data=pdf,
        file_name=f"health_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
        mime="application/pdf",
        width='stretch'
    )
