#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Aventura en la Montaña - RPG 2D cooperativo para Android
Desarrollado con Kivy (Python 3.10+)
Todos los sprites y sonidos generados directamente en el código
"""

import json
import os
import random
from collections import deque
from functools import partial
from time import time
import math
import array
import struct

from kivy.app import App
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle, Line, Canvas, Texture
from kivy.lang import Builder
from kivy.properties import (BooleanProperty, DictProperty, ListProperty,
                            NumericProperty, ObjectProperty, StringProperty)
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scatter import Scatter
from kivy.uix.screenmanager import Screen, ScreenManager, SlideTransition, SwapTransition
from kivy.uix.widget import Widget
from kivy.utils import get_color_from_hex
from kivy.storage.jsonstore import JsonStore

# Configuración inicial de la ventana para desarrollo
# En producción, esto se manejará en buildozer.spec
Window.clearcolor = (0.1, 0.1, 0.1, 1)
Window.size = (480, 800)  # Relación típica de pantalla móvil

# Constantes del juego
SCREEN_WIDTH = Window.width
SCREEN_HEIGHT = Window.height
TILE_SIZE = 32  # Tamaño estándar para sprites en pixel art
PLAYER_SPEED = 2  # Velocidad de movimiento del jugador

# Definición de personajes
CHARACTERS = {
    'alan': {
        'name': 'Alan',
        'description': 'El valiente',
        'attack_type': 'golpe_fierro',
        'max_health': 100,
        'max_mana': 50,
        'attack': 15,
        'defense': 8,
        'speed': 10
    },
    'alexis': {
        'name': 'Alexis',
        'description': 'El inteligente',
        'attack_type': 'cuchillo',
        'max_health': 80,
        'max_mana': 70,
        'attack': 12,
        'defense': 10,
        'speed': 12
    },
    'joaquin': {
        'name': 'Joaquín',
        'description': 'El cómico',
        'attack_type': 'patada',
        'max_health': 90,
        'max_mana': 60,
        'attack': 18,
        'defense': 6,
        'speed': 14
    }
}

# Definición de enemigos
ENEMIES = {
    'lobo': {
        'name': 'Lobo Salvaje',
        'health': 40,
        'attack': 8,
        'defense': 5,
        'speed': 7,
        'xp': 15,
        'gold': 5
    },
    'oso': {
        'name': 'Oso Pardo',
        'health': 70,
        'attack': 12,
        'defense': 8,
        'speed': 5,
        'xp': 30,
        'gold': 15
    },
    'monstruo': {
        'name': 'Monstruo Ancestral',
        'health': 150,
        'attack': 20,
        'defense': 15,
        'speed': 10,
        'xp': 100,
        'gold': 50
    }
}

# Definición de items
ITEMS = {
    'pocion_salud': {
        'name': 'Poción de Salud',
        'description': 'Restaura 30 puntos de salud',
        'type': 'consumable',
        'effect': {'health': 30},
        'price': 20
    },
    'pocion_mana': {
        'name': 'Poción de Mana',
        'description': 'Restaura 20 puntos de mana',
        'type': 'consumable',
        'effect': {'mana': 20},
        'price': 15
    },
    'comida': {
        'name': 'Comida de Montaña',
        'description': 'Restaura 15 puntos de energía',
        'type': 'consumable',
        'effect': {'energy': 15},
        'price': 10
    },
    'espada': {
        'name': 'Espada Rota',
        'description': 'Mejora el ataque en 5 puntos',
        'type': 'equipment',
        'effect': {'attack': 5},
        'price': 50
    }
}

# Estructura KV para la interfaz de usuario
KV = '''
#:import SlideTransition kivy.uix.screenmanager.SlideTransition
#:import SwapTransition kivy.uix.screenmanager.SwapTransition

<Joystick@Scatter>:
    size_hint: None, None
    size: 120, 120
    auto_bring_to_front: False
    do_rotation: False
    do_scale: False
    do_translation: False
    canvas.before:
        Color:
            rgba: 0.3, 0.3, 0.3, 0.7
        Ellipse:
            pos: self.pos
            size: self.size
        Color:
            rgba: 0.7, 0.7, 0.7, 0.7
        Ellipse:
            pos: self.center_x - 30, self.center_y - 30
            size: 60, 60

<ButtonAction@Button>:
    size_hint: None, None
    size: 80, 80
    background_color: 0.2, 0.6, 1, 0.8
    font_size: 24
    canvas.before:
        Color:
            rgba: 0.1, 0.1, 0.1, 0.5
        Line:
            width: 2
            rectangle: self.x, self.y, self.width, self.height
        Color:
            rgba: 1, 1, 1, 0.2
        Line:
            width: 1
            rectangle: self.x + 2, self.y + 2, self.width - 4, self.height - 4

<HealthBar@Widget>:
    health: 100
    max_health: 100
    size_hint: None, None
    size: 120, 20
    pos: 0, 0
    
    canvas:
        Color:
            rgba: 0.2, 0.2, 0.2, 1
        Rectangle:
            pos: self.pos
            size: self.width, self.height
        Color:
            rgba: 1, 0, 0, 1
        Rectangle:
            pos: self.x, self.y
            size: self.width * (self.health / self.max_health), self.height

<ManaBar@Widget>:
    mana: 50
    max_mana: 50
    size_hint: None, None
    size: 120, 10
    pos: 0, 0
    
    canvas:
        Color:
            rgba: 0.2, 0.2, 0.2, 1
        Rectangle:
            pos: self.pos
            size: self.width, self.height
        Color:
            rgba: 0, 0.5, 1, 1
        Rectangle:
            pos: self.x, self.y
            size: self.width * (self.mana / self.max_mana), self.height

<InventorySlot@Button>:
    size_hint: None, None
    size: 60, 60
    background_color: 0, 0, 0, 0
    image_source: ''
    
    canvas.before:
        Color:
            rgba: 0.3, 0.3, 0.3, 0.7
        Rectangle:
            pos: self.pos
            size: self.size
        Color:
            rgba: 1, 1, 1, 0.2
        Line:
            width: 1
            rectangle: self.x + 1, self.y + 1, self.width - 2, self.height - 2
    
    Image:
        source: root.image_source
        pos: self.pos
        size: self.size
        allow_stretch: True
        keep_ratio: False

<QuickSlot@Button>:
    size_hint: None, None
    size: 50, 50
    background_color: 0, 0, 0, 0
    image_source: ''
    
    canvas.before:
        Color:
            rgba: 0.3, 0.3, 0.3, 0.7
        Rectangle:
            pos: self.pos
            size: self.size
        Color:
            rgba: 1, 1, 1, 0.2
        Line:
            width: 1
            rectangle: self.x + 1, self.y + 1, self.width - 2, self.height - 2
    
    Image:
        source: root.image_source
        pos: self.pos
        size: self.size
        allow_stretch: True
        keep_ratio: False

<ActionButton@ButtonAction>:
    text: 'A'
    action_type: 'interact'

<ActionButtonX@ButtonAction>:
    text: 'X'
    action_type: 'jump'

<ActionButtonB@ButtonAction>:
    text: 'B'
    action_type: 'push'

<ActionButtonY@ButtonAction>:
    text: 'Y'
    action_type: 'switch'

<DialogueBox@BoxLayout>:
    orientation: 'vertical'
    size_hint: None, None
    size: Window.width * 0.9, 120
    pos: Window.width * 0.05, 50
    padding: 10
    
    canvas.before:
        Color:
            rgba: 0, 0, 0, 0.7
        Rectangle:
            pos: self.pos
            size: self.size
        Color:
            rgba: 1, 1, 1, 0.2
        Line:
            width: 2
            rectangle: self.x, self.y, self.width, self.height
    
    Label:
        id: dialogue_text
        text: ''
        font_size: 18
        halign: 'left'
        valign: 'top'
        text_size: self.width - 20, None
        size_hint_y: 0.8
    
    BoxLayout:
        size_hint_y: 0.2
        Button:
            text: 'Continuar'
            size_hint_x: 0.3
            on_release: root.parent.close_dialogue()

<MenuItem@Button>:
    size_hint_y: None
    height: 60
    background_color: 0.2, 0.6, 1, 0.8
    font_size: 24
    text_size: self.size
    halign: 'center'
    valign: 'middle'
    padding: 10
    canvas.before:
        Color:
            rgba: 0.1, 0.1, 0.1, 0.5
        Line:
            width: 2
            rectangle: self.x, self.y, self.width, self.height

<StartScreen>:
    name: 'start'
    
    FloatLayout:
        id: background
        
        # Capa estática de fondo (montaña)
        Image:
            id: static_bg
            allow_stretch: True
            keep_ratio: False
            size: self.parent.size
        
        # Capa animada de niebla
        Image:
            id: fog_layer
            allow_stretch: True
            keep_ratio: False
            size: self.parent.size
            opacity: 0.7
        
        BoxLayout:
            orientation: 'vertical'
            size_hint: None, None
            size: 300, 400
            pos_hint: {'center_x': 0.5, 'center_y': 0.5}
            spacing: 20
            
            Image:
                id: logo
                size_hint: None, None
                size: 250, 100
                allow_stretch: True
            
            Button:
                text: 'JUGAR'
                font_size: 32
                on_release: root.manager.current = 'game_mode'
            
            Button:
                text: 'OPCIONES'
                font_size: 24
                on_release: root.manager.current = 'options'
            
            Button:
                text: 'SALIR'
                font_size: 24
                on_release: app.stop()

<GameModeScreen>:
    name: 'game_mode'
    
    FloatLayout:
        canvas:
            Color:
                rgba: 0.1, 0.1, 0.2, 1
            Rectangle:
                pos: self.pos
                size: self.size
        
        BoxLayout:
            orientation: 'vertical'
            size_hint: None, None
            size: 300, 300
            pos_hint: {'center_x': 0.5, 'center_y': 0.5}
            spacing: 20
            
            Label:
                text: 'SELECCIONA MODO DE JUEGO'
                font_size: 28
                size_hint_y: None
                height: 50
            
            Button:
                text: 'UN JUGADOR'
                font_size: 24
                on_release: 
                    app.set_game_mode('single'); 
                    root.manager.current = 'game'
            
            Button:
                text: 'MULTIJUGADOR LOCAL'
                font_size: 24
                on_release: 
                    app.set_game_mode('multi'); 
                    root.manager.current = 'multiplayer_setup'
            
            Button:
                text: 'VOLVER'
                font_size: 20
                on_release: root.manager.current = 'start'

<MultiplayerSetupScreen>:
    name: 'multiplayer_setup'
    
    FloatLayout:
        canvas:
            Color:
                rgba: 0.1, 0.1, 0.2, 1
            Rectangle:
                pos: self.pos
                size: self.size
        
        BoxLayout:
            orientation: 'vertical'
            size_hint: None, None
            size: 350, 350
            pos_hint: {'center_x': 0.5, 'center_y': 0.5}
            spacing: 20
            
            Label:
                text: 'CONFIGURACIÓN MULTIJUGADOR'
                font_size: 24
                size_hint_y: None
                height: 40
            
            Label:
                id: connection_status
                text: 'Esperando conexión...'
                font_size: 18
                size_hint_y: None
                height: 30
            
            BoxLayout:
                size_hint_y: None
                height: 200
                
                Button:
                    text: 'SERVIDOR\\n(HOST)'
                    font_size: 20
                    on_release: 
                        app.start_server(); 
                        root.update_status('Servidor iniciado. Esperando jugadores...')
            
            BoxLayout:
                size_hint_y: None
                height: 50
                
                Button:
                    text: 'CLIENTE'
                    font_size: 20
                    on_release: 
                        app.connect_to_server(); 
                        root.update_status('Conectando al servidor...')
            
            Button:
                text: 'VOLVER'
                font_size: 20
                on_release: root.manager.current = 'game_mode'

<OptionsScreen>:
    name: 'options'
    
    FloatLayout:
        canvas:
            Color:
                rgba: 0.1, 0.1, 0.2, 1
            Rectangle:
                pos: self.pos
                size: self.size
        
        BoxLayout:
            orientation: 'vertical'
            size_hint: None, None
            size: 300, 350
            pos_hint: {'center_x': 0.5, 'center_y': 0.5}
            spacing: 20
            
            Label:
                text: 'OPCIONES'
                font_size: 28
                size_hint_y: None
                height: 50
            
            BoxLayout:
                size_hint_y: None
                height: 50
                Label:
                    text: 'VOLUMEN MÚSICA:'
                    halign: 'right'
                    size_hint_x: 0.5
                Slider:
                    id: music_slider
                    min: 0
                    max: 1
                    value: 0.5
                    size_hint_x: 0.5
            
            BoxLayout:
                size_hint_y: None
                height: 50
                Label:
                    text: 'VOLUMEN EFECTOS:'
                    halign: 'right'
                    size_hint_x: 0.5
                Slider:
                    id: sfx_slider
                    min: 0
                    max: 1
                    value: 0.7
                    size_hint_x: 0.5
            
            Button:
                text: 'GUARDAR Y VOLVER'
                font_size: 20
                on_release: 
                    app.save_options(root); 
                    root.manager.current = 'start'
            
            Button:
                text: 'CANAL DE YOUTUBE'
                font_size: 18
                on_release: app.open_youtube()
            
            Button:
                text: 'INSTAGRAM'
                font_size: 18
                on_release: app.open_instagram()

<GameScreen>:
    name: 'game'
    
    FloatLayout:
        id: game_layout
        
        # Capa del mapa del juego
        GameMap:
            id: game_map
            size: self.parent.size
        
        # HUD inferior
        BoxLayout:
            id: hud
            size_hint: 1, None
            height: 100
            pos: 0, 0
            padding: 10
            spacing: 10
            
            # Información del personaje actual
            BoxLayout:
                size_hint_x: 0.3
                orientation: 'vertical'
                
                Label:
                    id: character_name
                    text: 'Alan'
                    font_size: 20
                    halign: 'left'
                    text_size: self.size
                
                HealthBar:
                    id: health_bar
                    pos: 10, 60
                
                ManaBar:
                    id: mana_bar
                    pos: 10, 35
                
                Label:
                    id: mission_label
                    text: 'Misión: Escapa de la montaña'
                    font_size: 16
                    halign: 'left'
                    text_size: self.size
            
            # Inventario rápido
            BoxLayout:
                size_hint_x: 0.2
                spacing: 5
                
                QuickSlot:
                    id: quick_slot1
                    image_source: ''
                
                QuickSlot:
                    id: quick_slot2
                    image_source: ''
                
                QuickSlot:
                    id: quick_slot3
                    image_source: ''
            
            # Espacio vacío
            Widget:
                size_hint_x: 0.2
            
            # Botones de acción
            BoxLayout:
                size_hint_x: 0.3
                spacing: 10
                
                ActionButton:
                    on_release: root.interact()
                
                ActionButtonX:
                    on_release: root.jump()
                
                ActionButtonB:
                    on_release: root.push()
                
                ActionButtonY:
                    on_release: root.switch_character()
        
        # Joystick virtual
        Joystick:
            id: joystick
            pos: 30, 30
            
        # Diálogo NPC
        DialogueBox:
            id: dialogue_box
            size: 0, 0  # Inicialmente oculto

<CombatScreen>:
    name: 'combat'
    
    FloatLayout:
        canvas:
            Color:
                rgba: 0.05, 0.05, 0.15, 1
            Rectangle:
                pos: self.pos
                size: self.size
        
        # Personaje del jugador
        BoxLayout:
            orientation: 'vertical'
            size_hint: None, None
            size: 150, 200
            pos_hint: {'x': 0.1, 'y': 0.3}
            
            Image:
                id: player_image
                size: 64, 96  # Tamaño proporcional al sprite
            
            HealthBar:
                id: player_health
                health: 100
                max_health: 100
            
            Label:
                text: 'Alan'
                font_size: 20
        
        # Enemigo
        BoxLayout:
            orientation: 'vertical'
            size_hint: None, None
            size: 150, 200
            pos_hint: {'right': 0.9, 'y': 0.3}
            
            Image:
                id: enemy_image
                size: 64, 64  # Tamaño proporcional al sprite
            
            HealthBar:
                id: enemy_health
                health: 40
                max_health: 40
            
            Label:
                id: enemy_name
                text: 'Lobo Salvaje'
                font_size: 20
        
        # Mensaje de combate
        Label:
            id: combat_message
            text: '¡Un lobo salvaje te ataca!'
            font_size: 24
            size_hint: None, None
            size: 400, 50
            pos_hint: {'center_x': 0.5, 'center_y': 0.7}
            halign: 'center'
            text_size: self.size
        
        # Opciones de combate
        BoxLayout:
            id: combat_options
            orientation: 'vertical'
            size_hint: None, None
            size: 200, 250
            pos_hint: {'center_x': 0.5, 'y': 0.1}
            spacing: 10
            
            Button:
                text: 'ATACAR'
                font_size: 20
                on_release: root.attack()
            
            Button:
                text: 'DEFENDER'
                font_size: 20
                on_release: root.defend()
            
            Button:
                text: 'OBJETOS'
                font_size: 20
                on_release: root.use_item()
            
            Button:
                text: 'HUIR'
                font_size: 20
                on_release: root.run_away()

<MemoryPuzzleScreen>:
    name: 'memory_puzzle'
    
    FloatLayout:
        canvas:
            Color:
                rgba: 0.1, 0.1, 0.2, 1
            Rectangle:
                pos: self.pos
                size: self.size
        
        Label:
            text: 'JUEGO DE MEMORIA'
            font_size: 32
            size_hint: None, None
            size: 300, 50
            pos_hint: {'center_x': 0.5, 'y': 0.85}
        
        GridLayout:
            id: puzzle_grid
            cols: 3
            rows: 3
            size_hint: None, None
            size: 300, 300
            pos_hint: {'center_x': 0.5, 'center_y': 0.5}
            spacing: 10
        
        Label:
            id: puzzle_message
            text: 'Observa la secuencia...'
            font_size: 20
            size_hint: None, None
            size: 300, 30
            pos_hint: {'center_x': 0.5, 'y': 0.2}

<StoreScreen>:
    name: 'store'
    
    FloatLayout:
        canvas:
            Color:
                rgba: 0.1, 0.1, 0.2, 1
            Rectangle:
                pos: self.pos
                size: self.size
        
        Label:
            text: 'TIENDA'
            font_size: 32
            size_hint: None, None
            size: 200, 50
            pos_hint: {'center_x': 0.5, 'y': 0.85}
        
        Label:
            id: gold_label
            text: 'Oro: 50'
            font_size: 24
            size_hint: None, None
            size: 200, 30
            pos_hint: {'x': 0.7, 'y': 0.8}
        
        BoxLayout:
            id: store_items
            orientation: 'vertical'
            size_hint: None, None
            size: 350, 400
            pos_hint: {'center_x': 0.5, 'center_y': 0.4}
            spacing: 10
'''

# Funciones para generar texturas de sprites
def create_texture_from_pixels(pixels, width, height):
    """Crea una textura de Kivy a partir de una matriz de píxeles"""
    # Convertir la matriz de píxeles a un buffer de bytes
    buffer = bytes()
    for row in pixels:
        for pixel in row:
            # Cada píxel es (r, g, b, a)
            buffer += struct.pack('BBBB', *pixel)
    
    # Crear la textura
    texture = Texture.create(size=(width, height), colorfmt='rgba')
    texture.blit_buffer(buffer, colorfmt='rgba', bufferfmt='ubyte')
    return texture

def create_character_texture(character_type, animation_frame=0):
    """Crea una textura para un personaje específico"""
    # Tamaño del sprite
    width, height = 32, 64  # Personajes son más altos que anchos
    
    # Matriz de píxeles inicial (fondo transparente)
    pixels = [[[0, 0, 0, 0] for _ in range(width)] for _ in range(height)]
    
    if character_type == 'alan':
        # Cuerpo - tono de piel
        skin_color = [220, 180, 140, 255]
        for y in range(20, 45):
            for x in range(12, 20):
                pixels[y][x] = skin_color
        
        # Pelo negro medio largo
        hair_color = [20, 20, 20, 255]
        for y in range(10, 20):
            for x in range(8, 24):
                if (x-16)**2 + (y-15)**2 < 40:  # Forma ovalada
                    pixels[y][x] = hair_color
        
        # Lentes azules
        glasses_color = [50, 100, 200, 255]
        for y in range(15, 18):
            for x in range(10, 14):
                pixels[y][x] = glasses_color
            for x in range(18, 22):
                pixels[y][x] = glasses_color
        # Patilla de los lentes
        for y in range(16, 20):
            pixels[y][9] = glasses_color
            pixels[y][22] = glasses_color
        
        # Campera negra desprendida
        jacket_color = [30, 30, 30, 255]
        for y in range(20, 35):
            for x in range(8, 24):
                if (x-16)**2/15 + (y-28)**2/40 < 10:  # Forma ovalada
                    pixels[y][x] = jacket_color
        
        # Remera gris
        shirt_color = [150, 150, 150, 255]
        for y in range(25, 40):
            for x in range(12, 20):
                pixels[y][x] = shirt_color
        
        # Pantalón azul
        pants_color = [50, 100, 200, 255]
        for y in range(40, 55):
            for x in range(10, 22):
                if abs(x-16) < 6 - (y-40)/3:  # Piernas estrechándose
                    pixels[y][x] = pants_color
        
        # Zapatillas blancas
        shoes_color = [240, 240, 240, 255]
        for y in range(55, 60):
            for x in range(8, 24):
                if (x-16)**2/20 + (y-57)**2 < 10:
                    pixels[y][x] = shoes_color
        
        # Mochila
        backpack_color = [80, 80, 80, 255]
        for y in range(25, 35):
            for x in range(6, 10):
                pixels[y][x] = backpack_color
        
        # Fierro en la mano (dependiendo del frame de animación)
        weapon_color = [100, 100, 100, 255]
        if animation_frame == 0:
            # Posición normal
            for y in range(30, 35):
                for x in range(22, 24):
                    pixels[y][x] = weapon_color
        elif animation_frame == 1:
            # Levantado
            for y in range(20, 25):
                for x in range(22, 24):
                    pixels[y][x] = weapon_color
        else:
            # Bajado
            for y in range(35, 40):
                for x in range(22, 24):
                    pixels[y][x] = weapon_color
    
    elif character_type == 'alexis':
        # Cuerpo - tono de piel
        skin_color = [220, 180, 140, 255]
        for y in range(20, 45):
            for x in range(12, 20):
                pixels[y][x] = skin_color
        
        # Pelo corto negro
        hair_color = [20, 20, 20, 255]
        for y in range(10, 16):
            for x in range(10, 22):
                if (x-16)**2/10 + (y-13)**2 < 15:
                    pixels[y][x] = hair_color
        
        # Cabeza medianamente cuadrada
        for y in range(10, 20):
            for x in range(10, 22):
                if (x-16)**2 < 30 and (y-15)**2 < 20:
                    pixels[y][x] = skin_color
        
        # Remera manga corta azul oscuro
        shirt_color = [30, 60, 150, 255]
        for y in range(20, 35):
            for x in range(10, 22):
                if (x-16)**2/15 + (y-28)**2/25 < 10:
                    pixels[y][x] = shirt_color
        
        # Mangas
        sleeve_color = [20, 40, 100, 255]
        for y in range(20, 28):
            for x in range(8, 10):
                pixels[y][x] = sleeve_color
            for x in range(22, 24):
                pixels[y][x] = sleeve_color
        
        # Pantalón blanco amarillento
        pants_color = [220, 210, 150, 255]
        for y in range(35, 55):
            for x in range(10, 22):
                if abs(x-16) < 6 - (y-35)/4:
                    pixels[y][x] = pants_color
        
        # Zapatillas negras
        shoes_color = [30, 30, 30, 255]
        for y in range(55, 60):
            for x in range(8, 24):
                if (x-16)**2/20 + (y-57)**2 < 10:
                    pixels[y][x] = shoes_color
        
        # Mochila
        backpack_color = [50, 100, 50, 255]
        for y in range(25, 35):
            for x in range(6, 10):
                pixels[y][x] = backpack_color
        
        # Cuchillo en la mano (dependiendo del frame de animación)
        weapon_color = [200, 200, 200, 255]
        blade_color = [150, 150, 150, 255]
        if animation_frame == 0:
            # Posición normal
            for y in range(30, 33):
                for x in range(22, 24):
                    pixels[y][x] = weapon_color
        elif animation_frame == 1:
            # Lanzando
            for y in range(25, 30):
                for x in range(24, 28):
                    pixels[y][x] = blade_color
        else:
            # Bajado
            for y in range(33, 36):
                for x in range(22, 24):
                    pixels[y][x] = weapon_color
    
    elif character_type == 'joaquin':
        # Cuerpo - tono de piel
        skin_color = [220, 180, 140, 255]
        for y in range(20, 45):
            for x in range(12, 20):
                pixels[y][x] = skin_color
        
        # Pelo con rulos
        hair_color = [80, 50, 20, 255]
        for y in range(8, 16):
            for x in range(8, 24):
                if (x-16)**2/10 + (y-12)**2 < 15:
                    pixels[y][x] = hair_color
        
        # Rulos (círculos pequeños)
        for y in range(10, 15):
            for x in range(10, 22):
                if (x-13)**2 + (y-12)**2 < 3 or (x-19)**2 + (y-12)**2 < 3:
                    pixels[y][x] = hair_color
        
        # Remera manga corta blanca
        shirt_color = [240, 240, 240, 255]
        for y in range(20, 35):
            for x in range(10, 22):
                if (x-16)**2/15 + (y-28)**2/25 < 10:
                    pixels[y][x] = shirt_color
        
        # Shorts azules
        shorts_color = [50, 100, 200, 255]
        for y in range(35, 45):
            for x in range(10, 22):
                if abs(x-16) < 6 - (y-35)/2:
                    pixels[y][x] = shorts_color
        
        # Zapatillas chanclas
        sandal_color = [150, 100, 50, 255]
        for y in range(55, 58):
            for x in range(12, 20):
                pixels[y][x] = sandal_color
            # Correa
            for y in range(53, 56):
                pixels[y][16] = sandal_color
    
    elif character_type == 'monstruo':
        # Cuerpo musculoso - tono de piel oscuro
        skin_color = [100, 70, 50, 255]
        for y in range(20, 45):
            for x in range(10, 22):
                if (x-16)**2/15 + (y-30)**2/25 < 10:
                    pixels[y][x] = skin_color
        
        # Cabeza de venado
        deer_color = [120, 80, 50, 255]
        # Cabeza
        for y in range(5, 20):
            for x in range(8, 24):
                if (x-16)**2/15 + (y-12)**2/10 < 10:
                    pixels[y][x] = deer_color
        # Ojos
        for y in range(10, 12):
            for x in range(12, 14):
                pixels[y][x] = [0, 0, 0, 255]
            for x in range(18, 20):
                pixels[y][x] = [0, 0, 0, 255]
        # Cuernos
        for y in range(0, 10):
            for x in range(14, 18):
                if (x-16)**2 + (y-5)**2 < 5:
                    pixels[y][x] = [80, 50, 20, 255]
        
        # Pantalón corto roto
        pants_color = [100, 80, 60, 255]
        for y in range(40, 50):
            for x in range(10, 22):
                if abs(x-16) < 6 - (y-40)/2:
                    pixels[y][x] = pants_color
        # Roturas
        for y in range(42, 48):
            pixels[y][12] = [20, 20, 20, 255]
            pixels[y][20] = [20, 20, 20, 255]
        
        # Arco y flechas (dependiendo del frame de animación)
        bow_color = [100, 70, 40, 255]
        string_color = [200, 200, 200, 255]
        if animation_frame == 0:
            # Arco normal
            for y in range(25, 35):
                for x in range(6, 8):
                    pixels[y][x] = bow_color
            for y in range(25, 35):
                pixels[y][7] = string_color
        elif animation_frame == 1:
            # Arco tensado
            for y in range(25, 35):
                for x in range(4, 6):
                    pixels[y][x] = bow_color
            for y in range(25, 35):
                pixels[y][5] = string_color
        else:
            # Flecha lanzada
            arrow_color = [150, 100, 50, 255]
            tip_color = [200, 200, 200, 255]
            for y in range(28, 32):
                for x in range(20, 28):
                    pixels[y][x] = arrow_color
                pixels[y][27] = tip_color
    
    elif character_type == 'npc':
        # Cuerpo - tono de piel
        skin_color = [220, 180, 140, 255]
        for y in range(20, 45):
            for x in range(12, 20):
                pixels[y][x] = skin_color
        
        # Pelo marrón
        hair_color = [100, 70, 50, 255]
        for y in range(10, 18):
            for x in range(10, 22):
                if (x-16)**2/10 + (y-14)**2 < 15:
                    pixels[y][x] = hair_color
        
        # Sombrero
        hat_color = [100, 50, 50, 255]
        for y in range(5, 10):
            for x in range(8, 24):
                if (x-16)**2/15 + (y-7)**2 < 15:
                    pixels[y][x] = hat_color
        
        # Camisa azul
        shirt_color = [50, 100, 200, 255]
        for y in range(20, 35):
            for x in range(10, 22):
                if (x-16)**2/15 + (y-28)**2/25 < 10:
                    pixels[y][x] = shirt_color
        
        # Pantalones marrones
        pants_color = [120, 80, 50, 255]
        for y in range(35, 55):
            for x in range(10, 22):
                if abs(x-16) < 6 - (y-35)/3:
                    pixels[y][x] = pants_color
    
    # Aplicar efecto de animación si es necesario
    if animation_frame > 0 and character_type in ['alan', 'alexis', 'joaquin', 'monstruo']:
        # Pequeño movimiento en los brazos o piernas
        arm_color = [220, 180, 140, 255]  # Color de piel para brazos
        if animation_frame == 1:
            # Brazo izquierdo levantado
            for y in range(25, 30):
                for x in range(8, 10):
                    pixels[y][x] = arm_color
        elif animation_frame == 2:
            # Brazo derecho levantado
            for y in range(25, 30):
                for x in range(22, 24):
                    pixels[y][x] = arm_color
    
    return create_texture_from_pixels(pixels, width, height)

def create_item_texture(item_type):
    """Crea una textura para un item específico"""
    width, height = 32, 32
    
    # Matriz de píxeles inicial (fondo transparente)
    pixels = [[[0, 0, 0, 0] for _ in range(width)] for _ in range(height)]
    
    if item_type == 'pocion_salud':
        # Botella roja
        bottle_color = [200, 50, 50, 255]
        for y in range(10, 25):
            for x in range(12, 20):
                if (x-16)**2/10 + (y-18)**2/20 < 5:
                    pixels[y][x] = bottle_color
        # Tapón
        cap_color = [100, 100, 100, 255]
        for y in range(8, 10):
            for x in range(14, 18):
                pixels[y][x] = cap_color
    
    elif item_type == 'pocion_mana':
        # Botella azul
        bottle_color = [50, 50, 200, 255]
        for y in range(10, 25):
            for x in range(12, 20):
                if (x-16)**2/10 + (y-18)**2/20 < 5:
                    pixels[y][x] = bottle_color
        # Tapón
        cap_color = [100, 100, 100, 255]
        for y in range(8, 10):
            for x in range(14, 18):
                pixels[y][x] = cap_color
    
    elif item_type == 'comida':
        # Manzana roja
        apple_color = [200, 50, 50, 255]
        for y in range(10, 22):
            for x in range(10, 22):
                if (x-16)**2 + (y-16)**2 < 30:
                    pixels[y][x] = apple_color
        # Tallo
        stem_color = [100, 70, 50, 255]
        for y in range(8, 10):
            for x in range(15, 17):
                pixels[y][x] = stem_color
    
    elif item_type == 'espada':
        # Mango marrón
        handle_color = [120, 80, 50, 255]
        for y in range(20, 30):
            for x in range(14, 18):
                pixels[y][x] = handle_color
        # Hoja gris
        blade_color = [150, 150, 150, 255]
        for y in range(10, 20):
            for x in range(12, 20):
                if (x-16)**2/5 + (y-15)**2/15 < 5:
                    pixels[y][x] = blade_color
        # Pomo
        pommel_color = [200, 200, 100, 255]
        for y in range(30, 32):
            for x in range(14, 18):
                pixels[y][x] = pommel_color
    
    return create_texture_from_pixels(pixels, width, height)

def create_enemy_texture(enemy_type, animation_frame=0):
    """Crea una textura para un enemigo específico"""
    width, height = 32, 32
    
    # Matriz de píxeles inicial (fondo transparente)
    pixels = [[[0, 0, 0, 0] for _ in range(width)] for _ in range(height)]
    
    if enemy_type == 'lobo':
        # Cuerpo gris
        body_color = [100, 100, 100, 255]
        for y in range(10, 25):
            for x in range(8, 24):
                if (x-16)**2/20 + (y-18)**2/10 < 10:
                    pixels[y][x] = body_color
        
        # Patas
        leg_color = [80, 80, 80, 255]
        for y in range(25, 30):
            for x in range(10, 13):
                pixels[y][x] = leg_color
            for x in range(19, 22):
                pixels[y][x] = leg_color
        
        # Cabeza
        for y in range(5, 15):
            for x in range(5, 15):
                if (x-10)**2 + (y-10)**2 < 20:
                    pixels[y][x] = body_color
        
        # Ojos rojos
        eye_color = [200, 50, 50, 255]
        pixels[8][8] = eye_color
        pixels[8][12] = eye_color
    
    elif enemy_type == 'oso':
        # Cuerpo marrón
        body_color = [120, 80, 50, 255]
        for y in range(10, 25):
            for x in range(8, 24):
                if (x-16)**2/15 + (y-18)**2/10 < 10:
                    pixels[y][x] = body_color
        
        # Patas
        leg_color = [100, 60, 30, 255]
        for y in range(25, 30):
            for x in range(10, 13):
                pixels[y][x] = leg_color
            for x in range(19, 22):
                pixels[y][x] = leg_color
        
        # Cabeza
        for y in range(5, 15):
            for x in range(5, 15):
                if (x-10)**2 + (y-10)**2 < 20:
                    pixels[y][x] = body_color
        
        # Ojos negros
        eye_color = [20, 20, 20, 255]
        pixels[8][8] = eye_color
        pixels[8][12] = eye_color
    
    elif enemy_type == 'monstruo':
        return create_character_texture('monstruo', animation_frame)
    
    return create_texture_from_pixels(pixels, width, height)

def create_background_texture(background_type):
    """Crea una textura para un fondo específico"""
    width, height = int(Window.width), int(Window.height)
    
    # Matriz de píxeles inicial
    pixels = [[[0, 0, 0, 255] for _ in range(width)] for _ in range(height)]
    
    if background_type == 'mountain_static':
        # Fondo de montaña estático
        mountain_color = [100, 100, 100, 255]
        sky_color = [135, 206, 235, 255]  # Azul cielo
        
        # Cielo
        for y in range(height):
            for x in range(width):
                # Gradiente suave del cielo
                sky_intensity = min(255, 200 + y // 3)
                pixels[y][x] = [sky_color[0], sky_color[1], sky_color[2], 255]
        
        # Montañas lejanas
        mountain_color_far = [80, 80, 80, 255]
        for i in range(3):
            start_x = i * width // 3 - width // 6
            for x in range(width // 3):
                mountain_height = int(height * 0.4 * (1 - abs(x - width // 6) / (width // 6)))
                for y in range(height - mountain_height, height):
                    pixels[y][start_x + x] = mountain_color_far
        
        # Montañas cercanas
        for i in range(2):
            start_x = i * width // 2 - width // 4
            for x in range(width // 2):
                mountain_height = int(height * 0.6 * (1 - abs(x - width // 4) / (width // 4)))
                for y in range(height - mountain_height, height):
                    pixels[y][start_x + x] = mountain_color
        
        # Suelo
        ground_color = [50, 100, 50, 255]  # Verde para el pasto
        for y in range(int(height * 0.7), height):
            for x in range(width):
                pixels[y][x] = ground_color
    
    elif background_type == 'fog':
        # Niebla con movimiento suave
        fog_color = [200, 200, 200, 100]
        for y in range(height):
            for x in range(width):
                # Patrón de niebla con ruido
                noise = int(20 * math.sin(x / 20) * math.cos(y / 30))
                alpha = 80 + noise
                alpha = max(50, min(120, alpha))
                pixels[y][x] = [200, 200, 200, alpha]
    
    elif background_type == 'logo':
        # Logo del juego
        width, height = 250, 100
        pixels = [[[0, 0, 0, 0] for _ in range(width)] for _ in range(height)]
        
        # Texto "Aventura en la Montaña"
        text_color = [50, 100, 200, 255]
        
        # Dibujar texto simplificado (A)
        for y in range(20, 80):
            for x in range(20, 40):
                if (x-30)**2/100 + (y-50)**2/400 < 1:
                    pixels[y][x] = text_color
        
        # Dibujar montaña
        mountain_color = [100, 100, 100, 255]
        for x in range(60, 200):
            mountain_height = 60 * (1 - abs(x - 130) / 70)
            for y in range(40, 40 + int(mountain_height)):
                pixels[y][x] = mountain_color
        
        # Sol
        sun_color = [255, 255, 100, 255]
        for y in range(20, 40):
            for x in range(180, 200):
                if (x-190)**2 + (y-30)**2 < 60:
                    pixels[y][x] = sun_color
    
    return create_texture_from_pixels(pixels, width, height)

# Funciones para generar sonidos programáticamente
def generate_sine_wave(frequency, duration, sample_rate=44100):
    """Genera una onda sinusoidal como buffer de audio"""
    num_samples = int(duration * sample_rate)
    buffer = array.array('h')
    
    for i in range(num_samples):
        value = int(32767.0 * math.sin(2.0 * math.pi * frequency * i / sample_rate))
        buffer.append(value)
    
    return buffer

def generate_city_sound():
    """Genera un sonido tranquilo de ciudad para RPG"""
    # Crear un buffer de 2 segundos
    duration = 2.0
    sample_rate = 44100
    num_samples = int(duration * sample_rate)
    
    # Usamos un buffer de 16-bit signed (formato PCM)
    buffer = array.array('h', [0] * num_samples)
    
    # Añadir sonido ambiental suave
    for i in range(num_samples):
        # Sonido de fondo muy suave (tono bajo)
        buffer[i] += int(500 * math.sin(2.0 * math.pi * 87.31 * i / sample_rate))
        
        # Sonido ocasional de campana (cada 0.5 segundos)
        if i % int(sample_rate * 0.5) < 100:
            buffer[i] += int(2000 * math.sin(2.0 * math.pi * 440 * i / sample_rate))
        
        # Sonido de pájaros suaves
        if random.random() < 0.01:
            bird_freq = 800 + random.randint(0, 400)
            for j in range(100):
                if i + j < num_samples:
                    buffer[i + j] += int(1000 * math.sin(2.0 * math.pi * bird_freq * (i + j) / sample_rate))
    
    # Normalizar y convertir a bytes
    max_val = max(abs(min(buffer)), abs(max(buffer)))
    if max_val > 0:
        scale = 32767 / max_val
        buffer = array.array('h', [int(x * scale) for x in buffer])
    
    return struct.pack('<' + 'h' * len(buffer), *buffer)

def generate_mountain_sound():
    """Genera un sonido de suspenso para la montaña"""
    duration = 2.0
    sample_rate = 44100
    num_samples = int(duration * sample_rate)
    
    buffer = array.array('h', [0] * num_samples)
    
    # Sonido de suspenso (tonos bajos y lentos)
    for i in range(num_samples):
        # Base de suspenso
        buffer[i] += int(1000 * math.sin(2.0 * math.pi * 55.0 * i / sample_rate))
        
        # Sonido de viento
        wind_freq = 20 + 10 * math.sin(i / 10000.0)
        buffer[i] += int(500 * math.sin(2.0 * math.pi * wind_freq * i / sample_rate))
        
        # Sonido de arroyo ocasional
        if random.random() < 0.05:
            stream_freq = 1000 + random.randint(0, 500)
            for j in range(200):
                if i + j < num_samples:
                    buffer[i + j] += int(800 * math.sin(2.0 * math.pi * stream_freq * (i + j) / sample_rate))
        
        # Sonido de hojas moviéndose
        if random.random() < 0.02:
            for j in range(50):
                if i + j < num_samples:
                    rustle_freq = 500 + random.randint(0, 500)
                    buffer[i + j] += int(300 * math.sin(2.0 * math.pi * rustle_freq * (i + j) / sample_rate))
    
    # Normalizar
    max_val = max(abs(min(buffer)), abs(max(buffer)))
    if max_val > 0:
        scale = 32767 / max_val
        buffer = array.array('h', [int(x * scale) for x in buffer])
    
    return struct.pack('<' + 'h' * len(buffer), *buffer)

def generate_footstep_sound():
    """Genera un sonido de pasos"""
    duration = 0.3
    sample_rate = 44100
    num_samples = int(duration * sample_rate)
    
    buffer = array.array('h', [0] * num_samples)
    
    # Sonido de paso en tierra
    for i in range(num_samples):
        # Frecuencia decreciente para simular impacto
        freq = 200 - (i / num_samples) * 150
        # Amplitud decreciente
        amp = 3000 * (1 - i / num_samples) ** 2
        buffer[i] = int(amp * math.sin(2.0 * math.pi * freq * i / sample_rate))
    
    return struct.pack('<' + 'h' * len(buffer), *buffer)

def generate_monster_roar():
    """Genera un rugido del monstruo"""
    duration = 1.0
    sample_rate = 44100
    num_samples = int(duration * sample_rate)
    
    buffer = array.array('h', [0] * num_samples)
    
    # Rugido profundo
    for i in range(num_samples):
        # Frecuencia variable para efecto de rugido
        base_freq = 80 + 20 * math.sin(i / 5000.0)
        variation = 10 * math.sin(i / 1000.0)
        freq = base_freq + variation
        
        # Amplitud alta al principio, luego decae
        amp = 8000 * (1 - i / num_samples) ** 1.5
        
        # Añadir armónicos para hacerlo más rugoso
        harmonic1 = 0.3 * amp * math.sin(2.0 * math.pi * freq * 2 * i / sample_rate)
        harmonic2 = 0.1 * amp * math.sin(2.0 * math.pi * freq * 3 * i / sample_rate)
        
        buffer[i] = int(amp * math.sin(2.0 * math.pi * freq * i / sample_rate) + harmonic1 + harmonic2)
    
    # Normalizar
    max_val = max(abs(min(buffer)), abs(max(buffer)))
    if max_val > 0:
        scale = 32767 / max_val
        buffer = array.array('h', [int(x * scale) for x in buffer])
    
    return struct.pack('<' + 'h' * len(buffer), *buffer)

class GameMap(Widget):
    """Representa el mapa del juego donde ocurre la acción"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._keyboard = None
        self.current_character = 'alan'
        self.characters = {}
        self.npcs = {}
        self.items = {}
        self.enemies = {}
        self.map_size = (2000, 2000)  # Tamaño del mapa (más grande que la pantalla)
        self.camera_x = 0
        self.camera_y = 0
        self.target_camera_x = 0
        self.target_camera_y = 0
        self.camera_speed = 5
        self.animation_frame = 0
        self.animation_time = 0
        
        # Cargar el mapa (en un proyecto real, esto vendría de un archivo Tiled)
        self.create_map()
        
        # Registrar el teclado
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down=self._on_keyboard_down)
    
    def _keyboard_closed(self):
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None
    
    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        # Para pruebas en escritorio
        if keycode[1] == 'w':
            self.characters[self.current_character].move(0, PLAYER_SPEED)
        elif keycode[1] == 's':
            self.characters[self.current_character].move(0, -PLAYER_SPEED)
        elif keycode[1] == 'a':
            self.characters[self.current_character].move(-PLAYER_SPEED, 0)
        elif keycode[1] == 'd':
            self.characters[self.current_character].move(PLAYER_SPEED, 0)
        return True
    
    def create_map(self):
        """Crea un mapa simple con terreno y objetos"""
        with self.canvas:
            # Fondo del mapa
            Color(0.3, 0.6, 0.2, 1)  # Verde para el pasto
            Rectangle(pos=(0, 0), size=self.map_size)
            
            # Caminos
            Color(0.6, 0.5, 0.3, 1)  # Tierra
            # Camino principal
            Rectangle(pos=(500, 0), size=(200, 2000))
            Rectangle(pos=(0, 800), size=(2000, 200))
            
            # Rocas
            Color(0.4, 0.4, 0.4, 1)
            for i in range(10):
                x = random.randint(100, 1900)
                y = random.randint(100, 1900)
                size = random.randint(30, 80)
                Rectangle(pos=(x, y), size=(size, size))
            
            # Árboles
            Color(0.2, 0.5, 0.2, 1)
            for i in range(30):
                x = random.randint(50, 1950)
                y = random.randint(50, 1950)
                size = random.randint(20, 40)
                Rectangle(pos=(x, y), size=(size, size * 2))
        
        # Crear personajes
        self.create_characters()
        
        # Crear NPCs
        self.create_npcs()
        
        # Crear items
        self.create_items()
        
        # Crear enemigos
        self.create_enemies()
    
    def create_characters(self):
        """Crea los personajes jugables"""
        for char_id, char_data in CHARACTERS.items():
            char = Character(
                char_id=char_id,
                name=char_data['name'],
                max_health=char_data['max_health'],
                max_mana=char_data['max_mana'],
                attack=char_data['attack'],
                defense=char_data['defense'],
                speed=char_data['speed']
            )
            char.pos = (100, 100) if char_id == 'alan' else (150, 100)
            char.visible = (char_id == 'alan')  # Solo el primero es visible al inicio
            self.add_widget(char)
            self.characters[char_id] = char
    
    def create_npcs(self):
        """Crea NPCs en el mapa"""
        # Ejemplo de NPC
        npc = NPC(
            name="Montañista Perdido",
            dialogue=[
                "¡Ayuda! Me he perdido en esta montaña.",
                "Dicen que hay un monstruo ancestral en lo profundo de la cueva...",
                "Si encuentras mi mochila, te daré algo a cambio."
            ]
        )
        npc.pos = (800, 500)
        self.add_widget(npc)
        self.npcs["npc_1"] = npc
    
    def create_items(self):
        """Crea items recolectables en el mapa"""
        # Ejemplo de item
        item = Item(
            item_id="pocion_salud",
            name="Poción de Salud",
            description="Restaura 30 puntos de salud"
        )
        item.pos = (600, 300)
        self.add_widget(item)
        self.items["item_1"] = item
    
    def create_enemies(self):
        """Crea enemigos en el mapa"""
        # Ejemplo de enemigo
        enemy = Enemy(
            enemy_id="lobo",
            name="Lobo Salvaje",
            health=40,
            max_health=40,
            attack=8,
            defense=5,
            speed=7
        )
        enemy.pos = (1000, 800)
        self.add_widget(enemy)
        self.enemies["enemy_1"] = enemy
    
    def update(self, dt):
        """Actualiza el estado del mapa y la cámara"""
        # Actualizar animación
        self.animation_time += dt
        if self.animation_time > 0.2:
            self.animation_time = 0
            self.animation_frame = (self.animation_frame + 1) % 3
        
        # Actualizar personajes
        for char in self.characters.values():
            if char.visible:
                # Actualizar posición de la cámara para seguir al personaje
                self.target_camera_x = char.x - SCREEN_WIDTH / 2 + char.width / 2
                self.target_camera_y = char.y - SCREEN_HEIGHT / 2 + char.height / 2
                
                # Limitar la cámara al tamaño del mapa
                self.target_camera_x = max(0, min(self.target_camera_x, self.map_size[0] - SCREEN_WIDTH))
                self.target_camera_y = max(0, min(self.target_camera_y, self.map_size[1] - SCREEN_HEIGHT))
        
        # Mover la cámara suavemente hacia el objetivo
        self.camera_x += (self.target_camera_x - self.camera_x) / self.camera_speed
        self.camera_y += (self.target_camera_y - self.camera_y) / self.camera_speed
        
        # Aplicar la transformación de la cámara
        self.canvas.before.clear()
        with self.canvas.before:
            # Aplicar la transformación de la cámara
            Rectangle(texture=self.get_background_texture(), pos=(0, 0), size=(SCREEN_WIDTH, SCREEN_HEIGHT))
            Color(1, 1, 1, 1)
            self.transform = Rectangle(pos=(0, 0), size=(SCREEN_WIDTH, SCREEN_HEIGHT))
    
    def get_background_texture(self):
        """Devuelve la textura del fondo actual"""
        # En un proyecto real, esto cambiaría según la ubicación
        return create_background_texture('mountain_static')
    
    def check_collisions(self):
        """Verifica colisiones entre el personaje actual y otros objetos"""
        current_char = self.characters[self.current_character]
        
        # Colisión con NPCs
        for npc_id, npc in self.npcs.items():
            if self.check_collision(current_char, npc):
                return "npc", npc_id
        
        # Colisión con items
        for item_id, item in self.items.items():
            if self.check_collision(current_char, item):
                return "item", item_id
        
        # Colisión con enemigos
        for enemy_id, enemy in self.enemies.items():
            if self.check_collision(current_char, enemy):
                return "enemy", enemy_id
        
        return None, None
    
    def check_collision(self, obj1, obj2):
        """Verifica si dos objetos están colisionando"""
        return (abs(obj1.center_x - obj2.center_x) < (obj1.width + obj2.width) / 2 and
                abs(obj1.center_y - obj2.center_y) < (obj1.height + obj2.height) / 2)

