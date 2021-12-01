import os
import shutil
import random

# Parametros
temas = ['Deportes', 'Politica', 'Salud']
directorio_raw = './Original'
directorio_train = './Entrenamiento'
directorio_test = './Test'
prop_train = 0.5

# Crear directorios si no existen
shutil.rmtree(directorio_test)
shutil.rmtree(directorio_train)
os.makedirs(directorio_test, exist_ok=True)
os.makedirs(directorio_train, exist_ok=True)

for tema in temas:
    # https://stackoverflow.com/questions/3207219/how-do-i-list-all-files-of-a-directory
    path = f'{directorio_raw}/{tema}'
    ficheros = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
    random.shuffle(ficheros)
    ficheros_train = ficheros[:int(prop_train*len(ficheros))]
    ficheros_test = ficheros[int(prop_train*len(ficheros)):]
    path_test = f'{directorio_test}/{tema}'
    os.makedirs(path_test, exist_ok=True)
    path_train = f'{directorio_train}/{tema}'
    os.makedirs(path_train, exist_ok=True)
    for f_train in ficheros_train:
        shutil.copy(f'{path}/{f_train}', path_train)
    for f_test in ficheros_test:
        shutil.copy(f'{path}/{f_test}', path_test) 
