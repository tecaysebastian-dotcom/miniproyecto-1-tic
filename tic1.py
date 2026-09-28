import time
import random
import os
import copy
import board
import busio
import adafruit_dht
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
from gpiozero import Button, TonalBuzzer, RGBLED
from gpiozero.tones import Tone

# ============================
# --- UI (colores y pantalla) ---
# ============================
RESET = "\033[0m"

COLORES = {
    "Fuego": "\033[91m",
    "Planta": "\033[92m",
    "Agua": "\033[94m",
    "Roca": "\033[93m",
    "Tierra": "\033[33m",
    "exito": "\033[92m",
    "fallo": "\033[91m",
    "efectivo": "\033[93m",
    "titulo": "\033[96m",
}


def limpiar_pantalla():
    os.system("clear")


def colorear(texto, color):
    codigo = COLORES.get(color, "")
    return f"{codigo}{texto}{RESET}"


def encabezado(texto, ancho=42):
    linea = "=" * ancho
    print(colorear(linea, "titulo"))
    print(colorear(texto.center(ancho), "titulo"))
    print(colorear(linea, "titulo"))


# ============================
# --- Inicialización de Hardware ---
# ============================
dht = adafruit_dht.DHT11(board.D12)
i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1115(i2c)
joy_y = AnalogIn(ads, 1)
boton = Button(5, pull_up=True)
buzzer = TonalBuzzer(6)

led1 = RGBLED(red=16, green=20, blue=21)
led2 = RGBLED(red=19, green=13, blue=26)


# ============================
# --Mini proyecto 1--
# ============================
class Pokemon:
    def __init__(self, nombre, tipo, habitat, ps_max, prob_captura, cantidad, ataques):
        self.nombre = nombre
        self.tipo = tipo
        self.habitat = habitat
        self.ps_max = ps_max
        self.ps_actual = ps_max
        self.prob_captura = prob_captura
        self.cantidad = cantidad
        self.ataques = ataques


class Habitat:
    def __init__(self, nombre, condiciones):
        self.nombre = nombre
        self.condiciones = condiciones
        self.pokemones = []

    def agregar_pokemon(self, pokemon):
        self.pokemones.append(pokemon)

    def poblacion_total(self):
        return sum(p.cantidad for p in self.pokemones)


# ============================
# --- Funciones de Hardware y Menús ---
# ============================
def hacer_sonido(accion):
    if accion == "mover":
        buzzer.play(Tone(400))
        time.sleep(0.1)
    elif accion == "seleccionar":
        buzzer.play(Tone(800))
        time.sleep(0.2)
    buzzer.stop()


def esperar_soltar_boton():
    while boton.is_pressed:
        time.sleep(0.05)


def esperar_confirmacion():
    while not boton.is_pressed:
        time.sleep(0.1)
    hacer_sonido("seleccionar")
    esperar_soltar_boton()


def seleccionar_opcion_joystick(lista_textos, titulo=None):
    indice = 0
    ultimo_movimiento = 0

    while True:
        limpiar_pantalla()
        if titulo:
            encabezado(titulo)
        for i, texto in enumerate(lista_textos):
            if i == indice:
                print(f" > {texto} <")
            else:
                print(f"   {texto}")

        y_val = joy_y.value
        if y_val < 5000 and time.time() - ultimo_movimiento > 0.3:
            indice = (indice - 1) % len(lista_textos)
            hacer_sonido("mover")
            ultimo_movimiento = time.time()
        elif y_val > 20000 and time.time() - ultimo_movimiento > 0.3:
            indice = (indice + 1) % len(lista_textos)
            hacer_sonido("mover")
            ultimo_movimiento = time.time()

        if boton.is_pressed:
            hacer_sonido("seleccionar")
            esperar_soltar_boton()
            return indice

        time.sleep(0.1)


def menu_habitats(habitats):
    opciones = [h.nombre for h in habitats]
    indice = seleccionar_opcion_joystick(opciones, titulo="ZONA SAFARI POKÉMON")
    return habitats[indice]


