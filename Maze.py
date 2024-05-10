from collections import deque
import random
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox, filedialog
from abc import ABC, abstractmethod
import time
from enum import Enum
import csv

class State(Enum):
    EMPTY = 0
    WALL = 1

def generate_dfs_maze(width, height, start, end, app: "MazeSolverApp | None" = None):
    maze = [[State.WALL for _ in range(width)] for _ in range(height)]
    stack = [start]

    if app is not None:
        # fill the maze black
        for y in range(0, height):
            for x in range(0, width):
                app.renderer.draw((x, y), MazeSolverApp.WALL_COLOR)

    def is_within_bounds(x, y):
        return 0 <= x < width and 0 <= y < height

    while stack:
        current_cell = stack[-1]
        maze[current_cell[1]][current_cell[0]] = State.EMPTY
        if app and not app.stop_animation:
            app.renderer.draw(current_cell, MazeSolverApp.OPEN_COLOR)
            app.root.update()
            time.sleep(0.05)

        neighbors = []
        for dx, dy in [(0, -2), (0, 2), (-2, 0), (2, 0)]:
            x, y = current_cell[0] + dx, current_cell[1] + dy
            if is_within_bounds(x, y) and maze[y][x] == State.WALL:
                neighbors.append((x, y))

        if neighbors:
            next_cell = random.choice(neighbors)
            nx, ny = next_cell
            wall_x, wall_y = (current_cell[0] + nx) // 2, (current_cell[1] + ny) // 2
            maze[wall_y][wall_x] = State.EMPTY
            if app and not app.stop_animation:
                app.renderer.draw((wall_x, wall_y), MazeSolverApp.OPEN_COLOR)
                app.root.update()
                time.sleep(0.05)
            stack.append(next_cell)
        else:
            stack.pop()

        if app and app.stop_animation:
            return maze

    # Set entrance and exit
    maze[start[1]][start[0]] = State.EMPTY
    maze[end[1]][end[0]] = State.EMPTY
    return maze


def generate_kruskal_maze(width, height, start, end, app: "MazeSolverApp | None" = None):
    maze = [[State.WALL for _ in range(width)] for _ in range(height)]
    parent = {}
    rank = {}

    if app is not None:
        # fill the maze black
        for y in range(0, height):
            for x in range(0, width):
                app.renderer.draw((x, y), MazeSolverApp.WALL_COLOR)

    def find(node):
        if parent[node] != node:
            parent[node] = find(parent[node])
        return parent[node]

    def union(node1, node2):
        root1, root2 = find(node1), find(node2)
        if root1 != root2:
            if rank[root1] > rank[root2]:
                parent[root2] = root1
            else:
                parent[root1] = root2
                if rank[root1] == rank[root2]:
                    rank[root2] += 1

    edges = []

    for y in range(1, height, 2):
        for x in range(1, width, 2):
            parent[(x, y)] = (x, y)
            rank[(x, y)] = 0
            maze[y][x] = State.EMPTY

            if x + 2 < width:
                edges.append(((x, y), (x + 2, y), (x + 1, y)))
            if y + 2 < height:
                edges.append(((x, y), (x, y + 2), (x, y + 1)))

    random.shuffle(edges)

    for (x1, y1), (x2, y2), (wx, wy) in edges:
        if find((x1, y1)) != find((x2, y2)):
            union((x1, y1), (x2, y2))
            maze[wy][wx] = State.EMPTY
            if app and not app.stop_animation:
                app.renderer.draw((x1, y1), MazeSolverApp.OPEN_COLOR)
                app.renderer.draw((x2, y2), MazeSolverApp.OPEN_COLOR)
                app.renderer.draw((wx, wy), MazeSolverApp.OPEN_COLOR)
                app.root.update()
                time.sleep(0.05)

        if app and app.stop_animation:
            return maze

    # Set entrance and exit
    maze[start[1]][start[0]] = State.EMPTY
    maze[end[1]][end[0]] = State.EMPTY
    return maze


