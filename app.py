import streamlit as st
from PIL import Image
import pandas as pd
import re
import unicodedata
import time
import base64
import os
import io
try:
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
st.set_page_config(page_title="Mar Assistant", page_icon="🌊", layout="wide", initial_sidebar_state="expanded")
PALETTE = {"primary": "#154872","accent": "#5DC0DC","muted": "#437FAC","bg": "#ffffff"}
st.markdown(f"""
<style>
:root {{ --mar-primary: {PALETTE['primary']}; --mar-accent: {PALETTE['accent']}; --mar-muted: {PALETTE['muted']}; --mar-bg: {PALETTE['bg']}; --card-radius: 12px; --card-padding: 16px; --title-size: 36px; }}
.stApp {{ background-color: var(--mar-bg); color: #1b2635; font-family: 'Roboto', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}
.header-box {{ background-color: white; padding: 20px; border-radius: var(--card-radius); box-shadow: 0 8px 20px rgba(21,72,114,0.08); display: flex; align-items: center; }}
.title {{ color: var(--mar-primary); font-size: var(--title-size); font-weight: 800; margin: 0; font-family: 'Roboto Slab', serif; }}
.subtitle {{ color: #34495e; font-size: 16px; margin: 4px 0 0 0; }}
.mar-card {{ background-color: white; padding: var(--card-padding); border-radius: var(--card-radius); box-shadow: 0 6px 18px rgba(21,72,114,0.06); margin-bottom: 20px; }}
.stTextInput>div>div>input {{ background-color: white; border: 1px solid rgba(21,72,114,0.2); border-radius: 8px; padding: 10px 12px; font-size: 14px; height: 40px; }}
.stTextInput>div>div>input::placeholder {{ color: rgba(0, 0, 0, 0.4); font-style: italic; }}
.stButton>button {{ background-color: var(--mar-primary); color: white; border-radius: 8px; padding: 0 20px; font-weight: 600; border: none; height: 40px; }}
.stButton>button:hover {{ background-color: var(--mar-muted); }}
.stButton>button.btn-voz {{ background-color: #5DC0DC; color: white; border-radius: 8px; padding: 0 12px; font-weight: 600; border: none; height: 40px; display: flex; align-items: center; justify-content: center; gap: 6px; }}
.stButton>button.btn-voz:hover {{ background-color: #3aa6c1; }}
[data-testid="stSidebar"] {{ background-color: white; padding: 20px; border-radius: var(--card-radius); }}
.ghost { position: fixed; width: 120px; height: auto; z-index: 9999; pointer-events: none; filter: drop-shadow(0 8px 18px rgba(0,0,0,0.12)); opacity: 0.95; }
.ghost svg { width:100%; height:auto; display:block; }
.ghost-1 { top: 10vh; left: -160px; animation: moveGhost1 10s linear infinite; transform-origin: center; }
.ghost-2 { top: 30vh; left: -200px; animation: moveGhost2 14s linear infinite; transform-origin: center; }
.ghost-3 { top: 50vh; left: -120px; animation: moveGhost3 12s linear infinite; transform-origin: center; }
@keyframes moveGhost1 { 0% { left: -180px; transform: translateY(0) scale(0.9); } 50% { left: calc(100% - 100px); transform: translateY(-14px) scale(1.05); } 100% { left: -180px; transform: translateY(0) scale(0.9); } }
@keyframes moveGhost2 { 0% { left: -220px; transform: translateY(0) scale(1.0); } 50% { left: calc(100% - 160px); transform: translateY(-22px) scale(1.15); } 100% { left: -220px; transform: translateY(0) scale(1.0); } }
@keyframes moveGhost3 { 0% { left: -140px; transform: translateY(0) scale(0.85); } 50% { left: calc(100% - 80px); transform: translateY(-10px) scale(1.0); } 100% { left: -140px; transform: translateY(0) scale(0.85); } }
.ghost-eyes { transition: transform 0.2s ease; transform-origin: center; }
</style>
""", unsafe_allow_html=True)
logo_path = os.path.join("assets", "logoMar.png")
if os.path.exists(logo_path):
    try:
        logo_img = Image.open(logo_path)
        buffered = io.BytesIO()
        logo_img.save(buffered, format="PNG")
        img_b64 = base64.b64encode(buffered.getvalue()).decode()
        st.markdown(f"""<div style="display:flex; align-items:center; gap:20px; margin-bottom:20px;"><img src="data:image/png;base64,{img_b64}" style="height:110px; width:auto;"/><div><p class="title">Sistema Integrado de Información de Proyectos</p><p class="subtitle"> Asistente para el Seguimiento y Control — Constructora Marval</p></div></div>""", unsafe_allow_html=True)
    except Exception:
        st.image(logo_path, width=80)
