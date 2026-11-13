import pandas as pd
from sklearn.linear_model import LinearRegression
import requests
import api_manager as am

def obtener_recomendaciones_personalizadas(df_vistos):
    """
    Analiza las obras mejor calificadas por el usuario y obtiene recomendaciones balanceadas (películas y series) desde TMDB.
    """
    if df_vistos.empty:
        return []

    # Filtrar obras con calificaciones altas
    mejores_calificaciones = ["Absolute Cinema", "Impresionante", "Genial"]
    if 'Review' in df_vistos.columns:
        df_favoritas = df_vistos[df_vistos['Review'].isin(mejores_calificaciones)]
        if df_favoritas.empty:
            df_favoritas = df_vistos.head(6)
    else:
        df_favoritas = df_vistos.head(6)

    # Recopilar todos los IDs numéricos de TMDB que ya has visto para bloquearlos por completo
    ids_vistos_tmdb = set()
    for _, row in df_vistos.iterrows():
        id_str = str(row.get('ID', ''))
        if 'TMDB_' in id_str:
            num_id = "".join([c for c in id_str if c.isdigit()])
            if num_id:
                ids_vistos_tmdb.add(num_id)

    recomendaciones_peliculas = []
    recomendaciones_series = []

    # Procesar favoritas separando por tipo si es posible, o consultando ambos mundos
    for _, row in df_favoritas.iterrows():
        id_str = str(row.get('ID', ''))
        tipo_obra = str(row.get('Tipo', ''))
        
        if 'TMDB_' in id_str:
            try:
                tmdb_id = "".join([c for c in id_str if c.isdigit()])
                # Determinar si la favorita es película o serie
                media_type = "tv" if ("TV" in id_str or "Serie" in tipo_obra) else "movie"
                
                url_rec = f"{am.BASE_URL}/{media_type}/{tmdb_id}/recommendations?api_key={am.API_KEY}&language=es-ES&page=1"
                res = requests.get(url_rec, timeout=4).json()
                resultados = res.get('results', [])
                
                for item in resultados:
                    item_id_num = str(item.get('id'))
                    
                    # Evitar estrictamente lo que ya está visto en el Excel
                    if item_id_num not in ids_vistos_tmdb:
                        # Asignar el tipo correspondiente
                        if media_type == "movie" or 'title' in item:
                            item['media_type'] = 'movie'
                            recomendaciones_peliculas.append(item)
                        else:
                            item['media_type'] = 'tv'
                            recomendaciones_series.append(item)
            except Exception:
                continue

    # Eliminar duplicados internos
    def limpiar_duplicados(lista):
        vistos = set()
        resultado = []
        for r in lista:
            rid = str(r.get('id'))
            if rid not in vistos:
                vistos.add(rid)
                resultado.append(r)
        return resultado

    peliculas_unicas = limpiar_duplicados(recomendaciones_peliculas)
    series_unicas = limpiar_duplicados(recomendaciones_series)

    # Mezclar inteligentemente: asegurar que aparezcan tanto películas como series
    lista_final = []
    max_len = max(len(peliculas_unicas), len(series_unicas))
    
    for i in range(max_len):
        if i < len(peliculas_unicas):
            lista_final.append(peliculas_unicas[i])
        if i < len(series_unicas):
            lista_final.append(series_unicas[i])

    return lista_final[:12] # Devolver top 12 equilibrado

def entrenar_modelo_calificacion(df):
    """
    Entrena un modelo predictivo mapeando las calificaciones categóricas a valores numéricos.
    """
    if df.empty or len(df) < 3:
        return None, "Se necesitan al menos 3 registros en la base de datos para entrenar el modelo."

    try:
        datos = df.copy()
        
        # Mapeo de la nueva escala de calificaciones a números para la regresión
        mapeo_notas = {
            "Absolute Cinema": 10,
            "Impresionante": 9,
            "Genial": 8,
            "Bueno": 7,
            "Normal": 5,
            "Malo": 3,
            "Basura": 1
        }
        
        # Convertimos las reseñas de texto a numéricas usando el mapa (con respaldo para números antiguos)
        datos['Review_Num'] = datos['Review'].map(mapeo_notas)
        datos['Review_Num'] = datos['Review_Num'].fillna(pd.to_numeric(datos['Review'], errors='coerce'))
        
        datos['Año'] = pd.to_numeric(datos['Año'], errors='coerce')
        datos = datos.dropna(subset=['Review_Num', 'Año'])

        if len(datos) < 3:
            return None, "No hay suficientes datos con calificaciones válidas para entrenar."

        datos['Tipo_Num'] = datos['Tipo'].apply(lambda x: 1 if x == "Película" else 0)
        
        X = datos[['Año', 'Tipo_Num']]
        y = datos['Review_Num']

        modelo = LinearRegression()
        modelo.fit(X, y)

        return modelo, "Modelo entrenado con éxito."

    except Exception as e:
        return None, f"Error al entrenar el modelo predictivo: {e}"

def predecir_calificacion(modelo, anio, es_pelicula=True):
    """
    Predice la nota numérica esperada en base al año y tipo.
    """
    if modelo is None:
        return None
        
    try:
        tipo_num = 1 if es_pelicula else 0
        entrada = pd.DataFrame([[anio, tipo_num]], columns=['Año', 'Tipo_Num'])
        prediccion = modelo.predict(entrada)
        
        nota_final = max(0.0, min(10.0, round(prediccion[0], 1)))
        return nota_final
    except Exception:
        return None
    
def generar_datos_wrapped(df):
    """
    Calcula estadísticas clave para el reporte visual estilo Wrapped.
    """
    if df.empty:
        return None

    total_obras = len(df)
    pelis_df = df[df['Tipo'] == 'Película']
    series_df = df[df['Tipo'] == 'Serie']

    # Género más consumido
    genero_top = df['Género'].mode()[0] if 'Género' in df.columns and not df['Género'].empty else "N/A"

    # Top Director
    director_top = "N/A"
    if 'Director' in df.columns:
        dirs_validos = df[~df['Director'].isin(["Desconocido", "N/A", "nan"])]
        if not dirs_validos.empty:
            director_top = dirs_validos['Director'].mode()[0]

    # Top Actor
    actor_top = "N/A"
    if 'Actores Principales' in df.columns:
        actores_list = []
        for val in df['Actores Principales'].dropna():
            if val not in ["Desconocido", "N/A", "nan"]:
                actores_list.extend([a.strip() for a in str(val).split(",") if a.strip()])
        if actores_list:
            actor_top = pd.Series(actores_list).mode()[0]

    # Obra mejor calificada (Absolute Cinema)
    cinema_top = "N/A"
    if 'Review' in df.columns:
        abs_cinema = df[df['Review'] == 'Absolute Cinema']
        if not abs_cinema.empty:
            cinema_top = abs_cinema.iloc[0]['Título']

    return {
        "total_obras": total_obras,
        "total_peliculas": len(pelis_df),
        "total_series": len(series_df),
        "genero_top": genero_top,
        "director_top": director_top,
        "actor_top": actor_top,
        "cinema_top": cinema_top
    }