def bfs_shortest_path(maze, start, end, app: "MazeSolverApp | None" = None):
    directions = [(0, -1), (0, 1), (-1, 0), (1, 0)]
    queue = deque([(start, [])])
    visited = set()
    visited.add(start)

    while queue:
        (x, y), path = queue.popleft()
        if app and not app.stop_animation:
            app.renderer.draw((x, y), MazeSolverApp.EXPLORE_COLOR)
            app.root.update()
            time.sleep(0.05)

        if app and app.stop_animation:
            return None

        if (x, y) == end:
            return path + [(x, y)]

        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if 0 <= nx < len(maze[0]) and 0 <= ny < len(maze) and maze[ny][nx] == State.EMPTY and (nx, ny) not in visited:
                queue.append(((nx, ny), path + [(x, y)]))
                visited.add((nx, ny))

    return None


class Renderer(ABC):
    @abstractmethod
    def draw(self, pos, color):
        pass

    @abstractmethod
    def clear(self, pos):
        pass

    @abstractmethod
    def clear_all(self):
        pass


class CanvasRenderer(Renderer):
    def __init__(self, canvas, cell_size, root):
        self.canvas = canvas
        self.cell_size = cell_size
        self.rectangles = {}
        self.root = root

    def draw(self, pos, color):
        x, y = pos
        if pos not in self.rectangles:
            rect = self.canvas.create_rectangle(
                x * self.cell_size, y * self.cell_size,
                (x + 1) * self.cell_size, (y + 1) * self.cell_size,
                fill=color
            )
            self.rectangles[pos] = rect
        else:
            self.canvas.itemconfig(self.rectangles[pos], fill=color)

    def clear(self, pos):
        if pos in self.rectangles:
            self.canvas.itemconfig(self.rectangles[pos], fill='white')

    def clear_all(self):
        for rect in self.rectangles.values():
            self.canvas.itemconfig(rect, fill='white')


