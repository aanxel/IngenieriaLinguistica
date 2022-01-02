import json
from os import EX_PROTOCOL
import spacy as spa
import editdistance
import regex as re
from spanishconjugator import Conjugator
from thinc.config import VARIABLE_RE

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

    def __lt__(self, other):
        return self.s_terminos < other.s_terminos


class ConceptoGlobal:
    def __init__(self, terminos, tipo_pregunta, prioridad):
        self.terminos = terminos
        self.tipo_pregunta = tipo_pregunta
        self.prioridad = prioridad
        self.s_terminos = 0

    def __str__(self):
        return (f'{self.terminos}:{self.s_terminos}, {self.tipo_pregunta}, '
                f'{self.prioridad}\n')

    def __lt__(self, other):
        if self.s_terminos == other.s_terminos:
            return self.prioridad > other.prioridad
        return self.s_terminos < other.s_terminos


class ConceptoGrupo:
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

    # Preguntas específicas
    TP_CUAL = 'cual'
    TP_CUANTO = 'cuanto'
    TP_DE_CUANTO = 'de cuanto'
    TP_TIENE = 'tiene'

    # Preguntas generales
    TP_AGRUPACION = 'agrupacion'
    TP_LISTAR_MODELOS = 'listar_modelos'
    TP_LISTAR_PANELES = 'listar_paneles'
    TP_LISTAR_RESOLUCIONES = 'listar_resoluciones'
    TP_LISTAR_CURVAS = 'listar_curvas'
    TP_MAX_VALORACION = 'modelo_valoracion_maxima'
    TP_SALUDO = 'saludar'
    TP_DESPDEDIDA = 'salir'

    # Detección de modelos
    RET_VARIOS_MODELOS = 1
    RET_NO_HAY_MODELO = 2
    RET_UN_MODELO_ERRATA = 3
    
    # Respuestas erroneas o con inseguridad
    R_MOD_NO_ENTIENDO = 'r_mod_no_entiendo'
    R_NO_ENTIENDO = 'r_no_entiendo'
    R_NO_SEGURO = 'r_no_seguro'

    # Distancia de edición máxima para matchear palabras
    MAX_ED = 1

    # Plantillas para respuestas
    respuestas = {
        TP_CUAL: '{descripcion} del monitor {modelo} es {valor}.',
        TP_CUANTO: 'El monitor {modelo} tiene {valor} {descripcion}.',
        TP_DE_CUANTO: '{descripcion} del monitor {modelo} es de {valor}.',
        TP_TIENE: 'El monitor {modelo} {valor}tiene {descripcion}.',
        TP_AGRUPACION:
            'Esto es lo que sé sobre {descripcion} para el monitor {modelo}:',
        RET_VARIOS_MODELOS:
            'He detectado una pregunta sobre varios modelos de monitor: '
            '{}. Por favor, limita tu pregunta a un modelo.',
        RET_UN_MODELO_ERRATA: 'Si te refieres al modelo {n_modelo}:\n{resto}',
        R_MOD_NO_ENTIENDO: 'Lo siento, '
            'no dispongo de esa información para el modelo {}',
        R_NO_ENTIENDO:
            'Lo siento, no he entendido tu pregunta.',
        R_NO_SEGURO:
            'No estoy seguro de que me hayas preguntado esto, pero {}',
        TP_LISTAR_MODELOS: 'Este es el listado de modelos:{}',
        TP_LISTAR_PANELES: 'Este es el listado de modelos con tipo de panel '
            '{descripcion}:{resto}',
        TP_LISTAR_RESOLUCIONES: 'Este es el listado de modelos con resolución '
            '{descripcion}:{resto}',
        TP_LISTAR_CURVAS: 'Este es el listado de modelos con pantalla '
            '{descripcion}:{resto}',
        TP_MAX_VALORACION: 'El monitor {n_modelo} cuenta con la mejor '
            'valoración: {descripcion}',
        TP_SALUDO: 'Hola, soy Alexo, pregúntame lo que quieras '
            'sobre los monitores de la tienda.',
        TP_DESPDEDIDA: 'Hasta otra, un placer haberte ayudado.'
    }
    

    def __init__(self, f_tesauro='Datos/etiquetas.json',
                 f_preguntas='Datos/preguntasGenerales.json',
                 f_verbose='Datos/verbose.json', f_bd='Datos/database.json'):
        with open(f_tesauro, 'r') as f:
            self.tesauro = json.load(f)
            self.expandir_tesauro()
        with open(f_verbose, 'r') as f:
            self.verbose = json.load(f)
        with open(f_bd, 'r') as f:
            self.bd = json.load(f)
        with open(f_preguntas, 'r') as f:
            self.pg = json.load(f)
        self.parser = spa.load('es_core_news_md')
        self.resp_lambda = {
            self.TP_LISTAR_MODELOS: self.cb_listar_modelos,
            self.TP_MAX_VALORACION: self.cb_modelo_recomendado,
            self.TP_LISTAR_PANELES: self.cb_listar_paneles,
            self.TP_LISTAR_RESOLUCIONES: self.cb_listar_resoluciones,
            self.TP_LISTAR_CURVAS: self.cb_listar_curvas,
            self.TP_SALUDO: lambda *args: self.respuestas[self.TP_SALUDO],
            self.TP_DESPDEDIDA:
                lambda *args: self.respuestas[self.TP_DESPDEDIDA]
        }

    @staticmethod
    def quitar_ac(p):
        p = re.sub('[áÁ]', 'a', p)
        p = re.sub('[éÉ]', 'e', p)
        p = re.sub('[íÍ]', 'i', p)
        p = re.sub('[óÓ]', 'o', p)
        p = re.sub('[úÚ]', 'u', p)
        return p

    def expandir_tesauro(self):
        """
        Modifica el tesauro para transformar todos aquellos verbos en
        infinitivo que comienzan por _ por sus conjugaciones en imperativo

        Args:

        Returns:

        """
        personas = ('tu', 'usted')
        conjugaciones = [
            ('affirmative', 'imperative'),
            ('negative', 'imperative'),
            ('present', 'indicative'),
            ('present', 'indicative'),
            ('simple_conditional', 'conditional'),
        ]
        conj = Conjugator()
        for termino, etiquetas in self.tesauro.items():
            n_etiquetas = []
            for e in etiquetas:
                if type(e) != list:
                    e = [e, 1.0]
                if e[0].startswith('_'):
                    e[0] = e[0][1:]
                    n_etiquetas.append(e)
                    for p in personas:
                        for c in conjugaciones:
                            nuevo = conj.conjugate(e[0],
                                        *(c + (p,))).replace('ñ', '.')
                            
                            n_etiquetas.append([
                                self.quitar_ac(bytes(nuevo, 'latin-1').decode(
                                    'utf-8').replace('.', 'ñ')),
                                e[1]])
                else:
                    n_etiquetas.append(e)
            self.tesauro[termino] = n_etiquetas

    def score_etiqueta(self, etiqueta, palabras, umbral_ed=0):
        """
        Indica la puntuación de una etiqueta en una frase como la proporción de
        términos de la etiqueta que se han verificado

        Args:
            etiqueta (string): Forma de describir un concepto
            palabras ([string]): Lista de palabras de la frase a probar
            umbral_ed (int): Máxima distancia de edición permitida

        Returns:
            int: Puntuación de la etiqueta en la frase
        """    
        subetiquetas = etiqueta[0].split()
        score = 0
        for e in subetiquetas:
            ed = min(editdistance.eval(e, p) for p in palabras)
            if (ed <= umbral_ed and len(e) >= 5) or ed == 0:
                score += 1
        return etiqueta[1] if score == len(subetiquetas) else 0


    def score_etiquetas(self, etiquetas, palabras, umbral_ed=0):
        """
        Indica la puntuación de un conjunto de etiquetas para una frase rota en
        palabras, donde se devuelve la puntuación máxima de cualquiera de las
        etiquetas.

        Args:
            etiqueta ([string]): Formas distintas de describir un concepto
            palabras ([string]): Lista de palabras de la frase a probar
            umbral_ed (int): Máxima distancia de edición permitida

        Returns:
            int: Puntuación del ajuste de unas etiquetas a una frase
        """
        if not etiquetas:
            return 0
        return max(self.score_etiqueta(e, palabras, umbral_ed)
                   for e in etiquetas)


    def score_terminos(self, terminos, pesos, palabras, umbral_ed=0):
        """
        Indica la puntuación asociada a un conjunto de términos que describen
        un concepto, dados unos pesos que indican la relevancia de cada
        término.
        Args:
            terminos ([string]): Términos en orden decreciente de generalidad
            pesos ([float]): Pesos de cada término
            palabras ([string]): Palabras cuya relación con los términos se va
            a puntuar.
            umbral_ed (int): Máxima distancia de edición permitida

        Returns:
            [float]: Puntuación final de las palabras
        """
        return sum(
            pesos[i] * self.score_etiquetas(
            self.tesauro[terminos[i]], palabras, umbral_ed)
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
        doc = self.parser(texto)
        ret = []
        for w in doc:
            if w.pos_ != 'PUNCT':
                if w.pos_ == 'VERB' and str(w).endswith('me'):
                    ret.append(str(w)[:-2])
                elif w.pos_ == 'VERB' and str(w).endswith('nos'):
                    ret.append(str(w)[:-3])
                else:
                    ret.append(w.lemma_)
                ret.append(str(w))
        return list(set(map(lambda p: self.quitar_ac(p.lower()), ret)))

    def detectar_modelo(self, palabras):
        """
        Indica el modelo del monitor por el que se pregunta y el tipo de error
        en caso de que se detecte

        Args:
            palabras ([string]): Palabras de la pregunta

        Returns:
            (str, int): Nombre del modelo o None en caso de que no se detecte ninguno y
            el tipo de error asociado
        """
        lista_modelos = self.bd.keys()
        lista_candidatos = []
        errata = 0
        for modelo in lista_modelos:
            modelo_lower = modelo.lower()
            for p in palabras:
                dist = editdistance.eval(modelo_lower, p)
                if dist <= 2:
                    lista_candidatos.append(modelo)
                    errata = max(errata, dist)
        lista_candidatos = list(set(lista_candidatos))
        if len(lista_candidatos) == 1 and errata == 0:
            return lista_candidatos[0], None
        elif len(lista_candidatos) == 1 and errata <= 2:
            return lista_candidatos[0], self.RET_UN_MODELO_ERRATA
        elif len(lista_candidatos) >= 2:
            return lista_candidatos, self.RET_VARIOS_MODELOS
        elif len(lista_candidatos) == 0:
            return None, self.RET_NO_HAY_MODELO

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
            for ks in self._listar_dic_rec(v):
                ks.insert(0, k)
                yield Concepto(ks[:-2], ks[-2], ks[-1])

    def listar_conceptos_globales(self):
        for k, v in self.pg['global'].items():
            for ks in self._listar_dic_rec(v):
                ks.insert(0, k)
                yield ConceptoGlobal(ks[:-2], ks[-2], ks[-1])

    def _listar_dic_rec(self, dic):
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
                for ks in self._listar_dic_rec(v):
                    ks.insert(0, k)
                    yield ks

    def scores_conceptos(self, palabras, modelo, fn_pesos, umbral_ed=0):
        """
        Indica la puntuación de cada uno de los conceptos diferenciando entre
        el score de sus términos y de su tio de pregunta.
        Args:
            palabras ([str]): Lista de las palabras que contenía la pregunta
            modelo (dict): Diccionario del modelo de consulta
            fn_pesos (function): Función que genera una lista de pesos para los
            términos dado un concepto
            umbral_ed (int): Máxima distancia de edición permitida

        Returns:
            [Concepto]: Lista de los conceptos, que contienen adicionalmente
            las puntuaciones calculadas
        """
        conceptos = []
        for c in self.listar_conceptos_modelo(modelo):
            pesos = fn_pesos(c)
            c.s_terminos = self.score_terminos(c.terminos, pesos, palabras,
                                               umbral_ed)
            c.s_tipo_pregunta = self.score_terminos([c.tipo_pregunta], [1],
                                                    palabras, umbral_ed)
            conceptos.append(c)
        conceptos.sort(reverse=True)
        return conceptos

    def scores_conceptos_global(self, palabras, fn_pesos, umbral_ed=0):
        """
        Indica la puntuación de cada uno de los conceptos globales y su 
        prioridad
        Args:
            palabras ([str]): Lista de las palabras que contenía la pregunta
            fn_pesos (function): Función que genera una lista de pesos para los
            términos dado un concepto
            umbral_ed (int): Máxima distancia de edición permitida

        Returns:
            [ConceptoGlobal]: Lista de los conceptos globales, que contienen
            adicionalmente las puntuaciones calculadas
        """
        conceptos = []
        for c in self.listar_conceptos_globales():
            pesos = fn_pesos(c)
            c.s_terminos = self.score_terminos(c.terminos, pesos, palabras,
                                               umbral_ed)
            conceptos.append(c)
        conceptos.sort(reverse=True)
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
        idx = concepto.terminos + [concepto.tipo_pregunta]
        descripcion = self.get_by_keys(self.verbose, idx)
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
            [ConceptoGrupo]: Cada uno de los conceptos generales
        """
        l = []
        for k, v in self.pg['grupos'].items():
            l.append(ConceptoGrupo(k, v))
        return l
            
    def scores_conceptos_gen(self, palabras, umbral_ed=0):
        """
        Indica la puntuación de cada uno de los conceptos generales
        Args:
            palabras ([str]): Lista de las palabras que contenía la pregunta
            umbral_ed (int): Máxima distancia de edición permitida

        Returns:
            [ConceptoGrupo]: Cada uno de los conceptos generales con sus 
            respectivos scores
        """
        conceptos_gen = self.listar_conceptos_gen()
        for c in conceptos_gen:
            terminos = c.termino.split('&')
            c.score = 0
            for t in terminos:
                if self.score_etiquetas(self.tesauro[t], palabras) > 0:
                    c.score += 1
            c.score /= len(terminos)
        conceptos_gen.sort(reverse=True)
        return conceptos_gen

    def _concepto_tiene_terminos(self, concepto, terminos):
        try:
            resto = concepto.terminos[concepto.terminos.index(terminos[0])+1:]
            return not terminos[1:] or resto == terminos[1:]
        except ValueError:
            return False

    def respuesta_modelo(self, modelo, n_modelo, palabras, fn_pesos,
                         umbral_ed=0):
        conceptos = self.scores_conceptos(palabras, modelo, fn_pesos,
                                          umbral_ed)
        s_0 = conceptos[0].s_terminos
        if not s_0:
            if umbral_ed >= self.MAX_ED:
                return (self.respuestas[self.R_MOD_NO_ENTIENDO].format(
                    n_modelo))        
            r = self.respuesta_modelo(modelo, n_modelo, palabras, fn_pesos,
                                      umbral_ed + 1)
            return self._respuesta_insegura_ed(r)
        # Comprobar si hay empates
        candidatos = [c for c in conceptos if c.s_terminos == s_0]
        if len(candidatos) == 1:
            return self.respuesta_concepto(candidatos[0], n_modelo)
        # Intentar desambiguar por el tipo de pregunta
        if all(t.terminos[:-1] == candidatos[0].terminos[:-1] for t in candidatos):
            candidatos.sort(key=lambda c: c.s_tipo_pregunta, reverse=True)
            s_0_tp = candidatos[0].s_tipo_pregunta
            candidatos = [c for c in candidatos if c.s_tipo_pregunta == s_0_tp]
            if len(candidatos) == 1:
                return self.respuesta_concepto(candidatos[0], n_modelo)
        # Desambiguar por agrupación de conceptos
        conceptos_gen = self.scores_conceptos_gen(palabras)
        c_1, c_2 = conceptos_gen[0], conceptos_gen[1]
        # Pregunta demasiado ambigua
        if c_1.score == c_2.score and c_1.prioridad == c_2.prioridad:
            if umbral_ed >= self.MAX_ED:
                return (self.respuestas[self.R_MOD_NO_ENTIENDO].format(
                        n_modelo))        
            r = self.respuesta_modelo(modelo, n_modelo, palabras, fn_pesos,
                                      umbral_ed + 1)
            return self._respuesta_insegura_ed(r)
        descripcion = self.verbose['_gen'][c_1.termino]
        ret = self.respuestas[self.TP_AGRUPACION].format(
            modelo=n_modelo, descripcion=descripcion)
        for c in conceptos:
            if self._concepto_tiene_terminos(c, c_1.termino.split('&')):
                ret = ret + f'\n\t{self.respuesta_concepto(c, n_modelo)}'
        return self._respuesta_insegura(c_1, ret)

    def _respuesta_insegura(self, concepto, contenido):
        if concepto.prioridad < 3:
            return contenido
        r = contenido
        re_mod = self.respuestas[self.R_MOD_NO_ENTIENDO].format('*')
        if not(re.match(re_mod, r) or
               any(_r in r for _r in (self.respuestas[self.R_NO_SEGURO],
                                      self.respuestas[self.R_NO_ENTIENDO]))):
            r = self.respuestas[self.R_NO_SEGURO].format(r[0].lower() + r[1:])
        return r

    def _respuesta_insegura_ed(self, r):
        re_mod = self.respuestas[self.R_MOD_NO_ENTIENDO].format('*')
        if not(re.match(re_mod, r) or
               any(_r in r for _r in (self.respuestas[self.R_NO_SEGURO],
                                      self.respuestas[self.R_NO_ENTIENDO]))):
            r = self.respuestas[self.R_NO_SEGURO].format(r[0].lower() + r[1:])
        return r

    def respuesta_global(self, palabras, fn_pesos, umbral_ed=0):
        conceptos = self.scores_conceptos_global(palabras, fn_pesos, umbral_ed)
        c_1, c_2 = conceptos[0], conceptos[1]
        if (  # No se ha detectado una pregunta o pregunta ambigua
          c_1.s_terminos <= 0.0 or 
          c_1.s_terminos == c_2.s_terminos and c_1.prioridad == c_2.prioridad):
            if umbral_ed >= self.MAX_ED:
                return self.respuestas[self.R_NO_ENTIENDO]
            r = self.respuesta_global(palabras, fn_pesos, umbral_ed + 1)
            return self._respuesta_insegura_ed(r)
            
        return self.resp_lambda[c_1.tipo_pregunta](c_1, palabras)

    def cb_listar_modelos(self, concepto, *args):
        return self._respuesta_insegura(concepto,
            self.respuestas[self.TP_LISTAR_MODELOS].format(
                '\n\t- ' + ('\n\t- '.join(self.bd.keys()))))

    def cb_modelo_recomendado(self, concepto, *args):
        puntuaciones = []
        for m, c in self.bd.items():
            val = self.get_by_keys(c, ('valoracion', self.TP_DE_CUANTO), None)
            if val is not None:
                # https://tinyurl.com/2p8bcyhu
                puntuaciones.append(
                    (float(re.findall(r"[-+]?\d*\.\d+|\d+", val)[0]), val, m))
            else:
                puntuaciones.append(-1, 'no disponible', m)
        puntuaciones.sort(key=lambda p: p[0], reverse=True)
        ret = self.respuestas[self.TP_MAX_VALORACION].format(
            n_modelo=puntuaciones[0][2],descripcion=puntuaciones[0][1],
        )
        return self._respuesta_insegura(concepto, ret)

    def cb_listar_paneles(self, concepto, *args):
        tipo_panel = next(
            (x for x in concepto.terminos if x.startswith('_')), None)
        monitores = []
        for m, c in self.bd.items():
            val = self.get_by_keys(c, ('pantalla', 'tipoPanel', 'cual'), None)
            if val and self.score_etiquetas(self.tesauro[tipo_panel],
              [''.join(val.lower().split())], self.MAX_ED) >= 1:
                monitores.append(m)
        if len(monitores) == 0:
            resto = '\n\tLo siento, no tenemos monitores con ese tipo de panel'
        else:
            resto = '\n\t- ' + ('\n\t- '.join(monitores))
        return self._respuesta_insegura(concepto,
            self.respuestas[self.TP_LISTAR_PANELES].format(
                descripcion=self.verbose['_gen'][tipo_panel], resto=resto))

    def cb_listar_resoluciones(self, concepto, *args):
        tipo_resolucion = next(
            (x for x in concepto.terminos if x.startswith('_')), None)
        monitores = []
        for m, c in self.bd.items():
            val = self.get_by_keys(c, ('pantalla', 'resolucion', 'de cuanto'),
                                   None)
            if val and any(e[0] in ''.join(val.lower().split())
                           for e in self.tesauro[tipo_resolucion]):
                monitores.append(m)
        if len(monitores) == 0:
            resto = '\n\tLo siento, no tenemos monitores con esa resolución'
        else:
            resto = '\n\t- ' + ('\n\t- '.join(monitores))
        return self._respuesta_insegura(concepto,
            self.respuestas[self.TP_LISTAR_RESOLUCIONES].format(
              descripcion=self.verbose['_gen'][tipo_resolucion], resto=resto))

    def cb_listar_curvas(self, concepto, palabras, *args):
        tipo_curva = next(
            (x for x in concepto.terminos if x.startswith('_')), None)
        if any(e[0] in palabras for e in self.tesauro['no']):
            if tipo_curva == '_curva':
                tipo_curva = '_plana'
            else:
                tipo_curva = '_curva'
        monitores = []
        for m, c in self.bd.items():
            val = self.get_by_keys(c, ('pantalla', 'curva', 'tiene'), None)
            if (val and tipo_curva == '_curva' or
                val is False and tipo_curva == '_plana'):
                monitores.append(m)
        if len(monitores) == 0:
            resto = '\n\tLo siento, no tenemos monitores de ese tipo.'
        else:
            resto = '\n\t- ' + ('\n\t- '.join(monitores))
        return self._respuesta_insegura(concepto,
            self.respuestas[self.TP_LISTAR_CURVAS].format(
              descripcion=self.verbose['_gen'][tipo_curva], resto=resto))
        
    def responder_pregunta(self, texto, fn_pesos=None):
        if fn_pesos is None:
            fn_pesos = self.fn_pesos_unos
        palabras = self.parsear_palabras(texto)
        if not palabras:
            return self.respuestas[self.R_NO_ENTIENDO]
        n_modelo, err = self.detectar_modelo(palabras)
        modelo = (self.bd[n_modelo] if err in (None, self.RET_UN_MODELO_ERRATA)
                                    else None)

        if modelo is not None:
            ret = self.respuesta_modelo(modelo, n_modelo, palabras, fn_pesos)
            if err == self.RET_UN_MODELO_ERRATA:
                return self.respuestas[err].format(n_modelo=n_modelo,
                                                   resto=ret)
            return ret
        if err == self.RET_VARIOS_MODELOS:
            return self.respuestas[err].format(', '.join(n_modelo))
        elif err == self.RET_NO_HAY_MODELO:
            return self.respuesta_global(palabras, fn_pesos)

if __name__ == '__main__':
    
    qa = QA()
    while True:
        entrada = input('\nIntroduce una pregunta: ')
        respuesta = qa.responder_pregunta(entrada)

        if respuesta == qa.respuestas[qa.TP_DESPDEDIDA]:
            exit(respuesta)
        print(respuesta)
        