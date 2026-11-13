import requests

API_KEY = "4210d2b186e4e98707ebc33f94b916e5"
BASE_URL = "https://api.themoviedb.org/3"

def obtener_tendencias(media_type="movie"):
    """
    Obtiene las tendencias globales de la semana para películas o series.
    media_type: 'movie' o 'tv'
    """
    try:
        url = f"{BASE_URL}/trending/{media_type}/week?api_key={API_KEY}&language=es-ES"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            return data.get('results', [])[:6]
        else:
            print(f"Error en API TMDB ({response.status_code}): {response.text}")
            return []
    except Exception as e:
        print(f"Excepción al conectar con TMDB: {e}")
        return []

def obtener_detalles_completos(item_id, media_type="movie"):
    """
    Obtiene la información detallada de una película o serie usando su ID de TMDB.
    Devuelve una tupla: (Título, Año, Duración, Director/Creador, Actores, Género, Nota_TMDB)
    """
    try:
        url = f"{BASE_URL}/{media_type}/{item_id}?api_key={API_KEY}&language=es-ES&append_to_response=credits"
        res = requests.get(url, timeout=5)
        
        if res.status_code != 200:
            return None
            
        data = res.json()
        
        # 1. Título
        titulo = data.get('title') or data.get('name') or "Sin Título"
        
        # 2. Año de estreno
        fecha = data.get('release_date') or data.get('first_air_date') or "0000"
        anio = int(fecha[:4]) if len(fecha) >= 4 and fecha[:4].isdigit() else 0
        
        # 3. Duración
        if media_type == "movie":
            duracion_min = data.get('runtime', 0) or 0
            duracion = f"{duracion_min} min"
        else:
            episodes = data.get('number_of_episodes', 0)
            duracion = f"{episodes} eps"
            
        # 4. Director / Creador
        director = "Desconocido"
        credits = data.get('credits', {})
        if media_type == "movie":
            for crew in credits.get('crew', []):
                if crew.get('job') == 'Director':
                    director = crew.get('name')
                    break
        else:
            created_by = data.get('created_by', [])
            if created_by:
                director = created_by[0].get('name')
            elif credits.get('crew'):
                for crew in credits.get('crew', []):
                    if crew.get('job') in ['Executive Producer', 'Director']:
                        director = crew.get('name')
                        break
                        
        # 5. Actores principales (Top 3)
        cast = credits.get('cast', [])
        actores_list = [member.get('name') for member in cast[:3] if member.get('name')]
        actores = ", ".join(actores_list) if actores_list else "Sin datos"
        
        # 6. Género Principal
        genres = data.get('genres', [])
        genero = genres[0].get('name') if genres else "General"
        
        # 7. Rating TMDB
        tmdb_rating = round(data.get('vote_average', 0.0), 1)
        
        return (titulo, anio, duracion, director, actores, genero, tmdb_rating)

    except Exception as e:
        print(f"Error al obtener detalles de TMDB: {e}")
        return None

def obtener_recomendaciones(df_dashboard):
    """
    Genera 3 recomendaciones basadas en el último elemento guardado en la base de datos.
    """
    if df_dashboard.empty:
        return []
        
    try:
        ultimo_registro = df_dashboard.iloc[-1]
        titulo_ultimo = ultimo_registro['Título']
        tipo_ultimo = "movie" if ultimo_registro.get('Tipo') == "Película" else "tv"
        
        url_search = f"{BASE_URL}/search/{tipo_ultimo}?api_key={API_KEY}&query={titulo_ultimo}&language=es-ES"
        res_search = requests.get(url_search, timeout=5).json()
        resultados = res_search.get('results', [])
        
        if not resultados:
            return []
            
        item_id = resultados[0]['id']
        
        url_rec = f"{BASE_URL}/{tipo_ultimo}/{item_id}/recommendations?api_key={API_KEY}&language=es-ES"
        res_rec = requests.get(url_rec, timeout=5).json()
        recomendaciones = res_rec.get('results', [])
        
        lista_final = []
        for rec in recomendaciones[:3]:
            lista_final.append({
                'title': rec.get('title') or rec.get('name'),
                'poster_path': rec.get('poster_path'),
                'vote_average': round(rec.get('vote_average', 0.0), 1),
                'overview': rec.get('overview', 'Sin sinopsis disponible.')
            })
            
        return lista_final

    except Exception as e:
        print(f"Error al generar recomendaciones: {e}")
        return []

def obtener_proveedores_streaming(tmdb_id, media_type="movie"):
    """
    Consulta los proveedores de streaming (flatrate) disponibles para una obra en TMDB.
    """
    url = f"{BASE_URL}/{media_type}/{tmdb_id}/watch/providers?api_key={API_KEY}"
    try:
        res = requests.get(url, timeout=4).json()
        resultados = res.get('results', {})
        
        # Intentar obtener para Venezuela (VE), si no hay, probar con Argentina (AR) o España (ES)
        region_preferida = 'VE' if 'VE' in resultados else ('AR' if 'AR' in resultados else 'ES')
        
        if region_preferida in resultados:
            info_region = resultados[region_preferida]
            proveedores = info_region.get('flatrate', [])
            return [p.get('provider_name') for p in proveedores]
    except Exception:
        pass
    return []