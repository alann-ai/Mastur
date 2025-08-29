# main.py - La Montaña Prohibida (Versión Final Completa)
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.graphics import Color, Rectangle, Ellipse, Line
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.core.audio import SoundLoader
from kivy.vector import Vector
import random
import numpy as np

# Configuración de pantalla (ajustado a móvil)
Window.size = (1080 / 3, 1920 / 3)  # 360x640 aprox
Window.clearcolor = (0.1, 0.5, 0.2, 1)

# === 🔊 SONIDOS GENERADOS CON CÓDIGO (sin archivos) ===
# Usaremos arrays de NumPy para crear sonidos
try:
    import numpy as np
    from kivy.core.audio import Sound
    from array import array

    def crear_sonido(frecuencia, duracion=0.3, forma="sin"):
        sample_rate = 22050
        t = np.linspace(0, duracion, int(sample_rate * duracion))
        if forma == "sin":
            wave = np.sin(2 * np.pi * frecuencia * t)
        elif forma == "noise":
            wave = np.random.uniform(-1, 1, len(t))
        wave = (wave * 0.5 * 32767).astype(np.int16)
        return Sound(array('h', wave.tobytes()), sample_rate=sample_rate)

    snd_step = crear_sonido(400, 0.1)
    snd_joy = crear_sonido(800, 0.2, "sin")
    snd_grito = crear_sonido(150, 0.8, "noise")
    snd_puzzle = crear_sonido(600, 0.15)
    snd_combate = crear_sonido(200, 0.4, "noise")
except:
    snd_step = snd_joy = snd_grito = snd_puzzle = snd_combate = None

def reproducir(sonido):
    if sonido:
        sonido.play()

# === 🌍 MAPA 2000x2000 ===
MAPA_ANCHO, MAPA_ALTO = 2000, 2000

