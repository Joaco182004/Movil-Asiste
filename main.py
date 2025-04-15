from kivy.app import App
from kivy.lang import Builder
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle

# Paquetes

import requests
from bs4 import BeautifulSoup

# Crear una sesión para mantener cookies
session = requests.Session()
global flag_login
flag_login = False

# Paso 1: Obtener el token CSRF
def obtener_csrf_token(session, login_url):
    resp = session.get(login_url)
    soup = BeautifulSoup(resp.text, "html.parser")
    return soup.find("input", {"name": "_token"})["value"]

# Paso 2: Realizar login
def realizar_login(session, login_url, email, password):
    csrf_token = obtener_csrf_token(session, login_url)
    payload = {
        "_token": csrf_token,
        "email": email,
        "password": password
    }
    response = session.post(login_url, data=payload)
    if "Iniciar sesión" not in response.text and response.ok:
        print("✅ Login exitoso!")
        return True
    else:
        print("❌ Login fallido o datos incorrectos.")
        return False

# Establecer tamaño de ventana
Window.size = (380, 350)

KV = """
AnchorLayout:
    anchor_y: 'top'
    padding: 20

    BoxLayout:
        orientation: 'vertical'
        size_hint: None, None
        width: 370
        height: self.minimum_height
        spacing: 20

        Label:
            text: "Generación de Casos"
            font_size: '24sp'
            size_hint_y: None
            height: self.texture_size[1]
            halign: 'center'
            valign: 'middle'
            text_size: self.size

        BoxLayout:
            orientation: 'horizontal'
            size_hint_y: None
            height: '40dp'
            spacing: 10

            Label:
                text: "Número de Casos"
                size_hint_x: 0.5
                halign: 'center'
                valign: 'middle'
                text_size: self.size

            TextInput:
                id: input_casos
                multiline: False
                size_hint_x: 0.5
                size_hint_y: None
                height: '35dp'
                halign: 'left'

        Button:
            text: "Enviar Caso"
            size_hint_y: None
            height: '40dp'
            background_color: 0.141, 0.667, 0.882, 1  # Color de fondo #24AAE1
            on_press: app.enviar_caso()
        
        Label:
            id: status_label
            size_hint_y: None
            height: self.texture_size[1]
            halign: 'center'
            valign: 'middle'
            text_size: self.size
"""

class MyApp(App):
    def build(self):
        # Crear fondo de color #242424 (RGB: 0.141, 0.141, 0.141, 1)
        self.root = Builder.load_string(KV)
        with self.root.canvas.before:
            Color(0.141, 0.141, 0.141, 1)  # Color de fondo #242424
            self.rect = Rectangle(size=Window.size, pos=self.root.pos)

        self.root.bind(size=self._update_rect, pos=self._update_rect)
        return self.root

    def _update_rect(self, *args):
        # Actualizar el tamaño y la posición del rectángulo de fondo
        self.rect.pos = self.root.pos
        self.rect.size = self.root.size

    def enviar_caso(self):
        login_url = "https://pacifico.sigsa.app/login"
        email = "arsd64_gmail.com#EXT#@pacificocia.onmicrosoft.com"
        password = "080164"
        # Obtener el label de estado
        status_label = self.root.ids.status_label

        if realizar_login(session, login_url, email, password):
            status_label.color = (0.6, 1, 0.6, 1)  # Verde claro
            status_label.text = "Proceso completado con éxito!"
        else:
            status_label.color = (1, 0.3, 0.3, 1)  # Rojo claro
            status_label.text = "Proceso completado con errores!"

            


if __name__ == "__main__":
    MyApp().run()