class Character(Widget):
    """Representa un personaje jugable"""
    
    char_id = StringProperty('')
    name = StringProperty('')
    health = NumericProperty(100)
    max_health = NumericProperty(100)
    mana = NumericProperty(50)
    max_mana = NumericProperty(50)
    attack = NumericProperty(10)
    defense = NumericProperty(5)
    speed = NumericProperty(5)
    visible = BooleanProperty(True)
    
    # Estado de animación
    anim_frame = NumericProperty(0)
    anim_time = NumericProperty(0)
    anim_direction = StringProperty('down')
    anim_state = StringProperty('idle')  # idle, walking, attacking
    
    def __init__(self, char_id, name, max_health, max_mana, attack, defense, speed, **kwargs):
        super().__init__(**kwargs)
        self.char_id = char_id
        self.name = name
        self.max_health = max_health
        self.health = max_health
        self.max_mana = max_mana
        self.mana = max_mana
        self.attack = attack
        self.defense = defense
        self.speed = speed
        self.size = (TILE_SIZE, TILE_SIZE * 2)  # Tamaño del sprite (asumiendo que es más alto que ancho)
        
        # Crear y añadir el sprite
        self.sprite = Image(
            size=self.size,
            allow_stretch=True
        )
        self.update_sprite()
        self.add_widget(self.sprite)
    
    def move(self, dx, dy):
        """Mueve al personaje en la dirección dada"""
        if dx != 0 or dy != 0:
            self.anim_state = 'walking'
            
            # Determinar dirección para la animación
            if abs(dx) > abs(dy):
                self.anim_direction = 'right' if dx > 0 else 'left'
            else:
                self.anim_direction = 'down' if dy > 0 else 'up'
        else:
            self.anim_state = 'idle'
        
        # Actualizar posición
        self.x += dx
        self.y += dy
    
    def update_sprite(self):
        """Actualiza el sprite del personaje según su estado"""
        # Determinar el frame de animación
        anim_frame = 0
        if self.anim_state == 'walking':
            # Usar el frame actual de animación del mapa
            anim_frame = self.parent.animation_frame
        
        # Crear la textura
        texture = create_character_texture(self.char_id, anim_frame)
        
        # Actualizar el sprite
        self.sprite.texture = texture
    
    def attack_enemy(self, enemy):
        """Ataca a un enemigo"""
        damage = max(1, self.attack - enemy.defense)
        enemy.health = max(0, enemy.health - damage)
        return damage
    
    def take_damage(self, damage):
        """Recibe daño"""
        actual_damage = max(1, damage - self.defense)
        self.health = max(0, self.health - actual_damage)
        return actual_damage

