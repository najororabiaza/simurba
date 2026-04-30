import sys
import math
import random

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QHBoxLayout, QVBoxLayout, QFrame,
    QLabel, QPushButton, QComboBox,
    QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont

sys.path.insert(0, '.')
from traffic import markov, queue_model, monte_carlo, optimizer


#  Palette de couleurs centralisée

C_BG_MAIN     = '#1a1a2e'
C_BG_DASH     = '#16213e'
C_BG_SECTION  = '#0f3460'
C_BG_DEEP     = '#0a1628'
C_ACCENT      = '#e94560'
C_FLUIDE      = '#4ade80'
C_RALENTI     = '#fb923c'
C_BOUCHON     = '#ef4444'
C_TEXT_MUTED  = '#94a3b8'
C_TEXT_LABEL  = '#64748b'
C_BORDER      = '#1e3a5f'


#  Styles des boutons

STYLE_BTN_START = f'''
    QPushButton {{
        background-color: #22c55e; color: white;
        border: none; border-radius: 6px;
        padding: 9px; font-size: 13px; font-weight: 600;
    }}
    QPushButton:hover    {{ background-color: #16a34a; }}
    QPushButton:disabled {{ background-color: #1a4a2e; color: #4a7a5e; }}
'''
STYLE_BTN_PAUSE = f'''
    QPushButton {{
        background-color: {C_RALENTI}; color: white;
        border: none; border-radius: 6px;
        padding: 9px; font-size: 13px; font-weight: 600;
    }}
    QPushButton:hover    {{ background-color: #ea7a1e; }}
    QPushButton:disabled {{ background-color: #3a2a1a; color: #7a5a3a; }}
'''
STYLE_BTN_RESET = f'''
    QPushButton {{
        background-color: #334155; color: white;
        border: none; border-radius: 6px;
        padding: 9px; font-size: 13px; font-weight: 600;
    }}
    QPushButton:hover {{ background-color: #475569; }}
'''
STYLE_BTN_STOP = f'''
    QPushButton {{
        background-color: {C_BOUCHON}; color: white;
        border: none; border-radius: 6px;
        padding: 9px; font-size: 13px; font-weight: 600;
    }}
    QPushButton:hover    {{ background-color: #b91c1c; }}
    QPushButton:disabled {{ background-color: #3a1a1a; color: #7a3a3a; }}
'''

COULEURS_ETAT = {
    'fluide':  QColor(C_FLUIDE),
    'ralenti': QColor(C_RALENTI),
    'bouchon': QColor(C_BOUCHON),
}

NOEUDS_REL = [
    (0.18, 0.18), (0.50, 0.18), (0.82, 0.18),
    (0.18, 0.50), (0.50, 0.50), (0.82, 0.50),
    (0.18, 0.82), (0.50, 0.82), (0.82, 0.82),
]

ROUTES_DEF = [
    (0, 1), (1, 2),
    (3, 4), (4, 5),
    (6, 7), (7, 8),
    (0, 3), (1, 4),
    (2, 5), (3, 6),
    (4, 7), (5, 8),
]

SCENARIOS_CLES = ['normal', 'heure_de_pointe', 'nuit', 'accident']


