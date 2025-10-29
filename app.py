# app.py
import streamlit as st
from PIL import Image
import pandas as pd
import re
import unicodedata
import time
import base64
import os
import io

# Intentamos importar plotly
try:
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except Exception:
    PLOTLY_AVAILABLE = False

st.set_page_config(page_title="Mar Assistant", page_icon="🌊", layout="wide", initial_sidebar_state="expanded")

PALETTE = {"primary": "#154872", "accent": "#5DC0DC", "muted": "#437FAC", "bg": "#ffffff"}

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
.suggestion-chip {{
    display:inline-block;
    padding:6px 10px;
    margin:4px 6px 4px 0;
    border-radius:999px;
    background-color: rgba(21,72,114,0.07);
    border: 1px solid rgba(21,72,114,0.08);
    cursor: pointer;
    font-size:14px;
}}
.suggestion-chip:hover {{
    background-color: rgba(21,72,114,0.12);
}}
</style>
""", unsafe_allow_html=True)

# Optional: Halloween decorations (pure CSS/HTML, harmless)
st.markdown("""
<div style="position:fixed; top:0%; right:5%; font-size:30px; opacity:0.06; z-index:9999;">❄️</div>
<div style="position:fixed; bottom:5%; left:8%; font-size:22px; opacity:0.12; z-index:9999;">🎃</div>
""", unsafe_allow_html=True)

# HEADER
logo_path = os.path.join("assets", "logoMar.png")
if os.path.exists(logo_path):
    try:
        logo_img = Image.open(logo_path)
        buffered = io.BytesIO()
        logo_img.save(buffered, format="PNG")
        img_b64 = base64.b64encode(buffered.getvalue()).decode()
        st.markdown(f"""
            <div style="display:flex; align-items:center; gap:20px; margin-bottom:20px;">
                <img src="data:image/png;base64,{img_b64}" style="height:110px; width:auto;"/>
                <div>
                    <p class="title">Sistema Integrado de Información de Proyectos</p>
                    <p class="subtitle"> Asistente para el Seguimiento y Control — Constructora Marval</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
    except Exception:
        st.image(logo_path, width=80)
else:
    st.warning("Logo no encontrado en assets/logoMar.png")

# SIDEBAR uploads
st.sidebar.title("Herramientas")
st.sidebar.subheader("Cargas")
excel_file = st.sidebar.file_uploader("Sube tu archivo Excel (.xlsx)", type=["xlsx"])
img_file = st.sidebar.file_uploader("Sube imagen splash (opcional)", type=["png", "jpg", "jpeg"])
st.sidebar.markdown("---")
st.sidebar.markdown("💡 Consejo: coloca `assets/logoMar.png` junto a este archivo para mostrar el logo correctamente.")

# Optional splash
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

if not excel_file:
    st.info("Sube el archivo Excel en la barra lateral para cargar las hojas.")
    st.stop()

# LECTURA DE EXCEL
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

# NORMALIZACIÓN helpers
def normalizar_texto(texto):
    texto = str(texto).lower()
    texto = re.sub(r"[.,;:%\"()\/\\\\]", " ", texto)
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()

def quitar_tildes(texto):
    return ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')

# Check Proyecto column presence
for df_name, df in [("Avance", df_avance), ("Responsables", df_responsables),
                    ("Restricciones", df_restricciones), ("Sostenibilidad", df_sostenibilidad)]:
    if "Proyecto" not in df.columns:
        st.sidebar.error(f"La hoja '{df_name}' no contiene la columna 'Proyecto'.")
        st.stop()

# Añadir proyecto normalizado
for df in [df_avance, df_responsables, df_restricciones, df_sostenibilidad]:
    df["Proyecto_norm"] = df["Proyecto"].astype(str).apply(lambda x: quitar_tildes(normalizar_texto(x)))

all_projects = pd.concat([df_avance["Proyecto"].astype(str),
                          df_responsables["Proyecto"].astype(str),
                          df_restricciones["Proyecto"].astype(str),
                          df_sostenibilidad["Proyecto"].astype(str)]).dropna().unique()
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

# LISTA DE CARGOS (mantener)
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

# FUNCION DE RESPUESTA
def generar_respuesta(pregunta):
    pregunta_norm = quitar_tildes(normalizar_texto(pregunta))
    proyecto, proyecto_norm = extraer_proyecto(pregunta)

    estado_diseno_keywords = ["estado diseño", "estado diseno", "inventario diseño", "inventario diseno"]
    diseño_keywords = ["avance en diseño", "avance diseño", "diseno", "diseño"]
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
            grafico = px.bar(
                df.groupby("tipoRestriccion").size().reset_index(name="count"),
                x="tipoRestriccion", y="count", text="count",
                labels={"tipoRestriccion": "Tipo de Restricción", "count": "Cantidad"},
                color="tipoRestriccion"
            )
            grafico.update_layout(showlegend=False, xaxis_title="Tipo de Restricción", yaxis_title="Cantidad")

        return f"⚠️ Restricciones en {proyecto or 'todos'}:", df, grafico

    if any(k in pregunta_norm for k in ["sostenibilidad", "edge", "sostenible", "ambiental"]):
        df = df_sostenibilidad.copy()
        if proyecto_norm:
            df = df[df["Proyecto_norm"] == proyecto_norm]
        if df.empty:
            return f"❌ No hay registros de sostenibilidad en {proyecto or 'todos'}", None
        return f"🌱 Información de sostenibilidad en {proyecto or 'todos'}:", df

    return ("❓ No entendí la pregunta. Intenta con 'avance de obra', 'avance en diseño', "
            "'estado diseño', 'responsable', 'restricciones' o 'sostenibilidad'."), None

