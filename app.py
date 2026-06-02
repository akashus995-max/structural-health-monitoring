import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from fpdf import FPDF
import datetime
import time
import io

# -----------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & INTERFACE THEME
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="AI-Based Structural Health Monitoring Dashboard",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Slate Steel Engineering UI Styles
st.markdown("""
<style>
    /* Global modifications */
    .reportview-container .main .block-container {
        padding-top: 1.5rem;
    }
    
    /* Sleek Industrial Slate Metric Cards */
    .custom-card {
        background-color: rgba(120, 140, 160, 0.08); 
        border-radius: 12px;
        padding: 20px;
        border: 1px solid rgba(120, 140, 160, 0.2);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.03);
        margin-bottom: 15px;
        transition: transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
    }
    .custom-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.08);
    }
    .card-title {
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
        color: #7f8c8d;
        letter-spacing: 0.8px;
    }
    .card-value {
        font-size: 28px;
        font-weight: 700;
        margin-top: 5px;
        margin-bottom: 5px;
    }
    .card-subtitle {
        font-size: 11px;
        opacity: 0.7;
    }
    
    /* Left Border Indicators */
    .border-safe { border-left: 6px solid #2ecc71; }
    .border-warning { border-left: 6px solid #f39c12; }
    .border-danger { border-left: 6px solid #e74c3c; }
    
    /* Pulse Indicators for Real-Time Status Alerts */
    .indicator-pulse {
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 8px;
    }
    .pulse-safe {
        background-color: #2ecc71;
        box-shadow: 0 0 0 0 rgba(46, 204, 113, 0.7);
        animation: pulse-s 1.5s infinite;
    }
    .pulse-warn {
        background-color: #f39c12;
        box-shadow: 0 0 0 0 rgba(243, 156, 18, 0.7);
        animation: pulse-w 1.5s infinite;
    }
    .pulse-crit {
        background-color: #e74c3c;
        box-shadow: 0 0 0 0 rgba(231, 76, 60, 0.7);
        animation: pulse-c 1.5s infinite;
    }
    
    @keyframes pulse-s {
        0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(46, 204, 113, 0.7); }
        70% { transform: scale(1); box-shadow: 0 0 0 6px rgba(46, 204, 113, 0); }
        100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(46, 204, 113, 0); }
    }
    @keyframes pulse-w {
        0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(243, 156, 18, 0.7); }
        70% { transform: scale(1); box-shadow: 0 0 0 6px rgba(243, 156, 18, 0); }
        100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(243, 156, 18, 0); }
    }
    @keyframes pulse-c {
        0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(231, 76, 60, 0.7); }
        70% { transform: scale(1); box-shadow: 0 0 0 6px rgba(231, 76, 60, 0); }
        100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(231, 76, 60, 0); }
    }
</style>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# 2. ENGINEERING FORMULAS & SCIENTIFIC SCORES
# -----------------------------------------------------------------------------
def calculate_health_index(age, crack, corrosion, deflection, vibration):
    """
    Calculates the composite Structural Health Index (SHI) from 0 to 100
    by normalizing physical inputs into standardized structural scores.
    
    Normalizing equations explained:
    1. Crack Width Score (S_crack):
       Cracks > 0.3mm affect concrete serviceability, whereas cracks > 5.0mm represent severe structural
       shear/flexural risks. Normalized linearly to 5.0mm.
       Formula: S_crack = min(100.0, (Crack Width / 5.0) * 100.0)
       
    2. Corrosion Score (S_corrosion):
       Measures steel reinforcement cross-sectional loss. Input is already a percentage from 0 to 100%.
       Formula: S_corrosion = Corrosion Level (%)
       
    3. Deflection Score (S_deflection):
       Measures structural flexural deflection. Normal concrete beams have maximum allowable deflection limits 
       based on span length L (e.g. L/250). A nominal threshold of 40mm deflection is chosen as severe distress.
       Formula: S_deflection = min(100.0, (Deflection / 40.0) * 100.0)
       
    4. Vibration Score (S_vibration):
       Measures dynamic vibration level. A vibration frequency shift or high amplitude resonance above 15Hz 
       is considered structurally dangerous for basic civil buildings.
       Formula: S_vibration = min(100.0, (Vibration / 15.0) * 100.0)
       
    5. Age Score (S_age):
       Represents structural fatigue, environmental degradation, carbonation, and chemical attack. Normalizes age to 80 years.
       Formula: S_age = min(100.0, (Age / 80.0) * 100.0)
       
    Composite Health Index (SHI) weight distribution:
       SHI = 100 - (0.25 * S_crack) - (0.20 * S_corrosion) - (0.20 * S_deflection) - (0.20 * S_vibration) - (0.15 * S_age)
    """
    s_crack = min(100.0, (crack / 5.0) * 100.0)
    s_corrosion = float(corrosion)
    s_deflection = min(100.0, (deflection / 40.0) * 100.0)
    s_vibration = min(100.0, (vibration / 15.0) * 100.0)
    s_age = min(100.0, (age / 80.0) * 100.0)
    
    shi = 100.0 - (0.25 * s_crack) - (0.20 * s_corrosion) - (0.20 * s_deflection) - (0.20 * s_vibration) - (0.15 * s_age)
    
    scores = {
        's_crack': s_crack,
        's_corrosion': s_corrosion,
        's_deflection': s_deflection,
        's_vibration': s_vibration,
        's_age': s_age
    }
    
    return max(0.0, shi), scores


def get_audit_details(health_index):
    """
    Categorizes the calculated Structural Health Index into condition ratings
    and produces professional civil engineering recommendations.
    """
    if health_index >= 90:
        rating = "Excellent"
        color = "#2ecc71"
        style_class = "border-safe"
        recs = [
            "Conduct routine visual inspections annually.",
            "Verify deflection values remain stable under active live loads.",
            "Maintain general non-structural joints and aesthetic finishes."
        ]
    elif health_index >= 75:
        rating = "Good"
        color = "#2ecc71"
        style_class = "border-safe"
        recs = [
            "Monitor minor concrete hairline cracking on secondary members.",
            "Apply protective surface coatings (silane/siloxane) to reduce carbonation rate.",
            "Inspect roof drains and downspouts to prevent ponding on concrete slabs."
        ]
    elif health_index >= 60:
        rating = "Fair"
        color = "#f39c12"
        style_class = "border-warning"
        recs = [
            "Inject structural cracks wider than 0.3mm with low-viscosity epoxy resin.",
            "Perform non-destructive testing (UPV / Rebound Hammer) in areas of higher deflection.",
            "Conduct micro-corrosion monitoring of steel rebar in columns."
        ]
    elif health_index >= 45:
        rating = "Poor"
        color = "#e67e22"
        style_class = "border-warning"
        recs = [
            "Implement carbon fiber reinforced polymer (CFRP) wrapping on deficient concrete beams.",
            "Impose temporary structural occupancy or axle load limits.",
            "Perform patch repair on spalled areas with polymer-modified repair mortars."
        ]
    else:
        rating = "Critical"
        color = "#e74c3c"
        style_class = "border-danger"
        recs = [
            "Notify municipal building regulators and issue immediate structural evacuation.",
            "Install heavy-duty emergency steel shoring or scaffolding underneath distressed structural members.",
            "Mandate a comprehensive physical forensic structural audit including core-drilling tests."
        ]
    return rating, color, style_class, recs


# -----------------------------------------------------------------------------
# 3. AI RISK MODEL PREDICTION & TRAINING
# -----------------------------------------------------------------------------
@st.cache_resource
def train_ai_model():
    """
    Generates a synthetic historical audit dataset of 1500 structures
    and trains a Random Forest Classifier to categorize risk levels.
    """
    np.random.seed(42)
    n_samples = 1500
    
    # Feature distributions typical of infrastructure
    age = np.random.uniform(0, 100, n_samples)
    crack_width = np.random.exponential(scale=1.2, size=n_samples)
    crack_width = np.clip(crack_width, 0.0, 10.0)
    
    corrosion = np.random.beta(a=1.5, b=4.0, size=n_samples) * 100.0
    
    deflection = np.random.normal(loc=12.0, scale=8.0, size=n_samples)
    deflection = np.clip(deflection, 0.0, 80.0)
    
    vibration = np.random.uniform(0.5, 25.0, n_samples)
    temperature = np.random.normal(loc=25.0, scale=7.0, size=n_samples)
    floors = np.random.randint(1, 25, size=n_samples)
    
    df = pd.DataFrame({
        'Age': age,
        'CrackWidth': crack_width,
        'Corrosion': corrosion,
        'Deflection': deflection,
        'Vibration': vibration,
        'Temperature': temperature,
        'Floors': floors
    })
    
    # Mathematical health index labels for target classification
    s_crack = np.minimum(100.0, (df['CrackWidth'] / 5.0) * 100.0)
    s_corrosion = df['Corrosion']
    s_deflection = np.minimum(100.0, (df['Deflection'] / 40.0) * 100.0)
    s_vibration = np.minimum(100.0, (df['Vibration'] / 15.0) * 100.0)
    s_age = np.minimum(100.0, (df['Age'] / 80.0) * 100.0)
    
    shi = 100.0 - (0.25 * s_crack) - (0.20 * s_corrosion) - (0.20 * s_deflection) - (0.20 * s_vibration) - (0.15 * s_age)
    df['HealthIndex'] = np.clip(shi, 0.0, 100.0)
    
    # Introduce small random noise to labels to represent unobserved field variables
    shi_noisy = shi + np.random.normal(0, 3.0, n_samples)
    
    risk_category = []
    for val in shi_noisy:
        if val >= 75:
            risk_category.append("Safe")
        elif val >= 50:
            risk_category.append("Moderate Risk")
        else:
            risk_category.append("High Risk")
            
    df['RiskCategory'] = risk_category
    
    # Split & Train Model
    X = df[['Age', 'CrackWidth', 'Corrosion', 'Deflection', 'Vibration', 'Temperature', 'Floors']]
    y = df['RiskCategory']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    model = RandomForestClassifier(n_estimators=100, random_state=42, max_depth=10)
    model.fit(X_train, y_train)
    
    accuracy = model.score(X_test, y_test)
    
    return df, model, accuracy


# -----------------------------------------------------------------------------
# 4. REPORT GENERATION ENGINE (PDF)
# -----------------------------------------------------------------------------
class PDFReport(FPDF):
    def header(self):
        # Draw elegant Navy Header bar
        self.set_fill_color(44, 62, 80)
        self.rect(0, 0, 210, 35, 'F')
        
        self.set_text_color(255, 255, 255)
        self.set_font('Helvetica', 'B', 15)
        self.cell(0, 12, 'CIVIL INFRASTRUCTURE STRUCTURAL AUDIT REPORT', ln=1, align='C')
        self.set_font('Helvetica', 'I', 9)
        self.cell(0, 4, 'AI-Based Structural Health Monitoring & Diagnostic Program', ln=1, align='C')
        self.ln(18)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f'Page {self.page_no()} | Confidential Engineering Audit | Generated: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}', ln=0, align='C')


def generate_pdf_report(inputs, health_index, rating, risk, confidence, recommendations):
    """
    Assembles input telemetry, SHI scores, AI evaluation, and recommendations
    into a structured engineering PDF document.
    """
    pdf = PDFReport()
    pdf.add_page()
    
    # Status Banner
    if rating in ["Excellent", "Good"]:
        banner_color = (46, 204, 113) # Green
    elif rating == "Fair":
        banner_color = (243, 156, 18) # Amber
    else:
        banner_color = (231, 76, 60) # Red
        
    pdf.ln(5)
    pdf.set_fill_color(*banner_color)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 10, f"OVERALL RATING: {rating.upper()} (SHI SCORE: {health_index:.1f}/100)", ln=1, align='C', fill=True)
    pdf.ln(5)
    
    pdf.set_text_color(0, 0, 0)
    
    # 1. Structure Details Table
    pdf.set_font('Helvetica', 'B', 11)
    pdf.cell(0, 8, "1. Infrastructure Profile & Context", ln=1)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(2)
    
    pdf.set_font('Helvetica', '', 10)
    col_w = 95
    pdf.cell(col_w, 6, f"Structure Age: {inputs['Age']} years", border=1)
    pdf.cell(col_w, 6, f"Total Floor Levels: {inputs['Floors']}", border=1, ln=1)
    pdf.cell(col_w, 6, f"Audit Date/Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}", border=1)
    pdf.cell(col_w, 6, f"AI Risk Prediction: {risk} ({confidence:.1f}% confidence)", border=1, ln=1)
    pdf.ln(5)
    
    # 2. Measured Telemetry Table
    pdf.set_font('Helvetica', 'B', 11)
    pdf.cell(0, 8, "2. Inspected Performance Parameters", ln=1)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(2)
    
    pdf.set_font('Helvetica', 'B', 10)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(50, 7, "Parameter", border=1, fill=True)
    pdf.cell(40, 7, "Measured Value", border=1, fill=True)
    pdf.cell(100, 7, "Regulatory & Reference Limits", border=1, fill=True, ln=1)
    
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(50, 6, "Crack Width", border=1)
    pdf.cell(40, 6, f"{inputs['CrackWidth']:.2f} mm", border=1)
    pdf.cell(100, 6, "Allowable service limit: <0.3mm (ACI 318). Severe: >5.0mm", border=1, ln=1)
    
    pdf.cell(50, 6, "Corrosion Level", border=1)
    pdf.cell(40, 6, f"{inputs['Corrosion']:.1f} %", border=1)
    pdf.cell(100, 6, "Minor weathering: <10%. Severe reinforcement loss: >50%", border=1, ln=1)
    
    pdf.cell(50, 6, "Deflection", border=1)
    pdf.cell(40, 6, f"{inputs['Deflection']:.2f} mm", border=1)
    pdf.cell(100, 6, "L/250 limit for concrete flexure. Critical threshold: 40mm", border=1, ln=1)
    
    pdf.cell(50, 6, "Vibration Level", border=1)
    pdf.cell(40, 6, f"{inputs['Vibration']:.2f} Hz", border=1)
    pdf.cell(100, 6, "Natural frequency monitoring. Danger excitation limit: >15Hz", border=1, ln=1)
    
    pdf.cell(50, 6, "Temperature", border=1)
    pdf.cell(40, 6, f"{inputs['Temperature']:.1f} C", border=1)
    pdf.cell(100, 6, "Concrete thermal range. Standard service bounds: 10C - 45C", border=1, ln=1)
    pdf.ln(5)
    
    # 3. Recommendations
    pdf.set_font('Helvetica', 'B', 11)
    pdf.cell(0, 8, "3. Engineering Maintenance Action Items", ln=1)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(2)
    
    pdf.set_font('Helvetica', '', 10)
    pdf.set_fill_color(248, 249, 250)
    rec_text = "Based on computed metrics and Random Forest classifier categorisation, the following steps are required:\n\n"
    for i, rec in enumerate(recommendations, 1):
        rec_text += f"{i}. {rec}\n"
        
    pdf.multi_cell(0, 5, rec_text, border=1, fill=True)
    pdf.ln(5)
    
    # 4. Engineering Disclaimer
    pdf.set_font('Helvetica', 'B', 9)
    pdf.cell(0, 6, "Notice & Liability Disclaimer", ln=1)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(2)
    pdf.set_font('Helvetica', 'I', 8)
    pdf.set_text_color(120, 120, 120)
    disclaimer = ("This report is generated automatically by a software simulation platform. It is designed for "
                  "academic modeling, student instruction, and demonstration. It does not replace a comprehensive, "
                  "physical engineering investigation performed by a certified structural professional using physically "
                  "calibrated core tests, concrete scanners, and structural telemetry.")
    pdf.multi_cell(0, 4, disclaimer)
    
    pdf_bytes = pdf.output()
    if isinstance(pdf_bytes, str):
        return pdf_bytes.encode('latin1')
    return bytes(pdf_bytes)


# -----------------------------------------------------------------------------
# 5. DYNAMIC BUILDING DEGRADATION SEQUENCE GENERATOR
# -----------------------------------------------------------------------------
def generate_historical_building_trend(age, floors, current_crack, current_corrosion, current_deflection, current_vibration):
    """
    Generates a historical timeline of audits for this specific building,
    simulating aging and structural degradation from a clean initial state (Age=0)
    to its current measured parameters.
    """
    intervals = max(5, int(age // 5) + 1)
    ages = np.linspace(0, age, intervals)
    
    # Simulate gradual degradation trends over time
    crack_trend = np.linspace(0.0, current_crack, intervals)
    corrosion_trend = np.linspace(0.0, current_corrosion, intervals)
    deflection_trend = np.linspace(1.5, current_deflection, intervals)
    vibration_trend = np.linspace(3.0, current_vibration, intervals)
    
    df_trend = pd.DataFrame({
        'Inspection': [f"Audit {i+1} (Age {int(a)})" for i, a in enumerate(ages)],
        'Age': ages,
        'CrackWidth': crack_trend,
        'Corrosion': corrosion_trend,
        'Deflection': deflection_trend,
        'Vibration': vibration_trend
    })
    
    # Calculate historical health indexes
    shi_values = []
    for idx, row in df_trend.iterrows():
        shi, _ = calculate_health_index(
            row['Age'], row['CrackWidth'], row['Corrosion'], row['Deflection'], row['Vibration']
        )
        shi_values.append(shi)
    df_trend['HealthIndex'] = shi_values
    
    return df_trend


# -----------------------------------------------------------------------------
# 6. APP MAIN HEADER & SIDEBAR NAVIGATION
# -----------------------------------------------------------------------------
st.title("AI-Based Structural Health Monitoring & Audit Dashboard")

# Initialize models and datasets
df_synthetic, model_rf, model_accuracy = train_ai_model()

# Sidebar Setup
st.sidebar.image("https://img.icons8.com/color/150/bridge.png", width=90)
st.sidebar.header("Navigation Panel")
page = st.sidebar.radio(
    "Choose Dashboard View",
    ["🏢 Academic Overview & Theory",
     "🔍 Structural Audit & AI Predictor",
     "📊 Live Telemetry Simulator",
     "📁 Database & Report Center"]
)

st.sidebar.markdown("---")
st.sidebar.subheader("Dashboard Diagnostics")
st.sidebar.info(f"🤖 Random Forest Classifier Model trained successfully.\n\n🎯 Classification Accuracy: **{model_accuracy*100:.2f}%**")

# -----------------------------------------------------------------------------
# PAGE A: ACADEMIC OVERVIEW & THEORY
# -----------------------------------------------------------------------------
if page == "🏢 Academic Overview & Theory":
    st.header("Project Overview & Academic Framework")
    
    st.markdown("""
    ### Project Objective
    Civil infrastructure systems such as buildings, bridges, and tunnels represent massive capital investments that degrade over time due to environmental weathering, fatigue, corrosion, and seismic loading. 
    **Structural Health Monitoring (SHM)** and **Structural Auditing** are vital engineering processes used to transition infrastructure management from *reactive maintenance* (repairing after failures) to *predictive, proactive maintenance* (remediating early warning signals).
    
    This software platform simulates engineering inspections, calculates a mathematical **Structural Health Index (SHI)**, uses machine learning (**Random Forest Classifier**) to predict risk categories, and acts as an educational interface for civil engineering students.
    """)
    
    st.markdown("---")
    
    st.subheader("Methodology Workflow")
    # Custom Mermaid diagram representation inside streamlit markdown
    st.markdown("""
    ```mermaid
    graph TD;
        A[Periodic Inspections & Sensor Telemetry] --> B[Normalize Raw Inputs S_i];
        B --> C[Compute Weighted Structural Health Index SHI];
        C --> D[Identify Audit Rating: Excellent to Critical];
        A --> E[Train Random Forest Classifier on City Database];
        E --> F[Inference: Predict Risk Level Safe / Mod / High];
        D --> G[Generate Engineering Action Items];
        F --> G;
        G --> H[Export PDF Compliance Audit Report];
    ```
    """, unsafe_allow_html=True)
    st.caption("Diagram showing structural auditing and machine learning risk classification sequence.")
    
    st.markdown("---")
    
    st.subheader("Engineering Formulas Used")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        All raw engineering measurements vary in scale and unit metrics. To evaluate structural safety, each parameters is normalized into a score from $0$ (ideal condition) to $100$ (extreme damage threshold):
        """)
        st.latex(r"S_{\text{crack}} = \min\left(100.0, \frac{\text{Crack Width (mm)}}{5.0} \times 100.0\right)")
        st.latex(r"S_{\text{corrosion}} = \text{Corrosion Level (\%)}")
        st.latex(r"S_{\text{deflection}} = \min\left(100.0, \frac{\text{Deflection (mm)}}{40.0} \times 100.0\right)")
        st.latex(r"S_{\text{vibration}} = \min\left(100.0, \frac{\text{Vibration (Hz)}}{15.0} \times 100.0\right)")
        st.latex(r"S_{\text{age}} = \min\left(100.0, \frac{\text{Structure Age (years)}}{80.0} \times 100.0\right)")
        
    with col2:
        st.markdown("""
        Once parameters are converted to standardized scores, the overall **Structural Health Index (SHI)** is computed as a weighted deduction from $100$. The weights reflect civil engineering guidelines for member load-bearing capacity reduction:
        """)
        st.latex(r"\text{SHI} = 100 - (0.25 \times S_{\text{crack}}) - (0.20 \times S_{\text{corrosion}}) - (0.20 \times S_{\text{deflection}}) - (0.20 \times S_{\text{vibration}}) - (0.15 \times S_{\text{age}})")
        
        st.markdown("""
        **Weight Rationale:**
        * **Crack Width (25%)**: Cracks are visual indicators of structural stress, shear, or flexural cracking, directly exposing reinforcement to moisture.
        * **Corrosion (20%)**: Directly reduces the reinforcement cross-sectional area and steel tensile capacity.
        * **Deflection (20%)**: Evaluates structural stiffness and structural serviceability index limits.
        * **Vibration (20%)**: Checks dynamic natural frequency changes indicating local stiffness loss.
        * **Age (15%)**: Accounts for carbonation, creep, and environmental degradation factors.
        """)

    st.markdown("---")
    
    st.subheader("Key Academic Assumptions")
    st.markdown("""
    * **Independent Degradation**: It is assumed that structural parameters behave independently when calculating the health index, although in field conditions, corrosion leads to faster concrete cracking.
    * **Reference Bounds**: Normalized bounds are set based on standardized building codes (e.g. ACI 318, Indian Standard IS 456, and Eurocode 2).
    * **Environmental Stability**: Temperature fluctuations are assumed to represent expansion/contraction parameters, but are kept stable to prevent thermal deflection anomalies during regular audits.
    """)
    
    st.info("💡 **Student Note:** You can test these formulas by navigating to the **Structural Audit & AI Predictor** tab in the sidebar and modifying the sliders.")

