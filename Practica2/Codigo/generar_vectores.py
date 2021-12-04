# Limpiar caracteres especiales y palabras vacías de los documentos
import os
import json
import regex as re
import spacy as spa
from collections import Counter
from functools import reduce
import numpy as np

# Parametros
base = os.path.join(os.path.pardir, 'Datos')
temas = ['Deportes', 'Politica', 'Salud']
directorio_ficheros = os.path.join(base, 'Original')
fichero_particion = 'particion_train_test.json'
fichero_glosario = 'glosario.json'


# Crear una expresión regular para eliminar caracteres indeseados
re_caracteres = re.compile(r'[^a-záéíóúñ .¡!¿?,;:()]', re.IGNORECASE)
re_alfa = re.compile(r'[^a-záéíóúñ-]', re.IGNORECASE)

# Obtener set de palabras vacias
fichero_palabras_vacias = 'listado_palabras_vacias.json'
with open(fichero_palabras_vacias, 'r') as p_vacias:
    palabras_vacias = set(json.load(p_vacias))

# Obtener parseador de spacy
parser = spa.load('es_core_news_md')

def limpiar_texto(path):
    with open(path, 'r') as f:
        # Primero, leer todo el fichero, y pasar a minúsculas
        texto = ' '.join(f.readlines())
    # Quitar caracteres no deseados
    texto = re_caracteres.sub('', texto)
    # Parsear texto resultante con spacy
    doc = parser(texto)
    # Filtrar sustantivos y nombres propios
    palabras = []
    acarreo_nom_propios = []
    acarreo_det_preps = []
    for palabra in doc:
        if palabra.pos_ == 'NOUN':
            # Reforzar generalización guardando solamente lematización
            palabras.append(re_alfa.sub('', palabra.lemma_.lower()))
        # Añadir nombres propios, que pueden ser compuestos
        if palabra.pos_ == 'PROPN':
            if acarreo_det_preps:
                acarreo_nom_propios += acarreo_det_preps
                acarreo_det_preps = []
            acarreo_nom_propios.append(palabra.lemma_)
        elif acarreo_nom_propios:
             # Nombres con preposiciones y determinantes
            if palabra.pos_ in ('ADP', 'DET') and palabra.lemma_ in (
                'de', 'la', 'del'):
                acarreo_det_preps.append(palabra.lemma_)
            else:  # Fin de nombre compuesto
                palabras.append(re_alfa.sub('', '-'.join(acarreo_nom_propios)))
                acarreo_nom_propios = []
    if acarreo_nom_propios:
        palabras.append(re_alfa.sub('', '-'.join(acarreo_nom_propios)))
    palabras = list(filter(lambda p: p not in palabras_vacias, palabras))
    return Counter(palabras)

# Cargar particion train/test
with open(fichero_particion, 'r') as f:
    part = json.load(f)

# Generar tablas de frecuencias para cada fichero y glosario
out = {
    'train': {}, 'test': {}, 'frecuencias': {}, 'terminos': None,
}
terminos = set()
for particion, temas in part.items():
    out_part = out[particion]
    for tema, textos in temas.items():
        path_tema = os.path.join(directorio_ficheros, tema)
        texto_a_tabla = out_part.setdefault(tema, {})
        for texto in textos:
            path_texto = os.path.join(path_tema, texto)
            conteos_texto = limpiar_texto(path_texto)
            texto_a_tabla[texto] = conteos_texto
        # Solamente para la partición de entrenamiento, glosario
        if particion == 'train':
            glosario = reduce(lambda a,b: a+b, out['train'][tema].values())
            out['frecuencias'][tema] = glosario
            terminos.update(glosario.keys())
out['terminos'] = {k:v for v,k in enumerate(terminos)}

# Generar máscara idf para cada palabra
relevancias_idf = np.empty(len(terminos))
total_documentos = sum(len(tema) for tema in out['train'])
for termino, pos in out['terminos'].items():
    total_aparic = 0
    for textos in out['train'].values():
        total_aparic += sum(int(termino in tabla) for tabla in textos.values())
    relevancias_idf[pos] = np.log10(total_documentos / total_aparic)
# Generar máscar tf para cada tema
relevancia_tf = {}
for tema, frecuencias in out['frecuencias'].items():
    total_palabras = sum(conteo for conteo in frecuencias.values())
    rel_tf_tema = relevancia_tf.setdefault(tema, np.zeros(len(terminos)))
    for termino, pos in out['terminos'].items():
        rel_tf_tema[pos] = frecuencias.get(termino, 0) / total_palabras
# Generar vectores tf-idf para cada tema
out['vectores_tf_idf'] = {tema:(relevancia_tf[tema]*relevancias_idf).tolist()
                          for tema in temas}
out['relevancia_idf'] = relevancias_idf.tolist()
# Exportar a json
with open(fichero_glosario, 'w') as f:
    json.dump(out, f, indent=2)

            