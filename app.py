import streamlit as st
from PIL import Image
import pandas as pd
import re
import unicodedata
import time
import base64
import os
import io
import requests

# ==============================
# IMPORTACIONES ADICIONALES PARA NN
# ==============================
NN_AVAILABLE = False
try:
    import joblib
    import numpy as np
    from sklearn.neural_network import MLPClassifier 
    from sklearn.preprocessing import StandardScaler
    NN_AVAILABLE = True
except ImportError:
    pass

# Intentamos importar plotly
try:
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

# -----------------------------
# CONFIGURACIÓN GENERAL
# -----------------------------
st.set_page_config(
    page_title="Mar Assistant",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------
# PALETA DE COLORES (UX / BI)
# -----------------------------
PALETTE = {
    "primary": "#154872",
    "accent": "#5DC0DC", 
    "muted": "#437FAC",
    "bg": "#ffffff"
}

# -----------------------------
# CSS GLOBAL
# -----------------------------
st.markdown(f"""
<style>
:root {{
    --mar-primary: {PALETTE['primary']};
    --mar-accent: {PALETTE['accent']};
    --mar-muted: {PALETTE['muted']};
    --mar-bg: {PALETTE['bg']};
    --card-radius: 12px;
    --card-padding: 20px;
    --title-size: 38px;
    --shadow-light: 0 4px 12px rgba(21,72,114,0.06);
    --shadow-hover: 0 6px 16px rgba(21,72,114,0.10);
}}

.stApp {{
    background-color: var(--mar-bg);
    color: #1b2635;
    font-family: 'Roboto', sans-serif;
}}

.title {{
    color: var(--mar-primary);
    font-size: var(--title-size);
    font-weight: 900;
    margin: 0;
    line-height: 1.1;
    font-family: 'Roboto Slab', serif;
}}
.subtitle {{
    color: #34495e;
    font-size: 17px;
    margin: 6px 0 0 0;
    font-weight: 300;
}}

.mar-card {{
    background-color: white;
    padding: var(--card-padding);
    border-radius: var(--card-radius);
    box-shadow: var(--shadow-light);
    transition: box-shadow 0.3s ease;
    margin-bottom: 25px;
}}
.mar-card:hover {{
    box-shadow: var(--shadow-hover);
}}

.stTextInput>div>div>input {{
    background-color: white;
    border: 1px solid rgba(21,72,114,0.25);
    border-radius: 8px;
    padding: 10px 15px;
    font-size: 15px;
    height: 44px;
}}
.stTextInput>div>div>input:focus {{
    border-color: var(--mar-accent);
    box-shadow: 0 0 0 3px rgba(93,192,220,0.3);
}}

.stButton>button[key="btn_buscar"] {{
    background-color: var(--mar-primary) !important; 
    color: white !important;
    border: 1px solid var(--mar-primary) !important;
    border-radius: 8px;
    padding: 0 20px;
    font-weight: 600;
    height: 44px; 
    transition: background-color 0.2s ease, border-color 0.2s ease;
    margin-top: 0px; 
}}

.stButton>button[key="btn_buscar"]:hover {{
    background-color: var(--mar-muted) !important;
    color: white !important;
    border: 1px solid var(--mar-muted) !important;
}}

.stButton>button[key="voz"] {{
    background-color: var(--mar-accent) !important;
    color: var(--mar-primary) !important;
    border: 1px solid var(--mar-accent) !important;
    border-radius: 8px !important;
    padding: 0 12px !important;
    font-weight: 600 !important;
    height: 44px !important;
    transition: background-color 0.2s ease, color 0.2s ease;
    margin-top: 0px; 
}}
.stButton>button[key="voz"]:hover {{
    background-color: #3aa6c1 !important;
    color: white !important;
    border: 1px solid #3aa6c1 !important;
}}

.stButton>button[key="btn_prediccion"] {{
    background-color: #f7a835 !important;
    color: white !important;
    border: 1px solid #f7a835 !important;
    border-radius: 8px !important;
    padding: 0 20px !important;
    font-weight: 600 !important;
    height: 44px !important;
    transition: background-color 0.2s ease, color 0.2s ease;
    margin-top: 0px; 
}}
.stButton>button[key="btn_prediccion"]:hover {{
    background-color: #e69524 !important;
    border: 1px solid #e69524 !important;
}}

.stButton>button[key="btn_devolver"] {{
    background-color: #f0f2f6 !important;
    color: #34495e !important;
    border: 1px solid #dcdfe6 !important;
    border-radius: 8px !important;
    padding: 0 15px !important;
    font-weight: 600 !important;
    height: 44px !important;
    transition: background-color 0.2s ease, color 0.2s ease;
    margin-top: 0px; 
}}
.stButton>button[key="btn_devolver"]:hover {{
    background-color: #e9ecef !important;
}}

.metric-card {{
    background-color: #f0f2f6;
    padding: 15px;
    border-radius: 8px;
    text-align: center;
    box-shadow: 0 2px 5px rgba(0,0,0,0.05);
}}
.metric-value {{
    font-size: 36px;
    font-weight: 700;
    color: var(--mar-primary);
    line-height: 1;
}}
.metric-label {{
    font-size: 14px;
    color: #6b7280;
    margin-top: 5px;
}}

[data-testid="stSidebar"] {{
    background-color: white;
    padding: 20px;
    box-shadow: var(--shadow-light);
    border-right: 1px solid #e0e0e0;
}}

.stAlert > div {{
    border-radius: 8px;
    padding: 12px 15px;
    font-size: 15px;
}}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# CARGA DE MODELO DE NN (MLP)
# -----------------------------
MODELO_NN = None
SCALER_NN = None
FEATURES_NN = None
MODEL_PATH = os.path.join("assets", "mlp_contratos.joblib")
SCALER_PATH = os.path.join("assets", "scaler_contratos.joblib")
FEATURES_PATH = os.path.join("assets", "mlp_features.joblib")

if NN_AVAILABLE:
    if os.path.exists(MODEL_PATH) and os.path.exists(SCALER_PATH) and os.path.exists(FEATURES_PATH):
        try:
            @st.cache(allow_output_mutation=True, suppress_st_warning=True)
            def load_mlp_artifacts():
                model = joblib.load(MODEL_PATH)
                scaler = joblib.load(SCALER_PATH)
                features = joblib.load(FEATURES_PATH)
                return model, scaler, features
            
            MODELO_NN, SCALER_NN, FEATURES_NN = load_mlp_artifacts()
        except Exception as e:
            st.sidebar.error(f"Error al cargar el MLP o artefactos: {e}")
            MODELO_NN, SCALER_NN, FEATURES_NN = None, None, None
    else:
        st.sidebar.warning(f"Faltan archivos del MLP en la carpeta assets. El predictor no estará disponible.")

# -----------------------------
# CONFIGURACIÓN DEL ARCHIVO EXCEL DESDE GITHUB
# -----------------------------
GITHUB_EXCEL_URL = "https://raw.githubusercontent.com/bautistapulgarin/MarAssistant/main/data/control_obra.xlsx"

# CORRECCIÓN: Usar @st.cache en lugar de @st.cache_data
@st.cache(allow_output_mutation=True, suppress_st_warning=True)
def load_excel_from_github():
    """Carga el archivo Excel desde GitHub"""
    try:
        response = requests.get(GITHUB_EXCEL_URL)
        response.raise_for_status()
        
        # Leer el contenido del Excel
        excel_content = io.BytesIO(response.content)
        
        # Cargar todas las hojas necesarias
        df_avance = pd.read_excel(excel_content, sheet_name="Avance")
        excel_content.seek(0)
        df_responsables = pd.read_excel(excel_content, sheet_name="Responsables")
        excel_content.seek(0)
        df_restricciones = pd.read_excel(excel_content, sheet_name="Restricciones")
        excel_content.seek(0)
        df_sostenibilidad = pd.read_excel(excel_content, sheet_name="Sostenibilidad")
        excel_content.seek(0)
        df_avance_diseno = pd.read_excel(excel_content, sheet_name="AvanceDiseño")
        excel_content.seek(0)
        df_inventario_diseno = pd.read_excel(excel_content, sheet_name="InventarioDiseño")
        
        return {
            'avance': df_avance,
            'responsables': df_responsables,
            'restricciones': df_restricciones,
            'sostenibilidad': df_sostenibilidad,
            'avance_diseno': df_avance_diseno,
            'inventario_diseno': df_inventario_diseno,
            'success': True
        }
    except Exception as e:
        st.error(f"Error al cargar el archivo Excel desde GitHub: {e}")
        return {'success': False, 'error': str(e)}

# -----------------------------
# HEADER: logo + títulos + BOTÓN DE PREDICCIÓN
# -----------------------------
logo_path = os.path.join("assets", "logoMar.png")

col_header_title, col_header_button = st.columns([7, 1.5])

with col_header_title:
    if os.path.exists(logo_path):
        try:
            logo_img = Image.open(logo_path)
            buffered = io.BytesIO()
            logo_img.save(buffered, format="PNG")
            img_b64 = base64.b64encode(buffered.getvalue()).decode()
            
            st.markdown(
                f"""
                <div style="display:flex; align-items:center; gap:25px; margin-bottom:30px; padding-top:10px;">
                    <img src="data:image/png;base64,{img_b64}" style="height:120px; width:auto;"/>
                    <div>
                        <p class="title">Sistema Integrado de Información de Proyectos</p>
                        <p class="subtitle">Asistente para el Seguimiento y Control — Constructora Marval</p>
                    </div>
                </div>
                """, unsafe_allow_html=True
            )
        except Exception:
            st.markdown(f'<p class="title">Sistema Integrado de Información de Proyectos</p>', unsafe_allow_html=True)
    else:
        st.markdown(f'<p class="title">Sistema Integrado de Información de Proyectos</p>', unsafe_allow_html=True)

# LÓGICA DEL BOTÓN DE PREDICCIÓN
def switch_to_predictor():
    st.session_state.current_view = 'predictor'
    st.session_state.prediction_result = None

def switch_to_chat():
    st.session_state.current_view = 'chat'
    st.session_state.prediction_result = None
    if 'filtro_restriccion' in st.session_state:
        del st.session_state['filtro_restriccion'] 
    if 'tipo_restriccion_preseleccionado' in st.session_state:
        del st.session_state['tipo_restriccion_preseleccionado']
    st.rerun()

with col_header_button:
    st.markdown("<div style='height:75px;'></div>", unsafe_allow_html=True)
    if MODELO_NN:
        if st.button("Pronóstico", key="btn_prediccion", type="secondary", use_container_width=True):
            switch_to_predictor()
    else:
        st.warning("MLP no disponible.")
        
# Inicializar el estado de sesión
if 'current_view' not in st.session_state:
    st.session_state.current_view = 'chat'

if 'prediction_result' not in st.session_state:
    st.session_state.prediction_result = None

# -----------------------------
# CARGA DEL ARCHIVO EXCEL DESDE GITHUB
# -----------------------------
st.sidebar.markdown(f'<p style="color:{PALETTE["primary"]}; font-size: 24px; font-weight: 700; margin-bottom: 0px;">Herramientas</p>', unsafe_allow_html=True)
st.sidebar.subheader("Fuente de Datos")

# Cargar datos desde GitHub
excel_data = load_excel_from_github()

if excel_data['success']:
    st.sidebar.success("✅ Datos cargados correctamente desde GitHub")
    
    # Asignar los DataFrames
    df_avance = excel_data['avance']
    df_responsables = excel_data['responsables']
    df_restricciones = excel_data['restricciones']
    df_sostenibilidad = excel_data['sostenibilidad']
    df_avance_diseno = excel_data['avance_diseno']
    df_inventario_diseno = excel_data['inventario_diseno']
    
else:
    st.sidebar.error(f"❌ Error al cargar datos: {excel_data.get('error', 'Error desconocido')}")
    st.stop()

# El resto de tu código permanece igual...
# [Aquí va todo el resto de tu código original: normalización, funciones de respuesta, etc.]

# Solo necesitas reemplazar la parte del cache y la carga del Excel
