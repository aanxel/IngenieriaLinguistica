# Plantillas para respuestas
R_CUAL = '{descripcion} del monitor {modelo} es {valor}.'
R_CUANTO = 'El monitor {modelo} tiene {valor} {descripion}.'
R_DE_CUANTO = '{descripcion} del monitor {modelo} es de {valor}.'
R_TIENE = 'El monitor {modelo} {valor} tiene {descripcion}.'


def score_etiqueta(etiqueta, palabras):
    """
    Indica la puntuación de una etiqueta en una frase como la proporción de
    términos de la etiqueta que se han verificado

    Args:
        etiqueta (string): Forma de describir un concepto
        palabras ([string]): Lista de palabras que conforman la frase a probar

    Returns:
        int: Puntuación de la etiqueta en la frase
    """    
    subetiquetas = etiqueta.split()
    return sum(int(se in palabras) for se in subetiquetas) / len(subetiquetas)


def score_etiquetas(etiquetas, palabras):
    """
    Indica la puntuación de un conjunto de etiquetas para una frase rota en
    palabras, donde se devuelve la puntuación máxima de cualquiera de las
    etiquetas.

    Args:
        etiqueta ([string]): Formas distintas de describir un concepto
        palabras ([string]): Lista de palabras que conforman la frase a probar

    Returns:
        int: Puntuación del ajuste de unas etiquetas a una frase
    """
    return max(score_etiqueta(e, palabras) for e in etiquetas)