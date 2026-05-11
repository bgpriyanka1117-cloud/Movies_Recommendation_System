import streamlit as st
import pickle
import pandas as pd
import requests
import base64
import ast

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="AI Movie Recommender",
    page_icon="🎬",
    layout="wide"
)

# =========================
# SESSION STATE
# =========================
if "selected_trailer" not in st.session_state:
    st.session_state.selected_trailer = None


# =========================
# STYLE
# =========================
st.markdown("""
<style>

.stApp {
    background: linear-gradient(rgba(0,0,0,0.75), rgba(0,0,0,0.85)),
    url("https://images.unsplash.com/photo-1524985069026-dd778a71c7b4");
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
}

.title {
    text-align:center;
    font-size:42px;
    color:white;
    font-weight:800;
}

img {
    border-radius: 12px;
}

.download-btn {
    width: 100%;
    background: linear-gradient(135deg, #ff416c, #ff4b2b);
    color: white;
    padding: 5px;
    border: none;
    border-radius: 6px;
    font-size: 11px;
    cursor: pointer;
}

.download-btn:hover {
    opacity: 0.9;
}

</style>
""", unsafe_allow_html=True)

st.markdown("<div class='title'>🎬 AI Movie Recommendation System</div>", unsafe_allow_html=True)


# =========================
# LOAD DATA
# =========================
@st.cache_data
def load_data():
    movies = pd.DataFrame(pickle.load(open("movies.pkl", "rb")))
    similarity = pickle.load(open("similarity.pkl", "rb"))
    return movies, similarity

movies, similarity = load_data()


# =========================
# FUNCTIONS
# =========================

def fetch_poster(movie):
    try:
        url = "https://api.themoviedb.org/3/search/movie?api_key=YOUR_API_KEY&query=" + movie
        data = requests.get(url).json()

        if data.get("results") and data["results"][0].get("poster_path"):
            return "https://image.tmdb.org/t/p/w500/" + data["results"][0]["poster_path"]

        return "https://via.placeholder.com/300x450.png?text=No+Poster"

    except:
        return "https://via.placeholder.com/300x450.png?text=No+Poster"


def watch_links(movie):
    query = movie.replace(" ", "+")
    return {
        "YouTube": f"https://www.youtube.com/results?search_query={query}+full+movie",
        "Google": f"https://www.google.com/search?q={query}+watch+online",
        "IMDb": f"https://www.imdb.com/find/?q={query}",
        "JustWatch": f"https://www.justwatch.com/in/search?q={query}"
    }


def download_image(url):
    try:
        return requests.get(url).content
    except:
        return None


# =========================
# FIXED GENRES FUNCTION
# =========================
def extract_genres(row):

    if 'genres' in movies.columns:
        try:
            g = row['genres']

            if isinstance(g, str):
                try:
                    g = ast.literal_eval(g)
                except:
                    return g

            if isinstance(g, list):
                return ", ".join([i['name'] for i in g if 'name' in i])

            return str(g)

        except:
            return "N/A"

    elif 'tags' in movies.columns:
        return row['tags']

    return "N/A"


# =========================
# MOVIE INFO (FIXED)
# =========================
def clean_description(text):

    if not isinstance(text, str):
        return "No description available."

    # split and remove duplicates
    words = text.split()

    seen = set()
    clean_words = []

    for w in words:
        if w.lower() not in seen:
            clean_words.append(w)
            seen.add(w.lower())

    sentence = " ".join(clean_words)

    # better formatting
    sentence = sentence.replace("-", " ").replace("_", " ")
    sentence = sentence.capitalize()

    return sentence


def movie_info(movie):

    row = movies[movies['title'] == movie]

    if row.empty:
        return "No data found."

    row = row.iloc[0]

    title = row['title']
    movie_id = row['movie_id'] if 'movie_id' in movies.columns else "N/A"

    if 'overview' in movies.columns:
        raw = row['overview']
    elif 'tags' in movies.columns:
        raw = row['tags']
    else:
        raw = ""

    description = clean_description(raw)

    return f"""
🎬 Movie Details

Title: {title}
Movie ID: {movie_id}

📖 Description:
{description}

🤖 Recommended by priyanka's AI System
"""

# =========================
# RECOMMEND FUNCTION
# =========================
def recommend(movie):

    idx = movies[movies['title'] == movie].index[0]
    distances = similarity[idx]

    movie_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]

    names, posters = [], []

    for i in movie_list:
        title = movies.iloc[i[0]].title
        names.append(title)
        posters.append(fetch_poster(title))

    return names, posters


# =========================
# SEARCH UI
# =========================
search = st.text_input("🔍 Search Movies")

filtered_movies = movies['title'].values

if search:
    filtered_movies = movies[movies['title'].str.contains(search, case=False)]['title'].values

movie = st.selectbox("🎥 Choose a Movie", filtered_movies)


# =========================
# RECOMMENDATION UI
# =========================
if st.button("🚀 Get Recommendations"):

    names, posters = recommend(movie)

    st.subheader("🔥 Recommended Movies")

    for i in range(len(names)):

        col1, col2, col3 = st.columns([1, 3, 2])

        with col1:
            img = download_image(posters[i])
            if img:
                st.image(posters[i], width=120, caption="🎬 Poster")

                st.download_button(
                    label="📥 Poster",
                    data=img,
                    file_name=f"{names[i]}.jpg",
                    mime="image/jpeg",
                    use_container_width=True
                )

        with col2:
            st.markdown(f"### 🎬 {names[i]}")
            st.caption("AI Recommendation Engine")

        with col3:

            links = watch_links(names[i])

            st.markdown("### 🌐 Watch Options")

            st.link_button("▶ YouTube", links["YouTube"])
            st.link_button("🔎 Google", links["Google"])
            st.link_button("🎬 IMDb", links["IMDb"])
            st.link_button("📺 JustWatch", links["JustWatch"])

            info = movie_info(names[i])
            b64 = base64.b64encode(info.encode()).decode()

            st.markdown(f"""
            <a href="data:file/txt;base64,{b64}" download="{names[i]}.txt">
                <button class="download-btn">
                    📥 Download Info
                </button>
            </a>
            """, unsafe_allow_html=True)


# =========================
# FOOTER
# =========================
st.markdown("---")

st.markdown("""
<div style="
    text-align:center;
    color:white;
    font-size:14px;
    opacity:0.9;
">
    🚀 Built with Streamlit + Machine Learning<br>
    <b>© 2026 Priyanka Kumari | All Rights Reserved</b>
</div>
""", unsafe_allow_html=True)