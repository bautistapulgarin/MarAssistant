import streamlit as st
from PIL import Image
import pandas as pd
import re
import unicodedata
import time
import base64
import os
import io

# ==============================
# IMPORTACIONES ADICIONALES PARA NN
# ==============================
NN_AVAILABLE = False
try:
    import joblib
    import numpy as np
    # Importamos solo lo necesario para que el joblib pueda deserializar los objetos
    from sklearn.neural_network import MLPClassifier 
    from sklearn.preprocessing import StandardScaler
    NN_AVAILABLE = True
except ImportError:
    # No es necesario detener, solo avisar
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
    "primary": "#154872",  # Azul Oscuro
    "accent": "#5DC0DC",   # Azul Claro
    "muted": "#437FAC",    # Azul Medio
    "bg": "#ffffff"        # Fondo blanco puro
}

# -----------------------------
# CSS GLOBAL - ¡Agregando el estilo para el botón de 'Predicción'!
# -----------------------------
st.markdown(f"""
<style>
/* Variables de Estilo */
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

/* Aplicación Principal y Fuente */
.stApp {{
    background-color: var(--mar-bg);
    color: #1b2635;
    font-family: 'Roboto', sans-serif;
}}

/* Títulos y Subtítulos */
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

/* Contenedores y Tarjetas */
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

/* Input de Texto y Controles */
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
.stTextInput>div>div>input::placeholder {{
    color: rgba(0, 0, 0, 0.4);
    font-style: italic;
}}

/* Estilo para el botón BUSCAR */
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

/* Estilo para el botón SECUNDARIO (VOZ) */
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

/* NUEVO: Estilo para el botón de PREDICCIÓN (Arriba a la derecha) */
.stButton>button[key="btn_prediccion"] {{
    background-color: #f7a835 !important; /* Naranja/Amarillo llamativo */
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

/* Estilo para el botón de Devolver (en la vista de Predicción) */
.stButton>button[key="btn_devolver"] {{
    background-color: #f0f2f6 !important; /* Gris claro */
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

/* Estilo para la ficha de conteo */
.metric-card {{
    background-color: #f0f2f6; /* Gris claro */
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


/* Sidebar */
[data-testid="stSidebar"] {{
    background-color: white;
    padding: 20px;
    box-shadow: var(--shadow-light);
    border-right: 1px solid #e0e0e0;
}}

/* Estilo para st.info, st.success, etc. */
.stAlert > div {{
    border-radius: 8px;
    padding: 12px 15px;
    font-size: 15px;
}}
/* Estilo para Selectbox - Opcional */
[data-testid="stForm"] label, [data-testid="stForm"] p {{
    font-weight: 500;
    color: #34495e;
}}

</style>
""", unsafe_allow_html=True)



