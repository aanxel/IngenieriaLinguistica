import os
import statistics 

temas = ('Deportes', 'Politica', 'Salud')
dir_docs = os.path.join(os.path.pardir, 'Datos')

if __name__ == '__main__':
    for tema in temas:
        sizes = []
        path = os.path.join(dir_docs, tema)
        ficheros = [os.path.join(path, f) for f in os.listdir(path)]
        for fichero in ficheros:
            with open(fichero, 'r') as f:
                texto = ' '.join(f.readlines())
                sizes.append(len(texto.split()))
        print(f'{tema}: Media = {statistics.mean(sizes)}    ' +
              f'Std = {statistics.stdev(sizes)}')