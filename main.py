from fastapi import FastAPI
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer

# Crea una instancia de la aplicación FastAPI y la asigna a la variable app
app = FastAPI(debug=True) # Debug me muestra en el docs de fast api el error que tira y no solo por defecto internal server error

# Carga los datos desde los CSV
steam_games = pd.read_parquet('datasets/steam_games.parquet')
users_items = pd.read_parquet('datasets/users_items.parquet')
users_reviews = pd.read_parquet('datasets/users_reviews.parquet')

# Hace que la columna "posted_year" tenga tipo de dato int
users_reviews['posted_year'] = users_reviews['posted_year'].astype(int)
# Hace que ambas columnas "item_id" en los DataFrames tengan el mismo tipo de datos
steam_games['item_id'] = steam_games['item_id'].astype(int)
users_items['item_id'] = users_items['item_id'].astype(int)
users_reviews['item_id'] = users_reviews['item_id'].astype(int)

@app.get('/bienvenido/')
def get_saludo():
    return {"mensaje": "Hola, soy Aymara Falcon y bienvenido a mi proyecto"}

@app.get('/play_time_genre/')
def PlayTimeGenre(genero: str):
    
    # Filtra los juegos por género
    juegos_genero = steam_games[steam_games['genres'] == genero]

    if juegos_genero.empty:
        return {'message': f'No se encontraron juegos para el género: {genero}'}

    # Combina los DataFrames usando la columna común 'juego_id'
    horas = pd.merge(juegos_genero, users_items, on=['item_name'])

    # Agrupa por año y suma las horas jugadas
    horas_por_anio = horas.groupby('release_year')['playtime_forever'].sum()

    # Encuentra el año con más horas jugadas
    anio_max_horas = horas_por_anio.idxmax()
    # horas_max = horas_por_anio.max()

    return {"Año de lanzamiento con más horas jugadas para genero" + str(genero) : int(anio_max_horas)}

@app.get('/user_for_genre/')
def UserForGenre(genero: str):

    # Filtra los juegos por género
    juegos_genero = steam_games[steam_games['genres'] == genero]

    if juegos_genero.empty:
        return {'message': f'No se encontraron juegos para el género: {genero}'}

    # Combina los DataFrames usando la columna común 'item_name'
    datos_genero = pd.merge(juegos_genero, users_items, on=['item_id'])

    if datos_genero.empty:
        return {'message': f'No se encontraron datos para el género: {genero}'}

    # Agrupa por usuario y suma las horas jugadas
    horas_por_usuario = datos_genero.groupby('user_id')['playtime_forever'].sum()

    # Encuentra el usuario con más horas jugadas
    usuario_max_horas = horas_por_usuario.idxmax()
    horas_max = horas_por_usuario.max()

    return {
        "Usuario con más horas jugadas para el género" + str(genero): usuario_max_horas,
        "Horas jugadas por el usuario": int(horas_max)
    }

def UserForGenre(genero: str):

    # Filtra los juegos por género
    juegos_genero = steam_games[steam_games['genres'] == genero]

    if juegos_genero.empty:
        return {'message': f'No se encontraron juegos para el género: {genero}'}

    # Combina los DataFrames usando la columna común 'item_name'
    datos_genero = pd.merge(juegos_genero, users_items, on=['item_id'])

    genero_df = datos_genero[datos_genero['genres'].str.contains(genero, case=False)]

    if datos_genero.empty:
        return {'message': f'No se encontraron datos para el género: {genero}'}

    # Agrupa por usuario y suma las horas jugadas
    usuario_mas_horas = genero_df.loc[genero_df['playtime_forever'].idxmax(), 'user_id']

    # Encuentra el usuario con más horas jugadas
    horas_por_anio = genero_df.groupby('release_year')['playtime_forever'].sum().reset_index()
    acumulacion_horas = [{"Año": int(row[1]['release_year']), "Horas": int(row[1]['playtime_forever'])} for row in horas_por_anio.iterrows()]

    return {
        "Usuario con más horas jugadas para " + genero: usuario_mas_horas,
        "Horas jugadas": acumulacion_horas
    }

