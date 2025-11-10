import streamlit as st
import pandas as pd
import re
from datetime import datetime

# Opcionales si quieres gráficos con Plotly
try:
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

# --- PALETA DE COLORES ---
PALETTE = {'primary': '#1976d2'}

# --- CARGA DE MODELO MLP Y SCALER (simulados aquí) ---
MODELO_NN = None  # Cargar tu modelo real con joblib.load("modelo.joblib")
SCALER_NN = None  # Cargar tu scaler real
FEATURES_NN = []  # Lista de features usadas en el modelo

# --- UTILIDADES ---
def normalizar_texto(texto):
    return texto.lower().strip()

def quitar_tildes(texto):
    import unicodedata
    return ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')

# --- GOOGLE SHEETS ---
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def init_gsheets(sheet_name, credentials_file="credentials.json"):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, scope)
    client = gspread.authorize(creds)
    return client.open(sheet_name).sheet1

def registrar_consulta_gsheet(sheet, pregunta, tipo_resultado, proyecto, resultado_summary):
    fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row = [fecha_hora, pregunta, tipo_resultado, proyecto or "Todos", resultado_summary]
    sheet.append_row(row)

# --- CARGA DEL EXCEL ---
excel_file = st.sidebar.file_uploader("Sube el archivo Excel", type=["xlsx"])

if excel_file:
    df_avance = pd.read_excel(excel_file, sheet_name="Avance Obra")
    df_responsables = pd.read_excel(excel_file, sheet_name="Responsables")
    df_restricciones = pd.read_excel(excel_file, sheet_name="Restricciones")
    df_sostenibilidad = pd.read_excel(excel_file, sheet_name="Sostenibilidad")
    df_avance_diseno = pd.read_excel(excel_file, sheet_name="Avance Diseño")
    df_inventario_diseno = pd.read_excel(excel_file, sheet_name="Inventario Diseño")

    # --- NORMALIZACIÓN DE PROYECTOS ---
    proyectos_list = []
    for df in [df_avance, df_responsables, df_restricciones, df_sostenibilidad, df_avance_diseno, df_inventario_diseno]:
        if "Proyecto" in df.columns:
            df["Proyecto_norm"] = df["Proyecto"].astype(str).apply(lambda x: quitar_tildes(normalizar_texto(x)))
            proyectos_list.append(df["Proyecto"].astype(str))
        else:
            df["Proyecto_norm"] = ""

    if proyectos_list:
        all_projects = pd.concat(proyectos_list).dropna().unique()
    else:
        all_projects = []

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

    # --- CARGOS ---
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

    # --- MAPEOS DE RESTRICCIÓN ---
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

    # --- FUNCIÓN GENERAR RESPUESTA ---
    def generar_respuesta(pregunta):
        pregunta_norm = quitar_tildes(normalizar_texto(pregunta))
        proyecto, proyecto_norm = extraer_proyecto(pregunta)

        # Avance de Obra
        if "avance de obra" in pregunta_norm or "avance obra" in pregunta_norm:
            df = df_avance.copy()
            if proyecto_norm: df = df[df["Proyecto_norm"] == proyecto_norm]
            if df.empty: return f"❌ No hay registros de avance de obra en {proyecto or 'todos'}", None, None, 'general', None
            grafico = None
            if PLOTLY_AVAILABLE and "Avance" in df.columns and 'Etapa' in df.columns:
                df_sum = df.groupby('Etapa')['Avance'].mean().reset_index()
                grafico = px.bar(df_sum, x="Etapa", y="Avance", text=df_sum["Avance"].apply(lambda x: f'{x:.1f}%'),
                                 labels={"Etapa": "Etapa", "Avance": "Avance Promedio (%)"},
                                 title=f"Avance Promedio por Etapa en {proyecto or 'Todos los Proyectos'}",
                                 color_discrete_sequence=[PALETTE['primary']])
                grafico.update_layout(plot_bgcolor='white', paper_bgcolor='white', margin=dict(t=50,l=10,r=10,b=10))
            return f"🚧 Avance de obra en {proyecto or 'todos'}:", df, grafico, 'general', None

        # Avance Diseño / Inventario
        if any(k in pregunta_norm for k in ["avance en diseno","avance diseno","estado diseno","inventario diseno"]):
            if "inventario" in pregunta_norm:
                df = df_inventario_diseno.copy(); titulo_prefijo = "📑 Inventario de Diseño"
            else:
                df = df_avance_diseno.copy(); titulo_prefijo = "📐 Avance de Diseño"
            if proyecto_norm: df = df[df["Proyecto_norm"] == proyecto_norm]
            if df.empty: return f"❌ No hay registros de diseño en {proyecto or 'todos'}", None, None, 'general', None
            return f"{titulo_prefijo} en {proyecto or 'todos'}:", df, None, 'general', None

        # Responsables
        if "responsable" in pregunta_norm or "cargo" in pregunta_norm or any(c_norm in pregunta_norm for c_norm in CARGOS_VALIDOS_NORM.keys()):
            df = df_responsables.copy()
            if proyecto_norm: df = df[df["Proyecto_norm"] == proyecto_norm]
            cargo_encontrado = None
            for cargo_norm, cargo_real in CARGOS_VALIDOS_NORM.items():
                if cargo_norm in pregunta_norm: cargo_encontrado = cargo_real; break
            if cargo_encontrado and 'Cargo' in df.columns: df = df[df['Cargo']==cargo_encontrado]
            if df.empty: return f"❌ No se encontró responsable ({cargo_encontrado or 'cualquiera'}) en {proyecto or 'todos'}", None, None, 'general', None
            return f"👤 Responsables ({cargo_encontrado or 'todos'}) en {proyecto or 'todos'}:", df, None, 'general', None

        # Restricciones
        if any(k in pregunta_norm for k in ["restriccion","restricción","problema"]):
            df = df_restricciones.copy()
            if proyecto_norm: df = df[df["Proyecto_norm"]==proyecto_norm]
            tipo_restriccion_preseleccionado='Todas las restricciones'
            if "tipoRestriccion" in df.columns:
                for keyword, tipo_real in MAPEO_RESTRICCION.items():
                    if f"restriccion de {keyword}" in pregunta_norm or f"restricciones de {keyword}" in pregunta_norm:
                        if tipo_real in df["tipoRestriccion"].astype(str).unique().tolist():
                            tipo_restriccion_preseleccionado=tipo_real; break
            if df.empty: return f"❌ No hay restricciones registradas en {proyecto or 'todos'}", None, None, 'general', None
            grafico=None
            if PLOTLY_AVAILABLE and "tipoRestriccion" in df.columns:
                grafico=px.bar(df.groupby("tipoRestriccion").size().reset_index(name="count"),
                               x="tipoRestriccion", y="count", text="count",
                               labels={"tipoRestriccion":"Tipo de Restricción","count":"Cantidad"},
                               color="tipoRestriccion", color_discrete_sequence=px.colors.qualitative.Plotly)
                grafico.update_layout(showlegend=False, xaxis_title="Tipo de Restricción", yaxis_title="Cantidad",
                                      plot_bgcolor='white', paper_bgcolor='white', margin=dict(t=30,l=10,r=10,b=10))
            return f"⚠️ Restricciones en {proyecto or 'todos'}:", df, grafico, 'restricciones', tipo_restriccion_preseleccionado

        # Sostenibilidad
        if any(k in pregunta_norm for k in ["sostenibilidad","edge","sostenible","ambiental"]):
            df=df_sostenibilidad.copy()
            if proyecto_norm: df = df[df["Proyecto_norm"]==proyecto_norm]
            if df.empty: return f"❌ No hay registros de sostenibilidad en {proyecto or 'todos'}", None, None, 'general', None
            return f"🌱 Información de sostenibilidad en {proyecto or 'todos'}:", df, None, 'general', None

        return ("❓ No entendí la pregunta. Usa 'avance de obra', 'avance en diseño', "
                "'estado diseño', 'responsable', 'restricciones' o 'sostenibilidad'."), None, None, 'general', None

