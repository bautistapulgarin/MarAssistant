# app.py
import streamlit as st
from PIL import Image
import pandas as pd
import re
import unicodedata
import time
import base64
import os

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
    "primary": "#154872",   # profundo
    "accent": "#5DC0DC",    # cyan claro
    "muted": "#437FAC",     # azul intermedio
    "bg": "#D9DCE1"         # gris azulado suave
}

# -----------------------------
# CSS GLOBAL (UX friendly)
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
        --title-size: 26px;
    }}
    /* Background */
    .stApp {{
        background-color: var(--mar-bg);
        color: #1b2635;
    }}
    /* Header box */
    .header-box {{
        background-color: white;
        padding: 12px;
        border-radius: 10px;
        box-shadow: 0 6px 18px rgba(21,72,114,0.06);
        display: flex;
        align-items: center;
    }}
    .header-text {{
        margin-left: 14px;
    }}
    .title {{
        color: var(--mar-primary);
        font-size: var(--title-size);
        font-weight: 700;
        margin: 0;
    }}
    .subtitle {{
        color: #34495e;
        font-size: 14px;
        margin: 0;
    }}
    /* Logo ajustado a tamaño del título */
    .logo-header img {{
        height: var(--title-size);
        width: auto;
    }}
    /* Card */
    .mar-card {{
        background-color: white;
        padding: var(--card-padding);
        border-radius: var(--card-radius);
        box-shadow: 0 6px 18px rgba(21,72,114,0.06);
        margin-bottom: 16px;
    }}
    /* Inputs */
    .stTextInput>div>div>input {{
        background-color: white;
        border: 1px solid rgba(21,72,114,0.12);
        border-radius: 8px;
        padding: 10px 12px;
        font-size: 14px;
    }}
    /* Buttons */
    .stButton>button {{
        background-color: var(--mar-primary);
        color: white;
        border-radius: 8px;
        padding: 8px 16px;
        font-weight: 600;
        border: none;
    }}
    .stButton>button:hover {{
        background-color: var(--mar-muted);
    }}
    /* Sidebar */
    [data-testid="stSidebar"] {{
        background-color: white;
        padding: 16px;
        border-radius: 10px;
    }}
    </style>
""", unsafe_allow_html=True)

# -----------------------------
# HEADER: logo + titles
# -----------------------------
logo_path = os.path.join("assets", "logoMar.png")

col_logo, col_title = st.columns([0.14, 0.86], gap="small")
with col_logo:
    if os.path.exists(logo_path):
        try:
            logo_img = Image.open(logo_path)
            buffered = base64.b64encode(logo_img.tobytes()).decode()
            st.markdown(
                f'<div class="logo-header"><img src="data:image/png;base64,{buffered}" /></div>',
                unsafe_allow_html=True
            )
        except Exception:
            st.image(logo_path, width=26)  # fallback simple
    else:
        st.warning("Logo no encontrado en assets/logoMar.png")

with col_title:
    st.markdown(
        f"""
        <div class="header-box">
            <div class="header-text">
                <p class="title">Sistema Integrado de Control de Proyectos</p>
                <p class="subtitle">Plataforma de consolidación y consulta — Constructora Marval</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

st.write("")  # spacing

# -----------------------------
# SIDEBAR: Uploads y ayuda
# -----------------------------
st.sidebar.title("Herramientas")
st.sidebar.subheader("Cargas")
excel_file = st.sidebar.file_uploader("Sube tu archivo Excel (.xlsx)", type=["xlsx"])
img_file = st.sidebar.file_uploader("Sube imagen splash (opcional)", type=["png", "jpg", "jpeg"])

st.sidebar.markdown("---")
st.sidebar.markdown("Consejo: coloca `assets/logoMar.png` junto a este archivo para mostrar el logo correctamente.")

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

# -----------------------------
# NORMALIZACIÓN
# -----------------------------
def normalizar_texto(texto):
    texto = str(texto).lower()
    texto = re.sub(r"[.,;:%]", "", texto)
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()

def quitar_tildes(texto):
    return ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')

for df_name, df in [("Avance", df_avance), ("Responsables", df_responsables),
                    ("Restricciones", df_restricciones), ("Sostenibilidad", df_sostenibilidad)]:
    if "Proyecto" not in df.columns:
        st.sidebar.error(f"La hoja '{df_name}' no contiene la columna 'Proyecto'.")
        st.stop()

