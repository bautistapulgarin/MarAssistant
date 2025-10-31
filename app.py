import streamlit as st
import pandas as pd
import plotly.express as px
import joblib
import os.path as ospath # Importación corregida: 'os.path' como 'ospath'
import io
import base64
import re
import unicodedata
from time import sleep 
from PIL import Image

# -----------------------------
# 0. CONFIGURACIÓN INICIAL Y ESTILOS
# -----------------------------
st.set_page_config(layout="wide")

# Paleta de colores
PALETTE = {"primary": "#007BFF", "secondary": "#FF5733"} 
NN_AVAILABLE = True 

# Estilos CSS y Animaciones
st.markdown(
    """
    <style>
    .title { font-size: 32px; font-weight: 900; color: #1a1a1a; margin-bottom: 5px; }
    .subtitle { font-size: 16px; font-weight: 500; color: #6c757d; }
    .mar-card { background-color: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08); margin-bottom: 20px; }
    
    @keyframes floatDown { 0% { transform: translateY(-50px); opacity: 0.05; } 100% { transform: translateY(100vh); opacity: 0.1; } }
    @keyframes floatY { 0% { transform: translateY(0); } 50% { transform: translateY(10px); } 100% { transform: translateY(0); } }
    </style>
    """, unsafe_allow_html=True
)

# Animaciones HTML
ANIMATION_HTML = ""
ANIMATION_HTML += ''.join([f'<div style="position:fixed; top:{t}%; right:{r}%; font-size:{s}px; opacity:0.1; animation:floatDown {a}s linear infinite; z-index:9999;">❄️</div>' for t, r, s, a in [(0, 5, 30, 15), (10, 7, 28, 18), (20, 6, 25, 16)]])
ANIMATION_HTML += ''.join([f'<div style="position:fixed; bottom:{b}%; left:{l}%; font-size:{s}px; opacity:1; animation:floatY {a}s ease-in-out infinite; z-index:9999;">🎃</div>' for b, l, s, a in [(5, 8, 22, 3), (8, 10, 20, 2.8)]])
st.markdown(ANIMATION_HTML, unsafe_allow_html=True)

# -----------------------------
# 1. CARGA DE MODELO Y UTILIDADES
# -----------------------------
MODELO_NN, SCALER_NN, FEATURES_NN = None, None, None
MODEL_PATHS = {
    "model": ospath.join("assets", "mlp_contratos.joblib"),
    "scaler": ospath.join("assets", "scaler_contratos.joblib"), # Corregido: antes 'ospathath'
    "features": ospath.join("assets", "mlp_features.joblib"),
}

try:
    if all(ospath.exists(p) for p in MODEL_PATHS.values()):
        @st.cache_resource
        def load_mlp_artifacts():
            return (joblib.load(MODEL_PATHS[k]) for k in ["model", "scaler", "features"])

        MODELO_NN, SCALER_NN, FEATURES_NN = load_mlp_artifacts()
    else:
        NN_AVAILABLE = False
        st.sidebar.warning("Faltan archivos del MLP en 'assets'. El predictor no estará disponible.")
except Exception as e:
    NN_AVAILABLE = False
    st.sidebar.error(f"Error al cargar el MLP o artefactos: {e}")

# Inicializar el estado de sesión
for key, default in [('current_view', 'chat'), ('prediction_result', None)]:
    if key not in st.session_state:
        st.session_state[key] = default

# LÓGICA DE VISTAS
def set_view(view_name, reset_prediction=True, clear_filters=False):
    st.session_state.current_view = view_name
    if reset_prediction: st.session_state.pop('prediction_result', None)
    if clear_filters:
        for key in ['filtro_restriccion', 'tipo_restriccion_preseleccionado']:
            st.session_state.pop(key, None) 
    st.rerun()

switch_to_predictor = lambda: set_view('predictor', clear_filters=False)
switch_to_chat = lambda: set_view('chat', clear_filters=True)

# -----------------------------
# 2. HEADER Y SIDEBAR
# -----------------------------
logo_path = ospath.join("assets", "logoMar.png")
col_header_title, col_header_button = st.columns([7, 1.5])

