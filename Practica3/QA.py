import json
from unidecode import unidecode
import spacy as spa

class Concepto:
    def __init__(self, terminos, tipo_pregunta, valor):
        self.terminos = terminos
        self.tipo_pregunta = tipo_pregunta
        self.valor = valor
        self.s_terminos = 0
        self.s_tipo_pregunta = 0

    def __str__(self):
        return (f'{self.terminos}:{self.s_terminos}, {self.tipo_pregunta}'
                f':{self.s_tipo_pregunta}, {self.valor}\n')


class ConceptoGeneral:
    def __init__(self, termino, prioridad):
        self.termino = termino
        self.prioridad = prioridad
        self.score = 0

    def __str__(self):
        return f'{self.termino}:{self.score}, {self.prioridad}\n'

    def __lt__(self, other):
        if self.score == other.score:
            return self.prioridad > other.prioridad
        return self.score < other.score


class QA:

    TP_CUAL = 'cual'
    TP_CUANTO = 'cuanto'
    TP_DE_CUANTO = 'de cuanto'
    TP_TIENE = 'tiene'
    TP_AGRUPACION = 'agrupacion'

    # Plantillas para respuestas
    respuestas = {
        TP_CUAL: '{descripcion} del monitor {modelo} es {valor}.',
        TP_CUANTO: 'El monitor {modelo} tiene {valor} {descripcion}.',
        TP_DE_CUANTO: '{descripcion} del monitor {modelo} es de {valor}.',
        TP_TIENE: 'El monitor {modelo} {valor}tiene {descripcion}.',
        TP_AGRUPACION:
            'Esto es lo que sé sobre {descripcion} para el monitor {modelo}:',
    }
    

    def __init__(self, f_tesauro='Datos/etiquetas.json',
                 f_preguntas='Datos/preguntasGlobales.json',
                 f_verbose='Datos/verbose.json', f_bd='Datos/database.json'):
        with open(f_tesauro, 'r') as f:
            self.tesauro = json.load(f)
        with open(f_verbose, 'r') as f:
            self.verbose = json.load(f)
        with open(f_bd, 'r') as f:
            self.bd = json.load(f)
        with open(f_preguntas, 'r') as f:
            self.pg = json.load(f)
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
            self.tesauro[terminos[i]], palabras)
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

    def fn_pesos_unos(self, concepto):
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

    @staticmethod
    def get_by_keys(dic, keys, default=None):
        """
        Obtiene el valor de un diccionario compuesto a su vez más diccionarios, 
        dado un conjunto de claves
        Args:
            keys ([str]): Claves ordenadas por oden de apliación
            default: Valor por defecto en caso de que no exista una clave

        Returns:
            str: Texto del valor buscado en el diccionario
        """
        for k in keys:
            dic = dic.get(k, default)
            if type(dic) != dict:
                return dic
        return dic

    def respuesta_concepto(self, concepto, n_modelo):
        """
        Genera la respuesta a una pregunta dado un concepto y un modelo
        específico
        Args:
            concepto (Concepto): Concepto
            n_modelo (str): Nombre del modelo por el que se pregunta

        Returns:
            str: Texto con la respuesta generada
        """
        descripcion = self.get_by_keys(self.verbose, concepto.terminos)
        if type(descripcion) == dict:
            descripcion = self.verbose['conceptosGen'][concepto.terminos[-1]]
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

    def listar_conceptos_gen(self):
        """
        Lista el conjunto de conceptos generales
        Args:

        Returns:
            [ConceptoGeneral]: Cada uno de los conceptos generales
        """
        l = []
        for k, v in self.pg['conceptosGen'].items():
            l.append(ConceptoGeneral(k, v))
        return l
            
    def scores_conceptos_gen(self, palabras):
        """
        Indica la puntuación de cada uno de los conceptos generales
        Args:
            palabras ([str]): Lista de las palabras que contenía la pregunta

        Returns:
            [ConceptoGeneral]: Cada uno de los conceptos generales con sus 
            respectivos scores
        """
        conceptos_gen = self.listar_conceptos_gen()
        for c in conceptos_gen:
            c.score = self.score_etiquetas(self.tesauro[c.termino], palabras)
        conceptos_gen.sort(reverse=True)
        return conceptos_gen

    def responder_pregunta(self, texto, fn_pesos=None):
        if fn_pesos is None:
            fn_pesos = self.fn_pesos_unos
        palabras = self.parsear_palabras(texto)
        n_modelo = self.detectar_modelo(palabras)
        modelo = self.bd[n_modelo] if n_modelo else None
        if modelo is not None:
            conceptos = self.scores_conceptos(palabras, modelo, fn_pesos)
            s_0 = conceptos[0].s_terminos
            if s_0 <= 0.5:
                return 'Perdón, no te he entendido'
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
            # Desambiguar por agrupación de conceptos
            conceptos_gen = self.scores_conceptos_gen(palabras)
            c_1, c_2 = conceptos_gen[0], conceptos_gen[1]
            # Pregunta demasiado ambigua
            if c_1.score == c_2.score and c_1.prioridad == c_2.prioridad:
                return 'Perdón, no te he entendido'
            descripcion = self.verbose['conceptosGen'][c_1.termino]
            ret = self.respuestas[self.TP_AGRUPACION].format(
                modelo=n_modelo, descripcion=descripcion
            )
            for c in candidatos:
                if c_1.termino in c.terminos:
                    ret = ret + f'\n\t{self.respuesta_concepto(c, n_modelo)}'
            return ret

if __name__ == '__main__':
    
    qa = QA()
    while True:
        entrada = input('\nIntroduce una pregunta: ')
        respuesta = qa.responder_pregunta(entrada)
        print(respuesta)
        