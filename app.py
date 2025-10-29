# app.py
# Mar Assistant - versión con autocompletado estilo "Google" (componente HTML/JS integrado)
import streamlit as st
from PIL import Image
import pandas as pd
import re
import unicodedata
import time
import base64
import os
import io
import json
import streamlit.components.v1 as components

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
# FUNCIONES DE NORMALIZACIÓN
# -----------------------------
def normalizar_texto(texto):
    texto = str(texto).lower()
    texto = re.sub(r"[.,;:%]", "", texto)
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()

def quitar_tildes(texto):
    return ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')

# -----------------------------
# PALABRAS CLAVE (base para autocompletado)
# -----------------------------
PALABRAS_CLAVE = [
    "estado de diseño", "inventario de diseño",
    "avance de diseño", "avance en diseño",
    "avance diseño", "avance diseno", "avance de diseno",
    "avance de obra", "avance obra", "avance en obra",
    "restricciones", "problemas", "restriccion", "restricción",
    "responsable", "quien es el responsable", "quién es el responsable",
    "sostenibilidad", "edge", "ambiental", "proyectos sostenibles",
    "avance", "estado diseño", "inventario diseno"
]

# -----------------------------
# CSS GLOBAL (pequeño) para apariencia
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
.mar-card {{
    background-color: white;
    padding: var(--card-padding);
    border-radius: var(--card-radius);
    box-shadow: 0 6px 18px rgba(21,72,114,0.06);
    margin-bottom: 20px;
}}
.search-box {{
    max-width: 880px;
    margin: 8px 0 16px 0;
}}
.suggestion-item:hover {{
    background-color: #f1f5f9;
    cursor: pointer;
}}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# SIDEBAR: Uploads (igual que tu app)
# -----------------------------
st.sidebar.title("Herramientas")
st.sidebar.subheader("Cargas")
excel_file = st.sidebar.file_uploader("Sube tu archivo Excel (.xlsx)", type=["xlsx"])
img_file = st.sidebar.file_uploader("Sube imagen splash (opcional)", type=["png", "jpg", "jpeg"])
st.sidebar.markdown("---")
st.sidebar.markdown("💡 Consejo: coloca `assets/logoMar.png` junto a este archivo para mostrar el logo correctamente.")

# -----------------------------
# LECTURA DE EXCEL (si existe)
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
        # Algunos nombres de hojas pueden tener acento; intentamos alternativas
        try:
            df_avance_diseno = pd.read_excel(excel_file, sheet_name="AvanceDiseño")
        except Exception:
            excel_file.seek(0)
            try:
                df_avance_diseno = pd.read_excel(excel_file, sheet_name="AvanceDiseno")
            except Exception:
                df_avance_diseno = pd.DataFrame()
        excel_file.seek(0)
        try:
            df_inventario_diseno = pd.read_excel(excel_file, sheet_name="InventarioDiseño")
        except Exception:
            excel_file.seek(0)
            try:
                df_inventario_diseno = pd.read_excel(excel_file, sheet_name="InventarioDiseno")
            except Exception:
                df_inventario_diseno = pd.DataFrame()

        st.sidebar.success("✅ Hojas cargadas correctamente")
    except Exception as e:
        st.sidebar.error(f"Error al leer una o varias hojas: {e}")
        st.stop()
else:
    # Crear dataframes vacíos para que el resto del código no falle
    df_avance = pd.DataFrame()
    df_responsables = pd.DataFrame()
    df_restricciones = pd.DataFrame()
    df_sostenibilidad = pd.DataFrame()
    df_avance_diseno = pd.DataFrame()
    df_inventario_diseno = pd.DataFrame()

# -----------------------------
# Normalización de nombres de proyecto (si existen)
# -----------------------------
for df_name, df in [("Avance", df_avance), ("Responsables", df_responsables),
                    ("Restricciones", df_restricciones), ("Sostenibilidad", df_sostenibilidad)]:
    if not df.empty and "Proyecto" not in df.columns:
        st.sidebar.error(f"La hoja '{df_name}' no contiene la columna 'Proyecto'.")
        st.stop()