with col_header_title:
    try:
        logo_img = Image.open(logo_path)
        buffered = io.BytesIO(); logo_img.save(buffered, format="PNG")
        img_b64 = base64.b64encode(buffered.getvalue()).decode()
        HTML_HEADER = f"""
        <div style="display:flex; align-items:center; gap:25px; margin-bottom:30px; padding-top:10px;">
            <img src="data:image/png;base64,{img_b64}" style="height:120px; width:auto;"/>
            <div><p class="title">Sistema Integrado de Información de Proyectos</p>
                 <p class="subtitle">Asistente para el Seguimiento y Control</p></div>
        </div>
        """
        st.markdown(HTML_HEADER, unsafe_allow_html=True)
    except Exception:
        st.markdown('<p class="title">Sistema Integrado de Información de Proyectos</p>', unsafe_allow_html=True)

with col_header_button:
    st.markdown("<div style='height:75px;'></div>", unsafe_allow_html=True) 
    if NN_AVAILABLE:
        st.button("Pronóstico", key="btn_prediccion", type="secondary", use_container_width=True, on_click=switch_to_predictor)
    else:
        st.warning("MLP no disponible.")
        
# SIDEBAR
st.sidebar.markdown(f'<p style="color:{PALETTE["primary"]}; font-size: 24px; font-weight: 700; margin-bottom: 0px;">Herramientas</p>', unsafe_allow_html=True)
st.sidebar.subheader("Cargas de Datos")
excel_file = st.sidebar.file_uploader("Sube tu archivo Excel (.xlsx)", type=["xlsx"])
img_file = st.sidebar.file_uploader("Sube imagen splash (opcional)", type=["png", "jpg", "jpeg"])
st.sidebar.markdown("---")

# SPLASH SCREEN
placeholder = st.empty()
if img_file:
    try:
        img_file.seek(0); img_b64 = base64.b64encode(img_file.read()).decode()
        splash_html = f"""
        <div style="position: fixed; top: 0; left: 0; width: 100%; height: 100vh; background-color: white; display: flex; justify-content: center; align-items: center; z-index: 9999;">
            <div style="text-align:center; padding: 20px; border-radius: 12px;">
                <img src="data:image/png;base64,{img_b64}" style="width:180px; max-width:60vw; height:auto; display:block; margin:0 auto;">
                <p style="margin-top: 20px; color: {PALETTE['primary']}; font-size: 20px; font-weight: 600;">Cargando...</p>
            </div>
        </div>
        """
        placeholder.markdown(splash_html, unsafe_allow_html=True)
        sleep(1); placeholder.empty()
    except Exception:
        placeholder.empty()

# -----------------------------
# 3. LECTURA, NORMALIZACIÓN Y LÓGICA DE CONSULTA
# -----------------------------
HOJAS_REQUERIDAS = ["Avance", "Responsables", "Restricciones", "Sostenibilidad", "AvanceDiseño", "InventarioDiseño"]
dfs = {} 
df_avance, df_responsables, df_restricciones, df_sostenibilidad, df_avance_diseno, df_inventario_diseno = [None] * 6

if not excel_file:
    if st.session_state.current_view == 'chat':
        st.info("Sube el archivo Excel en la barra lateral para empezar a consultar los proyectos.")
