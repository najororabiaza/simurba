import random


#  Les paramètres λ (lambda) et μ (mu) pour chaque état du trafic
#
#  λ = taux d'arrivée des véhicules (combien arrivent par tick)
#  μ = taux de service du feu (combien passent par tick) — fixe à 5
#
#  Ces valeurs viennent directement du cours (chapitre 4)
#  et sont liées aux états Markov du module markov.py
#
#  Rappel de la condition de stabilité du cours : ρ = λ/μ < 1
#    fluide  : ρ = 2/5 = 0.40  → système stable, peu d'attente
#    ralenti : ρ = 3/5 = 0.60  → attente modérée
#    bouchon : ρ = 4/5 = 0.80  → attente élevée, proche saturation

PARAMETRES_PAR_ETAT = {
    'fluide':  { 'lambda': 2, 'mu': 5 },
    'ralenti': { 'lambda': 3, 'mu': 5 },
    'bouchon': { 'lambda': 4, 'mu': 5 },
}


#  Calculer les métriques M/M/1 théoriques pour une intersection
#
#  Ces formules viennent du chapitre 4 du cours :
#    ρ  = λ / μ
#    L  = λ / (μ - λ)
#    W  = 1 / (μ - λ)
#    Lq = λ² / μ(μ - λ)
#    Wq = λ / μ(μ - λ)
#
#  Paramètre :
#    etat = l'état actuel de la route ('fluide', 'ralenti', 'bouchon')
#
#  Retourne :
#    un dictionnaire avec toutes les métriques calculées

def calculer_metriques(etat):

    # On récupère λ et μ selon l'état de la route
    params = PARAMETRES_PAR_ETAT[etat]
    lam = params['lambda']   # taux d'arrivée
    mu  = params['mu']       # taux de service

    # Taux d'utilisation — doit être < 1 pour que le système soit stable
    # Formule du cours : ρ = λ / μ
    rho = lam / mu

    # Nombre moyen de véhicules dans le système (en attente + en service)
    # Formule du cours : L = λ / (μ - λ)
    L = lam / (mu - lam)

    # Temps moyen passé dans le système (attente + service)
    # Formule du cours : W = 1 / (μ - λ)
    W = 1 / (mu - lam)

    # Nombre moyen de véhicules EN ATTENTE (seulement dans la file)
    # Formule du cours : Lq = λ² / μ(μ - λ)
    Lq = (lam ** 2) / (mu * (mu - lam))

    # Temps moyen d'attente dans la file (sans le temps de service)
    # Formule du cours : Wq = λ / μ(μ - λ)
    Wq = lam / (mu * (mu - lam))

    # On retourne toutes les métriques dans un dictionnaire
    return {
        'lambda': lam,           # taux d'arrivée
        'mu':     mu,            # taux de service
        'rho':    round(rho, 3), # taux d'utilisation
        'L':      round(L,   3), # nb moyen dans le système
        'W':      round(W,   3), # temps moyen dans le système
        'Lq':     round(Lq,  3), # nb moyen en attente
        'Wq':     round(Wq,  3), # temps moyen d'attente
    }


#  Simuler l'évolution de la file d'attente d'UNE intersection
#
#  C'est la simulation concrète du cours (chapitre 4, page 26) :
#    arrivals = poisson(arrival_rate)
#    services = poisson(service_rate)
#    queue    = max(0, queue + arrivals - services)
#
#  Paramètres :
#    queue_actuelle = nombre de véhicules actuellement en attente
#    etat           = état actuel de la route ('fluide', etc.)
#
#  Retourne :
#    le nouveau nombre de véhicules en attente après ce tick