class NPC(Widget):
    """Representa un personaje no jugable (NPC)"""
    
    name = StringProperty('')
    dialogue = ListProperty([])
    
    def __init__(self, name, dialogue, **kwargs):
        super().__init__(**kwargs)
        self.name = name
        self.dialogue = dialogue
        self.size = (TILE_SIZE, TILE_SIZE * 2)
        
        # Crear y añadir el sprite
        self.sprite = Image(
            size=self.size,
            allow_stretch=True
        )
        self.sprite.texture = create_character_texture('npc')
        self.add_widget(self.sprite)

class Item(Widget):
    """Representa un item recolectable"""
    
    item_id = StringProperty('')
    name = StringProperty('')
    description = StringProperty('')
    
    def __init__(self, item_id, name, description, **kwargs):
        super().__init__(**kwargs)
        self.item_id = item_id
        self.name = name
        self.description = description
        self.size = (TILE_SIZE, TILE_SIZE)
        
        # Crear y añadir el sprite
        self.sprite = Image(
            size=self.size,
            allow_stretch=True
        )
        self.sprite.texture = create_item_texture(item_id)
        self.add_widget(self.sprite)

class Enemy(Widget):
    """Representa un enemigo"""
    
    enemy_id = StringProperty('')
    name = StringProperty('')
    health = NumericProperty(40)
    max_health = NumericProperty(40)
    attack = NumericProperty(8)
    defense = NumericProperty(5)
    speed = NumericProperty(7)
    
    def __init__(self, enemy_id, name, health, max_health, attack, defense, speed, **kwargs):
        super().__init__(**kwargs)
        self.enemy_id = enemy_id
        self.name = name
        self.health = health
        self.max_health = max_health
        self.attack = attack
        self.defense = defense
        self.speed = speed
        self.size = (TILE_SIZE * 1.5, TILE_SIZE * 1.5)  # Enemigos pueden ser más grandes
        
        # Crear y añadir el sprite
        self.sprite = Image(
            size=self.size,
            allow_stretch=True
        )
        self.sprite.texture = create_enemy_texture(enemy_id)
        self.add_widget(self.sprite)

