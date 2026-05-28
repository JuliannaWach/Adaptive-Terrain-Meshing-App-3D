import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import ttk
from matplotlib.path import Path
from scipy.interpolate import griddata

class TerrainVisualizer:
    def __init__(self, terrain_data, mesher):
        self.terrain = terrain_data
        self.mesher = mesher

        # Kolory dla wizualizacji
        self.terrain_cmap = 'terrain'
        self.mesh_color = 'black'
        self.point_color = 'red'

    def plot_mesh(self, mesh_data, ax=None, show_points=True, alpha=0.7, color='terrain'):
        if ax is None:
            fig = plt.figure(figsize=(10, 8))
            ax = fig.add_subplot(111, projection='3d')

        # Pobierz dane
        points = mesh_data['points']
        values = mesh_data['values']
        triangulation = mesh_data['triangulation']

        # Rysowanie powierzchni trojkatow
        x = points[:, 0]
        y = points[:, 1]
        z = values

        # Rysowanie powierzchni
        ax.plot_trisurf(x, y, z, triangles=triangulation.simplices,
                        cmap=color, alpha=alpha, edgecolor=self.mesh_color, linewidth=0.2)

        # Rysowanie punktow
        if show_points:
            ax.scatter(x, y, z, color=self.point_color, s=10)

        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')

        return ax

    def plot_error_comparison(self, uniform_mesh):
        # Oblicz bledy dla obu siatek
        adaptive_errors = self._calculate_mesh_errors(self.mesher.mesh_history[-1])
        uniform_errors = self._calculate_mesh_errors(uniform_mesh)

        # Wykres histogramu bledow
        fig, ax = plt.subplots(1, 2, figsize=(12, 6))

        ax[0].hist(adaptive_errors, bins=30, alpha=0.7, color='blue')
        ax[0].set_title(f'Bledy siatki adaptacyjnej\nSredni blad: {np.mean(adaptive_errors):.4f}')
        ax[0].set_xlabel('Blad')
        ax[0].set_ylabel('Liczba trojkatow')

        ax[1].hist(uniform_errors, bins=30, alpha=0.7, color='green')
        ax[1].set_title(f'Bledy siatki rownomiernej\nSredni blad: {np.mean(uniform_errors):.4f}')
        ax[1].set_xlabel('Blad')
        ax[1].set_ylabel('Liczba trojkatow')

        plt.tight_layout()
        return fig

    def _calculate_mesh_errors(self, mesh_data):
        errors = []

        for i in range(len(mesh_data['triangulation'].simplices)):
            # Pobierz indeksy wierzcholkow trojkata
            vertices_idx = mesh_data['triangulation'].simplices[i]
            vertices = mesh_data['points'][vertices_idx]
            values = mesh_data['values'][vertices_idx]

            # Znajdz bounding box trojkata
            min_x, min_y = np.min(vertices, axis=0)
            max_x, max_y = np.max(vertices, axis=0)

            # Utworz siatke punktow wewnatrz bounding box
            n_grid = 5
            x_grid = np.linspace(min_x, max_x, n_grid)
            y_grid = np.linspace(min_y, max_y, n_grid)
            X_grid, Y_grid = np.meshgrid(x_grid, y_grid)
            points_grid = np.vstack((X_grid.flatten(), Y_grid.flatten())).T

            # Sprawdz, ktore punkty siatki sa wewnatrz trojkata
            path = Path(vertices)
            inside = path.contains_points(points_grid)
            inner_points = points_grid[inside]

            if len(inner_points) == 0:
                errors.append(0)
                continue

            # Interpolacja wartosci wysokosci na trojkacie
            def barycentric_interpolation(p, vertices, values):
                # Obliczenie wspolrzednych barycentrycznych
                v0, v1, v2 = vertices
                a = ((v1[1] - v2[1]) * (p[0] - v2[0]) + (v2[0] - v1[0]) * (p[1] - v2[1])) / \
                    ((v1[1] - v2[1]) * (v0[0] - v2[0]) + (v2[0] - v1[0]) * (v0[1] - v2[1]) + 1e-10)
                b = ((v2[1] - v0[1]) * (p[0] - v2[0]) + (v0[0] - v2[0]) * (p[1] - v2[1])) / \
                    ((v1[1] - v2[1]) * (v0[0] - v2[0]) + (v2[0] - v1[0]) * (v0[1] - v2[1]) + 1e-10)
                c = 1 - a - b

                # Interpolacja wartosci
                return a * values[0] + b * values[1] + c * values[2]

            # Oblicz interpolowane wartosci
            interp_values = np.array([barycentric_interpolation(p, vertices, values)
                                      for p in inner_points])

            # Znajdz rzeczywiste wartosci z oryginalnych danych terenu
            real_values = griddata((self.terrain.X.flatten(), self.terrain.Y.flatten()),
                                   self.terrain.Z.flatten(),
                                   inner_points,
                                   method='linear')

            # Oblicz bledy
            triangle_errors = np.abs(interp_values - real_values)
            errors.append(np.mean(triangle_errors))

        return np.array(errors)

    def plot_mesh_comparison(self, uniform_mesh):
        fig = plt.figure(figsize=(12, 6))

        # Siatka adaptacyjna
        ax1 = fig.add_subplot(121, projection='3d')
        self.plot_mesh(self.mesher.mesh_history[-1], ax=ax1, show_points=False)
        ax1.set_title(f'Siatka adaptacyjna\n{len(self.mesher.mesh_history[-1]["points"])} punktow')

        # Siatka rownomierna
        ax2 = fig.add_subplot(122, projection='3d')
        self.plot_mesh(uniform_mesh, ax=ax2, show_points=False, color='viridis')
        ax2.set_title(f'Siatka rownomierna\n{len(uniform_mesh["points"])} punktow')

        plt.tight_layout()
        return fig

    def plot_interactive_comparison(self, uniform_mesh):
        # Utworz nowe okno
        root = tk.Tk()
        root.title("Porownanie siatkowania terenu")
        root.geometry("1200x800")

        # Ramka dla kontrolek
        control_frame = ttk.Frame(root)
        control_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        # Etykiety informacyjne
        adaptive_label = ttk.Label(control_frame,
                                   text=f"Siatka adaptacyjna: {len(self.mesher.mesh_history[-1]['points'])} punktow")
        adaptive_label.pack(side=tk.LEFT, padx=10)

        uniform_label = ttk.Label(control_frame,
                                  text=f"Siatka rownomierna: {len(uniform_mesh['points'])} punktow")
        uniform_label.pack(side=tk.LEFT, padx=10)

        # Przycisk do zmiany widoku
        view_var = tk.StringVar(value="wireframe")

        def change_view():
            redraw_plots()

        wireframe_radio = ttk.Radiobutton(control_frame, text="Siatka", variable=view_var,
                                          value="wireframe", command=change_view)
        wireframe_radio.pack(side=tk.LEFT, padx=10)

        surface_radio = ttk.Radiobutton(control_frame, text="Powierzchnia", variable=view_var,
                                        value="surface", command=change_view)
        surface_radio.pack(side=tk.LEFT, padx=10)

        points_var = tk.BooleanVar(value=False)
        points_check = ttk.Checkbutton(control_frame, text="Pokaz punkty", variable=points_var,
                                       command=change_view)
        points_check.pack(side=tk.LEFT, padx=10)

        # Ramka dla wykresow
        plot_frame = ttk.Frame(root)
        plot_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Utworz figury i osie
        fig1 = Figure(figsize=(6, 5))
        ax1 = fig1.add_subplot(111, projection='3d')

        fig2 = Figure(figsize=(6, 5))
        ax2 = fig2.add_subplot(111, projection='3d')

        # Umiesc figury w ramce
        canvas1 = FigureCanvasTkAgg(fig1, master=plot_frame)
        canvas1_widget = canvas1.get_tk_widget()
        canvas1_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        canvas2 = FigureCanvasTkAgg(fig2, master=plot_frame)
        canvas2_widget = canvas2.get_tk_widget()
        canvas2_widget.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        def redraw_plots():
            ax1.clear()
            ax2.clear()

            show_points = points_var.get()
            view_mode = view_var.get()

            # Siatka adaptacyjna
            if view_mode == "wireframe":
                self.plot_mesh(self.mesher.mesh_history[-1], ax=ax1, show_points=show_points, alpha=0.7)
            else:
                self.plot_mesh(self.mesher.mesh_history[-1], ax=ax1, show_points=show_points, alpha=0.9)

            ax1.set_title(f'Siatka adaptacyjna\n({len(self.mesher.mesh_history[-1]["points"])} punktow)')

            # Siatka rownomierna
            if view_mode == "wireframe":
                self.plot_mesh(uniform_mesh, ax=ax2, show_points=show_points, alpha=0.7, color='viridis')
            else:
                self.plot_mesh(uniform_mesh, ax=ax2, show_points=show_points, alpha=0.9, color='viridis')

            ax2.set_title(f'Siatka rownomierna\n({len(uniform_mesh["points"])} punktow)')

            # Synchronizuj widoki
            ax1.view_init(elev=30, azim=45)
            ax2.view_init(elev=30, azim=45)

            # Odswiezenie wykresow
            canvas1.draw()
            canvas2.draw()

        # Poczatkowe rysowanie
        redraw_plots()

        # Przycisk do zamkniecia
        close_button = ttk.Button(root, text="Zamknij", command=root.destroy)
        close_button.pack(side=tk.BOTTOM, pady=10)

        # Uruchom petle zdarzen
        root.mainloop()