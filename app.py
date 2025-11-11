# -----------------------------
# CONFIGURACIÓN DEL ARCHIVO EXCEL DESDE GITHUB
# -----------------------------
GITHUB_EXCEL_URL = "https://raw.githubusercontent.com/bautistapulgarin/MarAssistant/main/data/control_obra.xlsx"

@st.cache_data(ttl=3600)
def load_excel_from_github():
    """Carga el archivo Excel desde GitHub"""
    try:
        st.sidebar.info("📊 Descargando datos desde GitHub...")
        
        # Verificar la URL primero
        st.sidebar.write(f"URL: {GITHUB_EXCEL_URL}")
        
        response = requests.get(GITHUB_EXCEL_URL, timeout=30)
        response.raise_for_status()
        
        # Verificar que sea un archivo Excel
        content_type = response.headers.get('content-type', '')
        if 'spreadsheet' not in content_type and 'excel' not in content_type:
            st.sidebar.warning(f"Tipo de contenido: {content_type}")
        
        # Verificar tamaño del archivo
        content_length = len(response.content)
        st.sidebar.write(f"Tamaño del archivo: {content_length} bytes")
        
        if content_length < 1000:  # Archivo muy pequeño, probablemente error
            return {'success': False, 'error': 'Archivo demasiado pequeño, puede que no sea un Excel válido'}
        
        # Leer el Excel
        excel_content = io.BytesIO(response.content)
        
        # Probar diferentes engines si es necesario
        try:
            df_avance = pd.read_excel(excel_content, sheet_name="Avance", engine='openpyxl')
        except:
            excel_content.seek(0)
            df_avance = pd.read_excel(excel_content, sheet_name="Avance", engine='xlrd')
        
        excel_content.seek(0)
        df_responsables = pd.read_excel(excel_content, sheet_name="Responsables", engine='openpyxl')
        excel_content.seek(0)
        df_restricciones = pd.read_excel(excel_content, sheet_name="Restricciones", engine='openpyxl')
        excel_content.seek(0)
        df_sostenibilidad = pd.read_excel(excel_content, sheet_name="Sostenibilidad", engine='openpyxl')
        excel_content.seek(0)
        df_avance_diseno = pd.read_excel(excel_content, sheet_name="AvanceDiseño", engine='openpyxl')
        excel_content.seek(0)
        df_inventario_diseno = pd.read_excel(excel_content, sheet_name="InventarioDiseño", engine='openpyxl')
        
        st.sidebar.success("✅ Excel cargado correctamente")
        return {
            'avance': df_avance,
            'responsables': df_responsables,
            'restricciones': df_restricciones,
            'sostenibilidad': df_sostenibilidad,
            'avance_diseno': df_avance_diseno,
            'inventario_diseno': df_inventario_diseno,
            'success': True
        }
            
    except Exception as e:
        st.sidebar.error(f"❌ Error detallado: {str(e)}")
        return {'success': False, 'error': str(e)}