class Mapa:
    def __init__(self):
        self.arboles = [(random.randint(0, MAPA_ANCHO), random.randint(0, MAPA_ALTO)) for _ in range(120)]
        self.rocas = [(random.randint(0, MAPA_ANCHO), random.randint(0, MAPA_ALTO)) for _ in range(40)]
        self.arroyo = [(100 + i*20, 1000 + 20*np.sin(i/10)) for i in range(80)]
        self.cueva_x, self.cueva_y = 1000, 500
        self.cima_x, self.cima_y = 1800, 200
        # Pueblo Cosquín
        self.cosquin_x, self.cosquin_y = 100, 1300
        self.tienda_ropa_x, self.tienda_ropa_y = 150, 1350
        self.tienda_comida_x, self.tienda_comida_y = 200, 1350
        self.tienda_pociones_x, self.tienda_pociones_y = 250, 1350
        # NPCs
        self.npcs = [
            {"x": 180, "y": 1380, "nombre": "Abuelo", "dialogo": "No subas... él no perdona."},
            {"x": 220, "y": 1320, "nombre": "Niño", "dialogo": "Mi gato se perdió en la montaña..."},
            {"x": 270, "y": 1360, "nombre": "Vendedora", "dialogo": "Tengo un encargo para ti..."}
        ]

    def dibujar(self, canvas, camara_x, camara_y):
        canvas.clear()
        # Fondo: verde sierra
        with canvas:
            Color(0.1, 0.5, 0.2)
            Rectangle(pos=(0, 0), size=(1080, 1920))

        # Zonas del mapa
        # Bosque
        with canvas:
            Color(0, 0.4, 0)
            for x, y in self.arboles:
                Ellipse(pos=(x - camara_x, y - camara_y), size=(30, 30))
        # Rocas
        with canvas:
            Color(0.3, 0.3, 0.3)
            for x, y in self.rocas:
                Ellipse(pos=(x - camara_x, y - camara_y), size=(20, 12))
        # Arroyo
        with canvas:
            Color(0.4, 0.8, 1)
            puntos = [(px - camara_x, py - camara_y) for px, py in self.arroyo]
            for i in range(len(puntos) - 1):
                Line(points=[*puntos[i], *puntos[i+1]], width=3)
        # Cueva
        with canvas:
            Color(0.1, 0.1, 0.2)
            Rectangle(pos=(self.cueva_x - camara_x, self.cueva_y - camara_y), size=(60, 40))
        # Cima
        with canvas:
            Color(0.5, 0.5, 0.5)
            Rectangle(pos=(self.cima_x - camara_x, self.cima_y - camara_y), size=(50, 50))

        # === Pueblo Cosquín ===
        with canvas:
            Color(0.8, 0.7, 0.5)  # Adobe
            Rectangle(pos=(self.cosquin_x - camara_x, self.cosquin_y - camara_y), size=(100, 80))
            Color(0.7, 0.3, 0.2)  # Teja
            Line(points=[
                self.cosquin_x - camara_x,
                self.cosquin_y - camara_y + 80,
                self.cosquin_x - camara_x + 50,
                self.cosquin_y - camara_y + 100,
                self.cosquin_x - camara_x + 100,
                self.cosquin_y - camara_y + 80
            ], width=3)

        # Tiendas
        self.dibujar_tienda(canvas, self.tienda_ropa_x, self.tienda_ropa_y, camara_x, camara_y, "Ropa", "R")
        self.dibujar_tienda(canvas, self.tienda_comida_x, self.tienda_comida_y, camara_x, camara_y, "Comida", "C")
        self.dibujar_tienda(canvas, self.tienda_pociones_x, self.tienda_pociones_y, camara_x, camara_y, "Pociones", "P")

        # NPCs
        for npc in self.npcs:
            with canvas:
                Color(0.8, 0.6, 0.4)
                Ellipse(pos=(npc["x"] - camara_x, npc["y"] - camara_y), size=(20, 20))
                Color(0, 0, 0)
                Label(text="👤", pos=(npc["x"] - camara_x, npc["y"] - camara_y - 10), canvas=canvas)

    def dibujar_tienda(self, canvas, x, y, cam_x, cam_y, nombre, letra):
        with canvas:
            Color(0.9, 0.8, 0.6)
            Rectangle(pos=(x - cam_x, y - cam_y), size=(40, 40))
            Color(0, 0, 0)
            Label(text=letra, pos=(x - cam_x + 10, y - cam_y + 10), canvas=canvas)
            Label(text=nombre, pos=(x - cam_x, y - cam_y - 10), canvas=canvas)