def menu_pokemones_habitat(habitat):
    opciones = []
    for p in habitat.pokemones:
        estado = f"Disp: {p.cantidad}" if p.cantidad > 0 else "AGOTADO"
        opciones.append(f"{p.nombre} ({p.tipo}) - {estado}")

    indice = seleccionar_opcion_joystick(opciones, titulo=f"POKÉMON EN {habitat.nombre.upper()}")
    return habitat.pokemones[indice]


def menu_mi_equipo(equipo):
    if not equipo:
        limpiar_pantalla()
        encabezado(f"MI EQUIPO ({len(equipo)}/6)")
        print("\nAún no has capturado ningún Pokémon.")
        print("\n[Presiona el joystick para continuar...]")
        esperar_confirmacion()
        return None

    opciones = [f"{p.nombre} ({p.tipo}) - {p.ps_actual}/{p.ps_max} PS" for p in equipo]
    indice = seleccionar_opcion_joystick(opciones, titulo=f"MI EQUIPO ({len(equipo)}/6)")
    return equipo[indice]


def mostrar_ficha(pokemon):
    limpiar_pantalla()
    encabezado(f"FICHA POKÉDEX: {pokemon.nombre}")
    print(f"Tipo: {colorear(pokemon.tipo, pokemon.tipo)}")
    print(f"Habitat: {pokemon.habitat}")
    print(f"PS máximos: {pokemon.ps_max}")
    print(f"Probabilidad de captura: {pokemon.prob_captura * 100:.0f}%")
    print(f"Cantidad disponible: {pokemon.cantidad}")
    print(f"Ataques:")
    for ataque in pokemon.ataques:
        print(f" - {ataque['nombre']} (Daño: {ataque['daño']})")

    print("\n[Presiona el joystick para continuar...]")
    esperar_confirmacion()


# --- Leyendas de descanso (Ítem 1.3) ---
LEYENDAS_DESCANSO = {
    "Bosque": [
        "Has decidido descansar bajo un árbol frondoso. El susurro de las hojas te calma.",
        "Te sientas junto a un arroyo escondido entre la maleza del bosque.",
        "Un grupo de Pokémon curiosos se asoma entre los arbustos mientras descansas."
    ],
    "Volcán": [
        "El calor del volcán te obliga a buscar sombra entre las rocas.",
        "Sientes el suelo vibrar levemente mientras descansas cerca del cráter.",
        "Una fumarola cercana libera vapor caliente mientras recuperas fuerzas."
    ],
    "Glaciar": [
        "El frío es intenso, así que te abrigas y descansas sobre la nieve.",
        "Ves tu aliento formar nubes de vapor mientras contemplas el paisaje helado.",
        "Un silencio absoluto rodea el glaciar mientras tomas un respiro."
    ],
    "Cueva": [
        "La oscuridad de la cueva te envuelve mientras descansas apoyado en la roca.",
        "Escuchas ecos lejanos de Pokémon moviéndose en la profundidad.",
        "Una gota de agua cae desde el techo de la cueva, rompiendo el silencio."
    ],
    "Cañón": [
        "El viento seco del cañón levanta polvo mientras descansas a la sombra.",
        "Observas las paredes rocosas del cañón, talladas por años de erosión.",
        "El eco de tus propios pasos resuena entre las paredes del cañón."
    ]
}


def evento_descansar(habitat):
    limpiar_pantalla()
    encabezado(f"DESCANSO EN {habitat.nombre.upper()}")
    frases = LEYENDAS_DESCANSO.get(habitat.nombre, ["Decides descansar un momento."])
    frase = random.choice(frases)
    print(f"\n{frase}")
    print("\n[Presiona el joystick para continuar...]")
    esperar_confirmacion()


def elegir_pokemon_salvaje(habitat):
    disponibles = [p for p in habitat.pokemones if p.cantidad > 0]
    if not disponibles:
        return None
    return random.choice(disponibles)