# --- ESTADO DE VISTAS ---
if 'current_view' not in st.session_state: st.session_state.current_view='chat'
if 'last_query_result' not in st.session_state: st.session_state.last_query_result=None

# --- INTERFAZ PRINCIPAL ---
if st.session_state.current_view=='chat':
    st.markdown(f'<div class="mar-card"><p style="color:{PALETTE["primary"]}; font-size:18px; font-weight:700;">Consulta Rápida</p>'
                '<p>Escribe tu consulta sobre proyectos. Ej: "restricciones de materiales en Burdeos"</p></div>', unsafe_allow_html=True)
    with st.form("query_form", clear_on_submit=False):
        pregunta = st.text_input("", placeholder="Ej: 'Avance de obra en proyecto Altos del Mar'", key='chat_query')
        enviar = st.form_submit_button("Buscar", key="btn_buscar", type="secondary", use_container_width=True)
    
    if enviar and pregunta:
        if not excel_file:
            st.error("¡Sube el archivo Excel primero!")
        else:
            titulo, df_resultado, grafico, tipo_resultado, tipo_restriccion_preseleccionado = generar_respuesta(pregunta)
            # --- Registrar en Google Sheets ---
            try:
                sheet = init_gsheets("RegistroConsultas")
                resumen = f"{len(df_resultado) if df_resultado is not None else 0} registros"
                registrar_consulta_gsheet(sheet, pregunta, tipo_resultado, None, resumen)
            except Exception as e:
                st.warning(f"No se pudo registrar la consulta en Google Sheets: {e}")

            st.session_state['last_query_result'] = (titulo, df_resultado, grafico, tipo_resultado)

# --- MOSTRAR RESULTADOS ---
if st.session_state.last_query_result:
    titulo, df_resultado, grafico, tipo_resultado = st.session_state.last_query_result
    st.markdown(f'<div class="mar-card" style="margin-top:20px;"><p style="color:{PALETTE["primary"]}; font-size:20px; font-weight:700;">{titulo}</p></div>', unsafe_allow_html=True)
    if df_resultado is not None:
        if grafico: st.plotly_chart(grafico, use_container_width=True)
        st.dataframe(df_resultado.drop(columns=["Proyecto_norm"], errors='ignore'), use_container_width=True)
    else:
        st.error(titulo)
