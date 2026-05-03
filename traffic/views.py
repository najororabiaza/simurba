import json

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from . import markov
from . import queue_model
from . import monte_carlo
from . import optimizer
from . import pathfinding


# --- État global du réseau ---------------------------------------------------

etat_reseau         = None
files_intersections = None
scenario_actuel     = 'normal'


# --- Page principale ---------------------------------------------------------

def index(request):
    return render(request, 'traffic/base.html')


# --- API tick ----------------------------------------------------------------

@csrf_exempt
def api_tick(request):
    global etat_reseau, files_intersections

    if request.method != 'POST':
        return JsonResponse({'erreur': 'Méthode non autorisée'}, status=405)
    try:
        donnees = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'erreur': 'JSON invalide'}, status=400)

    etats_recus = donnees.get('etats', {})
    etats_recus = {int(cle): valeur for cle, valeur in etats_recus.items()}

    if etat_reseau is None:
        etat_reseau = etats_recus
    if files_intersections is None:
        files_intersections = queue_model.files_initiales(9)

    etat_reseau         = markov.tick(etat_reseau, scenario=scenario_actuel)
    files_intersections = queue_model.tick_files(files_intersections, etat_reseau)
    resultat_optim      = optimizer.optimiser_feux(etat_reseau)

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


# --- API scénario ------------------------------------------------------------

@csrf_exempt
def api_scenario(request):
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

    scenario_actuel     = scenario
    etat_reseau         = monte_carlo.generer_etats_initiaux(12, scenario)
    files_intersections = queue_model.files_initiales(9)
    risque              = monte_carlo.estimer_risque_bouchon(500, 12, scenario)

    return JsonResponse({
        'etats':          {str(k): v for k, v in etat_reseau.items()},
        'scenario':       scenario,
        'info_scenario':  monte_carlo.info_scenario(scenario),
        'risque_bouchon': risque,
        'compteurs':      markov.compter_etats(etat_reseau),
    })


# --- API stats ---------------------------------------------------------------

def api_stats(request):
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


# --- API Pathfinding — initialisation ----------------------------------------
# Python calcule TOUT le pathfinding (Dijkstra + marche aléatoire guidée).
# JavaScript reçoit les chemins et s'occupe uniquement de l'affichage.

@csrf_exempt
def api_pathfinding_init(request):
    """
    Génère les chemins initiaux pour tous les véhicules.

    Corps POST :
        { "num_vehicles": 12, "etats": {...}, "path_length": 30 }

    Réponse :
        { "paths": [ { "vehicle_id", "origin_node", "current_node", "path": [...] }, ... ] }
    """
    if request.method != 'POST':
        return JsonResponse({'erreur': 'Méthode non autorisée'}, status=405)
    try:
        donnees = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'erreur': 'JSON invalide'}, status=400)

    nb_vehicules    = int(donnees.get('num_vehicles', 12))
    longueur_chemin = int(donnees.get('path_length',  30))
    etats_recus     = {int(k): v for k, v in donnees.get('etats', {}).items()}

    chemins = pathfinding.init_chemins(
        nb_vehicules     = nb_vehicules,
        etats_routes     = etats_recus,
        longueur_chemin  = longueur_chemin,
    )
    return JsonResponse({'paths': chemins})


# --- API Pathfinding — extension de chemin -----------------------------------

@csrf_exempt
def api_pathfinding_extend(request):
    """
    Étend le chemin d'un véhicule (appelé quand < 6 étapes restantes).

    Corps POST :
        { "current_node": 4, "origin_node": 0,
          "visited_nodes": [0,1,4], "etats": {...} }

    Réponse :
        { "path": [ { "from_node", "to_node", "road_idx", "reversed" }, ... ] }
    """
    if request.method != 'POST':
        return JsonResponse({'erreur': 'Méthode non autorisée'}, status=405)
    try:
        donnees = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'erreur': 'JSON invalide'}, status=400)

    nœud_courant  = int(donnees.get('current_node', 0))
    nœud_origine  = int(donnees.get('origin_node',  0))
    nœuds_visités = [int(n) for n in donnees.get('visited_nodes', [])]
    etats_int     = {int(k): v for k, v in donnees.get('etats', {}).items()}

    extension = pathfinding.etendre_chemin(
        nœud_courant  = nœud_courant,
        nœud_origine  = nœud_origine,
        nœuds_visités = nœuds_visités,
        etats_routes  = etats_int,
        étapes_supp   = 20,
    )
    return JsonResponse({'path': extension})
