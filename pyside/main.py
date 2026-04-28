import sys
import math
import random

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QHBoxLayout, QVBoxLayout, QFrame,
    QLabel, QPushButton, QComboBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QColor, QPen, QBrush

# On importe les modèles Python directement depuis traffic/
# sys.path.insert permet à Python de trouver le dossier traffic/
# qui est au niveau parent (simurba/)
sys.path.insert(0, '.')
from traffic import markov, queue_model, monte_carlo, optimizer


#  Styles Qt — même palette que Django

STYLE_FENETRE   = 'background-color: #1a1a2e; color: white;'
STYLE_DASHBOARD = 'background-color: #16213e;'
STYLE_SECTION   = '''
    QFrame {
        background-color: #0f3460;
        border-radius: 8px;
        padding: 4px;
    }
'''
STYLE_LABEL_INFO = 'color: #aaaaaa; font-size: 11px;'
STYLE_BTN_START  = '''
    QPushButton { background-color: #22c55e; color: white; border: none;
        border-radius: 6px; padding: 8px; font-size: 13px; }
    QPushButton:hover    { background-color: #16a34a; }
    QPushButton:disabled { background-color: #22c55e; opacity: 0.4; }
'''
STYLE_BTN_PAUSE  = '''
    QPushButton { background-color: #fb923c; color: white; border: none;
        border-radius: 6px; padding: 8px; font-size: 13px; }
    QPushButton:hover { background-color: #ea7a1e; }
'''
STYLE_BTN_RESET  = '''
    QPushButton { background-color: #64748b; color: white; border: none;
        border-radius: 6px; padding: 8px; font-size: 13px; }
    QPushButton:hover { background-color: #475569; }
'''
STYLE_BTN_STOP   = '''
    QPushButton { background-color: #dc2626; color: white; border: none;
        border-radius: 6px; padding: 8px; font-size: 13px; }
    QPushButton:hover { background-color: #b91c1c; }
'''

#  Couleurs Qt des états de trafic
COULEURS_ETAT = {
    'fluide':  QColor('#4ade80'),
    'ralenti': QColor('#fb923c'),
    'bouchon': QColor('#ef4444'),
}

#  Positions relatives des 9 nœuds de la grille 3×3
NOEUDS_REL = [
    (0.18, 0.18), (0.50, 0.18), (0.82, 0.18),
    (0.18, 0.50), (0.50, 0.50), (0.82, 0.50),
    (0.18, 0.82), (0.50, 0.82), (0.82, 0.82),
]

#  Définition des 12 routes : (nœud_départ, nœud_arrivée)
ROUTES_DEF = [
    (0, 1), (1, 2),
    (3, 4), (4, 5),
    (6, 7), (7, 8),
    (0, 3), (1, 4),
    (2, 5), (3, 6),
    (4, 7), (5, 8),
]

#  Clés des scénarios Monte Carlo — correspondent aux clés de monte_carlo.py
SCENARIOS_CLES = ['normal', 'heure_de_pointe', 'nuit', 'accident']


#  Widget canvas — dessine le réseau routier avec QPainter

