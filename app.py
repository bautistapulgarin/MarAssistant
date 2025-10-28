# streamlit run app.py

import streamlit as st
import pandas as pd
import re
import unicodedata
import time
import base64

# -----------------------------
# Configuración general
# -----------------------------
st.set_page_config(page_title="Mar Assistant", layout="wide", page_icon="🌊", initial_sidebar_state="expanded")

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
        excel_file.seek(0)
        df_avance = pd.read_excel(excel_file, sheet_name="Avance")
        excel_file.seek(0)
        df_responsables = pd.read_excel(excel_file, sheet_name="Responsables")
        excel_file.seek(0)
        df_restricciones = pd.read_excel(excel_file, sheet_name="Restricciones")
        excel_file.seek(0)
        df_sostenibilidad = pd.read_excel(excel_file, sheet_name="Sostenibilidad")
        excel_file.seek(0)
        df_avance_diseno = pd.read_excel(excel_file, sheet_name="AvanceDiseño")  # SIN columna Proyecto
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

# Asegurarse de que la columna 'Proyecto' exista solo en las hojas que la tienen
for df_name, df in [("Avance", df_avance), ("Responsables", df_responsables),
                    ("Restricciones", df_restricciones), ("Sostenibilidad", df_sostenibilidad)]:
    if "Proyecto" not in df.columns:
        st.sidebar.error(f"La hoja '{df_name}' no contiene la columna 'Proyecto'.")
        st.stop()

# Normalizar la columna 'Proyecto' solo en hojas que la contienen
for df in [df_avance, df_responsables, df_restricciones, df_sostenibilidad]:
    df["Proyecto_norm"] = df["Proyecto"].astype(str).apply(lambda x: quitar_tildes(normalizar_texto(x)))

# Construir el mapa de proyectos
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
# Función de respuesta
# -----------------------------
def generar_respuesta(pregunta):
    pregunta_norm = quitar_tildes(normalizar_texto(pregunta))
    proyecto, proyecto_norm = extraer_proyecto(pregunta)

    # AVANCE
    if "avance" in pregunta_norm and "diseno" not in pregunta_norm and "diseño" not in pregunta_norm:
        df = df_avance.copy()
        if proyecto_norm:
            df = df[df["Proyecto_norm"] == proyecto_norm]
        if df.empty:
            return f"❌ No hay registros de avance en {proyecto or 'todos'}", None
        return f"📊 Avances en {proyecto or 'todos'}:", df

    # DISEÑO (Muestra tabla completa sin filtro)
    elif "diseno" in pregunta_norm or "diseño" in pregunta_norm:
        if df_avance_diseno.empty:
            return "❌ No hay registros en la hoja AvanceDiseño.", None
        return "📐 Avance de Diseño (tabla completa):", df_avance_diseno

    # RESPONSABLES
    elif "responsable" in pregunta_norm or "quien" in pregunta_norm or "quién" in pregunta_norm:
        df = df_responsables.copy()
        if proyecto_norm:
            df = df[df["Proyecto_norm"] == proyecto_norm]
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

    # SOSTENIBILIDAD
    elif any(k in pregunta_norm for k in ["sostenibilidad", "edge", "sostenible", "ambiental"]):
        df = df_sostenibilidad.copy()
        if proyecto_norm:
            df = df[df["Proyecto_norm"] == proyecto_norm]
        if df.empty:
            return f"❌ No hay registros de sostenibilidad en {proyecto or 'todos'}", None
        return f"🌱 Información de sostenibilidad en {proyecto or 'todos'}:", df

    else:
        return "❓ No entendí la pregunta. Intenta con 'avance', 'diseño', 'responsable', 'restricciones' o 'sostenibilidad'.", None

# -----------------------------
# Entrada de usuario
# -----------------------------
st.subheader("📝 Escribe tu consulta")
pregunta = st.text_input("Escribe tu pregunta aquí:")

# -----------------------------
# Procesar pregunta y mostrar resultados
# -----------------------------
if st.button("Enviar") and pregunta:
    texto, resultado = generar_respuesta(pregunta)
    st.markdown(f"<p style='color:#333333'>{texto}</p>", unsafe_allow_html=True)

    if isinstance(resultado, pd.DataFrame) and not resultado.empty:
        st.dataframe(
            resultado.style.set_properties(**{'background-color': 'white', 'color': '#333333'}),
            use_container_width=True
        )
