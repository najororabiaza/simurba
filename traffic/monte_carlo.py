import random


#  Les scénarios de trafic disponibles
#
#  Chaque scénario correspond à une situation réelle de la ville.
#  Il définit les probabilités initiales de chaque état pour les routes.
#
#  Ces probabilités sont utilisées pour générer aléatoirement
#  l'état de départ de chaque route — c'est le principe Monte Carlo :
#  on tire au sort selon des probabilités connues.

SCENARIOS = {

    'normal': {
        'nom':         'Normal',
        'description': 'Trafic ordinaire en journée',
        # Probabilités d'état au démarrage :
        # 70% fluide, 20% ralenti, 10% bouchon
        'probabilites': [0.70, 0.20, 0.10],
    },

    'heure_de_pointe': {
        'nom':         'Heure de pointe',
        'description': 'Trafic chargé matin ou soir',
        # Beaucoup plus de bouchons et ralentissements
        'probabilites': [0.20, 0.40, 0.40],
    },

    'nuit': {
        'nom':         'Nuit',
        'description': 'Trafic très faible la nuit',
        # Presque tout est fluide
        'probabilites': [0.90, 0.08, 0.02],
    },

    'accident': {
        'nom':         'Accident',
        'description': 'Un accident perturbe le réseau',
        # Beaucoup de bouchons
        'probabilites': [0.15, 0.30, 0.55],
    },

}

#  Liste ordonnée des états — doit correspondre aux probabilites ci-dessus
#  probabilites[0] = fluide, probabilites[1] = ralenti, probabilites[2] = bouchon
ETATS = ['fluide', 'ralenti', 'bouchon']


#  Générer un état aléatoire selon les probabilités d'un scénario
#
#  C'est le cœur de Monte Carlo : on tire au sort un résultat
#  en respectant les probabilités définies dans le scénario.
#
#  Paramètre :
#    scenario = la clé du scénario ('normal', 'heure_de_pointe', etc.)
#
#  Retourne :
#    un état tiré au sort ('fluide', 'ralenti' ou 'bouchon')

def tirer_etat(scenario):

    # On récupère les probabilités du scénario choisi
    probabilites = SCENARIOS[scenario]['probabilites']

    # random.choices() fait un tirage pondéré — même principe que dans markov.py
    # k=1 = on veut un seul résultat
    resultat = random.choices(ETATS, weights=probabilites, k=1)

    # resultat est une liste comme ['fluide'], on prend le premier élément
    return resultat[0]


#  Générer les états initiaux de TOUTES les routes selon un scénario
#
#  C'est ici qu'on applique Monte Carlo à l'ensemble du réseau :
#  chaque route reçoit un état tiré indépendamment selon le scénario.
#
#  Paramètres :
#    nombre_routes = le nombre de routes dans le réseau (12 ici)
#    scenario      = la clé du scénario à utiliser
#
#  Retourne :
#    un dictionnaire { 0: 'fluide', 1: 'bouchon', ... }

def generer_etats_initiaux(nombre_routes, scenario='normal'):

    # On vérifie que le scénario existe
    if scenario not in SCENARIOS:
        # Si le scénario n'existe pas, on utilise 'normal' par défaut
        scenario = 'normal'

    # On crée un dictionnaire vide pour stocker les états générés
    etats = {}

    # Pour chaque route, on tire un état au sort selon le scénario
    for i in range(nombre_routes):
        etats[i] = tirer_etat(scenario)

    return etats


#  Simuler plusieurs scénarios et compter les états obtenus
#
#  C'est la simulation Monte Carlo classique du cours (chapitre 5) :
#  on répète le tirage N fois et on regarde la distribution obtenue.
#
#  Ici on simule le réseau N fois et on compte combien de fois
#  chaque état apparaît — cela donne les probabilités empiriques.
#
#  Paramètres :
#    nombre_simulations = combien de fois on répète le tirage (ex: 1000)
#    nombre_routes      = nombre de routes dans le réseau (12 ici)
#    scenario           = le scénario à simuler
#
#  Retourne :
#    un dictionnaire avec les probabilités observées et les compteurs

def simuler_scenarios(nombre_simulations, nombre_routes, scenario='normal'):

    # On initialise les compteurs à zéro
    compteurs = {
        'fluide':  0,
        'ralenti': 0,
        'bouchon': 0,
    }

    # On répète le tirage nombre_simulations fois
    for _ in range(nombre_simulations):

        # On génère un réseau complet pour cette simulation
        etats = generer_etats_initiaux(nombre_routes, scenario)

        # On compte les états obtenus dans cette simulation
        for etat in etats.values():
            compteurs[etat] += 1

    # Nombre total de tirages individuels
    total = nombre_simulations * nombre_routes

    # On calcule les probabilités empiriques observées
    # (doit se rapprocher des probabilités théoriques du scénario)
    probabilites_observees = {
        'fluide':  round(compteurs['fluide']  / total, 3),
        'ralenti': round(compteurs['ralenti'] / total, 3),
        'bouchon': round(compteurs['bouchon'] / total, 3),
    }

    # On retourne les compteurs et les probabilités
    return {
        'scenario':                scenario,
        'nombre_simulations':      nombre_simulations,
        'compteurs':               compteurs,
        'probabilites_observees':  probabilites_observees,
        'probabilites_theoriques': SCENARIOS[scenario]['probabilites'],
    }


#  Estimer le risque de bouchon sur le réseau
#
#  On simule N fois le réseau et on compte le pourcentage de fois
#  où au moins une route est en bouchon — c'est une estimation Monte Carlo.
#
#  C'est directement inspiré de l'exemple du cours (chapitre 5) :
#  on tire des points aléatoires et on compte les succès.
#
#  Paramètres :
#    nombre_simulations = nombre de répétitions (ex: 500)
#    nombre_routes      = nombre de routes (12 ici)
#    scenario           = le scénario à tester
#
#  Retourne :
#    la probabilité estimée qu'au moins une route soit en bouchon (float)

def estimer_risque_bouchon(nombre_simulations, nombre_routes, scenario='normal'):

    # Compteur de simulations avec au moins un bouchon
    simulations_avec_bouchon = 0

    # On répète la simulation N fois
    for _ in range(nombre_simulations):

        # On génère un réseau aléatoire
        etats = generer_etats_initiaux(nombre_routes, scenario)

        # On vérifie si au moins une route est en bouchon
        if 'bouchon' in etats.values():
            simulations_avec_bouchon += 1

    # La probabilité estimée = succès / total (formule Monte Carlo du cours)
    probabilite = simulations_avec_bouchon / nombre_simulations

    return round(probabilite, 3)


#  Obtenir les informations d'un scénario
#
#  Paramètre :
#    scenario = la clé du scénario
#
#  Retourne :
#    un dictionnaire avec le nom, la description et les probabilités

def info_scenario(scenario):

    # Si le scénario n'existe pas, on retourne None
    if scenario not in SCENARIOS:
        return None

    return SCENARIOS[scenario]


#  Lister tous les scénarios disponibles
#
#  Retourne :
#    une liste des clés de scénarios disponibles

def lister_scenarios():
    return list(SCENARIOS.keys())