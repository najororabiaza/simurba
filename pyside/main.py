import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QHBoxLayout, QFrame
)
from PySide6.QtCore import Qt


#  Point d'entrée de l'application desktop Simurba
#
#  QApplication  = le gestionnaire principal de l'application
#  QMainWindow   = la fenêtre principale avec barre de titre
#  QHBoxLayout   = disposition horizontale (canvas gauche + dashboard droit)
#  QFrame        = widget de base pour les deux panneaux


class FenetrePrincipale(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle('Simurba Desktop')
        self.resize(1100, 700)
        self.setMinimumSize(800, 500)
        self.setStyleSheet('background-color: #1a1a2e; color: white;')

        # ── Widget central qui contient tout ──
        # QMainWindow exige un widget central — on y met notre layout
        widget_central = QWidget()
        self.setCentralWidget(widget_central)

        # ── Layout horizontal : canvas à gauche, dashboard à droite ──
        # QHBoxLayout dispose les widgets de gauche à droite
        layout = QHBoxLayout(widget_central)
        layout.setContentsMargins(0, 0, 0, 0)  # pas de marge extérieure
        layout.setSpacing(0)                    # pas d'espace entre les deux zones

        # ── Zone canvas (gauche) ──
        self.zone_canvas = QFrame()
        self.zone_canvas.setStyleSheet('background-color: #0d1020;')
        # stretch=3 = la zone canvas prend 3/4 de la largeur disponible
        layout.addWidget(self.zone_canvas, stretch=3)

        # ── Ligne de séparation verticale ──
        separateur = QFrame()
        separateur.setFrameShape(QFrame.VLine)
        separateur.setStyleSheet('color: #333;')
        layout.addWidget(separateur)

        # ── Zone dashboard (droite) ──
        self.zone_dashboard = QFrame()
        self.zone_dashboard.setStyleSheet('background-color: #16213e;')
        self.zone_dashboard.setFixedWidth(280)  # largeur fixe comme dans Django
        layout.addWidget(self.zone_dashboard)


#  Lancement de l'application

if __name__ == '__main__':

    # QApplication doit être créé avant tout widget
    app = QApplication(sys.argv)

    fenetre = FenetrePrincipale()
    fenetre.show()

    # app.exec() lance la boucle d'événements Qt
    # Elle tourne jusqu'à ce que l'utilisateur ferme la fenêtre
    sys.exit(app.exec())