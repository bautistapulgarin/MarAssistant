# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
import re
import unicodedata
from google.oauth2.service_account import Credentials
import gspread
import joblib

# -----------------------------
# CONFIGURACIÓN GENERAL
# -----------------------------
st.set_page_config(page_title="MAR Assistant", layout="wide")
PALETTE = {
    "primary": "#1f77b4"
}

# Variables globales (pueden cargarse desde archivo o GitHub)
PLOTLY_AVAILABLE = True
MODELO_NN = None
SCALER_NN = None
FEATURES_NN = []

# -----------------------------
# UTILIDADES
# -----------------------------
def normalizar_texto(texto):
    return texto.lower().strip()

def quitar_tildes(texto):
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )

# -----------------------------
# GOOGLE SHEETS / EXCEL
# -----------------------------
def init_gsheets(sheet_name, credentials_file="credentials.json"):
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_file(credentials_file, scopes=scope)
    client = gspread.authorize(creds)
    return client.open(sheet_name).sheet1

# -----------------------------
# CARGA DE DATOS (EXCEL / SHEETS)
# -----------------------------
excel_file = st.sidebar.file_uploader("Sube archivo Excel", type=["xlsx"])
if excel_file:
    # Leer todas las hojas necesarias
    xls = pd.ExcelFile(excel_file)
    df_avance = pd.read_excel(xls, sheet_name="AvanceObra")
    df_avance_diseno = pd.read_excel(xls, sheet_name="AvanceDiseno")
    df_inventario_diseno = pd.read_excel(xls, sheet_name="InventarioDiseno")
    df_responsables = pd.read_excel(xls, sheet_name="Responsables")
    df_restricciones = pd.read_excel(xls, sheet_name="Restricciones")
    df_sostenibilidad = pd.read_excel(xls, sheet_name="Sostenibilidad")
else:
    df_avance = df_avance_diseno = df_inventario_diseno = df_responsables = df_restricciones = df_sostenibilidad = pd.DataFrame()

# -----------------------------
# NORMALIZACIÓN DE PROYECTOS
# -----------------------------
proyectos_list = []
for df in [df_avance, df_responsables, df_restricciones, df_sostenibilidad, df_avance_diseno, df_inventario_diseno]:
    if "Proyecto" in df.columns:
        df["Proyecto_norm"] = df["Proyecto"].astype(str).apply(lambda x: quitar_tildes(normalizar_texto(x)))
        proyectos_list.append(df["Proyecto"].astype(str))
    else:
        df["Proyecto_norm"] = ""

all_projects = pd.concat(proyectos_list).dropna().unique() if proyectos_list else []
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
# CARGOS VALIDOS
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
# MAPEO DE RESTRICCIONES
# -----------------------------
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
}