# -----------------------------------------------------------------------------
# PAGE B: STRUCTURAL AUDIT & AI PREDICTOR
# -----------------------------------------------------------------------------
elif page == "🔍 Structural Audit & AI Predictor":
    st.header("Structural Audit Panel & ML Inference")
    
    # Layout splits into Control Panel and Outputs
    col_input, col_kpi = st.columns([1, 2])
    
    with col_input:
        st.subheader("Inspection Input Panel")
        age = st.slider("Structure Age (years)", 0, 100, 25, help="Current operational age of the civil infrastructure.")
        crack = st.slider("Crack Width (mm)", 0.0, 10.0, 1.2, 0.1, help="Max measured width of active concrete cracks.")
        corrosion = st.slider("Corrosion Level (%)", 0, 100, 15, help="Percentage cross-sectional steel loss due to rust.")
        deflection = st.slider("Deflection (mm)", 0.0, 80.0, 14.5, 0.5, help="Measured deflection of primary structural member under load.")
        vibration = st.slider("Vibration Level (Hz)", 0.5, 25.0, 4.2, 0.1, help="Fundamental structural vibration frequency.")
        temperature = st.slider("Ambient Temperature (°C)", 0, 50, 27, help="Ambient temperature during audit measurements.")
        floors = st.number_input("Number of Floor Levels", min_value=1, max_value=40, value=5, step=1, help="Total vertical stories of the asset.")
        
        # Calculate active values
        shi, scores = calculate_health_index(age, crack, corrosion, deflection, vibration)
        rating, rating_color, rating_style, recommendations = get_audit_details(shi)
        
        # Run AI prediction
        live_data = pd.DataFrame([{
            'Age': age,
            'CrackWidth': crack,
            'Corrosion': corrosion,
            'Deflection': deflection,
            'Vibration': vibration,
            'Temperature': temperature,
            'Floors': floors
        }])
        
        risk_prediction = model_rf.predict(live_data)[0]
        prediction_probs = model_rf.predict_proba(live_data)[0]
        class_labels = model_rf.classes_
        pred_confidence = prediction_probs[np.where(class_labels == risk_prediction)[0][0]] * 100.0

    with col_kpi:
        st.subheader("Audit Classification & AI Inference Results")
        
        # KPI Card Row
        c1, c2, c3 = st.columns(3)
        
        with c1:
            st.markdown(f"""
            <div class="custom-card border-safe" style="border-left-color: {rating_color};">
                <div class="card-title">Structural Health Index</div>
                <div class="card-value" style="color: {rating_color};">{shi:.1f} / 100</div>
                <div class="card-subtitle">Composite SHI Score</div>
            </div>
            """, unsafe_allow_html=True)
            
        with c2:
            st.markdown(f"""
            <div class="custom-card" style="border-left: 6px solid {rating_color};">
                <div class="card-title">Audit Rating</div>
                <div class="card-value" style="color: {rating_color};">{rating}</div>
                <div class="card-subtitle">Calculated Condition Rating</div>
            </div>
            """, unsafe_allow_html=True)
            
        with c3:
            # Match Risk border style
            risk_border = "border-safe" if risk_prediction == "Safe" else ("border-warning" if risk_prediction == "Moderate Risk" else "border-danger")
            risk_color = "#2ecc71" if risk_prediction == "Safe" else ("#f39c12" if risk_prediction == "Moderate Risk" else "#e74c3c")
            st.markdown(f"""
            <div class="custom-card {risk_border}">
                <div class="card-title">AI Risk Category</div>
                <div class="card-value" style="color: {risk_color};">{risk_prediction}</div>
                <div class="card-subtitle">Confidence: {pred_confidence:.1f}%</div>
            </div>
            """, unsafe_allow_html=True)
            
        # Immediate Danger Alerts based on thresholds
        danger_alerts = []
        if crack > 3.5:
            danger_alerts.append(f"⚠️ **Crack Threat**: Structural crack width ({crack:.2f}mm) exceeds safe serviceability limit of 3.5mm.")
        if deflection > 35.0:
            danger_alerts.append(f"⚠️ **Excessive Flexure**: Member deflection ({deflection:.2f}mm) exceeds safety limits of 35mm.")
        if vibration > 15.0:
            danger_alerts.append(f"⚠️ **Dynamic Excitation Alert**: Vibration frequency ({vibration:.2f}Hz) indicates structural stiffness anomalies.")
            
        if danger_alerts:
            for alert in danger_alerts:
                st.error(alert)
        elif shi < 50:
            st.warning("⚠️ **Low SHI Score Alert**: Structure is in Poor or Critical health. Restrict loading immediately.")
        else:
            st.success("🟢 **Operational Integrity**: Current measurements are within acceptable safety margins.")

        # Interactive Gauges
        c_gauge, c_radar = st.columns([1.2, 1])
        
        with c_gauge:
            # Plotly SHI Gauge chart
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=shi,
                domain={'x': [0, 1], 'y': [0, 1]},
                gauge={
                    'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#7f8c8d"},
                    'bar': {'color': "#34495e"},
                    'bgcolor': "rgba(0,0,0,0)",
                    'borderwidth': 1,
                    'bordercolor': "#95a5a6",
                    'steps': [
                        {'range': [0, 45], 'color': '#fadbd8'}, # Soft red
                        {'range': [45, 60], 'color': '#fdebd0'}, # Soft orange
                        {'range': [60, 75], 'color': '#fcf3cf'}, # Soft yellow
                        {'range': [75, 90], 'color': '#d4efdf'}, # Soft light green
                        {'range': [90, 100], 'color': '#a9dfbf'} # Soft emerald green
                    ],
                    'threshold': {
                        'line': {'color': "#c0392b", 'width': 3},
                        'thickness': 0.75,
                        'value': shi
                    }
                }
            ))
            fig_gauge.update_layout(
                height=250, 
                margin=dict(l=20, r=20, t=30, b=20),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_gauge, use_container_width=True)
            
        with c_radar:
            # Bar chart comparing normalized parameter scores
            categories = ['Crack Width', 'Corrosion', 'Deflection', 'Vibration', 'Structure Age']
            values = [scores['s_crack'], scores['s_corrosion'], scores['s_deflection'], scores['s_vibration'], scores['s_age']]
            
            fig_bar = px.bar(
                x=categories, 
                y=values,
                labels={'x': 'Structural Parameter', 'y': 'Normalized Damage Score (%)'},
                title="Normalized Damage Scores (Higher = Worse)",
                color=values,
                color_continuous_scale=['#2ecc71', '#f1c40f', '#e74c3c'],
                range_y=[0, 100]
            )
            fig_bar.update_layout(
                height=250, 
                margin=dict(l=10, r=10, t=40, b=10),
                coloraxis_showscale=False,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        st.markdown("### Engineering Recommendations & Action Plan")
        rec_box = ""
        for idx, rec in enumerate(recommendations, 1):
            rec_box += f"* **Action {idx}:** {rec}\n"
        st.markdown(rec_box)
        
        # Historical Trend Generation for current building parameters
        st.markdown("---")
        st.subheader("Historical Degradation Trends for Current Asset")
        st.caption("This chart displays how the asset degraded over time from construction (Age 0) to its current age, based on linear corrosion/cracking progress and stiffness reductions.")
        
        df_trend = generate_historical_building_trend(age, floors, crack, corrosion, deflection, vibration)
        
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(x=df_trend['Age'], y=df_trend['HealthIndex'], mode='lines+markers', name='Structural Health Index (SHI)', line=dict(color='#2c3e50', width=3)))
        fig_trend.add_trace(go.Scatter(x=df_trend['Age'], y=df_trend['CrackWidth']*10, mode='lines', name='Crack Width (x10 mm)', line=dict(color='#8e44ad', dash='dash')))
        fig_trend.add_trace(go.Scatter(x=df_trend['Age'], y=df_trend['Corrosion'], mode='lines', name='Corrosion (%)', line=dict(color='#e67e22', dash='dot')))
        fig_trend.add_trace(go.Scatter(x=df_trend['Age'], y=df_trend['Deflection'], mode='lines', name='Deflection (mm)', line=dict(color='#3498db', dash='dashdot')))
        
        fig_trend.update_layout(
            xaxis_title="Structure Age (years)",
            yaxis_title="Metric Score / Scale Value",
            template="plotly_white",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            height=300,
            margin=dict(l=10, r=10, t=10, b=10)
        )
        st.plotly_chart(fig_trend, use_container_width=True)

