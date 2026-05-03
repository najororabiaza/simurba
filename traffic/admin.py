"""
Configuration de l'interface d'administration Django.

Actuellement, aucun modèle n'est défini dans traffic.models,
donc admin.py est vide. Lorsque des modèles (par exemple,
SimulationResult, TrafficScenario) seront créés, ils pourront
être enregistrés ici pour l'administration.
"""
from django.contrib import admin

# Exemple (commenté) :
# from .models import SimulationResult
# admin.site.register(SimulationResult)