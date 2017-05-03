import os
import sys

import pygame

import baseui


class GUI(baseui.BaseUI):

    def menu(self):
        height, width = 640, 480
        size = [height, width]
        screen = pygame.display.set_mode(size)

        screen.fill([0,0,0])
        pygame.display.flip()

        grid = Grid()
        button_play = Button('play', self.player.play_current_track)
        button_next = Button('next', self.player.play_next_track)
        grid.add(button_play)
        grid.add(button_next)

        while 1:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    for element in grid.elements:
                        if element.image.get_rect().collidepoint(event.pos):
                            element.callback()

            for element in grid.elements:
                screen.blit(element.image, element.position)

            pygame.display.update()


class Button:
    position = None

    def __init__(self, name, callback):
        self.name = name
        self.callback = callback
        self.image = load_image(self.name)



class Grid:
    elements = []
    width = 2
    height = 2
    current_x = 0
    current_y = 0
    size_x = 100
    size_y = 100

    def add(self, element):
        element.position = self.get_next_position()
        self.elements.append(element)

    def get_next_position(self):
        position = self.current_x * self.size_x, self.current_y * self.size_y
        self.current_x += 1
        if self.current_x == self.width:
            self.current_x = 0
            self.current_y += 1
        return position

def load_image(name, directory='images'):
    file_name = name + '.png'
    path = os.path.join(directory, file_name)
    return pygame.image.load(path).convert()


if __name__ == '__main__':
    gui= GUI()
    gui.menu()