else:
    st.warning("Logo no encontrado en assets/logoMar.png")
st.markdown("""
<div class="ghost ghost-1">
<svg viewBox="0 0 128 128" xmlns="http://www.w3.org/2000/svg">
<g>
<path d="M64 6c-20 0-36 16-36 36v38c0 2 1 4 3 5 6 3 6 6 11 6s6-3 11-3 6 3 11 3 6-3 11-3 11 3 17 3c4 0 5-2 8-4 2-2 3-4 3-6V42C100 22 84 6 64 6z" fill="#ffffff" stroke="#f7f7f9" stroke-width="2"/>
<circle cx="48" cy="48" r="6" fill="#111827"/>
<circle cx="80" cy="48" r="6" fill="#111827"/>
</g>
</svg>
</div>
<div class="ghost ghost-2">
<svg viewBox="0 0 128 128" xmlns="http://www.w3.org/2000/svg">
<g>
<path d="M64 4C42 4 24 22 24 44v36c0 3 1 5 4 6 7 4 7 7 13 7s7-4 13-4 7 4 13 4 7-4 13-4 7 4 13 4c5 0 6-2 9-5 3-3 4-6 4-9V44C104 22 86 4 64 4z" fill="#fff2f8" stroke="#ffe6f2" stroke-width="2"/>
<circle cx="46" cy="48" r="7" fill="#0b1220"/>
<circle cx="82" cy="48" r="7" fill="#0b1220"/>
</g>
</svg>
</div>
<div class="ghost ghost-3">
<svg viewBox="0 0 128 128" xmlns="http://www.w3.org/2000/svg">
<g>
<path d="M64 8c-18 0-32 14-32 32v34c0 2 0 4 2 5 5 3 5 6 10 6s6-3 10-3 6 3 10 3 6-3 10-3 6 3 10 3c4 0 5-2 7-4 2-2 3-4 3-6V40C96 22 82 8 64 8z" fill="#fffef6" stroke="#fff6d9" stroke-width="2"/>
<circle cx="50" cy="48" r="5" fill="#071028"/>
<circle cx="78" cy="48" r="5" fill="#071028"/>
</g>
</svg>
</div>
""", unsafe_allow_html=True)
st.sidebar.title("Herramientas")
st.sidebar.subheader("Cargas")
excel_file = st.sidebar.file_uploader("Sube tu archivo Excel (.xlsx)", type=["xlsx"])
img_file = st.sidebar.file_uploader("Sube imagen splash (opcional)", type=["png", "jpg", "jpeg"])
st.sidebar.markdown("---")
st.sidebar.markdown("💡 Consejo: coloca `assets/logoMar.png` junto a este archivo para mostrar el logo correctamente.")
placeholder = st.empty()
if img_file:
    try:
        img_b64 = base64.b64encode(img_file.read()).decode()
        splash_html = f"""<div style="position: fixed;top: 0;left: 0;width: 100%;height: 100vh;background-color: white;display: flex;justify-content: center;align-items: center;z-index: 9999;"><div style="text-align:center; padding: 20px; border-radius: 12px;"><img src="data:image/png;base64,{img_b64}" style="width:160px; max-width:50vw; height:auto; display:block; margin:0 auto;"></div></div>"""
        placeholder.markdown(splash_html, unsafe_allow_html=True)
        time.sleep(0.5)
        placeholder.empty()
    except Exception:
        placeholder.empty()
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
def normalizar_texto(texto):
    texto = str(texto).lower()
    texto = re.sub(r"[.,;:%]", "", texto)
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()
def quitar_tildes(texto):
    return ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
for df_name, df in [("Avance", df_avance), ("Responsables", df_responsables), ("Restricciones", df_restricciones), ("Sostenibilidad", df_sostenibilidad)]:
    if "Proyecto" not in df.columns:
        st.sidebar.error(f"La hoja '{df_name}' no contiene la columna 'Proyecto'.")
        st.stop()
for df in [df_avance, df_responsables, df_restricciones, df_sostenibilidad]:
    df["Proyecto_norm"] = df["Proyecto"].astype(str).apply(lambda x: quitar_tildes(normalizar_texto(x)))