class CanvasReseau(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f'background-color: {C_BG_DEEP};')
        self.etats_routes = markov.etat_initial(12)
        self.vehicules    = [random.random() for _ in range(12)]
        self.vitesses     = [0.003 + random.random() * 0.002 for _ in range(12)]

    def noeuds_px(self):
        w, h = self.width(), self.height()
        return [(int(rx * w), int(ry * h)) for rx, ry in NOEUDS_REL]

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        noeuds = self.noeuds_px()

        for i, (idx_from, idx_to) in enumerate(ROUTES_DEF):
            x1, y1 = noeuds[idx_from]
            x2, y2 = noeuds[idx_to]
            etat    = self.etats_routes.get(i, 'fluide')
            couleur = COULEURS_ETAT.get(etat, QColor(C_FLUIDE))
            pen = QPen(couleur, 5)
            pen.setCapStyle(Qt.RoundCap)
            painter.setOpacity(0.85)
            painter.setPen(pen)
            painter.drawLine(x1, y1, x2, y2)

        painter.setOpacity(1.0)

        for x, y in noeuds:
            painter.setPen(QPen(QColor('#333355'), 2))
            painter.setBrush(QBrush(QColor(50, 50, 80, 100)))
            painter.drawEllipse(int(x - 20), int(y - 20), 40, 40)
            painter.setPen(QPen(QColor('#1a5c1a'), 1))
            painter.setBrush(QBrush(QColor(55, 130, 55, 180)))
            painter.drawEllipse(int(x - 9), int(y - 9), 18, 18)

        for i, (idx_from, idx_to) in enumerate(ROUTES_DEF):
            x1, y1 = noeuds[idx_from]
            x2, y2 = noeuds[idx_to]
            t      = self.vehicules[i]
            vx     = x1 + (x2 - x1) * t
            vy     = y1 + (y2 - y1) * t
            dx, dy = x2 - x1, y2 - y1
            dist   = math.sqrt(dx*dx + dy*dy) or 1
            vx    += (-dy / dist) * 10
            vy    += ( dx / dist) * 10
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor('#e2e8f0')))
            painter.drawEllipse(int(vx - 5), int(vy - 5), 10, 10)

    # Remplace avancer_vehicules par ceci
    def avancer_vehicules(self):
        """Avance les véhicules — vitesse selon l'état Markov de leur route."""
        for i in range(12):

            # La vitesse dépend de l'état de la route
            etat = self.etats_routes.get(i, 'fluide')

            if etat == 'fluide':
                # Route fluide = vitesse normale
                multiplicateur = 1.0
            elif etat == 'ralenti':
                # Route ralentie = moitié de la vitesse
                multiplicateur = 0.4
            else:
                # Bouchon = très lent
                multiplicateur = 0.1

            self.vehicules[i] += self.vitesses[i] * multiplicateur
            if self.vehicules[i] > 1.0:
                self.vehicules[i] = 0.0

        self.update()

    def mettre_a_jour_etats(self, nouveaux_etats):
        self.etats_routes = nouveaux_etats
        self.update()


def separateur_h():
    """Ligne horizontale de séparation discrète."""
    ligne = QFrame()
    ligne.setFrameShape(QFrame.HLine)
    ligne.setFixedHeight(1)
    ligne.setStyleSheet(f'background-color: {C_BORDER}; border: none;')
    return ligne


def label_section(texte):
    """Titre de section en petites majuscules espacées."""
    lbl = QLabel(texte.upper())
    lbl.setStyleSheet(f'''
        color: {C_TEXT_LABEL};
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 1.5px;
        padding-bottom: 2px;
    ''')
    return lbl


