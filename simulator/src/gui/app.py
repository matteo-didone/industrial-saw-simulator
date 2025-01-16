# simulator/src/gui/app.py
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QPushButton, QLabel, QComboBox, QFrame)
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QPalette, QColor
import sys

class SawSimulatorGUI(QMainWindow):
    def __init__(self, simulator):
        super().__init__()
        self.simulator = simulator
        self.init_ui()
        
        # Timer per aggiornare la GUI
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_values)
        self.update_timer.start(100)  # Aggiorna ogni 100ms

    def init_ui(self):
        self.setWindowTitle('Industrial Saw Simulator')
        self.setGeometry(100, 100, 800, 600)

        # Widget principale
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        # Sezione stato macchina
        status_frame = self.create_frame("Machine Status")
        status_layout = QVBoxLayout()
        
        self.state_label = QLabel('State: INACTIVE')
        self.safety_label = QLabel('Safety Barrier: CLOSED')
        
        status_layout.addWidget(self.state_label)
        status_layout.addWidget(self.safety_label)
        status_frame.setLayout(status_layout)
        layout.addWidget(status_frame)

        # Sezione controlli
        controls_frame = self.create_frame("Controls")
        controls_layout = QHBoxLayout()
        
        self.start_button = QPushButton('Start')
        self.stop_button = QPushButton('Stop')
        self.pause_button = QPushButton('Pause')
        self.barrier_button = QPushButton('Toggle Barrier')
        
        self.start_button.clicked.connect(self.simulator.start)
        self.stop_button.clicked.connect(self.simulator.stop)
        self.pause_button.clicked.connect(self.simulator.pause)
        self.barrier_button.clicked.connect(self.simulator.toggle_safety_barrier)
        
        controls_layout.addWidget(self.start_button)
        controls_layout.addWidget(self.stop_button)
        controls_layout.addWidget(self.pause_button)
        controls_layout.addWidget(self.barrier_button)
        
        controls_frame.setLayout(controls_layout)
        layout.addWidget(controls_frame)

        # Sezione materiale
        material_frame = self.create_frame("Material Selection")
        material_layout = QHBoxLayout()
        
        self.material_combo = QComboBox()
        self.material_combo.addItems(['steel', 'aluminum', 'wood'])
        self.material_combo.currentTextChanged.connect(self.simulator.set_material)
        
        material_layout.addWidget(QLabel('Material:'))
        material_layout.addWidget(self.material_combo)
        
        material_frame.setLayout(material_layout)
        layout.addWidget(material_frame)

        # Sezione metriche
        metrics_frame = self.create_frame("Metrics")
        metrics_layout = QVBoxLayout()
        
        self.speed_label = QLabel('Cutting Speed: 0.0 m/min')
        self.pieces_label = QLabel('Pieces Cut: 0')
        self.power_label = QLabel('Power Consumption: 0.0 kW')
        self.temp_label = QLabel('Temperature: 20.0 °C')
        self.wear_label = QLabel('Blade Wear: 0.0%')
        
        metrics_layout.addWidget(self.speed_label)
        metrics_layout.addWidget(self.pieces_label)
        metrics_layout.addWidget(self.power_label)
        metrics_layout.addWidget(self.temp_label)
        metrics_layout.addWidget(self.wear_label)
        
        metrics_frame.setLayout(metrics_layout)
        layout.addWidget(metrics_frame)

    def create_frame(self, title):
        """Crea un frame con bordo e titolo"""
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        frame.setLineWidth(1)
        frame.setMidLineWidth(0)
        
        # Aggiungi padding
        frame.setContentsMargins(10, 10, 10, 10)
        
        # Imposta uno sfondo leggermente diverso
        palette = frame.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(240, 240, 240))
        frame.setAutoFillBackground(True)
        frame.setPalette(palette)
        
        # Aggiungi il titolo
        if title:
            layout = QVBoxLayout(frame)
            title_label = QLabel(title)
            font = title_label.font()
            font.setBold(True)
            title_label.setFont(font)
            layout.addWidget(title_label)
        
        return frame

    def update_values(self):
        """Aggiorna tutti i valori visualizzati nella GUI"""
        state = self.simulator.get_state()
        
        # Aggiorna le etichette
        self.state_label.setText(f'State: {state["state"].upper()}')
        self.safety_label.setText(f'Safety Barrier: {"CLOSED" if state["safety_barrier"] else "OPEN"}')
        self.speed_label.setText(f'Cutting Speed: {state["cutting_speed"]:.1f} m/min')
        self.pieces_label.setText(f'Pieces Cut: {state["pieces_cut"]}')
        self.power_label.setText(f'Power Consumption: {state["power_consumption"]:.1f} kW')
        self.temp_label.setText(f'Temperature: {state["temperature"]:.1f} °C')
        self.wear_label.setText(f'Blade Wear: {state["blade_wear"]:.1f}%')
        
        # Imposta colori in base allo stato
        if state["state"] == "running":
            self.state_label.setStyleSheet("color: green")
        elif state["state"] == "alarm":
            self.state_label.setStyleSheet("color: red")
        elif state["state"] == "error":
            self.state_label.setStyleSheet("color: darkred")
        else:
            self.state_label.setStyleSheet("")
            
        # Imposta colori per temperatura
        if state["temperature"] > 50:
            self.temp_label.setStyleSheet("color: red")
        elif state["temperature"] > 40:
            self.temp_label.setStyleSheet("color: orange")
        else:
            self.temp_label.setStyleSheet("")

def run_gui(simulator):
    """Funzione per avviare la GUI"""
    app = QApplication(sys.argv)
    gui = SawSimulatorGUI(simulator)
    gui.show()
    sys.exit(app.exec())