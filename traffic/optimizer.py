from . import queue_model


# --- Plage de recherche pour les durées de feux -------------------------------
# L'optimiseur teste chaque combinaison (rouge, vert) parmi ces valeurs.
# Ces durées sont en secondes, réalistes pour un carrefour urbain.

DUREES_POSSIBLES = [15, 20, 25, 30, 35, 40, 45, 50, 55, 60]

# Valeurs par défaut utilisées au lancement de la simulation
DUREE_ROUGE_DEFAUT = 30
DUREE_VERT_DEFAUT  = 30


# --- Fonction objectif (score à minimiser) ------------------------------------

def calculer_score(duree_rouge, duree_vert, etats_routes):
    """
    Calcule un score reflétant l'attente totale sur le réseau
    pour une configuration de feux donnée.

    Plus le score est bas, meilleure est la configuration.

    Paramètres :
        duree_rouge  : int (secondes)
        duree_vert   : int (secondes)
        etats_routes : dict { id_route : etat }

    Retourne :
        float
    """
    ratio_rouge = duree_rouge / (duree_rouge + duree_vert)
    score_total = 0.0

    for etat in etats_routes.values():
        # Récupère le temps d'attente théorique Wq de l'état
        wq = queue_model.calculer_metriques(etat)['Wq']

        # Plus le feu rouge dure longtemps, plus la pénalité est forte
        score_total += wq * (1.0 + ratio_rouge)

    return round(score_total, 4)


# --- Recherche exhaustive de la meilleure combinaison -------------------------

def optimiser_feux(etats_routes):
    """
    Trouve la meilleure combinaison (rouge, vert) en testant
    toutes les valeurs possibles.

    Retourne un dictionnaire avec les durées optimales et le gain
    par rapport à la configuration par défaut.
    """
    meilleur_score = float('inf')
    meilleure_rouge = DUREE_ROUGE_DEFAUT
    meilleure_vert  = DUREE_VERT_DEFAUT

    for dr in DUREES_POSSIBLES:
        for dv in DUREES_POSSIBLES:
            score = calculer_score(dr, dv, etats_routes)
            if score < meilleur_score:
                meilleur_score = score
                meilleure_rouge = dr
                meilleure_vert  = dv

    # Score des durées par défaut pour comparaison
    score_defaut = calculer_score(DUREE_ROUGE_DEFAUT, DUREE_VERT_DEFAUT, etats_routes)
    gain = round(score_defaut - meilleur_score, 4)
    gain_pct = round(gain / score_defaut * 100, 1) if score_defaut > 0 else 0.0

    return {
        'duree_rouge': meilleure_rouge,
        'duree_vert':  meilleure_vert,
        'score':       meilleur_score,
        'score_defaut': score_defaut,
        'gain':        gain,
        'gain_pourcent': gain_pct,
    }


# --- Fonctions auxiliaires pour le dashboard ----------------------------------

def appliquer_configuration(duree_rouge, duree_vert, etats_routes):
    """
    Évalue une configuration manuelle (sans optimiser).

    Retourne le même format que `optimiser_feux` pour comparaison.
    """
    score = calculer_score(duree_rouge, duree_vert, etats_routes)
    score_defaut = calculer_score(DUREE_ROUGE_DEFAUT, DUREE_VERT_DEFAUT, etats_routes)
    gain = round(score_defaut - score, 4)
    gain_pct = round(gain / score_defaut * 100, 1) if score_defaut > 0 else 0.0
    return {
        'duree_rouge': duree_rouge,
        'duree_vert': duree_vert,
        'score': score,
        'score_defaut': score_defaut,
        'gain': gain,
        'gain_pourcent': gain_pct,
    }


def resume_optimisation(etats_routes):
    """
    Résume l'état du réseau pour le dashboard :
    - configuration optimale des feux
    - comptage des états
    """
    config_opt = optimiser_feux(etats_routes)
    compteurs = {'fluide': 0, 'ralenti': 0, 'bouchon': 0}
    for etat in etats_routes.values():
        if etat in compteurs:
            compteurs[etat] += 1
    return {
        'optimisation': config_opt,
        'compteurs': compteurs,
        'nb_routes': len(etats_routes),
    }