class StartScreen(Screen):
    def on_enter(self, *args):
        """Se llama cuando la pantalla se muestra"""
        # Crear texturas para el fondo y el logo
        self.ids.static_bg.texture = create_background_texture('mountain_static')
        self.ids.fog_layer.texture = create_background_texture('fog')
        self.ids.logo.texture = create_background_texture('logo')

class GameModeScreen(Screen):
    pass

class MultiplayerSetupScreen(Screen):
    def update_status(self, message):
        self.ids.connection_status.text = message

class OptionsScreen(Screen):
    pass

class GameScreen(Screen):
    current_character = StringProperty('alan')
    game_state = StringProperty('exploring')  # exploring, combat, puzzle, dialogue
    dialogue_active = BooleanProperty(False)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.player_inventory = {
            'pocion_salud': 3,
            'pocion_mana': 2,
            'comida': 5
        }
        self.gold = 50
        self.current_mission = "Escapa de la montaña"
        self.dialogue_queue = deque()
        self.dialogue_npc = None
        self.combat_enemy = None
        self.memory_puzzle = None
        
        # Generar y guardar sonidos
        self.sounds = {
            'city': self.create_sound_from_buffer(generate_city_sound()),
            'mountain': self.create_sound_from_buffer(generate_mountain_sound()),
            'footstep': self.create_sound_from_buffer(generate_footstep_sound()),
            'monster_roar': self.create_sound_from_buffer(generate_monster_roar())
        }
        
        # Reproducir sonido de montaña
        if self.sounds['mountain']:
            self.sounds['mountain'].play()
    
    def create_sound_from_buffer(self, buffer):
        """Crea un objeto Sound a partir de un buffer de audio"""
        try:
            # Crear un archivo temporal
            import tempfile
            import os
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as f:
                # Escribir encabezado WAV
                import wave
                with wave.open(f.name, 'wb') as wav_file:
                    wav_file.setnchannels(1)
                    wav_file.setsampwidth(2)  # 16-bit
                    wav_file.setframerate(44100)
                    wav_file.writeframes(buffer)
                
                # Cargar el sonido
                return SoundLoader.load(f.name)
        except:
            return None
    
    def on_pre_enter(self, *args):
        """Se llama antes de que la pantalla sea mostrada"""
        # Inicializar el juego
        self.init_game()
        # Programar la actualización del juego
        Clock.schedule_interval(self.update, 1.0/60.0)
    
    def on_leave(self, *args):
        """Se llama cuando la pantalla es abandonada"""
        # Cancelar la actualización del juego
        Clock.unschedule(self.update)
        
        # Detener sonidos
        if self.sounds['mountain']:
            self.sounds['mountain'].stop()
    
    def init_game(self):
        """Inicializa el estado del juego"""
        # Cargar progreso guardado si existe
        self.load_game()
        
        # Configurar HUD
        self.update_hud()
    
    def update(self, dt):
        """Actualiza el estado del juego"""
        # Actualizar el mapa
        self.ids.game_map.update(dt)
        
        # Verificar colisiones
        if self.game_state == 'exploring':
            obj_type, obj_id = self.ids.game_map.check_collisions()
            if obj_type == 'npc':
                self.start_dialogue(obj_id)
            elif obj_type == 'item':
                self.collect_item(obj_id)
            elif obj_type == 'enemy':
                self.start_combat(obj_id)
    
    def update_hud(self):
        """Actualiza el HUD con la información actual del personaje"""
        char = self.ids.game_map.characters[self.current_character]
        self.ids.character_name.text = char.name
        self.ids.health_bar.health = char.health
        self.ids.health_bar.max_health = char.max_health
        self.ids.mana_bar.mana = char.mana
        self.ids.mana_bar.max_mana = char.max_mana
        self.ids.mission_label.text = f"Misión: {self.current_mission}"
        
        # Actualizar inventario rápido
        items = list(self.player_inventory.keys())[:3]
        for i in range(3):
            slot = self.ids[f'quick_slot{i+1}']
            if i < len(items):
                item_id = items[i]
                # Crear textura para el item
                item_texture = create_item_texture(item_id)
                slot.image = Image(texture=item_texture, size=(60, 60))
                slot.add_widget(slot.image)
                slot.item_id = item_id
            else:
                slot.clear_widgets()
                slot.item_id = ''
    
    def interact(self):
        """Acción de interactuar con el entorno (botón A)"""
        if self.game_state == 'exploring':
            # En modo exploración, interactuar con NPCs u objetos
            obj_type, obj_id = self.ids.game_map.check_collisions()
            if obj_type == 'npc':
                self.start_dialogue(obj_id)
            elif obj_type == 'item':
                self.collect_item(obj_id)
        elif self.game_state == 'combat':
            # En combate, atacar
            self.ids.combat_screen.attack()
        elif self.game_state == 'dialogue' and self.dialogue_queue:
            # Avanzar en el diálogo
            self.next_dialogue()
        
        # Reproducir sonido de paso
        if self.sounds['footstep']:
            self.sounds['footstep'].play()
    
    def jump(self):
        """Acción de saltar (botón X)"""
        if self.game_state == 'exploring':
            # En modo exploración, saltar (para puzzles o obstáculos)
            pass
        elif self.game_state == 'combat':
            # En combate, defender
            self.ids.combat_screen.defend()
        
        # Reproducir sonido de paso
        if self.sounds['footstep']:
            self.sounds['footstep'].play()
    
    def push(self):
        """Acción de empujar (botón B)"""
        if self.game_state == 'exploring':
            # En modo exploración, empujar objetos
            pass
        elif self.game_state == 'combat':
            # En combate, usar objeto
            self.ids.combat_screen.use_item()
        
        # Reproducir sonido de paso
        if self.sounds['footstep']:
            self.sounds['footstep'].play()
    
    def switch_character(self):
        """Acción de cambiar de personaje (botón Y)"""
        if self.game_state == 'exploring':
            # Cambiar al siguiente personaje
            chars = list(self.ids.game_map.characters.keys())
            current_idx = chars.index(self.current_character)
            next_idx = (current_idx + 1) % len(chars)
            self.current_character = chars[next_idx]
            
            # Actualizar visibilidad
            for char_id, char in self.ids.game_map.characters.items():
                char.visible = (char_id == self.current_character)
                if char.visible:
                    # Actualizar el sprite del personaje visible
                    char.update_sprite()
            
            # Actualizar HUD
            self.update_hud()
    
    def start_dialogue(self, npc_id):
        """Inicia un diálogo con un NPC"""
        if self.game_state != 'exploring':
            return
        
        self.game_state = 'dialogue'
        self.dialogue_npc = self.ids.game_map.npcs[npc_id]
        self.dialogue_queue = deque(self.dialogue_npc.dialogue)
        
        # Mostrar el primer mensaje
        if self.dialogue_queue:
            self.ids.dialogue_box.ids.dialogue_text.text = self.dialogue_queue.popleft()
            self.ids.dialogue_box.size = self.ids.dialogue_box.size_hint_x * Window.width, 120
    
    def next_dialogue(self):
        """Muestra el siguiente mensaje en el diálogo"""
        if self.dialogue_queue:
            self.ids.dialogue_box.ids.dialogue_text.text = self.dialogue_queue.popleft()
        else:
            self.close_dialogue()
    
    def close_dialogue(self):
        """Cierra el diálogo actual"""
        self.ids.dialogue_box.size = 0, 0
        self.game_state = 'exploring'
        self.dialogue_npc = None
        self.dialogue_queue.clear()
    
    def collect_item(self, item_id):
        """Recolecta un item del mapa"""
        item = self.ids.game_map.items[item_id]
        
        # Añadir al inventario
        if item.item_id in self.player_inventory:
            self.player_inventory[item.item_id] += 1
        else:
            self.player_inventory[item.item_id] = 1
        
        # Eliminar del mapa
        self.ids.game_map.remove_widget(item)
        del self.ids.game_map.items[item_id]
        
        # Actualizar HUD
        self.update_hud()
    
    def start_combat(self, enemy_id):
        """Inicia un combate con un enemigo"""
        if self.game_state != 'exploring':
            return
        
        self.game_state = 'combat'
        self.combat_enemy = self.ids.game_map.enemies[enemy_id]
        
        # Reproducir rugido del monstruo si es el monstruo ancestral
        if enemy_id == 'monstruo' and self.sounds['monster_roar']:
            self.sounds['monster_roar'].play()
        
        # Configurar pantalla de combate
        combat_screen = self.manager.get_screen('combat')
        combat_screen.setup_combat(self.current_character, enemy_id)
        
        # Cambiar a la pantalla de combate
        self.manager.current = 'combat'
    
    def start_memory_puzzle(self):
        """Inicia el juego de memoria"""
        if self.game_state != 'exploring':
            return
        
        self.game_state = 'puzzle'
        
        # Configurar pantalla de puzzle
        puzzle_screen = self.manager.get_screen('memory_puzzle')
        puzzle_screen.start_puzzle()
        
        # Cambiar a la pantalla de puzzle
        self.manager.current = 'memory_puzzle'
    
    def start_store(self):
        """Abre la tienda"""
        if self.game_state != 'exploring':
            return
        
        self.game_state = 'store'
        
        # Configurar pantalla de tienda
        store_screen = self.manager.get_screen('store')
        store_screen.setup_store()
        
        # Cambiar a la pantalla de tienda
        self.manager.current = 'store'
    
    def save_game(self):
        """Guarda el estado actual del juego"""
        save_data = {
            'character': self.current_character,
            'inventory': self.player_inventory,
            'gold': self.gold,
            'mission': self.current_mission,
            'characters': {
                char_id: {
                    'health': char.health,
                    'mana': char.mana
                } for char_id, char in self.ids.game_map.characters.items()
            },
            'map_position': {
                'x': self.ids.game_map.camera_x,
                'y': self.ids.game_map.camera_y
            }
        }
        
        # Guardar en un archivo JSON
        try:
            with open('savegame.json', 'w') as f:
                json.dump(save_data, f)
            print("Juego guardado exitosamente")
        except Exception as e:
            print(f"Error al guardar el juego: {e}")
    
    def load_game(self):
        """Carga el estado guardado del juego"""
        if not os.path.exists('savegame.json'):
            return
        
        try:
            with open('savegame.json', 'r') as f:
                save_data = json.load(f)
            
            # Restaurar inventario
            self.player_inventory = save_data['inventory']
            self.gold = save_data['gold']
            self.current_mission = save_data['mission']
            
            # Restaurar estado de los personajes
            for char_id, char_data in save_data['characters'].items():
                if char_id in self.ids.game_map.characters:
                    char = self.ids.game_map.characters[char_id]
                    char.health = char_data['health']
                    char.mana = char_data['mana']
            
            # Restaurar posición en el mapa
            self.ids.game_map.camera_x = save_data['map_position']['x']
            self.ids.game_map.camera_y = save_data['map_position']['y']
            self.ids.game_map.target_camera_x = self.ids.game_map.camera_x
            self.ids.game_map.target_camera_y = self.ids.game_map.camera_y
            
            print("Juego cargado exitosamente")
        except Exception as e:
            print(f"Error al cargar el juego: {e}")

