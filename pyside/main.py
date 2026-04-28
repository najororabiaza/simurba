import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QHBoxLayout, QVBoxLayout, QFrame,
    QLabel, QPushButton, QComboBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


#  Styles CSS Qt partagés — même palette de couleurs que Django

STYLE_FENETRE    = 'background-color: #1a1a2e; color: white;'
STYLE_DASHBOARD  = 'background-color: #16213e;'
STYLE_SECTION    = '''
    QFrame {
        background-color: #0f3460;
        border-radius: 8px;
        padding: 4px;
    }
'''
STYLE_TITRE      = 'color: #e94560; font-size: 16px; font-weight: bold;'
STYLE_LABEL_INFO = 'color: #aaaaaa; font-size: 11px;'
STYLE_LABEL_VAL  = 'color: #4ade80; font-size: 12px; font-weight: bold;'

STYLE_BTN_START  = '''
    QPushButton {
        background-color: #22c55e; color: white;
        border: none; border-radius: 6px;
        padding: 8px; font-size: 13px;
    }
    QPushButton:hover  { background-color: #16a34a; }
    QPushButton:disabled { opacity: 0.4; }
'''
STYLE_BTN_PAUSE  = '''
    QPushButton {
        background-color: #fb923c; color: white;
        border: none; border-radius: 6px;
        padding: 8px; font-size: 13px;
    }
    QPushButton:hover { background-color: #ea7a1e; }
'''
STYLE_BTN_STOP   = '''
    QPushButton {
        background-color: #dc2626; color: white;
        border: none; border-radius: 6px;
        padding: 8px; font-size: 13px;
    }
    QPushButton:hover { background-color: #b91c1c; }
'''
STYLE_BTN_RESET  = '''
    QPushButton {
        background-color: #64748b; color: white;
        border: none; border-radius: 6px;
        padding: 8px; font-size: 13px;
    }
    QPushButton:hover { background-color: #475569; }
'''


#  Petite fonction utilitaire pour créer une section
#  (rectangle bleu arrondi avec un titre et un contenu)
#
#  Paramètres :
#    titre   = texte du titre de la section
#    contenu = QWidget à placer dans la section
#
#  Retourne :
#    un QFrame stylisé prêt à être ajouté dans un layout

def creer_section(titre, contenu):

    # Conteneur principal de la section
    section = QFrame()
    section.setStyleSheet(STYLE_SECTION)

    layout = QVBoxLayout(section)
    layout.setContentsMargins(8, 8, 8, 8)
    layout.setSpacing(6)

    # Titre en majuscules comme dans Django
    label_titre = QLabel(titre.upper())
    label_titre.setStyleSheet('color: #aaaaaa; font-size: 10px; font-weight: bold; letter-spacing: 1px;')
    layout.addWidget(label_titre)

    # Ligne de séparation sous le titre
    ligne = QFrame()
    ligne.setFrameShape(QFrame.HLine)
    ligne.setStyleSheet('color: #1a1a2e;')
    layout.addWidget(ligne)

    # Contenu de la section
    layout.addWidget(contenu)

    return section


