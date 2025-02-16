import google.generativeai as genai
import json

import streamlit


class Robot_bistro:
    def __init__(self, name_model="gemini-1.5-flash", temperature=1):
        with open('apikeybot.txt', 'r') as file:  # mettre clé api
            API_KEY = file.read().strip()
        self.api_key = API_KEY
        self.model = None
        self.name_model = name_model
        self.temperature = temperature
        self._configure()

    def _configure(self):
        genai.configure(api_key = self.api_key)
        model = genai.GenerativeModel(self.name_model)
        self.model = model.start_chat()

    def talk(self, message):
        return self.model.send_message(message).text

    def gethistory(self):
        return self.model.history

    def preprompt(self, filename):
        with open(filename, 'r') as file:
            prompt = file.read()
        system_instruction = prompt
        self._configure()
        self.talk(system_instruction)

    def get_welcome(self):
        return f"Bonjour {streamlit.session_state['user_id'][2].split()[1]} ! Je suis Robot Bistro, votre assistant pour trouver des restaurants 🍽️. Quel type de restaurant cherchez-vous ?"




    
