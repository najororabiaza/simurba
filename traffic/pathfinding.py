"""
pathfinding.py — Simurba
========================
Toute la logique de pathfinding est ici (Python).
JavaScript s'occupe uniquement de l'affichage et des interactions.

Réseau routier — grille 3×3 :
    nœud 0 — nœud 1 — nœud 2
       |         |         |
    nœud 3 — nœud 4 — nœud 5
       |         |         |
    nœud 6 — nœud 7 — nœud 8

12 routes dirigées (sens unique d'origine) :
    0→1, 1→2            (horizontal haut)
    3→4, 4→5            (horizontal milieu)
    6→7, 7→8            (horizontal bas)
    0→3, 1→4, 2→5       (vertical haut→milieu)
    3→6, 4→7, 5→8       (vertical milieu→bas)

Pour le pathfinding, on autorise le sens inverse (bidirectionnel).
Un tronçon inversé a road_idx = idx_original, reversed = True.
"""

import heapq
import random
import math

# ---------------------------------------------------------------------------
# Définition du graphe
# ---------------------------------------------------------------------------

# Chaque entrée = (nœud_départ, nœud_arrivée)
# L'index dans cette liste = road_idx (identique côté JavaScript)
ROUTES_DEF: list[tuple[int, int]] = [
    (0, 1), (1, 2),           # idx 0-1  — horizontal haut
    (3, 4), (4, 5),           # idx 2-3  — horizontal milieu
    (6, 7), (7, 8),           # idx 4-5  — horizontal bas
    (0, 3), (1, 4), (2, 5),  # idx 6-8  — vertical haut→milieu
    (3, 6), (4, 7), (5, 8),  # idx 9-11 — vertical milieu→bas
]

NUM_NOEUDS = 9
NUM_ROUTES = len(ROUTES_DEF)

# Coût de traversée selon l'état Markov
COUT_ETAT: dict[str, float] = {
    'fluide':  1.0,
    'ralenti': 3.0,
    'bouchon': 9.0,
}

# Coût additionnel pour les tronçons inversés (on préfère le sens canonique)
PENALITE_INVERSE = 0.6


# ---------------------------------------------------------------------------
# Construction du graphe bidirectionnel
# ---------------------------------------------------------------------------

def _construire_graphe(etats_routes: dict | None = None) -> dict:
    """
    Construit la liste d'adjacence bidirectionnelle pondérée.

    etats_routes : {road_idx (int) : etat (str)}  (peut être None)

    Retourne : { nœud_id : [ {to, road_idx, reversed, weight}, ... ] }
    """
    graphe: dict[int, list] = {i: [] for i in range(NUM_NOEUDS)}

    for idx, (a, b) in enumerate(ROUTES_DEF):
        etat = (etats_routes or {}).get(idx, 'fluide')
        w = COUT_ETAT.get(etat, 1.0)

        # Sens canonique (a → b)
        graphe[a].append({
            'to': b, 'road_idx': idx, 'reversed': False, 'weight': w
        })
        # Sens inverse (b → a) — légèrement pénalisé
        graphe[b].append({
            'to': a, 'road_idx': idx, 'reversed': True, 'weight': w + PENALITE_INVERSE
        })

    return graphe


# ---------------------------------------------------------------------------
# Algorithme de Dijkstra
# ---------------------------------------------------------------------------

def dijkstra(
    depart: int,
    arrivee: int,
    etats_routes: dict | None = None,
    noeuds_interdits: set | None = None,
) -> list:
    """
    Trouve le chemin le plus court entre `depart` et `arrivee`.

    Retourne une liste de tronçons :
        [ {'from_node', 'to_node', 'road_idx', 'reversed'}, ... ]
    ou [] si aucun chemin trouvé.
    """
    graphe   = _construire_graphe(etats_routes)
    bloqués  = set(noeuds_interdits or [])
    compteur = 0   # tie-breaker pour éviter la comparaison de dicts
    # tas : (coût_cumulé, compteur, nœud_courant, chemin_jusqu'ici)
    tas      = [(0.0, compteur, depart, [])]
    visités  = set()

    while tas:
        coût, _, nœud, chemin = heapq.heappop(tas)

        if nœud in visités:
            continue
        visités.add(nœud)

        if nœud == arrivee:
            return chemin

        for arête in graphe[nœud]:
            suivant = arête['to']
            if suivant in visités or suivant in bloqués:
                continue
            nouveau_tronçon = {
                'from_node': nœud,
                'to_node':   suivant,
                'road_idx':  arête['road_idx'],
                'reversed':  arête['reversed'],
            }
            compteur += 1
            heapq.heappush(
                tas,
                (coût + arête['weight'], compteur, suivant, chemin + [nouveau_tronçon])
            )

    return []   # aucun chemin


# ---------------------------------------------------------------------------
# Sélection pondérée aléatoire
# ---------------------------------------------------------------------------

def _choix_pondéré(candidats: list) -> dict | None:
    """
    Sélectionne une arête parmi `candidats` avec probabilité
    inversement proportionnelle au poids (route fluide = plus probable).
    """
    if not candidats:
        return None
    poids   = [1.0 / e['weight'] for e in candidats]
    total   = sum(poids)
    r       = random.random() * total
    cumulé  = 0.0
    for arête, p in zip(candidats, poids):
        cumulé += p
        if cumulé >= r:
            return arête
    return candidats[-1]