for df in [df_avance, df_responsables, df_restricciones, df_sostenibilidad]:
    if not df.empty:
        df["Proyecto_norm"] = df["Proyecto"].astype(str).apply(lambda x: quitar_tildes(normalizar_texto(x)))

all_projects = []
if not df_avance.empty:
    all_projects += df_avance["Proyecto"].astype(str).tolist()
if not df_responsables.empty:
    all_projects += df_responsables["Proyecto"].astype(str).tolist()
if not df_restricciones.empty:
    all_projects += df_restricciones["Proyecto"].astype(str).tolist()
if not df_sostenibilidad.empty:
    all_projects += df_sostenibilidad["Proyecto"].astype(str).tolist()

all_projects = [p for p in pd.unique(all_projects) if pd.notna(p)]
projects_map = {quitar_tildes(normalizar_texto(p)): p for p in all_projects}

# Agregar nombres de proyectos a las sugerencias para ser más amigable
suggestions_list = PALABRAS_CLAVE.copy()
for p in all_projects:
    if p and str(p).strip():
        suggestions_list.append(str(p))
        suggestions_list.append(quitar_tildes(normalizar_texto(str(p))))

# garantizar unicidad y orden
suggestions_list = sorted(list(dict.fromkeys(suggestions_list)), key=lambda x: (-len(x), x))

