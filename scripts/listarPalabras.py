
sustantivos = []
verbos = []
adjetivos = []
adverbios = []

with open('textoInicial.md') as t:
    words = []
    for line in t:
        line = line.replace('.', '').replace(',', '')
        words += line.split()
    for w in words:
        if w.startswith('__'):
            sustantivos.append(w.replace('__', ''))
        elif w.startswith('_'):
            verbos.append(w.replace('_', ''))
        elif w.startswith('<u>'):
            adverbios.append(w.replace('<u>', '').replace('</u>', ''))
        elif w.startswith('<i>'):
            adjetivos.append(w.replace('<i>', '').replace('</i>', ''))
    sustantivos = set(sustantivos[1:])
    verbos = set(verbos[1:])
    adjetivos = set(adjetivos[1:])
    adverbios = set(adverbios[1:])


with open('palabras.md', 'w') as p:
    def aniadeLista(tipo, palabras):
        p.write('## {}\n\n'.format(tipo))
        p.write('- ' + '\n\n- '.join(sorted(palabras)))
        p.write('\n\n')

    aniadeLista('Sustantivos', sustantivos)
    aniadeLista('Verbos', verbos)
    aniadeLista('Adverbios', adverbios)
    aniadeLista('Adjetivos', adjetivos)