class FenetrePrincipale(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle('Simurba Desktop')
        self.resize(1100, 720)
        self.setMinimumSize(800, 520)
        self.setStyleSheet(f'background-color: {C_BG_MAIN}; color: white;')

        self.en_cours     = False
        self.etats_routes = markov.etat_initial(12)
        # Scénario actif - qui doit correspondre aux clés de SCENARIOS_CLES
        self.scenario_actuel = 'normal'

        widget_central = QWidget()
        self.setCentralWidget(widget_central)
        layout_principal = QHBoxLayout(widget_central)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.setSpacing(0)

        # ── Canvas ──
        self.canvas = CanvasReseau()
        layout_principal.addWidget(self.canvas, stretch=3)

        # ── Séparateur vertical ──
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setFixedWidth(1)
        sep.setStyleSheet(f'background-color: {C_BORDER}; border: none;')
        layout_principal.addWidget(sep)

        # ── Dashboard scrollable ──
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFixedWidth(290)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f'''
            QScrollArea {{ background-color: {C_BG_DASH}; border: none; }}
            QScrollBar:vertical {{
                background: {C_BG_DASH}; width: 4px; border: none;
            }}
            QScrollBar::handle:vertical {{
                background: {C_BORDER}; border-radius: 2px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        ''')

        contenu_dash = QWidget()
        contenu_dash.setStyleSheet(f'background-color: {C_BG_DASH};')
        scroll.setWidget(contenu_dash)
        layout_principal.addWidget(scroll)

        self._construire_dashboard(contenu_dash)
        self._connecter_boutons()

        # ── Timers ──
        self.timer_animation = QTimer()
        self.timer_animation.setInterval(16)
        self.timer_animation.timeout.connect(self.canvas.avancer_vehicules)

        self.timer_markov = QTimer()
        self.timer_markov.setInterval(2000)
        self.timer_markov.timeout.connect(self._tick_markov)

        # Démarrage automatique
        self._demarrer()

        # Calcul initial du risque de bouchon
        risque = monte_carlo.estimer_risque_bouchon(500, 12, 'normal')
        self.label_risque.setText(str(int(risque * 100)) + '%')


    def _tick_markov(self):
        self.etats_routes = markov.tick(self.etats_routes, self.scenario_actuel)
        self.canvas.mettre_a_jour_etats(self.etats_routes)

        compteurs = markov.compter_etats(self.etats_routes)
        self.label_fluide.setText(str(compteurs['fluide']))
        self.label_ralenti.setText(str(compteurs['ralenti']))
        self.label_bouchon.setText(str(compteurs['bouchon']))

        resultat = optimizer.optimiser_feux(self.etats_routes)
        self.label_rouge.setText(str(resultat['duree_rouge']) + ' s')
        self.label_vert.setText(str(resultat['duree_vert']) + ' s')
        self.label_gain.setText('+' + str(resultat['gain_pourcent']) + '%')


    def _demarrer(self):
        self.en_cours = True
        self.timer_animation.start()
        self.timer_markov.start()
        self._set_etat('en cours...', C_FLUIDE)
        self.btn_start.setEnabled(False)
        self.btn_pause.setEnabled(True)
        self.btn_stop.setEnabled(True)

    def _pauser(self):
        self.en_cours = False
        self.timer_animation.stop()
        self.timer_markov.stop()
        self._set_etat('en pause', C_RALENTI)
        self.btn_start.setEnabled(True)
        self.btn_pause.setEnabled(False)

    def _reinitialiser(self):
        self.canvas.vehicules = [0.0] * 12
        self.etats_routes = markov.etat_initial(12)
        self.canvas.mettre_a_jour_etats(self.etats_routes)
        if not self.en_cours:
            self._demarrer()

    def _arreter(self):
        self.en_cours = False
        self.timer_animation.stop()
        self.timer_markov.stop()
        self.canvas.vehicules = [0.0] * 12
        self.etats_routes = markov.etat_initial(12)
        self.canvas.mettre_a_jour_etats(self.etats_routes)
        self._set_etat('arrêté', C_BOUCHON)
        self.btn_start.setEnabled(True)
        self.btn_pause.setEnabled(False)
        self.btn_stop.setEnabled(False)
        self.canvas.update()

    def _set_etat(self, texte, couleur):
        self.label_etat.setText(texte)
        self.label_etat.setStyleSheet(
            f'color: {couleur}; font-size: 12px; font-weight: 700;'
        )

    def _changer_scenario(self, index):
        self.scenario_actuel = SCENARIOS_CLES[index]  # sauvegarde le scénario
        self.etats_routes = monte_carlo.generer_etats_initiaux(12, self.scenario_actuel)
        self.canvas.mettre_a_jour_etats(self.etats_routes)
        risque = monte_carlo.estimer_risque_bouchon(500, 12, self.scenario_actuel)
        self.label_risque.setText(str(int(risque * 100)) + '%')

    def _connecter_boutons(self):
        self.btn_start.clicked.connect(self._demarrer)
        self.btn_pause.clicked.connect(self._pauser)
        self.btn_reset.clicked.connect(self._reinitialiser)
        self.btn_stop.clicked.connect(self._arreter)
        self.combo_scenario.currentIndexChanged.connect(self._changer_scenario)


    def _construire_dashboard(self, parent):

        layout = QVBoxLayout(parent)
        layout.setContentsMargins(14, 16, 14, 16)
        layout.setSpacing(0)


        # ── En-tête ──
        header = QWidget()
        lh = QHBoxLayout(header)
        lh.setContentsMargins(0, 0, 0, 0)
        dot = QLabel('🚦')
        dot.setStyleSheet('font-size: 18px;')
        titre = QLabel('Simurba')
        titre.setStyleSheet(f'color: {C_ACCENT}; font-size: 18px; font-weight: 700;')
        lh.addWidget(dot)
        lh.addWidget(titre)
        lh.addStretch()
        layout.addWidget(header)
        layout.addSpacing(14)
        layout.addWidget(separateur_h())
        layout.addSpacing(14)


        # ── Section Contrôles ──
        layout.addWidget(label_section('Contrôles'))
        layout.addSpacing(8)

        # Ligne état
        ligne_etat = QWidget()
        le = QHBoxLayout(ligne_etat)
        le.setContentsMargins(0, 0, 0, 0)
        lbl_e = QLabel('État')
        lbl_e.setStyleSheet(f'color: {C_TEXT_MUTED}; font-size: 12px;')
        self.label_etat = QLabel('en cours...')
        self.label_etat.setStyleSheet(f'color: {C_FLUIDE}; font-size: 12px; font-weight: 700;')
        self.label_etat.setAlignment(Qt.AlignRight)
        le.addWidget(lbl_e)
        le.addWidget(self.label_etat)
        layout.addWidget(ligne_etat)
        layout.addSpacing(10)

        self.btn_start = QPushButton('▶  Démarrer')
        self.btn_start.setStyleSheet(STYLE_BTN_START)
        self.btn_pause = QPushButton('⏸  Pauser')
        self.btn_pause.setStyleSheet(STYLE_BTN_PAUSE)
        self.btn_reset = QPushButton('↺  Réinitialiser')
        self.btn_reset.setStyleSheet(STYLE_BTN_RESET)
        self.btn_stop  = QPushButton('⏹  Arrêter')
        self.btn_stop.setStyleSheet(STYLE_BTN_STOP)

        for btn in [self.btn_start, self.btn_pause, self.btn_reset, self.btn_stop]:
            layout.addWidget(btn)
            layout.addSpacing(4)

        layout.addSpacing(10)
        layout.addWidget(separateur_h())
        layout.addSpacing(14)


        # ── Section Trafic en direct ──
        layout.addWidget(label_section('Trafic en direct'))
        layout.addSpacing(10)

        self.label_fluide  = self._stat_row(C_FLUIDE,  '● Fluide',  layout)
        layout.addSpacing(6)
        self.label_ralenti = self._stat_row(C_RALENTI, '● Ralenti', layout)
        layout.addSpacing(6)
        self.label_bouchon = self._stat_row(C_BOUCHON, '● Bouchon', layout)

        layout.addSpacing(14)
        layout.addWidget(separateur_h())
        layout.addSpacing(14)


        # ── Section Scénario Monte Carlo ──
        layout.addWidget(label_section('Scénario Monte Carlo'))
        layout.addSpacing(10)

        self.combo_scenario = QComboBox()
        self.combo_scenario.addItems(['Normal', 'Heure de pointe', 'Nuit', 'Accident'])
        self.combo_scenario.setStyleSheet(f'''
            QComboBox {{
                background-color: {C_BG_DEEP}; color: white;
                border: 1px solid {C_BORDER}; border-radius: 6px;
                padding: 7px 10px; font-size: 12px;
            }}
            QComboBox::drop-down {{ border: none; width: 20px; }}
            QComboBox::down-arrow {{ color: white; }}
            QComboBox QAbstractItemView {{
                background-color: {C_BG_DEEP}; color: white;
                border: 1px solid {C_BORDER};
                selection-background-color: {C_ACCENT};
            }}
        ''')
        layout.addWidget(self.combo_scenario)
        layout.addSpacing(8)

        self.label_risque = self._info_row('Risque de bouchon', '—', layout, C_BOUCHON)

        layout.addSpacing(14)
        layout.addWidget(separateur_h())
        layout.addSpacing(14)


        # ── Section Optimisation des feux ──
        layout.addWidget(label_section('Optimisation des feux'))
        layout.addSpacing(10)

        self.label_rouge = self._info_row('Feu rouge optimal', '—',  layout, 'white')
        layout.addSpacing(6)
        self.label_vert  = self._info_row('Feu vert optimal',  '—',  layout, 'white')
        layout.addSpacing(6)
        self.label_gain  = self._info_row('Gain fluidité',     '—',  layout, C_FLUIDE)

        layout.addStretch()


    def _stat_row(self, couleur, texte, layout_parent):
        """Ligne colorée avec valeur à droite — pour Fluide/Ralenti/Bouchon."""
        conteneur = QWidget()
        conteneur.setStyleSheet(f'''
            QWidget {{
                background-color: {C_BG_SECTION};
                border-radius: 6px;
                padding: 2px;
            }}
        ''')
        ll = QHBoxLayout(conteneur)
        ll.setContentsMargins(10, 6, 10, 6)
        lbl_t = QLabel(texte)
        lbl_t.setStyleSheet(f'color: {couleur}; font-size: 12px; background: transparent;')
        lbl_v = QLabel('0')
        lbl_v.setStyleSheet(
            f'color: {couleur}; font-size: 14px; font-weight: 700; background: transparent;'
        )
        lbl_v.setAlignment(Qt.AlignRight)
        ll.addWidget(lbl_t)
        ll.addWidget(lbl_v)
        layout_parent.addWidget(conteneur)
        return lbl_v

    def _info_row(self, texte, valeur, layout_parent, val_color='white'):
        """Ligne label + valeur générique."""
        ligne = QWidget()
        ll = QHBoxLayout(ligne)
        ll.setContentsMargins(0, 0, 0, 0)
        lbl_t = QLabel(texte)
        lbl_t.setStyleSheet(f'color: {C_TEXT_MUTED}; font-size: 12px;')
        lbl_v = QLabel(valeur)
        lbl_v.setStyleSheet(
            f'color: {val_color}; font-size: 12px; font-weight: 700;'
        )
        lbl_v.setAlignment(Qt.AlignRight)
        ll.addWidget(lbl_t)
        ll.addWidget(lbl_v)
        layout_parent.addWidget(ligne)
        return lbl_v


#  Lancement

if __name__ == '__main__':
    app = QApplication(sys.argv)
    fenetre = FenetrePrincipale()
    fenetre.show()
    sys.exit(app.exec())