class CanvasReseau(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet('background-color: #0d1020;')

        # États initiaux des 12 routes — générés par Monte Carlo au démarrage
        self.etats_routes = markov.etat_initial(12)

        # Positions des véhicules sur chaque route (0.0 = départ, 1.0 = arrivée)
        self.vehicules = [random.random() for _ in range(12)]

        # Vitesses légèrement différentes pour chaque véhicule
        self.vitesses = [0.003 + random.random() * 0.002 for _ in range(12)]


    def noeuds_px(self):
        """Convertit les positions relatives en coordonnées pixels."""
        w = self.width()
        h = self.height()
        return [(int(rx * w), int(ry * h)) for rx, ry in NOEUDS_REL]


    def paintEvent(self, event):
        """Redessine tout le canvas — appelé par Qt à chaque update()."""

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        noeuds = self.noeuds_px()

        # ── Dessiner les routes ──
        for i, (idx_from, idx_to) in enumerate(ROUTES_DEF):
            x1, y1 = noeuds[idx_from]
            x2, y2 = noeuds[idx_to]

            # On récupère l'état actuel de cette route
            etat    = self.etats_routes.get(i, 'fluide')
            couleur = COULEURS_ETAT.get(etat, QColor('#4ade80'))

            pen = QPen(couleur, 5)
            pen.setCapStyle(Qt.RoundCap)
            painter.setOpacity(0.8)
            painter.setPen(pen)
            painter.drawLine(x1, y1, x2, y2)

        painter.setOpacity(1.0)

        # ── Dessiner les ronds-points ──
        for x, y in noeuds:
            painter.setPen(QPen(QColor('#444444'), 2))
            painter.setBrush(QBrush(QColor(70, 70, 70, 80)))
            painter.drawEllipse(int(x - 20), int(y - 20), 40, 40)
            painter.setPen(QPen(QColor('#1a5c1a'), 1))
            painter.setBrush(QBrush(QColor(55, 130, 55, 160)))
            painter.drawEllipse(int(x - 9), int(y - 9), 18, 18)

        # ── Dessiner les véhicules ──
        for i, (idx_from, idx_to) in enumerate(ROUTES_DEF):
            x1, y1 = noeuds[idx_from]
            x2, y2 = noeuds[idx_to]

            t  = self.vehicules[i]
            vx = x1 + (x2 - x1) * t
            vy = y1 + (y2 - y1) * t

            # Décalage latéral pour simuler une voie
            dx   = x2 - x1
            dy   = y2 - y1
            dist = math.sqrt(dx*dx + dy*dy) or 1
            vx  += (-dy / dist) * 10
            vy  += ( dx / dist) * 10

            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor('#ffffff')))
            painter.drawEllipse(int(vx - 5), int(vy - 5), 10, 10)


    def avancer_vehicules(self):
        """Avance les véhicules d'un pas — appelé par le timer d'animation."""
        for i in range(12):
            self.vehicules[i] += self.vitesses[i]
            if self.vehicules[i] > 1.0:
                self.vehicules[i] = 0.0
        self.update()


    def mettre_a_jour_etats(self, nouveaux_etats):
        """Reçoit les nouveaux états Markov et redessine les routes."""
        self.etats_routes = nouveaux_etats
        self.update()


def creer_section(titre, contenu):
    """Crée un bloc bleu arrondi avec titre et contenu."""
    section = QFrame()
    section.setStyleSheet(STYLE_SECTION)
    layout = QVBoxLayout(section)
    layout.setContentsMargins(8, 8, 8, 8)
    layout.setSpacing(6)
    lbl = QLabel(titre.upper())
    lbl.setStyleSheet('color: #aaaaaa; font-size: 10px; font-weight: bold; letter-spacing: 1px;')
    layout.addWidget(lbl)
    sep = QFrame()
    sep.setFrameShape(QFrame.HLine)
    sep.setStyleSheet('color: #1a1a2e;')
    layout.addWidget(sep)
    layout.addWidget(contenu)
    return section


