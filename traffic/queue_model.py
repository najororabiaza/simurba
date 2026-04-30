import numpy as np   # uniquement pour np.random.poisson (loi de Poisson du cours)


# --- Paramètres λ et μ par état -----------------------------------------------
# Les trois états du trafic ont des taux d'arrivée différents.
# Le taux de service µ est fixe (5 véhicules par tick).
# Ces valeurs respectent la condition de stabilité ρ = λ/µ < 1 (cours chap. 4).

PARAMETRES_PAR_ETAT = {
    'fluide':  { 'lambda': 2, 'mu': 5 },   # ρ = 0.40 → système stable
    'ralenti': { 'lambda': 3, 'mu': 5 },   # ρ = 0.60 → attente modérée
    'bouchon': { 'lambda': 4, 'mu': 5 },   # ρ = 0.80 → proche saturation
}


# --- Calcul des métriques M/M/1 théoriques ------------------------------------

def calculer_metriques(etat):
    """
    Calcule les indicateurs de performance d'une file M/M/1
    en utilisant les formules exactes du cours (chapitre 4).

    Retourne un dictionnaire contenant λ, µ, ρ, L, W, Lq, Wq.
    """
    params = PARAMETRES_PAR_ETAT[etat]
    lam = params['lambda']
    mu  = params['mu']

    # Taux d'occupation (doit être < 1)
    rho = lam / mu

    # Nombre moyen de véhicules dans le système (file + service)
    L = lam / (mu - lam)

    # Temps moyen passé dans le système
    W = 1 / (mu - lam)

    # Nombre moyen de véhicules en attente (dans la file seulement)
    Lq = (lam ** 2) / (mu * (mu - lam))

    # Temps moyen d'attente dans la file
    Wq = lam / (mu * (mu - lam))

    return {
        'lambda': lam,
        'mu': mu,
        'rho': round(rho, 3),
        'L': round(L, 3),
        'W': round(W, 3),
        'Lq': round(Lq, 3),
        'Wq': round(Wq, 3),
    }


# --- Simulation concrète d'un pas de temps ------------------------------------

def simuler_tick_file(queue_actuelle, etat):
    """
    Fait évoluer la file d'attente d'une intersection pendant un tick.
    Les arrivées et les services sont tirés selon une loi de Poisson,
    comme dans la modélisation M/M/1 du cours.

    Paramètres :
        queue_actuelle : int (nombre de véhicules actuellement en attente)
        etat           : str (état de la route associée)

    Retourne :
        int : nouvelle longueur de la file (ne peut pas être négative)
    """
    params = PARAMETRES_PAR_ETAT[etat]
    lam = params['lambda']
    mu  = params['mu']

    # Nombre de véhicules qui arrivent pendant ce tick (loi de Poisson)
    arrivees = np.random.poisson(lam)

    # Nombre de véhicules qui peuvent passer le feu (loi de Poisson)
    services = np.random.poisson(mu)

    # Nouvelle file = ancienne file + arrivées - services, avec un minimum de 0
    nouvelle_queue = max(0, queue_actuelle + arrivees - services)

    return nouvelle_queue


# --- Gestion de toutes les intersections --------------------------------------

def tick_files(files_intersections, etats_routes):
    """
    Applique un tick à toutes les intersections du réseau.

    Paramètres :
        files_intersections : dict { id_noeud (int) : nb_vehicules (int) }
        etats_routes        : dict { id_route (int) : etat (str) }

    Retourne :
        dict avec les nouvelles files.
    """
    nouvelles_files = {}

    for id_noeud, queue in files_intersections.items():
        # Chaque intersection est associée à une route (id_noeud % 9)
        etat_noeud = 'fluide'
        for id_route, etat in etats_routes.items():
            if id_route % 9 == id_noeud:
                etat_noeud = etat
                break

        nouvelles_files[id_noeud] = simuler_tick_file(queue, etat_noeud)

    return nouvelles_files


def files_initiales(nombre_noeuds):
    """
    Crée un dictionnaire représentant des files vides (toutes à 0).

    Paramètre :
        nombre_noeuds : int (9 dans notre grille 3x3)

    Retourne :
        dict { 0:0, 1:0, ..., 8:0 }
    """
    return {i: 0 for i in range(nombre_noeuds)}


def intersection_max(files_intersections):
    """
    Identifie l'intersection ayant la plus longue file d'attente.

    Retourne :
        dict { 'id': int, 'queue': int }
    """
    id_max = 0
    queue_max = 0
    for id_noeud, queue in files_intersections.items():
        if queue > queue_max:
            queue_max = queue
            id_max = id_noeud
    return {'id': id_max, 'queue': queue_max}


def temps_attente_moyen(files_intersections, etats_routes):
    """
    Calcule la moyenne des temps d'attente théoriques Wq
    sur toutes les intersections du réseau, pour le tableau de bord.

    Retourne :
        float (moyenne des Wq)
    """
    if not files_intersections:
        return 0.0

    total_wq = 0.0
    for id_noeud in files_intersections:
        # Retrouve l'état de la route qui gouverne ce nœud
        etat_noeud = 'fluide'
        for id_route, etat in etats_routes.items():
            if id_route % 9 == id_noeud:
                etat_noeud = etat
                break
        total_wq += calculer_metriques(etat_noeud)['Wq']

    return round(total_wq / len(files_intersections), 3)