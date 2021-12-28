import json
from unidecode import unidecode
import spacy as spa

class Concepto:
    def __init__(self, terminos, tipo_pregunta, valor):
        self.terminos = terminos
        self.tipo_pregunta = tipo_pregunta
        self.valor = valor

    def __str__(self):
        return (f'{self.terminos}:{self.s_terminos}, {self.tipo_pregunta}'
                f':{self.s_tipo_pregunta}, {self.valor}\n')


class QA:

    TP_CUAL = 'cual'
    TP_CUANTO = 'cuanto'
    TP_DE_CUANTO = 'de cuanto'
    TP_TIENE = 'tiene'

    # Plantillas para respuestas
    respuestas = {
        TP_CUAL: '{descripcion} del monitor {modelo} es {valor}.',
        TP_CUANTO: 'El monitor {modelo} tiene {valor} {descripcion}.',
        TP_DE_CUANTO: '{descripcion} del monitor {modelo} es de {valor}.',
        TP_TIENE: 'El monitor {modelo} {valor}tiene {descripcion}.'
    }
    

    def __init__(self, f_tesauro='terminos.json', f_bd='Datos/database.json'):
        with open(f_tesauro, 'r') as f:
            self.tesauro = json.load(f)
        with open(f_bd, 'r') as f:
            self.bd = json.load(f)
        self.parser = spa.load('es_core_news_md')

    def score_etiqueta(self, etiqueta, palabras):
        """
        Indica la puntuación de una etiqueta en una frase como la proporción de
        términos de la etiqueta que se han verificado

        Args:
            etiqueta (string): Forma de describir un concepto
            palabras ([string]): Lista de palabras de la frase a probar

        Returns:
            int: Puntuación de la etiqueta en la frase
        """    
        subetiquetas = etiqueta.split()
        return sum(int(e in palabras) for e in subetiquetas)/len(subetiquetas)


    def score_etiquetas(self, etiquetas, palabras):
        """
        Indica la puntuación de un conjunto de etiquetas para una frase rota en
        palabras, donde se devuelve la puntuación máxima de cualquiera de las
        etiquetas.

        Args:
            etiqueta ([string]): Formas distintas de describir un concepto
            palabras ([string]): Lista de palabras de la frase a probar

        Returns:
            int: Puntuación del ajuste de unas etiquetas a una frase
        """
        return max(self.score_etiqueta(e, palabras) for e in etiquetas)


    def score_terminos(self, terminos, pesos, palabras):
        """
        Indica la puntuación asociada a un conjunto de términos que describen
        un concepto, dados unos pesos que indican la relevancia de cada
        término.
        Args:
            terminos ([string]): Términos en orden decreciente de generalidad
            pesos ([float]): Pesos de cada término
            palabras ([string]): Palabras cuya relación con los términos se va
            a puntuar.

        Returns:
            [float]: Puntuación final de las palabras
        """
        return sum(
            pesos[i] * self.score_etiquetas(
            self.tesauro[terminos[i]]['etiquetas'], palabras)
            for i in range(len(terminos)))


    def parsear_palabras(self, texto):
        """
        Dado un pregunta, se tokeniza, se eliminan los signos de puntuación, y
        se transforman todas las palabras a minúsculas eliminandose los acentos
        Args:
            texto (str): El texto que contiene la pregunta a ser respondida

        Returns:
            [str]: Lista de las palabras que contenía la pregunta
        """
        return [
            unidecode(w.lemma_.lower()) for w in self.parser(texto)
            if w.pos_ != 'PUNCT'
        ]

    def detectar_modelo(self, palabras):
        """
        Indica el modelo del monitor por el que se pregunta

        Args:
            palabras ([string]): Palabras de la pregunta

        Returns:
            [type]: [description]
        """        
        return '27UP850-W'

    def listar_conceptos_modelo(self, modelo):
        """
        Lista el conjunto de conceptos que posee un modelo específico
        Args:
            modelo (dict): Diccionario del modelo del que extraer sus conceptos

        Yields:
            Concepto: Instancia de Concepto que contiene los terminos, el tipo
            de pregunta y su valor específico
        """  
        for k, v in modelo.items():
            for ks in self._listar_conceptos_modelo_rec(v):
                ks.insert(0, k)
                yield Concepto(ks[:-2], ks[-2], ks[-1])

    def _listar_conceptos_modelo_rec(self, dic):
        """
        Recorrido recursivo por un diccionario en profundidad
        Args:
            dic ([dict]): Diccionario de diccionarios

        Yields:
            [str]: recorrido en profundidad por claves del diccionario
        """        
        if type(dic) != dict:
            yield [dic]
        else:
            for k, v in dic.items():
                for ks in self._listar_conceptos_modelo_rec(v):
                    ks.insert(0, k)
                    yield ks

    def scores_conceptos(self, palabras, modelo, fn_pesos):
        """
        Indica la puntuación de cada uno de los conceptos diferenciando entre
        el score de sus términos y de su tio de pregunta.
        Args:
            palabras ([str]): Lista de las palabras que contenía la pregunta
            modelo (dict): Diccionario del modelo de consulta
            fn_pesos (function): Función que genera una lista de pesos para los
            términos dado un concepto

        Returns:
            [Concepto]: Lista de los conceptos, que contienen adicionalmente
            las puntuaciones calculadas
        """   
        conceptos = []
        for c in self.listar_conceptos_modelo(modelo):
            pesos = fn_pesos(c)
            c.s_terminos = self.score_terminos(c.terminos, pesos, palabras)
            c.s_tipo_pregunta = self.score_terminos([c.tipo_pregunta], [1],
                                                    palabras)
            # c.s_valor = self.score_terminos([c.valor])
            conceptos.append(c)
        conceptos.sort(key=lambda c: -1 * c.s_terminos)
        return conceptos

    def fn_pesos_exp(self, concepto):
        """
        Generador de pesos para cada termino de un concepto con decrecimiento
        exponencial
        Args:
            concepto (Concepto): Concepto

        Returns:
            [float]: Lista de pesos de cada termino de un conpeto
        """   
        return [1.0] * len(concepto.terminos)

    def terminos_comunes(self, c_1, c_2):
        comun = []
        for t_1, t_2 in zip(c_1.terminos, c_2.terminos):
            if t_1 == t_2:
                comun.append(t_1)
            else:
                break
        return comun

    def respuesta_concepto(self, concepto, n_modelo):
        descripcion = self.tesauro[concepto.terminos[-1]]['verbose']
        valor = concepto.valor
        modelo = n_modelo
        if concepto.tipo_pregunta == self.TP_TIENE:
            if type(concepto.valor) == bool:
                valor = ('no ', '')[int(concepto.valor)]
            else:
                descripcion = descripcion + ' ' + valor
                valor = ''
        return self.respuestas[concepto.tipo_pregunta].format(
            descripcion=descripcion, modelo=modelo, valor=valor)

    def responder_pregunta(self, texto, fn_pesos=None):
        if fn_pesos is None:
            fn_pesos = self.fn_pesos_exp
        palabras = self.parsear_palabras(texto)
        n_modelo = self.detectar_modelo(palabras)
        modelo = self.bd[n_modelo] if n_modelo else None
        if modelo is not None:  # Pregunta sobre modelo concreto
            conceptos = self.scores_conceptos(palabras, modelo, fn_pesos)
            s_0 = conceptos[0].s_terminos
            if s_0 > 0.5:
                # Comprobar si hay empates
                candidatos = [c for c in conceptos if c.s_terminos == s_0]
                if len(candidatos) == 1:
                    return self.respuesta_concepto(candidatos[0], n_modelo)
                # Intentar desambiguar por el tipo de pregunta
                candidatos.sort(key=lambda c: -1 * c.s_tipo_pregunta)
                s_0_tp = candidatos[0].s_tipo_pregunta
                candidatos = [c for c in candidatos
                                if c.s_tipo_pregunta == s_0_tp]
                if len(candidatos) == 1:
                    return self.respuesta_concepto(candidatos[0], n_modelo)
                else:  # Responder por concepto general
                    min_terminos = min(len(c.terminos) for c in candidatos)
                    candidatos = [c for c in candidatos
                                  if len(c.terminos) == min_terminos]
                    if len(candidatos) == 1:
                        return self.respuesta_concepto(candidatos[0], n_modelo)
                    comun = self.terminos_comunes(candidatos[0], candidatos[1])
                    if not comun:
                        return 'Perdón, no te he entendido'
                    grado_generalidad = len(comun)/len(candidatos[0].terminos)
                    ret = ''
                    if grado_generalidad <= 0.5:
                        ret = 'No estoy seguro de haber entendido tu pregunta. '
                    dic = modelo
                    for t in comun:
                        dic = dic[t]
                    concepto_gen = self.tesauro[comun[-1]]['verbose']
                    concepto_gen = concepto_gen[0].lower() + concepto_gen[1:]
                    ret = f'{ret}Esto es lo que se sobre {concepto_gen}:'
                    for c in self.listar_conceptos_modelo(dic):
                        ret = ret + f'\n{self.respuesta_concepto(c, n_modelo)}'
                    return ret
            else:
                return 'Perdón, no te he entendido'

if __name__ == '__main__':
    
    qa = QA()
    while True:
        entrada = input('\nIntroduce una pregunta: ')
        respuesta = qa.responder_pregunta(entrada)
        print(respuesta)
        