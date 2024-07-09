from flask import Flask, render_template, request, send_file
import pickle
import numpy as np
import pandas as pd
import requests
from io import BytesIO
from PIL import Image

app = Flask(__name__)

# Load pickled data
with open('data/movies.pkl', 'rb') as f:
    movies = pickle.load(f)

with open('data/similarity_words.pkl', 'rb') as f:
    similarity_words = pickle.load(f)

TMDB_API_KEY = '980b61cc43cda2cab96f39081f1075ac'

def get_movie_poster(movie_id):
    url = f'https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}&language=en-US'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        poster_path = data.get('poster_path')
        if poster_path:
            return f'https://image.tmdb.org/t/p/original{poster_path}'
    return None


# Define a function to get recommendations
def get_similar_movies(title, num_recommendations=11):
    idx = movies[movies['title'] == title].index[0]
    similar_idx = np.array([order[0] for order in 
                            sorted(enumerate(similarity_words[idx]), 
                                   key=lambda x: x[1], reverse=True)])[1:num_recommendations+1]
    similar_movies = movies.iloc[similar_idx[1:6]][['id', 'title', 'weighted_rating']] # \
            #.sort_values(by='weighted_rating', ascending=False)
    similar_movies = similar_movies[['id', 'title', 'weighted_rating']]

    return similar_movies.values.tolist()


@app.route('/poster/<movie_id>')
def get_poster(movie_id):
    poster_url = get_movie_poster(movie_id)
    if poster_url:
        response = requests.get(poster_url)
        if response.status_code == 200:
            img = Image.open(BytesIO(response.content))
            
            # Process the image (e.g., resize)
            img = img.resize((300, 450))  # Example resizing
            
            # Save the image to a BytesIO object
            img_io = BytesIO()
            img.save(img_io, 'JPEG', quality=85)  # Save as JPEG with compression
            img_io.seek(0)
            
            return send_file(img_io, mimetype='image/jpeg')

    return  "Poster not found"


# Home route
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Get the selected movie title from the form
        selected_movie = request.form.get('movie_title')
        selected_movie_id = movies[movies['title'] == selected_movie]['id'].iloc[0]
        if selected_movie:
            # Generate recommendations for the selected movie
            recommendations = get_similar_movies(selected_movie)
            return render_template('index.html', selected_movie_id = selected_movie_id, movies=movies['title'], recommendations=recommendations, selected=selected_movie, get_movie_poster=get_movie_poster)
        
    # Default: render index.html with all movies and empty recommendations
    return render_template('index.html', movies=movies['title'], recommendations=[], selected='', get_movie_poster=get_movie_poster)

if __name__ == '__main__':
    app.run(debug=True)