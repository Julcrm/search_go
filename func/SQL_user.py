from sqlalchemy import create_engine, text
import pandas as pd
import json
import plotly.express as px
import folium
import re
import os
from dotenv import load_dotenv

load_dotenv()


class SQL_user:
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    password_regex = r'^(?=.*[a-zàâäéèêëîïôöùûüÿçáéíñóúü])(?=.*[A-ZÀÂÄÉÈÊËÎÏÔÖÙÛÜŸÇÁÉÍÑÓÚÜ])(?=.*\d)(?=.*[@$!%*?&_\"\'\'])[A-Za-zàâäéèêëîïôöùûüÿçáéíñóúüÀÂÄÉÈÊËÎÏÔÖÙÛÜŸÇÁÉÍÑÓÚÜ\d@$!%*?&_\"\'\']{8,}$'

    # Informations de connexion
    DATABASE_TYPE = os.getenv('DATABASE_TYPE')
    DBAPI = os.getenv('DBAPI')
    HOST = os.getenv('PGHOST')
    PORT = os.getenv('PGPORT')
    USER = os.getenv('PGUSER')
    PASSWORD = os.getenv('PGPASSWORD')
    DATABASE = os.getenv('PGDATABASE')
    print(DATABASE)


    def __init__(self):
        self.engine = create_engine(f"{SQL_user.DATABASE_TYPE}+{SQL_user.DBAPI}://{SQL_user.USER}:{SQL_user.PASSWORD}@{SQL_user.HOST}:{SQL_user.PORT}/{SQL_user.DATABASE}")

    def is_email_known(self, email):
        query = text('SELECT COUNT(*) FROM "user" WHERE email = :email')
        with self.engine.connect() as connection:
            result = connection.execute(query, {'email': email})
            count = result.scalar()
        return count > 0
    
    def is_authentificate(self, email, password):
        query = text("""SELECT user_id, first_name, last_name, email, COUNT(*) 
                     FROM "user" WHERE email = :email AND password = :password 
                     GROUP BY user_id, first_name, last_name, email""")
        with self.engine.connect() as connection:
            result = connection.execute(query, {'email': email, 'password': password})
            data = result.fetchall()
        
        if data:
            identification = pd.DataFrame(data, columns=['user_id', 'first_name','last_name','email','count'])
            user_id = int(identification['user_id'].iloc[0])
            name = identification['first_name'].iloc[0]+" "+identification['last_name'].iloc[0]
            email_user = identification['email'].iloc[0]
            count = identification['count'].iloc[0]
            return count > 0, user_id, name, email_user
        else:
            return False, None, None, None

    @staticmethod
    def is_valid_email(email):
        return re.match(SQL_user.email_regex, email) is not None

    @staticmethod
    def is_valid_password(password):
        return re.match(SQL_user.password_regex, password) is not None

    @staticmethod
    def is_valid_name(name):
        return bool(name) and all(char.isalpha() or char.isspace() for char in name)

    @staticmethod
    def is_valid_lastname(lastname):
        return bool(lastname) and all(char.isalpha() or char.isspace() for char in lastname)

    def validate_user(self, email, password, name, lastname):
        if not self.is_valid_email(email):
            print("Mail invalide")
            return False
        if not self.is_valid_password(password):
            print("Mot de passe invalide merci de renseigner minimum 8 caractères dont un chiffre, majuscule et symbole")
            return False
        if not self.is_valid_name(name):
            print("Name invalid")
            return False
        if not self.is_valid_lastname(lastname):
            print("Lastname invalid")
            return False
        return True

    def add_user(self,email, password, name, lastname):
        dict_user = {'first_name': [name], 'last_name': [lastname], 'email': [email], 'password': [password]}
        df_user = pd.DataFrame(dict_user)
        df_user['create_date'] = pd.to_datetime('now')
        df_user.to_sql(name='user', con=self.engine, if_exists = 'append', index=False)

    def favorite_restau(self, user_id):
        query = text("""
                        SELECT r.name as Restaurant, s.nb_visite as max_visite
                        FROM (
                            SELECT restaurant_id, COUNT(restaurant_id) as nb_visite 
                            FROM query 
                            WHERE selected = True AND user_id = :user_id 
                            GROUP BY restaurant_id) as s
                        JOIN restaurants as r ON r.restaurant_id = s.restaurant_id
                        WHERE s.nb_visite = (
                            SELECT MAX(nb_visite)
                            FROM (
                                SELECT COUNT(restaurant_id) as nb_visite
                                FROM query
                                WHERE selected = True AND user_id = :user_id
                                GROUP BY restaurant_id) as subquery
                            )
                        """)
        with self.engine.connect() as connection:
                    result = connection.execute(query, {'user_id': user_id})
                    favorite = result.fetchall()
        return favorite[0][0]
    
    def listing_resto(self, user_id):
        query = text("""                            
                        SELECT r.name as Nom, r.types as Catégorie, r.formatted_address, r.lat, r.lng, COUNT(q.restaurant_id) as Visite, q.note
                        FROM query as q
                        JOIN restaurants as r ON r.restaurant_id = q.restaurant_id
                        WHERE selected = True AND user_id = :user_id
                        GROUP BY r.name, r.types, r.formatted_address, r.lat, r.lng, q.note
                        ORDER BY COUNT(q.restaurant_id) DESC
                        """)
        with self.engine.connect() as connection:
                    result = connection.execute(query, {'user_id': user_id})
                    data = result.fetchall()
        df_resto = pd.DataFrame(data, columns= ['Lieu', 'Catégorie','formatted_address','lat','lng', 'Visite', 'Note'])
        df_resto['ville'] = [re.search(r', (\d{5}) ([\S\s]*),', address).group(2) for address in df_resto['formatted_address']]
        return df_resto        
         
    
    def bar_budget(self, user_id):
        query = text("""
                        SELECT r.price_level as budget, COUNT(q.restaurant_id) as nb_restau
                        FROM query as q
                        JOIN restaurants as r ON r.restaurant_id = q.restaurant_id
                        WHERE selected = True AND user_id = :user_id
                        GROUP BY r.price_level
                        """)
        with self.engine.connect() as connection:
                    result = connection.execute(query, {'user_id': user_id})
                    data = result.fetchall()
        df_histo = pd.DataFrame(data, columns= ['Budget', 'Total_Resto'])
        # Remplir les valeurs manquantes avec 'Inconnu'
        df_histo['Budget'] = df_histo['Budget'].fillna('Inconnu')
        # Créer une fonction pour mapper les valeurs de Budget
        def cat_budget(row):
            if row == 0:
                return '0€-10€'
            elif row == 1:
                return '11€-20€'
            elif row == 2:
                return '21€-30€'
            elif row == 3:
                return '31€-40€'
            elif row == 4:
                return '+41€'
            else:
                return 'Inconnu'
            

        # Appliquer la fonction à la colonne Budget
        df_histo['Budget'] = df_histo['Budget'].apply(cat_budget)

        # Définir l'ordre des catégories pour la colonne Budget
        categories = ['0€-10€', '11€-20€', '21€-30€', '31€-40€', '+41€', 'Inconnu']
        df_histo['Budget'] = pd.Categorical(df_histo['Budget'], categories=categories, ordered=True)

        # Trier le DataFrame par les catégories de Budget
        df_histo = df_histo.sort_values('Budget')

        fig = px.bar(df_histo, x='Budget', y='Total_Resto', labels={'Budget':'Fourchettes de prix', 'Total_Resto':'Nombre de visites'})
        fig.update_layout(title_text='Nombre de visites par fourchette de prix', title_x=0.3)
        fig.update_traces(marker_color="#E7673F")
        # Afficher les valeurs au-dessus de chaque barre
        fig.update_traces(textposition='outside')
        return fig
    
    def pie_chart_resto(self, user_id):
        query = text("""
            SELECT r.types, COUNT(r.types) as category
            FROM query as q
            JOIN restaurants as r ON r.restaurant_id = q.restaurant_id
            WHERE selected = True AND user_id = :user_id
            GROUP BY r.types
            ORDER BY COUNT(r.types) DESC
            """)


        with self.engine.connect() as connection:
                    result = connection.execute(query, {'user_id': user_id})
                    data = result.fetchall()

        df_cat_resto = pd.DataFrame(data, columns=['Catégories','Nb restau'])
        peach_colors = ['#FFB79E', '#F28C52', '#E57A3F']



        fig = px.pie(df_cat_resto, names='Catégories', values='Nb restau', color_discrete_sequence=peach_colors)

        # Mise à jour du layout pour ne pas afficher la légende
        fig.update_layout(
            title_text='Proportions des visites en fonction des catégories',
            title_x=0,  # Centrer le titre
            width=425,  # Largeur du graphique
            height=425
        )


        return fig
    
    def carte_resto_user(self, lat, lng, df_user):
        df_loc_freq = df_user

        # Initialiser la carte sans position initiale spécifique
        m = folium.Map(location= [lat,lng], zoom_start=15,tiles="https://tiles.stadiamaps.com/tiles/alidade_smooth/{z}/{x}/{y}{r}.png",
                    attr='&copy; <a ></a> ',)
        fig = folium.Figure(height=580, width=550)
        m.add_to(fig)
        # Ajouter des cercles pour chaque restaurant visité
        for _, row in df_loc_freq.iterrows():
            popup_html = f"""
                    <div style='width:300px'>
                    <b>Restaurant :</b> {row['Lieu']} <br>
                    <b>Nombre de visites :</b> {row['Visite']}<br>
                    </div>
                    """
            folium.Circle(
                location=[row['lat'], row['lng']],
                radius=row['Visite'] * 30,  # Ajustez le facteur de multiplication selon vos besoins
                color='orange',
                fill=True,
                fill_color= 'orange',
                fill_opacity=0.6,  # Augmenter l'opacité du remplissage (valeur entre 0 et 1)
                opacity=0.8,  # Augmenter l'opacité de la bordure (valeur entre 0 et 1)
                popup=popup_html
            ).add_to(m)

        # Centrer la carte automatiquement en fonction des marqueurs
        m.fit_bounds(m.get_bounds())

        return m

    def distance_driving(self, user_id):
        query = text("""
                        SELECT SUM(q.distance) AS distance_parcouru
                        FROM query as q
                        WHERE user_id = :user_id AND mode = 'driving'                    
                        """)
        with self.engine.connect() as connection:
            result = connection.execute(query, {'user_id': user_id})
            data = result.fetchall()
            distance = data[0][0] if data and data[0][0] is not None else 0
            return distance


    def distance_walking(self, user_id):
        query = text("""
                        SELECT SUM(q.distance) AS distance_parcouru
                        FROM query as q
                        WHERE user_id = :user_id AND mode = 'walking'                    
                        """)
        with self.engine.connect() as connection:
            result = connection.execute(query, {'user_id': user_id})
            data = result.fetchall()
            distance = data[0][0] if data and data[0][0] is not None else 0
            return distance



    def dash_admin_user(self):
        query = text("""
                    SELECT *
                    FROM "user"
                    """)

        with self.engine.connect() as connection:
            result = connection.execute(query)
            data = result.fetchall()
            df = pd.DataFrame(data)

            return df

    def dash_admin_query(self):
        query = text("""
                    SELECT *
                    FROM query
                    """)

        with self.engine.connect() as connection:
            result = connection.execute(query)
            data = result.fetchall()
            df = pd.DataFrame(data)

            return df

    def dash_admin_restaurants(self):
        query = text("""
                    SELECT *
                    FROM restaurants
                    """)

        with self.engine.connect() as connection:
            result = connection.execute(query)
            data = result.fetchall()
            df = pd.DataFrame(data)

        return df

    def dash_admin_total_restaurants(self):
        query = text("""
                    SELECT r.restaurant_id, q.date
                    FROM restaurants as r
                    JOIN query as q ON r.restaurant_id = q.restaurant_id
                    GROUP BY r.restaurant_id, q.date
                    """)
        with self.engine.connect() as connection:
            result = connection.execute(query)
            data = result.fetchall()
            df = pd.DataFrame(data)
        return df

    def dash_admin_cat(self):
        query = text("""
                            SELECT r.types, COUNT(r.types) as nb_restaurants
                            FROM query as q
                            JOIN restaurants as r ON q.restaurant_id = r.restaurant_id
                            WHERE selected = True
                            GROUP BY r.types
                            """)

        with self.engine.connect() as connection:
            result = connection.execute(query)
            restaurants = result.fetchall()
            df = pd.DataFrame(restaurants)
            return df
    def dash_admin_best_users(self):
        query = text("""
                            SELECT u.first_name, u.last_name,  COUNT(q.query_id) as nb_query
                            FROM query as q
                            JOIN restaurants as r ON q.restaurant_id = r.restaurant_id
                            JOIN "user" as u ON q.user_id = u.user_id
                            GROUP BY u.first_name, u.last_name
                            ORDER BY nb_query DESC
                            """)

        with self.engine.connect() as connection:
            result = connection.execute(query)
            restaurants = result.fetchall()
            df = pd.DataFrame(restaurants)
            return df

    def dash_admin_map(self):
        # %%
        query = text("""WITH restaurant_counts AS (
            SELECT r.restaurant_id, r.name, COUNT(q.selected) AS selected_count
            FROM query AS q
            JOIN restaurants AS r ON q.restaurant_id = r.restaurant_id
            WHERE q.selected = TRUE
            GROUP BY r.restaurant_id, r.name
        )
        SELECT r.name, r.lat, r.lng, rc.selected_count
        FROM restaurant_counts AS rc
        RIGHT JOIN restaurants AS r ON r.restaurant_id = rc.restaurant_id;
                            """)

        with self.engine.connect() as connection:
            result = connection.execute(query)
            restaurants = result.fetchall()
            df = pd.DataFrame(restaurants)
            return df