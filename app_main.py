import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import json
import os

import data_manager as dm
import api_manager as am
import ml_predictive as ml

st.set_page_config(
    page_title="Media Tracker Pro",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# GESTIÓN DE SESIÓN Y MULTI-USUARIO
# ==========================================
if "usuario_activo" not in st.session_state:
    st.session_state.usuario_activo = None

PERFILES_FILE = "perfiles_usuarios.json"

def cargar_perfiles():
    if os.path.exists(PERFILES_FILE):
        with open(PERFILES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return ["Ricardo"]

def guardar_perfiles(perfiles):
    with open(PERFILES_FILE, "w", encoding="utf-8") as f:
        json.dump(perfiles, f, ensure_ascii=False, indent=4)

lista_perfiles = cargar_perfiles()

# Pantalla de selección de usuario si no se ha iniciado sesión
if st.session_state.usuario_activo is None:
    st.title("🎬 Media Tracker Pro - Selección de Perfil")
    st.markdown("Selecciona tu perfil existente o registra uno nuevo para comenzar.")
    
    col_p1, col_p2 = st.columns(2)
    
    with col_p1:
        st.markdown("### 👤 Perfiles Disponibles")
        perfil_elegido = st.selectbox("Elige un perfil:", lista_perfiles)
        if st.button("Entrar con este perfil"):
            st.session_state.usuario_activo = perfil_elegido
            st.rerun()
            
    with col_p2:
        st.markdown("### ➕ Registrar Nuevo Usuario")
        nuevo_nombre = st.text_input("Nombre del nuevo usuario:")
        if st.button("Crear y Entrar"):
            if nuevo_nombre.strip():
                nombre_limpio = nuevo_nombre.strip()
                if nombre_limpio not in lista_perfiles:
                    lista_perfiles.append(nombre_limpio)
                    guardar_perfiles(lista_perfiles)
                st.session_state.usuario_activo = nombre_limpio
                st.success(f"¡Perfil {nombre_limpio} creado con éxito!")
                st.rerun()
            else:
                st.warning("Escribe un nombre válido.")
    
    st.stop()

# ==========================================
# ESTILOS CSS GLOBAL AVANZADOS (ESTILO STREAMING)
# ==========================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    .stApp {
        background-color: #0b0e14;
        color: #e6edf3;
    }
    .custom-card {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 14px;
        padding: 24px;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
        transition: transform 0.3s ease, border-color 0.3s ease;
        margin-bottom: 20px;
    }
    .custom-card:hover {
        transform: translateY(-4px);
        border-color: #58a6ff;
    }
    img {
        border-radius: 10px;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    img:hover {
        transform: scale(1.03);
        box-shadow: 0 10px 25px rgba(88, 166, 255, 0.25);
    }
    .stButton>button {
        background: linear-gradient(135deg, #238636 0%, #2ea043 100%);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        padding: 0.5rem 1rem;
        transition: all 0.2s ease-in-out;
        box-shadow: 0 4px 12px rgba(35, 134, 54, 0.3);
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #2ea043 0%, #3fb950 100%);
        box-shadow: 0 6px 16px rgba(46, 160, 67, 0.5);
        transform: translateY(-2px);
    }
    .stTextInput>div>div>input, .stSelectbox>div>div>div {
        background-color: #0d1117;
        border: 1px solid #30363d;
        color: #e6edf3;
        border-radius: 8px;
    }
    [data-testid="stSidebar"] {
        background-color: #0d1117;
        border-right: 1px solid #21262d;
    }
    .stMetric { 
        background: linear-gradient(135deg, #161b22 0%, #1f242d 100%);
        padding: 20px; 
        border-radius: 14px; 
        border: 1px solid #30363d;
        box-shadow: 0 4px 20px rgba(0,0,0,0.4);
    }
    .stMetric label {
        color: #8b949e !important;
        font-weight: 600 !important;
    }
    /* Proporción uniforme para los pósters de las vitrinas del perfil */
    [data-testid="column"] img {
        max-width: 100%;
        border-radius: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# GESTIÓN DE RUTAS Y DATOS POR USUARIO ACTIVO
# ==========================================
usuario_actual = st.session_state.usuario_activo

# Generar nombres de archivos únicos e independientes para cada usuario
limpio_user = "".join(c for c in usuario_actual if c.isalnum() or c in ('_', '-')).lower()
PERFIL_FILE = f"perfil_usuario_{limpio_user}.json"
WATCHLIST_FILE = f"watchlist_{limpio_user}.json"

def cargar_perfil():
    if os.path.exists(PERFIL_FILE):
        try:
            with open(PERFIL_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "nombre": usuario_actual,
        "descripcion": "Amante del cine, las series y el análisis de datos.",
        "avatar": None,
        "favoritas": []
    }

def guardar_perfil(perfil):
    with open(PERFIL_FILE, "w", encoding="utf-8") as f:
        json.dump(perfil, f, ensure_ascii=False, indent=4)

def cargar_watchlist():
    limpio_user = "".join(c for c in usuario_actual if c.isalnum() or c in ('_', '-')).lower()
    if limpio_user in ["ricardo", "rickdiaz"]:
        archivo_w = "watchlist.json"
    else:
        archivo_w = f"watchlist_{limpio_user}.json"
        
    if os.path.exists(archivo_w):
        try:
            with open(archivo_w, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []

def guardar_watchlist(watchlist):
    limpio_user = "".join(c for c in usuario_actual if c.isalnum() or c in ('_', '-')).lower()
    if limpio_user in ["ricardo", "rickdiaz"]:
        archivo_w = "watchlist.json"
    else:
        archivo_w = f"watchlist_{limpio_user}.json"
        
    with open(archivo_w, "w", encoding="utf-8") as f:
        json.dump(watchlist, f, ensure_ascii=False, indent=4)

# Cargar datos independientes
df_global = dm.cargar_excel_usuario(usuario_actual)
perfil_data = cargar_perfil()
watchlist_data = cargar_watchlist()

# Barra lateral
st.sidebar.markdown("# 🎬 Media Tracker Pro")
st.sidebar.markdown("<p style='color: #8b949e; font-size: 0.85rem;'>Tu centro personal de cine y series</p>", unsafe_allow_html=True)
st.sidebar.markdown("---")
st.sidebar.markdown(f"👤 **Usuario:** `{usuario_actual}`")
if st.sidebar.button("🔄 Cambiar de Usuario"):
    st.session_state.usuario_activo = None
    st.rerun()
st.sidebar.markdown("---")

menu = st.sidebar.radio(
    "Menú de Navegación",
    [
        "👤 Mi Perfil", 
        "📊 Dashboard Principal", 
        "🎁 Media Wrapped",
        "🎬 Films por ver", 
        "➕ Registrar Contenido", 
        "🔍 Explorar TMDB & Tendencias", 
        "🎯 Recomendaciones para Ti",
        "🤖 Analítica Predictiva", 
        "🗄️ Gestionar Base de Datos"
    ],
    key="menu_navegacion_principal"
)

# ==========================================
# FUNCIÓN AUXILIAR PARA VITRINAS DEL PERFIL
# ==========================================
def renderizar_vitrina_perfil(titulo_seccion, clave_json, limite, tipo_busqueda="multi", placeholder_busq="🔍 Busca para añadir..."):
    st.markdown("---")
    st.subheader(titulo_seccion)
    
    busq = st.text_input(placeholder_busq, key=f"input_busq_{clave_json}")
    
    if busq.strip():
        url_search = f"{am.BASE_URL}/search/{tipo_busqueda}?api_key={am.API_KEY}&query={busq}&language=es-ES"
        try:
            res = requests.get(url_search, timeout=5).json()
            resultados = res.get('results', [])
            
            if tipo_busqueda == "multi":
                resultados = [r for r in resultados if r.get('media_type') in ['movie', 'tv']]
                
            if resultados:
                opciones = {}
                for item in resultados:
                    t = item.get('title') or item.get('name') or 'Sin título'
                    fecha = item.get('release_date') or item.get('first_air_date') or '0000'
                    anio_str = fecha[:4] if len(fecha) >= 4 else "N/A"
                    
                    etiqueta_tipo = ""
                    if tipo_busqueda == "multi":
                        m_type = "Serie" if item.get('media_type') == 'tv' else "Película"
                        etiqueta_tipo = f" [{m_type}]"
                        
                    opciones[f"{t}{etiqueta_tipo} ({anio_str})"] = item

                sel_label = st.selectbox("Selecciona de TMDB:", list(opciones.keys()), key=f"select_{clave_json}")
                
                if st.button(f"➕ Añadir", key=f"btn_add_{clave_json}"):
                    item_elegido = opciones[sel_label]
                    entry = {
                        "id": item_elegido.get('id'),
                        "title": item_elegido.get('title') or item_elegido.get('name'),
                        "poster_path": item_elegido.get('poster_path'),
                        "release_date": item_elegido.get('release_date') or item_elegido.get('first_air_date') or ''
                    }
                    
                    if clave_json not in perfil_data:
                        perfil_data[clave_json] = []
                        
                    if len(perfil_data[clave_json]) >= limite:
                        st.warning(f"⚠️ Ya alcanzaste el límite máximo de {limite} obra(s) para esta sección.")
                    elif any(f["id"] == entry["id"] for f in perfil_data[clave_json]):
                        st.info("Esta obra ya está agregada en esta sección.")
                    else:
                        perfil_data[clave_json].append(entry)
                        guardar_perfil(perfil_data)
                        st.success(f"✅ ¡'{entry['title']}' añadida!")
                        st.rerun()
            else:
                st.warning("No se encontraron resultados.")
        except Exception as e:
            st.error(f"Error al buscar en TMDB: {e}")

    items_actuales = perfil_data.get(clave_json, [])
    if items_actuales:
        # Creamos siempre un bloque de columnas basado en el límite exacto para mantener la misma escala
        cols = st.columns(limite)
            
        for idx in range(limite):
            with cols[idx]:
                if idx < len(items_actuales):
                    obra = items_actuales[idx]
                    poster = obra.get("poster_path")
                    if poster:
                        st.image(f"https://image.tmdb.org/t/p/w300{poster}", use_container_width=True)
                    else:
                        st.markdown(f"**{obra.get('title')}**")
                        
                    if st.button("❌ Quitar", key=f"del_{clave_json}_{obra.get('id')}_{idx}"):
                        perfil_data[clave_json].pop(idx)
                        guardar_perfil(perfil_data)
                        st.rerun()
# ==========================================
# 0. MI PERFIL
# ==========================================
if menu == "👤 Mi Perfil":
    st.title("👤 Perfil de Usuario")
    st.markdown("Personaliza tu espacio con tu foto, biografía y tus vitrinas destacadas de cine y series.")

    col_perfil_1, col_perfil_2 = st.columns([1, 2])

    with col_perfil_1:
        st.subheader("🖼️ Avatar")
        avatar_actual_path = perfil_data.get("avatar")
        if avatar_actual_path and os.path.exists(avatar_actual_path):
            st.image(avatar_actual_path, width=180, caption="Foto actual")
        else:
            st.info("No hay foto cargada.")
            
        archivo_imagen = st.file_uploader("Subir Avatar (PNG, JPG)", type=["png", "jpg", "jpeg"])
        if archivo_imagen is not None:
            avatar_path = f"avatar_{limpio_user}.png"
            with open(avatar_path, "wb") as f:
                f.write(archivo_imagen.getbuffer())
            perfil_data["avatar"] = avatar_path
            guardar_perfil(perfil_data)
            st.success("¡Avatar actualizado con éxito!")

    with col_perfil_2:
        st.subheader("✏️ Información Personal")
        nuevo_nombre = st.text_input("Nombre de Usuario:", value=perfil_data.get("nombre", ""))
        
        desc_actual = perfil_data.get("descripcion", "")
        nueva_desc = st.text_area("Biografía (Máximo 30 palabras):", value=desc_actual)
        
        palabras_desc = nueva_desc.strip().split()
        if len(palabras_desc) > 30:
            st.warning(f"⚠️ Tu biografía tiene {len(palabras_desc)} palabras. Por favor, reduce a 30 palabras o menos.")
        
        if st.button("Guardar Cambios del Perfil", type="primary"):
            if len(palabras_desc) <= 30:
                perfil_data["nombre"] = nuevo_nombre
                perfil_data["descripcion"] = nueva_desc
                guardar_perfil(perfil_data)
                st.success("✅ ¡Perfil actualizado correctamente!")
            else:
                st.error("La biografía supera las 30 palabras.")

    # 1. Top 5 Películas Favoritas (mantiene la clave "favoritas" para conservar tus 5 películas actuales)
    renderizar_vitrina_perfil(
        titulo_seccion="🌟 Tus 5 Películas Favoritas",
        clave_json="favoritas",
        limite=5,
        tipo_busqueda="movie",
        placeholder_busq="🔍 Busca una película para añadir a tus favoritas:"
    )

    # 2. Top 4 Series Favoritas
    renderizar_vitrina_perfil(
        titulo_seccion="📺 Tus 4 Series Favoritas",
        clave_json="series_favoritas",
        limite=4,
        tipo_busqueda="tv",
        placeholder_busq="🔍 Busca una serie para añadir a tus favoritas:"
    )

    # 3. Top 3 Películas/Series Recomendadas
    renderizar_vitrina_perfil(
        titulo_seccion="👍 3 Películas o Series que Recomiendas",
        clave_json="recomendadas_perfil",
        limite=3,
        tipo_busqueda="multi",
        placeholder_busq="🔍 Busca una película o serie para recomendar:"
    )

    # 4. Top 2 Películas/Series que te Sorprendieron
    renderizar_vitrina_perfil(
        titulo_seccion="🤯 2 Películas o Series que te Sorprendieron",
        clave_json="sorprendieron_2",
        limite=2,
        tipo_busqueda="multi",
        placeholder_busq="🔍 Busca una película o serie que te haya sorprendido:"
    )

    # 5. Top 1 Película/Serie Sobrevalorada
    renderizar_vitrina_perfil(
        titulo_seccion="📉 1 Película o Serie Sobrevalorada",
        clave_json="sobrevalorada_1",
        limite=1,
        tipo_busqueda="multi",
        placeholder_busq="🔍 Busca esa obra que consideras sobrevalorada:"
    )

# ==========================================
# 1. DASHBOARD PRINCIPAL
# ==========================================
elif menu == "📊 Dashboard Principal":
    st.title("📊 Dashboard General de Medios")
    st.markdown("Visualiza el rendimiento, estadísticas y distribución de tus contenidos consumidos.")

    if df_global.empty:
        st.info("👋 ¡Aún no tienes registros! Ve a la sección **'➕ Registrar Contenido'** para empezar.")
    else:
        total_items = len(df_global)
        peliculas_count = len(df_global[df_global['Tipo'] == 'Película']) if 'Tipo' in df_global.columns else 0
        series_count = len(df_global[df_global['Tipo'] == 'Serie']) if 'Tipo' in df_global.columns else 0

        total_capitulos = 0
        minutos_totales = 0

        for _, row in df_global.iterrows():
            dur_str = str(row.get('Duración Total', '0')).strip().lower()
            tipo_obra = str(row.get('Tipo', 'Película')).strip().capitalize()
            
            digitos_dur = "".join([c for c in dur_str if c.isdigit()])
            num_extraido = int(digitos_dur) if digitos_dur else 0

            if tipo_obra == 'Serie':
                capitulos_serie = num_extraido if num_extraido > 0 else 10
                total_capitulos += capitulos_serie
                minutos_totales += (capitulos_serie * 45)
            
            elif tipo_obra in ['Película', 'Pelicula']:
                if 'h' in dur_str:
                    try:
                        partes = dur_str.split('h')
                        horas = int("".join([c for c in partes[0] if c.isdigit()])) if partes[0] else 0
                        minutos = int("".join([c for c in partes[1] if c.isdigit()])) if len(partes) > 1 and partes[1] else 0
                        duracion_peli = (horas * 60) + minutos
                    except:
                        duracion_peli = num_extraido if num_extraido > 0 else 120
                else:
                    duracion_peli = num_extraido if num_extraido > 0 else 120
                minutos_totales += duracion_peli

        total_horas = minutos_totales / 60
        total_dias = total_horas / 24

        years = int(total_dias // 365)
        dias_restantes = total_dias % 365
        months = int(dias_restantes // 30)
        days = int(dias_restantes % 30)
        hours = int(round(total_horas % 24))

        partes_tiempo = []
        if years > 0:
            partes_tiempo.append(f"{years} {'Year' if years == 1 else 'Years'}")
        if months > 0 or years > 0:
            partes_tiempo.append(f"{months} {'Month' if months == 1 else 'Months'}")
        partes_tiempo.append(f"{days} {'Day' if days == 1 else 'Days'}")
        partes_tiempo.append(f"{hours} {'Hr' if hours == 1 else 'Hrs'}")

        tiempo_formateado = ", ".join(partes_tiempo)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(label="📚 Total Registros", value=total_items)
        with col2:
            st.metric(label="🎥 Películas", value=peliculas_count)
        with col3:
            st.metric(label="📺 Series", value=series_count)

        col4, col5 = st.columns(2)
        with col4:
            st.metric(label="📺 Total Capítulos Vistos", value=total_capitulos)
        with col5:
            st.metric(label="⏱️ Tiempo Total Invertido", value=tiempo_formateado)

        st.markdown("---")
        st.subheader("🏆 Top 3 Años con Mayor Consumo")
        if 'Año' in df_global.columns:
            df_anios = df_global[df_global['Año'].notna() & (df_global['Año'] != 0) & (df_global['Año'] != "N/A")]
            if not df_anios.empty:
                conteo_anios = df_anios['Año'].value_counts().reset_index()
                conteo_anios.columns = ['Año', 'Cantidad']
                top_3_anios = conteo_anios.sort_values(by='Cantidad', ascending=False).head(3)
                cols_podio_anios = st.columns(min(3, len(top_3_anios)))
                medallas_anios = ["🥇 1er Lugar", "🥈 2do Lugar", "🥉 3er Lugar"]
                for idx, row in top_3_anios.reset_index(drop=True).iterrows():
                    if idx < 3:
                        with cols_podio_anios[idx]:
                            st.metric(label=medallas_anios[idx], value=f"Año {int(row['Año'])}", delta=f"{row['Cantidad']} obras")

        st.markdown("---")
        st.subheader("🎬 Top Directores Más Vistos")
        if 'Director' in df_global.columns:
            df_directores = df_global[df_global['Director'].notna() & (df_global['Director'] != "Desconocido") & (df_global['Director'] != "N/A")]
            if not df_directores.empty:
                conteo_directores = df_directores['Director'].value_counts().reset_index()
                conteo_directores.columns = ['Director', 'Cantidad']
                
                top_3_dir = conteo_directores.head(3)
                cols_podio_dir = st.columns(min(3, len(top_3_dir)))
                medallas_dir = ["🥇 1er Lugar", "🥈 2do Lugar", "🥉 3er Lugar"]
                for idx, row in top_3_dir.iterrows():
                    if idx < 3:
                        with cols_podio_dir[idx]:
                            st.metric(label=medallas_dir[idx], value=row['Director'], delta=f"{row['Cantidad']} obra(s)")
                
                st.markdown("<br>", unsafe_allow_html=True)
                col_dir_1, col_dir_2 = st.columns(2)
                with col_dir_1:
                    st.markdown("### 📋 Listado Completo")
                    st.dataframe(conteo_directores, use_container_width=True)
                with col_dir_2:
                    fig_dir = px.bar(conteo_directores.head(10), x='Cantidad', y='Director', orientation='h', title="Top 10 Directores", color='Cantidad', color_continuous_scale='Reds')
                    fig_dir.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white', yaxis={'categoryorder':'total ascending'})
                    st.plotly_chart(fig_dir, use_container_width=True)

        st.markdown("---")
        st.subheader("⭐ Top 10 Actores Más Vistos")
        if 'Actores Principales' in df_global.columns and 'Tipo' in df_global.columns:
            registros_actores = []
            for _, row in df_global.iterrows():
                actores_str = str(row['Actores Principales'])
                tipo_obra = row['Tipo']
                if actores_str and actores_str not in ["nan", "Desconocido", "N/A"]:
                    lista_actores = [a.strip() for a in actores_str.split(',') if a.strip()]
                    for actor in lista_actores:
                        registros_actores.append({'Actor': actor, 'Tipo': tipo_obra})
            
            if registros_actores:
                df_actores_flat = pd.DataFrame(registros_actores)
                df_pivote_act = df_actores_flat.pivot_table(index='Actor', columns='Tipo', aggfunc=len, fill_value=0)
                if 'Película' not in df_pivote_act.columns:
                    df_pivote_act['Película'] = 0
                if 'Serie' not in df_pivote_act.columns:
                    df_pivote_act['Serie'] = 0
                df_pivote_act['Total'] = df_pivote_act['Película'] + df_pivote_act['Serie']
                df_pivote_act = df_pivote_act.sort_values(by='Total', ascending=False).reset_index()
                
                top_10_actores = df_pivote_act.head(10)
                top_3_act = top_10_actores.head(3)
                cols_podio_act = st.columns(min(3, len(top_3_act)))
                medallas_act = ["🥇 1er Lugar", "🥈 2do Lugar", "🥉 3er Lugar"]
                for idx, row in top_3_act.iterrows():
                    if idx < 3:
                        with cols_podio_act[idx]:
                            st.metric(label=medallas_act[idx], value=row['Actor'], delta=f"{row['Total']} total")
                
                st.markdown("<br>", unsafe_allow_html=True)
                col_act_1, col_act_2 = st.columns(2)
                with col_act_1:
                    st.markdown("### 📋 Desglose de Actores")
                    st.dataframe(top_10_actores, use_container_width=True)
                with col_act_2:
                    fig_act = px.bar(top_10_actores, x='Total', y='Actor', orientation='h', title="Top 10 Actores", color='Total', color_continuous_scale='Sunset')
                    fig_act.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white', yaxis={'categoryorder':'total ascending'})
                    st.plotly_chart(fig_act, use_container_width=True)

        st.markdown("---")
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            if 'Género' in df_global.columns:
                st.subheader("🎭 Distribución por Género")
                fig_genero = px.pie(df_global, names='Género', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
                fig_genero.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white')
                st.plotly_chart(fig_genero, use_container_width=True)
        with col_g2:
            if 'Año' in df_global.columns:
                st.subheader("📅 Histograma General de Años")
                fig_anio = px.histogram(df_global, x='Año', nbins=10, color_discrete_sequence=['#ff4b4b'])
                fig_anio.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white')
                st.plotly_chart(fig_anio, use_container_width=True)

        st.markdown("### 📋 Tabla de Registros Actuales")
        st.dataframe(df_global, use_container_width=True)

# ==========================================
# 2. WATCHLIST
# ==========================================
elif menu == "🎬 Films por ver":
    st.title("🎬 Films por Ver (Watchlist)")
    st.markdown("Tus producciones pendientes. Haz clic en **(Vista)** cuando las termines para calificarlas.")

    if not watchlist_data:
        st.info("No tienes películas o series pendientes.")
    else:
        for idx, item in enumerate(watchlist_data):
            with st.container():
                cols = st.columns([0.8, 3, 2, 2, 2])
                
                poster_path = item.get('poster_path')
                tmdb_id = item.get('tmdb_id')
                media_type = "movie" if item.get('tipo') == "Película" else "tv"
                
                if not poster_path and tmdb_id:
                    try:
                        url_info = f"{am.BASE_URL}/{media_type}/{tmdb_id}?api_key={am.API_KEY}&language=es-ES"
                        data_info = requests.get(url_info, timeout=3).json()
                        poster_path = data_info.get('poster_path')
                        if poster_path:
                            item['poster_path'] = poster_path
                            guardar_watchlist(watchlist_data)
                    except Exception:
                        pass

                with cols[0]:
                    if poster_path:
                        st.image(f"https://image.tmdb.org/t/p/w200{poster_path}", width=60)
                    else:
                        st.markdown("🎬")

                with cols[1]:
                    st.markdown(f"**{item.get('titulo')}**")
                    st.markdown(f"<p style='color: #8b949e; font-size: 0.85rem;'>{item.get('anio', 'N/A')}</p>", unsafe_allow_html=True)

                with cols[2]:
                    st.markdown(f"Tipo: `{item.get('tipo')}`")

                with cols[3]:
                    st.markdown(f"Género: `{item.get('genero')}`")
                
                with cols[4]:
                    with st.popover("✔️ Vista"):
                        escala_reviews = ["Absolute Cinema", "Impresionante", "Genial", "Bueno", "Normal", "Malo", "Basura"]
                        review_elegida = st.selectbox("Tu Calificación:", escala_reviews, key=f"rev_w_{idx}")
                        
                        if st.button("Confirmar y mover", key=f"btn_visto_w_{idx}"):
                            if tmdb_id:
                                detalles = am.obtener_detalles_completos(tmdb_id, media_type)
                                if detalles:
                                    tit, an, dur, dir_val, act, gen, tmdb_r = detalles
                                else:
                                    tit, an, dur, dir_val, act, gen, tmdb_r = item.get('titulo'), item.get('anio'), "N/A", "Desconocido", "Desconocido", item.get('genero'), 0.0
                            else:
                                tit, an, dur, dir_val, act, gen, tmdb_r = item.get('titulo'), item.get('anio'), "N/A", "Desconocido", "Desconocido", item.get('genero'), 0.0

                            prefix = "TMDB_MOVIE_" if media_type == "movie" else "TMDB_TV_"
                            nuevo_id = f"{prefix}{tmdb_id}" if tmdb_id else f"CUSTOM_{idx}"
                            
                            reg = {
                                "ID": nuevo_id, "Título": tit, "Tipo": item.get('tipo'), "Género": gen,
                                "Año": an, "Duración Total": dur, "Review": review_elegida, "Letterboxd": "N/A",
                                "IMDb Rating": tmdb_r, "Rotten Tomatoes": "N/A", "TMDB Rating": tmdb_r,
                                "Serie Graph": "N/A", "Director": dir_val, "Actores Principales": act,
                                "Fecha/Hora Registro": str(pd.Timestamp.now())
                            }
                            
                            dm.guardar_registro_usuario(usuario_actual, reg)
                            watchlist_data.pop(idx)
                            guardar_watchlist(watchlist_data)
                            st.success(f"¡'{tit}' movida a vistos!")
                            st.rerun()

                st.divider()

# ==========================================
# 3. REGISTRAR CONTENIDO
# ==========================================
elif menu == "➕ Registrar Contenido":
    st.title("➕ Registrar Nuevo Contenido")
    st.markdown("Busca producciones en el catálogo de TMDB, selecciónalas y regístralas en tus vistos.")

    busqueda_reg = st.text_input("🔍 Buscar película o serie para registrar...", placeholder="Ej: Interstellar, Breaking Bad...")

    if busqueda_reg.strip():
        url_search = f"{am.BASE_URL}/search/multi?api_key={am.API_KEY}&query={busqueda_reg}&language=es-ES"
        try:
            res = requests.get(url_search, timeout=5).json()
            resultados = res.get('results', [])
            resultados_filtrados = [r for r in resultados if r.get('media_type') in ['movie', 'tv'] or 'title' in r or 'name' in r]
            
            if resultados_filtrados:
                st.markdown(f"<p style='color: #8b949e;'>Haz clic en <b>'Ver Detalles'</b> en la obra que deseas registrar.</p>", unsafe_allow_html=True)
                st.markdown("---")

                # Cuadrícula de pósters para el buscador
                NUM_COLUMNAS = 6
                cols = st.columns(NUM_COLUMNAS)

                for idx, item in enumerate(resultados_filtrados):
                    col_actual = cols[idx % NUM_COLUMNAS]
                    poster_path = item.get('poster_path')
                    titulo_item = item.get('title') or item.get('name') or "Sin Título"
                    item_id = item.get('id')
                    m_val = item.get('media_type')
                    media_t = "tv" if (m_val == 'tv' or ('name' in item and 'title' not in item)) else "movie"

                    with col_actual:
                        if poster_path:
                            st.image(f"https://image.tmdb.org/t/p/w300{poster_path}", use_container_width=True)
                        else:
                            st.markdown(f"**{titulo_item}**")

                        if st.button("Ver Detalles", key=f"det_reg_btn_{item_id}_{idx}"):
                            st.session_state.obra_seleccionada_reg = {
                                "id": item_id,
                                "tipo": media_t,
                                "titulo": titulo_item
                            }
                            st.rerun()
            else:
                st.warning("No se encontraron resultados para tu búsqueda.")
        except Exception as e:
            st.error(f"Error al conectar con TMDB: {e}")
    else:
        st.info("Escribe el nombre de una película o serie arriba para comenzar a buscar.")

    # ==========================================
    # VISTA DETALLADA DE LA OBRA SELECCIONADA EN REGISTRO
    # ==========================================
    if "obra_seleccionada_reg" in st.session_state:
        obra_reg = st.session_state.obra_seleccionada_reg
        st.markdown("---")
        
        if st.button("← Volver a la búsqueda"):
            del st.session_state.obra_seleccionada_reg
            st.rerun()

        tmdb_id = obra_reg["id"]
        media_type = obra_reg["tipo"]
        
        detalles = am.obtener_detalles_completos(tmdb_id, media_type)
        
        url_detalles = f"{am.BASE_URL}/{media_type}/{tmdb_id}?api_key={am.API_KEY}&language=es-ES"
        backdrop_url = ""
        overview_text = "Sin sinopsis disponible."
        data_full = {}
        try:
            data_full = requests.get(url_detalles, timeout=5).json()
            if data_full.get('backdrop_path'):
                backdrop_url = f"https://image.tmdb.org/t/p/original{data_full.get('backdrop_path')}"
            if data_full.get('overview'):
                overview_text = data_full.get('overview')
        except:
            pass

        if detalles:
            tit, an, dur, dir_val, act, gen, tmdb_r = detalles
            
            if backdrop_url:
                st.markdown(f"""
                    <div style="
                        background-image: linear-gradient(to bottom, rgba(11,14,20,0.3), rgba(11,14,20,0.95)), url('{backdrop_url}');
                        background-size: cover;
                        background-position: center;
                        padding: 40px;
                        border-radius: 16px;
                        border: 1px solid #30363d;
                        margin-bottom: 25px;
                    ">
                """, unsafe_allow_html=True)
            else:
                st.markdown('<div class="custom-card">', unsafe_allow_html=True)

            col_det1, col_det2, col_det3 = st.columns([1.2, 2.2, 1.6])

            with col_det1:
                poster_p = data_full.get('poster_path')
                if poster_p:
                    st.image(f"https://image.tmdb.org/t/p/w400{poster_p}", use_container_width=True)

            with col_det2:
                st.markdown(f"# {tit}")
                st.markdown(f"<p style='color: #8b949e; font-size: 1.1rem;'>{an} • {dur} • {gen}</p>", unsafe_allow_html=True)
                st.markdown("### Sinopsis")
                st.write(overview_text)

            with col_det3:
                st.markdown("### DIRECCIÓN")
                st.markdown(f"<p style='color: #58a6ff; font-weight: 600;'>{dir_val}</p>", unsafe_allow_html=True)
                
                st.markdown("### ELENCO PRINCIPAL")
                actores_lista = [a.strip() for a in act.split(",") if a.strip()]
                for actor in actores_lista[:5]:
                    st.markdown(f"- {actor}")

                st.markdown("### 📺 DISPONIBLE EN STREAMING")
                proveedores = am.obtener_proveedores_streaming(tmdb_id, media_type)
                if proveedores:
                    prov_str = ", ".join([f"`{p}`" for p in proveedores])
                    st.markdown(prov_str)
                else:
                    st.markdown("<p style='color: #8b949e; font-size: 0.9rem;'>No hay plataformas registradas para tu región.</p>", unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)

            # Opciones de registro interactivo
            st.markdown("### 📝 Registrar en tu Base de Datos o Watchlist")
            
            col_acc1, col_acc2 = st.columns(2)
            
            with col_acc1:
                if st.button("➕ Agregar a Films por ver (Watchlist)", key="btn_add_watchlist_reg"):
                    tipo_str = "Película" if media_type == "movie" else "Serie"
                    poster_p_val = data_full.get('poster_path')
                    w_item = {
                        "tmdb_id": tmdb_id, 
                        "titulo": tit, 
                        "tipo": tipo_str, 
                        "genero": gen, 
                        "anio": an,
                        "poster_path": poster_p_val
                    }
                    if any(w.get("tmdb_id") == w_item["tmdb_id"] for w in watchlist_data):
                        st.info("Ya está en tu watchlist.")
                    else:
                        watchlist_data.append(w_item)
                        guardar_watchlist(watchlist_data)
                        st.success("✅ ¡Añadida a pendientes!")

            with col_acc2:
                with st.popover("📥 Importar directo a Vistos (Calificar)"):
                    escala_reviews = ["Absolute Cinema", "Impresionante", "Genial", "Bueno", "Normal", "Malo", "Basura"]
                    review_elegida_reg = st.selectbox("Tu Calificación:", escala_reviews, key="rev_reg_popup")
                    
                    if st.button("Confirmar Guardado", key="btn_confirm_reg_visto"):
                        prefix = "TMDB_MOVIE_" if media_type == "movie" else "TMDB_TV_"
                        nuevo_id = f"{prefix}{tmdb_id}"
                        df_check = dm.cargar_excel_usuario(usuario_actual)
                        
                        if not df_check.empty and nuevo_id in df_check['ID'].values:
                            st.warning("⚠️ Ya se encuentra registrado en tu base de datos.")
                        else:
                            reg = {
                                "ID": nuevo_id, "Título": tit, "Tipo": "Película" if media_type == 'movie' else "Serie",
                                "Género": gen, "Año": an, "Duración Total": dur, "Review": review_elegida_reg,
                                "Letterboxd": "N/A", "IMDb Rating": tmdb_r, "Rotten Tomatoes": "N/A",
                                "TMDB Rating": tmdb_r, "Serie Graph": "N/A", "Director": dir_val,
                                "Actores Principales": act, "Fecha/Hora Registro": str(pd.Timestamp.now())
                            }
                            dm.guardar_registro_usuario(usuario_actual, reg)
                            st.success("🎉 ¡Importado a tus vistos con éxito!")
                            st.rerun()

# ==========================================
# 4. EXPLORAR TMDB & TENDENCIAS
# ==========================================
elif menu == "🔍 Explorar TMDB & Tendencias":
    st.title("🔍 Explorar Catálogo")
    
    col_search1, col_search2 = st.columns([3, 1])
    with col_search1:
        query_manual = st.text_input("🔍 Buscar película o serie...", placeholder="Ej: The Dark Knight, Parasite...")
    with col_search2:
        categoria = st.selectbox("Filtrar por:", ["Películas en Tendencia", "Series en Tendencia", "Búsqueda Manual"])

    tendencias = []

    if query_manual.strip():
        url_m = f"{am.BASE_URL}/search/multi?api_key={am.API_KEY}&query={query_manual}&language=es-ES"
        try:
            res_m = requests.get(url_m, timeout=5).json()
            tendencias = [r for r in res_m.get('results', []) if r.get('poster_path')]
        except Exception:
            tendencias = []
    else:
        if categoria == "Películas en Tendencia":
            tendencias = am.obtener_tendencias("movie")
        elif categoria == "Series en Tendencia":
            tendencias = am.obtener_tendencias("tv")

    if not tendencias:
        st.info("No se encontraron producciones o el catálogo está cargando.")
    else:
        st.markdown(f"<p style='color: #8b949e;'>Haz clic en cualquier obra para abrir su vista detallada.</p>", unsafe_allow_html=True)
        st.markdown("---")

        NUM_COLUMNAS = 6
        cols = st.columns(NUM_COLUMNAS)

        for idx, item in enumerate(tendencias):
            col_actual = cols[idx % NUM_COLUMNAS]
            poster_path = item.get('poster_path')
            titulo_item = item.get('title') or item.get('name') or "Sin Título"
            item_id = item.get('id')
            media_t = "movie" if (item.get('media_type') == "movie" or ('title' in item and 'name' not in item)) else "tv"

            with col_actual:
                if poster_path:
                    st.image(f"https://image.tmdb.org/t/p/w300{poster_path}", use_container_width=True)
                else:
                    st.markdown(f"**{titulo_item}**")

                if st.button("Ver Detalles", key=f"det_btn_{item_id}_{idx}"):
                    st.session_state.obra_seleccionada = {
                        "id": item_id,
                        "tipo": media_t,
                        "titulo": titulo_item
                    }
                    st.rerun()

    if "obra_seleccionada" in st.session_state:
        obra = st.session_state.obra_seleccionada
        st.markdown("---")
        
        if st.button("← Volver al catálogo"):
            del st.session_state.obra_seleccionada
            st.rerun()

        tmdb_id = obra["id"]
        media_type = obra["tipo"]
        
        detalles = am.obtener_detalles_completos(tmdb_id, media_type)
        
        url_detalles = f"{am.BASE_URL}/{media_type}/{tmdb_id}?api_key={am.API_KEY}&language=es-ES"
        backdrop_url = ""
        overview_text = "Sin sinopsis disponible."
        data_full = {}
        try:
            data_full = requests.get(url_detalles, timeout=5).json()
            if data_full.get('backdrop_path'):
                backdrop_url = f"https://image.tmdb.org/t/p/original{data_full.get('backdrop_path')}"
            if data_full.get('overview'):
                overview_text = data_full.get('overview')
        except:
            pass

        if detalles:
            tit, an, dur, dir_val, act, gen, tmdb_r = detalles
            
            if backdrop_url:
                st.markdown(f"""
                    <div style="
                        background-image: linear-gradient(to bottom, rgba(11,14,20,0.3), rgba(11,14,20,0.95)), url('{backdrop_url}');
                        background-size: cover;
                        background-position: center;
                        padding: 40px;
                        border-radius: 16px;
                        border: 1px solid #30363d;
                        margin-bottom: 25px;
                    ">
                """, unsafe_allow_html=True)
            else:
                st.markdown('<div class="custom-card">', unsafe_allow_html=True)

            col_det1, col_det2, col_det3 = st.columns([1.2, 2.2, 1.6])

            with col_det1:
                poster_p = data_full.get('poster_path')
                if poster_p:
                    st.image(f"https://image.tmdb.org/t/p/w400{poster_p}", use_container_width=True)

            with col_det2:
                st.markdown(f"# {tit}")
                st.markdown(f"<p style='color: #8b949e; font-size: 1.1rem;'>{an} • {dur} • {gen}</p>", unsafe_allow_html=True)
                st.markdown("### Sinopsis")
                st.write(overview_text)

            with col_det3:
                st.markdown("### DIRECCIÓN")
                st.markdown(f"<p style='color: #58a6ff; font-weight: 600;'>{dir_val}</p>", unsafe_allow_html=True)
                
                st.markdown("### ELENCO PRINCIPAL")
                actores_lista = [a.strip() for a in act.split(",") if a.strip()]
                for actor in actores_lista[:5]:
                    st.markdown(f"- {actor}")

                st.markdown("### 📺 DISPONIBLE EN STREAMING")
                proveedores = am.obtener_proveedores_streaming(tmdb_id, media_type)
                if proveedores:
                    prov_str = ", ".join([f"`{p}`" for p in proveedores])
                    st.markdown(prov_str)
                else:
                    st.markdown("<p style='color: #8b949e; font-size: 0.9rem;'>No hay plataformas registradas para tu región.</p>", unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)

            col_acc1, col_acc2 = st.columns(2)
            with col_acc1:
                if st.button("➕ Agregar a Films por ver (Watchlist)"):
                    tipo_str = "Película" if media_type == "movie" else "Serie"
                    poster_p_val = data_full.get('poster_path')
                    w_item = {
                        "tmdb_id": tmdb_id, 
                        "titulo": tit, 
                        "tipo": tipo_str, 
                        "genero": gen, 
                        "anio": an,
                        "poster_path": poster_p_val
                    }
                    if any(w.get("tmdb_id") == w_item["tmdb_id"] for w in watchlist_data):
                        st.info("Ya está en tu watchlist.")
                    else:
                        watchlist_data.append(w_item)
                        guardar_watchlist(watchlist_data)
                        st.success("✅ ¡Añadida a pendientes!")
            with col_acc2:
                if st.button("📥 Importar directo a Vistos (Dashboard)"):
                    prefix = "TMDB_MOVIE_" if media_type == "movie" else "TMDB_TV_"
                    nuevo_id = f"{prefix}{tmdb_id}"
                    df_check = dm.cargar_excel_usuario(usuario_actual)
                    if not df_check.empty and nuevo_id in df_check['ID'].values:
                        st.warning("⚠️ Ya se encuentra registrado en tu base de datos.")
                    else:
                        reg = {
                            "ID": nuevo_id, "Título": tit, "Tipo": "Película" if media_type == 'movie' else "Serie",
                            "Género": gen, "Año": an, "Duración Total": dur, "Review": "Bueno",
                            "Letterboxd": "N/A", "IMDb Rating": tmdb_r, "Rotten Tomatoes": "N/A",
                            "TMDB Rating": tmdb_r, "Serie Graph": "N/A", "Director": dir_val,
                            "Actores Principales": act, "Fecha/Hora Registro": str(pd.Timestamp.now())
                        }
                        dm.guardar_registro_usuario(usuario_actual, reg)
                        st.success("🎉 ¡Importado a tus vistos con éxito!")

# ==========================================
# 5. ANALÍTICA PREDICTIVA
# ==========================================
elif menu == "🤖 Analítica Predictiva":
    st.title("🤖 Analítica Predictiva")
    modelo, mensaje_entrenamiento = ml.entrenar_modelo_calificacion(df_global)

    if modelo is None:
        st.warning(f"⚠️ {mensaje_entrenamiento}")
    else:
        st.success(f"✅ {mensaje_entrenamiento}")
        st.markdown("### 🔮 Predictor de Calificación")
        col1, col2 = st.columns(2)
        with col1:
            anio_input = st.number_input("Año:", min_value=1900, max_value=2030, value=2026)
            tipo_input = st.selectbox("Tipo:", ["Película", "Serie"])
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Predecir Calificación"):
                es_peli = (tipo_input == "Película")
                prediccion = ml.predecir_calificacion(modelo, anio_input, es_peli)
                if prediccion is not None:
                    st.metric(label="Estimado", value=f"{prediccion} / 10")

# ==========================================
# 6. GESTIONAR BASE DE DATOS
# ==========================================
elif menu == "🗄️ Gestionar Base de Datos":
    st.title("🗄️ Gestión de Base de Datos")
    if df_global.empty:
        st.info("La base de datos está vacía.")
    else:
        lista_ids = df_global['ID'].tolist()
        id_a_borrar = st.selectbox("ID a eliminar:", lista_ids)
        if st.button("🗑️ Eliminar Registro", type="primary"):
            dm.eliminar_registro_usuario(usuario_actual, id_a_borrar)
            st.success("✅ Eliminado correctamente.")
            st.rerun()
        st.dataframe(df_global, use_container_width=True)

# ==========================================
# 🎯 RECOMENDACIONES PARA TI
# ==========================================
elif menu == "🎯 Recomendaciones para Ti":
    st.title("🎯 Recomendaciones Personalizadas")
    st.markdown("Sugerencias generadas automáticamente en función de las películas y series que has calificado positivamente en tu historial.")

    if df_global.empty:
        st.info("⚠️ Necesitas registrar al menos algunas obras vistas en tu base de datos para que el sistema pueda aprender tus gustos.")
    else:
        with st.spinner("Analizando tus gustos y consultando TMDB..."):
            recomendaciones = ml.obtener_recomendaciones_personalizadas(df_global)

        if not recomendaciones:
            st.warning("No hay suficientes datos de recomendaciones disponibles en este momento. ¡Sigue calificando más obras!")
        else:
            st.markdown(f"<p style='color: #8b949e;'>Basado en tu historial, te sugerimos estas {len(recomendaciones)} producciones:</p>", unsafe_allow_html=True)
            st.markdown("---")

            NUM_COLUMNAS = 6
            cols = st.columns(NUM_COLUMNAS)

            for idx, item in enumerate(recomendaciones):
                col_actual = cols[idx % NUM_COLUMNAS]
                poster_path = item.get('poster_path')
                titulo_item = item.get('title') or item.get('name') or "Sin Título"
                item_id = item.get('id')
                media_t = item.get('media_type', 'movie')

                with col_actual:
                    if poster_path:
                        st.image(f"https://image.tmdb.org/t/p/w300{poster_path}", use_container_width=True)
                    else:
                        st.markdown(f"**{titulo_item}**")

                    with st.popover(f"🎬 {titulo_item[:14]}..."):
                        st.markdown(f"### {titulo_item}")
                        st.caption(f"**Tipo:** {'Película' if media_t == 'movie' else 'Serie'} | ⭐ **TMDB:** {item.get('vote_average', 'N/A')}")
                        st.write(item.get('overview', 'Sin sinopsis disponible.')[:180] + "...")
                        st.markdown("---")

                        col_act1, col_act2 = st.columns(2)
                        with col_act1:
                            if st.button("➕ Watchlist", key=f"rec_w_{item_id}_{idx}"):
                                tipo_str = "Película" if media_t == "movie" else "Serie"
                                fecha_val = item.get('release_date') or item.get('first_air_date') or "0000"
                                anio_val = int(fecha_val[:4]) if fecha_val[:4].isdigit() else 0
                                w_item = {
                                    "tmdb_id": item_id, 
                                    "titulo": titulo_item, 
                                    "tipo": tipo_str, 
                                    "genero": "Desconocido", 
                                    "anio": anio_val,
                                    "poster_path": poster_path
                                }
                                if any(w.get("tmdb_id") == w_item["tmdb_id"] for w in watchlist_data):
                                    st.info("Ya en lista.")
                                else:
                                    watchlist_data.append(w_item)
                                    guardar_watchlist(watchlist_data)
                                    st.success("¡Añadida!")
                                    st.rerun()

                        with col_act2:
                            if st.button("📥 Visto", key=f"rec_imp_{item_id}_{idx}"):
                                detalles = am.obtener_detalles_completos(item_id, media_t)
                                if detalles:
                                    tit, an, dur, dir_val, act, gen, tmdb_r = detalles
                                    prefix = "TMDB_MOVIE_" if media_t == "movie" else "TMDB_TV_"
                                    nuevo_id = f"{prefix}{item_id}"
                                    df_check = dm.cargar_excel_usuario(usuario_actual)
                                    if not df_check.empty and nuevo_id in df_check['ID'].values:
                                        st.warning("Ya registrado.")
                                    else:
                                        reg = {
                                            "ID": nuevo_id, "Título": tit, "Tipo": "Película" if media_t == 'movie' else "Serie",
                                            "Género": gen, "Año": an, "Duración Total": dur, "Review": "Bueno",
                                            "Letterboxd": "N/A", "IMDb Rating": tmdb_r, "Rotten Tomatoes": "N/A",
                                            "TMDB Rating": tmdb_r, "Serie Graph": "N/A", "Director": dir_val,
                                            "Actores Principales": act, "Fecha/Hora Registro": str(pd.Timestamp.now())
                                        }
                                        dm.guardar_registro_usuario(usuario_actual, reg)
                                        st.success("¡Guardado!")
                                        st.rerun()

# ==========================================
# 🎁 MEDIA WRAPPED
# ==========================================
elif menu == "🎁 Media Wrapped":
    st.title("🎁 Tu Media Tracker Wrapped")
    st.markdown("Un recorrido visual por lo más destacado de tus hábitos de cine y series.")

    datos_w = ml.generar_datos_wrapped(df_global)

    if not datos_w:
        st.info("⚠️ Necesitas registrar obras en tu base de datos para generar tu Wrapped.")
    else:
        st.markdown("---")
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"""
                <div class="custom-card" style="text-align: center; border-left: 5px solid #ff4b4b;">
                    <h3 style="color: #8b949e; margin-bottom: 5px;">👑 GÉNERO N° 1</h3>
                    <h1 style="color: #ffffff; font-size: 2rem;">{datos_w['genero_top']}</h1>
                </div>
            """, unsafe_allow_html=True)
            
        with c2:
            st.markdown(f"""
                <div class="custom-card" style="text-align: center; border-left: 5px solid #58a6ff;">
                    <h3 style="color: #8b949e; margin-bottom: 5px;">🎬 DIRECTOR TOP</h3>
                    <h1 style="color: #ffffff; font-size: 1.8rem;">{datos_w['director_top']}</h1>
                </div>
            """, unsafe_allow_html=True)

        with c3:
            st.markdown(f"""
                <div class="custom-card" style="text-align: center; border-left: 5px solid #238636;">
                    <h3 style="color: #8b949e; margin-bottom: 5px;">⭐ ACTOR FAVORITO</h3>
                    <h1 style="color: #ffffff; font-size: 1.8rem;">{datos_w['actor_top']}</h1>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        col_w_left, col_w_right = st.columns([1, 1])

        with col_w_left:
            st.markdown(f"""
                <div class="custom-card">
                    <h2 style="color: #f0883e;">🔥 Tu Obra Insignia</h2>
                    <p style="color: #8b949e;">Calificada con la máxima distinción (Absolute Cinema):</p>
                    <h1 style="color: #ffffff; font-size: 2.2rem; margin-top: 10px;">{datos_w['cinema_top']}</h1>
                </div>
            """, unsafe_allow_html=True)

        with col_w_right:
            st.markdown(f"""
                <div class="custom-card">
                    <h2 style="color: #a371f7;">📊 Balance de Contenido</h2>
                    <p style="color: #e6edf3; font-size: 1.2rem; margin-top: 15px;">
                        🎥 <b>{datos_w['total_peliculas']}</b> Películas vistas<br>
                        📺 <b>{datos_w['total_series']}</b> Series disfrutadas<br>
                        🏆 <b>{datos_w['total_obras']}</b> Obras registradas en total
                    </p>
                </div>
            """, unsafe_allow_html=True)