class MazeSolverApp:
    CELL_SIZE = 25
    WALL_COLOR = "black"
    PATH_COLOR = "red"
    OPEN_COLOR = "white"
    START_COLOR = "grey"
    END_COLOR = "grey"
    EXPLORE_COLOR = "yellow"

    def __init__(self, root):
        self.root = root
        self.root.title("Maze Solver")

        # Controls Frame
        controls_frame = tk.Frame(self.root)
        controls_frame.pack(pady=10, side=tk.RIGHT)

        # Generation Settings
        config_frame = tk.LabelFrame(controls_frame, text="迷宫设置", padx=10, pady=10)
        config_frame.grid(row=0, column=0, padx=10, pady=5, sticky="W")

        tk.Label(config_frame, text="宽度: ").grid(row=0, column=0, padx=5, pady=2)
        self.width_entry = tk.Entry(config_frame, width=5)
        self.width_entry.grid(row=0, column=1, padx=5, pady=2)
        self.width_entry.insert(0, "21")

        tk.Label(config_frame, text="高度: ").grid(row=1, column=0, padx=5, pady=2)
        self.height_entry = tk.Entry(config_frame, width=5)
        self.height_entry.grid(row=1, column=1, padx=5, pady=2)
        self.height_entry.insert(0, "21")

        tk.Label(config_frame, text="起点 (x, y): ").grid(row=2, column=0, padx=5, pady=2)
        self.start_entry = tk.Entry(config_frame, width=5)
        self.start_entry.grid(row=2, column=1, padx=5, pady=2)
        self.start_entry.insert(0, "1,1")

        tk.Label(config_frame, text="终点 (x, y): ").grid(row=3, column=0, padx=5, pady=2)
        self.end_entry = tk.Entry(config_frame, width=5)
        self.end_entry.grid(row=3, column=1, padx=5, pady=2)
        self.end_entry.insert(0, "19,19")

        algorithm_frame = tk.LabelFrame(controls_frame, text="算法", padx=10, pady=10)
        algorithm_frame.grid(row=4, column=0, columnspan=2, padx=10, pady=5, sticky="W")

        self.generate_algorithm_var = tk.StringVar(value="DFS")
        self.generate_algorithm_combobox = ttk.Combobox(algorithm_frame, textvariable=self.generate_algorithm_var, values=["DFS", "Kruskal"], state="readonly", width=6)
        self.generate_algorithm_combobox.grid(row=0, column=1, padx=10, pady=5)

        self.generate_button = tk.Button(algorithm_frame, text="生成", command=self.generate_maze)
        self.generate_button.grid(row=0, column=0, padx=10, pady=5)

        self.solve_algorithm_var = tk.StringVar(value="BFS")
        self.solve_algorithm_combobox = ttk.Combobox(algorithm_frame, textvariable=self.solve_algorithm_var, values=["BFS"], state="readonly", width=6)
        self.solve_algorithm_combobox.grid(row=1, column=1, padx=10, pady=5)

        self.solve_button = tk.Button(algorithm_frame, text="求解", command=self.solve_maze)
        self.solve_button.grid(row=1, column=0, padx=10, pady=5)

        # Animation Mode
        self.animate_var = tk.IntVar()
        self.animate_checkbox = tk.Checkbutton(algorithm_frame, text="动画模式", variable=self.animate_var, command=self.on_checkbox_toggle)
        self.animate_checkbox.grid(row=2, column=0, padx=10, pady=5, columnspan=2)

        # Import/Export
        import_export_frame = tk.LabelFrame(controls_frame, text="导入/导出", padx=10, pady=10)
        import_export_frame.grid(row=3, column=0, padx=10, pady=10, sticky="W")

        self.export_button = tk.Button(import_export_frame, text="导出迷宫", command=self.export_maze)
        self.export_button.grid(row=0, column=0, padx=10, pady=5)

        self.import_button = tk.Button(import_export_frame, text="导入迷宫", command=self.import_maze)
        self.import_button.grid(row=1, column=0, padx=10, pady=5)

        # Canvas for Maze Display
        self.canvas = tk.Canvas(self.root, bg="white")
        self.canvas.pack(padx=20, side=tk.LEFT)

        # Maze Variables
        self.cell_size = MazeSolverApp.CELL_SIZE
        self.renderer = CanvasRenderer(self.canvas, self.cell_size, self.root)

        self.maze = []
        self.path = []
        self.width = 21
        self.height = 21
        self.start : tuple[int, int] = (1, 1)
        self.end : tuple[int, int] = (19, 19)
        self.stop_animation = False

        # Initial Maze Generation
        self.generate_maze()

    def parse_coordinates(self, entry) -> tuple[int, int] | None:
        try:
            x, y = map(int, entry.get().split(","))
            return (x, y)
        except ValueError:
            messagebox.showerror("输入错误", f"无效的坐标: {entry.get()}")
            return None

    def validate_start_end(self):
        """Ensure that the start and end coordinates are not too close to edges and are within the maze bounds."""
        def is_too_close_to_edges(x, y):
            return x < 1 or y < 1 or x >= self.width - 1 or y >= self.height - 1

        if is_too_close_to_edges(self.start[0], self.start[1]):
            messagebox.showerror("输入错误", "起点距离边界太近，请保持至少1个单位距离。")
            return False
        if is_too_close_to_edges(self.end[0], self.end[1]):
            messagebox.showerror("输入错误", "终点距离边界太近，请保持至少1个单位距离。")
            return False
        return True

    def generate_maze(self):
        # Stop animation
        self.stop_animation = True
        self.clear_maze()
        self.renderer.clear_all()

        try:
            self.width = int(self.width_entry.get())
            self.height = int(self.height_entry.get())
        except ValueError:
            messagebox.showerror("输入错误", "宽度和高度必须是整数！")
            return

        if self.width < 5 or self.height < 5:
            messagebox.showerror("输入错误", "宽度和高度必须至少5。")
            return

        if self.width % 2 == 0 or self.height % 2 == 0:
            messagebox.showerror("输入错误", "宽度和高度必须是奇数。")
            return

        # Parse start and end coordinates
        start = self.parse_coordinates(self.start_entry)
        end = self.parse_coordinates(self.end_entry)

        if not start or not end:
            return

        self.start = start
        self.end = end

        if not (0 <= self.start[0] < self.width and 0 <= self.start[1] < self.height) or \
           not (0 <= self.end[0] < self.width and 0 <= self.end[1] < self.height):
            messagebox.showerror("输入错误", "起点或终点位置超出迷宫范围！")
            return

        if not self.validate_start_end():
            return

        # Choose maze generation algorithm
        algorithm = self.generate_algorithm_var.get()
        if algorithm == "DFS":
            if self.animate_var.get():
                self.stop_animation = False
                self.maze = generate_dfs_maze(self.width, self.height, self.start, self.end, self)
            else:
                self.maze = generate_dfs_maze(self.width, self.height, self.start, self.end)
        elif algorithm == "Kruskal":
            if self.animate_var.get():
                self.stop_animation = False
                self.maze = generate_kruskal_maze(self.width, self.height, self.start, self.end, self)
            else:
                self.maze = generate_kruskal_maze(self.width, self.height, self.start, self.end)

        self.path = []
        self.resize_canvas()
        self.draw_maze()

    def solve_maze(self):
        # Stop animation
        self.stop_animation = True
        # Clear previous exploration path
        self.clear_maze()

        if self.animate_var.get():
            self.stop_animation = False
            self.path = bfs_shortest_path([row[:] for row in self.maze], self.start, self.end, self)
        else:
            self.path = bfs_shortest_path([row[:] for row in self.maze], self.start, self.end)

        if self.path:
            self.draw_maze()
        else:
            messagebox.showinfo("迷宫求解器", "未找到解决方案！")

    def on_checkbox_toggle(self):
        # Stop animation when checkbox is toggled
        self.stop_animation = True

    def resize_canvas(self):
        self.canvas.config(width=self.width * self.cell_size, height=self.height * self.cell_size)
        self.renderer = CanvasRenderer(self.canvas, self.cell_size, self.root)

    def draw_maze(self):
        self.renderer.clear_all()
        for y, row in enumerate(self.maze):
            for x, cell in enumerate(row):
                fill_color = MazeSolverApp.WALL_COLOR if cell == State.WALL else MazeSolverApp.OPEN_COLOR
                if self.path and (x, y) in self.path:
                    fill_color = MazeSolverApp.PATH_COLOR
                if (x, y) == self.start:
                    fill_color = MazeSolverApp.START_COLOR
                if (x, y) == self.end:
                    fill_color = MazeSolverApp.END_COLOR
                self.renderer.draw((x, y), fill_color)

    def clear_maze(self):
        """Clears the exploration path and solves path"""
        for y, row in enumerate(self.maze):
            for x, cell in enumerate(row):
                if (x, y) != self.start and (x, y) != self.end and cell != State.WALL:
                    self.renderer.clear((x, y))

    def export_maze(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".csv",
                                                 filetypes=[("CSV files", "*.csv")],
                                                 title="选择导出文件的路径")
        if file_path:
            try:
                with open(file_path, mode='w', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow(["Width", self.width])
                    writer.writerow(["Height", self.height])
                    writer.writerow(["Start", self.start[0], self.start[1]])
                    writer.writerow(["End", self.end[0], self.end[1]])
                    for row in self.maze:
                        writer.writerow([cell.value for cell in row])
                messagebox.showinfo("导出成功", f"迷宫已成功导出到 {file_path}")
            except Exception as e:
                messagebox.showerror("导出错误", f"导出迷宫时发生错误: {e}")

    def import_maze(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")],
                                               title="选择要导入的迷宫文件")
        if file_path:
            try:
                with open(file_path, mode='r', newline='') as file:
                    reader = csv.reader(file)
                    rows = list(reader)

                    self.width = int(rows[0][1])
                    self.height = int(rows[1][1])
                    self.start = (int(rows[2][1]), int(rows[2][2]))
                    self.end = (int(rows[3][1]), int(rows[3][2]))

                    self.maze = [[State(int(cell)) for cell in row] for row in rows[4:]]

                    self.width_entry.delete(0, tk.END)
                    self.width_entry.insert(0, str(self.width))

                    self.height_entry.delete(0, tk.END)
                    self.height_entry.insert(0, str(self.height))

                    self.start_entry.delete(0, tk.END)
                    self.start_entry.insert(0, f"{self.start[0]},{self.start[1]}")

                    self.end_entry.delete(0, tk.END)
                    self.end_entry.insert(0, f"{self.end[0]},{self.end[1]}")

                self.resize_canvas()
                self.path = []
                self.draw_maze()
                messagebox.showinfo("导入成功", f"迷宫已成功从 {file_path} 导入")
            except Exception as e:
                messagebox.showerror("导入错误", f"导入迷宫时发生错误: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = MazeSolverApp(root)
    root.mainloop()