class FenetrePrincipale(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle('Simurba Desktop')
        self.resize(1100, 700)
        self.setMinimumSize(800, 500)
        self.setStyleSheet(STYLE_FENETRE)

        # ── État interne de la simulation ──
        # True = simulation en cours, False = en pause ou arrêtée
        self.en_cours = False

        # États Markov des routes — mis à jour par le timer Markov
        self.etats_routes = markov.etat_initial(12)

        widget_central = QWidget()
        self.setCentralWidget(widget_central)

        layout_principal = QHBoxLayout(widget_central)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.setSpacing(0)

        # ── Canvas ──
        self.canvas = CanvasReseau()
        layout_principal.addWidget(self.canvas, stretch=3)

        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setStyleSheet('color: #333333;')
        layout_principal.addWidget(sep)

        # ── Dashboard ──
        self.zone_dashboard = QFrame()
        self.zone_dashboard.setStyleSheet(STYLE_DASHBOARD)
        self.zone_dashboard.setFixedWidth(280)
        layout_principal.addWidget(self.zone_dashboard)

        self._construire_dashboard()
        self._connecter_boutons()

        # ── Timer animation (60fps) — anime les véhicules ──
        self.timer_animation = QTimer()
        self.timer_animation.setInterval(16)
        self.timer_animation.timeout.connect(self.canvas.avancer_vehicules)

        # ── Timer Markov (2s) — fait évoluer les états des routes ──
        self.timer_markov = QTimer()
        self.timer_markov.setInterval(2000)
        self.timer_markov.timeout.connect(self._tick_markov)

        # On démarre la simulation automatiquement
        self._demarrer()


    def _tick_markov(self):
        """
        Appelé toutes les 2 secondes par timer_markov.
        Fait évoluer les états via Markov, met à jour le dashboard.
        """

        # Étape 1 — Markov fait évoluer les états des routes
        self.etats_routes = markov.tick(self.etats_routes)

        # On met à jour les couleurs des routes sur le canvas
        self.canvas.mettre_a_jour_etats(self.etats_routes)

        # Étape 2 — On compte les routes par état pour le dashboard
        compteurs = markov.compter_etats(self.etats_routes)
        self.label_fluide.setText(str(compteurs['fluide']))
        self.label_ralenti.setText(str(compteurs['ralenti']))
        self.label_bouchon.setText(str(compteurs['bouchon']))

        # Étape 3 — L'optimiseur calcule les meilleures durées de feux
        resultat = optimizer.optimiser_feux(self.etats_routes)
        self.label_rouge.setText(str(resultat['duree_rouge']) + ' s')
        self.label_vert.setText(str(resultat['duree_vert']) + ' s')
        self.label_gain.setText('+' + str(resultat['gain_pourcent']) + '%')


    def _demarrer(self):
        """Démarre les deux timers — animation + Markov."""
        self.en_cours = True
        self.timer_animation.start()
        self.timer_markov.start()
        self.label_etat.setText('en cours...')
        self.label_etat.setStyleSheet('color: #4ade80; font-size: 12px; font-weight: bold;')
        self.btn_start.setEnabled(False)
        self.btn_pause.setEnabled(True)
        self.btn_stop.setEnabled(True)


    def _pauser(self):
        """Arrête les deux timers sans remettre à zéro."""
        self.en_cours = False
        self.timer_animation.stop()
        self.timer_markov.stop()
        self.label_etat.setText('en pause')
        self.label_etat.setStyleSheet('color: #fb923c; font-size: 12px; font-weight: bold;')
        self.btn_start.setEnabled(True)
        self.btn_pause.setEnabled(False)


    def _reinitialiser(self):
        """Remet les véhicules à zéro et relance."""
        self.canvas.vehicules = [0.0] * 12
        self.etats_routes = markov.etat_initial(12)
        self.canvas.mettre_a_jour_etats(self.etats_routes)
        if not self.en_cours:
            self._demarrer()


    def _arreter(self):
        """Arrête tout et remet à zéro."""
        self.en_cours = False
        self.timer_animation.stop()
        self.timer_markov.stop()
        self.canvas.vehicules = [0.0] * 12
        self.etats_routes = markov.etat_initial(12)
        self.canvas.mettre_a_jour_etats(self.etats_routes)
        self.label_etat.setText('arrêté')
        self.label_etat.setStyleSheet('color: #ef4444; font-size: 12px; font-weight: bold;')
        self.btn_start.setEnabled(True)
        self.btn_pause.setEnabled(False)
        self.btn_stop.setEnabled(False)
        self.canvas.update()


    def _changer_scenario(self, index):
        """
        Appelé quand l'utilisateur choisit un scénario dans le menu déroulant.
        Monte Carlo génère de nouveaux états selon le scénario choisi.
        """

        # On récupère la clé du scénario selon l'index du menu déroulant
        cle_scenario = SCENARIOS_CLES[index]

        # Monte Carlo génère les nouveaux états
        self.etats_routes = monte_carlo.generer_etats_initiaux(12, cle_scenario)

        # On met à jour le canvas avec les nouveaux états
        self.canvas.mettre_a_jour_etats(self.etats_routes)

        # On estime le risque de bouchon avec 500 simulations
        risque = monte_carlo.estimer_risque_bouchon(500, 12, cle_scenario)
        self.label_risque.setText(str(int(risque * 100)) + '%')


    def _connecter_boutons(self):
        """Connecte chaque bouton à sa fonction."""

        # .clicked.connect() = équivalent de addEventListener('click') en JS
        self.btn_start.clicked.connect(self._demarrer)
        self.btn_pause.clicked.connect(self._pauser)
        self.btn_reset.clicked.connect(self._reinitialiser)
        self.btn_stop.clicked.connect(self._arreter)

        # currentIndexChanged = déclenché quand l'utilisateur choisit un scénario
        self.combo_scenario.currentIndexChanged.connect(self._changer_scenario)


    def _construire_dashboard(self):

        layout = QVBoxLayout(self.zone_dashboard)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # Titre
        titre = QLabel('🚦 Simurba Desktop')
        titre.setStyleSheet('color: #e94560; font-size: 16px; font-weight: bold;')
        layout.addWidget(titre)

        # Section 1 : Contrôles
        c_ctrl = QWidget()
        lc = QVBoxLayout(c_ctrl)
        lc.setContentsMargins(0, 0, 0, 0)
        lc.setSpacing(6)
        ligne_etat = QWidget()
        le = QHBoxLayout(ligne_etat)
        le.setContentsMargins(0, 0, 0, 0)
        lbl_e = QLabel('État :')
        lbl_e.setStyleSheet(STYLE_LABEL_INFO)
        self.label_etat = QLabel('en cours...')
        self.label_etat.setStyleSheet('color: #4ade80; font-size: 12px; font-weight: bold;')
        self.label_etat.setAlignment(Qt.AlignRight)
        le.addWidget(lbl_e)
        le.addWidget(self.label_etat)
        lc.addWidget(ligne_etat)
        self.btn_start = QPushButton('▶  Démarrer')
        self.btn_start.setStyleSheet(STYLE_BTN_START)
        self.btn_pause = QPushButton('⏸  Pauser')
        self.btn_pause.setStyleSheet(STYLE_BTN_PAUSE)
        self.btn_reset = QPushButton('↺  Réinitialiser')
        self.btn_reset.setStyleSheet(STYLE_BTN_RESET)
        self.btn_stop  = QPushButton('⏹  Arrêter')
        self.btn_stop.setStyleSheet(STYLE_BTN_STOP)
        for btn in [self.btn_start, self.btn_pause, self.btn_reset, self.btn_stop]:
            lc.addWidget(btn)
        layout.addWidget(creer_section('Contrôles', c_ctrl))

        # Section 2 : Trafic en direct
        c_trafic = QWidget()
        lt = QVBoxLayout(c_trafic)
        lt.setContentsMargins(0, 0, 0, 0)
        lt.setSpacing(4)
        self.label_fluide  = self._ligne_stat('● Fluide',  '#4ade80', lt)
        self.label_ralenti = self._ligne_stat('● Ralenti', '#fb923c', lt)
        self.label_bouchon = self._ligne_stat('● Bouchon', '#ef4444', lt)
        layout.addWidget(creer_section('Trafic en direct', c_trafic))

        # Section 3 : Scénario Monte Carlo
        c_sc = QWidget()
        ls = QVBoxLayout(c_sc)
        ls.setContentsMargins(0, 0, 0, 0)
        ls.setSpacing(4)
        self.combo_scenario = QComboBox()
        self.combo_scenario.addItems(['Normal', 'Heure de pointe', 'Nuit', 'Accident'])
        self.combo_scenario.setStyleSheet('''
            QComboBox { background-color: #1a1a2e; color: white;
                border: 1px solid #334155; border-radius: 4px;
                padding: 5px; font-size: 12px; }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView { background-color: #1a1a2e; color: white;
                selection-background-color: #e94560; }
        ''')
        ls.addWidget(self.combo_scenario)
        ligne_r = QWidget()
        lr = QHBoxLayout(ligne_r)
        lr.setContentsMargins(0, 4, 0, 0)
        lbl_r = QLabel('Risque bouchon :')
        lbl_r.setStyleSheet(STYLE_LABEL_INFO)
        self.label_risque = QLabel('—')
        self.label_risque.setStyleSheet('color: #ef4444; font-weight: bold; font-size: 12px;')
        self.label_risque.setAlignment(Qt.AlignRight)
        lr.addWidget(lbl_r)
        lr.addWidget(self.label_risque)
        ls.addWidget(ligne_r)
        layout.addWidget(creer_section('Scénario Monte Carlo', c_sc))

        # Section 4 : Optimisation des feux
        c_opt = QWidget()
        lo = QVBoxLayout(c_opt)
        lo.setContentsMargins(0, 0, 0, 0)
        lo.setSpacing(4)
        self.label_rouge = self._ligne_info('Feu rouge optimal', '—', lo)
        self.label_vert  = self._ligne_info('Feu vert optimal',  '—', lo)
        self.label_gain  = self._ligne_info('Gain fluidité',     '—', lo, '#4ade80')
        layout.addWidget(creer_section('Optimisation des feux', c_opt))

        layout.addStretch()


    def _ligne_stat(self, texte, couleur, layout_parent):
        ligne = QWidget()
        ll = QHBoxLayout(ligne)
        ll.setContentsMargins(0, 0, 0, 0)
        lbl_t = QLabel(texte)
        lbl_t.setStyleSheet(f'color: {couleur}; font-size: 12px;')
        lbl_v = QLabel('0')
        lbl_v.setStyleSheet(f'color: {couleur}; font-size: 12px; font-weight: bold;')
        lbl_v.setAlignment(Qt.AlignRight)
        ll.addWidget(lbl_t)
        ll.addWidget(lbl_v)
        layout_parent.addWidget(ligne)
        return lbl_v

    def _ligne_info(self, texte, valeur, layout_parent, val_color='white'):
        ligne = QWidget()
        ll = QHBoxLayout(ligne)
        ll.setContentsMargins(0, 0, 0, 0)
        lbl_t = QLabel(texte)
        lbl_t.setStyleSheet(STYLE_LABEL_INFO)
        lbl_v = QLabel(valeur)
        lbl_v.setStyleSheet(f'color: {val_color}; font-size: 12px; font-weight: bold;')
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