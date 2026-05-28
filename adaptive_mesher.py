import numpy as np
from scipy.spatial import Delaunay
from scipy.interpolate import griddata
from matplotlib.path import Path

class AdaptiveMesher:

    def __init__(self, terrain_data, min_points=100, max_points=5000):
        self.terrain = terrain_data
        self.min_points = min_points
        self.max_points = max_points

        # Poczatkowa triangulacja (mala liczba punktow)
        self.current_points = None
        self.current_values = None
        self.triangulation = None

        # Historia rozwoju siatki
        self.mesh_history = []

        # Inicjalizacja z podstawowa siatka
        self._initialize_mesh()

    def _initialize_mesh(self):
        # Rozpocznij od malej liczby rownomiernie rozlozonych punktow
        n = int(np.sqrt(self.min_points))
        x_sparse = np.linspace(self.terrain.x_range[0], self.terrain.x_range[1], n)
        y_sparse = np.linspace(self.terrain.y_range[0], self.terrain.y_range[1], n)
        X_sparse, Y_sparse = np.meshgrid(x_sparse, y_sparse)

        # Interpolacja wartosci wysokosci
        Z_sparse = griddata((self.terrain.X.flatten(), self.terrain.Y.flatten()),
                            self.terrain.Z.flatten(),
                            (X_sparse, Y_sparse),
                            method='linear')

        # Zapisz aktualna siatke
        self.current_points = np.vstack((X_sparse.flatten(), Y_sparse.flatten())).T
        self.current_values = Z_sparse.flatten()

        # Poczatkowa triangulacja
        self._update_triangulation()

        # Zapisz historie
        self.mesh_history.append({
            'points': self.current_points.copy(),
            'values': self.current_values.copy(),
            'triangulation': self.triangulation
        })

    def _update_triangulation(self):
        self.triangulation = Delaunay(self.current_points)

    def _calculate_error(self, triangle_idx):
        # Pobierz wierzcholki trojkata
        vertices_idx = self.triangulation.simplices[triangle_idx]
        vertices = self.current_points[vertices_idx]

        # Znajdz bounding box trojkata
        min_x, min_y = np.min(vertices, axis=0)
        max_x, max_y = np.max(vertices, axis=0)

        # Utworz siatke punktow wewnatrz bounding box
        n_grid = 10
        x_grid = np.linspace(min_x, max_x, n_grid)
        y_grid = np.linspace(min_y, max_y, n_grid)
        X_grid, Y_grid = np.meshgrid(x_grid, y_grid)
        points_grid = np.vstack((X_grid.flatten(), Y_grid.flatten())).T

        # Sprawdz, ktore punkty siatki sa wewnatrz trojkata
        path = Path(vertices)
        inside = path.contains_points(points_grid)
        inner_points = points_grid[inside]

        if len(inner_points) == 0:
            return 0, vertices[0], 0

        # Interpolacja wartosci wysokosci na trojkacie
        values_vertices = self.current_values[vertices_idx]

        # Funkcja interpolacji barycentrycznej
        def barycentric_interpolation(p, vertices, values):
            # Obliczenie wspolrzednych barycentrycznych
            v0, v1, v2 = vertices
            a = ((v1[1] - v2[1]) * (p[0] - v2[0]) + (v2[0] - v1[0]) * (p[1] - v2[1])) / \
                ((v1[1] - v2[1]) * (v0[0] - v2[0]) + (v2[0] - v1[0]) * (v0[1] - v2[1]))
            b = ((v2[1] - v0[1]) * (p[0] - v2[0]) + (v0[0] - v2[0]) * (p[1] - v2[1])) / \
                ((v1[1] - v2[1]) * (v0[0] - v2[0]) + (v2[0] - v1[0]) * (v0[1] - v2[1]))
            c = 1 - a - b

            # Interpolacja wartosci
            return a * values[0] + b * values[1] + c * values[2]

        # Oblicz interpolowane wartosci
        interp_values = np.array([barycentric_interpolation(p, vertices, values_vertices)
                                  for p in inner_points])

        # Znajdz rzeczywiste wartosci z oryginalnych danych terenu
        real_values = griddata((self.terrain.X.flatten(), self.terrain.Y.flatten()),
                               self.terrain.Z.flatten(),
                               inner_points,
                               method='linear')

        # Oblicz bledy
        errors = np.abs(interp_values - real_values)

        if len(errors) == 0:
            return 0, vertices[0], 0

        # Znajdz punkt o najwiekszym bledzie
        max_error_idx = np.argmax(errors)
        max_error = errors[max_error_idx]
        max_error_point = inner_points[max_error_idx]
        max_error_value = real_values[max_error_idx]

        return max_error, max_error_point, max_error_value

    def refine_mesh(self, num_iterations=5, error_threshold=0.1):
        for iteration in range(num_iterations):
            # Sprawdz, czy osiagnieto maksymalna liczbe punktow
            if len(self.current_points) >= self.max_points:
                print(f"Osiagnieto maksymalna liczbe punktow: {self.max_points}")
                break

            # Sprawdz wszystkie trojkaty i oblicz bledy
            errors = []
            new_points = []
            new_values = []

            for i in range(len(self.triangulation.simplices)):
                error, point, value = self._calculate_error(i)
                if error > error_threshold:
                    errors.append(error)
                    new_points.append(point)
                    new_values.append(value)

            # Jesli nie znaleziono punktow o bledzie powyzej progu, zakoncz
            if not errors:
                print(f"Brak punktow o bledzie powyzej progu: {error_threshold}")
                break

            # Dodaj punkty o najwiekszym bledzie
            max_points_to_add = min(len(errors), self.max_points - len(self.current_points))

            if max_points_to_add <= 0:
                break

            # Posortuj punkty wedlug bledu
            sorted_indices = np.argsort(errors)[::-1]
            top_indices = sorted_indices[:max_points_to_add]

            # Dodaj punkty do siatki
            for idx in top_indices:
                self.current_points = np.vstack((self.current_points, new_points[idx]))
                self.current_values = np.append(self.current_values, new_values[idx])

            # Aktualizuj triangulacje
            self._update_triangulation()

            # Zapisz historie
            self.mesh_history.append({
                'points': self.current_points.copy(),
                'values': self.current_values.copy(),
                'triangulation': self.triangulation
            })

            print(f"Iteracja {iteration + 1}: dodano {len(top_indices)} punktow, "
                  f"lacznie {len(self.current_points)} punktow")

        return len(self.mesh_history) - 1  # Liczba krokow siatkowania

    def generate_uniform_mesh(self, num_points):
        # Oblicz liczbe punktow w kazdym wymiarze
        n = int(np.sqrt(num_points))

        # Generuj rownomiernie rozlozone punkty
        x_uniform = np.linspace(self.terrain.x_range[0], self.terrain.x_range[1], n)
        y_uniform = np.linspace(self.terrain.y_range[0], self.terrain.y_range[1], n)
        X_uniform, Y_uniform = np.meshgrid(x_uniform, y_uniform)

        # Interpolacja wartosci wysokosci
        Z_uniform = griddata((self.terrain.X.flatten(), self.terrain.Y.flatten()),
                             self.terrain.Z.flatten(),
                             (X_uniform, Y_uniform),
                             method='linear')

        # Utworz punkty dla triangulacji
        uniform_points = np.vstack((X_uniform.flatten(), Y_uniform.flatten())).T
        uniform_values = Z_uniform.flatten()

        # Triangulacja
        triangulation = Delaunay(uniform_points)

        return {
            'points': uniform_points,
            'values': uniform_values,
            'triangulation': triangulation
        }