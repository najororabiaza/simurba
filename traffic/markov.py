import random

#  Les 3 etats possibles d'une route
FLUIDE  = 'fluide'
RALENTI = 'ralenti'
BOUCHON = 'bouchon'

# Liste ordonnée des états — l'ordre est important pour la matrice
ETATS = [FLUIDE, RALENTI, BOUCHON]



#  La matrice de transition
#
#  C'est le cœur des Chaînes de Markov.
#  Elle dit : "si je suis dans l'état X, quelle est la probabilité
#  de passer dans l'état Y au prochain tick ?"
#
#  Lecture : chaque LIGNE correspond à l'état actuel.
#            chaque COLONNE correspond à l'état suivant possible.
#            La somme de chaque ligne doit toujours valoir 1.0
#
#  Exemple : si une route est FLUIDE (ligne 0) :
#    - 85% de chances de rester FLUIDE
#    - 12% de chances de devenir RALENTI
#    -  3% de chances de devenir BOUCHON


MATRICE_TRANSITION = {
    #          Fluide  Ralenti  Bouchon
    FLUIDE:  [  0.85,   0.12,    0.03  ],
    RALENTI: [  0.20,   0.65,    0.15  ],
    BOUCHON: [  0.10,   0.25,    0.65  ],
}



#  calculer le prochain état d'UNE route
#
#  Paramètre :
#    etat_actuel = l'état actuel de la route ('fluide', etc.)
#
#  Retourne :
#    le nouvel état de la route après un tick


def prochain_etat(etat_actuel):

    # On récupère les probabilités de transition pour cet état
    # Exemple si etat_actuel = 'fluide' = probabilites = [0.85, 0.12, 0.03]
    probabilites = MATRICE_TRANSITION[etat_actuel]

    # random.choices() choisit un élément dans ETATS
    # en tenant compte des poids (probabilites)
    # k=1 signifie qu'on veut 1 seul résultat = retourne une liste
    resultat = random.choices(ETATS, weights=probabilites, k=1)

    # resultat est une liste comme ['fluide'], on prend le premier élément
    return resultat[0]



#  faire évoluer TOUTES les routes du réseau
#
#  Paramètre :
#    etats_routes = un dictionnaire { id_route: etat_actuel }
#    Exemple : { 0: 'fluide', 1: 'ralenti', 2: 'bouchon', ... }
#
#  Retourne :
#    un nouveau dictionnaire avec les états mis à jour


def tick(etats_routes):

    # On crée un dictionnaire vide pour stocker les nouveaux états
    nouveaux_etats = {}

    # On parcourt chaque route et son état actuel
    for id_route, etat_actuel in etats_routes.items():

        # On calcule le prochain état pour cette route
        nouvel_etat = prochain_etat(etat_actuel)

        # On sauvegarde le nouvel état dans le dictionnaire
        nouveaux_etats[id_route] = nouvel_etat

    # On retourne tous les nouveaux états
    return nouveaux_etats



#  créer l'état initial du réseau
#
#  Paramètre :
#    nombre_routes = le nombre de routes dans le réseau (12 ici)
#
#  Retourne :
#    un dictionnaire { 0: 'fluide', 1: 'fluide', ... }
#    toutes les routes commencent en état FLUIDE


def etat_initial(nombre_routes):

    # On crée un dictionnaire avec toutes les routes en état FLUIDE
    etats = {}

    # On crée une entrée pour chaque route (de 0 à nombre_routes - 1)
    for i in range(nombre_routes):
        etats[i] = FLUIDE

    return etats



#  compter les routes par état
#
#  Utile pour le dashboard (Fluide: 6, Ralenti: 4, Bouchon: 2)
#
#  Paramètre :
#    etats_routes = le dictionnaire des états actuels
#
#  Retourne :
#    un dictionnaire { 'fluide': N, 'ralenti': N, 'bouchon': N }


def compter_etats(etats_routes):

    # On initialise les compteurs à zéro
    compteurs = {
        FLUIDE:  0,
        RALENTI: 0,
        BOUCHON: 0,
    }

    # On parcourt tous les états et on incrémente le bon compteur
    for etat in etats_routes.values():
        compteurs[etat] += 1

    return compteurs