class CombatScreen(Screen):
    current_character = StringProperty('')
    enemy_id = StringProperty('')
    player_turn = BooleanProperty(True)
    combat_message = StringProperty('')
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.combat_log = []
    
    def on_pre_enter(self, *args):
        """Se llama antes de que la pantalla sea mostrada"""
        # Inicializar combate
        self.init_combat()
    
    def setup_combat(self, character_id, enemy_id):
        """Configura el combate con los participantes"""
        self.current_character = character_id
        self.enemy_id = enemy_id
    
    def init_combat(self):
        """Inicializa el estado del combate"""
        # Obtener referencias a los personajes
        game_screen = self.manager.get_screen('game')
        char = game_screen.ids.game_map.characters[self.current_character]
        enemy = game_screen.ids.game_map.enemies[self.enemy_id]
        
        # Configurar HUD del jugador
        self.ids.player_health.health = char.health
        self.ids.player_health.max_health = char.max_health
        
        # Crear textura para el personaje
        char_texture = create_character_texture(self.current_character)
        self.ids.player_image.texture = char_texture
        
        # Configurar HUD del enemigo
        self.ids.enemy_health.health = enemy.health
        self.ids.enemy_health.max_health = enemy.max_health
        self.ids.enemy_name.text = enemy.name
        
        # Crear textura para el enemigo
        enemy_texture = create_enemy_texture(self.enemy_id)
        self.ids.enemy_image.texture = enemy_texture
        
        # Mensaje inicial
        self.combat_message = f"¡{enemy.name} te ataca!"
        self.ids.combat_message.text = self.combat_message
    
    def attack(self):
        """El jugador ataca al enemigo"""
        if not self.player_turn:
            return
        
        game_screen = self.manager.get_screen('game')
        char = game_screen.ids.game_map.characters[self.current_character]
        enemy = game_screen.ids.game_map.enemies[self.enemy_id]
        
        # Calcular daño
        damage = char.attack_enemy(enemy)
        
        # Actualizar HUD
        self.ids.enemy_health.health = enemy.health
        
        # Mostrar mensaje
        self.combat_message = f"¡Has hecho {damage} puntos de daño!"
        self.ids.combat_message.text = self.combat_message
        
        # Verificar si el enemigo fue derrotado
        if enemy.health <= 0:
            Clock.schedule_once(self.end_combat, 1.5)
            return
        
        # Cambiar de turno
        self.player_turn = False
        Clock.schedule_once(self.enemy_turn, 1.0)
    
    def defend(self):
        """El jugador se defiende"""
        if not self.player_turn:
            return
        
        # Aumentar temporalmente la defensa
        game_screen = self.manager.get_screen('game')
        char = game_screen.ids.game_map.characters[self.current_character]
        char.defense *= 1.5
        
        # Mostrar mensaje
        self.combat_message = "¡Te has defendido!"
        self.ids.combat_message.text = self.combat_message
        
        # Cambiar de turno
        self.player_turn = False
        Clock.schedule_once(lambda dt: self.end_defense(char), 0.5)
        Clock.schedule_once(self.enemy_turn, 1.0)
    
    def end_defense(self, char):
        """Restaura la defensa después de defender"""
        char.defense = char.defense / 1.5
    
    def use_item(self):
        """El jugador usa un objeto"""
        if not self.player_turn:
            return
        
        # Mostrar menú de objetos (en un proyecto real, esto sería una pantalla separada)
        game_screen = self.manager.get_screen('game')
        
        if not game_screen.player_inventory:
            self.combat_message = "¡No tienes objetos!"
            self.ids.combat_message.text = self.combat_message
            return
        
        # Usar el primer objeto disponible (simplificado)
        item_id = next(iter(game_screen.player_inventory))
        item = ITEMS[item_id]
        
        # Aplicar efecto
        if 'health' in item['effect']:
            char = game_screen.ids.game_map.characters[self.current_character]
            char.health = min(char.max_health, char.health + item['effect']['health'])
            self.ids.player_health.health = char.health
            game_screen.player_inventory[item_id] -= 1
            if game_screen.player_inventory[item_id] <= 0:
                del game_screen.player_inventory[item_id]
        
        # Mostrar mensaje
        self.combat_message = f"¡Has usado {item['name']}!"
        self.ids.combat_message.text = self.combat_message
        
        # Actualizar HUD
        game_screen.update_hud()
        
        # Cambiar de turno
        self.player_turn = False
        Clock.schedule_once(self.enemy_turn, 1.0)
    
    def run_away(self):
        """El jugador intenta huir del combate"""
        game_screen = self.manager.get_screen('game')
        char = game_screen.ids.game_map.characters[self.current_character]
        enemy = game_screen.ids.game_map.enemies[self.enemy_id]
        
        # Probabilidad de huir basada en la velocidad
        flee_chance = min(0.8, char.speed / (char.speed + enemy.speed))
        
        if random.random() < flee_chance:
            self.combat_message = "¡Has escapado exitosamente!"
            self.ids.combat_message.text = self.combat_message
            Clock.schedule_once(self.end_combat, 1.5)
        else:
            self.combat_message = "¡No pudiste escapar!"
            self.ids.combat_message.text = self.combat_message
            Clock.schedule_once(self.enemy_turn, 1.5)
    
    def enemy_turn(self, dt):
        """Turno del enemigo"""
        game_screen = self.manager.get_screen('game')
        char = game_screen.ids.game_map.characters[self.current_character]
        enemy = game_screen.ids.game_map.enemies[self.enemy_id]
        
        # El enemigo ataca
        damage = enemy.attack
        actual_damage = char.take_damage(damage)
        
        # Actualizar HUD
        self.ids.player_health.health = char.health
        
        # Mostrar mensaje
        self.combat_message = f"¡{enemy.name} te hizo {actual_damage} puntos de daño!"
        self.ids.combat_message.text = self.combat_message
        
        # Verificar si el jugador fue derrotado
        if char.health <= 0:
            Clock.schedule_once(self.game_over, 1.5)
            return
        
        # Cambiar de turno
        self.player_turn = True
    
    def end_combat(self, dt):
        """Finaliza el combate con victoria del jugador"""
        game_screen = self.manager.get_screen('game')
        enemy = game_screen.ids.game_map.enemies[self.enemy_id]
        
        # Otorgar recompensas
        game_screen.gold += enemy.gold
        # En un proyecto real, se añadiría XP y posiblemente items
        
        # Eliminar enemigo del mapa
        game_screen.ids.game_map.remove_widget(enemy)
        del game_screen.ids.game_map.enemies[self.enemy_id]
        
        # Volver a la pantalla de juego
        game_screen.game_state = 'exploring'
        game_screen.manager.current = 'game'
    
    def game_over(self, dt):
        """Maneja el final del juego por derrota"""
        # En un proyecto real, mostraría una pantalla de game over
        game_screen = self.manager.get_screen('game')
        game_screen.game_state = 'exploring'
        game_screen.manager.current = 'game'
        
        # Restaurar salud del personaje
        char = game_screen.ids.game_map.characters[game_screen.current_character]
        char.health = char.max_health * 0.2  # Revivir con 20% de salud

