from django.urls import path
from . import views

urlpatterns = [
    # Page principale
    path('', views.index, name='index'),

    # API Markov + Files d'attente + Optimisation (toutes les 2 s)
    path('api/tick/', views.api_tick, name='api_tick'),

    # API Monte Carlo — changement de scénario
    path('api/scenario/', views.api_scenario, name='api_scenario'),

    # API Stats — métriques M/M/1 complètes
    path('api/stats/', views.api_stats, name='api_stats'),

    # API Pathfinding — Python calcule les chemins, JS affiche seulement
    path('api/pathfinding/init/',   views.api_pathfinding_init,   name='api_pathfinding_init'),
    path('api/pathfinding/extend/', views.api_pathfinding_extend, name='api_pathfinding_extend'),
]