@app.get('/users_recommend/')
def UsersRecommend(anio: int):

    # Filtrar recomendaciones positivas (sentiment_analysis = 1 o 2) y para el año especificado
    recomendaciones = users_reviews[(users_reviews['recommend'] == True) & ((users_reviews['sentiment_analysis'] == 1) | (users_reviews['sentiment_analysis'] == 2)) & (users_reviews['posted_year'] == anio)]

    if recomendaciones.empty:
        return {'message': f'No se encontraron recomendaciones para el año: {anio}'}

    # Combinar con los datos de juegos
    datos_completos = pd.merge(recomendaciones, steam_games, on=['item_id'])

    if datos_completos.empty:
        return {'message': f'No se encontraron datos de juegos para las recomendaciones del año: {anio}'}

    # Obtener el top 3 de juegos más recomendados
    top_3_juegos = datos_completos['item_name'].value_counts().head(3).index.tolist()

    # Formatear la respuesta
    respuesta = [{"Puesto 1": top_3_juegos[0]}, {"Puesto 2": top_3_juegos[1]}, {"Puesto 3": top_3_juegos[2]}]

    return respuesta

@app.get('/users_not_recommend/')
def UsersNotRecommend(anio: int):
    # Filtrar recomendaciones positivas (sentiment_analysis = 1 o 2) y para el año especificado
    recomendaciones = users_reviews[(users_reviews['recommend'] == False) & ((users_reviews['sentiment_analysis'] == 0)) & (users_reviews['posted_year'] == anio)]

    if recomendaciones.empty:
        return {'message': f'No se encontraron recomendaciones para el año: {anio}'}

    # Combinar con los datos de juegos
    datos_completos = pd.merge(recomendaciones, steam_games, on=['item_id'])

    if datos_completos.empty:
        return {'message': f'No se encontraron datos de juegos para las recomendaciones del año: {anio}'}

    # Obtener el top 3 de juegos menos recomendados
    top_3_juegos = datos_completos['item_name'].value_counts().head(3).index.tolist()

    # Formatear la respuesta
    respuesta = [{"Puesto 1": top_3_juegos[0]}, {"Puesto 2": top_3_juegos[1]}, {"Puesto 3": top_3_juegos[2]}]

    return respuesta

@app.get('/sentiment_analysis/')
def SentimentAnalysis(anio: int):
    # Filtrar reseñas para el año especificado
    reseñas_por_anio = users_reviews[users_reviews['posted_year'] == anio]

    if reseñas_por_anio.empty:
        return {'message': f'No se encontraron reseñas para el año: {anio}'}

    # Contar la cantidad de reseñas por categoría de sentiment_analysis
    conteo_sentimiento = reseñas_por_anio['sentiment_analysis'].value_counts().to_dict()

    # Formatear la respuesta
    return {
        "Negative": conteo_sentimiento.get(0, 0),
        "Neutral": conteo_sentimiento.get(1, 0),
        "Positive": conteo_sentimiento.get(2, 0)
    }

muestra_steam_games = steam_games.head(20000)

@app.get('/recomendacion_juego/')
def recomendacion_juego(game_id:int, top_n=5): #Creo la funcion que toma como parametros la id del juego en game_id y los otros son hiperparametros que defino
    tfidf_vectorizer = TfidfVectorizer()

    #Con esto los datos de la columna genero se transforman en vectores numericos para porder entrenarlos y luego los entreno
    tfidf_matrix = tfidf_vectorizer.fit_transform(muestra_steam_games['genres'])

    #Aca compara los cosenos de los vectores para encontrar similitudes
    cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)
    
    # Busca el indice del juego del que ingrese el ID
    idx = None
    idx_list = muestra_steam_games.index[muestra_steam_games['item_id'] == game_id].tolist()
    recommended_indices = []  # Inicializa como una lista vacía
    if idx_list:
        idx = idx_list[0]
    # Continúa con el procesamiento
    if idx is not None:
    # No se encontró ninguna coincidencia, maneja esto adecuadamente
        sim_scores = list(enumerate(cosine_sim[idx]))# Optiene la puntuacion de similitud de los cosenos
        sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True) # Ordena los juegos por la similitud
        top_n = int(top_n)
        recommended_indices = [i[0] for i in sim_scores[1:top_n+1]]  # Obtiene los indices de los juegos recomendados
    return set(muestra_steam_games['item_name'].iloc[recommended_indices]) # Devuelve los titulos de los juegos recomendados

@app.get('/recomendacion_usuario/')
def recomendacion_usuario(id:str):
    aux = users_reviews[users_reviews['user_id'] == id]
    aux.reset_index(drop=True, inplace=True)

    if not aux.empty:  # Verifica si hay datos en 'aux'
        game_id = aux['item_id'].iloc[0]  # Toma el 'item_id' del primer juego del usuario
        recommended_games = recomendacion_juego(game_id=int(game_id))  # Llama a la función
        return recommended_games  # Devuelve las recomendaciones
    else:
        return []  # Retorna una lista vacía si no se encontraron datos para ese usuario