# ------------------------------
# Construcción automática de palabras clave
# ------------------------------
def construir_palabras_clave():
    keywords = set([
        "avance de obra", "avance diseño", "estado diseño", "inventario diseño",
        "responsable", "restricciones", "sostenibilidad", "avance", "proyecto",
        "quién", "quien", "tipo restriccion", "tipoRestriccion"
    ])
    # Añadir proyectos
    for p in all_projects:
        if pd.notna(p) and str(p).strip():
            keywords.add(str(p).strip())
    # Añadir cargos si existe la columna Cargo
    if "Cargo" in df_responsables.columns:
        for c in df_responsables["Cargo"].dropna().unique():
            keywords.add(str(c).strip())
    # Añadir tipoRestriccion si existe
    if "tipoRestriccion" in df_restricciones.columns:
        for t in df_restricciones["tipoRestriccion"].dropna().unique():
            keywords.add(str(t).strip())
    # Extraer palabras frecuentes de columnas de texto (limitar)
    text_columns = []
    for df in [df_avance, df_responsables, df_restricciones, df_sostenibilidad]:
        for col in df.columns:
            if df[col].dtype == object:
                text_columns.append((df, col))
    token_counts = {}
    for df, col in text_columns:
        for val in df[col].dropna().astype(str).head(500):
            for token in re.findall(r"\b[^\d\W]{3,}\b", normalizar_texto(quitar_tildes(val))):
                token_counts[token] = token_counts.get(token, 0) + 1
    # Añadir tokens más frecuentes
    for t, _ in sorted(token_counts.items(), key=lambda x: x[1], reverse=True)[:60]:
        keywords.add(t)
    # Normalizar y devolver lista ordenada
    cleaned = []
    for k in keywords:
        kk = " ".join(str(k).split())
        if kk:
            cleaned.append(kk)
    cleaned = sorted(set(cleaned), key=lambda x: (len(x), x))
    return cleaned

KEYWORDS = construir_palabras_clave()

# -----------------------------
# INTERFAZ: input + sugerencias sin JS (Streamlit puro)
# -----------------------------
st.markdown(f'<div class="mar-card"><strong style="color:{PALETTE["primary"]}">Consulta rápida</strong>'
            '<p style="margin:6px 0 10px 0;">Escribe tu consulta relacionada con el estado u contexto de los proyectos </p></div>',
            unsafe_allow_html=True)

# Inicializar estado
if "pregunta" not in st.session_state:
    st.session_state["pregunta"] = ""

def set_pregunta(val):
    st.session_state["pregunta"] = val

col_input, col_enviar, col_voz = st.columns([5, 1, 1])
with col_input:
    pregunta = st.text_input(label="", placeholder="Escribe tu pregunta aquí", key="pregunta")
with col_enviar:
    enviar = st.button("Enviar", use_container_width=True)
with col_voz:
    voz = st.button("🎤 Voz", key="voz", help="Activar entrada por voz", use_container_width=True)

# Mostrar sugerencias dinámicas (sin JS) - filtrado por contenido
def mostrar_sugerencias(p_text, max_items=12):
    if not p_text:
        # mostrar sugerencias populares (primeras)
        suggestions = KEYWORDS[:16]
    else:
        q = quitar_tildes(normalizar_texto(p_text))
        suggestions = [k for k in KEYWORDS if q in quitar_tildes(normalizar_texto(k))]
        if not suggestions:
            # intentar fragmentos
            parts = q.split()
            suggestions = []
            for p in parts:
                suggestions.extend([k for k in KEYWORDS if p in quitar_tildes(normalizar_texto(k))])
        # mantener orden y unicidad
        seen = set()
        new = []
        for s in suggestions:
            if s not in seen:
                seen.add(s)
                new.append(s)
        suggestions = new
    suggestions = suggestions[:max_items]
    if suggestions:
        st.markdown("<div style='margin-top:6px; margin-bottom:8px;'>", unsafe_allow_html=True)
        cols = st.columns(4)
        for idx, s in enumerate(suggestions):
            c = cols[idx % 4]
            # Cada sugerencia es un botón que completa el campo
            with c:
                if st.button(s, key=f"sugg_{idx}"):
                    set_pregunta(s)
                    # pequeño rerun para ver el cambio inmediato
                    st.experimental_rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# Mostrar sugerencias bajo el input
mostrar_sugerencias(st.session_state.get("pregunta", ""))

# Lógica de botones
if enviar and st.session_state.get("pregunta", "").strip():
    respuesta = generar_respuesta(st.session_state["pregunta"].strip())

    if isinstance(respuesta, tuple) and len(respuesta) == 3:
        texto, resultado, grafico = respuesta
    else:
        texto, resultado = respuesta
        grafico = None

    st.markdown(f"<div class='mar-card'><p style='color:{PALETTE['primary']}; font-weight:700; margin:0 0 8px 0;'>{texto}</p>",
                unsafe_allow_html=True)

    if grafico:
        st.plotly_chart(grafico, use_container_width=True)

    if isinstance(resultado, pd.DataFrame) and not resultado.empty:
        max_preview = 200
        if len(resultado) > max_preview:
            st.info(f"Mostrando primeras {max_preview} filas de {len(resultado)}.")
            df_preview = resultado.head(max_preview)
        else:
            df_preview = resultado

        # Mostrar DataFrame simple
        st.dataframe(df_preview, use_container_width=True)
    elif isinstance(resultado, str):
        st.write(resultado)

# FOOTER
st.markdown(f"<br><hr><p style='font-size:12px;color:#6b7280;'>Mar Assistant • CONSTRUCTORA MARVAL • Versión: 1.0</p>",
            unsafe_allow_html=True)
