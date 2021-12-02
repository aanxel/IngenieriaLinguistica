# Limpiar caracteres especiales y palabras vacías de los documentos
import os
import json
import regex as re

# Parametros
base = '../Datos'
temas = ['Deportes', 'Politica', 'Salud']
directorio_ficheros = f'{base}/Original'
directorio_limpieza = f'{base}/Limpieza'


# Crear una expresión regular para eliminar caracteres no alfabeto o espacios
re_caracteres = re.compile(r'[^a-záéíóúñ \n]', re.IGNORECASE)

# Crear una expresión regular para eliminar palabras vacias
# https://stackoverflow.com/questions/15435726/remove-all-occurrences-of-words-in-a-string-from-a-python-list
fichero_palabras_vacias = 'listado_palabras_vacias.json'
with open(fichero_palabras_vacias, 'r') as p_vacias:
    listado_palabras_vacias = json.load(p_vacias)
eliminar = '|'.join(fichero_palabras_vacias)
re_palabras_vacias = re.compile(r'\b(' + eliminar + r')\b', re.IGNORECASE)

print(re_palabras_vacias.sub('', re_caracteres.sub('', 'Un    árbol.\n Bonito!')))
exit()
for tema in temas:
    # https://stackoverflow.com/questions/3207219/how-do-i-list-all-files-of-a-directory
    path = f'{directorio_ficheros}/{tema}'
    ficheros = [f'{f}' for f in os.listdir(path)
                if os.path.isfile(os.path.join(path, f))]