def gestionar_captura(pokemon_original, equipo):
    """Crea una copia INDEPENDIENTE del Pokémon y la agrega al equipo,
    respetando el límite de 6. Si el equipo está lleno, permite liberar."""
    capturado = copy.deepcopy(pokemon_original)
    capturado.ps_actual = capturado.ps_max

    if len(equipo) < 6:
        equipo.append(capturado)
        print(colorear(f"¡{capturado.nombre} se unió a tu equipo! ({len(equipo)}/6)", "exito"))
    else:
        sub_opciones = [f"Liberar a {p.nombre}" for p in equipo] + ["Retirarse"]
        idx2 = seleccionar_opcion_joystick(sub_opciones, titulo="EQUIPO LLENO (6/6)")
        if sub_opciones[idx2] != "Retirarse":
            liberado = equipo.pop(idx2)
            equipo.append(capturado)
            print(f"Liberaste a {liberado.nombre} y capturaste a {capturado.nombre}.")
        else:
            print("Decidiste no capturarlo.")


def evento_atrapar(habitat, equipo):
    pokemon_salvaje = elegir_pokemon_salvaje(habitat)

    if pokemon_salvaje is None:
        print(f"\nNo quedan más Pokémon disponibles en {habitat.nombre}.")
        return

    limpiar_pantalla()
    encabezado("¡ENCUENTRO SALVAJE!")
    tipo_coloreado = colorear(pokemon_salvaje.tipo, pokemon_salvaje.tipo)
    print(f"\n¡Un {pokemon_salvaje.nombre} ({tipo_coloreado}) salvaje apareció!")
    hacer_sonido("mover")

    prob_actual = pokemon_salvaje.prob_captura

    while True:
        opciones = ["Lanzar Poké Ball", "Dar de comer", "Escapar"]
        titulo = f"{pokemon_salvaje.nombre} - Captura: {prob_actual*100:.0f}% | Equipo: {len(equipo)}/6"
        indice = seleccionar_opcion_joystick(opciones, titulo=titulo)

        if opciones[indice] == "Lanzar Poké Ball":
            exito = random.random() < prob_actual
            if exito:
                print(colorear(f"\n¡Capturaste a {pokemon_salvaje.nombre}!", "exito"))
                pokemon_salvaje.cantidad -= 1
                gestionar_captura(pokemon_salvaje, equipo)
                led2.color = (0, 1, 0)
                hacer_sonido("seleccionar")
            else:
                print(colorear(f"\n{pokemon_salvaje.nombre} escapó de la Poké Ball.", "fallo"))
                led2.color = (1, 0, 0)
                hacer_sonido("mover")
            time.sleep(1.5)
            led2.off()
            break

        elif opciones[indice] == "Dar de comer":
            prob_actual = min(prob_actual + 0.20, 1.0)
            print(f"\nLe diste de comer. Probabilidad de captura ahora: {prob_actual*100:.0f}%")
            hacer_sonido("mover")

        elif opciones[indice] == "Escapar":
            print(colorear("\nDecidiste escapar del encuentro.", "fallo"))
            led2.color = (1, 0, 0)
            hacer_sonido("mover")
            time.sleep(1.5)
            led2.off()
            break


# --- Sistema de combate (Ítem 1.4) ---
def calcular_multiplicador(atacante_tipo, defensor_tipo):
    tabla = {
        "Fuego":  {"Fuego": 1,   "Planta": 2,   "Agua": 0.5},
        "Planta": {"Fuego": 0.5, "Planta": 1,   "Agua": 2},
        "Agua":   {"Fuego": 2,   "Planta": 0.5, "Agua": 1},
    }
    return tabla.get(atacante_tipo, {}).get(defensor_tipo, 1)


def seleccionar_pokemon_equipo(equipo):
    if len(equipo) == 1:
        return equipo[0]
    opciones = [f"{p.nombre} ({p.ps_actual}/{p.ps_max} PS)" for p in equipo]
    indice = seleccionar_opcion_joystick(opciones, titulo=f"ELIGE TU POKÉMON ({len(equipo)}/6)")
    return equipo[indice]


