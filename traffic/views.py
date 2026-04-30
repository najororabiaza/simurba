import json

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from . import markov
from . import queue_model
from . import monte_carlo
from . import optimizer


# --- État global du réseau (mémoire côté serveur) ---------------------------
# Ces variables sont partagées entre tous les appels API.
# Elles vivent tant que le serveur Django tourne.

etat_reseau         = None      # dict { id_route: etat }         (Markov)
files_intersections = None      # dict { id_noeud: nb_vehicules } (files d'attente)
scenario_actuel     = 'normal'  # scénario Monte Carlo en cours


# --- Page principale ----------------------------------------------------------

def index(request):
    """Affiche la page HTML de la simulation."""
    return render(request, 'traffic/base.html')


# --- API tick (appelée toutes les 2 secondes par le JS) -----------------------

@csrf_exempt
def api_tick(request):
    """
    Fait avancer la simulation d'un pas de temps :
      1. Markov : nouvel état de chaque route (en fonction du scénario)
      2. Files d'attente M/M/1 : mise à jour des files
      3. Optimisation : calcul des meilleurs temps de feux
    Retourne tout en JSON pour l'IHM.
    """
    global etat_reseau, files_intersections

    if request.method != 'POST':
        return JsonResponse({'erreur': 'Méthode non autorisée'}, status=405)

    try:
        donnees = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'erreur': 'JSON invalide'}, status=400)

    # Récupération des états envoyés par le client (pour initialisation éventuelle)
    etats_recus = donnees.get('etats', {})
    etats_recus = {int(cle): valeur for cle, valeur in etats_recus.items()}

    # Initialisation au tout premier appel
    if etat_reseau is None:
        etat_reseau = etats_recus

    if files_intersections is None:
        files_intersections = queue_model.files_initiales(9)  # grille 3x3

    # 1. Évolution Markov avec le scénario actif
    etat_reseau = markov.tick(etat_reseau, scenario=scenario_actuel)

    # 2. Mise à jour des files d'attente
    files_intersections = queue_model.tick_files(files_intersections, etat_reseau)

    # 3. Optimisation des feux
    resultat_optim = optimizer.optimiser_feux(etat_reseau)

    # Indicateurs pour le dashboard
    compteurs = markov.compter_etats(etat_reseau)
    inter_max = queue_model.intersection_max(files_intersections)
    wq_moyen  = queue_model.temps_attente_moyen(files_intersections, etat_reseau)

    return JsonResponse({
        'etats':        {str(k): v for k, v in etat_reseau.items()},
        'compteurs':    compteurs,
        'files':        {str(k): v for k, v in files_intersections.items()},
        'inter_max':    inter_max,
        'wq_moyen':     wq_moyen,
        'optimisation': resultat_optim,
    })


# --- API scénario (changement de scénario Monte Carlo) -----------------------

@csrf_exempt
def api_scenario(request):
    """
    Change le scénario actif.
    Génère de nouveaux états initiaux par Monte Carlo,
    remet les files à zéro, et estime le risque de bouchon.
    """
    global etat_reseau, files_intersections, scenario_actuel

    if request.method != 'POST':
        return JsonResponse({'erreur': 'Méthode non autorisée'}, status=405)

    try:
        donnees = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'erreur': 'JSON invalide'}, status=400)

    scenario = donnees.get('scenario', 'normal')

    if scenario not in monte_carlo.lister_scenarios():
        return JsonResponse({'erreur': 'Scénario inconnu'}, status=400)

    # Mise à jour du scénario actif
    scenario_actuel = scenario

    # Génération Monte Carlo des états du réseau
    etat_reseau = monte_carlo.generer_etats_initiaux(12, scenario)

    # Remise à zéro des files d'attente
    files_intersections = queue_model.files_initiales(9)

    # Estimation du risque de bouchon (500 simulations)
    risque = monte_carlo.estimer_risque_bouchon(500, 12, scenario)

    return JsonResponse({
        'etats':          {str(k): v for k, v in etat_reseau.items()},
        'scenario':       scenario,
        'info_scenario':  monte_carlo.info_scenario(scenario),
        'risque_bouchon': risque,
        'compteurs':      markov.compter_etats(etat_reseau),
    })


# --- API stats (métriques M/M/1 détaillées) -----------------------------------

def api_stats(request):
    """
    Retourne les métriques M/M/1 pour chaque route et la moyenne Wq.
    (Appelée en GET)
    """
    if request.method != 'GET':
        return JsonResponse({'erreur': 'Méthode non autorisée'}, status=405)

    if etat_reseau is None:
        return JsonResponse({'erreur': 'Simulation non démarrée'}, status=400)

    metriques = {}
    for id_route, etat in etat_reseau.items():
        metriques[str(id_route)] = queue_model.calculer_metriques(etat)

    return JsonResponse({
        'metriques_par_route': metriques,
        'wq_moyen': queue_model.temps_attente_moyen(
            files_intersections or {}, etat_reseau
        ),
        'scenario_actuel': scenario_actuel,
        'scenarios_disponibles': monte_carlo.lister_scenarios(),
    })