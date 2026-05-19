import random

import pygame

from circleshape import CircleShape
from constants import ASTEROID_MIN_RADIUS, LINE_WIDTH
from logger import log_event


class Asteroid(CircleShape):
    def __init__(self, x, y, radius):
        super().__init__(x, y, radius)

    def draw(self, screen):
        pygame.draw.circle(screen, "white", self.position, self.radius, LINE_WIDTH)

    def update(self, dt):
        self.position += self.velocity * dt

    def split(self):
        self.kill()

        if self.radius <= ASTEROID_MIN_RADIUS:
            return

        log_event("asteroid_split")

        angle = random.uniform(20, 50)

        new_velocity_1 = self.velocity.rotate(angle)
        new_velocity_2 = self.velocity.rotate(-angle)

        new_radius = self.radius - ASTEROID_MIN_RADIUS

        asteroid_1 = Asteroid(self.position.x, self.position.y, new_radius)
        asteroid_1.velocity = new_velocity_1 * 1.2

        asteroid_2 = Asteroid(self.position.x, self.position.y, new_radius)
        asteroid_2.velocity = new_velocity_2 * 1.2