def evento_combatir(habitat, equipo):
    pokemon_salvaje = elegir_pokemon_salvaje(habitat)
    if pokemon_salvaje is None:
        print(f"\nNo hay Pokémon salvajes disponibles en {habitat.nombre}.")
        return

    # La vida del salvaje se fija UNA sola vez, al inicio del combate completo.
    pokemon_salvaje.ps_actual = pokemon_salvaje.ps_max

    limpiar_pantalla()
    encabezado("¡COMBATE!")
    tipo_coloreado = colorear(pokemon_salvaje.tipo, pokemon_salvaje.tipo)
    print(f"\n¡Un {pokemon_salvaje.nombre} ({tipo_coloreado}) salvaje te desafía!")
    hacer_sonido("mover")
    time.sleep(1)

    mi_pokemon = None

    while pokemon_salvaje.ps_actual > 0:
        if mi_pokemon is None:
            if not equipo:
                break
            mi_pokemon = seleccionar_pokemon_equipo(equipo)
            mi_pokemon.ps_actual = mi_pokemon.ps_max
            limpiar_pantalla()
            print(f"\n¡Adelante, {mi_pokemon.nombre}!")
            hacer_sonido("mover")
            print("\n[Presiona el joystick para continuar...]")
            esperar_confirmacion()

        # --- Turno del jugador ---
        opciones = [a["nombre"] for a in mi_pokemon.ataques]
        titulo = (f"{mi_pokemon.nombre}: {mi_pokemon.ps_actual}/{mi_pokemon.ps_max} PS | "
                  f"{pokemon_salvaje.nombre}: {pokemon_salvaje.ps_actual}/{pokemon_salvaje.ps_max} PS")
        indice = seleccionar_opcion_joystick(opciones, titulo=titulo)
        ataque_jugador = mi_pokemon.ataques[indice]

        mult = calcular_multiplicador(mi_pokemon.tipo, pokemon_salvaje.tipo)
        daño = round(ataque_jugador["daño"] * mult)
        pokemon_salvaje.ps_actual = max(0, pokemon_salvaje.ps_actual - daño)

        limpiar_pantalla()
        if mult > 1:
            print(colorear(f"\n{mi_pokemon.nombre} usó {ataque_jugador['nombre']}! ¡Es súper efectivo! ({daño} daño)", "efectivo"))
            led2.color = (1, 1, 0)
        elif mult < 1:
            print(f"\n{mi_pokemon.nombre} usó {ataque_jugador['nombre']}! No es muy efectivo... ({daño} daño)")
        else:
            print(f"\n{mi_pokemon.nombre} usó {ataque_jugador['nombre']}! ({daño} daño)")
        print(f"{pokemon_salvaje.nombre}: {pokemon_salvaje.ps_actual}/{pokemon_salvaje.ps_max} PS")
        hacer_sonido("mover")
        print("\n[Presiona el joystick para continuar...]")
        esperar_confirmacion()
        if mult > 1:
            led2.off()

        if pokemon_salvaje.ps_actual <= 0:
            break

        # --- Turno del Pokémon salvaje ---
        ataque_salvaje = random.choice(pokemon_salvaje.ataques)
        mult_salvaje = calcular_multiplicador(pokemon_salvaje.tipo, mi_pokemon.tipo)
        daño_salvaje = round(ataque_salvaje["daño"] * mult_salvaje)
        mi_pokemon.ps_actual = max(0, mi_pokemon.ps_actual - daño_salvaje)

        limpiar_pantalla()
        print(f"\n{pokemon_salvaje.nombre} usó {ataque_salvaje['nombre']}! Hizo {daño_salvaje} de daño a {mi_pokemon.nombre}.")
        print(f"{mi_pokemon.nombre}: {mi_pokemon.ps_actual}/{mi_pokemon.ps_max} PS")
        print("\n[Presiona el joystick para continuar...]")
        esperar_confirmacion()

        if mi_pokemon.ps_actual <= 0:
            print(colorear(f"\n{mi_pokemon.nombre} quedó debilitado y fue retirado del equipo permanentemente.", "fallo"))
            equipo.remove(mi_pokemon)
            led2.color = (1, 0, 0)
            hacer_sonido("mover")
            time.sleep(1.5)
            led2.off()

            if not equipo:
                limpiar_pantalla()
                encabezado("DERROTA")
                print(colorear("\nTodos tus Pokémon quedaron debilitados.", "fallo"))
                print("Vuelves al menú de hábitats.")
                return

            print(f"\nEquipo restante: {len(equipo)}/6")
            print("[Presiona el joystick para elegir tu siguiente Pokémon...]")
            esperar_confirmacion()
            mi_pokemon = None  # fuerza elegir uno nuevo; el salvaje mantiene su vida actual

    # --- Victoria: el Pokémon salvaje fue derrotado ---
    limpiar_pantalla()
    encabezado("¡VICTORIA!")
    print(colorear(f"\n¡Ganaste el combate! {pokemon_salvaje.nombre} salvaje fue derrotado.", "exito"))
    pokemon_salvaje.cantidad -= 1
    led2.color = (0, 1, 0)
    hacer_sonido("seleccionar")
    time.sleep(1.5)
    led2.off()

    opciones = ["Capturar", "Retirarse"]
    indice = seleccionar_opcion_joystick(opciones, titulo=f"¿CAPTURAR AL DERROTADO? (Equipo: {len(equipo)}/6)")

    if opciones[indice] == "Capturar":
        gestionar_captura(pokemon_salvaje, equipo)
    else:
        print("Te retiras sin capturar.")


