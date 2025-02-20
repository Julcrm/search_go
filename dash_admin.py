from func.SQL_user import SQL_user
import pandas as pd
import plotly.express as px
import folium
from folium.plugins import MarkerCluster
import streamlit as st





def dash_admin():

    sql_user = SQL_user()


    df_user = sql_user.dash_admin_user().drop(columns="password")
    df_query = sql_user.dash_admin_query()
    df_restaurants = sql_user.dash_admin_restaurants()
    df_total_restaurants = sql_user.dash_admin_total_restaurants()
    df_categories = sql_user.dash_admin_cat()
    df_best_users = sql_user.dash_admin_best_users()
    df_map = sql_user.dash_admin_map()

    st.markdown("<h1 style='text-align: center;'>Tableau de bord</h1>",unsafe_allow_html=True)
    st.write("")
    st.write("")
    st.write("")
    st.write("")



    if st.button("Déconnexion"):
        st.session_state["authenticated"] = False
        st.session_state["current_user"] = None
        st.session_state["current_page"] = "Landing"
        st.rerun()


    st.markdown("<h5 style='text-align: center;'>Bonjour patron , voici un petit tour d'horizon de l'utilisation de Search & GO</h5>",unsafe_allow_html=True)
    st.write("")
    st.divider()

    st.markdown("<h4 style='text-align: center;'> 📊 Évolution hebdomadaire</h4>",unsafe_allow_html=True)

    st.write("")
    st.write("")
    st.write("")

    # Nombre total d'utilisateurs uniques
    total_users = df_user["user_id"].nunique()

    # Définir la semaine actuelle et la semaine précédente
    current_week = df_user["create_date"].max().isocalendar()[1]  # Semaine actuelle

    previous_week = current_week - 1  # Semaine précédente

    # Filtrer les utilisateurs uniques de la semaine dernière
    previous_week_users = df_user[df_user["create_date"].dt.isocalendar().week == previous_week]["user_id"].nunique()

    # Calcul du delta
    delta_users = total_users - previous_week_users

    #--------------------------------------------------------------------------------------------------------#

    # Nombre total query
    total_query = round(df_query["query_id"].nunique() / 4)

    # Définir la semaine actuelle et la semaine précédente
    current_week_query = df_query["date"].max().isocalendar()[1]  # Semaine actuelle

    previous_week_query = current_week_query - 1  # Semaine précédente

    # Filtrer les utilisateurs uniques de la semaine dernière
    previous_week_query_f = round(df_query[df_query["date"].dt.isocalendar().week == previous_week_query]["query_id"].nunique() / 4)

    # Calcul du delta
    delta_query = total_query - previous_week_query_f

    #--------------------------------------------------------------------------------------------------------#

    # Nombre total de restau
    total_restaurants = df_total_restaurants["restaurant_id"].count()

    # Définir la semaine actuelle et la semaine précédente
    current_week_restaurants = df_total_restaurants["date"].max().isocalendar()[1]  # Semaine actuelle

    previous_week_restaurants = current_week_restaurants - 1  # Semaine précédente

    # Filtrer les utilisateurs uniques de la semaine dernière
    previous_week_restaurants_f = df_total_restaurants[df_total_restaurants["date"].dt.isocalendar().week == previous_week_restaurants]["restaurant_id"].nunique()

    # Calcul du delta
    delta_restaurants = total_restaurants - previous_week_restaurants_f

    #______________________________________________________________________________________________________________#

    col1, col2, col3, col4, col5 = st.columns([2,2,2,2,1])
    col2.metric("Nombre d'utilisateurs", f"{total_users}", f"{delta_users}")
    col3.metric("Nombre de recherches", f"{total_query}", f"{delta_query}")
    col4.metric("Nombre de restaurants dans la base", f"{total_restaurants}", f"{delta_restaurants}")

    st.divider()


    l1, l2, l3 = st.columns([2,0.5,2])

    with l1:
        peach_colors = ['#FFB79E', '#F28C52', '#E57A3F']

        fig = px.pie(df_categories, names='types', values='nb_restaurants', color_discrete_sequence=peach_colors)

        # Mise à jour du layout pour ne pas afficher la légende
        fig.update_layout(
                    title_text='Catégories de restaurants les plus appréciées des utilisateurs',
                    title_x=0,  # Centrer le titre
                    width=425,  # Largeur du graphique
                    height=425
                )
        st.plotly_chart(fig)

        st.markdown("""<h5 style="text-align: center; font-size: 17px; font-weight: bold; color: white;">Affichage des tables de la base de données</h5>""",unsafe_allow_html=True)
        option = st.selectbox("Choisir une table",("User", "Query", "Restaurants"))
        if option == "User":
            st.dataframe(df_user)
        if option == "Query":
            st.dataframe(df_query)
        if option == "Restaurants":
            st.dataframe(df_restaurants)


    with l3:
        st.write("")
        st.markdown("""<h5 style="text-align: center; font-size: 17px; font-weight: bold; color: white;">Podium des meilleurs clients</h5>""", unsafe_allow_html=True)
        # CSS pour styliser le podium
        st.markdown(
            """
            <style>
            .podium {
                display: flex;
                justify-content: center;
                align-items: flex-end;
                height: 300px;
                margin-top: 20px;
            }
            .podium .place {
                width: 100px;
                margin: 0 10px;
                text-align: center;
                position: relative;
            }
            .podium .place .medal {
                position: absolute;
                top: -130px;
                left: 50%;
                transform: translateX(-50%);
                font-size: 50px;
            }
            .podium .place.gold {
                background-color: gold;
                height: 200px;
            }
            .podium .place.silver {
                background-color: silver;
                height: 150px;
            }
            .podium .place.bronze {
                background-color: #cd7f32;
                height: 100px;
            }
            .podium .place .label {
                position: absolute;
                top: -65px;
                left: 50%;
                transform: translateX(-50%);
                font-size: 20px;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

        # Données des clients (exemple)
        clients = {
            "Or": f"{df_best_users['last_name'].iloc[0]} {df_best_users['first_name'].iloc[0]}",
            "Argent": f"{df_best_users['last_name'].iloc[1]} {df_best_users['first_name'].iloc[1]}",
            "Bronze": f"{df_best_users['last_name'].iloc[2]} {df_best_users['first_name'].iloc[2]}"
        }

        # Affichage du podium
        st.markdown(
            f"""
            <div class="podium">
                <div class="place silver">
                    <div class="medal">🥈</div>
                    <div class="label">{clients["Argent"]}</div>
                </div>
                <div class="place gold">
                    <div class="medal">🥇</div>
                    <div class="label">{clients["Or"]}</div>
                </div>
                <div class="place bronze">
                    <div class="medal">🥉</div>
                    <div class="label">{clients["Bronze"]}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.write("")
        st.write("")
        st.write("")


        st.markdown("""<h5 style="text-align: center; font-size: 17px; font-weight: bold; color: white;">Carte des restaurants</h5>""",unsafe_allow_html=True)
        # Remplir les valeurs manquantes et convertir en entier

        # Centrer la carte
        center_map = [46.233870597212665, 2.221999414881632]
        # Créer la carte Folium
        map_folium = folium.Map(
            location=center_map,
            zoom_start=5,
            tiles="https://tiles.stadiamaps.com/tiles/alidade_smooth/{z}/{x}/{y}{r}.png",
             attr='&copy; <a ></a> ',)

        # Ajouter un cluster de marqueurs
        marker_cluster = MarkerCluster().add_to(map_folium)

        # Boucle pour ajouter les marqueurs
        for i, (lat, lng) in enumerate(df_map[['lat', 'lng']].values.tolist()):
            popup_html = f"""
                <div style='width:300px'>
                <b>Nom :</b> {df_map.iloc[i]["name"]} 🏙️<br>
                <b>Nombre de visites :</b> {df_map.iloc[i]["selected_count"]} 🏆<br>
                </div>
            """
            marker = folium.Marker(
                location=[lat, lng],
                tooltip="Plus d'informations !",
                popup=popup_html,
                icon=folium.DivIcon(html="""
                    <div style="text-align: center;">
                        <img src="https://i.postimg.cc/jSQwjLmS/hat.png"
                        style="width: 30px; height: 30px;"><br>
                    </div>
                """)
            )

            # Ajouter le marqueur au cluster
            marker.add_to(marker_cluster)

        fig = folium.Figure(height=500, width=550)  # Définit la taille de la carte
        map_folium.add_to(fig)
        # Afficher la carte dans Streamlit
        st.components.v1.html(map_folium._repr_html_(), height=580, width=550)