class MemoryPuzzleScreen(Screen):
    puzzle_size = 3
    sequence = ListProperty([])
    player_sequence = ListProperty([])
    showing_sequence = BooleanProperty(False)
    level = NumericProperty(1)
    
    def on_pre_enter(self, *args):
        """Se llama antes de que la pantalla sea mostrada"""
        self.start_puzzle()
    
    def start_puzzle(self):
        """Inicia el juego de memoria"""
        self.ids.puzzle_message.text = "Observa la secuencia..."
        self.showing_sequence = True
        self.player_sequence = []
        self.sequence = []
        
        # Generar una secuencia aleatoria
        for _ in range(self.level + 2):  # La secuencia crece con el nivel
            self.sequence.append(random.randint(0, self.puzzle_size * self.puzzle_size - 1))
        
        # Crear el grid de botones
        self.ids.puzzle_grid.clear_widgets()
        for i in range(self.puzzle_size * self.puzzle_size):
            btn = Button(
                background_color=(0.2, 0.2, 0.8, 1),
                on_release=partial(self.button_pressed, i)
            )
            self.ids.puzzle_grid.add_widget(btn)
        
        # Mostrar la secuencia
        Clock.schedule_once(self.show_sequence, 1.0)
    
    def show_sequence(self, dt):
        """Muestra la secuencia al jugador"""
        if not self.sequence:
            self.showing_sequence = False
            self.ids.puzzle_message.text = "¡Tu turno!"
            return
        
        index = self.sequence[len(self.player_sequence)]
        btn = self.ids.puzzle_grid.children[-(index + 1)]  # Los children están en orden inverso
        
        # Resaltar el botón
        original_color = btn.background_color
        btn.background_color = (0.8, 0.8, 0.2, 1)
        
        # Volver al color original después de un tiempo
        def reset_color(dt):
            btn.background_color = original_color
            Clock.schedule_once(self.show_sequence, 0.5)
        
        Clock.schedule_once(reset_color, 0.7)
    
    def button_pressed(self, index, instance):
        """Maneja cuando el jugador presiona un botón"""
        if self.showing_sequence:
            return
        
        self.player_sequence.append(index)
        
        # Resaltar el botón
        original_color = instance.background_color
        instance.background_color = (0.2, 0.8, 0.2, 1)
        
        # Volver al color original después de un tiempo
        def reset_color(dt):
            instance.background_color = original_color
        
        Clock.schedule_once(reset_color, 0.3)
        
        # Verificar la secuencia
        if self.player_sequence == self.sequence[:len(self.player_sequence)]:
            if len(self.player_sequence) == len(self.sequence):
                # Secuencia completa correcta
                self.ids.puzzle_message.text = "¡Correcto! Nivel completado."
                Clock.schedule_once(self.end_puzzle, 1.5)
        else:
            # Error en la secuencia
            self.ids.puzzle_message.text = "¡Secuencia incorrecta!"
            Clock.schedule_once(self.start_puzzle, 1.5)
    
    def end_puzzle(self, dt):
        """Finaliza el puzzle con éxito"""
        game_screen = self.manager.get_screen('game')
        game_screen.game_state = 'exploring'
        
        # Otorgar recompensa
        game_screen.player_inventory['pocion_salud'] = game_screen.player_inventory.get('pocion_salud', 0) + 1
        game_screen.update_hud()
        
        # Volver a la pantalla de juego
        game_screen.manager.current = 'game'