# -----------------------------
# FUNCION DE RESPUESTA
# -----------------------------
def generar_respuesta(pregunta):
    pregunta_norm = quitar_tildes(normalizar_texto(pregunta))
    proyecto, proyecto_norm = extraer_proyecto(pregunta)

    # Avance de obra
    if "avance de obra" in pregunta_norm or "avance obra" in pregunta_norm:
        df = df_avance.copy()
        if proyecto_norm and "Proyecto_norm" in df.columns:
            df = df[df["Proyecto_norm"] == proyecto_norm]
        if df.empty:
            return f"❌ No hay registros de avance de obra en {proyecto or 'todos'}", None, None, 'general', None
        grafico = None
        if PLOTLY_AVAILABLE and "Avance" in df.columns and 'Etapa' in df.columns:
            df_sum = df.groupby('Etapa')['Avance'].mean().reset_index()
            grafico = px.bar(
                df_sum,
                x="Etapa",
                y="Avance",
                text=df_sum["Avance"].apply(lambda x: f'{x:.1f}%'),
                labels={"Etapa": "Etapa", "Avance": "Avance Promedio (%)"},
                title=f"Avance Promedio por Etapa en {proyecto or 'Todos los Proyectos'}"
            )
        return f"🚧 Avance de obra en {proyecto or 'todos'}:", df, grafico, 'general', None

    # Avance o inventario de diseño
    if "avance en diseno" in pregunta_norm or "avance diseno" in pregunta_norm or "estado diseno" in pregunta_norm or "inventario diseno" in pregunta_norm:
        if "inventario" in pregunta_norm:
            df = df_inventario_diseno.copy()
            titulo_prefijo = "📑 Inventario de Diseño"
        else:
            df = df_avance_diseno.copy()
            titulo_prefijo = "📐 Avance de Diseño"
        if proyecto_norm and "Proyecto_norm" in df.columns:
            df = df[df["Proyecto_norm"] == proyecto_norm]
        if df.empty:
            return f"❌ No hay registros de diseño en {proyecto or 'todos'}", None, None, 'general', None
        return f"{titulo_prefijo} en {proyecto or 'todos'}:", df, None, 'general', None

    # Responsables
    if "responsable" in pregunta_norm or "cargo" in pregunta_norm or any(c_norm in pregunta_norm for c_norm in CARGOS_VALIDOS_NORM.keys()):
        df = df_responsables.copy()
        if proyecto_norm and "Proyecto_norm" in df.columns:
            df = df[df["Proyecto_norm"] == proyecto_norm]
        cargo_encontrado = None
        for cargo_norm, cargo_real in CARGOS_VALIDOS_NORM.items():
            if cargo_norm in pregunta_norm:
                cargo_encontrado = cargo_real
                break
        if cargo_encontrado and 'Cargo' in df.columns:
            df = df[df['Cargo'] == cargo_encontrado]
        if df.empty:
            return f"❌ No se encontró responsable ({cargo_encontrado or 'cualquiera'}) en {proyecto or 'todos'}", None, None, 'general', None
        return f"👤 Responsables ({cargo_encontrado or 'todos'}) en {proyecto or 'todos'}:", df, None, 'general', None

    # Restricciones
    if "restriccion" in pregunta_norm or "restricción" in pregunta_norm or "problema" in pregunta_norm:
        df = df_restricciones.copy()
        if proyecto_norm and "Proyecto_norm" in df.columns:
            df = df[df["Proyecto_norm"] == proyecto_norm]
        tipo_restriccion_preseleccionado = 'Todas las restricciones'
        if "tipoRestriccion" in df.columns:
            for keyword, tipo_real in MAPEO_RESTRICCION.items():
                if f"restriccion de {keyword}" in pregunta_norm or f"restricciones de {keyword}" in pregunta_norm:
                    if tipo_real in df["tipoRestriccion"].astype(str).unique().tolist():
                        tipo_restriccion_preseleccionado = tipo_real
                        break
        if df.empty:
            return f"❌ No hay restricciones registradas en {proyecto or 'todos'}", None, None, 'general', None
        grafico = None
        if PLOTLY_AVAILABLE and "tipoRestriccion" in df.columns:
            grafico = px.bar(
                df.groupby("tipoRestriccion").size().reset_index(name="count"),
                x="tipoRestriccion",
                y="count",
                text="count",
                labels={"tipoRestriccion": "Tipo de Restricción", "count": "Cantidad"},
                color="tipoRestriccion"
            )
        return f"⚠️ Restricciones en {proyecto or 'todos'}:", df, grafico, 'restricciones', tipo_restriccion_preseleccionado

    # Sostenibilidad
    if any(k in pregunta_norm for k in ["sostenibilidad", "edge", "sostenible", "ambiental"]):
        df = df_sostenibilidad.copy()
        if proyecto_norm and "Proyecto_norm" in df.columns:
            df = df[df["Proyecto_norm"] == proyecto_norm]
        if df.empty:
            return f"❌ No hay registros de sostenibilidad en {proyecto or 'todos'}", None, None, 'general', None
        return f"🌱 Información de sostenibilidad en {proyecto or 'todos'}:", df, None, 'general', None

    return ("❓ No entendí la pregunta. Intenta con 'avance de obra', 'avance en diseño', "
            "'estado diseño', 'responsable', 'restricciones' o 'sostenibilidad'."), None, None, 'general', None