else:
    try:
        for sheet in HOJAS_REQUERIDAS:
            excel_file.seek(0)
            dfs[sheet] = pd.read_excel(excel_file, sheet_name=sheet)
        st.sidebar.success("✅ Hojas cargadas correctamente")
    except Exception as e:
        st.sidebar.error(f"Error al leer una o varias hojas: {e}")
        st.stop()
    
    df_avance, df_responsables, df_restricciones, df_sostenibilidad, df_avance_diseno, df_inventario_diseno = [dfs.get(s) for s in HOJAS_REQUERIDAS]

    # Funciones de normalización
    def normalizar_texto(texto):
        texto = str(texto).lower()
        texto = re.sub(r"[.,;:%]", "", texto)
        return re.sub(r"\s+", " ", texto).strip()

    def quitar_tildes(texto):
        return ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')

    # Normalización de Proyectos
    proyectos_list = []
    CRITICAS = ["Avance", "Responsables", "Restricciones", "Sostenibilidad"] 
    for df_name, df in zip(HOJAS_REQUERIDAS, [df_avance, df_responsables, df_restricciones, df_sostenibilidad, df_avance_diseno, df_inventario_diseno]):
        if "Proyecto" not in df.columns:
            if df_name in CRITICAS: st.stop() 
            df["Proyecto_norm"] = "" 
        else:
            df["Proyecto_norm"] = df["Proyecto"].astype(str).apply(lambda x: quitar_tildes(normalizar_texto(x)))
            proyectos_list.append(df["Proyecto"].astype(str))

    all_projects = pd.concat(proyectos_list).dropna().unique() if proyectos_list else []
    projects_map = {quitar_tildes(normalizar_texto(p)): p for p in set(all_projects)}

    def extraer_proyecto(texto):
        texto_norm = quitar_tildes(normalizar_texto(texto))
        for norm in sorted(projects_map.keys(), key=len, reverse=True):
            if re.search(rf'(^|\W){re.escape(norm)}($|\W)', texto_norm, flags=re.UNICODE) or norm in texto_norm:
                return projects_map[norm], norm
        return None, None

    # Mapeo de Restricciones y Cargos
    MAPEO_RESTRICCION = {"material": "Materiales", "diseno": "Diseño", "contrato": "Contratos", "permisos": "Permisos y Licencias", "financiero": "Financiera"}
    CARGOS_VALIDOS = ["Analista de compras", "Analista de Programación", "Arquitecto", "Contralor de proyectos", "Director de obra", "Gerente de proyectos"] 

    # Función principal de lógica de negocio (genera la respuesta del chat)
    def generar_respuesta(pregunta):
        pregunta_norm = quitar_tildes(normalizar_texto(pregunta))
        proyecto, proyecto_norm = extraer_proyecto(pregunta)
        
        # Mapeo de acciones
        df_map = {
            'avance': (df_avance, "🚧 Avance de obra", ['avance de obra', 'avance obra']),
            'diseno': (df_avance_diseno, "📐 Avance de Diseño", ['avance en diseno', 'avance diseno', 'estado diseno']),
            'restricciones': (df_restricciones, "⚠️ Restricciones", ['restriccion', 'restricción', 'problema']),
            'responsables': (df_responsables, "👤 Responsables", ['responsable', 'cargo']),
            'sostenibilidad': (df_sostenibilidad, "🌱 Información de sostenibilidad", ['sostenibilidad', 'edge', 'sostenible']),
        }

        accion = next((key for key, (_, _, keywords) in df_map.items() if any(kw in pregunta_norm for kw in keywords)), None)
        if not accion:
            return ("❓ No entendí la pregunta. Intenta con 'avance de obra', 'responsable', 'restricciones', etc."), None, None, 'general', None

        df_base, titulo_prefijo, _ = df_map[accion]
        df = df_base.copy()
        
        # Filtrar por Proyecto
        if proyecto_norm and "Proyecto_norm" in df.columns:
            df = df[df["Proyecto_norm"] == proyecto_norm]
        
        if df.empty:
            return f"❌ No hay registros de {accion.replace('_', ' ')} en {proyecto or 'todos'}", None, None, 'general', None

        grafico, tipo_resultado, tipo_restriccion_preseleccionado = None, 'general', 'Todas las restricciones'

        # Lógica Específica para la Acción
        if accion == 'avance' and "Avance" in df.columns and 'Etapa' in df.columns:
            if len(df['Etapa'].unique()) > 1:
                df_sum = df.groupby('Etapa')['Avance'].mean().reset_index()
                grafico = px.bar(df_sum, x="Etapa", y="Avance", text=df_sum["Avance"].apply(lambda x: f'{x:.1f}%'))
        
        elif accion == 'responsables':
            cargo_encontrado = next((c for c in CARGOS_VALIDOS if quitar_tildes(normalizar_texto(c)) in pregunta_norm), None)
            if cargo_encontrado and 'Cargo' in df.columns:
                df = df[df['Cargo'] == cargo_encontrado]
                titulo_prefijo = f"👤 Responsables ({cargo_encontrado})"
                if df.empty: return f"❌ No se encontró responsable ({cargo_encontrado})", None, None, 'general', None

        elif accion == 'restricciones':
            tipo_encontrado = next((
                tipo_real for keyword, tipo_real in MAPEO_RESTRICCION.items()
                if keyword in pregunta_norm
            ), None)

            if tipo_encontrado and "tipoRestriccion" in df.columns and tipo_encontrado in df["tipoRestriccion"].astype(str).unique():
                tipo_restriccion_preseleccionado = tipo_encontrado

            if "tipoRestriccion" in df.columns:
                df_rest = df.groupby("tipoRestriccion").size().reset_index(name="count")
                grafico = px.bar(df_rest, x="tipoRestriccion", y="count", text="count")
            
            tipo_resultado = 'restricciones'

        return f"{titulo_prefijo} en {proyecto or 'todos'}:", df, grafico, tipo_resultado, tipo_restriccion_preseleccionado


