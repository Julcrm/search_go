import json
import requests
import pandas as pd
from func.gepetto import Robot_bistro
from PIL import Image
from io import BytesIO
import folium
from func.mage_local import Mage_local
from streamlit_js_eval import get_geolocation
from streamlit_float import *
import streamlit.components.v1 as components
import time
from streamlit_option_menu import option_menu
from dash_user import dash_user
from func.SQL_user import SQL_user
import streamlit as st
import os


def chatbot():
    mage_local = Mage_local()
    sql_user = SQL_user()

    if "page" not in st.session_state:
        st.session_state.page = "chat"

    def set_page(page_name):
        st.session_state.page = page_name


    API_KEY = os.getenv('api_google')

    if st.session_state.page == "chat":

        # Initialisation de l'étape courante dans session_state si elle n'existe pas
        if "current_step" not in st.session_state:
            st.session_state["current_step"] = "🤖 Discute avec Robot bistro"


        if 'dico' not in st.session_state:
            st.session_state.dico = dict()

        if "has_moved_to_step_2" not in st.session_state:
            st.session_state["has_moved_to_step_2"] = False

        # Fonction pour ajouter un message et générer une réponse avec contexte
        def addtext():
            user_input = st.session_state["prompt"]  # Récupère le message utilisateur
            if user_input:
                # Ajoute le message utilisateur à l'historique
                st.session_state.messages.append({"role": "user", "text": user_input})

                # Stockage temporaire des réponses utilisateur (tous les messages de type 'user')
                st.session_state["history"] = []
                for message in st.session_state.messages:
                    if message["role"] == "user":
                        st.session_state["history"].append(message["text"])

            # Crée un contexte pour le chatbot en concaténant les anciens messages
            context = "\n".join([msg["text"] for msg in st.session_state.messages])

            # Obtenir la réponse du bot en lui donnant le contexte
            response_bot = st.session_state["robot"].talk(context)

            # Ajoute la réponse du bot à l'historique
            st.session_state.messages.append({"role": "assistant", "text": response_bot})



        if st.session_state["current_step"] == "🤖 Discute avec Robot bistro":

            # Liste des étapes
            options_1 = ["🤖 Discute avec Robot bistro"]

            # Affichage des étapes avec st.pills
            selection_1 = st.pills("Les étapes :", options_1, selection_mode="single",default=st.session_state["current_step"])

            st.divider()

            # Si l'utilisateur a choisi une autre étape, on met à jour l'état
            if selection_1 != st.session_state["current_step"]:
                # Delete all the items in Session state
                for key in st.session_state.keys():
                    if key not in ["user_id", "authenticated", "current_page"]:
                        del st.session_state[key]
                    else:
                        pass
                st.session_state["current_step"] = selection_1
                st.rerun()

            # Disposition des colonnes pour l'affichage avec Streamlit
            chat_col, empty_col, img_col = st.columns([1.5, 0.1, 1])
            with img_col:
                st.image("img/Leonardo_Phoenix_09_a_whimsical_cartoon_illustration_of_a_robo_1.jpg", width=500)  # Ajuste la largeur à 500 pixels
            with chat_col:
                if "user_location" not in st.session_state:
                    st.session_state["user_location"] = ()
                    # Récupération de la localisation de l'utilisateur
                location_data = get_geolocation()
                user_location = None

                if location_data:
                    user_lat = location_data.get("coords", {}).get("latitude")
                    user_lon = location_data.get("coords", {}).get("longitude")
                    if user_lat and user_lon:
                        st.session_state["user_location"] = (user_lat, user_lon)
                    else:
                        st.warning("Impossible d'obtenir votre localisation. Assurez-vous que la géolocalisation est activée.")

                # Initialisation du chatbot
                if "robot" not in st.session_state:
                    st.session_state["robot"] = Robot_bistro()
                    st.session_state["robot"].preprompt("prompt/robot_chat.txt")

                # Initialisation de l'historique des messages
                if "messages" not in st.session_state:
                    st.session_state.messages = []

                avatar_bot = "img/icons8-robot-100.png"
                avatar_user = "img/user.png"
                # Affiche le message de bienvenue avec l'avatar du chatbot
                st.chat_message("assistant", avatar=avatar_bot).write(st.session_state["robot"].get_welcome())

                # Affiche les messages précédents dans l'ordre chronologique
                for message in st.session_state.messages:
                    avatar = avatar_user if message["role"] == "user" else avatar_bot  # Choix de l'avatar
                    st.chat_message(message["role"], avatar=avatar).write(message["text"])
                action_buttons_container = st.container(key="testcont")

                # Espacement entre les icônes
                cols_dimensions = [20, 29, 40, 9]
                col1, col2, col3, col4= action_buttons_container.columns(cols_dimensions)


                with col2:
                    # Bouton pour effacer le chat
                    if st.button("Réinitialiser le Chat 🧹"):
                        st.session_state["messages"] = []
                        st.rerun()

                with col3:
                    icon = "😩 J'ai FAIMMMM !!! 😩"
                    if st.button(icon):
                        if "history" not in st.session_state:
                            st.session_state["history"] = []
                        df_resto = sql_user.listing_resto(st.session_state['user_id'][1])
                        category_counts = df_resto['Catégorie'].value_counts()
                        df_favorite = pd.DataFrame(category_counts).reset_index()
                        adresse = mage_local.gps_to_address_google(user_lat, user_lon)

                        phrase = f"Je veux manger {df_favorite['Catégorie'].iloc[0]} , à cette adresse {adresse} pas de budget et de régime alimentaire particulier"
                        st.toast(f'Vous avez faim et vous aimez la {df_favorite["Catégorie"].iloc[0]}')
                        time.sleep(.5)
                        st.toast("Allez Go !! je m'occupe de vous trouvez ça", icon='🎉')
                        time.sleep(.5)

                        st.session_state["history"].append(phrase)
                        query = st.session_state["robot"].talk(phrase)


                        st.session_state["history"].append(query)
                        st.session_state["robot_hist"] = Robot_bistro()
                        st.session_state["robot_hist"].preprompt("prompt/robot_hist.txt")
                        history = st.session_state["robot_hist"].talk(st.session_state["history"])


                         # Stockage des informations extraites
                        st.session_state["extracted_info"] = history
                        # Marque que l'étape 2 a été atteinte pour éviter la boucle infinie
                        st.session_state["has_moved_to_step_2"] = True
                        st.session_state["current_step"] = "🍽️ Trouve ton resto idéal"
                        st.rerun()



                # Barre de saisie en bas, juste après les boutons
                st.chat_input("Faites une demande", key="prompt", on_submit=addtext)




            # Vérification de la présence du message spécifique
            if any("Très bien. Tout est bon, je lance la recherche !" in msg["text"] for msg in
                   st.session_state.messages) and not st.session_state["has_moved_to_step_2"]:
                # Création de Robot_hist pour extraire les informations
                st.session_state["robot_hist"] = Robot_bistro()
                st.session_state["robot_hist"].preprompt("prompt/robot_hist.txt")

                history = [f'{dico["role"]}:{dico["text"]}' for dico in st.session_state.messages]
                st.session_state["robot_hist"].talk(history)

                # Stockage des informations extraites
                st.session_state["extracted_info"] = st.session_state["robot_hist"].talk(history)
            # Marque que l'étape 2 a été atteinte pour éviter la boucle infinie
                st.session_state["has_moved_to_step_2"] = True
                st.session_state["current_step"] = "🍽️ Trouve ton resto idéal"
                st.rerun()


         # Fonction pour récupérer et redimensionner l'image
        def get_resized_image(photo_reference, size=(200, 200)):
            default_img = Image.open("img/icons8-robot-100.png").resize((200, 200))  # Image par défaut
            image_url = "https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photo_reference="
            if not photo_reference:
                return default_img
            try:
                img_url = f"{image_url}{photo_reference}&key={API_KEY}"
                response = requests.get(img_url)
                if response.status_code == 200:
                    img = Image.open(BytesIO(response.content)).resize(size)
                    return img
            except Exception:
                pass
            return default_img  # En cas d'erreur, renvoyer l'image par défaut



        # Vérifier que la session est au bon état
        if st.session_state["current_step"] == "🍽️ Trouve ton resto idéal":

            options_2 = ["🤖 Discute avec Robot bistro", "🍽️ Trouve ton resto idéal"]

            # Affichage des étapes avec st.pills
            selection_2 = st.pills("Les étapes :", options_2, selection_mode="single",default=st.session_state["current_step"])

            if selection_2 != st.session_state["current_step"]:
                if  selection_2 == "🤖 Discute avec Robot bistro":              # Delete all the items in Session state
                    for key in st.session_state.keys():
                        if key not in ["user_id", "authenticated", "current_page"]:
                            del st.session_state[key]
                    st.session_state["current_step"] = selection_2
                    st.rerun()
                else:
                    st.session_state["current_step"] = selection_2
                    st.rerun()


            st.divider()

            # URL de l'API de l'image
            if "selected" not in st.session_state:
                st.session_state["selected"] = ""


            df = mage_local.request_api(st.session_state["extracted_info"]) #st.session_state['user_id'][1])


            if len(df)>0:
                # Créer 3 colonnes
                cols = st.columns([2, 2, 3])

                # Affichage des résultats dans les 3 colonnes
                for i, row in enumerate(df.itertuples()):
                    if i < 2:  # Affichage des deux premiers restaurants dans la première colonne
                        col = cols[0]
                    elif i < 4:  # Affichage des deux autres restaurants dans la troisième colonne
                        col = cols[1]
                    else:
                        continue  # Si tu as moins de 4 restaurants, on ne continue pas à afficher

                    with col:
                        # Bouton de sélection avec une clé unique
                        if st.button(f"Choisir {row.name}", key=f"select_restaurant_{i}"):
                            st.session_state.update({
                                "selected": row.name,
                                "lat": row.lat,
                                "lng": row.lng,
                                "formated_address_selected": row.formatted_address,
                                "rating_selected": row.rating,
                                "user_ratings_total_selected": row.user_ratings_total,
                                "photo_reference_selected": row.photo_reference,
                                "location_selected": [row.lat, row.lng],
                                "place_id" : row.place_id,
                                "current_step": "🏁 À table !"
                            })
                            mage_local.api_mage(df)
                            st.rerun()

                        # Image redimensionnée avec alignement centré
                        img = get_resized_image(row.photo_reference)
                        st.image(img, width=200)

                        # Bloc texte avec hauteur fixe pour alignement
                        st.markdown(
                            f'<div style="height: 40px;">⭐ Note : {row.rating}</div>',
                            unsafe_allow_html=True
                        )
                        st.markdown(
                            f'<div style="height: 40px;">👥 Votes : {row.user_ratings_total}</div>',
                            unsafe_allow_html=True
                        )
                        st.markdown(
                            f'<div style="height: 50px; max-width: 200px; word-wrap: break-word;">📍 Adresse : {row.formatted_address}</div>',
                            unsafe_allow_html=True
                        )
                        st.write("")
                        st.write("")
                        st.write("")
                        st.write("")
                        st.markdown("<hr style='border: 1px solid #ddd; width: 80%;'>", unsafe_allow_html=True)




                # Affichage de la carte dans la deuxième colonne
                locations = df[['lat', 'lng']].values.tolist()
                mean_lat = df['lat'].mean()
                mean_lng = df['lng'].mean()
                map_folium = folium.Map(
                    location=[mean_lat, mean_lng],  # Coordonnées pour centrer la carte
                    zoom_start=13,  # Zoom initial plus large
                    tiles="https://tiles.stadiamaps.com/tiles/alidade_smooth/{z}/{x}/{y}{r}.png",
                    attr='&copy; <a href="https://stadiamaps.com/">Stadia Maps</a>',
                )

                # Boucle pour ajouter les marqueurs
                for i, (lat, lng) in enumerate(locations):
                    popup_html = f"""
                    <div style='width:300px'>
                    <b>Nom :</b> {df.iloc[i]["name"]} 🏙️<br>
                    <b>Note :</b> {df.iloc[i]["rating"]} ⭐<br>
                    </div>
                    """

                    folium.Marker(
                        location=[lat, lng],
                        tooltip="Plus d'informations !",
                        popup=popup_html,  # Récupère le nom du restaurant correspondant
                        icon=folium.DivIcon(html="""
                               <div style="text-align: center;">
                                   <img src="https://i.postimg.cc/jSQwjLmS/hat.png"
                                   style="width: 30px; height: 30px;"><br>
                               </div>
                           """)
                ).add_to(map_folium)

                fig = folium.Figure(height=650, width=560)  # Définit la taille de la carte
                map_folium.add_to(fig)

                # Afficher la carte dans la deuxième colonne
                with cols[2]:
                    st.markdown("<h3 style='text-align: center;'>Carte des restaurants</h3>", unsafe_allow_html=True)
                    st.write("")
                    st.write("")
                    st.write("")
                    st.write("")
                    st.write("")
                    col_empty_1, col_map1, col_empty_2 = st.columns([0.3, 2, 2])
                    with col_map1:
                     st.components.v1.html(map_folium._repr_html_(), height=650, width=560)
            else:
                st.write("J'ai épluché le net et malgré mes recherches je n'ai trouvé aucune perle à vous proposer")


        if st.session_state["current_step"] == "🏁 À table !":

            options_3 = ["🤖 Discute avec Robot bistro", "🍽️ Trouve ton resto idéal", "🏁 À table !"]

            # Affichage des étapes avec st.pills
            selection_3 = st.pills("Les étapes :", options_3, selection_mode="single",default=st.session_state["current_step"])

            st.divider()

            if selection_3 != st.session_state["current_step"]:
                if selection_3 == "🤖 Discute avec Robot bistro":  # Delete all the items in Session state
                    for key in st.session_state.keys():
                        if key not in ["user_id", "authenticated", "current_page"]:
                            del st.session_state[key]
                    st.session_state["current_step"] = selection_3
                    st.rerun()
                else:
                    st.session_state["current_step"] = selection_3
                    st.rerun()

            if "mode" not in st.session_state:
                st.session_state["mode"] = "driving"

            # 📍 Coordonnées de départ et d'arrivée
            start_location = f"{st.session_state['user_location'][0]}, {st.session_state['user_location'][1]}"
            end_location = f"{st.session_state['lat']}, {st.session_state['lng']}"

            # Affichage initial de la carte avec mode "driving"
            driving_map, driving_km = mage_local.afficher_itineraire(start_location, end_location, st.session_state["mode"])

            walking_map, walking_km = mage_local.afficher_itineraire(start_location, end_location, st.session_state["mode"])

            cols = st.columns([2, 0.7, 0.2, 0.1, 3])

            with cols[4]:
                st.markdown(
                    """
                    <div style="text-align: center;">
                        <h3>📍 Sélection :</h3>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                st.write(f"<div style='text-align: center;'>{st.session_state['selected']}</div>", unsafe_allow_html=True)
                st.write("")
                # Image redimensionnée et centrée
                img = get_resized_image(st.session_state["photo_reference_selected"])

                col_empty_m1, col_empty_m2, col_map = st.columns([0.5, 1, 3])  # Deux sous-colonnes

                with col_map:
                    st.image(img)

                st.markdown("""<div style="text-align: center;"><h3>🏠 Adresse :</h3></div>""",unsafe_allow_html=True)

                st.write(f"<div style='text-align: center;'>{st.session_state['formated_address_selected']}</div>",unsafe_allow_html=True)

                phone = mage_local.phone(st.session_state["place_id"])

                st.markdown("")

                st.markdown("""<div style="text-align: center;">   <h3>☎️ Téléphone :</h3> </div>  """, unsafe_allow_html=True)

                st.write(f"<div style='text-align: center;'>{phone}</div>",unsafe_allow_html=True)

                st.markdown("<hr style='border: 1px solid #ddd; width: 100%;'>", unsafe_allow_html=True)

                st.markdown("""<div style="text-align: center;"> <h3>⭐ Avis :</h3></div>""",unsafe_allow_html=True)

                reviews = mage_local.reviews(st.session_state["place_id"])

                if len(reviews) >0:
                    # Afficher le carrousel dans l'app Streamlit
                    mage_local.show_carrousel(reviews)

            with cols[0]:  # Même colonne pour le toggle et le bouton
                col_toggle, col_empty, col_button = st.columns([5, 0.5, 1])  # Deux sous-colonnes

                with col_toggle:
                    walking = st.toggle("Y aller à pied", key="toggle")

                if walking:
                    st.session_state["mode"] = "walking"
                    walking_duree = mage_local.afficher_duree(start_location, end_location, st.session_state["mode"])
                    st.markdown(f"""<div style="font-size: 1.25rem; font-weight: bold;">Temps de trajet : {walking_duree} &nbsp;&nbsp; <img src="https://i.ibb.co/LhJVnC1m/walking.png" width="40"></div>""", unsafe_allow_html=True)

                else:
                    st.session_state["mode"] = "driving"
                    driving_duree = mage_local.afficher_duree(start_location, end_location, st.session_state["mode"])
                    st.markdown(f"""<div style="font-size: 1.25rem; font-weight: bold;">Temps de trajet : {driving_duree} &nbsp;&nbsp; <img src="https://i.ibb.co/qFFFybvZ/car-1.png" width="40"></div>""", unsafe_allow_html=True)

                if st.session_state["mode"] == "driving":
                    st.components.v1.html(driving_map._repr_html_(), height=600, width=550)
                else:
                    st.components.v1.html(walking_map._repr_html_(), height=600, width=550)

                with col_button:
                    if st.button("GO !!", key="go"):
                        if st.session_state["mode"] == "driving":
                            mage_local.api_mage_distance(st.session_state["mode"],driving_km)
                        else:
                            mage_local.api_mage_distance(st.session_state["mode"], walking_km)
                        st.toast("C'est parti ! Le trajet a été ajouté à votre tableau de bord 🎉")
                        st.session_state['current_step'] = 'Go !'
                        st.rerun()

        if st.session_state["current_step"] == "Go !":

            options_3 = ["🤖 Discute avec Robot bistro", "🍽️ Trouve ton resto idéal", "🏁 À table !", "Go !"]

            # Affichage des étapes avec st.pills
            selection_3 = st.pills("Les étapes :", options_3, selection_mode="single",default=st.session_state["current_step"])

            st.divider()

            if selection_3 != st.session_state["current_step"]:
                if selection_3 == "🤖 Discute avec Robot bistro":  # Delete all the items in Session state
                    for key in st.session_state.keys():
                        if key not in ["user_id", "authenticated", "current_page"]:
                            del st.session_state[key]
                    st.session_state["current_step"] = selection_3
                    st.rerun()
                else:
                    st.session_state["current_step"] = selection_3
                    st.rerun()


            cols1, cols2 = st.columns(2)

            with cols2:
                st.markdown(
                    """
                    <div style="text-align: center;">
                        <h3>📍 Sélection :</h3>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                st.write(f"<div style='text-align: center;'>{st.session_state['selected']}</div>", unsafe_allow_html=True)
                st.write("")
                # Image redimensionnée et centrée
                img = get_resized_image(st.session_state["photo_reference_selected"])

                col_empty_m1, col_empty_m2, col_map = st.columns([0.5, 1, 3])  # Deux sous-colonnes

                with col_map:
                    st.image(img)

                st.markdown("""<div style="text-align: center;"><h3>🏠 Adresse :</h3></div>""",unsafe_allow_html=True)

                st.write(f"<div style='text-align: center;'>{st.session_state['formated_address_selected']}</div>",unsafe_allow_html=True)

                phone = mage_local.phone(st.session_state["place_id"])

                st.markdown("")

                st.markdown("""<div style="text-align: center;">   <h3>☎️ Téléphone :</h3> </div>  """, unsafe_allow_html=True)

                st.write(f"<div style='text-align: center;'>{phone}</div>",unsafe_allow_html=True)

                st.markdown("<hr style='border: 1px solid #ddd; width: 100%;'>", unsafe_allow_html=True)

                st.markdown("""<div style="text-align: center;"> <h3>⭐ Avis :</h3></div>""",unsafe_allow_html=True)

                reviews = mage_local.reviews(st.session_state["place_id"])

                if len(reviews) >0:
                    # Afficher le carrousel dans l'app Streamlit
                    mage_local.show_carrousel(reviews)

            with cols1: 

                st.markdown("""
        <style>
        @import url('https://fonts.bunny.net/css?family=bad-script:400');

        .handwritten {
            font-family: 'Bad Script', cursive;
            font-size: 48px;
            text-align: center;
        }
        .bonappetit {
            font-family: 'Bad Script', cursive;
            font-size: 48px;
            text-align: center;
        }
        .bottom-right {
            position: absolute;
            bottom: 10px;
            right: 10px;
            font-family: 'Bad Script', cursive;
            font-size: 30px;
        }
        </style>
        """, unsafe_allow_html=True)
                st.write("")
                st.write("")
                st.write("")
                st.markdown('<div class="handwritten">Merci d\'avoir choisi Bistro Robot</div>', unsafe_allow_html=True)
                st.write("")
                st.markdown('<div class="bonappetit">Bon appétît</div>', unsafe_allow_html=True)
                st.write("")
                st.write("")
                st.write("")
                st.write("")
                st.write("")
                # Ajouter un délai de quelques secondes
                time.sleep(3)
                st.markdown('<div class="bottom-right">Merci Léo</div>', unsafe_allow_html=True)
                time.sleep(2)
                st.balloons()


        with st.sidebar:
            val_menu = option_menu(menu_title=None, options=["Robot Bistro", "Tableau de bord", "Déconnexion"],
                                   icons=['house', 'graph-up-arrow', "box-arrow-left"])
            if val_menu == "Robot Bistro":
                set_page("chat")
            if val_menu == "Tableau de bord":
                set_page("dash_user")
                st.rerun()
            if val_menu == "Déconnexion":
                for key in st.session_state.keys():
                    if key not in ["current_page"]:
                        del st.session_state[key]
                if "current_page" not in st.session_state:
                    st.session_state["current_page"] = "Landing"
                st.rerun()

        


    elif st.session_state.page == "dash_user":
        dash_user()

    st.markdown(
        """
        <style>
            /* Arrière-plan des composants */
            .st-emotion-cache-janbn0 {
                background-color: rgba(255, 112, 67, 0.9) !important;
            }
            .st-emotion-cache-4oy321 {
                background-color: rgba(213, 220, 220, 0.5) !important;
            }
    
            /* Effet hover sur certains éléments interactifs */
            .st-emotion-cache-1wtrl3u:hover {
                color : rgba(255, 112, 67, 0.9);
                border: 1px solid rgba(255, 112, 67, 0.9);
                height: 2.5rem; /* Augmenter la hauteur du bouton */
                max-width: 48rem; /* Augmenter la largeur maximale */
                padding: 0.35rem 0.80rem; /* Augmenter le padding pour élargir le bouton */
    
            }
            .st-emotion-cache-1d25zpz:hover {
                color : rgba(255, 112, 67, 0.9);
                border: 1px solid rgba(255, 112, 67, 0.9);
                height: 2.5rem; /* Augmenter la hauteur du bouton */
                max-width: 48rem; /* Augmenter la largeur maximale */
                padding: 0.35rem 0.80rem; /* Augmenter le padding pour élargir le bouton */
    
            }
    
            .st-emotion-cache-1d25zpz {
                height: 2.5rem; /* Augmenter la hauteur du bouton */
                max-width: 48rem; /* Augmenter la largeur maximale */
                padding: 0.35rem 0.80rem; /* Augmenter le padding pour élargir le bouton */
    
            }
            .st-emotion-cache-1wtrl3u {
                color : rgba(255, 112, 67, 0.9);
                border: 1px solid rgba(255, 112, 67, 0.9);
                height: 2.5rem; /* Augmenter la hauteur du bouton */
                max-width: 48rem; /* Augmenter la largeur maximale */
                padding: 0.35rem 0.80rem; /* Augmenter le padding pour élargir le bouton */
    
            }
    
            .st-emotion-cache-b0y9n5 button {
                width: 200px;  /* Taille fixe du bouton */
                min-width: 200px;
                max-width: 200px;
                height: 40px;  /* Hauteur fixe */
                display: flex;
                align-items: center;
                justify-content: center;
                text-align: center;
                font-size: 16px;  /* Taille de base */
                white-space: nowrap;
                overflow: hidden;
            }  
            
            .st-emotion-cache-b0y9n5 button span {
                display: inline-block;
                max-width: 100%;
                transform-origin: center;
            }
            
            /* Réduction automatique de la taille du texte si nécessaire */
            .st-emotion-cache-b0y9n5 button span {
                font-size: clamp(10px, 2vw, 16px);
            }
        
            .st-emotion-cache-b0y9n5:hover {
                color : rgba(255, 112, 67, 0.9);
                border: 1px solid rgba(255, 112, 67, 0.9);/* Légère augmentation de la taille au survol */
            }
            .st-key-toggle>div>label>div{
                transform: scale(1.5)
                }
            .st-key-toggle p{
                margin-left: 30px;
                }
    
            .st-key-go p {
            font-size: 20px;
            height: 2em;
            width: 5em;
        }
            
          
        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <style>
            @import url('https://fonts.bunny.net/css?family=fredoka:400'); /* Remplace par ta police choisie */
    
            html, body, * {
                font-family: 'Fredoka', sans-serif !important; /* Mets ici le nom de la police */
            }
    
            .stButton > button {
                font-family: 'Fredoka', sans-serif !important;
                font-size: 18px;
            }
        </style>
        """,
        unsafe_allow_html=True
    )







