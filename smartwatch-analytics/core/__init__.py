"""
Core FIT File System

Sistema central para criação e leitura de arquivos FIT.
"""

from .fit_creator import criar_treino_fit, ler_treino_fit, ler_atividade_fit

__version__ = "1.0.0"
__author__ = "Garmin Integration Team"

__all__ = [
    "criar_treino_fit",
    "ler_treino_fit", 
    "ler_atividade_fit"
] 