class StoreScreen(Screen):
    items_for_sale = ListProperty([])
    
    def setup_store(self):
        """Configura la tienda con items disponibles"""
        self.items_for_sale = [
            'pocion_salud',
            'pocion_mana',
            'comida',
            'espada'
        ]
        self.update_store()
    
    def update_store(self):
        """Actualiza la interfaz de la tienda"""
        game_screen = self.manager.get_screen('game')
        self.ids.gold_label.text = f'Oro: {game_screen.gold}'
        
        # Limpiar items existentes
        self.ids.store_items.clear_widgets()
        
        # Añadir items a la tienda
        for item_id in self.items_for_sale:
            item = ITEMS[item_id]
            
            # Crear un layout para el item
            item_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=60)
            
            # Imagen del item
            item_image = Image(
                size=(40, 40),
                texture=create_item_texture(item_id)
            )
            item_layout.add_widget(item_image)
            
            # Nombre y precio
            item_label = Label(
                text=f"{item['name']} - {item['price']} oro",
                halign='left',
                valign='middle'
            )
            item_layout.add_widget(item_label)
            
            # Botón de compra
            buy_button = Button(
                text="Comprar",
                size_hint_x=None,
                width=100,
                on_release=partial(self.buy_item, item_id)
            )
            item_layout.add_widget(buy_button)
            
            self.ids.store_items.add_widget(item_layout)
    
    def buy_item(self, item_id, instance):
        """Compra un item de la tienda"""
        game_screen = self.manager.get_screen('game')
        item = ITEMS[item_id]
        
        if game_screen.gold >= item['price']:
            # Añadir al inventario
            if item_id in game_screen.player_inventory:
                game_screen.player_inventory[item_id] += 1
            else:
                game_screen.player_inventory[item_id] = 1
            
            # Restar oro
            game_screen.gold -= item['price']
            
            # Actualizar interfaz
            self.update_store()
            game_screen.update_hud()
            
            # Mensaje de confirmación
            self.ids.store_items.add_widget(Label(
                text=f"¡Has comprado {item['name']}!",
                size_hint_y=None,
                height=40,
                color=(0, 1, 0, 1)
            ))
            Clock.schedule_once(lambda dt: self.remove_last_widget(), 2.0)
        else:
            # Mensaje de error
            self.ids.store_items.add_widget(Label(
                text="¡No tienes suficiente oro!",
                size_hint_y=None,
                height=40,
                color=(1, 0, 0, 1)
            ))
            Clock.schedule_once(lambda dt: self.remove_last_widget(), 2.0)
    
    def remove_last_widget(self):
        """Elimina el último widget añadido (mensaje de confirmación/error)"""
        if len(self.ids.store_items.children) > len(self.items_for_sale):
            self.ids.store_items.remove_widget(self.ids.store_items.children[0])

