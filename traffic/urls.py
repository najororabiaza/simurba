from django.urls import path
from . import views

urlpatterns = [

    # Route principale — affiche la page de simulation
    path('', views.index, name='index'),

    # API Markov + Files d'attente + Optimisation
    # Appelée toutes les 2 secondes par le JavaScript
    path('api/tick/', views.api_tick, name='api_tick'),

    # API Monte Carlo — changer le scénario de trafic
    # Le JS envoie le nom du scénario, Django retourne les nouveaux états
    path('api/scenario/', views.api_scenario, name='api_scenario'),

    # API Stats — métriques M/M/1 complètes pour le dashboard
    path('api/stats/', views.api_stats, name='api_stats'),

]