for df in [df_avance, df_responsables, df_restricciones, df_sostenibilidad]:
    df["Proyecto_norm"] = df["Proyecto"].astype(str).apply(lambda x: quitar_tildes(normalizar_texto(x)))

all_projects = pd.concat([
    df_avance["Proyecto"].astype(str),
    df_responsables["Proyecto"].astype(str),
    df_restricciones["Proyecto"].astype(str),
    df_sostenibilidad["Proyecto"].astype(str)
]).dropna().unique()

projects_map = {quitar_tildes(normalizar_texto(p)): p for p in all_projects}

def extraer_proyecto(texto):
    texto_norm = quitar_tildes(normalizar_texto(texto))
    for norm in sorted(projects_map.keys(), key=len, reverse=True):
        pattern = rf'(^|\W){re.escape(norm)}($|\W)'
        if re.search(pattern, texto_norm, flags=re.UNICODE):
            return projects_map[norm], norm
    for norm in sorted(projects_map.keys(), key=len, reverse=True):
        if norm in texto_norm:
            return projects_map[norm], norm
    return None, None

# -----------------------------
# LISTA DE CARGOS
# -----------------------------
CARGOS_VALIDOS = [
    "Analista de compras", "Analista de Programación", "Arquitecto",
    "Contralor de proyectos", "Coordinador Administrativo de Proyectos", "Coordinador BIM",
    "Coordinador Eléctrico", "Coordinador Logístico", "Coordinador SIG", "Coordinadora de pilotaje",
    "Director de compras", "Director de obra", "Director Nacional Lean y BIM", "Director Técnico",
    "Diseñador estructural", "Diseñador externo", "Equipo MARVAL", "Gerente de proyectos",
    "Ingeniera Eléctrica", "Ingeniero Ambiental", "Ingeniero de Contratación", "Ingeniero electromecánico",
    "Ingeniero FCA", "Ingeniero FCA #2", "Ingeniero Lean", "Ingeniero Lean 3", "Profesional SYST",
    "Programador de obra", "Programador de obra #2", "Practicante de Interventoría #1",
    "Practicante Lean", "Residente", "Residente #2", "Residente Administrativo de Equipos",
    "Residente auxiliar", "Residente Auxiliar #2", "Residente Auxiliar #3", "Residente Auxiliar #4",
    "Residente de acabados", "Residente de acabados #2", "Residente de control e interventoría",
    "Residente de Equipos", "Residente de supervisión técnica", "Residente logístico", "Técnico de almacén"
]
CARGOS_VALIDOS_NORM = {quitar_tildes(normalizar_texto(c)): c for c in CARGOS_VALIDOS}

