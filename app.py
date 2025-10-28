# streamlit run app.py

import streamlit as st
import pandas as pd
import re
import unicodedata
import matplotlib.pyplot as plt
import time
import base64

# -----------------------------
# Configuración general
# -----------------------------
st.set_page_config(
    page_title="Mar Assistant",
    layout="wide",
    page_icon="🌊",
    initial_sidebar_state="expanded"
)

# -----------------------------
# Título estilizado
# -----------------------------
st.markdown("""
    <h1 style="color:#1E90FF; font-size:50px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">
        Hola, soy Mar 🌊
    </h1>
    <h3 style="color:#1B1F3B; font-size:22px;">
        Asistente para el seguimiento y control de los proyectos de la Constructora Marval
    </h3>
""", unsafe_allow_html=True)

# -----------------------------
# Subida de archivos
# -----------------------------
st.sidebar.subheader("Sube los archivos necesarios")
excel_file = st.sidebar.file_uploader("Sube tu archivo Excel", type=["xlsx"])
img_file = st.sidebar.file_uploader("Sube la imagen de carga", type=["png", "jpg", "jpeg"])

# -----------------------------
# Splash fullscreen
# -----------------------------
placeholder = st.empty()
if img_file:
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
                 style="width:150px; max-width:40vw; height:auto; display:block; margin:0 auto;">
        </div>
    </div>
    """
    placeholder.markdown(splash_html, unsafe_allow_html=True)
    time.sleep(0.5)
    placeholder.empty()
else:
    st.info("Sube la imagen de carga para mostrar splash screen")

# -----------------------------
# Lectura de Excel
# -----------------------------
if excel_file:
    try:
        df_avance = pd.read_excel(excel_file, sheet_name="Avance")
        excel_file.seek(0)
        df_responsables = pd.read_excel(excel_file, sheet_name="Responsables")
        excel_file.seek(0)
        df_restricciones = pd.read_excel(excel_file, sheet_name="Restricciones")
        st.sidebar.success("✅ Hojas cargadas correctamente")
    except Exception as e:
        st.sidebar.error(f"Error al leer hojas: {e}")
        st.stop()
else:
    st.info("Sube el archivo Excel para continuar")
    st.stop()

# -----------------------------
# Normalización de texto
# -----------------------------
def normalizar_texto(texto):
    texto = str(texto).lower()
    texto = re.sub(r"[.,;:%]", "", texto)
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()

def quitar_tildes(texto):
    return ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')

for df in [df_avance, df_responsables, df_restricciones]:
    df["Proyecto_norm"] = df["Proyecto"].astype(str).apply(lambda x: quitar_tildes(normalizar_texto(x)))

all_projects = pd.concat([
    df_avance["Proyecto"].astype(str),
    df_responsables["Proyecto"].astype(str),
    df_restricciones["Proyecto"].astype(str)
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
# Cargos válidos
# -----------------------------
CARGOS_VALIDOS = [
    "Analista de compras", "Analista de Compras y Suministros", "Analista de Programación", "Arquitecto",
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
# Función de respuesta
# -----------------------------
def generar_respuesta(pregunta):
    pregunta_norm = quitar_tildes(normalizar_texto(pregunta))
    proyecto, proyecto_norm = extraer_proyecto(pregunta)

    # AVANCE
    if "avance" in pregunta_norm:
        df = df_avance.copy()
        if proyecto_norm:
            df = df[df["Proyecto_norm"] == proyecto_norm]
        if df.empty:
            return f"❌ No hay registros de avance en {proyecto or 'todos'}", None
        return f"📊 Avances en {proyecto or 'todos'}:", df

    # RESPONSABLES
    elif "responsable" in pregunta_norm or "quien" in pregunta_norm or "quién" in pregunta_norm:
        df = df_responsables.copy()
        if proyecto_norm:
            df = df[df["Proyecto_norm"] == proyecto_norm]
        cargo_encontrado = None
        for cargo_norm, cargo_real in CARGOS_VALIDOS_NORM.items():
            if cargo_norm in pregunta_norm:
                cargo_encontrado = cargo_real
                break
        if cargo_encontrado:
            df = df[df["Cargo"].str.lower().str.contains(cargo_encontrado.lower(), na=False)]
            if df.empty:
                return f"❌ No encontré responsables con cargo '{cargo_encontrado}' en {proyecto or 'todos'}", None
            return f"👷 Responsables con cargo **{cargo_encontrado}** en {proyecto or 'todos'}:", df
        if df.empty:
            return f"❌ No hay responsables registrados en {proyecto or 'todos'}", None
        return f"👷 Responsables en {proyecto or 'todos'}:", df

    # RESTRICCIONES
    elif "restriccion" in pregunta_norm or "restricción" in pregunta_norm or "problema" in pregunta_norm:
        df = df_restricciones.copy()
        if proyecto_norm:
            df = df[df["Proyecto_norm"] == proyecto_norm]
        if df.empty:
            return f"❌ No hay restricciones registradas en {proyecto or 'todos'}", None
        return f"⚠️ Restricciones en {proyecto or 'todos'}:", df

    # INFORMACION GENERAL
    elif "informacion general" in pregunta_norm or "general de" in pregunta_norm:
        if not proyecto_norm:
            return "❌ No detecté el proyecto. Por favor indica el nombre del proyecto.", None
        df_a = df_avance[df_avance["Proyecto_norm"] == proyecto_norm]
        df_r = df_responsables[df_responsables["Proyecto_norm"] == proyecto_norm]
        df_res = df_restricciones[df_restricciones["Proyecto_norm"] == proyecto_norm]
        return f"📑 Información general del proyecto **{proyecto}**:", {"Avance": df_a, "Responsables": df_r, "Restricciones": df_res}

    else:
        return "❓ No entendí la pregunta. Intenta con 'avance', 'responsable', 'restricciones' o 'información general'.", None

# -----------------------------
# Entrada de usuario
# -----------------------------
st.subheader("💬 Haz tu consulta por teclado")
pregunta = st.text_input("Escribe tu pregunta aquí:")

# -----------------------------
# Procesar pregunta y mostrar resultados con filtros
# -----------------------------
if st.button("Enviar") and pregunta:
    texto, resultado = generar_respuesta(pregunta)
    
    st.markdown(f"<p style='color:#333333'>{texto}</p>", unsafe_allow_html=True)

    if isinstance(resultado, pd.DataFrame):
        if "tabla_base" not in st.session_state:
            st.session_state["tabla_base"] = resultado.copy()
        df_tabla = st.session_state["tabla_base"].copy()

        # Filtros como encabezado
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        sucursal_sel = col1.selectbox("Sucursal", ["Todas"] + sorted(df_tabla["Sucursal"].dropna().unique()))
        cluster_sel = col2.selectbox("Cluster", ["Todos"] + sorted(df_tabla["Cluster"].dropna().unique()))
        proyecto_sel = col3.selectbox("Proyecto", ["Todos"] + sorted(df_tabla["Proyecto"].dropna().unique()))
        cargo_sel = col4.selectbox("Cargo", ["Todos"] + sorted(df_tabla["Cargo"].dropna().unique()))
        estado_sel = col5.selectbox("Estado", ["Todos"] + sorted(df_tabla["Estado"].dropna().unique()))
        gerente_sel = col6.selectbox("Gerente de proyectos", ["Todos"] + sorted(df_tabla[df_tabla["Cargo"]=="Gerente de proyectos"]["Responsable"].dropna().unique()))

        # Aplicar filtros progresivos
        if sucursal_sel != "Todas":
            df_tabla = df_tabla[df_tabla["Sucursal"] == sucursal_sel]
        if cluster_sel != "Todos":
            df_tabla = df_tabla[df_tabla["Cluster"] == cluster_sel]
        if proyecto_sel != "Todos":
            df_tabla = df_tabla[df_tabla["Proyecto"] == proyecto_sel]
        if cargo_sel != "Todos":
            df_tabla = df_tabla[df_tabla["Cargo"] == cargo_sel]
        if estado_sel != "Todos":
            df_tabla = df_tabla[df_tabla["Estado"] == estado_sel]
        if gerente_sel != "Todos":
            df_tabla = df_tabla[df_tabla["Responsable"] == gerente_sel]

        if st.button("Restablecer filtros"):
            df_tabla = st.session_state["tabla_base"].copy()

        st.dataframe(df_tabla.style.set_properties(**{
            'background-color': 'white',
            'color': '#333333'
        }), use_container_width=True)

    elif isinstance(resultado, dict):
        for nombre, df_out in resultado.items():
            if not df_out.empty:
                st.subheader(nombre)
                st.dataframe(df_out.style.set_properties(**{
                    'background-color': 'white',
                    'color': '#333333'
                }), use_container_width=True)
