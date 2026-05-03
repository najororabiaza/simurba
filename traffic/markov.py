import random

# --- États possibles du trafic ------------------------------------------------
# Une route peut être dans l'un de ces trois états à chaque instant.
# Ces états sont ceux vus dans le cours (chapitre 3, chaînes de Markov).

FLUIDE  = 'fluide'      # circulation fluide
RALENTI = 'ralenti'     # circulation ralentie
BOUCHON = 'bouchon'     # bouchon

# Liste des états dans l'ordre utilisé pour les probabilités
ETATS = [FLUIDE, RALENTI, BOUCHON]


# --- Matrices de transition selon le scénario ----------------------------------
# Chaque scénario a sa propre matrice de transition.
# Cela permet d'avoir un comportement plus agressif en heure de pointe,
# plus calme la nuit, etc. (cohérent avec les scénarios Monte Carlo).
#
# Pour chaque matrice :
#   - une ligne correspond à l'état actuel,
#   - une colonne correspond à l'état suivant,
#   - la somme de chaque ligne vaut toujours 1.

MATRICES = {
    # Scénario normal (journée ordinaire)
    'normal': {
        FLUIDE:  [0.85, 0.12, 0.03],   # fluide → fluide 85%, ralenti 12%, bouchon 3%
        RALENTI: [0.20, 0.65, 0.15],   # ralenti → fluide 20%, ralenti 65%, bouchon 15%
        BOUCHON: [0.10, 0.25, 0.65],   # bouchon → fluide 10%, ralenti 25%, bouchon 65%
    },
    # Heure de pointe (transitions plus brutales)
    'heure_de_pointe': {
        FLUIDE:  [0.70, 0.20, 0.10],
        RALENTI: [0.15, 0.60, 0.25],
        BOUCHON: [0.05, 0.20, 0.75],
    },
    # Nuit (trafic très stable, peu de changements)
    'nuit': {
        FLUIDE:  [0.95, 0.04, 0.01],
        RALENTI: [0.40, 0.55, 0.05],
        BOUCHON: [0.30, 0.40, 0.30],
    },
    # Accident (forte probabilité de se dégrader)
    'accident': {
        FLUIDE:  [0.60, 0.25, 0.15],
        RALENTI: [0.10, 0.50, 0.40],
        BOUCHON: [0.05, 0.15, 0.80],
    },
}


# --- Fonctions publiques -------------------------------------------------------

def prochain_etat(etat_actuel, scenario='normal'):
    """
    Calcule le prochain état d'une route selon la chaîne de Markov
    pour le scénario donné.

    Paramètres :
        etat_actuel : str  ( 'fluide' , 'ralenti' , 'bouchon' )
        scenario    : str  (clé dans MATRICES)

    Retourne :
        str : le nouvel état après un pas de temps.
    """
    # Récupère la matrice correspondant au scénario
    matrice = MATRICES.get(scenario, MATRICES['normal'])

    # Ligne de la matrice pour l'état actuel
    probabilites = matrice[etat_actuel]

    # Tirage aléatoire pondéré (comme dans le cours)
    resultat = random.choices(ETATS, weights=probabilites, k=1)

    return resultat[0]


def tick(etats_routes, scenario='normal'):
    """
    Fait avancer toutes les routes d'un cran (un tick de la simulation)
    en utilisant la chaîne de Markov adaptée au scénario.

    Paramètres :
        etats_routes : dict { id_route (int) : etat (str) }
        scenario     : str

    Retourne :
        dict avec les nouveaux états.
    """
    nouveaux_etats = {}

    for id_route, etat_actuel in etats_routes.items():
        nouveaux_etats[id_route] = prochain_etat(etat_actuel, scenario)

    return nouveaux_etats


def etat_initial(nombre_routes):
    """
    Crée l'état de départ du réseau : toutes les routes sont fluides.
    (Utilisé si aucun scénario Monte Carlo n'est chargé.)

    Paramètre :
        nombre_routes : int (12 dans notre grille)

    Retourne :
        dict { 0: 'fluide', 1: 'fluide', ... }
    """
    return {i: FLUIDE for i in range(nombre_routes)}


def compter_etats(etats_routes):
    """
    Compte combien de routes sont dans chaque état.
    Utile pour le tableau de bord.

    Paramètre :
        etats_routes : dict { id_route : etat }

    Retourne :
        dict { 'fluide': nb, 'ralenti': nb, 'bouchon': nb }
    """
    compteurs = {FLUIDE: 0, RALENTI: 0, BOUCHON: 0}

    for etat in etats_routes.values():
        compteurs[etat] += 1

    return compteurs