import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget
from PySide6.QtCore import Qt


#  Point d'entrée de l'application desktop Simurba
#
#  QApplication = le gestionnaire principal de l'application
#  QMainWindow  = la fenêtre principale avec barre de titre


class FenetrePrincipale(QMainWindow):

    def __init__(self):
        # On appelle le constructeur de QMainWindow
        super().__init__()

        # Titre de la fenêtre (affiché dans la barre de titre macOS)
        self.setWindowTitle('Simurba Desktop')

        # Taille initiale de la fenêtre : largeur x hauteur en pixels
        self.resize(1100, 700)

        # Taille minimale — la fenêtre ne peut pas être plus petite
        self.setMinimumSize(800, 500)

        # Couleur de fond de la fenêtre — même bleu nuit que Django
        self.setStyleSheet('background-color: #1a1a2e; color: white;')


#  Lancement de l'application

if __name__ == '__main__':

    # QApplication doit être créé avant tout widget
    # sys.argv transmet les arguments de ligne de commande à Qt
    app = QApplication(sys.argv)

    # On crée et on affiche la fenêtre principale
    fenetre = FenetrePrincipale()
    fenetre.show()

    # app.exec() lance la boucle d'événements Qt
    # Elle tourne jusqu'à ce que l'utilisateur ferme la fenêtre
    sys.exit(app.exec())