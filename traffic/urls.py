from django.urls import path
from . import views

urlpatterns = [

    # Route principale — affiche la page de simulation
    path('', views.index, name='index'),

    # Route API — appelée par le JavaScript pour faire avancer la simulation
    # Le JS envoie POST /api/tick/ avec les états actuels
    # Django retourne les nouveaux états calculés par Markov
    path('api/tick/', views.api_tick, name='api_tick'),

]