# -----------------------------
# 4. FUNCIÓN DE PREDICCIÓN (MLP)
# -----------------------------
def mostrar_predictor_mlp():
    if not MODELO_NN: st.error("No se pudo cargar el modelo de predicción de contratos (MLP)."); return

    col_pred_title, col_pred_back = st.columns([6, 1.5])
    with col_pred_title:
        st.markdown(f'<div class="mar-card" style="margin-bottom: 0px;"><p style="color:{PALETTE["primary"]}; font-size: 22px; font-weight:700; margin:0 0 8px 0;">🔮 Previsión de Cumplimiento de Contratos</p>'
                    '<p style="margin:0 0 0 0;">Ingresa los parámetros del contrato para predecir la probabilidad de cumplimiento a tiempo.</p></div>', unsafe_allow_html=True)
    with col_pred_back:
        st.markdown("<div style='height:42px;'></div>", unsafe_allow_html=True) 
        st.button("⬅️ Devolver", key="btn_devolver", type="secondary", use_container_width=True, on_click=switch_to_chat)

    st.markdown("<div style='height:15px;'></div>", unsafe_allow_html=True)

    with st.form("mlp_predictor_form_body", clear_on_submit=False):
        cols = st.columns([2, 2, 3, 3, 3]) 
        with cols[0]: dias_input = st.number_input("Días de legalización esperados", min_value=1, value=15, step=1)
        with cols[1]: reprog_input = st.number_input("Número de reprogramaciones", min_value=0, value=0, step=1)
        with cols[2]: prioridad_input = st.selectbox("Prioridad", options=['Alta', 'Media', 'Baja'])
        with cols[3]: contrato_input = st.selectbox("Tipo de contrato", options=['Obra', 'Suministro', 'Servicios', 'Subcontrato'])
        with cols[4]: cnc_input = st.selectbox("Causa de retraso (CNCCompromiso)", options=['Aprobación interna', 'Proveedor', 'Legalización interna', 'Financiera'])

        predict_button = st.form_submit_button("🚀 Predecir", type="primary", on_click=lambda: st.session_state.pop('prediction_result', None))

    if predict_button:
        try:
            nuevo_df = pd.DataFrame([[dias_input, reprog_input, prioridad_input, contrato_input, cnc_input]], 
                                    columns=['dias_legalizacion_esperados', 'numero_reprogramaciones', 'prioridad', 'tipo_contrato', 'CNCCompromiso'])
            nuevo_df = pd.get_dummies(nuevo_df)
            for col in FEATURES_NN:
                if col not in nuevo_df.columns: nuevo_df[col] = 0
            nuevo_df = nuevo_df[FEATURES_NN]

            cols_to_scale = ['dias_legalizacion_esperados', 'numero_reprogramaciones']
            nuevo_df[cols_to_scale] = SCALER_NN.transform(nuevo_df[cols_to_scale])
            
            prob_cumplimiento = MODELO_NN.predict_proba(nuevo_df)[0][1]
            prediccion = MODELO_NN.predict(nuevo_df)[0]
            st.session_state.prediction_result = {'prediccion': prediccion, 'prob_cumplimiento': prob_cumplimiento}

        except Exception as e:
            st.error(f"Error al procesar la predicción: {e}")
            st.info("Revisa si el formato de los datos es compatible.")
            st.session_state.pop('prediction_result', None)

    # Lógica de Visualización de Resultados
    if st.session_state.get('prediction_result') is not None:
        prediccion = st.session_state['prediction_result']['prediccion']
        prob_cumplimiento = st.session_state['prediction_result']['prob_cumplimiento'] * 100
        
        emoji, titulo_res, mensaje = ("✅", "Cumplido a tiempo", "¡Parece que este contrato va bien!") if prediccion == 1 else ("⚠️", "Probable reprogramación", "Se requiere seguimiento.")

        st.markdown("<div class='mar-card' style='margin-top:20px;'>", unsafe_allow_html=True)
        st.markdown(f"### Predicción: {emoji} {titulo_res}")
        st.markdown(f"La probabilidad de **cumplimiento** es del **`{prob_cumplimiento:.2f}%`**. {mensaje}")
        st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("<div style='height: 100px;'></div>", unsafe_allow_html=True)

