import pickle
import streamlit as st
import requests
import pandas as pd
from dotenv import load_dotenv
import os

# --------------------- TMDB Fetch Function ---------------------

@st.cache_data(show_spinner=False)
def fetch_movie_details(movie_id: int):
    load_dotenv()
    API_KEY = os.getenv("API_KEY")
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}&language=en-US"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Poster
        poster_path = data.get('poster_path')
        full_poster = (
            f"https://image.tmdb.org/t/p/w500/{poster_path}"
            if poster_path
            else "https://placehold.co/500x750/333/FFFFFF?text=No+Poster"
        )

        # Year & rating
        year = data.get('release_date', 'N/A')
        year = year[:4] if year and year != 'N/A' else 'N/A'
        rating = data.get('vote_average', 'N/A')
        if rating != 'N/A':
                rating = round(float(rating), 1) 
  

        return full_poster, year, rating

    except requests.exceptions.RequestException:
        # Network or API issue fallback
        return "https://placehold.co/500x750/333/FFFFFF?text=No+Poster", "N/A", "N/A"


# --------------------- Recommendation Function ---------------------

def recommend(movie: str):
    """Recommends top 5 similar movies using similarity matrix."""
    try:
        index = movies[movies['title'] == movie].index[0]
    except IndexError:
        st.error("Movie not found in the dataset. Please select another one.")
        return [], [], [], []

    distances = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda x: x[1])

    recommended_movie_names = []
    recommended_movie_posters = []
    recommended_movie_years = []
    recommended_movie_ratings = []

    for i in distances[1:6]:
        movie_id = movies.iloc[i[0]]['movie_id']
        poster, year, rating = fetch_movie_details(movie_id)

        recommended_movie_names.append(movies.iloc[i[0]]['title'])
        recommended_movie_posters.append(poster)
        recommended_movie_years.append(year)
        recommended_movie_ratings.append(rating)

    return recommended_movie_names, recommended_movie_posters, recommended_movie_years, recommended_movie_ratings


# --------------------- Streamlit UI ---------------------

st.set_page_config(layout="wide")
st.title('🎬 Movie Recommender System Using Machine Learning')

# Load pickled model data
try:
    movies_dict = pickle.load(open('art/movie_list.pkl', 'rb'))
    movies = pd.DataFrame(movies_dict)
    similarity = pickle.load(open('art/similary.pkl', 'rb'))
except FileNotFoundError:
    st.error("Model files not found. Please ensure 'movie_list.pkl' and 'similary.pkl' are present in the 'art/' folder.")
    st.stop()

# Show dataset summary (optional)
# st.write("Columns in dataset:", movies.columns.tolist())

movie_list = movies['title'].values
selected_movie = st.selectbox("🎥 Type or select a movie from the dropdown", movie_list)

if st.button('Show Recommendation'):
    with st.spinner('Fetching best matches...'):
        names, posters, years, ratings = recommend(selected_movie)

    if names:
        cols = st.columns(5)
        for i, col in enumerate(cols):
            with col:
                st.text(names[i])
                st.image(posters[i], use_container_width=True)
                st.caption(f"Year: {years[i]}")
                st.caption(f"Rating: {ratings[i]} ⭐" if ratings[i] != 'N/A' else "Rating: N/A")
    else:
        st.warning("No recommendations available for this movie.")
