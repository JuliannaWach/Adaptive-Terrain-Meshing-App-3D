import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
import time
from terrain_data import TerrainData
from adaptive_mesher import AdaptiveMesher
from terrain_visualizer import TerrainVisualizer

class TerrainApp:
    def __init__(self, master):
        self.master = master
        master.title("System adaptacyjnego siatkowania terenu 3D")
        master.geometry("1000x700")

        # Inicjalizacja zmiennych
        self.terrain_data = None
        self.mesher = None
        self.visualizer = None
        self.uniform_mesh = None

        # Utworzenie interfejsu uzytkownika
        self._create_ui()

        # Stan aplikacji
        self.is_mesh_generated = False

    def _create_ui(self):
        # Glowna ramka
        main_frame = ttk.Frame(self.master)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Lewa ramka kontrolna
        control_frame = ttk.LabelFrame(main_frame, text="Ustawienia")
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        # Ramka do generowania terenu
        terrain_frame = ttk.LabelFrame(control_frame, text="Generowanie terenu")
        terrain_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(terrain_frame, text="Typ terenu:").pack(anchor=tk.W, padx=5, pady=2)

        self.terrain_type_var = tk.StringVar(value="gaussian_hills")
        terrain_types = ["gaussian_hills", "sine_waves", "ridges", "crater"]
        terrain_combobox = ttk.Combobox(terrain_frame, textvariable=self.terrain_type_var,
                                        values=terrain_types, state="readonly")
        terrain_combobox.pack(fill=tk.X, padx=5, pady=2)

        generate_button = ttk.Button(terrain_frame, text="Generuj teren", command=self._generate_terrain)
        generate_button.pack(fill=tk.X, padx=5, pady=5)

        # Ramka do siatkowania
        mesh_frame = ttk.LabelFrame(control_frame, text="Parametry siatkowania")
        mesh_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(mesh_frame, text="Min. liczba punktow:").pack(anchor=tk.W, padx=5, pady=2)
        self.min_points_var = tk.StringVar(value="100")
        min_points_entry = ttk.Entry(mesh_frame, textvariable=self.min_points_var)
        min_points_entry.pack(fill=tk.X, padx=5, pady=2)

        ttk.Label(mesh_frame, text="Max. liczba punktow:").pack(anchor=tk.W, padx=5, pady=2)
        self.max_points_var = tk.StringVar(value="1000")
        max_points_entry = ttk.Entry(mesh_frame, textvariable=self.max_points_var)
        max_points_entry.pack(fill=tk.X, padx=5, pady=2)

        ttk.Label(mesh_frame, text="Liczba iteracji:").pack(anchor=tk.W, padx=5, pady=2)
        self.iterations_var = tk.StringVar(value="5")
        iterations_entry = ttk.Entry(mesh_frame, textvariable=self.iterations_var)
        iterations_entry.pack(fill=tk.X, padx=5, pady=2)

        ttk.Label(mesh_frame, text="Prog bledu:").pack(anchor=tk.W, padx=5, pady=2)
        self.error_threshold_var = tk.StringVar(value="0.1")
        error_entry = ttk.Entry(mesh_frame, textvariable=self.error_threshold_var)
        error_entry.pack(fill=tk.X, padx=5, pady=2)

        generate_mesh_button = ttk.Button(mesh_frame, text="Generuj siatke",
                                          command=self._generate_mesh)
        generate_mesh_button.pack(fill=tk.X, padx=5, pady=5)

        # Ramka do wizualizacji
        viz_frame = ttk.LabelFrame(control_frame, text="Wizualizacja")
        viz_frame.pack(fill=tk.X, padx=5, pady=5)

        compare_button = ttk.Button(viz_frame, text="Porownaj siatki",
                                    command=self._compare_meshes)
        compare_button.pack(fill=tk.X, padx=5, pady=5)

        show_errors_button = ttk.Button(viz_frame, text="Analiza bledow",
                                        command=self._show_errors)
        show_errors_button.pack(fill=tk.X, padx=5, pady=5)

        interactive_compare_button = ttk.Button(viz_frame, text="Interaktywne porownanie",
                                                command=self._interactive_compare)
        interactive_compare_button.pack(fill=tk.X, padx=5, pady=5)

        # Prawy panel z logami
        log_frame = ttk.LabelFrame(main_frame, text="Log")
        log_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.log_text = tk.Text(log_frame, wrap=tk.WORD, height=20)
        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        self.log_text.config(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Poczatkowy komunikat
        self.log("System adaptacyjnego siatkowania terenu 3D gotowy.")
        self.log("Generuj teren, aby rozpoczac.")

    def log(self, message):
        self.log_text.insert(tk.END, f"{time.strftime('%H:%M:%S')} - {message}\n")
        self.log_text.see(tk.END)

    def _generate_terrain(self):
        try:
            terrain_type = self.terrain_type_var.get()

            self.log(f"Generowanie terenu typu: {terrain_type}")

            # Tworzenie obiektow
            self.terrain_data = TerrainData()

            # Generowanie terenu
            self.terrain_data.generate_terrain(terrain_type=terrain_type)

            self.log(f"Teren wygenerowany pomyslnie.")
            self.is_mesh_generated = False

            # Pokaz teren
            self._show_terrain()

        except Exception as e:
            self.log(f"Blad podczas generowania terenu: {e}")

    def _show_terrain(self):
        try:
            if self.terrain_data is None or self.terrain_data.Z is None:
                self.log("Najpierw wygeneruj teren.")
                return

            self.log("Wyswietlanie terenu...")

            plt.figure(figsize=(10, 8))
            ax = plt.subplot(111, projection='3d')

            # Rysowanie powierzchni
            surf = ax.plot_surface(self.terrain_data.X, self.terrain_data.Y, self.terrain_data.Z,
                                   cmap='terrain', alpha=0.8)

            ax.set_xlabel('X')
            ax.set_ylabel('Y')
            ax.set_zlabel('Z')
            ax.set_title('Wygenerowany teren')

            plt.tight_layout()
            plt.show()

        except Exception as e:
            self.log(f"Blad podczas wyswietlania terenu: {e}")

    def _generate_mesh(self):
        try:
            # Sprawdz, czy teren istnieje
            if self.terrain_data is None or self.terrain_data.Z is None:
                self.log("Najpierw wygeneruj teren.")
                return

            # Pobierz parametry
            min_points = int(self.min_points_var.get())
            max_points = int(self.max_points_var.get())
            iterations = int(self.iterations_var.get())
            error_threshold = float(self.error_threshold_var.get())

            self.log(f"Generowanie siatki adaptacyjnej z parametrami:")
            self.log(f"Min. punktow: {min_points}, Max. punktow: {max_points}")
            self.log(f"Iteracje: {iterations}, Prog bledu: {error_threshold}")

            # Tworzenie obiektow siatkowania
            self.mesher = AdaptiveMesher(self.terrain_data, min_points=min_points, max_points=max_points)

            # Udoskonalanie siatki
            start_time = time.time()
            steps = self.mesher.refine_mesh(num_iterations=iterations, error_threshold=error_threshold)
            end_time = time.time()

            self.log(f"Siatkowanie zakonczone po {steps} krokach.")
            self.log(f"Czas siatkowania: {end_time - start_time:.2f} sekund.")
            self.log(f"Liczba punktow w siatce: {len(self.mesher.current_points)}")

            # Tworzenie wizualizatora
            self.visualizer = TerrainVisualizer(self.terrain_data, self.mesher)

            # Generowanie siatki rownomiernej z podobna liczba punktow dla porownania
            num_points = len(self.mesher.current_points)
            self.uniform_mesh = self.mesher.generate_uniform_mesh(num_points)
            self.log(f"Wygenerowano siatke rownomierna z {len(self.uniform_mesh['points'])} punktami.")

            self.is_mesh_generated = True

            # Pokaz siatke
            self._show_adaptive_mesh()

        except Exception as e:
            self.log(f"Blad podczas generowania siatki: {e}")

    def _show_adaptive_mesh(self):
        try:
            if not self.is_mesh_generated:
                self.log("Najpierw wygeneruj siatke.")
                return

            self.log("Wyswietlanie siatki adaptacyjnej...")

            plt.figure(figsize=(10, 8))
            ax = plt.subplot(111, projection='3d')

            self.visualizer.plot_mesh(self.mesher.mesh_history[-1], ax=ax)
            ax.set_title(f'Siatka adaptacyjna ({len(self.mesher.current_points)} punktow)')

            plt.tight_layout()
            plt.show()

        except Exception as e:
            self.log(f"Blad podczas wyswietlania siatki: {e}")

    def _compare_meshes(self):
        try:
            if not self.is_mesh_generated:
                self.log("Najpierw wygeneruj siatke.")
                return

            self.log("Porownywanie siatki adaptacyjnej i rownomiernej...")

            # Generowanie i wyswietlanie porownania
            fig = self.visualizer.plot_mesh_comparison(self.uniform_mesh)
            plt.show()

        except Exception as e:
            self.log(f"Blad podczas porownywania siatek: {e}")

    def _show_errors(self):
        try:
            if not self.is_mesh_generated:
                self.log("Najpierw wygeneruj siatke.")
                return

            self.log("Analiza bledow siatek...")

            # Generowanie i wyswietlanie analizy bledow
            fig = self.visualizer.plot_error_comparison(self.uniform_mesh)
            plt.show()

        except Exception as e:
            self.log(f"Blad podczas analizy bledow: {e}")

    def _interactive_compare(self):
        try:
            if not self.is_mesh_generated:
                self.log("Najpierw wygeneruj siatke.")
                return

            self.log("Uruchamianie interaktywnego porownania siatek...")

            # Interaktywne porownanie
            self.visualizer.plot_interactive_comparison(self.uniform_mesh)

        except Exception as e:
            self.log(f"Blad podczas interaktywnego porownania: {e}")

def main():
    root = tk.Tk()
    app = TerrainApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()