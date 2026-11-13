import pandas as pd
import os

EXCEL_FILE = "media_tracker_db.xlsx"

def inicializar_excel():
    """Crea el archivo Excel con los encabezados necesarios si no existe."""
    if not os.path.exists(EXCEL_FILE):
        columnas = [
            "ID", "Título", "Tipo", "Género", "Año", "Duración Total", 
            "Review", "Letterboxd", "IMDb Rating", "Rotten Tomatoes", 
            "TMDB Rating", "Serie Graph", "Director", "Actores Principales", 
            "Fecha/Hora Registro"
        ]
        df_vacio = pd.DataFrame(columns=columnas)
        df_vacio.to_excel(EXCEL_FILE, index=False, engine='openpyxl')

def cargar_excel():
    """Carga la base de datos de Excel de manera segura."""
    inicializar_excel()
    try:
        df = pd.read_excel(EXCEL_FILE, engine='openpyxl')
        return df
    except Exception:
        inicializar_excel()
        return pd.read_excel(EXCEL_FILE, engine='openpyxl')

def guardar_registro(nuevo_registro):
    """Agrega un nuevo registro al archivo Excel."""
    df = cargar_excel()
    nuevo_df = pd.DataFrame([nuevo_registro])
    df = pd.concat([df, nuevo_df], ignore_index=True)
    df.to_excel(EXCEL_FILE, index=False, engine='openpyxl')

def actualizar_calificacion(id_registro, nueva_nota):
    """Actualiza la reseña personal de un registro existente por su ID."""
    df = cargar_excel()
    if not df.empty and id_registro in df['ID'].values:
        df.loc[df['ID'] == id_registro, 'Review'] = nueva_nota
        df.to_excel(EXCEL_FILE, index=False, engine='openpyxl')

def eliminar_registro(id_registro):
    """Elimina un registro de la base de datos por su ID."""
    df = cargar_excel()
    if not df.empty and id_registro in df['ID'].values:
        df = df[df['ID'] != id_registro]
        df.to_excel(EXCEL_FILE, index=False, engine='openpyxl')
        
import os
import pandas as pd

def obtener_ruta_usuario(nombre_usuario):
    limpio = "".join(c for c in nombre_usuario if c.isalnum() or c in ('_', '-')).lower()
    
    # Si el usuario es Ricardo o rickdiaz, usamos directamente tu base de datos original
    if limpio in ["ricardo", "rickdiaz"]:
        return "media_tracker_db.xlsx", "watchlist.json"
        
    # Para cualquier otro usuario nuevo, se le asigna su propio archivo independiente
    return f"media_tracker_db_{limpio}.xlsx", f"watchlist_{limpio}.json"

def cargar_excel_usuario(nombre_usuario):
    db_path, _ = obtener_ruta_usuario(nombre_usuario)
    
    if not os.path.exists(db_path):
        df = pd.DataFrame(columns=[
            "ID", "Título", "Tipo", "Género", "Año", "Duración Total", 
            "Review", "Letterboxd", "IMDb Rating", "Rotten Tomatoes", 
            "TMDB Rating", "Serie Graph", "Director", "Actores Principales", "Fecha/Hora Registro"
        ])
        df.to_excel(db_path, index=False)
        return df
        
    return pd.read_excel(db_path)

def guardar_registro_usuario(nombre_usuario, reg):
    db_path, _ = obtener_ruta_usuario(nombre_usuario)
    df = cargar_excel_usuario(nombre_usuario)
    nuevo_df = pd.DataFrame([reg])
    df = pd.concat([df, nuevo_df], ignore_index=True)
    df.to_excel(db_path, index=False)

def eliminar_registro_usuario(nombre_usuario, id_registro):
    db_path, _ = obtener_ruta_usuario(nombre_usuario)
    df = cargar_excel_usuario(nombre_usuario)
    df = df[df['ID'] != id_registro]
    df.to_excel(db_path, index=False)