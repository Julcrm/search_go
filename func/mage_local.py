import pandas as pd
import requests
from datetime import datetime
from sqlalchemy import create_engine, text
import json
import requests
import streamlit as st
import folium
import streamlit.components.v1 as components
from numpy import mean
import os


class Mage_local:
    API_KEY = os.getenv('api_google')
    # Informations de connexion
    DATABASE_TYPE = os.getenv('DATABASE_TYPE')
    DBAPI = os.getenv('DBAPI')
    HOST = os.getenv('PGHOST')
    PORT = os.getenv('PGPORT')
    USER = os.getenv('PGUSER')
    PASSWORD = os.getenv('PGPASSWORD')
    DATABASE = os.getenv('PGDATABASE')




    def __init__(self):
        self.engine = create_engine(f"{Mage_local.DATABASE_TYPE}+{Mage_local.DBAPI}://{Mage_local.USER}:{Mage_local.PASSWORD}@{Mage_local.HOST}:{Mage_local.PORT}/{Mage_local.DATABASE}"),
        self.user_id = st.session_state["user_id"][1]

    
    def request_api(self, query):
        query = query
        url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query={query}&key={self.API_KEY}"
        response = requests.get(url)
        data = response.json()
        nb_result = 15

        dict_adresses = {
            
        'restaurant_id': [result['name'] + str(result['geometry']['location']['lat']) if result.get('name') else '' for result in data['results'][:nb_result]],
        'name': [result['name'] if result.get('name') else '' for result in data['results'][:nb_result]],
        'formatted_address': [result['formatted_address'] if result.get('formatted_address') else '' for result in data['results'][:nb_result]],
        'lat': [result['geometry']['location']['lat'] if result.get('geometry') and result['geometry'].get('location') else '' for result in data['results'][:nb_result]],
        'lng': [result['geometry']['location']['lng'] if result.get('geometry') and result['geometry'].get('location') else '' for result in data['results'][:nb_result]],
        'photo_reference': [result['photos'][0]['photo_reference'] if result.get('photos') else '' for result in data['results'][:nb_result]],
        'rating': [result['rating'] if result.get('rating') else '' for result in data['results'][:nb_result]],
        'user_ratings_total': [result['user_ratings_total'] if result.get('user_ratings_total') else '' for result in data['results'][:nb_result]],
        'price_level': [result['price_level'] if 'price_level' in result else 0 for result in data['results'][:nb_result]],
        'place_id': [result['place_id'] if 'place_id' in result else 0 for result in data['results'][:nb_result]]
        }

        df = pd.DataFrame(dict_adresses)
        df['rating'] = df['rating'].replace('', '0').astype(float)
        df = df.sort_values(by='rating', ascending=False).head(4)
        return df


    def api_mage(self, df):
        url_api_request_user = 'https://searchandgo-portfolio.up.railway.app/api/pipeline_schedules/2/pipeline_runs/560f7d55840746e4955611c5ebcd6f50'

        kwargs = {
                "pipeline_run": {
                    "variables": {
                    "df": df.to_json(orient='records'),
                    "user_id":self.user_id,
                    "restaurant_selected" : st.session_state["place_id"],
                    "trigger" : "chatbot"
                    }
                }
                }
        requests.post(url_api_request_user, json = kwargs)


    def api_mage_distance(self, mode, distance):
        url_api_request_user = 'https://searchandgo-portfolio.up.railway.app/api/pipeline_schedules/3/pipeline_runs/c6b9969f8e2a4352bfff35f34f73d284'

        kwargs = {
                "pipeline_run": {
                    "variables": {
                    "mode" : mode,
                    "distance": distance,
                    "user_id":self.user_id,
                    "trigger" : "distance"
                    }
                }
                }
        requests.post(url_api_request_user, json = kwargs)

    def afficher_duree(self, start_location, end_location, mode):
        # 📌 URL de l'API Google Directions
        url = f"https://maps.googleapis.com/maps/api/directions/json?origin={start_location}&destination={end_location}&mode={mode}&key={self.API_KEY}"
        # 📡 Requête à l'API
        response = requests.get(url)
        data = response.json()

        # Extraire la durée
        duree_en= data["routes"][0]["legs"][0]["duration"]["text"]
        duree_fr = duree_en


        # Dictionnaire de traduction
        translations = {
            "days": "jours",
            "day": "jour",
            "hours": "heures",
            "hour": "heure",
            "mins": "minutes"
        }

        # Traduire en français
        for eng, fr in translations.items():
            duree_fr = duree_fr.replace(eng, fr)

        return duree_fr  # ✅ Retourne la durée traduite

    def afficher_itineraire(self,start_location, end_location, mode):

        # 📌 URL de l'API Google Directions
        url = f"https://maps.googleapis.com/maps/api/directions/json?origin={start_location}&destination={end_location}&mode={mode}&key={self.API_KEY}"

        # 📡 Requête à l'API
        response = requests.get(url)
        data = response.json()

        start_lat = float(start_location.split(',')[0])
        start_lng = float(start_location.split(',')[1])


        end_lat = float(end_location.split(',')[0])
        end_lng = float(end_location.split(',')[1])

        min_lat = mean([end_lat, start_lat])
        min_lng = mean([end_lng, start_lng])


        # 🎯 Extraire les coordonnées du trajet
        route = data["routes"][0]["legs"][0]["steps"]
        km = data["routes"][0]["legs"][0]["distance"]["value"]
        route_coords = [(step["start_location"]["lat"], step["start_location"]["lng"]) for step in route]
        route_coords.append((route[-1]["end_location"]["lat"], route[-1]["end_location"]["lng"]))  # Ajouter le dernier point

        # 🗺️ Création de la carte centrée sur le trajet
        final_map = folium.Map(location=[min_lat, min_lng], zoom_start=12, tiles="https://tiles.stadiamaps.com/tiles/alidade_smooth/{z}/{x}/{y}{r}.png",
                    attr='&copy; <a ></a> ',
                               )
        fig = folium.Figure(height=600, width=550)  # Définit la taille de la carte
        final_map.add_to(fig)

        # 🔵 Ajouter les marqueurs
        folium.Marker(route_coords[0], popup="Départ - Ta position", icon=folium.DivIcon(html="""
                                                                                    <div style="text-align: center;">
                                                                                    <img src="https://i.postimg.cc/7YTGSrmN/home.png"
                                                                                    style="width: 30px; height: 30px;"><br>
                                                                                    </div>
                                                                                     """)).add_to(final_map)
        folium.Marker(route_coords[-1], popup=f"Arrivée - {st.session_state['selected']}", icon=folium.DivIcon(html="""
                                                                                    <div style="text-align: center;">
                                                                                    <img src="https://i.postimg.cc/jSQwjLmS/hat.png"
                                                                                    style="width: 30px; height: 30px;"><br>
                                                                                    </div>
                                                                                     """)).add_to(final_map)

        # 🛣️ Ajouter l'itinéraire sur la carte
        folium.PolyLine(route_coords, color="orange", weight=5, opacity=0.7).add_to(final_map)

        # 📐 Adapter le zoom pour inclure toutes les coordonnées
        final_map.fit_bounds(route_coords)

        return final_map, km

    def gps_to_address_google(self, latitude, longitude):
        url = f"https://maps.googleapis.com/maps/api/geocode/json?latlng={latitude},{longitude}&key={self.API_KEY}"

        response = requests.get(url)
        data = response.json()

        if data["status"] == "OK":
            return data["results"][0]["formatted_address"]  # Récupère la première adresse trouvée
        return "Adresse introuvable"


    def reviews(self, place_id):
        url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields=reviews&language=fr&reviews_no_translations=true&reviews_sort=newest&key={self.API_KEY}"
        response = requests.get(url)
        data = response.json()
        return data['result']['reviews']

    def phone(self, place_id):
        url= f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields=name,vicinity,formatted_phone_number&key={self.API_KEY}"
        response= requests.get(url)
        data = response.json()
        if 'formatted_phone_number' in data['result']:
            return data['result']['formatted_phone_number']
        else:
            return "Pas de numéro"

    # Fonction pour afficher le carrousel avec défilement automatique
    @staticmethod
    def show_carrousel(reviews):
        # HTML + JS pour le carrousel avec défilement automatique
        html_code = f"""
            <div id="carrousel" style="width: 100%; overflow: hidden; background-color: #0D1116;">
                <div id="carousel-items" style="display: flex; transition: transform 0.5s ease;">
            """

        for review in reviews:
            html_code += f"""
                <div class="carousel-item" style="min-width: 100%; padding: 10px; box-sizing: border-box; background-color: #0D1116; color: white;">
                    <div style="text-align: center;">
                        <h3>{review['author_name']}</h3>
                        <p>{review['text']}</p>
                        <p><strong>Note: {review['rating']}⭐</strong></p>
                    </div>
                </div>
                """

        html_code += """
                </div>
            </div>

            <script>
            let index = 0;
            const items = document.querySelectorAll('.carousel-item');
            const totalItems = items.length;

            function moveToNext() {
                index = (index + 1) % totalItems;
                updateCarousel();
            }

            function updateCarousel() {
                const carousel = document.getElementById('carousel-items');
                carousel.style.transform = 'translateX(' + (-index * 100) + '%)';
            }

            setInterval(moveToNext, 6000);  // Défilement automatique toutes les 3 secondes
            </script>
            """

        return components.html(html_code, height=400)