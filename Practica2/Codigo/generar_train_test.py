# Generar una partición train/test de los documentos
import os
import random
import json

# Parametros
base = '../Datos'
temas = ['Deportes', 'Politica', 'Salud']
directorio_ficheros = f'{base}/Original'
fichero_particion = 'particion_train_test.json'
prop_train = 0.5

out = {'train': {}, 'test': {}}
for tema in temas:
    # https://stackoverflow.com/questions/3207219/how-do-i-list-all-files-of-a-directory
    path = f'{directorio_ficheros}/{tema}'
    ficheros = [f'{f}' for f in os.listdir(path)
                if os.path.isfile(os.path.join(path, f))]
    random.shuffle(ficheros)
    out['train'][tema] = ficheros[:int(prop_train*len(ficheros))]
    out['test'][tema] = ficheros[int(prop_train*len(ficheros)):]
    with open(fichero_particion, 'w') as f_p:
        json.dump(out, f_p, indent=2)
