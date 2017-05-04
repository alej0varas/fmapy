import os
import sys

import pygame

import baseui


class GUI(baseui.BaseUI):

    def menu(self, width=640, height=480):
        self.size = [height, width]

        self.screen = self.prepare()

        self.grid = Grid(width=4)
        button_play = Button('play', self.play)
        self.grid.add(button_play)
        button_next = Button('next', self.next)
        self.grid.add(button_next)
        button_stop = Button('stop', self.stop)
        self.grid.add(button_stop)
        button_exit = Button('exit', self.exit)

        self.grid.add(button_exit)

        self.resize()

        while 1:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.exit()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    for element in self.grid.elements:
                        if element.rect.collidepoint(event.pos):
                            element.callback()

            for element in self.grid.elements:
                self.screen.blit(element.image, element.rect)

            pygame.display.update()

    def exit(self):
        self.stop()
        sys.exit()

    def get_size(self):
        return self.size

    def prepare(self):
        size = self.get_size()
        screen = pygame.display.set_mode(size)
        screen.fill([0,0,0])
        pygame.display.flip()
        return screen

    def resize(self):
        size = self.grid.get_size()
        self.screen = pygame.display.set_mode(size)


class Button:
    rect = None

    def __init__(self, name, callback):
        self.name = name
        self.callback = callback
        self.image = load_image(self.name)
        self.rect = self.image.get_rect()

    def resize_and_position(self, rect, width, height):
        dst_surface = pygame.Surface((width, height))
        self.image = pygame.transform.scale(self.image, (width, height), dst_surface)
        self.image.blit(self.image, (0, 0))
        self.rect = pygame.Rect(rect)


class Grid:
    elements = []
    current_x = -1
    current_y = 0

    def __init__(self, width=2, height=2, size_x=200, size_y=200):
        self.width = width
        self.height = height
        self.size_x = size_x
        self.size_y = size_y

    def add(self, element):
        element.resize_and_position(self.get_next_rect(), self.size_x, self.size_y)
        self.elements.append(element)

    def get_next_rect(self):
        self.current_x += 1
        if self.current_x == self.width:
            self.current_x = 0
            self.current_y += 1
        if self.current_y == self.height:
            return None
        # (left, top, width, height)
        rect = (self.current_x * self.size_x,
                    self.current_y * self.size_y,
                    self.current_x * self.size_x + self.size_x,
                    self.current_y * self.size_y + self.size_y)
        return rect

    def get_size(self):
        size = (self.width * self.size_x,
                self.height * self.size_y)
        return size

def load_image(name, directory='images'):
    file_name = name + '.png'
    path = os.path.join(directory, file_name)
    return pygame.image.load(path).convert()


if __name__ == '__main__':
    gui= GUI()
    gui.menu()
