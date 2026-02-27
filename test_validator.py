import os
import sys

sys.path.append(os.path.abspath(r"d:\Python\ASO Agent\aso-python-app"))
from validator import validate_aso_text

test_output = """
--------------------USA-----------------------------
App Title:          Croc Chomper Fun
Sub Title:          Jungle Predator Hunt Quest
Keywords:           crocodile,game,alligator,reptile,simulator,action,kids,family,swamp,river,water,attack,bite,survive
--------------------Spain-----------------------------
App Title:          Croc Salvaje Juego
Sub Title:          Depredador Selva Caza
Keywords:           cocodrilo,caiman,reptil,simulador,accion,niños,familia,pantano,rio,agua,ataque,mordisco,sobrevivir
"""

locales_data, warnings = validate_aso_text(test_output)
print("Locales Data:", locales_data)
print("Warnings:", warnings)
