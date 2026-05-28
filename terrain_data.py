import numpy as np
from scipy.interpolate import griddata

class TerrainData:

    def __init__(self, x_range=(-10, 10), y_range=(-10, 10), resolution=100):
        self.x_range = x_range
        self.y_range = y_range
        self.resolution = resolution

        # Utworzenie siatki probkowania
        self.x = np.linspace(x_range[0], x_range[1], resolution)
        self.y = np.linspace(y_range[0], y_range[1], resolution)
        self.X, self.Y = np.meshgrid(self.x, self.y)

        # Domyslny teren jako plaska powierzchnia
        self.Z = np.zeros_like(self.X)

        # Wspolrzedne punktow w formacie dla triangulacji
        self.points = None
        self.values = None

    def generate_terrain(self, terrain_type="gaussian_hills"):
        if terrain_type == "gaussian_hills":
            # Generowanie losowych wzniesien
            num_hills = 5
            for _ in range(num_hills):
                x0 = np.random.uniform(self.x_range[0], self.x_range[1])
                y0 = np.random.uniform(self.y_range[0], self.y_range[1])
                sigma_x = np.random.uniform(1, 3)
                sigma_y = np.random.uniform(1, 3)
                amplitude = np.random.uniform(1, 5)

                self.Z += amplitude * np.exp(-((self.X - x0) ** 2 / (2 * sigma_x ** 2) +
                                               (self.Y - y0) ** 2 / (2 * sigma_y ** 2)))

        elif terrain_type == "sine_waves":
            # Teren typu fala sinusoidalna
            freq_x = np.random.uniform(0.2, 0.5)
            freq_y = np.random.uniform(0.2, 0.5)
            self.Z = 2 * np.sin(freq_x * np.pi * self.X) * np.cos(freq_y * np.pi * self.Y)

        elif terrain_type == "ridges":
            # Teren z grzbietami
            for i in range(3):
                angle = np.random.uniform(0, np.pi)
                dist = np.random.uniform(-5, 5)
                width = np.random.uniform(0.5, 2.0)
                height = np.random.uniform(1, 3)

                rotated_x = self.X * np.cos(angle) + self.Y * np.sin(angle)
                self.Z += height * np.exp(-(rotated_x - dist) ** 2 / width)

        elif terrain_type == "crater":
            # Teren z kraterem
            center_x = np.random.uniform(self.x_range[0] / 2, self.x_range[1] / 2)
            center_y = np.random.uniform(self.y_range[0] / 2, self.y_range[1] / 2)
            radius = np.random.uniform(3, 6)
            depth = np.random.uniform(2, 4)

            distance = np.sqrt((self.X - center_x) ** 2 + (self.Y - center_y) ** 2)
            rim = np.exp(-((distance - radius) ** 2) / 0.5)
            crater = -depth * np.exp(-(distance ** 2) / (radius ** 2))
            self.Z = rim + crater

        else:
            raise ValueError(f"Nieznany typ terenu: {terrain_type}")

        # Aktualizacja punktow dla triangulacji
        self._update_points()

    def _update_points(self):
        self.points = np.vstack((self.X.flatten(), self.Y.flatten())).T
        self.values = self.Z.flatten()