# -----------------------------
# FUNCION DE RESPUESTA (igual que la tuya)
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

        grafico = None
        if PLOTLY_AVAILABLE and "tipoRestriccion" in df.columns:
            grafico = px.bar(
                df.groupby("tipoRestriccion").size().reset_index(name="count"),
                x="tipoRestriccion",
                y="count",
                text="count",
                labels={"tipoRestriccion": "Tipo de Restricción", "count": "Cantidad"},
                color="tipoRestriccion",
                color_discrete_sequence=px.colors.qualitative.Pastel
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
                    <p style='margin:0;font-size:24px;font-weight:800;color:{PALETTE['primary']};'>Sistema Integrado de Información de Proyectos</p>
                    <p style="margin:4px 0 0 0;color:#34495e;"> Asistente para el Seguimiento y Control — Constructora Marval</p>
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
# AUTOCOMPLETADO: componente HTML + JS (modo flotante moderno)
# -----------------------------
# Pasamos la lista de sugerencias como JSON al HTML
suggestions_json = json.dumps(suggestions_list)

# HTML + JS: todo dentro de una cadena triple-quoted para evitar errores de sintaxis en Python
html_component = f'''
<div class='mar-card search-box'>
  <label style='font-weight:700;color:{PALETTE["primary"]};display:block;margin-bottom:6px;'>Consulta rápida</label>
  <div style='position:relative;'>
    <input id='search' type='text' placeholder='Escribe tu pregunta aquí' autocomplete='off'
      style='width:100%; padding:12px 14px; border-radius:8px; border:1px solid rgba(21,72,114,0.2); font-size:15px; height:44px;' />
    <button id='sendBtn' style='position:absolute;right:6px;top:6px;height:32px;border-radius:8px;padding:0 12px;border:none;background:{PALETTE["primary"]};color:white;font-weight:600;'>Enviar</button>

    <div id='suggestions' style='position:absolute; left:0; right:0; top:52px; background:white; border-radius:8px; box-shadow:0 8px 30px rgba(0,0,0,0.08); max-height:260px; overflow:auto; display:none; z-index:9999;'>
    </div>
  </div>
  <small style='color:#6b7280;'>Sugerencias mientras escribes. Haz clic para autocompletar.</small>
</div>

<script>
const suggestions = {suggestions_json};
const input = document.getElementById('search');
const sugBox = document.getElementById('suggestions');
const sendBtn = document.getElementById('sendBtn');

function escapeHtml(text) {{
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}}

function filterSuggestions(query) {{
  if(!query) return [];
  const q = query.trim().toLowerCase();
  let results = suggestions.filter(s => s.toLowerCase().startsWith(q));
  if(results.length === 0) {{
    results = suggestions.filter(s => s.toLowerCase().includes(q));
  }}
  return results.slice(0, 40);
}}

function renderSuggestions(items) {{
  if(!items || items.length === 0) {{
    sugBox.style.display = 'none';
    sugBox.innerHTML = '';
    return;
  }}
  sugBox.innerHTML = items.map(it =>
    `<div class='suggestion-item' data-value="${{escapeHtml(it)}}" style='padding:10px 12px;border-bottom:1px solid #f3f4f6;'>${{escapeHtml(it)}}</div>`
  ).join('');
  sugBox.style.display = 'block';

  // attach click handlers
  Array.from(sugBox.querySelectorAll('.suggestion-item')).forEach(el => {{
    el.addEventListener('click', function(e) {{
      const v = this.getAttribute('data-value');
      input.value = v;
      submitQuery(v);
    }});
  }});
}}

function submitQuery(value=null) {{
  const v = value !== null ? value : input.value;
  const url = window.location.pathname + '?q=' + encodeURIComponent(v);
  window.location.href = url;
}}

input.addEventListener('input', function(e) {{
  const q = e.target.value;
  if(!q || q.trim().length === 0) {{
    renderSuggestions([]);
    return;
  }}
  const items = filterSuggestions(q);
  renderSuggestions(items);
}});

// close suggestions when clicking outside the search box
document.addEventListener('click', function(e) {{
  const container = document.querySelector('.search-box');
  if (!container.contains(e.target)) {{
    sugBox.style.display = 'none';
  }}
}});

// support pressing Enter to submit
input.addEventListener('keydown', function(e) {{
  if(e.key === 'Enter') {{
    e.preventDefault();
    submitQuery();
  }}
}});

// send button action
sendBtn.addEventListener('click', function() {{
  submitQuery();
}});

// if query param ?q= exists, fill input (useful when returning)
(function(){{
  const params = new URLSearchParams(window.location.search);
  const q = params.get('q');
  if(q) {{
    input.value = decodeURIComponent(q);
  }}
}})();
</script>
'''

# Renderizamos el componente (alto suficiente para mostrarse, el HTML controla su propio scroll)
components.html(html_component, height=160)

# -----------------------------
# Tomamos la query param ?q= y la usamos
# -----------------------------
query_params = st.experimental_get_query_params()
pregunta = query_params.get('q', [''])[0].strip()

# Mostrar la consulta actual (si existe)
if pregunta:
    st.markdown(f"<div class='mar-card'><strong style='color:{PALETTE['primary']};'>Consulta:</strong> {pregunta}</div>", unsafe_allow_html=True)

# -----------------------------
# Si existe pregunta, procesarla con la función generar_respuesta
# -----------------------------
if pregunta:
    respuesta = generar_respuesta(pregunta)

    if len(respuesta) == 3:
        texto, resultado, grafico = respuesta
    else:
        texto, resultado = respuesta
        grafico = None

    st.markdown(
        f"<div class='mar-card'><p style='color:{PALETTE['primary']}; font-weight:700; margin:0 0 8px 0;'>{texto}</p>",
        unsafe_allow_html=True
    )

    if grafico:
        st.plotly_chart(grafico, use_container_width=True)

    if isinstance(resultado, pd.DataFrame) and not resultado.empty:
        max_preview = 200
        if len(resultado) > max_preview:
            st.info(f"Mostrando primeras {max_preview} filas de {len(resultado)}.")
            df_preview = resultado.head(max_preview)
        else:
            df_preview = resultado

        styled_df = df_preview.style.set_table_styles([
            {'selector': 'tr:nth-child(even)', 'props': [('background-color', '#f4f6f8')]},
            {'selector': 'th', 'props': [('background-color', PALETTE['accent']),
                                         ('color', 'white'),
                                         ('font-weight', 'bold')]},
        ])
        st.dataframe(styled_df, use_container_width=True)

# -----------------------------
# FOOTER
# -----------------------------
st.markdown(
    f"<br><hr><p style='font-size:12px;color:#6b7280;'>Mar Assistant • CONSTRUCTORA MARVAL • Versión: 1.0</p>",
    unsafe_allow_html=True
)
