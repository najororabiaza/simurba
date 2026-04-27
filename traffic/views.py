import json

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from . import markov
from . import queue_model
from . import monte_carlo
from . import optimizer


#  État global du réseau — gardé en mémoire côté serveur
#
#  Ces variables persistent tant que le serveur Django tourne.
#  Elles sont partagées entre tous les appels API.

etat_reseau         = None   # { id_route: etat }    — vient de markov.py
files_intersections = None   # { id_noeud: nb_veh }  — vient de queue_model.py
scenario_actuel     = 'normal'   # scénario Monte Carlo actif


#  Vue principale — affiche la page HTML

def index(request):
    return render(request, 'traffic/base.html')


#  API tick — appelée toutes les 2 secondes par le JavaScript
#
#  Fait avancer la simulation d'un pas :
#    1. Markov fait évoluer les états des routes
#    2. Les files d'attente sont mises à jour
#    3. L'optimiseur calcule les meilleures durées de feux
#
#  Le JS envoie : { "etats": { "0": "fluide", ... } }
#  Django retourne : { "etats": {...}, "files": {...}, "optimisation": {...}, ... }

@csrf_exempt
def api_tick(request):

    global etat_reseau, files_intersections

    if request.method != 'POST':
        return JsonResponse({'erreur': 'Méthode non autorisée'}, status=405)

    try:
        donnees = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'erreur': 'JSON invalide'}, status=400)

    # On récupère les états envoyés par le JS et on convertit les clés en int
    etats_recus = donnees.get('etats', {})
    etats_recus = { int(cle): valeur for cle, valeur in etats_recus.items() }

    # Initialisation au premier appel
    if etat_reseau is None:
        etat_reseau = etats_recus

    if files_intersections is None:
        # 9 intersections pour notre grille 3x3
        files_intersections = queue_model.files_initiales(9)

    # Étape 1 — Markov fait évoluer les états des routes
    etat_reseau = markov.tick(etat_reseau)

    # Étape 2 — Les files d'attente évoluent selon les nouveaux états
    files_intersections = queue_model.tick_files(files_intersections, etat_reseau)

    # Étape 3 — L'optimiseur calcule les meilleures durées de feux
    resultat_optimisation = optimizer.optimiser_feux(etat_reseau)

    # On compte les routes par état pour le dashboard
    compteurs = markov.compter_etats(etat_reseau)

    # On trouve l'intersection la plus chargée
    inter_max = queue_model.intersection_max(files_intersections)

    # On calcule le temps d'attente moyen sur le réseau
    wq_moyen = queue_model.temps_attente_moyen(files_intersections, etat_reseau)

    # On retourne tout au JavaScript
    return JsonResponse({
        # États Markov mis à jour
        'etats':      { str(k): v for k, v in etat_reseau.items() },
        'compteurs':  compteurs,

        # Files d'attente
        'files':      { str(k): v for k, v in files_intersections.items() },
        'inter_max':  inter_max,
        'wq_moyen':   wq_moyen,

        # Optimisation
        'optimisation': resultat_optimisation,
    })


#  API scénario — changer le scénario Monte Carlo actif
#
#  Le JS envoie : { "scenario": "heure_de_pointe" }
#  Django retourne les nouveaux états générés par Monte Carlo

@csrf_exempt
def api_scenario(request):

    global etat_reseau, files_intersections, scenario_actuel

    if request.method != 'POST':
        return JsonResponse({'erreur': 'Méthode non autorisée'}, status=405)

    try:
        donnees = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'erreur': 'JSON invalide'}, status=400)

    # On récupère le scénario demandé
    scenario = donnees.get('scenario', 'normal')

    # On vérifie que le scénario existe
    scenarios_disponibles = monte_carlo.lister_scenarios()
    if scenario not in scenarios_disponibles:
        return JsonResponse({'erreur': 'Scénario inconnu'}, status=400)

    # Monte Carlo génère de nouveaux états selon ce scénario
    etat_reseau = monte_carlo.generer_etats_initiaux(12, scenario)

    # On remet les files à zéro pour le nouveau scénario
    files_intersections = queue_model.files_initiales(9)

    # On mémorise le scénario actif
    scenario_actuel = scenario

    # On estime le risque de bouchon avec 500 simulations Monte Carlo
    risque_bouchon = monte_carlo.estimer_risque_bouchon(500, 12, scenario)

    # On retourne les nouveaux états et les infos du scénario
    return JsonResponse({
        'etats':         { str(k): v for k, v in etat_reseau.items() },
        'scenario':      scenario,
        'info_scenario': monte_carlo.info_scenario(scenario),
        'risque_bouchon': risque_bouchon,
        'compteurs':     markov.compter_etats(etat_reseau),
    })


#  API stats — retourne les statistiques complètes du réseau
#
#  Appelée par le JS pour afficher les métriques M/M/1 dans le dashboard
#  GET /api/stats/

def api_stats(request):

    if request.method != 'GET':
        return JsonResponse({'erreur': 'Méthode non autorisée'}, status=405)

    # Si la simulation n'a pas encore démarré, on retourne des valeurs vides
    if etat_reseau is None:
        return JsonResponse({'erreur': 'Simulation non démarrée'}, status=400)

    # On calcule les métriques M/M/1 pour chaque route
    metriques_par_route = {}
    for id_route, etat in etat_reseau.items():
        metriques_par_route[str(id_route)] = queue_model.calculer_metriques(etat)

    # On retourne les métriques complètes
    return JsonResponse({
        'metriques_par_route': metriques_par_route,
        'wq_moyen':            queue_model.temps_attente_moyen(
                                   files_intersections or {},
                                   etat_reseau
                               ),
        'scenario_actuel':     scenario_actuel,
        'scenarios_disponibles': monte_carlo.lister_scenarios(),
    })