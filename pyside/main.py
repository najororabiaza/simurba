import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QHBoxLayout, QVBoxLayout, QFrame,
    QLabel, QPushButton, QComboBox
)
from PySide6.QtCore import Qt, QTimer, QPointF
from PySide6.QtGui import QFont, QPainter, QColor, QPen, QBrush


#  Styles CSS Qt

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
STYLE_LABEL_VAL  = 'color: #4ade80; font-size: 12px; font-weight: bold;'
STYLE_TITRE      = 'color: #e94560; font-size: 16px; font-weight: bold;'

STYLE_BTN_START = '''
    QPushButton { background-color: #22c55e; color: white; border: none;
        border-radius: 6px; padding: 8px; font-size: 13px; }
    QPushButton:hover { background-color: #16a34a; }
'''
STYLE_BTN_PAUSE = '''
    QPushButton { background-color: #fb923c; color: white; border: none;
        border-radius: 6px; padding: 8px; font-size: 13px; }
    QPushButton:hover { background-color: #ea7a1e; }
'''
STYLE_BTN_STOP = '''
    QPushButton { background-color: #dc2626; color: white; border: none;
        border-radius: 6px; padding: 8px; font-size: 13px; }
    QPushButton:hover { background-color: #b91c1c; }
'''
STYLE_BTN_RESET = '''
    QPushButton { background-color: #64748b; color: white; border: none;
        border-radius: 6px; padding: 8px; font-size: 13px; }
    QPushButton:hover { background-color: #475569; }
'''

#  Couleurs des états de trafic
COULEURS_ETAT = {
    'fluide':  QColor('#4ade80'),
    'ralenti': QColor('#fb923c'),
    'bouchon': QColor('#ef4444'),
}

#  Positions des 9 nœuds de la grille 3×3
#  Ces coordonnées sont relatives à la taille du widget canvas
NOEUDS_REL = [
    (0.18, 0.18), (0.50, 0.18), (0.82, 0.18),
    (0.18, 0.50), (0.50, 0.50), (0.82, 0.50),
    (0.18, 0.82), (0.50, 0.82), (0.82, 0.82),
]

#  Définition des 12 routes — index de nœud from → to
ROUTES = [
    (0, 1, 'fluide'),  (1, 2, 'ralenti'),
    (3, 4, 'fluide'),  (4, 5, 'bouchon'),
    (6, 7, 'ralenti'), (7, 8, 'fluide'),
    (0, 3, 'fluide'),  (1, 4, 'bouchon'),
    (2, 5, 'fluide'),  (3, 6, 'ralenti'),
    (4, 7, 'fluide'),  (5, 8, 'ralenti'),
]


#  Widget canvas — dessine le réseau routier
#
#  QPainter est l'équivalent Qt du ctx Canvas HTML.
#  paintEvent() est appelé automatiquement par Qt à chaque
#  fois que le widget doit être redessiné.

class CanvasReseau(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        # Fond sombre
        self.setStyleSheet('background-color: #0d1020;')

        # États des routes — mis à jour par les modèles Markov
        # Format : liste de 12 états, un par route
        self.etats_routes = [etat for _, _, etat in ROUTES]

        # Positions des véhicules — un float 0.0→1.0 par route
        self.vehicules = [0.0] * 12

        # Vitesses des véhicules — légèrement différentes pour chacun
        import random
        self.vitesses = [0.003 + random.random() * 0.002 for _ in range(12)]


    def noeuds_px(self):
        """Convertit les positions relatives en pixels selon la taille actuelle."""
        w = self.width()
        h = self.height()
        return [(int(rx * w), int(ry * h)) for rx, ry in NOEUDS_REL]


    def paintEvent(self, event):
        """Qt appelle cette méthode automatiquement pour redessiner le widget."""

        painter = QPainter(self)

        # Active l'antialiasing — les lignes et cercles sont lisses
        painter.setRenderHint(QPainter.Antialiasing)

        noeuds = self.noeuds_px()

        # ── Dessiner les routes ──
        for i, (idx_from, idx_to, _) in enumerate(ROUTES):
            x1, y1 = noeuds[idx_from]
            x2, y2 = noeuds[idx_to]

            etat   = self.etats_routes[i]
            couleur = COULEURS_ETAT.get(etat, QColor('#4ade80'))

            # Ligne épaisse semi-transparente — équivalent ctx.stroke()
            pen = QPen(couleur, 5)
            pen.setCapStyle(Qt.RoundCap)
            painter.setOpacity(0.8)
            painter.setPen(pen)
            painter.drawLine(x1, y1, x2, y2)

        painter.setOpacity(1.0)

        # ── Dessiner les ronds-points aux intersections ──
        for x, y in noeuds:

            # Anneau extérieur gris semi-transparent
            painter.setPen(QPen(QColor('#444444'), 2))
            painter.setBrush(QBrush(QColor(70, 70, 70, 80)))
            painter.drawEllipse(int(x - 20), int(y - 20), 40, 40)

            # Îlot central vert
            painter.setPen(QPen(QColor('#1a5c1a'), 1))
            painter.setBrush(QBrush(QColor(55, 130, 55, 160)))
            painter.drawEllipse(int(x - 9), int(y - 9), 18, 18)

        # ── Dessiner les véhicules ──
        for i, (idx_from, idx_to, _) in enumerate(ROUTES):
            x1, y1 = noeuds[idx_from]
            x2, y2 = noeuds[idx_to]

            # Position du véhicule sur la route (interpolation linéaire)
            t = self.vehicules[i]
            vx = x1 + (x2 - x1) * t
            vy = y1 + (y2 - y1) * t

            # Petit décalage latéral pour simuler une voie
            import math
            dx = x2 - x1
            dy = y2 - y1
            dist = math.sqrt(dx*dx + dy*dy) or 1
            # Vecteur perpendiculaire normalisé × décalage
            px = (-dy / dist) * 10
            py = ( dx / dist) * 10

            vx += px
            vy += py

            # Cercle coloré = véhicule
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor('#ffffff')))
            painter.drawEllipse(int(vx - 5), int(vy - 5), 10, 10)


    def avancer_vehicules(self):
        """Fait avancer tous les véhicules d'un pas — appelé par QTimer."""
        for i in range(12):
            self.vehicules[i] += self.vitesses[i]
            # Quand un véhicule atteint la fin, il repart du début
            if self.vehicules[i] > 1.0:
                self.vehicules[i] = 0.0
        # Demande à Qt de redessiner le widget
        self.update()


