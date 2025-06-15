import sys
import os
import json
import requests # type: ignore
from PyQt5.QtWidgets import ( # type: ignore
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QMessageBox, QHBoxLayout, QComboBox, QSpinBox, QCheckBox, QFormLayout, QGroupBox, QScrollArea, QGridLayout
)
from PyQt5.QtGui import QPixmap, QFont # type: ignore
from PyQt5.QtCore import Qt # type: ignore
from io import BytesIO

INVENTORY_FILE = "inventarios/demo.json"

class InventoryViewer(QWidget):
    def __init__(self, inventory):
        super().__init__()
        self.setWindowTitle("Inventario de Cartas")
        layout = QVBoxLayout()
        scroll = QScrollArea()
        container = QWidget()
        grid = QGridLayout()
        for i, card in enumerate(inventory):
            info = f"{card['nombre']} ({card['tipo']})\nATK: {card['atk']} DEF: {card['def']}\nNivel: {card['nivel']} Rareza: {card['rareza']}\nEn uso: {card['en_uso']}"
            label = QLabel(info)
            label.setWordWrap(True)
            # Buscar imagen desde la API usando el nombre
            try:
                url = f"https://db.ygoprodeck.com/api/v7/cardinfo.php?name={card['nombre']}"
                r = requests.get(url)
                data = r.json()
                img_url = data["data"][0]["card_images"][0]["image_url"]
                img_data = requests.get(img_url).content
                pixmap = QPixmap()
                pixmap.loadFromData(img_data)
                img_label = QLabel()
                img_label.setPixmap(pixmap.scaledToHeight(120))
            except Exception:
                img_label = QLabel("Sin imagen")
            grid.addWidget(img_label, i, 0)
            grid.addWidget(label, i, 1)
        container.setLayout(grid)
        scroll.setWidget(container)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        self.setLayout(layout)
        self.resize(600, 400)

class CardSearch(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Buscar Carta - Yu-Gi-Oh!")
        self.setGeometry(100, 100, 600, 600)
        self.setStyleSheet("background-color: #f9f9f9;")

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Nombre de la carta")
        layout.addWidget(self.search_input)

        self.search_button = QPushButton("🔍 Buscar")
        self.search_button.clicked.connect(self.search_card)
        layout.addWidget(self.search_button)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.image_label)

        self.info_label = QLabel("")
        self.info_label.setWordWrap(True)
        self.info_label.setFont(QFont("Segoe UI", 10))
        layout.addWidget(self.info_label)

        self.form_group = QGroupBox("Detalles adicionales")
        self.form_layout = QFormLayout()

        self.cantidad_input = QSpinBox()
        self.cantidad_input.setMinimum(1)
        self.form_layout.addRow("Cantidad:", self.cantidad_input)

        self.rareza_input = QLineEdit()
        self.form_layout.addRow("Rareza:", self.rareza_input)

        self.en_uso_input = QCheckBox("¿En uso (en deck)?")
        self.form_layout.addRow("", self.en_uso_input)

        self.form_group.setLayout(self.form_layout)
        layout.addWidget(self.form_group)
        self.form_group.setVisible(False)

        self.add_button = QPushButton("➕ Agregar al inventario")
        self.add_button.clicked.connect(self.add_to_inventory)
        self.add_button.setVisible(False)
        layout.addWidget(self.add_button)

        self.view_inventory_button = QPushButton("📋 Ver Inventario")
        self.view_inventory_button.clicked.connect(self.show_inventory)
        layout.addWidget(self.view_inventory_button)

        self.card_data = None

    def search_card(self):
        name = self.search_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Ingresa un nombre para buscar.")
            return

        url = f"https://db.ygoprodeck.com/api/v7/cardinfo.php?name={name}"
        try:
            r = requests.get(url)
            data = r.json()
            if "data" not in data:
                raise ValueError("Carta no encontrada")
            card = data["data"][0]
            self.card_data = card
            self.display_card(card)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"No se encontró la carta: {name}")
            self.image_label.clear()
            self.info_label.clear()
            self.form_group.setVisible(False)
            self.add_button.setVisible(False)

    def display_card(self, card):
        info = f"Nombre: {card['name']} Tipo: {card['type']}"
        if "attribute" in card:
            info += f"Atributo: {card['attribute']}"
        if "atk" in card and "def" in card:
            info += f"ATK/DEF: {card['atk']} / {card['def']}"
        if "level" in card:
            info += f"Nivel: {card['level']}"
        elif "rank" in card:
            info += f"Rango: {card['rank']}"

        self.info_label.setText(info)

        image_url = card["card_images"][0]["image_url"]
        img_data = requests.get(image_url).content
        pixmap = QPixmap()
        pixmap.loadFromData(img_data)
        self.image_label.setPixmap(pixmap.scaledToHeight(250))

        self.form_group.setVisible(True)
        self.add_button.setVisible(True)

    def add_to_inventory(self):
        if not self.card_data:
            return

        new_card = {
            "nombre": self.card_data.get("name"),
            "tipo": self.card_data.get("type"),
            "atributo": self.card_data.get("attribute", ""),
            "atk": self.card_data.get("atk", ""),
            "def": self.card_data.get("def", ""),
            "nivel": self.card_data.get("level", self.card_data.get("rank", "")),
            "cantidad": self.cantidad_input.value(),
            "rareza": self.rareza_input.text(),
            "en_uso": self.en_uso_input.isChecked()
        }

        os.makedirs("inventarios", exist_ok=True)
        if not os.path.exists(INVENTORY_FILE):
            with open(INVENTORY_FILE, "w") as f:
                json.dump([], f)

        with open(INVENTORY_FILE, "r", encoding="utf-8") as f:
            inventario = json.load(f)

        inventario.append(new_card)

        with open(INVENTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(inventario, f, indent=4)

        QMessageBox.information(self, "Guardado", "Carta agregada al inventario.")

    def show_inventory(self):
        if not os.path.exists(INVENTORY_FILE):
            QMessageBox.information(self, "Inventario vacío", "No hay cartas guardadas.")
            return
        with open(INVENTORY_FILE, "r", encoding="utf-8") as f:
            inventario = json.load(f)
        self.inventory_viewer = InventoryViewer(inventario)
        self.inventory_viewer.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = CardSearch()
    ventana.show()
    sys.exit(app.exec_())
