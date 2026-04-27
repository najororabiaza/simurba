import json

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from . import markov


#  L'état du réseau est gardé en mémoire le temps que le serveur tourne.
#  Ce dictionnaire contient l'état actuel de chaque route.
#  Exemple : { 0: 'fluide', 1: 'ralenti', 2: 'bouchon', ... }
#
#  On utilise None pour savoir si c'est la première requête —
#  dans ce cas on initialise avec etat_initial()

etat_reseau = None


#  Vue principale — affiche la page HTML de la simulation

def index(request):
    return render(request, 'traffic/base.html')


#  Vue API — appelée par le JavaScript toutes les 2 secondes
#
#  Méthode HTTP : POST
#  Ce que le JS envoie : { "etats": { "0": "fluide", "1": "ralenti", ... } }
#  Ce que Django retourne : { "etats": { "0": "fluide", ... }, "compteurs": { ... } }
#
#  @csrf_exempt permet au JavaScript d'appeler cette vue
#  sans avoir à envoyer un token CSRF (simplifie le code JS)

@csrf_exempt
def api_tick(request):

    # On déclare qu'on utilise la variable globale etat_reseau
    global etat_reseau

    # On accepte uniquement les requêtes POST
    if request.method != 'POST':
        return JsonResponse({'erreur': 'Méthode non autorisée'}, status=405)

    # On lit le corps de la requête JSON envoyée par le JavaScript
    try:
        donnees = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'erreur': 'JSON invalide'}, status=400)

    # On récupère les états envoyés par le JS
    # Le JS envoie les clés en string ("0", "1"...), on les convertit en int
    etats_recus = donnees.get('etats', {})
    etats_recus = { int(cle): valeur for cle, valeur in etats_recus.items() }

    # Si c'est la première fois (etat_reseau est None),
    # on initialise le réseau avec les états reçus du JS
    if etat_reseau is None:
        etat_reseau = etats_recus

    # On fait évoluer le réseau d'un tick avec le modèle de Markov
    etat_reseau = markov.tick(etat_reseau)

    # On compte les routes par état pour le dashboard
    compteurs = markov.compter_etats(etat_reseau)

    # On retourne les nouveaux états et les compteurs au JavaScript
    # On convertit les clés int en string pour que JSON les accepte
    return JsonResponse({
        'etats':      { str(k): v for k, v in etat_reseau.items() },
        'compteurs':  compteurs,
    })