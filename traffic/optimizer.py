from . import queue_model


#  Les durées de feux possibles qu'on peut tester (en secondes)
#
#  L'optimiseur va tester chaque combinaison de ces durées
#  et garder celle qui minimise le temps d'attente global.
#
#  Ces valeurs sont réalistes — dans une vraie ville, un feu
#  reste entre 15 et 60 secondes selon le trafic.

DUREES_POSSIBLES = [15, 20, 25, 30, 35, 40, 45, 50, 55, 60]


#  Durées par défaut au démarrage de la simulation

DUREE_ROUGE_DEFAUT = 30   # secondes
DUREE_VERT_DEFAUT  = 30   # secondes


#  Calculer le temps d'attente total pour une configuration de feux donnée
#
#  C'est la fonction objectif qu'on cherche à minimiser.
#  Plus le temps d'attente total est bas, meilleure est la configuration.
#
#  Paramètres :
#    duree_rouge   = durée du feu rouge en secondes
#    duree_vert    = durée du feu vert en secondes
#    etats_routes  = dictionnaire { id_route: etat } (vient de markov.py)
#
#  Retourne :
#    le score total (float) — plus c'est bas, mieux c'est

def calculer_score(duree_rouge, duree_vert, etats_routes):

    # Le score total est la somme des temps d'attente de toutes les routes
    score_total = 0

    # On parcourt chaque route et son état actuel
    for id_route, etat in etats_routes.items():

        # On récupère les métriques M/M/1 pour cet état
        metriques = queue_model.calculer_metriques(etat)

        # Wq = temps moyen d'attente théorique pour cet état
        wq = metriques['Wq']

        # On pénalise selon la durée du rouge :
        # plus le rouge est long, plus les véhicules attendent
        # On multiplie Wq par le ratio rouge/(rouge+vert)
        ratio_rouge = duree_rouge / (duree_rouge + duree_vert)

        # Le score de cette route = Wq × pénalité du rouge
        score_route = wq * (1 + ratio_rouge)

        # On ajoute au score total
        score_total += score_route

    return round(score_total, 4)


#  Trouver la meilleure durée de feux par recherche exhaustive
#
#  Principe : on teste TOUTES les combinaisons possibles de
#  (duree_rouge, duree_vert) et on garde celle qui donne
#  le score le plus bas.
#
#  C'est une optimisation par force brute — simple et efficace
#  pour un petit nombre de valeurs comme ici.
#
#  Paramètre :
#    etats_routes = dictionnaire { id_route: etat }
#
#  Retourne :
#    un dictionnaire avec la meilleure configuration trouvée

def optimiser_feux(etats_routes):

    # On initialise avec des valeurs impossibles pour forcer la mise à jour
    meilleur_score      = float('inf')   # infini — tout sera mieux que ça
    meilleure_rouge     = DUREE_ROUGE_DEFAUT
    meilleure_vert      = DUREE_VERT_DEFAUT

    # On teste toutes les combinaisons possibles de durées
    for duree_rouge in DUREES_POSSIBLES:
        for duree_vert in DUREES_POSSIBLES:

            # On calcule le score pour cette combinaison
            score = calculer_score(duree_rouge, duree_vert, etats_routes)

            # Si ce score est meilleur (plus bas), on garde cette configuration
            if score < meilleur_score:
                meilleur_score  = score
                meilleure_rouge = duree_rouge
                meilleure_vert  = duree_vert

    # On calcule aussi le score avec les durées par défaut pour comparer
    score_defaut = calculer_score(
        DUREE_ROUGE_DEFAUT,
        DUREE_VERT_DEFAUT,
        etats_routes
    )

    # Le gain = différence entre le score par défaut et le score optimisé
    # Un gain positif signifie qu'on a amélioré le trafic
    gain = round(score_defaut - meilleur_score, 4)

    # On retourne la meilleure configuration et les métriques associées
    return {
        'duree_rouge':    meilleure_rouge,   # durée rouge optimale (secondes)
        'duree_vert':     meilleure_vert,    # durée vert optimale (secondes)
        'score':          meilleur_score,    # score obtenu avec cette config
        'score_defaut':   score_defaut,      # score avec les durées par défaut
        'gain':           gain,              # amélioration obtenue
        'gain_pourcent':  round(gain / score_defaut * 100, 1) if score_defaut > 0 else 0,
    }


#  Appliquer une configuration de feux et calculer son impact
#
#  Permet de tester manuellement une configuration spécifique
#  et de voir son effet sur les métriques du réseau.
#
#  Paramètres :
#    duree_rouge  = durée rouge choisie (secondes)
#    duree_vert   = durée vert choisie (secondes)
#    etats_routes = dictionnaire { id_route: etat }
#
#  Retourne :
#    un dictionnaire avec les métriques de cette configuration

def appliquer_configuration(duree_rouge, duree_vert, etats_routes):

    # On calcule le score de la configuration demandée
    score = calculer_score(duree_rouge, duree_vert, etats_routes)

    # On calcule le score par défaut pour comparaison
    score_defaut = calculer_score(
        DUREE_ROUGE_DEFAUT,
        DUREE_VERT_DEFAUT,
        etats_routes
    )

    # Gain par rapport à la configuration par défaut
    gain = round(score_defaut - score, 4)

    return {
        'duree_rouge':   duree_rouge,
        'duree_vert':    duree_vert,
        'score':         score,
        'score_defaut':  score_defaut,
        'gain':          gain,
        'gain_pourcent': round(gain / score_defaut * 100, 1) if score_defaut > 0 else 0,
    }


#  Calculer le résumé de l'état du réseau pour le dashboard
#
#  Regroupe les infos importantes en un seul appel :
#    - configuration optimale actuelle
#    - nombre de routes par état
#    - score moyen du réseau
#
#  Paramètre :
#    etats_routes = dictionnaire { id_route: etat }
#
#  Retourne :
#    un dictionnaire complet pour alimenter le dashboard

def resume_optimisation(etats_routes):

    # On lance l'optimisation pour trouver la meilleure config
    meilleure_config = optimiser_feux(etats_routes)

    # On compte les routes par état
    compteurs = {'fluide': 0, 'ralenti': 0, 'bouchon': 0}
    for etat in etats_routes.values():
        if etat in compteurs:
            compteurs[etat] += 1

    # On retourne tout en un seul dictionnaire
    return {
        'optimisation': meilleure_config,
        'compteurs':    compteurs,
        'nb_routes':    len(etats_routes),
    }