# -----------------------------
# FUNCION DE RESPUESTA
# -----------------------------
def generar_respuesta(pregunta):
    pregunta_norm = quitar_tildes(normalizar_texto(pregunta))
    proyecto, proyecto_norm = extraer_proyecto(pregunta)

    estado_diseno_keywords = ["estado diseño", "estado diseno", "inventario diseño", "inventario diseno"]
    diseño_keywords = ["avance en diseno", "avance en diseño", "avance diseno", "avance diseño",
                       "avance de diseno", "avance de diseño", "diseno", "diseño"]
    obra_keywords = ["avance de obra", "avance obra", "avance en obra"]

    if any(k in pregunta_norm for k in estado_diseno_keywords):
        if df_inventario_diseno.empty:
            return "❌ No hay registros en la hoja InventarioDiseño.", None
        return "📐 Estado de Diseño (InventarioDiseño):", df_inventario_diseno

    if any(k in pregunta_norm for k in diseño_keywords):
        if ("avance" in pregunta_norm) or (pregunta_norm.strip() in ["diseno", "diseño"]):
            if df_avance_diseno.empty:
                return "❌ No hay registros en la hoja AvanceDiseño.", None
            return "📐 Avance de Diseño (tabla completa):", df_avance_diseno

    if any(k in pregunta_norm for k in obra_keywords):
        df = df_avance.copy()
        if proyecto_norm:
            df = df[df["Proyecto_norm"] == proyecto_norm]
        if df.empty:
            return f"❌ No hay registros de avance en {proyecto or 'todos'}", None
        return f"📊 Avance de obra en {proyecto or 'todos'}:", df

    if "avance" in pregunta_norm:
        df = df_avance.copy()
        if proyecto_norm:
            df = df[df["Proyecto_norm"] == proyecto_norm]
        if df.empty:
            return f"❌ No hay registros de avance en {proyecto or 'todos'}", None
        return f"📊 Avances en {proyecto or 'todos'}:", df

    if "responsable" in pregunta_norm or "quien" in pregunta_norm or "quién" in pregunta_norm:
        df = df_responsables.copy()
        if proyecto_norm:
            df = df[df["Proyecto_norm"] == proyecto_norm]
        cargo_encontrado = None
        for cargo_norm, cargo_real in CARGOS_VALIDOS_NORM.items():
            if cargo_norm in pregunta_norm:
                cargo_encontrado = cargo_real
                break
        if cargo_encontrado:
            df = df[df["Cargo"].astype(str).str.lower().str.contains(cargo_encontrado.lower(), na=False)]
            if df.empty:
                return f"❌ No encontré responsables con cargo '{cargo_encontrado}' en {proyecto or 'todos'}", None
            return f"👷 Responsables con cargo **{cargo_encontrado}** en {proyecto or 'todos'}:", df
        if df.empty:
            return f"❌ No hay responsables registrados en {proyecto or 'todos'}", None
        return f"👷 Responsables en {proyecto or 'todos'}:", df

    if "restriccion" in pregunta_norm or "restricción" in pregunta_norm or "problema" in pregunta_norm:
        df = df_restricciones.copy()
        if proyecto_norm:
            df = df[df["Proyecto_norm"] == proyecto_norm]
        if df.empty:
            return f"❌ No hay restricciones registradas en {proyecto or 'todos'}", None
        return f"⚠️ Restricciones en {proyecto or 'todos'}:", df

    if any(k in pregunta_norm for k in ["sostenibilidad", "edge", "sostenible", "ambiental"]):
        df = df_sostenibilidad.copy()
        if proyecto_norm:
            df = df[df["Proyecto_norm"] == proyecto_norm]
        if df.empty:
            return f"❌ No hay registros de sostenibilidad en {proyecto or 'todos'}", None
        return f"🌱 Información de sostenibilidad en {proyecto or 'todos'}:", df

    return ("❓ No entendí la pregunta. Intenta con 'avance de obra', 'avance en diseño', "
            "'estado diseño', 'responsable', 'restricciones' o 'sostenibilidad'."), None

# -----------------------------
# INTERFAZ: entrada y despliegue
# -----------------------------
st.markdown('<div class="mar-card"><strong>Consulta rápida</strong><p style="margin:6px 0 0 0;">Escribe tu consulta en lenguaje natural (ej. "avance de obra en Proyecto X" o "¿quién es el responsable?")</p></div>', unsafe_allow_html=True)

pregunta = st.text_input("Escribe tu pregunta aquí:")

col_btn_1, col_btn_2 = st.columns([0.3, 0.7])
with col_btn_1:
    enviar = st.button("Enviar")
with col_btn_2:
    mostrar_raw = st.checkbox("Mostrar tabla completa (raw)", value=False)

if enviar and pregunta:
    texto, resultado = generar_respuesta(pregunta)
    st.markdown(f"<div class='mar-card'><p style='color:{PALETTE['primary']}; font-weight:700; margin:0 0 8px 0;'>{texto}</p></div>", unsafe_allow_html=True)

    if isinstance(resultado, pd.DataFrame) and not resultado.empty:
        if mostrar_raw:
            st.dataframe(resultado, use_container_width=True)
        else:
            max_preview = 200
            if len(resultado) > max_preview:
                st.info(f"Mostrando primeras {max_preview} filas de {len(resultado)}. Usa 'Mostrar tabla completa (raw)' para ver todo.")
                st.dataframe(resultado.head(max_preview), use_container_width=True)
            else:
                st.dataframe(resultado, use_container_width=True)

# -----------------------------
# FOOTER
# -----------------------------
st.markdown("<br><hr><p style='font-size:12px;color:#6b7280;'>Mar Assistant • UI organizada según lineamientos UX & BI • Versión: 1.0</p>", unsafe_allow_html=True)