def proxima_aventura(habitat, equipo):
    if equipo:
        evento = random.choice(["descansar", "atrapar", "combatir"])
    else:
        evento = random.choice(["descansar", "atrapar"])

    if evento == "descansar":
        evento_descansar(habitat)
    elif evento == "atrapar":
        evento_atrapar(habitat, equipo)
    elif evento == "combatir":
        evento_combatir(habitat, equipo)


def submenu_habitat(habitat, equipo):
    while True:
        opciones = ["Próxima aventura", "Pokédex del Hábitat", "Mi Equipo", "Volver a hábitats"]
        titulo = f"{habitat.nombre.upper()} | Equipo: {len(equipo)}/6"
        indice = seleccionar_opcion_joystick(opciones, titulo=titulo)

        if opciones[indice] == "Próxima aventura":
            if habitat.poblacion_total() > 0:
                led1.color = (0, 1, 0)
            else:
                led1.off()
            proxima_aventura(habitat, equipo)
            led1.off()

        elif opciones[indice] == "Pokédex del Hábitat":
            pokemon_elegido = menu_pokemones_habitat(habitat)
            mostrar_ficha(pokemon_elegido)

        elif opciones[indice] == "Mi Equipo":
            pokemon_elegido = menu_mi_equipo(equipo)
            if pokemon_elegido is not None:
                mostrar_ficha(pokemon_elegido)

        elif opciones[indice] == "Volver a hábitats":
            led1.off()
            break


# ============================
# --- Creación de Objetos ---
# ============================
bosque = Habitat("Bosque", {"humedad_min": 40, "humedad_max": 70})
bosque.agregar_pokemon(Pokemon("Sceptile", "Planta", "Bosque", 70, 0.25, 1, [{"nombre": "Hoja Afilada", "daño": 20}, {"nombre":"Ataque Rápido", "daño": 10}]))
bosque.agregar_pokemon(Pokemon("Chikorita", "Planta", "Bosque", 40, 0.7, 3, [{"nombre": "Látigo Cepa", "daño": 8}, {"nombre":"PLacaje", "daño": 6}]))
bosque.agregar_pokemon(Pokemon("Trevenant", "Planta", "Bosque", 60, 0.4, 2, [{"nombre": "Golpe Fantasma", "daño":16}, {"nombre":"Hoja Aguda", "daño": 10}]))

cueva = Habitat("Cueva", {"humedad_min": 70})
cueva.agregar_pokemon(Pokemon("Geodude", "Roca", "Cueva", 40, 0.6, 3, [{"nombre": "Lanza Rocas", "daño":8}, {"nombre":"Golpe Roca", "daño": 6}]))
cueva.agregar_pokemon(Pokemon("Lycanroc", "Roca", "Cueva", 75, 0.3, 2, [{"nombre": "Avalancha", "daño":16}, {"nombre":"Colmillo Rayo", "daño": 12}]))
cueva.agregar_pokemon(Pokemon("Tyranitar", "Roca", "Cueva", 95, 0.15, 1, [{"nombre": "Roca Afilada", "daño":21}, {"nombre":"Triturar", "daño": 16}]))

