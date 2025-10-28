import pandas as pd
import re

# Cargar archivo Excel
excel_path = "control_obra.xlsx"

# Cargar las hojas
avance_df = pd.read_excel(excel_path, sheet_name="Avance")
responsables_df = pd.read_excel(excel_path, sheet_name="Responsables")
avancediseno_df = pd.read_excel(excel_path, sheet_name="AvanceDiseño")

# Normalizar nombres de columnas (por si acaso)
avance_df.columns = avance_df.columns.str.strip().str.lower()
responsables_df.columns = responsables_df.columns.str.strip().str.lower()
avancediseno_df.columns = avancediseno_df.columns.str.strip().str.lower()

# Unificar nombres de proyectos
avance_df["proyecto"] = avance_df["proyecto"].str.strip().str.upper()
responsables_df["proyecto"] = responsables_df["proyecto"].str.strip().str.upper()
avancediseno_df["proyecto"] = avancediseno_df["proyecto"].str.strip().str.upper()

# Función para detectar hoja según el mensaje
def detectar_hoja(mensaje):
    mensaje = mensaje.lower()
    if any(p in mensaje for p in ["avance diseño", "avancediseño", "avance de diseño"]):
        return "avancediseño"
    else:
        return "avance"

# Función principal
def generar_respuesta(mensaje):
    hoja = detectar_hoja(mensaje)
    
    if hoja == "avancediseño":
        df = avancediseno_df
    else:
        df = avance_df

    proyectos = df["proyecto"].unique()
    coincidencias = [p for p in proyectos if re.search(p, mensaje, re.IGNORECASE)]

    if coincidencias:
        respuestas = []
        for proyecto in coincidencias:
            data_proyecto = df[df["proyecto"].str.contains(proyecto, case=False, na=False)]
            responsable_info = responsables_df[responsables_df["proyecto"].str.contains(proyecto, case=False, na=False)]
            
            if not data_proyecto.empty:
                avance = data_proyecto["avance"].iloc[0] if "avance" in data_proyecto.columns else "No disponible"
                respuestas.append(f"📊 *{proyecto}* → Avance: {avance}")
            
            if not responsable_info.empty:
                nombre = responsable_info["responsable"].iloc[0]
                cargo = responsable_info["cargo"].iloc[0]
                correo = responsable_info["correo"].iloc[0]
                respuestas.append(f"👷 Responsable: {nombre} ({cargo}) - 📧 {correo}")
        return "\n".join(respuestas)
    
    return "No se encontró información para el proyecto especificado."

# Ejemplo de prueba
mensaje = "Muéstrame el avance diseño del proyecto edificio central"
print(generar_respuesta(mensaje))