# -------------------- FANTASMAS HALLOWEEN (derecha → arriba/abajo) + CALABAZAS (izquierda con rebote) --------------------
st.markdown("""
<style>
@keyframes floatDown {
    0% { top: -10%; }
    100% { top: 100%; }
}

@keyframes floatY {
    0% { transform: translateY(0); }
    50% { transform: translateY(10px); }
    100% { transform: translateY(0); }
}
</style>

<div style="position:fixed; top:0%; right:5%; font-size:30px; opacity:0.1; animation:floatDown 15s linear infinite; z-index:9999;">❄️</div>
<div style="position:fixed; top:10%; right:7%; font-size:28px; opacity:0.1; animation:floatDown 18s linear infinite; z-index:9999;">❄️</div>
<div style="position:fixed; top:20%; right:6%; font-size:25px; opacity:0.1; animation:floatDown 16s linear infinite; z-index:9999;">❄️</div>
<div style="position:fixed; top:25%; right:8%; font-size:20px; opacity:0.1; animation:floatDown 15s linear infinite; z-index:9999;">❄️</div>
<div style="position:fixed; top:10%; right:5%; font-size:28px; opacity:0.1; animation:floatDown 13s linear infinite; z-index:9999;">❄️</div>
<div style="position:fixed; top:20%; right:7%; font-size:25px; opacity:0.1; animation:floatDown 15s linear infinite; z-index:9999;">❄️</div>
<div style="position:fixed; top:25%; right:9%; font-size:20px; opacity:0.1; animation:floatDown 11s linear infinite; z-index:9999;">❄️</div>




<div style="position:fixed; bottom:5%; left:8%; font-size:22px; opacity:1; animation:floatY 3s ease-in-out infinite; z-index:9999;">🎃</div>
<div style="position:fixed; bottom:8%; left:10%; font-size:20px; opacity:1; animation:floatY 2.8s ease-in-out infinite; z-index:9999;">🎃</div>
<div style="position:fixed; bottom:6%; left:12%; font-size:18px; opacity:1; animation:floatY 3.2s ease-in-out infinite; z-index:9999;">🎃</div>
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
            @st.cache_resource
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
# HEADER: logo + títulos + BOTÓN DE PREDICCIÓN
# -----------------------------
logo_path = os.path.join("assets", "logoMar.png")

# Contenedor para alinear logo/títulos con el botón
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
            st.warning("Error al cargar logo. Usando título plano.")
            st.markdown(f'<p class="title">Sistema Integrado de Información de Proyectos</p>', unsafe_allow_html=True)
    else:
        st.warning("Logo no encontrado en assets/logoMar.png")
        st.markdown(f'<p class="title">Sistema Integrado de Información de Proyectos</p>', unsafe_allow_html=True)


# LÓGICA DEL BOTÓN DE PREDICCIÓN
def switch_to_predictor():
    """Cambia el estado de sesión para mostrar la vista del predictor y resetea la predicción."""
    st.session_state.current_view = 'predictor'
    # Reseteamos el resultado de predicción al cambiar la vista para que inicie limpio
    st.session_state.prediction_result = None

# Función para volver al chat
def switch_to_chat():
    """Cambia el estado de sesión para mostrar la vista del chat."""
    st.session_state.current_view = 'chat'
    st.session_state.prediction_result = None # Limpiamos también el resultado
    # Limpiamos los filtros de restricciones al volver al chat
    if 'filtro_restriccion' in st.session_state:
        del st.session_state['filtro_restriccion'] 
    if 'tipo_restriccion_preseleccionado' in st.session_state:
        del st.session_state['tipo_restriccion_preseleccionado']
    st.rerun()

with col_header_button:
    st.markdown("<div style='height:75px;'></div>", unsafe_allow_html=True) # Espacio para alinear
    if MODELO_NN:
        if st.button("Pronóstico", key="btn_prediccion", type="secondary", use_container_width=True):
            switch_to_predictor()
    else:
        st.warning("MLP no disponible.")
        
# Inicializar el estado de sesión para la vista
if 'current_view' not in st.session_state:
    st.session_state.current_view = 'chat'

# Inicializar el estado de la predicción
if 'prediction_result' not in st.session_state:
    st.session_state.prediction_result = None

# -----------------------------
# SIDEBAR: Uploads
# -----------------------------
st.sidebar.markdown(f'<p style="color:{PALETTE["primary"]}; font-size: 24px; font-weight: 700; margin-bottom: 0px;">Herramientas</p>', unsafe_allow_html=True)
st.sidebar.subheader("Cargas de Datos")
excel_file = st.sidebar.file_uploader("Sube tu archivo Excel (.xlsx)", type=["xlsx"])
img_file = st.sidebar.file_uploader("Sube imagen splash (opcional)", type=["png", "jpg", "jpeg"])
st.sidebar.markdown("---")

st.sidebar.markdown("💡 **Consejo:** Asegúrate de que tu archivo Excel contenga las hojas requeridas: *Avance*, *Responsables*, *Restricciones*, *Sostenibilidad*, *AvanceDiseño*, *InventarioDiseño*.")
st.sidebar.markdown(f'<p style="font-size:12px; color:#6b7280;">Coloca <code>assets/logoMar.png</code> y los archivos <code>*.joblib</code> junto a este archivo.</p>', unsafe_allow_html=True)


# -----------------------------
# SPLASH (opcional) - Se mantiene
# -----------------------------
placeholder = st.empty()
if img_file:
    # Lógica del splash screen...
    try:
        img_file.seek(0)
        img_b64 = base64.b64encode(img_file.read()).decode()
        splash_html = f"""
        <div style="position: fixed; top: 0; left: 0; width: 100%; height: 100vh; background-color: white; display: flex; justify-content: center; align-items: center; z-index: 9999;">
            <div style="text-align:center; padding: 20px; border-radius: 12px;">
                <img src="data:image/png;base64,{img_b64}" style="width:180px; max-width:60vw; height:auto; display:block; margin:0 auto;">
                <p style="margin-top: 20px; color: {PALETTE['primary']}; font-size: 20px; font-weight: 600;">Cargando...</p>
            </div>
        </div>
        """
        placeholder.markdown(splash_html, unsafe_allow_html=True)
        time.sleep(1)
        placeholder.empty()
    except Exception:
        placeholder.empty()

# -----------------------------
# LECTURA DE EXCEL (Se mantiene)
# -----------------------------
if not excel_file:
    st.info("Sube el archivo Excel en la barra lateral para cargar las hojas y empezar a consultar.")
    # Permite continuar para el predictor si ya está cargado y no depende del Excel
    if st.session_state.current_view == 'chat':
        st.stop()
else:
    # Intento de lectura (mantenido del original)
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
# NORMALIZACIÓN (Corregido el error de KeyError)
# -----------------------------
if excel_file:
    def normalizar_texto(texto):
        texto = str(texto).lower()
        texto = re.sub(r"[.,;:%]", "", texto)
        texto = re.sub(r"\s+", " ", texto)
        return texto.strip()

    def quitar_tildes(texto):
        return ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')

    # 🎯 CORRECCIÓN CLAVE: Verificar que la columna 'Proyecto' exista en TODAS las hojas
    hojas_a_verificar = [
        ("Avance", df_avance), 
        ("Responsables", df_responsables),
        ("Restricciones", df_restricciones), 
        ("Sostenibilidad", df_sostenibilidad),
        ("AvanceDiseño", df_avance_diseno), 
        ("InventarioDiseño", df_inventario_diseno)
    ]

    for df_name, df in hojas_a_verificar:
        if "Proyecto" not in df.columns:
            st.sidebar.error(f"La hoja '{df_name}' no contiene la columna 'Proyecto'. Esto puede afectar la búsqueda por proyecto.")
            # Detenemos solo si son las 4 hojas principales (consideradas críticas)
            if df_name in ["Avance", "Responsables", "Restricciones", "Sostenibilidad"]:
                 st.stop() 

    # Crear 'Proyecto_norm' y construir la lista de proyectos
    proyectos_list = []
    for df in [df_avance, df_responsables, df_restricciones, df_sostenibilidad, df_avance_diseno, df_inventario_diseno]:
        if "Proyecto" in df.columns:
            df["Proyecto_norm"] = df["Proyecto"].astype(str).apply(lambda x: quitar_tildes(normalizar_texto(x)))
            proyectos_list.append(df["Proyecto"].astype(str))
        else:
            # Si no existe 'Proyecto', creamos una columna 'Proyecto_norm' vacía para no romper el código posterior
            df["Proyecto_norm"] = ""

    # Concatenar todos los proyectos de las listas válidas
    if proyectos_list:
        all_projects = pd.concat(proyectos_list).dropna().unique()
    else:
        all_projects = [] # Lista vacía si ninguna hoja tenía la columna Proyecto

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
    
    # NUEVO: Mapeo de palabras clave a valores reales en "tipoRestriccion"
    MAPEO_RESTRICCION = {
        "material": "Materiales",
        "materiales": "Materiales",
        "diseno": "Diseño",
        "diseño": "Diseño",
        "contrato": "Contratos",
        "contratos": "Contratos",
        "permisos": "Permisos y Licencias",
        "licencias": "Permisos y Licencias",
        "financiero": "Financiera",
        "financiera": "Financiera"
        # Agregar aquí más mapeos si hay más tipos en la columna tipoRestriccion
    }

    # -----------------------------
    # FUNCION DE RESPUESTA
    # -----------------------------
    def generar_respuesta(pregunta):
        # La función devuelve: titulo, df_resultado, grafico, tipo_resultado, tipo_restriccion_preseleccionado
        pregunta_norm = quitar_tildes(normalizar_texto(pregunta))
        proyecto, proyecto_norm = extraer_proyecto(pregunta)
        
        # 🎯 Bloque de Avance de Obra (CORREGIDO EL FILTRADO)
        if "avance de obra" in pregunta_norm or "avance obra" in pregunta_norm:
            df = df_avance.copy()
            
            # 1. Aplicar filtro por Proyecto_norm si se encuentra
            if proyecto_norm and "Proyecto_norm" in df.columns:
                df = df[df["Proyecto_norm"] == proyecto_norm]
            
            # 2. Manejo de resultados
            if df.empty:
                return f"❌ No hay registros de avance de obra en {proyecto or 'todos'}", None, None, 'general', None
            
            # Gráfico de avance
            grafico = None
            if PLOTLY_AVAILABLE and "Avance" in df.columns:
                if 'Etapa' in df.columns and len(df['Etapa'].unique()) > 1:
                    df_sum = df.groupby('Etapa')['Avance'].mean().reset_index()
                    grafico = px.bar(
                        df_sum,
                        x="Etapa",
                        y="Avance",
                        text=df_sum["Avance"].apply(lambda x: f'{x:.1f}%'),
                        labels={"Etapa": "Etapa", "Avance": "Avance Promedio (%)"},
                        title=f"Avance Promedio por Etapa en {proyecto or 'Todos los Proyectos'}",
                        color_discrete_sequence=[PALETTE['primary']]
                    )
                    grafico.update_layout(
                        plot_bgcolor='white',
                        paper_bgcolor='white',
                        margin=dict(t=50, l=10, r=10, b=10)
                    )

            return f"🚧 Avance de obra en {proyecto or 'todos'}:", df, grafico, 'general', None

        # 🎯 Bloque de Avance en Diseño y Estado Diseño (combinadas)
        if "avance en diseno" in pregunta_norm or "avance diseno" in pregunta_norm or "estado diseno" in pregunta_norm or "inventario diseno" in pregunta_norm:
            
            # Buscar si se pide inventario específico
            if "inventario" in pregunta_norm:
                df = df_inventario_diseno.copy()
                titulo_prefijo = "📑 Inventario de Diseño"
            else:
                df = df_avance_diseno.copy()
                titulo_prefijo = "📐 Avance de Diseño"
            
            # Aplicar filtro por Proyecto_norm
            if proyecto_norm and "Proyecto_norm" in df.columns:
                df = df[df["Proyecto_norm"] == proyecto_norm]
            
            if df.empty:
                return f"❌ No hay registros de diseño en {proyecto or 'todos'}", None, None, 'general', None
            
            return f"{titulo_prefijo} en {proyecto or 'todos'}:", df, None, 'general', None
            
        # 🎯 Bloque de Responsables
        if "responsable" in pregunta_norm or "cargo" in pregunta_norm or any(c_norm in pregunta_norm for c_norm in CARGOS_VALIDOS_NORM.keys()):
            df = df_responsables.copy()
            
            # 1. Filtrar por Proyecto si se encuentra
            if proyecto_norm and "Proyecto_norm" in df.columns:
                df = df[df["Proyecto_norm"] == proyecto_norm]
            
            # 2. Filtrar por Cargo si se encuentra en la pregunta
            cargo_encontrado = None
            for cargo_norm, cargo_real in CARGOS_VALIDOS_NORM.items():
                if cargo_norm in pregunta_norm:
                    cargo_encontrado = cargo_real
                    break
            
            if cargo_encontrado:
                if 'Cargo' in df.columns:
                    df = df[df['Cargo'] == cargo_encontrado]
                else:
                    st.warning("La columna 'Cargo' no se encontró en la hoja 'Responsables' para filtrar.")
                    
            if df.empty:
                return f"❌ No se encontró responsable ({cargo_encontrado or 'cualquiera'}) en {proyecto or 'todos'}", None, None, 'general', None
            
            return f"👤 Responsables ({cargo_encontrado or 'todos'}) en {proyecto or 'todos'}:", df, None, 'general', None


        # 🎯 Bloque de Restricciones (Se mantiene corregido)
        if "restriccion" in pregunta_norm or "restricción" in pregunta_norm or "problema" in pregunta_norm:
            df = df_restricciones.copy()
            
            # 1. Filtrar por Proyecto si se encuentra
            if proyecto_norm and "Proyecto_norm" in df.columns:
                df = df[df["Proyecto_norm"] == proyecto_norm]
            
            # 2. Identificar tipo de restricción en el texto de la pregunta
            tipo_restriccion_preseleccionado = 'Todas las restricciones' # Default
            
            if "tipoRestriccion" in df.columns:
                # Buscar un tipo de restricción en la pregunta (Ej: "restricciones de materiales")
                for keyword, tipo_real in MAPEO_RESTRICCION.items():
                    if f"restriccion de {keyword}" in pregunta_norm or f"restricciones de {keyword}" in pregunta_norm:
                        # Nos aseguramos de que el tipo real existe en el DataFrame
                        if tipo_real in df["tipoRestriccion"].astype(str).unique().tolist():
                            tipo_restriccion_preseleccionado = tipo_real
                            break
            
            # Si el DataFrame filtrado por proyecto está vacío
            if df.empty:
                return f"❌ No hay restricciones registradas en {proyecto or 'todos'}", None, None, 'general', None

            grafico = None
            if PLOTLY_AVAILABLE and "tipoRestriccion" in df.columns:
                # Generar gráfico del subconjunto actual (filtrado por proyecto, si aplica)
                grafico = px.bar(
                    df.groupby("tipoRestriccion").size().reset_index(name="count"),
                    x="tipoRestriccion",
                    y="count",
                    text="count",
                    labels={"tipoRestriccion": "Tipo de Restricción", "count": "Cantidad"},
                    color="tipoRestriccion",
                    color_discrete_sequence=px.colors.qualitative.Plotly
                )
                grafico.update_layout(
                    showlegend=False,
                    xaxis_title="Tipo de Restricción",
                    yaxis_title="Cantidad",
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                    margin=dict(t=30, l=10, r=10, b=10)
                )

            # Devolvemos el DataFrame filtrado por proyecto, el gráfico y el tipo preseleccionado
            return f"⚠️ Restricciones en {proyecto or 'todos'}:", df, grafico, 'restricciones', tipo_restriccion_preseleccionado

        if any(k in pregunta_norm for k in ["sostenibilidad", "edge", "sostenible", "ambiental"]):
            # Lógica de Sostenibilidad (se mantiene)
            df = df_sostenibilidad.copy()
            if proyecto_norm and "Proyecto_norm" in df.columns:
                df = df[df["Proyecto_norm"] == proyecto_norm]
            if df.empty:
                return f"❌ No hay registros de sostenibilidad en {proyecto or 'todos'}", None, None, 'general', None
            return f"🌱 Información de sostenibilidad en {proyecto or 'todos'}:", df, None, 'general', None


        # Si no se encuentra nada
        return ("❓ No entendí la pregunta. Intenta con 'avance de obra', 'avance en diseño', "
                "'estado diseño', 'responsable', 'restricciones' o 'sostenibilidad'."), None, None, 'general', None

# -----------------------------
# FUNCIÓN DE PREDICCIÓN (MLP) - (Se mantiene igual)
# -----------------------------
def mostrar_predictor_mlp():
    # ... (Lógica del predictor - se mantiene igual) ...
    """Muestra la interfaz de entrada y hace la predicción del MLP."""
    if not MODELO_NN:
        st.error("No se pudo cargar el modelo de predicción de contratos (MLP). Verifica los archivos `.joblib` en la carpeta `assets`.")
        return

    # Creamos un contenedor para el título y el botón de volver
    col_pred_title, col_pred_back = st.columns([6, 1.5])
    
    with col_pred_title:
        st.markdown(f'<div class="mar-card" style="margin-bottom: 0px;"><p style="color:{PALETTE["primary"]}; font-size: 22px; font-weight:700; margin:0 0 8px 0;">🔮 Previsión de Cumplimiento de Contratos</p>'
                    '<p style="margin:0 0 0 0;">Ingresa los parámetros del contrato para predecir la probabilidad de cumplimiento a tiempo.</p></div>',
                    unsafe_allow_html=True)
    
    with col_pred_back:
        st.markdown("<div style='height:42px;'></div>", unsafe_allow_html=True) # Espacio para alinear
        # Botón de devolver en la vista principal de Predicción
        if st.button("⬅️ Devolver", key="btn_devolver", type="secondary", use_container_width=True):
            switch_to_chat()
            
    # Separador visual después del título/botón
    st.markdown("<div style='height:15px;'></div>", unsafe_allow_html=True)


    # Nuevo formulario exclusivo para la predicción
    with st.form("mlp_predictor_form_body", clear_on_submit=False):
        st.subheader("Datos de Entrada del Contrato")
        col_dias, col_reprog = st.columns(2)
        with col_dias:
            dias_input = st.number_input("Días de legalización esperados", min_value=1, value=15, step=1, key='dias_input_nn')
        with col_reprog:
            reprog_input = st.number_input("Número de reprogramaciones", min_value=0, value=0, step=1, key='reprog_input_nn')

        col_prior, col_tipo, col_cnc = st.columns(3)
        with col_prior:
            prioridad_input = st.selectbox("Prioridad", options=['Alta', 'Media', 'Baja'], key='prioridad_input_nn')
        with col_tipo:
            contrato_input = st.selectbox("Tipo de contrato", options=['Obra', 'Suministro', 'Servicios', 'Subcontrato'], key='contrato_input_nn')
        with col_cnc:
            cnc_input = st.selectbox("Causa de retraso (CNCCompromiso)", options=['Aprobación interna', 'Proveedor', 'Legalización interna', 'Financiera'], key='cnc_input_nn')

        # Usamos on_click para limpiar el resultado ANTES de la nueva predicción.
        predict_button = st.form_submit_button("🚀 Predecir", type="primary", 
                                               on_click=lambda: setattr(st.session_state, 'prediction_result', None))

    if predict_button:
        try:
            # Crear el DataFrame de entrada
            nuevo_df = pd.DataFrame({
                'dias_legalizacion_esperados': [dias_input],
                'numero_reprogramaciones': [reprog_input],
                'prioridad': [prioridad_input],
                'tipo_contrato': [contrato_input],
                'CNCCompromiso': [cnc_input]
            })

            # One-hot encoding y Alinear columnas
            nuevo_df = pd.get_dummies(nuevo_df)
            
            # Asegurar que todas las columnas del modelo (FEATURES_NN) estén presentes y en orden
            for col in FEATURES_NN:
                if col not in nuevo_df.columns:
                    nuevo_df[col] = 0
            nuevo_df = nuevo_df[FEATURES_NN]

            # Escalar las variables numéricas
            cols_to_scale = ['dias_legalizacion_esperados', 'numero_reprogramaciones']
            nuevo_df[cols_to_scale] = SCALER_NN.transform(nuevo_df[cols_to_scale])

            # Predecir con MLP
            prob_cumplimiento = MODELO_NN.predict_proba(nuevo_df)[0][1]
            prediccion = MODELO_NN.predict(nuevo_df)[0]
            
            # Guardar el resultado en el estado de sesión
            st.session_state.prediction_result = {
                'prediccion': prediccion,
                'prob_cumplimiento': prob_cumplimiento
            }
            # st.rerun() # Descomentar si la visualización del resultado no es inmediata

        except Exception as e:
            st.error(f"Error al procesar la predicción: {e}")
            st.info("Revisa si el formato de los datos es compatible con el modelo MLP cargado.")
            st.session_state.prediction_result = None # Limpiar el resultado si hay error

    # Mostrar el resultado fuera del if predict_button, controlado por el estado
    if st.session_state.prediction_result is not None:
        prediccion = st.session_state.prediction_result['prediccion']
        prob_cumplimiento = st.session_state.prediction_result['prob_cumplimiento']

        # Mostrar resultado en un bloque de tarjeta
        st.markdown("<div class='mar-card' style='margin-top:20px;'>", unsafe_allow_html=True)
        if prediccion == 1:
            st.success(f"### Predicción: ✅ Cumplido a tiempo")
            st.markdown(f"La probabilidad de **cumplimiento** es del **`{prob_cumplimiento*100:.2f}%`**. ¡Parece que este contrato va bien!")
        else:
            st.warning(f"### Predicción: ⚠️ Probable reprogramación")
            st.markdown(f"La probabilidad de **incumplimiento/reprogramación** es alta (Cumplimiento: `{prob_cumplimiento*100:.2f}%`). Se requiere seguimiento.")
        st.markdown("</div>", unsafe_allow_html=True)


# -----------------------------
# LÓGICA DE VISTAS PRINCIPALES
# -----------------------------
if st.session_state.current_view == 'predictor':
    mostrar_predictor_mlp()
    st.markdown("<div style='height: 100px;'></div>", unsafe_allow_html=True) # Espacio inferior

elif st.session_state.current_view == 'chat':
    # -----------------------------
    # INTERFAZ: input + botón al lado + voz 
    # -----------------------------
    # Tarjeta informativa (más limpia)
    st.markdown(
        f'<div class="mar-card"><p style="color:{PALETTE["primary"]}; font-size: 18px; font-weight:700; margin:0 0 8px 0;">Consulta Rápida</p>'
        '<p style="margin:0 0 0 0;">Escribe tu consulta relacionada con el estado u contexto de los proyectos. Ej: "restricciones de materiales en Burdeos"</p></div>',
        unsafe_allow_html=True
    )

    # Formulario de Chat
    with st.form("query_form", clear_on_submit=False):
        col_input, col_enviar, col_voz = st.columns([6, 1.2, 1])
        
        with col_input:
            # Usamos la misma clave para que el texto persista si se presiona el botón de voz
            pregunta = st.text_input(label="", placeholder="Ej: 'Avance de obra en proyecto Altos del Mar' o 'Responsable de diseño'", label_visibility="collapsed", key='chat_query')
        
        with col_enviar:
            # Le decimos a Streamlit que, si se presiona "Buscar", debe ejecutar el callback
            enviar = st.form_submit_button("Buscar", key="btn_buscar", type="secondary", use_container_width=True) 
        
        with col_voz:
            voz = st.form_submit_button("🎤 Voz", key="voz", help="Activar entrada por voz", type="secondary", use_container_width=True)

    # Lógica de procesamiento de la pregunta
    if enviar and pregunta:
        if not excel_file:
            st.error("No se puede consultar. ¡Sube el archivo Excel en la barra lateral primero!")
        else:
            # Generar respuesta: ahora devuelve 5 valores
            st.session_state['last_query_text'] = pregunta
            
            # Intentamos obtener el resultado (esperamos 5 valores)
            titulo, df_resultado, grafico, tipo_resultado, tipo_restriccion_preseleccionado = generar_respuesta(pregunta)
            
          if tipo_resultado == 'restricciones':
            # -----------------------------
            # BOTÓN Y MODAL PARA REGISTRAR RESTRICCIÓN
            # -----------------------------
            col_btn, _ = st.columns([1, 6])
            with col_btn:
                if st.button("Registrar Restricción", key="btn_registrar"):
                    st.session_state.show_popup = True

            if st.session_state.get('show_popup', False):
                with st.modal("Registro de Restricciones", key="modal_restricciones"):
                    st.markdown("📋 **Formulario de Nueva Restricción**")
                    campo_actividad = st.text_input("Nombre de la Actividad")
                    campo_tipo = st.selectbox("Tipo de Restricción", options=list(MAPEO_RESTRICCION.values()))
                    campo_descripcion = st.text_area("Descripción")
            
                    if st.button("Guardar", key="btn_guardar_restriccion"):
                    # Aquí puedes agregar lógica para guardar en df_restricciones o Excel
                        st.success("Formulario listo (aún sin persistencia).")
                        st.session_state.show_popup = False




















                
                # Si es una restricción y tiene preselección, la guardamos
                st.session_state['tipo_restriccion_preseleccionado'] = tipo_restriccion_preseleccionado
                # Guardamos los 4 principales
                st.session_state['last_query_result'] = (titulo, df_resultado, grafico, tipo_resultado) 
            else:
                # Si no es restricción o no hay preselección válida, limpiamos y guardamos
                if 'tipo_restriccion_preseleccionado' in st.session_state:
                    del st.session_state['tipo_restriccion_preseleccionado']
                # Guardamos los 4 principales
                st.session_state['last_query_result'] = (titulo, df_resultado, grafico, tipo_resultado)


            # Aseguramos que el filtro interactivo se inicie con el valor del texto (si aplica) o con 'Todas'
            if 'filtro_restriccion' in st.session_state:
                # Eliminamos la clave del filtro interactivo para que se inicialice con el nuevo default/preselección
                del st.session_state['filtro_restriccion']
            
            st.rerun() # Dispara el re-render para mostrar los resultados

    # -----------------------------
    # MOSTRAR RESULTADOS (Ajustado para el recalculo en el filtro y la nueva columna)
    # -----------------------------
    if 'last_query_result' in st.session_state:
        # Recuperamos los 4 elementos
        titulo, df_resultado, grafico, tipo_resultado = st.session_state['last_query_result'] 
        
        st.markdown(f'<div class="mar-card" style="margin-top:20px;"><p style="color:{PALETTE["primary"]}; font-size: 20px; font-weight:700; margin:0 0 8px 0;">{titulo}</p></div>', unsafe_allow_html=True)

        if tipo_resultado == 'restricciones':
            
            # Lista de tipos de restricción para el selectbox
            if "tipoRestriccion" in df_resultado.columns:
                tipos_restriccion = ['Todas las restricciones'] + df_resultado["tipoRestriccion"].astype(str).unique().tolist()
            else:
                tipos_restriccion = ['Todas las restricciones']
                
            # Inicializamos el filtro interactivo con la preselección si existe
            default_index = 0
            if 'tipo_restriccion_preseleccionado' in st.session_state and st.session_state['tipo_restriccion_preseleccionado'] in tipos_restriccion:
                default_index = tipos_restriccion.index(st.session_state['tipo_restriccion_preseleccionado'])
                
            # --- Se coloca el filtro ANTES de la tarjeta resumen para que afecte la variable df_filtrado ---
            filtro_restriccion = st.selectbox(
                "Filtro por Tipo de Restricción:",
                options=tipos_restriccion,
                index=default_index,
                key='filtro_restriccion',
                label_visibility="visible"
            )

            # Aplicar filtro
            df_filtrado = df_resultado.copy()
            if filtro_restriccion != 'Todas las restricciones' and "tipoRestriccion" in df_filtrado.columns:
                df_filtrado = df_filtrado[df_filtrado["tipoRestriccion"] == filtro_restriccion]

            # Dividimos la sección de resultados en dos columnas (después de aplicar el filtro)
            col_dias, col_filtro = st.columns([1, 2])
            
            # Cálculo de DiasDiferencia en el df_filtrado para mostrarlo en la tabla
            if all(col in df_filtrado.columns for col in ["FechaCompromisoActual", "FechaCompromisoInicial"]):
                # Convertir a datetime (manejando errores)
                df_filtrado['FechaCompromisoActual'] = pd.to_datetime(df_filtrado['FechaCompromisoActual'], errors='coerce')
                df_filtrado['FechaCompromisoInicial'] = pd.to_datetime(df_filtrado['FechaCompromisoInicial'], errors='coerce')
                
                # Calcular la diferencia en días
                df_filtrado['DiasDiferencia'] = (df_filtrado['FechaCompromisoActual'] - df_filtrado['FechaCompromisoInicial']).dt.days
            else:
                 df_filtrado['DiasDiferencia'] = pd.NA # Si faltan columnas, agregamos NA

            
            # Recalcular la tarjeta de resumen
            with col_dias:
                dias_diferencia_df = None
                
                # Solo consideramos filas con valores válidos para el cálculo de métricas
                df_valido = df_filtrado.dropna(subset=['DiasDiferencia']).copy()

                if not df_valido.empty:
                    # Filtramos solo las que tienen retraso (diferencia > 0)
                    restricciones_reprogramadas = df_valido[df_valido['DiasDiferencia'] > 0]
                    total_restricciones = len(df_valido)
                    total_restricciones_reprogramadas = len(restricciones_reprogramadas)
                    promedio_dias_retraso = restricciones_reprogramadas['DiasDiferencia'].mean()
                    
                    # Creamos la tabla de resumen (CON LOS CAMPOS CORREGIDOS)
                    data = {
                        'Métrica': [
                            'Total Restricciones (con Fechas)',
                            'Restricciones Reprogramadas (Días > 0)', 
                            'Promedio Días de Retraso (Por Reprogramada)'
                        ],
                        'Valor': [
                            total_restricciones,
                            total_restricciones_reprogramadas, 
                            f"{promedio_dias_retraso:,.2f}" if not pd.isna(promedio_dias_retraso) else "0.00"
                        ]
                    }
                    dias_diferencia_df = pd.DataFrame(data)

                if dias_diferencia_df is not None:
                    st.markdown('<div class="mar-card" style="background-color:#fff3e0; padding: 15px;">', unsafe_allow_html=True)
                    st.markdown('📅 **Resumen de Demoras por Reprogramación**', unsafe_allow_html=True)
                    st.dataframe(
                        dias_diferencia_df, 
                        hide_index=True, 
                        use_container_width=True,
                        column_config={
                            "Métrica": st.column_config.Column("Métrica de Demora", width="medium"),
                            "Valor": st.column_config.TextColumn("Resultado", width="small")
                        }
                    )
                    st.markdown('<p style="font-size:12px; margin:0; color:#8d6e63;">*Datos filtrados por el tipo de restricción actual.</p>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.info("No hay datos de fechas válidos para calcular la diferencia de días.")

            # Columna principal con la tabla de detalle
            with col_filtro:
                st.markdown(f'<p style="font-weight:600; color:{PALETTE["primary"]}; margin-top:15px; margin-bottom:10px;">Detalle de Restricciones ({len(df_filtrado)} encontradas)</p>', unsafe_allow_html=True)
                
                # 🎯 LISTA DE COLUMNAS ACTUALIZADA
                columns_to_show = [
                    'Actividad', 
                    'Restriccion', 
                    'numeroReprogramacionesCompromiso', 
                    'Descripción', 
                    'tipoRestriccion', 
                    'FechaCompromisoInicial', 
                    'FechaCompromisoActual', 
                    'DiasDiferencia', 
                    'Responsable', 
                    'Comentarios'
                ]
                
                # Seleccionamos las columnas que existen y mostramos el DataFrame
                # Usamos filter(items=...) para seleccionar solo las columnas que realmente existen
                df_display = df_filtrado.filter(items=columns_to_show)
                
                # Renombramos las columnas calculadas/nuevas para la visualización (si existen)
                rename_map = {}
                if 'DiasDiferencia' in df_display.columns:
                     rename_map['DiasDiferencia'] = 'Diferencia (Días)'
                if 'numeroReprogramacionesCompromiso' in df_display.columns:
                     rename_map['numeroReprogramacionesCompromiso'] = 'Núm. Reprog.'
                     
                df_display = df_display.rename(columns=rename_map)

                st.dataframe(df_display, use_container_width=True)
                
            # Gráfico de Restricciones (si aplica, en la parte inferior para no competir con el DF de días)
            if grafico:
                st.markdown('<div class="mar-card" style="margin-top: 25px;">', unsafe_allow_html=True)
                st.markdown(f'<p style="font-weight:600; color:{PALETTE["primary"]}; margin-bottom:5px;">Conteo por Tipo de Restricción (Todos los Proyectos/Tipo)</p>', unsafe_allow_html=True)
                st.plotly_chart(grafico, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
        # --- Lógica para otros resultados (Avance, Responsables, etc.) ---
        else:
            # Caso general: muestra solo el dataframe o mensaje
            if df_resultado is not None:
                st.markdown(f'<div class="mar-card" style="margin-top:0px;">', unsafe_allow_html=True)
                if grafico:
                    # Si hay gráfico (Avance de Obra), lo mostramos primero
                    st.plotly_chart(grafico, use_container_width=True)
                
                # Mostramos el detalle del DataFrame
                st.dataframe(df_resultado.drop(columns=["Proyecto_norm"], errors='ignore'), use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.error(titulo) # Muestra el mensaje de error o "No entendí"
    
    st.markdown("<div style='height: 100px;'></div>", unsafe_allow_html=True) # Espacio inferior