# === 🎞️ SPRITES CON ANIMACIÓN (estilo Pokémon GBA) ===
def dibujar_sprite(canvas, x, y, tipo, frame=0, flip=False):
    x_base = x if not flip else x + 32
    # Cabeza
    with canvas:
        Color(0, 0, 0)
        Rectangle(pos=(x_base + 10, y + 8), size=(12, 8))  # Pelo
        Color(1, 0.8, 0.7)
        Rectangle(pos=(x_base + 10, y + 10), size=(12, 10))  # Cara
        # Ojos
        Color(1, 1, 1)
        Rectangle(pos=(x_base + 11, y + 10), size=(4, 4))
        Color(0, 0, 0)
        Rectangle(pos=(x_base + 12, y + 11), size=(2, 2))
        # Lentes (Alan)
        if tipo == "alan":
            Color(0, 0.5, 1)
            Rectangle(pos=(x_base + 9, y + 9), size=(6, 6), texture=None)
        # Rulos (Joaquín)
        elif tipo == "joaquin":
            Color(0.4, 0.2, 0.1)
            Ellipse(pos=(x_base + 10, y + 6), size=(4, 4))
            Ellipse(pos=(x_base + 18, y + 6), size=(4, 4))

    # Cuerpo
    with canvas:
        color = (0.5, 0.5, 0.5) if tipo == "alan" else (0, 0, 0.8) if tipo == "alexis" else (1, 1, 1)
        Color(*color)
        Rectangle(pos=(x_base + 10, y + 18), size=(12, 12))

    # Animación de brazos y piernas
    arm_dy = 0
    leg_dy = 0
    if frame == 1:
        arm_dy = 3
        leg_dy = 4
    elif frame == 2:
        arm_dy = -3
        leg_dy = -4

    with canvas:
        Color(1, 0.8, 0.7)
        # Brazos
        Rectangle(pos=(x_base + 6, y + 20 + arm_dy), size=(4, 6))
        Rectangle(pos=(x_base + 22, y + 20 - arm_dy), size=(4, 6))
        # Piernas
        Rectangle(pos=(x_base + 10, y + 30 + leg_dy), size=(4, 8))
        Rectangle(pos=(x_base + 18, y + 30 - leg_dy), size=(4, 8))
        # Zapatos
        Color(0.3, 0.3, 0.3)
        Rectangle(pos=(x_base + 10, y + 38 + leg_dy), size=(4, 4))
        Rectangle(pos=(x_base + 18, y + 38 - leg_dy), size=(4, 4))

    # Accesorios
    if tipo == "alan":
        with canvas:
            Color(0.3, 0.3, 0.3)
            Rectangle(pos=(x_base + 26, y + 22), size=(4, 4))  # Fierro
    elif tipo == "alexis":
        with canvas:
            Color(0.2, 0.2, 0.2)
            Rectangle(pos=(x_base + 8, y + 24), size=(2, 6))  # Cuchillo
    elif tipo == "joaquin":
        with canvas:
            Color(0.7, 0.5, 0.3)
            Ellipse(pos=(x_base + 4, y + 24), size=(6, 4))  # Mate
    elif tipo == "cazador":
        with canvas:
            Color(0.4, 0.2, 0.1)
            Rectangle(pos=(x_base + 8, y + 6), size=(16, 6))  # Cuernos
            Color(0.6, 0.3, 0.1)
            Rectangle(pos=(x_base + 10, y + 12), size=(12, 10))
            # Arco
            Color(0.4, 0.2, 0.1)
            Line(points=[x_base + 8, y + 20, x_base + 24, y + 34], width=2)

