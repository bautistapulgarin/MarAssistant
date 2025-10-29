import streamlit as st
from PIL import Image
import pandas as pd
import re
import unicodedata
import time
import base64
import os
import io
import random

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
    --card-padding: 16px;
    --title-size: 36px;
}}
.stApp {{
    background-color: var(--mar-bg);
    color: #1b2635;
    font-family: 'Roboto', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}}
.header-box {{
    background-color: white;
    padding: 20px;
    border-radius: var(--card-radius);
    box-shadow: 0 8px 20px rgba(21,72,114,0.08);
    display: flex;
    align-items: center;
}}
.title {{
    color: var(--mar-primary);
    font-size: var(--title-size);
    font-weight: 800;
    margin: 0;
    font-family: 'Roboto Slab', serif;
}}
.subtitle {{
    color: #34495e;
    font-size: 16px;
    margin: 4px 0 0 0;
}}
.mar-card {{
    background-color: white;
    padding: var(--card-padding);
    border-radius: var(--card-radius);
    box-shadow: 0 6px 18px rgba(21,72,114,0.06);
    margin-bottom: 20px;
}}
.stTextInput>div>div>input {{
    background-color: white;
    border: 1px solid rgba(21,72,114,0.2);
    border-radius: 8px;
    padding: 10px 12px;
    font-size: 14px;
    height: 40px;
}}
.stTextInput>div>div>input::placeholder {{
    color: rgba(0, 0, 0, 0.4);
    font-style: italic;
}}
.stButton>button {{
    background-color: var(--mar-primary);
    color: white;
    border-radius: 8px;
    padding: 0 20px;
    font-weight: 600;
    border: none;
    height: 40px;
}}
.stButton>button:hover {{
    background-color: var(--mar-muted);
}}
.stButton>button.btn-voz {{
    background-color: #5DC0DC;
    color: white;
    border-radius: 8px;
    padding: 0 12px;
    font-weight: 600;
    border: none;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
}}
.stButton>button.btn-voz:hover {{
    background-color: #3aa6c1;
}}
[data-testid="stSidebar"] {{
    background-color: white;
    padding: 20px;
    border-radius: var(--card-radius);
}}
/* Animación fantasmas */
@keyframes floatY {{
    0% {{ top: -10%; }}
    100% {{ top: 110%; }}
}}
</style>
""", unsafe_allow_html=True)

# -------------------- FANTASMAS HALLOWEEN (derecha → arriba/abajo) --------------------
st.markdown("""
<div style="position:fixed; top:-10%; right:95%; font-size:20px; opacity:0.8; animation:floatY 7s linear infinite; z-index:0;">👻</div>
<div style="position:fixed; top:-5%; right:92%; font-size:18px; opacity:0.85; animation:floatY 8s linear infinite; z-index:0;">👻</div>
<div style="position:fixed; top:-8%; right:94%; font-size:22px; opacity:0.75; animation:floatY 6.5s linear infinite; z-index:0;">👻</div>
<div style="position:fixed; top:-3%; right:91%; font-size:16px; opacity:0.9; animation:floatY 7.5s linear infinite; z-index:0;">👻</div>
<div style="position:fixed; top:-6%; right:93%; font-size:18px; opacity:0.8; animation:floatY 7.2s linear infinite; z-index:0;">👻</div>
<div style="position:fixed; top:-2%; right:90%; font-size:15px; opacity:0.85; animation:floatY 8.3s linear infinite; z-index:0;">👻</div>
<div style="position:fixed; top:-9%; right:92%; font-size:19px; opacity:0.8; animation:floatY 6.8s linear infinite; z-index:0;">👻</div>
<div style="position:fixed; top:-4%; right:94%; font-size:17px; opacity:0.88; animation:floatY 7.1s linear infinite; z-index:0;">👻</div>
<div style="position:fixed; top:-7%; right:91%; font-size:16px; opacity:0.9; animation:floatY 8.0s linear infinite; z-index:0;">👻</div>
<div style="position:fixed; top:-3%; right:95%; font-size:15px; opacity:0.85; animation:floatY 7.7s linear infinite; z-index:0;">👻</div>
""", unsafe_allow_html=True)

# -----------------------------
# HEADER: logo + títulos
# -----------------------------
logo_path = os.path.join("assets", "logoMar.png")

if os.path.exists(logo_path):
    try:
        logo_img = Image.open(logo_path)
        buffered = io.BytesIO()
        logo_img.save(buffered, format="PNG")
        img_b64 = base64.b64encode(buffered.getvalue()).decode()
        st.markdown(
            f"""
            <div style="display:flex; align-items:center; gap:20px; margin-bottom:20px;">
                <img src="data:image/png;base64,{img_b64}" style="height:110px; width:auto;"/>
                <div>
                    <p class="title">Sistema Integrado de Información de Proyectos</p>
                    <p class="subtitle"> Asistente para el Seguimiento y Control — Constructora Marval</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    except Exception:
        st.image(logo_path, width=80)
else:
    st.warning("Logo no encontrado en assets/logoMar.png")

# -----------------------------
# SIDEBAR: Uploads
# -----------------------------
st.sidebar.title("Herramientas")
st.sidebar.subheader("Cargas")
excel_file = st.sidebar.file_uploader("Sube tu archivo Excel (.xlsx)", type=["xlsx"])
img_file = st.sidebar.file_uploader("Sube imagen splash (opcional)", type=["png", "jpg", "jpeg"])
st.sidebar.markdown("---")
st.sidebar.markdown("💡 Consejo: coloca `assets/logoMar.png` junto a este archivo para mostrar el logo correctamente.")

# -----------------------------
# SPLASH (opcional)
# -----------------------------
placeholder = st.empty()
if img_file:
    try:
        img_b64 = base64.b64encode(img_file.read()).decode()
        splash_html = f"""
        <div style="
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100vh;
            background-color: white;
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 9999;">
            <div style="text-align:center; padding: 20px; border-radius: 12px;">
                <img src="data:image/png;base64,{img_b64}" 
                     style="width:160px; max-width:50vw; height:auto; display:block; margin:0 auto;">
            </div>
        </div>
        """
        placeholder.markdown(splash_html, unsafe_allow_html=True)
        time.sleep(0.5)
        placeholder.empty()
    except Exception:
        placeholder.empty()

# -----------------------------
# LECTURA DE EXCEL
# -----------------------------
if not excel_file:
    st.info("Sube el archivo Excel en la barra lateral para cargar las hojas.")
    st.stop()

try:
    excel_file.seek(0)
    df_avance = pd.read_excel(excel_file, sheet_name="Avance")
    excel_file.seek(0)
    df_responsables = pd.read_excel(excel_file, sheet_name="Responsables")
    excel_file.seek(0)
    df_restricciones = pd.read_excel(excel_file, sheet_name="Restricciones")
    excel_file.seek(0)
    df_sostenibilidad = pd.read_excel(excel_file, sheet_name="Sostenibilidad")
    excel_file.seek(0)
    df_avance_diseno = pd.read_excel(excel_file, sheet_name="AvanceDiseño")
    excel_file.seek(0)
    df_inventario_diseno = pd.read_excel(excel_file, sheet_name="InventarioDiseño")
    st.sidebar.success("✅ Hojas cargadas correctamente")
except Exception as e:
    st.sidebar.error(f"Error al leer una o varias hojas: {e}")
    st.stop()