class MountainAdventureApp(App):
    game_mode = StringProperty('single')  # single o multi
    multiplayer_client = None
    multiplayer_server = None
    
    def build(self):
        """Construye la aplicación"""
        # Cargar KV
        Builder.load_string(KV)
        
        # Crear ScreenManager
        sm = ScreenManager(transition=SwapTransition())
        
        # Añadir pantallas
        sm.add_widget(StartScreen(name='start'))
        sm.add_widget(GameModeScreen(name='game_mode'))
        sm.add_widget(MultiplayerSetupScreen(name='multiplayer_setup'))
        sm.add_widget(OptionsScreen(name='options'))
        sm.add_widget(GameScreen(name='game'))
        sm.add_widget(CombatScreen(name='combat'))
        sm.add_widget(MemoryPuzzleScreen(name='memory_puzzle'))
        sm.add_widget(StoreScreen(name='store'))
        
        # Cargar opciones
        self.load_options()
        
        return sm
    
    def on_start(self):
        """Se llama después de que la aplicación se inicia"""
        # En un proyecto real, aquí se manejarían inicializaciones adicionales
        pass
    
    def set_game_mode(self, mode):
        """Establece el modo de juego"""
        self.game_mode = mode
    
    def start_server(self):
        """Inicia el servidor para multijugador"""
        if self.game_mode != 'multi':
            return
        
        # En un proyecto real, aquí se iniciaría un servidor de red
        # Por ahora, solo actualizamos el estado
        setup_screen = self.root.get_screen('multiplayer_setup')
        setup_screen.update_status('Servidor iniciado. Esperando jugadores...')
        
        # Simular conexión después de 2 segundos
        Clock.schedule_once(lambda dt: self.simulate_multiplayer_connection(), 2.0)
    
    def connect_to_server(self):
        """Conecta como cliente al servidor"""
        if self.game_mode != 'multi':
            return
        
        # En un proyecto real, aquí se conectaría al servidor
        # Por ahora, solo actualizamos el estado
        setup_screen = self.root.get_screen('multiplayer_setup')
        setup_screen.update_status('Conectando al servidor...')
        
        # Simular conexión después de 2 segundos
        Clock.schedule_once(lambda dt: self.simulate_multiplayer_connection(), 2.0)
    
    def simulate_multiplayer_connection(self):
        """Simula una conexión multijugador exitosa (para el prototipo)"""
        setup_screen = self.root.get_screen('multiplayer_setup')
        setup_screen.update_status('¡Conexión establecida!')
        Clock.schedule_once(lambda dt: self.root.current = 'game', 1.5)
    
    def load_options(self):
        """Carga las opciones guardadas"""
        try:
            with open('options.json', 'r') as f:
                options = json.load(f)
                # En un proyecto real, aplicaría las opciones de volumen
        except:
            # Opciones por defecto
            pass
    
    def save_options(self, screen):
        """Guarda las opciones actuales"""
        options = {
            'music_volume': screen.ids.music_slider.value,
            'sfx_volume': screen.ids.sfx_slider.value
        }
        
        try:
            with open('options.json', 'w') as f:
                json.dump(options, f)
            print("Opciones guardadas exitosamente")
        except Exception as e:
            print(f"Error al guardar opciones: {e}")
    
    def open_youtube(self):
        """Abre el canal de YouTube en el navegador"""
        try:
            import webbrowser
            webbrowser.open('https://youtube.com/@ocex17')
        except:
            print("No se pudo abrir el navegador")
    
    def open_instagram(self):
        """Abre Instagram en el navegador"""
        try:
            import webbrowser
            webbrowser.open('https://www.instagram.com/alan_10236')
        except:
            print("No se pudo abrir el navegador")

if __name__ == '__main__':
    MountainAdventureApp().run()