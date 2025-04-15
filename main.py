from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.spinner import Spinner
from kivy.core.window import Window
import requests
from bs4 import BeautifulSoup
import json
import time
import webbrowser

class ConsultaCasosApp(App):
    login_url = "https://pacifico.sigsa.app/login"
    email = "arsd64_gmail.com#EXT#@pacificocia.onmicrosoft.com"
    password = "080164"
    session = requests.Session()
    def build(self):
        # Configuración de la ventana
        Window.size = (380, 590)
        Window.clearcolor = (1, 1, 1, 1)  # Fondo blanco
        self.title = "Consulta de Casos"

        # Layout principal
        main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Sección del logo
        logo_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=70, spacing=5)
        logo = Image(source="util/logo.png", size_hint=(None, None), size=(130, 70))
        logo_label = Label(text="Consulta de Casos", font_size=24, color=(0, 0, 0, 1), bold=True, halign="right", valign="middle", size_hint_x=None, width=250)
        logo_label.bind(size=logo_label.setter('text_size'))
        logo_layout.add_widget(logo)
        logo_layout.add_widget(logo_label)
        logo_layout.spacing = 5  # Reduce el espaciado entre el logo y el texto
        logo_layout.padding = [10, 0, 10, 0]  # Espaciado entre los bordes
        main_layout.add_widget(logo_layout)

        # Sección de entrada
        input_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=10, padding=[10, 0, 10, 0])
        label_entry = Label(text="Detalle del Caso:", font_size=16, bold=True, color=(0, 0, 0, 1), size_hint_x=None, width=170, halign="left", valign="middle")
        label_entry.bind(size=label_entry.setter('text_size'))
        self.case_number_entry = TextInput(hint_text="Ingrese el número de caso", multiline=False, font_size=16, size_hint_x=None, width=270, halign="left")
        input_layout.add_widget(label_entry)
        input_layout.add_widget(self.case_number_entry)
        main_layout.add_widget(input_layout)

        # Botón para buscar el caso
        search_button = Button(text="Buscar Caso", size_hint_y=None, height=50, bold=True, background_color=(0.0, 0.396, 0.851, 1))  # Fondo color #0065D9
        search_button.bind(on_press=lambda instance: self.inicio())
        main_layout.add_widget(search_button)

        # Scrollable frame para mostrar resultados
        self.scrollable_frame = ScrollView(size_hint=(1, 1))
        self.results_layout = BoxLayout(orientation='vertical', size_hint_y=None)
        self.results_layout.bind(minimum_height=self.results_layout.setter('height'))
        self.scrollable_frame.add_widget(self.results_layout)
        main_layout.add_widget(self.scrollable_frame)

        return main_layout

    def buscar_caso(self, instance):
        # Aquí puedes implementar la lógica para buscar el caso
        # Por ahora, solo muestra un ejemplo de resultado
        self.results_layout.clear_widgets()
        example_result = Label(text="Resultados del caso aparecerán aquí.", font_size=14, size_hint_y=None, height=30)
        self.results_layout.add_widget(example_result)

    # Paso 1: Obtener el token CSRF
    def obtener_csrf_token(self, session, login_url):
        resp = session.get(login_url)
        soup = BeautifulSoup(resp.text, "html.parser")
        return soup.find("input", {"name": "_token"})["value"]

    # Paso 2: Realizar login
    def realizar_login(self,session, login_url, email, password):
        csrf_token = self.obtener_csrf_token(session, login_url)
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

    # Paso 3: Obtener datos del caso
    def inicio(self):
        if(self.case_number_entry.text.strip() != ""):
            caso_id = int(self.case_number_entry.text.strip())
            if self.realizar_login(self.session, self.login_url, self.email, self.password):
                body_content = self.obtener_datos_caso(self.session, caso_id)
                dict_options = self.procesar_opciones(body_content[1])
                scripts = body_content[0].find_all("script")
                caso_parsed_json = self.extraer_datos_json(scripts)
                poliza_info = self.obtener_poliza(caso_parsed_json)
                siniestro_info = self.estructurar_info(caso_parsed_json, dict_options)
                self.mostrar_datos(siniestro_info,poliza_info)

    def obtener_datos_caso(self,session, caso_id):
        caso_url = f"https://pacifico.sigsa.app/casos/{caso_id}/edit"
        locacion_url = f"https://pacifico.sigsa.app/casos/{caso_id}"
        caso_resp = session.get(caso_url)
        locacion_resp = session.get(locacion_url)
        soup = BeautifulSoup(caso_resp.text, "html.parser")
        soup_locacion = BeautifulSoup(locacion_resp.text, "html.parser")

        return [soup.body,soup_locacion.body]

    # Extraer opciones de etiquetas <label> y <option>
    def procesar_opciones(self,body_content):
        elements_options = body_content.find_all(["td", "th"])
        dict_options = {}
        flag = False
        label = ""
        for element in elements_options:
            if(element.name == "td"):
                if("Causa del siniestro" in element.text or "Departamento" in element.text or "Provincia" in element.text or "Distrito" in element.text):
                    label = element.text.strip()
                    flag = True
                    continue
                if(flag):
                    if label in dict_options:
                        dict_options[label+"1"] = element.text.strip()
                    else:
                        dict_options[label] = element.text.strip()
                    flag = False

        return dict_options

    # Extraer datos del script JSON
    def extraer_datos_json(self,scripts):
        for script in scripts:
            script_content = script.string
            if script_content and "datavue" in script_content:
                try:
                    json_start = script_content.find("{")
                    json_end = script_content.rfind("}") + 1
                    json_data = script_content[json_start:json_end]
                    return json.loads(json_data)
                except json.JSONDecodeError:
                    print("Error al decodificar el JSON.")
        return {}

    # Limpiar texto del solicitante
    def limpiar_solicitante(self,solicitante):
        solicitante_final = ''.join([i for i in solicitante if not i.isdigit() and i not in ":;/"]).replace("am ", "").replace("pm ", "")
        months = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Set", "Oct", "Nov", "Dic"]
        full_months = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Setiembre", "Octubre", "Noviembre", "Diciembre"]

        for month in months + full_months:
            solicitante_final = solicitante_final.replace(month + " ", "").replace(month.lower() + " ", "")
        if solicitante_final[:5].lower() in ["eneam", "febam", "maram", "abram", "mayam", "junam", "julam", "agoam", "setam", "octam", "novam", "dicam", "enepm", "febpm", "marpm", "abrpm", "maypm", "junpm", "julpm", "agopm", "setpm", "octpm", "novpm", "dicpm"]:
            solicitante_final = solicitante_final[5:]
        if solicitante_final[:2].lower() in ["am", "pm"]:
            solicitante_final = solicitante_final[2:]
        return solicitante_final

    def obtener_poliza(self,caso_parsed_json):
        poliza = caso_parsed_json["caso"]["polizaid"]
        url_poliza = f"https://pacifico.sigsa.app/poliza/datosAdicionales/{poliza}"
        poliza_res = self.session.get(url_poliza)
        soup_poliza = BeautifulSoup(poliza_res.text, "html.parser")
        elements_poliza = soup_poliza.find_all(["td", "th"])
        dict_poliza = {}
        for element in elements_poliza:
            if element.text.lower().strip() in ["estado", "póliza cobertura prima", "poliza cobertura prima", "fecha inicio póliza", "fecha inicio poliza", "fecha fin póliza", "fecha fin poliza"]:
                label = element.text.strip()
                flag = True
                continue
            if(flag):
                if label in dict_poliza:
                    dict_poliza[label+"1"] = element.text.strip()
                else:
                    dict_poliza[label] = element.text.strip()
                flag = False
        dict_poliza["id_poliza"] = poliza
        return dict_poliza
    # Mostrar resultados
    def estructurar_info(self,caso_parsed_json, dict_options):
        num_caso = caso_parsed_json["caso"]["casoid"]
        num_siniestro = caso_parsed_json["caso"]["numSin"]
        asegurado = caso_parsed_json["poliza"]["asegurado"]
        solicitante = self.limpiar_solicitante(caso_parsed_json["caso"]["solicitante"])
        celular_contacto = caso_parsed_json["datosGenerales"]["celular_solicitante"]

        tipo_siniestro = dict_options.get("Causa del siniestro", "N/A")
        
        departamento_ubicacion = dict_options.get("Departamento1", "N/A")
        provincia_ubicacion = dict_options.get("Provincia1", "N/A")
        distrito_ubicacion = dict_options.get("Distrito1", "N/A")

        referencia_ubicacion = caso_parsed_json["caso"]["direccionevento"]
        ubicacion_final = f"Perú - {departamento_ubicacion} - {provincia_ubicacion} - {distrito_ubicacion} - {referencia_ubicacion}"

        auto = str(caso_parsed_json["caso"]["poliza"]["marca"]) + " - " + str(caso_parsed_json["caso"]["poliza"]["linea"]) + " - " +str(caso_parsed_json["caso"]["poliza"]["modelo"]) + " - " + str(caso_parsed_json["caso"]["poliza"]["color"])
        if (caso_parsed_json["detalleIncidenteVehicular"]["placa"] == None):
            placa = caso_parsed_json["detalleIncidenteVehicular"]["placa_temporal"] 
        else:
            placa = caso_parsed_json["detalleIncidenteVehicular"]["placa"]

        deducibles_array = []
        datos_adicionales = json.loads(caso_parsed_json["poliza"]["datos_adicionales"]) if isinstance(caso_parsed_json["poliza"]["datos_adicionales"], str) else caso_parsed_json["poliza"]["datos_adicionales"]
        infoVeh = json.loads(datos_adicionales["infoVeh"]) if isinstance(datos_adicionales["infoVeh"], str) else datos_adicionales["infoVeh"]
        for ele in infoVeh[0].get("infoVeh")[0]["coberturas"]:
            for ele in ele.get("cobertura"):
                if "DanoPropio" in ele.get("svcio"):
                    for item in ele.get("deducible"):
                        deducibles_array.append(item.get("patron"))
        deducibles_set = set(deducibles_array)

        deducibles_text = ""
        for ele in deducibles_set:
            deducibles_text += "- " + str(ele) + "\n"
        if(deducibles_text == ""):
            deducibles_text = "Por confirmar"
        labels=["Tipo Siniestro", "Num. Caso","Num. Siniestro","Asegurado","Solicitante", "Celular Contacto","Ubicación","Auto","Placa","Deducibles"]
        inputs = [tipo_siniestro,num_caso, num_siniestro, asegurado, solicitante, celular_contacto, ubicacion_final,auto, placa, deducibles_text]

        dict_siniestro = {}
        for l in labels:
            dict_siniestro[l] = inputs[labels.index(l)]

        return dict_siniestro


    def mostrar_datos(self, siniestro_info, poliza_info):
        # Limpiar el layout de resultados antes de agregar nuevos datos
        self.results_layout.clear_widgets()
    
        # Mostrar información del siniestro
        for key, value in siniestro_info.items():
            # Etiqueta para la clave
            label = Label(
                text=f"{key}:",
                font_size=16,
                bold=True,
                color=(0, 0, 0, 1),  # Letra color negra
                size_hint_y=None,
                height=30,
                halign="left",
                valign="middle",
            )
            label.bind(size=label.setter('text_size'))
            self.results_layout.add_widget(label)
            if (key == "Ubicación"):
                text_input = TextInput(
                text=str(value).strip(),
                multiline=True,
                font_size=14,
                size_hint_y=None,
                height=70,  # Ajustar altura según el contenido
                )
            elif(key == "Deducibles"):
                text_input = TextInput(
                text=str(value).strip(),
                multiline=True,
                font_size=14,
                size_hint_y=None,
                height=150,  # Ajustar altura según el contenido
                )
            else:
                text_input = TextInput(
                text=str(value).strip(),
                multiline=True,
                font_size=14,
                size_hint_y=None,
                height=40,  # Ajustar altura según el contenido
            )
            self.results_layout.add_widget(text_input)
    
        # Espaciado entre secciones
        self.results_layout.add_widget(Label(size_hint_y=None, height=20))
        label = Label(
            text=f"Descripción de la Póliza {str(poliza_info["id_poliza"])}:",
            font_size=16,
            bold=True,
            color=(0, 0, 0, 1),  # Letra color negra
            size_hint_y=None,
            height=30,
            halign="left",
            valign="middle",
        )
        label.bind(size=label.setter('text_size'))
        self.results_layout.add_widget(label)
        # Eliminar el key y valor de "id_poliza" antes de mostrar la información
        if "id_poliza" in poliza_info:
            del poliza_info["id_poliza"]
        # Mostrar información de la póliza
        for key, value in poliza_info.items():
            # Etiqueta para la clave
            label = Label(
                text=f"{key}:",
                font_size=16,
                bold=True,
                size_hint_y=None,
                color=(0, 0, 0, 1),
                height=30,
                halign="left",
                valign="middle",
            )
            label.bind(size=label.setter('text_size'))
            self.results_layout.add_widget(label)
            if(key  == "Estado" or key == "Póliza cobertura prima"):
                text_input = TextInput(
                text=str(value).strip(),
                multiline=True,
                font_size=14,
                size_hint_y=None,
                height=70,  # Ajustar altura según el contenido
            )
            else:
                text_input = TextInput(
                text=str(value).strip(),
                multiline=True,
                font_size=14,
                size_hint_y=None,
                height=40,  # Ajustar altura según el contenido
            )
            self.results_layout.add_widget(text_input)

        label = Label(
                text="",
                font_size=16,
                bold=True,
                size_hint_y=None,
                color=(0, 0, 0, 1),
                height=16,
                halign="left",
                valign="middle",
            )
        label.bind(size=label.setter('text_size'))

        self.results_layout.add_widget(label)
        search_button = Button(
            text="Enviar Caso",
            size_hint_y=None,
            height=50,
            bold=True,
            background_color=(0.0, 0.396, 0.851, 1),  # Fondo color #0065D9
            padding=(0, 16),
        )
        # Aplicar margen superior de 1 rem (aproximadamente 16 píxeles)
        search_button.margin = [0, 16, 0, 0]
        search_button.bind(on_press=lambda instance: self.enviar_caso(siniestro_info,poliza_info))
        self.results_layout.add_widget(search_button)
    def enviar_caso(self, siniestro_info, poliza_info):
        # Crear el mensaje con la información del caso
        mensaje = "Información del Caso:\n"
        for key, value in siniestro_info.items():
            mensaje += f"{key}: {value}\n"
        mensaje += "\nInformación de la Póliza:\n"
        for key, value in poliza_info.items():
            mensaje += f"{key}: {value}\n"

        # Reemplazar caracteres especiales para codificar la URL
        mensaje_codificado = requests.utils.quote(mensaje)

        # Números de teléfono al que se enviará el mensaje
        numero_telefono_1 = "51975527430"  # Formato internacional sin el símbolo '+'
        numero_telefono_2 = "51987400228"

        # URL de WhatsApp
        url_whatsapp_1 = f"https://wa.me/{numero_telefono_1}?text={mensaje_codificado}"
        url_whatsapp_2 = f"https://wa.me/{numero_telefono_2}?text={mensaje_codificado}"

        webbrowser.open(url_whatsapp_1)
        webbrowser.open(url_whatsapp_2)
if __name__ == "__main__":
    ConsultaCasosApp().run()