glaciar = Habitat("Glaciar", {"temp_max": 15})
glaciar.agregar_pokemon(Pokemon("Vulpix", "Agua", "Glaciar", 38, 0.65, 3, [{"nombre": "Rayo Hielo", "daño":8}, {"nombre":"Ataque Rápido", "daño": 5}]))
glaciar.agregar_pokemon(Pokemon("Glaceon", "Agua", "Glaciar", 65, 0.35, 2, [{"nombre": "Ventisca", "daño":15}, {"nombre":"Colmillo Hielo", "daño": 10}]))
glaciar.agregar_pokemon(Pokemon("Lapras", "Agua", "Glaciar", 90, 0.15, 1, [{"nombre": "Hidrobromba", "daño":20}, {"nombre":"Canto Helado", "daño": 15}]))

cañon = Habitat("Cañón", {"temp_min": 16, "temp_max": 29})
cañon.agregar_pokemon(Pokemon("Cubone", "Tierra", "Cañón", 40, 0.7, 3, [{"nombre": "Golpe Cabeza", "daño": 10}, {"nombre":"Doble Patada", "daño": 5}]))
cañon.agregar_pokemon(Pokemon("Sandlash", "Tierra", "Cañón", 60, 0.45, 2, [{"nombre": "Terremoto", "daño":15}, {"nombre":"Ataque Rápido", "daño": 10}]))
cañon.agregar_pokemon(Pokemon("Krookodile", "Tierra", "Cañón", 80, 0.15, 1, [{"nombre": "Triturar", "daño":21}, {"nombre":"Excavar", "daño": 16}]))

volcan = Habitat("Volcán", {"temp_min": 30, "temp_max": 50})
volcan.agregar_pokemon(Pokemon("Chimchar", "Fuego", "Volcán", 45, 0.6, 3, [{"nombre": "Ascuas", "daño": 9}, {"nombre":"Arañazo", "daño": 6}]))
volcan.agregar_pokemon(Pokemon("Quilaba", "Fuego", "Volcán", 58, 0.4, 2, [{"nombre": "Lanzallamas", "daño":14}, {"nombre":"Ataque Rápido", "daño": 10}]))
volcan.agregar_pokemon(Pokemon("Blaziken", "Fuego", "Volcán", 80, 0.2, 1, [{"nombre": "Evite Ígneo", "daño":22}, {"nombre":"Patada Ígnea", "daño": 17}]))

todos_los_habitats = [bosque, volcan, glaciar, cueva, cañon]
equipo_jugador = []

# ============================
# --- PROGRAMA PRINCIPAL ---
# ============================
try:
    while True:
        try:
            temp = dht.temperature
            hum = dht.humidity
            if temp is None or hum is None:
                time.sleep(2)
                continue
        except RuntimeError:
            time.sleep(2)
            continue
        except OverflowError:
            time.sleep(2)
            continue

        print(f"\nClima actual -> Temp: {temp}°C | Humedad: {hum}%")

        habitats_disponibles = []
        for h in todos_los_habitats:
            conds = h.condiciones
            if "humedad_min" in conds and hum < conds["humedad_min"]: continue
            if "humedad_max" in conds and hum > conds["humedad_max"]: continue
            if "temp_min" in conds and temp < conds["temp_min"]: continue
            if "temp_max" in conds and temp > conds["temp_max"]: continue
            habitats_disponibles.append(h)

        if not habitats_disponibles:
            print("No hay hábitats disponibles con este clima. Esperando...")
            time.sleep(3)
            continue

        habitat_elegido = menu_habitats(habitats_disponibles)
        submenu_habitat(habitat_elegido, equipo_jugador)

except KeyboardInterrupt:
    led1.off()
    led2.off()
    buzzer.stop()
    print("\nPrograma terminado.")