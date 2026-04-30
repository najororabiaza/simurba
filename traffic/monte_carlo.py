import random

# --- Scénarios de trafic (Monte Carlo) -----------------------------------------
# Chaque scénario définit les probabilités d'état au démarrage du réseau.
# On les utilise pour générer aléatoirement l'état initial de chaque route.
# C'est le principe du cours (chapitre 5) : on tire au sort selon des
# probabilités connues.

SCENARIOS = {
    'normal': {
        'nom':         'Normal',
        'description': 'Trafic ordinaire en journée',
        # Probabilités : fluide 70%, ralenti 20%, bouchon 10%
        'probabilites': [0.70, 0.20, 0.10],
    },
    'heure_de_pointe': {
        'nom':         'Heure de pointe',
        'description': 'Trafic chargé matin ou soir',
        'probabilites': [0.20, 0.40, 0.40],
    },
    'nuit': {
        'nom':         'Nuit',
        'description': 'Trafic très faible la nuit',
        'probabilites': [0.90, 0.08, 0.02],
    },
    'accident': {
        'nom':         'Accident',
        'description': 'Un accident perturbe le réseau',
        'probabilites': [0.15, 0.30, 0.55],
    },
}

# Liste des états dans le même ordre que les probabilités ci-dessus
ETATS = ['fluide', 'ralenti', 'bouchon']


# --- Fonctions ----------------------------------------------------------------

def tirer_etat(scenario):
    """
    Tire un état aléatoire selon les probabilités du scénario.
    (Monte Carlo élémentaire)

    Paramètre :
        scenario : str (clé dans SCENARIOS)

    Retourne :
        str : 'fluide', 'ralenti' ou 'bouchon'
    """
    probabilites = SCENARIOS[scenario]['probabilites']
    resultat = random.choices(ETATS, weights=probabilites, k=1)
    return resultat[0]


def generer_etats_initiaux(nombre_routes, scenario='normal'):
    """
    Génère l'état initial de toutes les routes en tirant au sort
    pour chaque route indépendamment selon le scénario choisi.

    Paramètres :
        nombre_routes : int (12 ici)
        scenario      : str

    Retourne :
        dict { id_route (int) : etat (str) }
    """
    if scenario not in SCENARIOS:
        scenario = 'normal'

    etats = {}
    for i in range(nombre_routes):
        etats[i] = tirer_etat(scenario)
    return etats


def simuler_scenarios(nombre_simulations, nombre_routes, scenario='normal'):
    """
    Répète la génération aléatoire du réseau un grand nombre de fois
    pour observer si les probabilités empiriques se rapprochent
    des probabilités théoriques (principe de convergence Monte Carlo).

    Retourne aussi l'erreur max entre observé et théorique.
    """
    compteurs = {'fluide': 0, 'ralenti': 0, 'bouchon': 0}

    for _ in range(nombre_simulations):
        etats = generer_etats_initiaux(nombre_routes, scenario)
        for etat in etats.values():
            compteurs[etat] += 1

    total = nombre_simulations * nombre_routes

    prob_obs = {}
    for i, etat in enumerate(ETATS):
        prob_obs[etat] = round(compteurs[etat] / total, 3)

    prob_theo = SCENARIOS[scenario]['probabilites']
    erreur_max = 0.0
    for i, etat in enumerate(ETATS):
        ecart = abs(prob_obs[etat] - prob_theo[i])
        if ecart > erreur_max:
            erreur_max = ecart

    return {
        'scenario': scenario,
        'nombre_simulations': nombre_simulations,
        'compteurs': compteurs,
        'probabilites_observees': prob_obs,
        'probabilites_theoriques': prob_theo,
        'erreur_max': round(erreur_max, 4),
    }


def estimer_risque_bouchon(nombre_simulations, nombre_routes, scenario='normal'):
    """
    Estime la probabilité qu'au moins une route soit en bouchon
    sur l'ensemble du réseau, en répétant plusieurs fois la génération.

    Retourne une probabilité entre 0 et 1.
    """
    compteur = 0
    for _ in range(nombre_simulations):
        etats = generer_etats_initiaux(nombre_routes, scenario)
        if 'bouchon' in etats.values():
            compteur += 1
    return round(compteur / nombre_simulations, 3)


def info_scenario(scenario):
    """Retourne le dictionnaire d'informations d'un scénario, ou None."""
    return SCENARIOS.get(scenario, None)


def lister_scenarios():
    """Retourne la liste des clés de scénarios disponibles."""
    return list(SCENARIOS.keys())