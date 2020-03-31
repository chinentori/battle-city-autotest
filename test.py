# -*- coding: UTF-8 -*-
import pygame

callbacks = {}

# 外层scope定义的变量
current_string = []
main_loop = True
start = True


def register_key_callback(key, cb):
    callbacks[key] = cb


def event_loop():
    while True:
        event = pygame.event.pool()
        if event.key in callbacks:
            callbacks[event.key](event.key)


def append_char(key):
    current_string.append(key)


def start_game(key):
    main_loop = False
    start = False

for key in range(128):
    register_key_callback(key, start_game)

register_key_callback(pygame.K_RETURN,start_game)