# -----------------------------------------------------------------------------
# PAGE C: LIVE TELEMETRY SIMULATOR
# -----------------------------------------------------------------------------
elif page == "📊 Live Telemetry Simulator":
    st.header("Real-Time Telemetry Simulation")
    st.markdown("""
    This panel simulates live sensor telemetry for dynamic vibration acceleration, structural beam deflection, 
    ambient structural temperature, and micro-crack expansion.
    """)
    
    # Telemetry Control Interface
    col_ctrl, col_status = st.columns([1, 2])
    with col_ctrl:
        st.subheader("Simulation Controls")
        if st.button("▶️ Start Live Telemetry", use_container_width=True):
            st.session_state.simulation_running = True
            
        if st.button("⏸️ Stop Live Telemetry", use_container_width=True):
            st.session_state.simulation_running = False
            
    with col_status:
        st.subheader("Dynamic Telemetry Status")
        if st.session_state.simulation_running:
            st.markdown("""
            <div class="custom-card border-warning">
                <span class="indicator-pulse pulse-warn"></span>
                <span style="font-weight: 600; font-size: 16px;">LIVE SIMULATION ACTIVE</span>
                <div style="font-size: 12px; margin-top: 5px; opacity: 0.8;">The sensor feed is continuously refreshing and writing parameters to session storage. Check charts below.</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="custom-card border-safe">
                <span class="indicator-pulse pulse-safe"></span>
                <span style="font-weight: 600; font-size: 16px;">SYSTEM PAUSED</span>
                <div style="font-size: 12px; margin-top: 5px; opacity: 0.8;">Simulation is idle. Click 'Start Live Telemetry' to generate dynamic readings.</div>
            </div>
            """, unsafe_allow_html=True)

    # Telemetry data processor
    if st.session_state.simulation_running:
        now = datetime.datetime.now()
        
        # Extract last values if exist
        if len(st.session_state.telemetry_history) > 0:
            last_vib = st.session_state.telemetry_history['Vibration'].iloc[-1]
            last_def = st.session_state.telemetry_history['Deflection'].iloc[-1]
            last_crack = st.session_state.telemetry_history['CrackWidth'].iloc[-1]
        else:
            last_vib = 4.2
            last_def = 14.5
            last_crack = 1.2
            
        # Simulate new data point
        # Vibration: constant signal + random noise + occasional massive excitation spike
        vib_reading = float(np.random.normal(loc=4.5, scale=0.8) + (13.5 if np.random.random() > 0.94 else 0.0))
        # Deflection: slow random walk with gradual upward drift
        def_reading = float(np.clip(last_def + np.random.normal(loc=0.08, scale=0.4), 0.0, 75.0))
        # Crack growth: very slow monotonic expansion
        crack_reading = float(np.clip(last_crack + (0.015 if np.random.random() > 0.85 else 0.0), 0.0, 10.0))
        # Temperature: diurnal sinus curve representation
        temp_reading = float(27.0 + 6.0 * np.sin(now.timestamp() / 15.0) + np.random.normal(0, 0.15))
        
        new_row = {
            'Timestamp': now.strftime("%H:%M:%S"),
            'Vibration': vib_reading,
            'Deflection': def_reading,
            'Temperature': temp_reading,
            'CrackWidth': crack_reading
        }
        
        # Concatenate and restrict window to last 50 points
        df_hist = st.session_state.telemetry_history
        df_hist = pd.concat([df_hist, pd.DataFrame([new_row])], ignore_index=True)
        if len(df_hist) > 50:
            df_hist = df_hist.iloc[-50:]
        st.session_state.telemetry_history = df_hist

    # Display Charts if history exists
    df_hist = st.session_state.telemetry_history
    if len(df_hist) > 0:
        c1, c2 = st.columns(2)
        with c1:
            fig_vib = px.line(df_hist, x='Timestamp', y='Vibration', title='Vibration Spectrum Feed (Hz)', template="plotly_white")
            fig_vib.update_traces(line_color='#e74c3c', line_width=2.5)
            fig_vib.update_layout(height=240, margin=dict(l=10, r=10, t=35, b=10))
            st.plotly_chart(fig_vib, use_container_width=True)
            
            fig_crack = px.line(df_hist, x='Timestamp', y='CrackWidth', title='Crack Expansion Telemetry (mm)', template="plotly_white")
            fig_crack.update_traces(line_color='#8e44ad', line_width=2.5)
            fig_crack.update_layout(height=240, margin=dict(l=10, r=10, t=35, b=10))
            st.plotly_chart(fig_crack, use_container_width=True)
            
        with c2:
            fig_def = px.line(df_hist, x='Timestamp', y='Deflection', title='Vertical Flexural Deflection (mm)', template="plotly_white")
            fig_def.update_traces(line_color='#3498db', line_width=2.5)
            fig_def.update_layout(height=240, margin=dict(l=10, r=10, t=35, b=10))
            st.plotly_chart(fig_def, use_container_width=True)
            
            fig_temp = px.line(df_hist, x='Timestamp', y='Temperature', title='Thermal Telemetry (°C)', template="plotly_white")
            fig_temp.update_traces(line_color='#e67e22', line_width=2.5)
            fig_temp.update_layout(height=240, margin=dict(l=10, r=10, t=35, b=10))
            st.plotly_chart(fig_temp, use_container_width=True)
            
        # Check active thresholds
        latest = df_hist.iloc[-1]
        active_alerts = []
        if latest['Vibration'] > 15.0:
            active_alerts.append(f"🚨 **THRESHOLD EXCEEDED: High Vibration** - Measured {latest['Vibration']:.2f}Hz. Structural dynamic limits exceeded!")
        if latest['Deflection'] > 35.0:
            active_alerts.append(f"🚨 **THRESHOLD EXCEEDED: Excessive Member Deflection** - Deflection is {latest['Deflection']:.2f}mm. Flexural cracks may accelerate.")
        if latest['CrackWidth'] > 3.5:
            active_alerts.append(f"🚨 **THRESHOLD EXCEEDED: Concrete Crack Width Warning** - Crack width is {latest['CrackWidth']:.2f}mm. Ingress of moisture likely.")
            
        if active_alerts:
            for alert in active_alerts:
                st.error(alert)
        else:
            st.success("🟢 **Operational Normal**: Sensor telemetry indicators remain within code-compliant margins.")
            
    else:
        st.info("System is currently empty. Click 'Start Live Telemetry' above to begin reading simulated structures.")
        
    # Sleep & rerun if simulation active
    if st.session_state.simulation_running:
        time.sleep(0.7)
        st.rerun()

