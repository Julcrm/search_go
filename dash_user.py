import streamlit as st
from func.SQL_user import SQL_user
from streamlit_option_menu import option_menu


def dash_user():
    def set_page(page_name):
        st.session_state.page = page_name

    with st.sidebar:
        val_menu = option_menu(menu_title=None, options=["Robot Bistro", "Tableau de bord", "Déconnexion"],
                               icons=['house', 'graph-up-arrow', "box-arrow-left"])
        if val_menu == "Robot Bistro":
            set_page("chat")
            st.rerun()
        if val_menu == "Tableau de bord":
            set_page("dash_user")
        if val_menu == "Déconnexion":
            for key in st.session_state.keys():
                if key not in ["current_page"]:
                    del st.session_state[key]
            if "current_page" not in st.session_state:
                st.session_state["current_page"] = "Landing"
            st.rerun()


    sql_user = SQL_user()

    user_id = st.session_state["user_id"][1]
    name = st.session_state["user_id"][2]

    df_liste = sql_user.listing_resto(user_id)

    st.markdown("<h1 style='text-align: center;'>Tableau de bord</h1>",unsafe_allow_html=True)
    st.write("")
    st.write("")
    st.write("")
    st.write("")

    st.subheader(name)
    st.write("")
    st.divider()

    fav_resto = sql_user.favorite_restau(user_id)
    driving = round(sql_user.distance_driving(user_id) / 1000)
    walking = round(sql_user.distance_walking(user_id) / 1000)

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown(f"""
            <div style="background-color: #0D1116; color: white; max-width: 18rem; border-radius: 5px; padding: 10px; text-align: center;">
                <div style="font-size: 1.25rem; font-weight: bold;">Restaurant favori <img src="https://i.ibb.co/rXr68HK/icons8-coeurs-48.png" width="24"> :</div>
                <div style="padding-top: 10px; text-align: center;">
                    <h5 style="font-size: 1.25rem; color: white;">{fav_resto}</h5>
                </div>
            </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
            <div style="background-color: #0D1116; color: white; max-width: 18rem; border-radius: 5px; padding: 10px; text-align: center;">
                <div style="font-size: 1.25rem; font-weight: bold;">Km parcourus en voiture <img src="https://i.ibb.co/qFFFybvZ/car-1.png" width="24"> :
                </div><div style="padding-top: 10px; text-align: center;">
                    <h5 style="font-size: 1.25rem; color: white;">{str(f"{driving:,}").replace(",", " ")}</h5>
                </div>
            </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
            <div style="background-color: #0D1116; color: white; max-width: 18rem; border-radius: 5px; padding: 10px; text-align: center;">
                <div style="font-size: 1.25rem; font-weight: bold;">Km parcourus à pieds <img src="https://i.ibb.co/LhJVnC1m/walking.png" width="24"> :</div>
                <div style="padding-top: 10px; text-align: center;">
                    <h5 style="font-size: 1.25rem; color: white;">{str(f"{walking:,}").replace(",", " ")}</h5>
                </div>
            </div>
        """, unsafe_allow_html=True)

    st.divider()


    l1, l2, l3 = st.columns([2,1,2])

    # Ajouter des éléments dans la première colonne
    with l1:
        st.plotly_chart(sql_user.bar_budget(user_id))
        st.write("")
        st.write("")
    # Ajouter des éléments dans la deuxième colonne
    with l3:
        st.plotly_chart(sql_user.pie_chart_resto(user_id))
        st.write("")
        st.write("")


    l3, l4, l5 = st.columns([2,0.5,2])
    with l3:
        st.markdown("""<h5 style="text-align: center; font-size: 17px; font-weight: bold; color: white;">Tableau des visites</h5>""", unsafe_allow_html=True)
        liste_ville = df_liste['ville'].sort_values(ascending=True).unique().tolist()
        liste_ville.insert(0,'(toutes)')
        option = st.selectbox("Ville", liste_ville)

        if "data" not in st.session_state:
            st.session_state["data"] = df_liste

        if option != '(toutes)' :
            df_user = df_liste[df_liste['ville']==option]
            st.data_editor(
                df_user[['Lieu', 'Catégorie', 'Visite', 'Note']],
                column_config={
                    "command": "Streamlit Command",
                    "Note": st.column_config.NumberColumn(
                        "Ta note",
                        help="How much do you like this command (1-5)?",
                        min_value=1,
                        max_value=5,

                        step=1,
                        format="%d ⭐",
                    ),
                    "is_widget": "Widget ?",
                },
                disabled=["command", "is_widget"],
                hide_index=True,
            )


        else :
            df_user = df_liste
            st.data_editor(
                df_user[['Lieu', 'Catégorie', 'Visite', 'Note']],
                column_config={
                    "command": "Streamlit Command",
                    "Note": st.column_config.NumberColumn(
                        "Ta note",
                        help="How much do you like this command (1-5)?",
                        min_value=1,
                        max_value=5,
                        step=1,
                        format="%d ⭐",
                    ),
                    "is_widget": "Widget ?",
                },
                disabled=["command", "is_widget"],
                hide_index=True,
            )


        #st.dataframe(df_user[['Lieu','Catégorie','Visite']], hide_index=True)






    # Ajouter des éléments dans la deuxième colonne
    with l5:
        mean_lat = df_user['lat'].mean()
        mean_lng = df_user['lng'].mean()
        st.markdown("""<h5 style="text-align: center; font-size: 17px; font-weight: bold; color: white;">Carte des restaurants visités</h5>""", unsafe_allow_html=True)

        m = sql_user.carte_resto_user(mean_lat, mean_lng, df_user)
        # Afficher la carte dans Streamlit avec un affichage plus large
        st.components.v1.html(m._repr_html_(), height=580, width=550)



