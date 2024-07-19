import sys
import requests
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget, QComboBox, QInputDialog, QDateEdit, QMessageBox, QMessageBox
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QDate


api_key = '1pOC4W9fimTfKr0qAb9nLOAbkFx9uE8CIEtiWexG'

def get_available_rovers():
    url = f'https://api.nasa.gov/mars-photos/api/v1/rovers?api_key={api_key}'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        rovers = [rover['name'] for rover in data['rovers']]
        
        # Supprimez le rover Perseverance s'il est présent dans la liste
        if "Perseverance" in rovers:
            rovers.remove("Perseverance")
        return rovers
    else:
        return []

# Fonction pour obtenir les images du rover sélectionné
def get_rover_images(selected_rover, selected_date):
    url = f'https://api.nasa.gov/mars-photos/api/v1/rovers/{selected_rover}/photos?earth_date={selected_date}&api_key={api_key}'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data['photos']:
            img_src = data['photos'][0]['img_src']
            return img_src
    return None

def get_mars_weather_for_sol(sol):
    url = f'https://api.nasa.gov/insight_weather/?api_key={api_key}&feedtype=json&ver=1.0'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if sol in data['sol_keys']:
            weather_info = data[sol]
            return weather_info
    return None

# Classe pour le thread de téléchargement de l'image
class DownloadThread(QThread):
    imageDownloaded = pyqtSignal(str)

    def __init__(self, selected_rover, selected_date):
        super(DownloadThread, self).__init__()
        self.selected_rover = selected_rover
        self.selected_date = selected_date

    def run(self):
        img_url = get_rover_images(self.selected_rover, self.selected_date)
        if img_url:
            response = requests.get(img_url)
            if response.status_code == 200:
                image_path = "rover_image.jpg"
                with open(image_path, 'wb') as file:
                    file.write(response.content)
                self.imageDownloaded.emit(image_path)
            else:
                self.imageDownloaded.emit(None)
        else:
            self.imageDownloaded.emit(None)

class MarsWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MarsWindow, self).__init__(parent)
        self.setWindowTitle('NASA APIs')
        self.setFixedSize(1280, 720)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout(self.central_widget)

        # Bouton pour afficher la liste des rovers
        self.rover_button = QPushButton("Mars Rover")
        self.layout.addWidget(self.rover_button)
        self.rover_button.clicked.connect(self.show_rover_list)

        # Bouton pour afficher les données météorologiques
        self.weather_button = QPushButton("Mars Weather")
        self.layout.addWidget(self.weather_button)
        self.weather_button.clicked.connect(self.show_mars_weather)

        # Liste déroulante pour sélectionner un rover
        self.rover_combo = QComboBox(self)
        self.layout.addWidget(self.rover_combo)
        self.rover_combo.hide()
        
        # Entrée de date pour choisir la date de la photo
        self.date_edit = QDateEdit(self)
        self.date_edit.setDate(QDate.currentDate())  # Date par défaut
        self.layout.addWidget(self.date_edit)
        self.date_edit.hide()

        # Bouton pour afficher l'image du rover
        self.show_image_button = QPushButton("Afficher l'image du rover")
        self.layout.addWidget(self.show_image_button)
        self.show_image_button.clicked.connect(self.show_rover_image)
        self.show_image_button.hide()

        # Créez un QLabel pour afficher l'image du rover
        self.rover_image_label = QLabel(self)
        self.rover_image_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.rover_image_label)
        self.rover_image_label.hide()

        # Bouton de retour pour revenir à la sélection du rover
        self.return_button = QPushButton("Retour")
        self.return_button.clicked.connect(self.return_to_rover_selection)
        self.return_button.hide()
        self.layout.addWidget(self.return_button)

        # Bouton pour retourner au menu principal
        self.return_to_menu_button = QPushButton("Retour au menu")
        self.return_to_menu_button.clicked.connect(self.return_to_menu)
        self.return_to_menu_button.hide()
        self.layout.addWidget(self.return_to_menu_button)

    def show_rover_list(self):
        # Masquer le bouton "Mars Rover" et le bouton "Mars Weather"
        self.rover_button.hide()
        self.weather_button.hide()
    
        # Ajoutez le bouton "Retour au menu"
        self.menu_button = QPushButton("Retour au menu")
        self.menu_button.clicked.connect(self.return_to_menu)
        self.layout.addWidget(self.menu_button)

        self.rover_combo.show()
        self.date_edit.show()   # Afficher l'entrée de la date
        self.show_image_button.show()
    
        # Charger la liste des rovers disponibles
        available_rovers = get_available_rovers()
        self.rover_combo.addItems(available_rovers)

    def show_rover_image(self):
        selected_rover = self.rover_combo.currentText()
        selected_date = self.date_edit.date().toString('yyyy-MM-dd')  # Récupère la date sélectionnée

        # Utiliser un thread pour le téléchargement de l'image
        self.download_thread = DownloadThread(selected_rover, selected_date)
        self.download_thread.imageDownloaded.connect(self.display_rover_image)
        self.download_thread.start()
    
    def display_rover_image(self, image_path):
        if image_path:
            pixmap = QPixmap()
            pixmap.load(image_path)
            if not pixmap.isNull():
                # Afficher l'image et masquer les boutons
                self.rover_image_label.setPixmap(pixmap.scaledToHeight(360))
                self.rover_image_label.show()
                self.rover_combo.hide()
                self.show_image_button.hide()
                self.return_button.show()
        else:
            # Afficher un message d'erreur
            self.show_error_message("Aucune photo disponible pour la date sélectionnée.")

    def return_to_rover_selection(self):
        # Masquer l'image, afficher la liste déroulante et le bouton
        self.rover_image_label.clear()
        self.rover_image_label.hide()
        self.rover_combo.show()
        self.show_image_button.show()
        self.return_button.hide()

    def show_mars_weather(self):
        # Créez un dialogue pour saisir le sol (jour) souhaité
        sol, ok = QInputDialog.getText(self, 'Mars Weather', 'Entrez le sol (jour) souhaité:')
        if ok:
            # Obtenez les données météorologiques pour le sol souhaité
            weather_data = get_mars_weather_for_sol(sol)
            if weather_data:
                # Création d'un QLabel pour afficher les données météorologiques
                weather_label = QLabel(self)
                weather_label.setAlignment(Qt.AlignCenter)
                weather_text = f"Mars Weather (Sol {sol}):\n"
                weather_text += f"Min Temp: {weather_data['AT']['mn']}°C, Max Temp: {weather_data['AT']['mx']}°C\n"
                weather_text += f"Pressure: {weather_data['PRE']['av']} Pa"
                weather_label.setText(weather_text)
                self.setCentralWidget(weather_label)
    
    def return_to_menu(self):
        # Masquer tous les éléments inutiles
        self.rover_combo.hide()
        self.show_image_button.hide()
        self.menu_button.hide()
        self.date_edit.hide()
        self.rover_image_label.hide()
        self.return_button.hide()

        # Afficher à nouveau les boutons "Mars Rover" et "Mars Weather"
        self.rover_button.show()
        self.weather_button.show()
        self.return_to_menu_button.hide()
    
        # Afficher à nouveau les boutons "Mars Rover" et "Mars Weather"
        self.rover_button.show()
        self.weather_button.show()

    def show_error_message(self, message):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText(message)
        msg.setWindowTitle("Erreur")
        msg.exec_()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MarsWindow()
    window.show()
    sys.exit(app.exec_())
