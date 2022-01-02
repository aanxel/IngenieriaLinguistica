from QA import QA

qa = QA()

m1 = '27UP850-W'
m2 = '34WN80C'
ms = [m1, m2]

preguntas = [
    # Preguntas especificas
    "¿Que valoracion tiene el monitor {m}?",
    "Dime quien es el fabricante del monitor {m}",
    "De que web has extraido la pantalla {m}?",
    [
        "¿Que tamaño tiene la pantalla del monitor {m}?",
        "Cuantas pulgadas tiene la pantalla del monitor {m}?",
    ],
    "¿Que resolucion posee el monitor {m}?",
    "¿Cual es el ratio de aspecto del monitor {m}?",
    "¿El monitor {m} tiene retroiluminacion LED?",
    "Dime el brillo minimo del monitor {m}",
    "Que brillo tipico tiene el monitor {m}?",
    "¿Que ratio de contraste minimo tiene el monitor {m}?",
    "Cual es el ratio de contraste tipico del monitor {m}?",
    "¿Con que velocidad de respuesta cuenta el monitor {m}?",
    "Cual es la profundidad de color o numero de colores de la pantalla del monitor {m}?",
    "¿Que tipo de panel tiene el monitor {m}?",
    [
        "Es curva la pantalla del monitor {m}?",
        "¿El monitor {m} tiene pantalla plana?"
    ],
    [
        "¿Que angulo de vision arriba abajo tiene el monitor {m}",
        "¿Cual es el angulo de vision U/D del monitor {m}",
        "¿Cuanto angulo de vision vertical tiene el monitor {m}",
    ],
    [
        "¿Que angulo de vision izquierda derecha tiene el monitor {m}",
        "¿Cual es el angulo de vision R/L del monitor {m}",
        "¿Cuanto angulo de vision horizontal tiene el monitor {m}",
    ],
    [
        "¿Que version de HDR tiene el monitor {m}?",
        "¿El monitor {m} cuenta con HDR?",
    ],
    "Dime si el monitor {m} tiene FreeSync",
    "¿El monitor {m} tiene GSync?",
    "El monitor {m} cuenta con algun tipo de overclock?",
    "Existe alguna funcionalidad asociada al ahorro de energía del monitor {m}",
    "Dime si el monitor {m} tiene microfono",
    "¿El monitor {m} tiene webcam?",
    "Existe algun contador de FPS incorporado para el monitor {m}?",
    "¿Cuantas entradas HDMI tiene el monitor {m}?",
    "¿Cual es la frecuencia maxima de las entradas HDMI del monitor {m}?",
    "¿Hasta que resolucion adminte el high definition multimedia interface del monitor {m}?",
    "¿Cual es la version del HDMI del monitor {m}?",
    "¿Cual es el numero de entradas del monitor {m}?",
    "¿Que frecuencia adminten las conexiones DP del monitor {m}?",
    "¿Que resolucion se alcanza con las entradas Display Port del monitor {m}?",
    "¿Que version de DP tiene el monitor {m}?",
    "¿Cuantas entradas miniDP tiene el monitor {m}?",
    "Dime cuantas entradas VGA tiene el monitor {m}",
    "Que tantas entradas DVI tiene el monitor {m}?",
    "De cuantas entradas thunderbolt dispone el monitor {m}?",
    "Cuantas entradas USB-C tiene el monitor {m}?",
    "Dime que resolucion maxima se alcanza con USB-C en el monitor {m}",
    "Es posible que el monitor {m} tenga algun USB de entrada?",
    "Cuantas conexiones USB de salida tiene el monitor {m}",
    "¿Que version tienen las conexiones de salida USB del monitor {m}?",
    "¿El monitor {m} tiene entrada de audio?",
    "¿Hay entrada de microfono en el monitor {m}?",
    "¿El monitor {m} dispone de salida de auriculares?",
    "¿Cuantos altavoces tiene el monitor {m}?",
    "¿Cual es la potencia de los altavoces del monitor {m}?",
    "¿El monitor {m} tiene incorporado control bluetooth para los altavoces?",
    "¿Que tipo de alimentacion de energia tiene el monitor {m}?",
    "¿Cual es el consumo tipico de energia del monitor {m}?",
    "¿Cuanta energia maxima consume el monitor {m}?",
    "¿Cual es la media de energia consumida por el monitor {m} en caso de encontrarse en modo ahorro de energia?",
    "¿Cuanta energia consume el monitor {m} en modo reposo con la pantalla suspendida?",
    "¿Cuanta energía consume el monitor {m} con la pantalla apagada?",
    # Preguntas grupales
    [   # Sobre la frecuencia
        "Cual es la frecuencia del monitor {m}?",
        "para el monitor {m}, cual es la tasa de refresco?"
    ],
    [   # Sobre las entradas del monitor
        "Cuales son las entradas del monitor {m}?",
        "que entradas tiene el {m}" 
    ],
    [   # Sobre la resolución del monitor
        "que resolucion tiene el monitor {m}?",
        "el {m} cuantos pixeles tiene"
    ],
    [   # Sobre el brillo
        "que brillo tiene el monitor {m}",
    ],
    [   # Sobre el ratio de contraste
        "cual es el ratio de contraste del monitor {m}",
        "de cuanto es el ratio de contraste del {m}"
    ],
    [   # Sobre el ángulo de visión
        "que angulo de visión tiene el monitor {m}",
    ],
    [   # Sobre la alimentación
        "el monitor {m}, que tipo de alimentación tiene?",
        "dime que sabes sobre la alimentación del monitor {m}"
    ],
    [   # Sobre el hdmi
        "Que me puedes decir del hdmi del monitor {m}"
    ],
    [   # Sobre DP
        "que sabes sobre el DP del monitor {m}"
    ],
    [   # Sobe miniDP
        "me podrias decir algo del miniDP de {m}"
    ],
    [   # Sobre VGA
        "este monitor {m} tiene VGA?"
    ],
    [   # Sobre DVI
        "que información me puedes dar para el monitor {m} sobre el DVI?"
    ],
    [   # Sobre Thunderbolt
        "el monitor {m} tiene Thunderbolt?"
    ],
    [   # Sobre USB-C
        "me podrias decir si el monitor {m} tiene usb tipo c?"
    ],
    [   # Sobre USBinput
        "Dime todo lo que sepas sobre las conexiones de entrada USB del monitor {m}"
    ],
    [   # Sobre USBoutput
        "Que informacion tienes sobre las conexiones de salida USB del monitor {m}"
    ],
    [   # Sobre USB
        "Que me puedes decir sobre las conexiones USB del monitor {m}"
    ],
    [   # Sobre sonido
        "Dame toda la informacion relacionada con el sonido acerca del monitor {m}?",
        "Que propiedades de audio tiene disponible el monitor {m}"
    ],
    [   # Sobre atributos
        "Que conjunto de atributos posee el monitor {m}?",
        "Que informacion albergas sobre los atributos del modelo {m}"
    ],
    [   # Sobre conectividad
        "Que conectividades tiene disponible el monitor {m}?",
        "Que conexiones de entrada y salida tiene el monitor {m}"
    ],
    [   # Sobre altavoces
        "Dime que sabes sobre los altavoces del monitor {m}",
        "Que información tienes sobre los altavoces del monitor {m}"
    ],
    [   # Sobre consumo de potencia
        "Que sabes sobre el consumo de potencia del monitor {m}",
        "Que información tienes disponible sobre el consumo energetico del monitor {m}"
    ],
    [   # Sobre la pantalla
        "Que sabes sobre la pantalla del monitor {m}",
        "Dime todo lo que sepas sobre el monitor {m}"
    ],
    "",
    # Preguntas globales
    [   # Saludo:
        "Hola, como va?",
        "Que tal alexo",
    ],
    [   # Despedida
            "Adios",
            "Nos vemos",
    ],
    [   # Listar modelos
        "Que modelos tienes en la tienda?",
        "Me podrias listar los modelos?",
        "Hazme una lista de los modelos por favor",
        "Cuales monitores hay?",
    ],
    [   # Monitores con tipo de panel ips
        "que monitores tiene ips?",
        "cuales van con ips?"
    ],
    [   # Monitores con otro tipo de panel
        "que monitores tienen panel VA?",
        "dime que monitores tienen tn"
    ],
    [   # Monitores con resolución 4K
        "que monitores son 4k?",
        "tienes monitores uhd?"
    ],
    [   # Monitores con otra resolución
        "y monitores 8k tienes alguno?",
        "no tendrás monitoes 5k no?",
        "tienes por ahi algun monitor hd?",
        "hay disponible algún monitor fhd"

    ],
    [   # Monitores de pantalla plana
        "por ahi hay algún monitor plano?",
        "te queda algún monitor que no sea curvo?"
    ],
    [   # Monitores de pantalla curva
        "cuales son los monitores no planos",
        "listame los monitores curvos plis"
    ],
    [   # Modelos de valoración máxima
        "que me recomiendas?",
        "cual es el mejor monitor",
        "que modelo tiene la mejor valoración"
    ]
]

def comprobar_pregunta(p):
    print(p)
    print(qa.responder_pregunta(p))
    print()

def test_pregunta(ps):
    for p in ps:
        if '{m}' in p:
            test_pregunta([p.format(m=m) for m in ms])
        else:
            comprobar_pregunta(p)    

for p in preguntas:
    if type(p) != list:
        test_pregunta([p])
    else:
        test_pregunta(p)