# === 👤 CAZADOR CON IA ===
class Cazador:
    def __init__(self, mapa):
        self.x = mapa.cima_x
        self.y = mapa.cima_y
        self.velocidad = 1.8
        self.frame = 0

    def actualizar(self, jugador_x, jugador_y):
        dx = jugador_x - self.x
        dy = jugador_y - self.y
        dist = (dx**2 + dy**2)**0.5
        if dist < 50:
            return "ATACAR"
        elif dist < 300:
            if abs(dx) > 5:
                self.x += self.velocidad * (1 if dx > 0 else -1)
            if abs(dy) > 5:
                self.y += self.velocidad * (1 if dy > 0 else -1)
            return "PERSEGUIR"
        return "OCULTO"

    def dibujar(self, canvas, camara_x, camara_y):
        frame = (int(self.x) // 20) % 3
        dibujar_sprite(canvas, self.x - camara_x, self.y - camara_y, "cazador", frame=frame)

# === 🎮 INTERFAZ TÁCTIL ===
class Interfaz(FloatLayout):
    def __init__(self, juego, **kwargs):
        super().__init__(**kwargs)
        self.juego = juego

        # Joystick virtual
        self.joystick = Button(text="📍", size_hint=(0.25, 0.25), pos_hint={'x': 0, 'y': 0})
        self.add_widget(self.joystick)
        self.joystick.bind(on_touch_down=self.start_move, on_touch_move=self.move, on_touch_up=self.stop_move)

        # Botones A, B, X, Y
        self.btn_A = Button(text="A", size_hint=(0.15, 0.15), pos_hint={'x': 0.85, 'y': 0})
        self.btn_B = Button(text="B", size_hint=(0.15, 0.15), pos_hint={'x': 0.70, 'y': 0})
        self.btn_X = Button(text="X", size_hint=(0.15, 0.15), pos_hint={'x': 0.85, 'y': 0.15})
        self.btn_Y = Button(text="Y", size_hint=(0.15, 0.15), pos_hint={'x': 0.70, 'y': 0.15})
        self.add_widget(self.btn_A)
        self.add_widget(self.btn_B)
        self.add_widget(self.btn_X)
        self.add_widget(self.btn_Y)

        self.btn_A.bind(on_press=lambda x: juego.interactuar())
        self.btn_Y.bind(on_press=lambda x: juego.grito_cazador())

    def start_move(self, btn, touch):
        if btn.collide_point(*touch.pos):
            self.move(btn, touch)

    def move(self, btn, touch):
        if btn.collide_point(*touch.pos):
            centro_x = btn.x + btn.width / 2
            centro_y = btn.y + btn.height / 2
            dx = touch.x - centro_x
            dy = touch.y - centro_y
            mag = (dx**2 + dy**2)**0.5
            if mag > 10:
                self.juego.mov_x = dx / 50
                self.juego.mov_y = dy / 50
            else:
                self.juego.mov_x = self.juego.mov_y = 0

    def stop_move(self, btn, touch):
        self.juego.mov_x = self.juego.mov_y = 0

# === 🧩 MINIJUEGOS ===
class PuzzleMemoria(Popup):
    def __init__(self, on_exit):
        super().__init__(title="Puzzle de Memoria", size_hint=(0.9, 0.7))
        self.on_exit = on_exit
        self.secuencia = [random.randint(1, 9) for _ in range(5)]
        self.intento = []
        layout = BoxLayout(orientation='vertical')
        self.label = Label(text="Memoriza la secuencia...")
        layout.add_widget(self.label)
        for i in range(1, 10):
            btn = Button(text=str(i), on_press=lambda b, n=int(b.text): self.presionar(n))
            layout.add_widget(btn)
        self.add_widget(layout)
        Clock.schedule_once(self.mostrar, 0.5)

    def mostrar(self, dt):
        self.label.text = " -> ".join(map(str, self.secuencia))
        Clock.schedule_once(self.pedir, 2)

    def pedir(self, dt):
        self.label.text = "Ingresa la secuencia"
        reproducir(snd_puzzle)

    def presionar(self, n):
        self.intento.append(n)
        if len(self.intento) == len(self.secuencia):
            if self.intento == self.secuencia:
                self.label.text = "¡Correcto!"
                Clock.schedule_once(lambda dt: self.on_exit(True), 1)
                self.dismiss()
            else:
                self.label.text = "Fallaste..."
                Clock.schedule_once(lambda dt: self.on_exit(False), 1)
                self.dismiss()

# === 🎮 JUEGO PRINCIPAL ===
class JuegoWidget(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.jugador_x = 100
        self.jugador_y = 100
        self.camara_x = 0
        self.camara_y = 0
        self.mov_x = 0
        self.mov_y = 0
        self.frame = 0
        self.inventario = {"monedas": 50}
        self.misiones = {"buscar_gato": False}
        self.mapa = Mapa()
        self.cazador = Cazador(self.mapa)
        self.personaje = "alan"  # Puedes cambiarlo

        # UI
        self.label = Label(text="¡Bienvenido a La Montaña Prohibida!", size_hint=(1, 0.1), pos_hint={'x': 0, 'y': 0.9})
        self.add_widget(self.label)

        # Interfaz táctil
        self.interfaz = Interfaz(self)
        self.add_widget(self.interfaz)

    def interactuar(self):
        # Detectar NPCs
        for npc in self.mapa.npcs:
            dx = npc["x"] - self.jugador_x
            dy = npc["y"] - self.jugador_y
            if (dx**2 + dy**2)**0.5 < 60:
                popup = Popup(title=npc["nombre"], content=Label(text=npc["dialogo"]), size_hint=(0.8, 0.4))
                popup.open()
                return

        # Tiendas
        tiendas = [
            (self.mapa.tienda_ropa_x, self.mapa.tienda_ropa_y, "Ropa"),
            (self.mapa.tienda_comida_x, self.mapa.tienda_comida_y, "Comida"),
            (self.mapa.tienda_pociones_x, self.mapa.tienda_pociones_y, "Pociones")
        ]
        for x, y, nombre in tiendas:
            if ((x - self.jugador_x)**2 + (y - self.jugador_y)**2)**0.5 < 60:
                popup = Popup(title=nombre, content=Label(text=f"Bienvenido a la tienda de {nombre}"), size_hint=(0.8, 0.4))
                popup.open()
                return

        # Puzzle
        if ((self.mapa.cueva_x - self.jugador_x)**2 + (self.mapa.cueva_y - self.jugador_y)**2)**0.5 < 80:
            PuzzleMemoria(on_exit=self.on_puzzle).open()

    def on_puzzle(self, exito):
        if exito:
            self.label.text = "¡Resolviste el puzzle! Encontraste un objeto secreto."
        else:
            self.label.text = "No lograste resolverlo."

    def grito_cazador(self):
        reproducir(snd_grito)
        self.label.text = "¡JA-JA-JA! ¡NUNCA ESCAPARÁS!"

    def update(self, dt):
        self.frame += 1

        # Movimiento
        self.jugador_x += self.mov_x * 5
        self.jugador_y += self.mov_y * 5
        self.jugador_x = max(0, min(MAPA_ANCHO, self.jugador_x))
        self.jugador_y = max(0, min(MAPA_ALTO, self.jugador_y))

        # Cámara
        self.camara_x = self.jugador_x - Window.width / 2
        self.camara_y = self.jugador_y - Window.height / 2

        # Animación de paso
        moviendose = abs(self.mov_x) > 0.1 or abs(self.mov_y) > 0.1
        if moviendose and self.frame % 15 == 0:
            reproducir(snd_step)

        # IA Cazador
        estado = self.cazador.actualizar(self.jugador_x, self.jugador_y)
        if estado == "PERSEGUIR" and random.random() < 0.03:
            self.label.text = "¿Oyes eso...?"
            reproducir(snd_grito)

        # Render
        self.canvas.clear()
        self.mapa.dibujar(self.canvas, self.camara_x, self.camara_y)
        frame_anim = 0 if not moviendose else (self.frame // 10) % 3
        dibujar_sprite(self.canvas, Window.width / 2 - 16, Window.height / 2 - 16, self.personaje, frame_anim)
        self.cazador.dibujar(self.canvas, self.camara_x, self.camara_y)

# === 🎮 PANTALLA PRINCIPAL ===
class MenuApp(App):
    def build(self):
        layout = FloatLayout()
        layout.add_widget(Label(text="LA MONTAÑA PROHIBIDA", font_size=40, pos_hint={'x': 0, 'y': 0.4}))
        btn_play = Button(text="▶ PLAY", size_hint=(0.5, 0.1), pos_hint={'x': 0.25, 'y': 0.3})
        btn_multi = Button(text="👥 Multijugador (3 jugadores)", size_hint=(0.5, 0.1), pos_hint={'x': 0.25, 'y': 0.15})
        layout.add_widget(btn_play)
        layout.add_widget(btn_multi)

        def iniciar_juego(*args):
            self.stop()
            class JuegoApp(App):
                def build(self):
                    juego = JuegoWidget()
                    Clock.schedule_interval(juego.update, 1/30)
                    return juego
            JuegoApp().run()

        btn_play.bind(on_press=iniciar_juego)
        return layout

if __name__ == '__main__':
    MenuApp().run()