# -----------------------------
# PREDICCIÓN MLP
# -----------------------------
def mostrar_predictor_mlp():
    if not MODELO_NN:
        st.error("No se pudo cargar el modelo de predicción de contratos (MLP).")
        return

    col_pred_title, col_pred_back = st.columns([6, 1.5])
    with col_pred_title:
        st.markdown(f'<div class="mar-card" style="margin-bottom: 0px;"><p style="color:{PALETTE["primary"]}; font-size: 22px; font-weight:700; margin:0 0 8px 0;">🔮 Previsión de Cumplimiento de Contratos</p></div>', unsafe_allow_html=True)

    with st.form("mlp_predictor_form_body", clear_on_submit=False):
        col_dias, col_reprog = st.columns(2)
        with col_dias:
            dias_input = st.number_input("Días de legalización esperados", min_value=1, value=15)
        with col_reprog:
            reprog_input = st.number_input("Número de reprogramaciones", min_value=0, value=0)
        col_prior, col_tipo, col_cnc = st.columns(3)
        with col_prior:
            prioridad_input = st.selectbox("Prioridad", options=['Alta', 'Media', 'Baja'])
        with col_tipo:
            contrato_input = st.selectbox("Tipo de contrato", options=['Obra', 'Suministro', 'Servicios', 'Subcontrato'])
        with col_cnc:
            cnc_input = st.selectbox("Causa de retraso (CNCCompromiso)", options=['Aprobación interna', 'Proveedor', 'Legalización interna', 'Financiera'])
        predict_button = st.form_submit_button("🚀 Predecir")

    if predict_button:
        try:
            nuevo_df = pd.DataFrame({
                'dias_legalizacion_esperados': [dias_input],
                'numero_reprogramaciones': [reprog_input],
                'prioridad': [prioridad_input],
                'tipo_contrato': [contrato_input],
                'CNCCompromiso': [cnc_input]
            })
            nuevo_df = pd.get_dummies(nuevo_df)
            for col in FEATURES_NN:
                if col not in nuevo_df.columns:
                    nuevo_df[col] = 0
            nuevo_df = nuevo_df[FEATURES_NN]
            cols_to_scale = ['dias_legalizacion_esperados', 'numero_reprogramaciones']
            nuevo_df[cols_to_scale] = SCALER_NN.transform(nuevo_df[cols_to_scale])
            prob_cumplimiento = MODELO_NN.predict_proba(nuevo_df)[0][1]
            prediccion = MODELO_NN.predict(nuevo_df)[0]
            st.session_state.prediction_result = {'prediccion': prediccion, 'prob_cumplimiento': prob_cumplimiento}
        except Exception as e:
            st.error(f"Error al procesar la predicción: {e}")
            st.session_state.prediction_result = None

    if 'prediction_result' in st.session_state and st.session_state.prediction_result:
        prediccion = st.session_state.prediction_result['prediccion']
        prob_cumplimiento = st.session_state.prediction_result['prob_cumplimiento']
        if prediccion == 1:
            st.success(f"✅ Predicción: Cumplido a tiempo ({prob_cumplimiento*100:.2f}%)")
        else:
            st.warning(f"⚠️ Predicción: Probable reprogramación ({prob_cumplimiento*100:.2f}%)")

# -----------------------------
# VISTA PRINCIPAL
# -----------------------------
if 'current_view' not in st.session_state:
    st.session_state.current_view = 'chat'

if st.session_state.current_view == 'predictor':
    mostrar_predictor_mlp()
elif st.session_state.current_view == 'chat':
    st.markdown(f'<div class="mar-card"><p style="color:{PALETTE["primary"]}; font-size: 18px; font-weight:700;">Consulta Rápida</p></div>', unsafe_allow_html=True)
    with st.form("query_form", clear_on_submit=False):
        col_input, col_enviar = st.columns([6, 1.2])
        with col_input:
            pregunta = st.text_input("", placeholder="Ej: 'Avance de obra en Altos del Mar'", key='chat_query')
        with col_enviar:
            enviar = st.form_submit_button("Buscar")
    if enviar and pregunta:
        if not excel_file:
            st.error("Sube el archivo Excel primero.")
        else:
            titulo, df_resultado, grafico, tipo_resultado, tipo_restriccion_preseleccionado = generar_respuesta(pregunta)
            st.markdown(f'**{titulo}**')
            if df_resultado is not None:
                st.dataframe(df_resultado)
            if grafico:
                st.plotly_chart(grafico)