# -----------------------------
# 5. LÓGICA DE VISTAS PRINCIPALES Y CHAT UI
# -----------------------------
if st.session_state.current_view == 'predictor':
    mostrar_predictor_mlp()
    
elif st.session_state.current_view == 'chat':
    # INTERFAZ DE CONSULTA
    st.markdown(f'<div class="mar-card"><p style="color:{PALETTE["primary"]}; font-size: 18px; font-weight:700; margin:0 0 8px 0;">Consulta Rápida</p></div>', unsafe_allow_html=True)
    
    with st.form("query_form", clear_on_submit=False):
        col_input, col_enviar, col_voz = st.columns([6, 1.2, 1])
        with col_input:
            pregunta = st.text_input(label="", placeholder="Ej: 'Avance de obra en Altos del Mar'", label_visibility="collapsed", key='chat_query')
        with col_enviar:
            enviar = st.form_submit_button("Buscar", key="btn_buscar", type="secondary", use_container_width=True) 
        with col_voz:
            st.form_submit_button("🎤 Voz", key="voz", help="Activar entrada por voz", type="secondary", use_container_width=True)

    # Lógica de procesamiento de la pregunta
    if enviar and pregunta and excel_file:
        st.session_state['last_query_text'] = pregunta
        titulo, df_resultado, grafico, tipo_resultado, tipo_restriccion_preseleccionado = generar_respuesta(pregunta)
        st.session_state['last_query_result'] = (titulo, df_resultado, grafico, tipo_resultado)
        
        if tipo_resultado == 'restricciones' and tipo_restriccion_preseleccionado != 'Todas las restricciones':
            st.session_state['tipo_restriccion_preseleccionado'] = tipo_restriccion_preseleccionado
        else:
            st.session_state.pop('tipo_restriccion_preseleccionado', None) 
        
        st.session_state.pop('filtro_restriccion', None) 
        st.rerun()

    # MOSTRAR RESULTADOS
    if st.session_state.get('last_query_result'):
        titulo, df_resultado, grafico, tipo_resultado = st.session_state['last_query_result'] 
        st.markdown(f'<div class="mar-card" style="margin-top:20px;"><p style="color:{PALETTE["primary"]}; font-size: 20px; font-weight:700; margin:0 0 8px 0;">{titulo}</p></div>', unsafe_allow_html=True)

        if tipo_resultado == 'restricciones' and df_resultado is not None:
            tipos_restriccion = ['Todas las restricciones'] + df_resultado["tipoRestriccion"].astype(str).unique().tolist() if "tipoRestriccion" in df_resultado.columns else ['Todas las restricciones']
            
            default_key = st.session_state.get('tipo_restriccion_preseleccionado', 'Todas las restricciones')
            default_index = tipos_restriccion.index(default_key) if default_key in tipos_restriccion else 0
            filtro_restriccion = st.selectbox("Filtro por Tipo de Restricción:", options=tipos_restriccion, index=default_index, key='filtro_restriccion')

            df_filtrado = df_resultado.copy()
            if filtro_restriccion != 'Todas las restricciones' and "tipoRestriccion" in df_filtrado.columns:
                df_filtrado = df_filtrado[df_filtrado["tipoRestriccion"] == filtro_restriccion]

            # CÁLCULO DE MÉTRICAS 
            if all(col in df_filtrado.columns for col in ["FechaCompromisoActual", "FechaCompromisoInicial"]):
                df_valido = df_filtrado.assign(
                    FechaCompromisoActual=pd.to_datetime(df_filtrado['FechaCompromisoActual'], errors='coerce'),
                    FechaCompromisoInicial=pd.to_datetime(df_filtrado['FechaCompromisoInicial'], errors='coerce')
                ).dropna(subset=['FechaCompromisoActual', 'FechaCompromisoInicial']).assign(
                    DiasDiferencia=lambda x: (x['FechaCompromisoActual'] - x['FechaCompromisoInicial']).dt.days
                ).dropna(subset=['DiasDiferencia'])
                
                restricciones_reprogramadas = df_valido[df_valido['DiasDiferencia'] > 0]
                total_restricciones = len(df_valido)
                total_restricciones_reprogramadas = len(restricciones_reprogramadas)
                promedio_dias_retraso = restricciones_reprogramadas['DiasDiferencia'].mean()
            else:
                total_restricciones = len(df_filtrado); total_restricciones_reprogramadas = 0; promedio_dias_retraso = 0

            # VISUALIZACIÓN DE RESTRICCIONES (Tarjeta y Tabla)
            col_dias, col_filtro = st.columns([1, 2])
            
            with col_dias:
                if total_restricciones > 0:
                    data = {'Métrica': ['Total Restricciones (con Fechas)', 'Restricciones Reprogramadas (Días > 0)', 'Promedio Días de Retraso (Por Reprogramada)'],
                            'Valor': [total_restricciones, total_restricciones_reprogramadas, f"{promedio_dias_retraso:,.2f}" if promedio_dias_retraso > 0 else "0.00"]}
                    st.markdown('<div class="mar-card" style="background-color:#fff3e0; padding: 15px;">📅 **Resumen de Demoras por Reprogramación**', unsafe_allow_html=True)
                    st.dataframe(pd.DataFrame(data), hide_index=True, use_container_width=True)
                    st.markdown('<p style="font-size:12px; margin:0; color:#8d6e63;">*Datos filtrados por el tipo de restricción actual.</p></div>', unsafe_allow_html=True)
                else: st.info("No hay datos de fechas válidos para calcular la diferencia de días.")

            with col_filtro:
                st.markdown(f'<p style="font-weight:600; color:{PALETTE["primary"]}; margin-top:15px; margin-bottom:10px;">Detalle de Restricciones ({len(df_filtrado)} encontradas)</p>', unsafe_allow_html=True)
                
                df_display = df_filtrado.drop(columns=["Proyecto_norm"], errors='ignore')
                
                # Intentar añadir 'Diferencia (Días)' si se pudo calcular
                if 'DiasDiferencia' in locals().get('df_valido', {}).columns:
                    df_display['Diferencia (Días)'] = df_valido['DiasDiferencia']

                columns_to_show_and_rename = {'Actividad': 'Actividad', 'Restriccion': 'Restricción', 'numeroReprogramacionesCompromiso': 'Núm. Reprog.', 'Descripción': 'Descripción', 
                                              'tipoRestriccion': 'Tipo Restricción', 'FechaCompromisoInicial': 'F. Inicial', 'FechaCompromisoActual': 'F. Actual', 
                                              'Responsable': 'Responsable', 'Comentarios': 'Comentarios', 'Diferencia (Días)': 'Diferencia (Días)'}
                
                df_display = df_display.filter(items=columns_to_show_and_rename.keys()).rename(columns=columns_to_show_and_rename)
                st.dataframe(df_display, use_container_width=True)
                
            if grafico:
                st.markdown('<div class="mar-card" style="margin-top: 25px;">', unsafe_allow_html=True)
                st.markdown(f'<p style="font-weight:600; color:{PALETTE["primary"]}; margin-bottom:5px;">Conteo por Tipo de Restricción (General)</p>', unsafe_allow_html=True)
                st.plotly_chart(grafico, use_container_width=True) 
                st.markdown('</div>', unsafe_allow_html=True)
                
        # Caso general (Avance, Responsables, etc.)
        else:
            if df_resultado is not None:
                st.markdown(f'<div class="mar-card" style="margin-top:0px;">', unsafe_allow_html=True)
                if grafico: st.plotly_chart(grafico, use_container_width=True)
                st.dataframe(df_resultado.drop(columns=["Proyecto_norm"], errors='ignore'), use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.error(titulo) 
                
        st.markdown("<div style='height: 100px;'></div>", unsafe_allow_html=True)