def simuler_tick_file(queue_actuelle, etat):

    # On récupère λ et μ pour cet état
    params = PARAMETRES_PAR_ETAT[etat]
    lam = params['lambda']
    mu  = params['mu']

    # On tire aléatoirement le nombre de véhicules qui arrivent
    # randint(0, lam*2) simule une distribution centrée sur λ
    # (simplifié par rapport à Poisson pour rester lisible)
    arrivees = random.randint(0, lam * 2)

    # On tire aléatoirement le nombre de véhicules qui passent le feu
    services = random.randint(0, mu * 2)

    # La file ne peut pas être négative — formule exacte du cours
    nouvelle_queue = max(0, queue_actuelle + arrivees - services)

    return nouvelle_queue


#  Faire évoluer les files de TOUTES les intersections d'un tick
#
#  Paramètres :
#    files_intersections = dictionnaire { id_noeud: nb_vehicules_en_attente }
#    etats_routes        = dictionnaire { id_route: etat } (vient de markov.py)
#
#  Retourne :
#    un nouveau dictionnaire avec les files mises à jour

def tick_files(files_intersections, etats_routes):

    # On crée un dictionnaire vide pour les nouvelles files
    nouvelles_files = {}

    # On parcourt chaque intersection (nœud du réseau)
    for id_noeud, queue_actuelle in files_intersections.items():

        # On cherche l'état de la route associée à ce nœud
        # Par convention : nœud i est influencé par la route i % 9
        etat_noeud = 'fluide'   # valeur par défaut

        for id_route, etat in etats_routes.items():
            if id_route % 9 == id_noeud:
                etat_noeud = etat
                break   # on s'arrête dès qu'on trouve une route

        # On simule un tick pour cette intersection
        nouvelles_files[id_noeud] = simuler_tick_file(queue_actuelle, etat_noeud)

    return nouvelles_files


#  Créer les files initiales — toutes vides au départ
#
#  Paramètre :
#    nombre_noeuds = le nombre d'intersections (9 dans notre grille 3x3)
#
#  Retourne :
#    un dictionnaire { 0: 0, 1: 0, ..., 8: 0 }

def files_initiales(nombre_noeuds):

    # On initialise chaque intersection avec 0 véhicule en attente
    files = {}

    for i in range(nombre_noeuds):
        files[i] = 0

    return files


#  Trouver l'intersection la plus saturée
#
#  Utile pour le dashboard : "Intersection 4 — 7 véhicules en attente"
#
#  Paramètre :
#    files_intersections = dictionnaire { id_noeud: nb_vehicules }
#
#  Retourne :
#    un dictionnaire { 'id': N, 'queue': N }

def intersection_max(files_intersections):

    # On cherche l'intersection avec le plus de véhicules en attente
    id_max    = 0
    queue_max = 0

    for id_noeud, queue in files_intersections.items():
        if queue > queue_max:
            queue_max = queue
            id_max    = id_noeud

    return {
        'id':    id_max,      # numéro de l'intersection la plus chargée
        'queue': queue_max,   # nombre de véhicules en attente
    }


#  Calculer le temps d'attente moyen sur tout le réseau
#
#  On moyenne les Wq de toutes les intersections
#  Wq vient des formules M/M/1 du cours (chapitre 4)
#
#  Paramètres :
#    files_intersections = dictionnaire { id_noeud: nb_vehicules }
#    etats_routes        = dictionnaire { id_route: etat }
#
#  Retourne :
#    le temps d'attente moyen en secondes (float)

def temps_attente_moyen(files_intersections, etats_routes):

    # On accumule les Wq de chaque intersection
    total_wq = 0
    nombre   = len(files_intersections)

    # Si pas d'intersections, on retourne 0 pour éviter une division par zéro
    if nombre == 0:
        return 0

    # Pour chaque intersection, on calcule son Wq selon son état
    for id_noeud in files_intersections:

        # On cherche l'état de ce nœud
        etat_noeud = 'fluide'

        for id_route, etat in etats_routes.items():
            if id_route % 9 == id_noeud:
                etat_noeud = etat
                break

        # On récupère le Wq théorique pour cet état
        metriques = calculer_metriques(etat_noeud)
        total_wq += metriques['Wq']

    # On retourne la moyenne
    return round(total_wq / nombre, 3)