def creer_section(titre, contenu):
    """Crée un bloc bleu arrondi avec titre et contenu."""
    section = QFrame()
    section.setStyleSheet(STYLE_SECTION)
    layout = QVBoxLayout(section)
    layout.setContentsMargins(8, 8, 8, 8)
    layout.setSpacing(6)
    label_titre = QLabel(titre.upper())
    label_titre.setStyleSheet('color: #aaaaaa; font-size: 10px; font-weight: bold; letter-spacing: 1px;')
    layout.addWidget(label_titre)
    ligne = QFrame()
    ligne.setFrameShape(QFrame.HLine)
    ligne.setStyleSheet('color: #1a1a2e;')
    layout.addWidget(ligne)
    layout.addWidget(contenu)
    return section


class FenetrePrincipale(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle('Simurba Desktop')
        self.resize(1100, 700)
        self.setMinimumSize(800, 500)
        self.setStyleSheet(STYLE_FENETRE)

        widget_central = QWidget()
        self.setCentralWidget(widget_central)

        layout_principal = QHBoxLayout(widget_central)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.setSpacing(0)

        # ── Canvas réseau routier ──
        self.canvas = CanvasReseau()
        layout_principal.addWidget(self.canvas, stretch=3)

        # ── Séparateur ──
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

        # ── QTimer — anime les véhicules à ~60fps (1000ms / 60 ≈ 16ms) ──
        self.timer_animation = QTimer()
        self.timer_animation.setInterval(16)
        self.timer_animation.timeout.connect(self.canvas.avancer_vehicules)
        self.timer_animation.start()


    def _construire_dashboard(self):

        layout = QVBoxLayout(self.zone_dashboard)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # Titre
        titre = QLabel('🚦 Simurba Desktop')
        titre.setStyleSheet(STYLE_TITRE)
        layout.addWidget(titre)

        # Section 1 : Contrôles
        contenu_ctrl = QWidget()
        lc = QVBoxLayout(contenu_ctrl)
        lc.setContentsMargins(0, 0, 0, 0)
        lc.setSpacing(6)

        ligne_etat = QWidget()
        le = QHBoxLayout(ligne_etat)
        le.setContentsMargins(0, 0, 0, 0)
        lbl_e = QLabel('État :')
        lbl_e.setStyleSheet(STYLE_LABEL_INFO)
        self.label_etat = QLabel('en cours...')
        self.label_etat.setStyleSheet(STYLE_LABEL_VAL)
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

        layout.addWidget(creer_section('Contrôles', contenu_ctrl))

        # Section 2 : Trafic en direct
        contenu_trafic = QWidget()
        lt = QVBoxLayout(contenu_trafic)
        lt.setContentsMargins(0, 0, 0, 0)
        lt.setSpacing(4)
        self.label_fluide  = self._ligne_stat('● Fluide',  '#4ade80', lt)
        self.label_ralenti = self._ligne_stat('● Ralenti', '#fb923c', lt)
        self.label_bouchon = self._ligne_stat('● Bouchon', '#ef4444', lt)
        layout.addWidget(creer_section('Trafic en direct', contenu_trafic))

        # Section 3 : Scénario Monte Carlo
        contenu_sc = QWidget()
        ls = QVBoxLayout(contenu_sc)
        ls.setContentsMargins(0, 0, 0, 0)
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
        ligne_risque = QWidget()
        lr = QHBoxLayout(ligne_risque)
        lr.setContentsMargins(0, 4, 0, 0)
        lbl_r = QLabel('Risque bouchon :')
        lbl_r.setStyleSheet(STYLE_LABEL_INFO)
        self.label_risque = QLabel('—')
        self.label_risque.setStyleSheet('color: #ef4444; font-weight: bold;')
        self.label_risque.setAlignment(Qt.AlignRight)
        lr.addWidget(lbl_r)
        lr.addWidget(self.label_risque)
        ls.addWidget(ligne_risque)
        layout.addWidget(creer_section('Scénario Monte Carlo', contenu_sc))

        # Section 4 : Optimisation des feux
        contenu_opt = QWidget()
        lo = QVBoxLayout(contenu_opt)
        lo.setContentsMargins(0, 0, 0, 0)
        lo.setSpacing(4)
        self.label_rouge = self._ligne_info('Feu rouge optimal', '—', lo)
        self.label_vert  = self._ligne_info('Feu vert optimal',  '—', lo)
        self.label_gain  = self._ligne_info('Gain fluidité',     '—', lo, '#4ade80')
        layout.addWidget(creer_section('Optimisation des feux', contenu_opt))

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