all_projects = pd.concat([ df_avance["Proyecto"].astype(str), df_responsables["Proyecto"].astype(str), df_restricciones["Proyecto"].astype(str), df_sostenibilidad["Proyecto"].astype(str) ]).dropna().unique()
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
CARGOS_VALIDOS = ["Analista de compras", "Analista de Programación", "Arquitecto", "Contralor de proyectos", "Coordinador Administrativo de Proyectos", "Coordinador BIM", "Coordinador Eléctrico", "Coordinador Logístico", "Coordinador SIG", "Coordinadora de pilotaje", "Director de compras", "Director de obra", "Director Nacional Lean y BIM", "Director Técnico", "Diseñador estructural", "Diseñador externo", "Equipo MARVAL", "Gerente de proyectos", "Ingeniera Eléctrica", "Ingeniero Ambiental", "Ingeniero de Contratación", "Ingeniero electromecánico", "Ingeniero FCA", "Ingeniero FCA #2", "Ingeniero Lean", "Ingeniero Lean 3", "Profesional SYST", "Programador de obra", "Programador de obra #2", "Practicante de Interventoría #1", "Practicante Lean", "Residente", "Residente #2", "Residente Administrativo de Equipos", "Residente auxiliar", "Residente Auxiliar #2", "Residente Auxiliar #3", "Residente Auxiliar #4", "Residente de acabados", "Residente de acabados #2", "Residente de control e interventoría", "Residente de Equipos", "Residente de supervisión técnica", "Residente logístico", "Técnico de almacén"]
CARGOS_VALIDOS_NORM = {quitar_tildes(normalizar_texto(c)): c for c in CARGOS_VALIDOS}
def generar_respuesta(pregunta):
    pregunta_norm = quitar_tildes(normalizar_texto(pregunta))
    proyecto, proyecto_norm = extraer_proyecto(pregunta)
    estado_diseno_keywords = ["estado diseño", "estado diseno", "inventario diseño", "inventario diseno"]
    diseño_keywords = ["avance en diseno", "avance en diseño", "avance diseno", "avance diseño", "avance de diseno", "avance de diseño", "diseno", "diseño"]
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
        grafico = None
        if PLOTLY_AVAILABLE and "tipoRestriccion" in df.columns:
            grafico = px.bar(df.groupby("tipoRestriccion").size().reset_index(name="count"), x="tipoRestriccion", y="count", text="count", labels={"tipoRestriccion": "Tipo de Restricción", "count": "Cantidad"}, color="tipoRestriccion", color_discrete_sequence=px.colors.qualitative.Pastel)
            grafico.update_layout(showlegend=False, xaxis_title="Tipo de Restricción", yaxis_title="Cantidad")
        return f"⚠️ Restricciones en {proyecto or 'todos'}:", df, grafico
    if any(k in pregunta_norm for k in ["sostenibilidad", "edge", "sostenible", "ambiental"]):
        df = df_sostenibilidad.copy()
        if proyecto_norm:
            df = df[df["Proyecto_norm"] == proyecto_norm]
        if df.empty:
            return f"❌ No hay registros de sostenibilidad en {proyecto or 'todos'}", None
        return f"🌱 Información de sostenibilidad en {proyecto or 'todos'}:", df
    return ("❓ No entendí la pregunta. Intenta con 'avance de obra', 'avance en diseño', 'estado diseño', 'responsable', 'restricciones' o 'sostenibilidad'."), None
st.markdown(f'<div class="mar-card"><strong style="color:{PALETTE["primary"]}">Consulta rápida</strong><p style="margin:6px 0 10px 0;">Escribe tu consulta relacionada con el estado u contexto de los proyectos </p></div>', unsafe_allow_html=True)
col_input, col_enviar, col_voz = st.columns([5, 1, 1])
with col_input:
    pregunta = st.text_input(label="", placeholder="Escribe tu pregunta aquí")
with col_enviar:
    enviar = st.button("Enviar", use_container_width=True)
with col_voz:
    voz = st.button("🎤 Voz", key="voz", help="Activar entrada por voz", use_container_width=True)
if enviar and pregunta:
    respuesta = generar_respuesta(pregunta)
    if len(respuesta) == 3:
        texto, resultado, grafico = respuesta
    else:
        texto, resultado = respuesta
        grafico = None
    st.markdown(f"<div class='mar-card'><p style='color:{PALETTE['primary']}; font-weight:700; margin:0 0 8px 0;'>{texto}</p>", unsafe_allow_html=True)
    if grafico:
        st.plotly_chart(grafico, use_container_width=True)
    if isinstance(resultado, pd.DataFrame) and not resultado.empty:
        max_preview = 200
        if len(resultado) > max_preview:
            st.info(f"Mostrando primeras {max_preview} filas de {len(resultado)}.")
            df_preview = resultado.head(max_preview)
        else:
            df_preview = resultado
        styled_df = df_preview.style.set_table_styles([ {'selector': 'tr:nth-child(even)', 'props': [('background-color', '#f4f6f8')]}, {'selector': 'th', 'props': [('background-color', PALETTE['accent']), ('color', 'white'), ('font-weight', 'bold')]} ])
        st.dataframe(styled_df, use_container_width=True)
st.markdown(f"<br><hr><p style='font-size:12px;color:#6b7280;'>Mar Assistant • CONSTRUCTORA MARVAL • Versión: 1.0</p>", unsafe_allow_html=True)