# -----------------------------------------------------------------------------
# PAGE D: DATABASE & REPORT CENTER
# -----------------------------------------------------------------------------
else:
    st.header("Database Management & Inspection Reports")
    
    tab_data, tab_pdf = st.tabs(["📁 City Infrastructure Database", "📄 Generate Audit Compliance PDF"])
    
    with tab_data:
        st.subheader("Synthetic Historical Inspection Register")
        st.markdown("""
        This database displays structural audit files for 1,500 assets compiled across the municipality. 
        It is used to train our Random Forest model and query risk classifications.
        """)
        
        # Risk Distribution Pie Chart
        col_chart, col_stats = st.columns([1, 1])
        with col_chart:
            pie_data = df_synthetic['RiskCategory'].value_counts().reset_index()
            pie_data.columns = ['RiskCategory', 'Count']
            fig_pie = px.pie(
                pie_data, 
                values='Count', 
                names='RiskCategory', 
                title='Risk Class Distribution Across Synthetic Registry',
                color='RiskCategory',
                color_discrete_map={'Safe': '#2ecc71', 'Moderate Risk': '#f39c12', 'High Risk': '#e74c3c'}
            )
            fig_pie.update_layout(height=260, margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(fig_pie, use_container_width=True)
            
        with col_stats:
            st.markdown("#### Database Summary Stats")
            c1, c2 = st.columns(2)
            with c1:
                st.metric("Total Records", len(df_synthetic))
                st.metric("Mean Building Age", f"{df_synthetic['Age'].mean():.1f} Years")
            with c2:
                st.metric("Average Health Index", f"{df_synthetic['HealthIndex'].mean():.1f}")
                st.metric("Model Precision", f"{model_accuracy*100:.1f}%")
                
        st.markdown("---")
        
        # Filter interface
        risk_filter = st.multiselect("Filter by Risk Category", ["Safe", "Moderate Risk", "High Risk"], default=["Safe", "Moderate Risk", "High Risk"])
        df_filtered = df_synthetic[df_synthetic['RiskCategory'].isin(risk_filter)]
        
        # Data table
        st.dataframe(df_filtered.head(100), use_container_width=True)
        
        # CSV Exporter
        csv_buffer = io.StringIO()
        df_synthetic.to_csv(csv_buffer, index=False)
        st.download_button(
            label="📥 Download Database CSV",
            data=csv_buffer.getvalue(),
            file_name="structural_audit_records.csv",
            mime="text/csv"
        )
        
    with tab_pdf:
        st.subheader("Generate & Export Engineering Report")
        st.markdown("""
        Compile the current values from the **Structural Audit Panel** into an official compliance PDF document.
        Please verify your inputs below before exporting:
        """)
        
        # Form for parameters confirmation
        with st.form("pdf_details_form"):
            col_pdf1, col_pdf2 = st.columns(2)
            with col_pdf1:
                pdf_age = st.number_input("Confirmed Age (years)", min_value=0, max_value=120, value=25)
                pdf_crack = st.number_input("Confirmed Crack Width (mm)", min_value=0.0, max_value=15.0, value=1.2, format="%.2f")
                pdf_corrosion = st.number_input("Confirmed Corrosion (%)", min_value=0, max_value=100, value=15)
                pdf_floors = st.number_input("Confirmed Floor Levels", min_value=1, max_value=50, value=5)
            with col_pdf2:
                pdf_deflection = st.number_input("Confirmed Deflection (mm)", min_value=0.0, max_value=100.0, value=14.5, format="%.2f")
                pdf_vibration = st.number_input("Confirmed Vibration (Hz)", min_value=0.1, max_value=30.0, value=4.2, format="%.2f")
                pdf_temp = st.number_input("Confirmed Temperature (°C)", min_value=-10, max_value=60, value=27)
                
            submit_pdf = st.form_submit_button("Generate PDF Report Buffer")
            
        if submit_pdf or 'pdf_compiled' in st.session_state:
            st.session_state.pdf_compiled = True
            
            # Recompute values for PDF
            pdf_shi, pdf_scores = calculate_health_index(pdf_age, pdf_crack, pdf_corrosion, pdf_deflection, pdf_vibration)
            pdf_rating, _, _, pdf_recs = get_audit_details(pdf_shi)
            
            # Predict
            pdf_live = pd.DataFrame([{
                'Age': pdf_age,
                'CrackWidth': pdf_crack,
                'Corrosion': pdf_corrosion,
                'Deflection': pdf_deflection,
                'Vibration': pdf_vibration,
                'Temperature': pdf_temp,
                'Floors': pdf_floors
            }])
            pdf_risk = model_rf.predict(pdf_live)[0]
            pdf_prob = model_rf.predict_proba(pdf_live)[0]
            pdf_conf = pdf_prob[np.where(model_rf.classes_ == pdf_risk)[0][0]] * 100.0
            
            pdf_inputs = {
                'Age': pdf_age,
                'CrackWidth': pdf_crack,
                'Corrosion': pdf_corrosion,
                'Deflection': pdf_deflection,
                'Vibration': pdf_vibration,
                'Temperature': pdf_temp,
                'Floors': pdf_floors
            }
            
            # Generate bytes
            try:
                pdf_bytes = generate_pdf_report(pdf_inputs, pdf_shi, pdf_rating, pdf_risk, pdf_conf, pdf_recs)
                st.success("✅ PDF compilation successful! Click the button below to download your report.")
                
                st.download_button(
                    label="📥 Download Compliance PDF Report",
                    data=pdf_bytes,
                    file_name=f"Structural_Audit_Report_{datetime.datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf"
                )
            except Exception as e:
                st.error(f"Failed to generate report: {e}")