# ---------------------------------------------------------------------------
# Marche aléatoire guidée (sans retour à l'origine)
# ---------------------------------------------------------------------------

def generer_chemin(
    nœud_départ:   int,
    nb_étapes:     int,
    etats_routes:  dict | None = None,
    nœud_origine:  int | None = None,
) -> list:
    """
    Génère une marche aléatoire de `nb_étapes` tronçons depuis `nœud_départ`.

    Règles :
    - Ne jamais retourner à `nœud_origine`.
    - Évite les 4 derniers nœuds visités pour favoriser l'exploration.
    - Pondération inverse au coût → préfère les routes fluides.

    Retourne la même structure de liste que `dijkstra()`.
    """
    graphe  = _construire_graphe(etats_routes)
    chemin  = []
    courant = nœud_départ
    récents: list[int] = []   # mémoire circulaire des 6 derniers nœuds

    for _ in range(nb_étapes):
        arêtes = graphe[courant]

        # 1. Ne jamais retourner à l'origine
        if nœud_origine is not None:
            arêtes = [e for e in arêtes if e['to'] != nœud_origine]

        # 2. Préférer les nœuds non-récemment visités
        frais = [e for e in arêtes if e['to'] not in récents[-4:]]
        if frais:
            arêtes = frais

        # 3. Repli si bloqué (mais jamais vers l'origine)
        if not arêtes:
            arêtes = graphe[courant]
            if nœud_origine is not None:
                arêtes = [e for e in arêtes if e['to'] != nœud_origine]
        if not arêtes:
            break   # impasse réelle (très rare avec le graphe bidirectionnel)

        choix = _choix_pondéré(arêtes)
        if choix is None:
            break

        chemin.append({
            'from_node': courant,
            'to_node':   choix['to'],
            'road_idx':  choix['road_idx'],
            'reversed':  choix['reversed'],
        })

        récents.append(courant)
        if len(récents) > 6:
            récents.pop(0)

        courant = choix['to']

    return chemin


# ---------------------------------------------------------------------------
# API publique — appelée par views.py
# ---------------------------------------------------------------------------

def init_chemins(
    nb_vehicules: int,
    etats_routes: dict | None = None,
    longueur_chemin: int = 30,
) -> list:
    """
    Génère les chemins initiaux pour tous les véhicules.
    Chaque véhicule démarre sur un nœud aléatoire.

    Retourne :
        [ { 'vehicle_id', 'origin_node', 'current_node', 'path': [...] }, ... ]
    """
    véhicules = []
    for vid in range(nb_vehicules):
        origine = random.randint(0, NUM_NOEUDS - 1)
        chemin  = generer_chemin(
            nœud_départ  = origine,
            nb_étapes    = longueur_chemin,
            etats_routes = etats_routes,
            nœud_origine = origine,
        )
        véhicules.append({
            'vehicle_id':   vid,
            'origin_node':  origine,
            'current_node': origine,
            'path':         chemin,
        })
    return véhicules


def etendre_chemin(
    nœud_courant:   int,
    nœud_origine:   int,
    nœuds_visités:  list,
    etats_routes:   dict | None = None,
    étapes_supp:    int = 20,
) -> list:
    """
    Étend le chemin d'un véhicule qui approche de la fin de son trajet.

    nœuds_visités : liste des derniers nœuds parcourus (pour l'évitement).
    Retourne une liste de tronçons supplémentaires.
    """
    graphe  = _construire_graphe(etats_routes)
    chemin  = []
    courant = nœud_courant
    récents = list(nœuds_visités[-6:])

    for _ in range(étapes_supp):
        arêtes = graphe[courant]

        if nœud_origine is not None:
            arêtes = [e for e in arêtes if e['to'] != nœud_origine]

        frais = [e for e in arêtes if e['to'] not in récents[-4:]]
        if frais:
            arêtes = frais

        if not arêtes:
            arêtes = graphe[courant]
            if nœud_origine is not None:
                arêtes = [e for e in arêtes if e['to'] != nœud_origine]
        if not arêtes:
            break

        choix = _choix_pondéré(arêtes)
        if choix is None:
            break

        chemin.append({
            'from_node': courant,
            'to_node':   choix['to'],
            'road_idx':  choix['road_idx'],
            'reversed':  choix['reversed'],
        })

        récents.append(courant)
        if len(récents) > 6:
            récents.pop(0)

        courant = choix['to']

    return chemin


def calcul_statistiques_chemin(chemin: list, etats_routes: dict | None = None) -> dict:
    """
    Calcule des statistiques sur un chemin donné.
    Utile pour le debug et les métriques.
    """
    if not chemin:
        return {'longueur': 0, 'nœuds_uniques': 0, 'coût_total': 0.0}

    nœuds_visités = set()
    nœuds_visités.add(chemin[0]['from_node'])
    coût_total = 0.0

    for t in chemin:
        nœuds_visités.add(t['to_node'])
        etat = (etats_routes or {}).get(t['road_idx'], 'fluide')
        coût_total += COUT_ETAT.get(etat, 1.0)
        if t['reversed']:
            coût_total += PENALITE_INVERSE

    return {
        'longueur':       len(chemin),
        'nœuds_uniques':  len(nœuds_visités),
        'coût_total':     round(coût_total, 2),
    }