class FenetrePrincipale(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle('Simurba Desktop')
        self.resize(1100, 700)
        self.setMinimumSize(800, 500)
        self.setStyleSheet(STYLE_FENETRE)

        # ── Widget central ──
        widget_central = QWidget()
        self.setCentralWidget(widget_central)

        layout_principal = QHBoxLayout(widget_central)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.setSpacing(0)

        # ── Zone canvas (gauche) ──
        self.zone_canvas = QFrame()
        self.zone_canvas.setStyleSheet('background-color: #0d1020;')
        layout_principal.addWidget(self.zone_canvas, stretch=3)

        # ── Séparateur ──
        separateur = QFrame()
        separateur.setFrameShape(QFrame.VLine)
        separateur.setStyleSheet('color: #333333;')
        layout_principal.addWidget(separateur)

        # ── Zone dashboard (droite) ──
        self.zone_dashboard = QFrame()
        self.zone_dashboard.setStyleSheet(STYLE_DASHBOARD)
        self.zone_dashboard.setFixedWidth(280)
        layout_principal.addWidget(self.zone_dashboard)

        # On construit le contenu du dashboard
        self._construire_dashboard()


    def _construire_dashboard(self):

        # Layout vertical — les sections s'empilent de haut en bas
        layout = QVBoxLayout(self.zone_dashboard)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)


        # ── En-tête : titre Simurba ──
        titre = QLabel('🚦 Simurba Desktop')
        titre.setStyleSheet(STYLE_TITRE)
        layout.addWidget(titre)


        # ── Section 1 : Contrôles ──
        contenu_controles = QWidget()
        layout_ctrl = QVBoxLayout(contenu_controles)
        layout_ctrl.setContentsMargins(0, 0, 0, 0)
        layout_ctrl.setSpacing(6)

        # Ligne état : label + valeur côte à côte
        ligne_etat = QWidget()
        layout_etat = QHBoxLayout(ligne_etat)
        layout_etat.setContentsMargins(0, 0, 0, 0)
        label_etat_txt = QLabel('État :')
        label_etat_txt.setStyleSheet(STYLE_LABEL_INFO)
        self.label_etat = QLabel('en cours...')
        self.label_etat.setStyleSheet(STYLE_LABEL_VAL)
        self.label_etat.setAlignment(Qt.AlignRight)
        layout_etat.addWidget(label_etat_txt)
        layout_etat.addWidget(self.label_etat)
        layout_ctrl.addWidget(ligne_etat)

        # Boutons de contrôle
        self.btn_start = QPushButton('▶  Démarrer')
        self.btn_start.setStyleSheet(STYLE_BTN_START)
        layout_ctrl.addWidget(self.btn_start)

        self.btn_pause = QPushButton('⏸  Pauser')
        self.btn_pause.setStyleSheet(STYLE_BTN_PAUSE)
        layout_ctrl.addWidget(self.btn_pause)

        self.btn_reset = QPushButton('↺  Réinitialiser')
        self.btn_reset.setStyleSheet(STYLE_BTN_RESET)
        layout_ctrl.addWidget(self.btn_reset)

        self.btn_stop = QPushButton('⏹  Arrêter')
        self.btn_stop.setStyleSheet(STYLE_BTN_STOP)
        layout_ctrl.addWidget(self.btn_stop)

        layout.addWidget(creer_section('Contrôles', contenu_controles))


        # ── Section 2 : Trafic en direct ──
        contenu_trafic = QWidget()
        layout_trafic = QVBoxLayout(contenu_trafic)
        layout_trafic.setContentsMargins(0, 0, 0, 0)
        layout_trafic.setSpacing(4)

        # Compteurs Fluide / Ralenti / Bouchon
        self.label_fluide  = self._creer_ligne_stat('● Fluide',  '#4ade80', layout_trafic)
        self.label_ralenti = self._creer_ligne_stat('● Ralenti', '#fb923c', layout_trafic)
        self.label_bouchon = self._creer_ligne_stat('● Bouchon', '#ef4444', layout_trafic)

        layout.addWidget(creer_section('Trafic en direct', contenu_trafic))


        # ── Section 3 : Scénario Monte Carlo ──
        contenu_scenario = QWidget()
        layout_scenario = QVBoxLayout(contenu_scenario)
        layout_scenario.setContentsMargins(0, 0, 0, 0)

        # Menu déroulant avec les 4 scénarios
        self.combo_scenario = QComboBox()
        self.combo_scenario.addItems([
            'Normal',
            'Heure de pointe',
            'Nuit',
            'Accident',
        ])
        self.combo_scenario.setStyleSheet('''
            QComboBox {
                background-color: #1a1a2e; color: white;
                border: 1px solid #334155; border-radius: 4px;
                padding: 5px; font-size: 12px;
            }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView {
                background-color: #1a1a2e; color: white;
                selection-background-color: #e94560;
            }
        ''')
        layout_scenario.addWidget(self.combo_scenario)

        # Risque de bouchon estimé
        ligne_risque = QWidget()
        layout_risque = QHBoxLayout(ligne_risque)
        layout_risque.setContentsMargins(0, 4, 0, 0)
        lbl_risque_txt = QLabel('Risque bouchon :')
        lbl_risque_txt.setStyleSheet(STYLE_LABEL_INFO)
        self.label_risque = QLabel('—')
        self.label_risque.setStyleSheet('color: #ef4444; font-weight: bold;')
        self.label_risque.setAlignment(Qt.AlignRight)
        layout_risque.addWidget(lbl_risque_txt)
        layout_risque.addWidget(self.label_risque)
        layout_scenario.addWidget(ligne_risque)

        layout.addWidget(creer_section('Scénario Monte Carlo', contenu_scenario))


        # ── Section 4 : Optimisation des feux ──
        contenu_optim = QWidget()
        layout_optim = QVBoxLayout(contenu_optim)
        layout_optim.setContentsMargins(0, 0, 0, 0)
        layout_optim.setSpacing(4)

        self.label_rouge = self._creer_ligne_info('Feu rouge optimal', '—', layout_optim)
        self.label_vert  = self._creer_ligne_info('Feu vert optimal',  '—', layout_optim)
        self.label_gain  = self._creer_ligne_info('Gain fluidité',     '—', layout_optim, val_color='#4ade80')

        layout.addWidget(creer_section('Optimisation des feux', contenu_optim))


        # ── Espace flexible en bas ──
        layout.addStretch()


    def _creer_ligne_stat(self, texte, couleur, layout_parent):
        """Crée une ligne 'Fluide : 0' avec la couleur correspondante."""
        ligne = QWidget()
        layout_ligne = QHBoxLayout(ligne)
        layout_ligne.setContentsMargins(0, 0, 0, 0)
        lbl_txt = QLabel(texte)
        lbl_txt.setStyleSheet(f'color: {couleur}; font-size: 12px;')
        lbl_val = QLabel('0')
        lbl_val.setStyleSheet(f'color: {couleur}; font-size: 12px; font-weight: bold;')
        lbl_val.setAlignment(Qt.AlignRight)
        layout_ligne.addWidget(lbl_txt)
        layout_ligne.addWidget(lbl_val)
        layout_parent.addWidget(ligne)
        # On retourne lbl_val pour pouvoir le mettre à jour plus tard
        return lbl_val


    def _creer_ligne_info(self, texte, valeur, layout_parent, val_color='white'):
        """Crée une ligne 'Texte : valeur' générique."""
        ligne = QWidget()
        layout_ligne = QHBoxLayout(ligne)
        layout_ligne.setContentsMargins(0, 0, 0, 0)
        lbl_txt = QLabel(texte)
        lbl_txt.setStyleSheet(STYLE_LABEL_INFO)
        lbl_val = QLabel(valeur)
        lbl_val.setStyleSheet(f'color: {val_color}; font-size: 12px; font-weight: bold;')
        lbl_val.setAlignment(Qt.AlignRight)
        layout_ligne.addWidget(lbl_txt)
        layout_ligne.addWidget(lbl_val)
        layout_parent.addWidget(ligne)
        return lbl_val


#  Lancement de l'application

if __name__ == '__main__':

    app = QApplication(sys.argv)

    fenetre = FenetrePrincipale()
    fenetre.show()

    sys.exit(app.exec())