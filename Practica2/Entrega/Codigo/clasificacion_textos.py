import numpy as np
import json
import os
import regex as re
import spacy as spa
from collections import Counter
from functools import reduce
import random

dir_documentos = os.path.join(os.path.pardir, 'Datos')
temas = ('Deportes', 'Politica', 'Salud')

def generar_particion_train_test(f_salida='particion_train_test.json',
                                 temas=temas, dir_docs=dir_documentos,
                                 prop_train=0.5):
    out = {'train': {}, 'test': {}}
    for tema in temas:
        # https://tinyurl.com/2p8m225p
        path = os.path.join(dir_docs, tema)
        ficheros = [f for f in os.listdir(path)
                    if os.path.isfile(os.path.join(path, f))]
        random.shuffle(ficheros)
        out['train'][tema] = ficheros[:int(prop_train*len(ficheros))]
        out['test'][tema] = ficheros[int(prop_train*len(ficheros)):]
        with open(f_salida, 'w') as f_p:
            json.dump(out, f_p, indent=2)
            

def sim_cos(a, b):
    return np.dot(a, b)/(np.linalg.norm(a)*np.linalg.norm(b))

class ClasificadorTfIdf:
    def __init__(self, fichero_salida='clasificacion.json',
                 f_compilacion='compilacion.json',
                 f_particion='particion_train_test.json',
                 d_docs=dir_documentos,
                 temas=temas):
        self.salida = fichero_salida
        self.f_compilacion = f_compilacion
        self.temas = temas
        self.d_docs = d_docs
        # Crear una expresión regular para eliminar caracteres indeseados
        self.re_caracteres = re.compile(
            r'[^a-záéíóúñ .¡!¿?,;:()]', re.IGNORECASE)
        self.re_alfa = re.compile(r'[^a-záéíóúñ-]', re.IGNORECASE)

        # Obtener set de palabras vacias
        fichero_palabras_vacias = 'listado_palabras_vacias.json'
        with open(fichero_palabras_vacias, 'r') as p_vacias:
            self.palabras_vacias = set(json.load(p_vacias))

        # Obtener parseador de spacy
        self.parser = spa.load('es_core_news_md')
        self.modelo = None

        # Obtener particion train/test
        if f_particion:
            with open(f_particion, 'r') as f:
                self.part = json.load(f)
        else:  # O asumir que todos los datos son de entrenamiento
            self.part = {
                'train': {},
                'test': {t:[] for t in self.temas}}
            for t in self.temas:
                path = os.path.join(d_docs, t)
                self.part['train'][t] = [f for f in os.listdir(path)
                                         if os.path.isfile(
                                             os.path.join(path, f))]
    
    @property
    def modelo(self):
        # Abrir fichero con el modelo
        if self._modelo is None:
            try:
                with open(self.f_compilacion, 'r') as f:
                    self._modelo = json.load(f)
            except FileNotFoundError:
                print('Hay que compilar modelo')
                raise FileNotFoundError()
        return self._modelo
    
    @modelo.setter
    def modelo(self, v):
        self._modelo = v

    def test(self, exportar=True):
        errores = []
        predicciones_total = {}
        for tema_r, ficheros in self.part['test'].items():
            dir_t = os.path.join(self.d_docs, tema_r)
            paths = [os.path.join(dir_t, f) for f in ficheros]
            predicciones = self.clasifica(paths, exportar=False)
            predicciones_total = {**predicciones_total, **predicciones}
            # Comprobar errores en la clasificación
            for i in range(len(ficheros)):
                tema_pred = predicciones[paths[i]][0][0]
                id_r = os.path.join(tema_r, ficheros[i])
                if tema_pred != tema_r:
                    errores.append({
                        'real': id_r,
                        'pred': os.path.join(tema_pred, ficheros[i])
                    })
        t_aciertos = (1 - len(errores) / len(predicciones_total)) * 100
        out = {'errores': errores, 'predicciones': predicciones_total,
               'tasa_aciertos': f'{t_aciertos}%'}
        if exportar:
            with open(self.salida, 'w') as f:
                json.dump(out, f, indent=4)
        return out

    def clasifica(self, paths, exportar=True):
        prediccion = {}
        vs_tfidf_tema = {t: self.modelo['vectores_tf_idf'][t]
                         for t in self.temas}
        for p in paths:
            vector_f = self.genera_vector(p)
            simil_tema = [(t, sim_cos(vs_tfidf_tema[t], vector_f))
                          for t in self.temas]
            simil_tema.sort(key=lambda e: -1 * e[1])
            prediccion[p] = [e for e in simil_tema]
        if exportar:
            with open(self.salida, 'w') as f:
                json.dump(prediccion, f, indent=4)
        return prediccion

    def genera_vector(self, path):
        vector = np.zeros(len(self.modelo['terminos']))
        t_frecuencias = self.frecuencias_terminos(path)
        # Generar vector como tf * idf
        normalizacion_tf = max(t_frecuencias.values())
        for termino, pos in self.modelo['terminos'].items():
            tf = t_frecuencias.get(termino, 0) / normalizacion_tf
            vector[pos] = tf
            vector[pos] *= self.modelo['relevancia_idf'][pos]
        return vector

    def frecuencias_terminos(self, path):
        with open(path, 'r') as f:
            # Primero, leer todo el fichero, y pasar a minúsculas
            texto = ' '.join(f.readlines())
        # Quitar caracteres no deseados
        texto = self.re_caracteres.sub('', texto)
        # Parsear texto resultante con spacy
        doc = self.parser(texto)
        # Filtrar sustantivos y nombres propios
        palabras = []
        acarreo_nom_propios = []
        acarreo_det_preps = []
        for palabra in doc:
            if palabra.pos_ == 'NOUN':
                # Reforzar generalización guardando solamente lematización
                palabras.append(self.re_alfa.sub('', palabra.lemma_.lower()))
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
                    palabras.append(
                        self.re_alfa.sub('', '-'.join(acarreo_nom_propios)))
                    acarreo_nom_propios = []
        # Por si quedaba pendiente el parseo de un nombre propio
        if acarreo_nom_propios:
            palabras.append(
                self.re_alfa.sub('', '-'.join(acarreo_nom_propios)))
        # Quitar palabras vacias
        palabras = list(
            filter(lambda p: p not in self.palabras_vacias, palabras))
        return Counter(palabras)

    def compilar(self):
        # Generar compilacion
        out = {}
        frecs_fich = {}
        frecs_tema = {}
        # Obtener terminos y frecuencias absolutas según tema y fichero
        terminos = set()
        for tema, textos in self.part['train'].items():
            path_tema = os.path.join(self.d_docs, tema)
            texto_a_tabla = frecs_fich.setdefault(tema, {})
            for texto in textos:
                path_texto = os.path.join(path_tema, texto)
                conteos_texto = self.frecuencias_terminos(path_texto)
                texto_a_tabla[texto] = conteos_texto
            cont_tema = reduce(lambda a,b: a+b, frecs_fich[tema].values())
            frecs_tema[tema] = cont_tema
            terminos.update(cont_tema.keys())
        out['terminos'] = {k:v for v,k in enumerate(terminos)}

        # Generar máscara idf para cada palabra
        relevancias_idf = np.empty(len(terminos))
        total_documentos = sum(len(self.part['train'][t]) for t in self.temas)
        for termino, pos in out['terminos'].items():
            total_aparic = sum(int(termino in tabla)
                               for t in self.temas
                               for tabla in frecs_fich[t].values())
            relevancias_idf[pos] = np.log10(total_documentos / total_aparic)

        # Generar máscar tf para cada tema
        relevancia_tf = {}
        for tema, frecuencias in frecs_tema.items():
            normalizacion_tf = max(frecuencias.values())
            rel_tf_t = relevancia_tf.setdefault(tema, np.zeros(len(terminos)))
            for termino, pos in out['terminos'].items():
                rel_tf_t[pos] = frecuencias.get(termino, 0) / normalizacion_tf

        # Generar vectores tf-idf para cada tema
        out['vectores_tf_idf'] = {
            tema: (relevancia_tf[tema]*relevancias_idf).tolist()
            for tema in self.temas}
        out['relevancia_idf'] = relevancias_idf.tolist()

        # Exportar a json
        with open(self.f_compilacion, 'w') as f:
            json.dump(out, f, indent=2)
        self.modelo = out


if __name__ == '__main__':
    c = ClasificadorTfIdf()
    # c.compilar()
    c.test()
