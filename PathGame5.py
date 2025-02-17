# ---------------------------
# Libraries
# ---------------------------
import tkinter as tk
from tkinter import messagebox
import random
import time
import math


# ---------------------------
# Global Defaults and Variables
# ---------------------------
CELL_SIZE = 40         # Cell pixel size
max_grid_value = 20    # Max grid dimension

# Set from title screen:
grid_width = 10        # Number of columns (x-axis)
grid_height = 10       # Number of rows (y-axis)
difficulty = None      # "Easy" or "Hard"
min_path_length = None # Minimum number of cells in path
max_path_length = None # Maximum number of cells in path

# Game state variables:
path = []              # Lists (row, col) tuples for path
current_index = 0      # Which cell in path user must click next
game_state = "waiting" # "waiting", "memorize", or "play"

# Timer variables:
timer_start = None
timer_update_job = None
timer_running = False


# Main Window Setup
root = tk.Tk()
root.title("Pathing Game")


# ---------------------------
# Title Screen
# ---------------------------

title_frame = tk.Frame(root)
title_frame.pack(padx=10, pady=10)

title_label = tk.Label(title_frame, text="Pathing Game", font=("Arial", 24))
title_label.pack(pady=10)

# Grid size inputs:
grid_frame = tk.Frame(title_frame)
grid_frame.pack(pady=5)

x_label = tk.Label(grid_frame, text="X-Axis (columns):")
x_label.grid(row=0, column=0, padx=5, pady=5)
x_entry = tk.Entry(grid_frame, width=5)
x_entry.grid(row=0, column=1, padx=5, pady=5)
x_entry.insert(0, "10")

y_label = tk.Label(grid_frame, text="Y-Axis (rows):")
y_label.grid(row=1, column=0, padx=5, pady=5)
y_entry = tk.Entry(grid_frame, width=5)
y_entry.grid(row=1, column=1, padx=5, pady=5)
y_entry.insert(0, "10")

# Difficulty selection: Easy/Hard
difficulty_var = tk.StringVar(value="Easy")
diff_frame = tk.Frame(title_frame)
diff_frame.pack(pady=5)

diff_label = tk.Label(diff_frame, text="Select Difficulty:")
diff_label.pack()
easy_rb = tk.Radiobutton(diff_frame, text="Easy", variable=difficulty_var, value="Easy")
easy_rb.pack(anchor="w")
hard_rb = tk.Radiobutton(diff_frame, text="Hard", variable=difficulty_var, value="Hard")
hard_rb.pack(anchor="w")

def start_button_click():
    global grid_width, grid_height, difficulty, min_path_length, max_path_length
    try:
        gw = int(x_entry.get())
        gh = int(y_entry.get())
    except ValueError:
        messagebox.showerror("Invalid Input", "Stahp trying to break the game, just put in numbers.")
        return
    if gw < 2 or gh < 2 or gw > max_grid_value or gh > max_grid_value:
        messagebox.showerror("Invalid Input", f"Grid sizes must be between 2 and {max_grid_value}.")
        return

    grid_width = gw
    grid_height = gh
    difficulty = difficulty_var.get()

    # Difficulty ranges.
    if difficulty == "Easy":
        min_path_length = grid_width              # Min one cell per column
        max_path_length = math.ceil(grid_width * 2.5)
    elif difficulty == "Hard":
        min_path_length = math.ceil(grid_width * 4) + 1
        max_path_length = grid_width * grid_height  # full grid, logic later fixes this

    # Check if grid's big enough for difficulty range requirements
    if grid_width * grid_height < min_path_length:
        messagebox.showerror("Invalid Grid Size", 
                             "Difficulty selected can't be applied to desired grid size. Please modify grid values.")
        return

    # Proceed to game screen
    title_frame.pack_forget()
    init_game_frame()

start_button = tk.Button(title_frame, text="Start", command=start_button_click)
start_button.pack(pady=10)

# ---------------------------
# Game Screen and Controls
# ---------------------------
# Note* game_frame created fresh in init_game_frame
canvas = None
control_frame = None
show_path_button = None
timer_label = None

def init_game_frame():
    global canvas, control_frame, show_path_button, timer_label, game_frame
    # Create new game_frame so previous game windows are removed
    game_frame = tk.Frame(root)
    game_frame.pack(padx=10, pady=10)
    
    canvas_width_px = grid_width * CELL_SIZE
    canvas_height_px = grid_height * CELL_SIZE

    # Create canvas for grid
    canvas = tk.Canvas(game_frame, width=canvas_width_px, height=canvas_height_px)
    canvas.grid(row=0, column=0, padx=10, pady=10)

    # Create control panel below canvas
    control_frame = tk.Frame(game_frame)
    control_frame.grid(row=1, column=0, pady=5)

    show_path_button = tk.Button(control_frame, text="Show Path", command=on_show_path)
    show_path_button.pack(side="left", padx=5)

    timer_label = tk.Label(control_frame, text="Time: 0.00 s")
    timer_label.pack(side="left", padx=5)

    reset_button = tk.Button(control_frame, text="Reset", command=reset_game)
    reset_button.pack(side="left", padx=5)
    
    home_button = tk.Button(control_frame, text="Home", command=go_home)
    home_button.pack(side="left", padx=5)

    reset_game()

# ---------------------------
# Drawing Functions
# ---------------------------
def draw_grid():
    canvas.delete("all")
    for i in range(grid_height):
        for j in range(grid_width):
            x0 = j * CELL_SIZE
            y0 = i * CELL_SIZE
            x1 = x0 + CELL_SIZE
            y1 = y0 + CELL_SIZE
            canvas.create_rectangle(x0, y0, x1, y1, fill="white", outline="black")

def draw_path_highlight():
    # Show memorization path with numbered cells
    for idx, (r, c) in enumerate(path):
        x0 = c * CELL_SIZE
        y0 = r * CELL_SIZE
        x1 = x0 + CELL_SIZE
        y1 = y0 + CELL_SIZE
        canvas.create_rectangle(x0, y0, x1, y1, fill="lightblue", outline="black")
        # Draw step number in center
        cx = x0 + CELL_SIZE/2
        cy = y0 + CELL_SIZE/2
        canvas.create_text(cx, cy, text=str(idx+1), font=("Arial", 16), fill="black")

# ---------------------------
# Path Generation
# ---------------------------
def generate_path():
    global grid_width, grid_height, min_path_length, max_path_length
    # Try starting from random row in first column
    start_rows = list(range(grid_height))
    random.shuffle(start_rows)
    for start_row in start_rows:
        grid_visited = [[False] * grid_width for _ in range(grid_height)]
        current_path = []
        def dfs(r, c):
            # Only the very first cell is allowed in column 0
            if c == 0 and current_path:
                return False

            current_path.append((r, c))
            grid_visited[r][c] = True

            # Check length once reaching last column
            if c == grid_width - 1:
                if min_path_length <= len(current_path) <= max_path_length:
                    return True
                else:
                    grid_visited[r][c] = False
                    current_path.pop()
                    return False

            if len(current_path) >= max_path_length:
                grid_visited[r][c] = False
                current_path.pop()
                return False

            directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
            random.shuffle(directions)
            for dr, dc in directions:
                nr, nc = r + dr, c + dc
                # Check boundaries
                if not (0 <= nr < grid_height and 0 <= nc < grid_width):
                    continue
                if grid_visited[nr][nc]:
                    continue
                # Disallow going back into column 0 (except for start)
                if nc == 0:
                    continue
                # If currently in last column, don't leave it
                if c == grid_width - 1 and nc != grid_width - 1:
                    continue
                # Enforce candidate cell, the next good cell in path, (nr,nc) touches ONLY current cell
                # Ensures each cell has two adjacent good cells max
                adjacent_count = 0
                for ddr, ddc in [(-1,0), (1,0), (0,-1), (0,1)]:
                    ar, ac = nr + ddr, nc + ddc
                    if (ar, ac) in current_path:
                        adjacent_count += 1
                if adjacent_count != 1:
                    continue

                if dfs(nr, nc):
                    return True
            grid_visited[r][c] = False
            current_path.pop()
            return False

        if dfs(start_row, 0):
            return current_path
    return None

# ---------------------------
# Reset Game / Revert to Title Screen if necessary
# ---------------------------
def reset_game():
    global path, current_index, game_state, timer_start
    stop_timer()
    timer_label.config(text="Time: 0.00 s")
    game_state = "waiting"
    current_index = 0
    draw_grid()
    valid_path = generate_path()
    if valid_path is None:
        messagebox.showerror("Invalid Grid/Difficulty", 
                             "Difficulty selected can't be applied to desired grid size. Please modify grid values.")
        go_home()  # Return to title if no valid path can be generated
        return
    path = valid_path
    canvas.unbind("<Button-1>")
    show_path_button.config(state="normal")

# ---------------------------
# Timer Functions
# ---------------------------
def update_timer():
    global timer_start, timer_update_job
    if timer_start is None:
        return
    elapsed = time.time() - timer_start
    timer_label.config(text=f"Time: {elapsed:.2f} s")
    timer_update_job = root.after(50, update_timer)

def stop_timer():
    global timer_start, timer_update_job, timer_running
    timer_start = None
    if timer_update_job is not None:
        root.after_cancel(timer_update_job)
        timer_update_job = None
    timer_running = False

# ---------------------------
# Game Flow: Memorization and Play Phases
# ---------------------------
def on_show_path():
    global game_state, timer_start, timer_running
    if game_state != "waiting":
        return
    game_state = "memorize"
    show_path_button.config(state="disabled")
    draw_grid()
    draw_path_highlight()
    timer_start = time.time()
    timer_running = True
    update_timer()
    # Bind a click to end the memorization phase
    canvas.bind("<Button-1>", end_memorization)

def end_memorization(event):
    global game_state
    if game_state != "memorize":
        return
    stop_timer()
    draw_grid()  # Hide highlighted path
    canvas.unbind("<Button-1>")
    game_state = "play"
    canvas.bind("<Button-1>", on_game_click)

def on_game_click(event):
    global current_index, game_state
    if game_state != "play":
        return
    col = event.x // CELL_SIZE
    row = event.y // CELL_SIZE
    if row < 0 or row >= grid_height or col < 0 or col >= grid_width:
        return
    if current_index >= len(path):
        return
    correct_cell = path[current_index]
    x0 = col * CELL_SIZE
    y0 = row * CELL_SIZE
    x1 = x0 + CELL_SIZE
    y1 = y0 + CELL_SIZE
    if (row, col) == correct_cell:
        # Mark correct cell with green and display its number
        canvas.create_rectangle(x0, y0, x1, y1, fill="lightgreen", outline="black")
        canvas.create_text(x0 + CELL_SIZE/2, y0 + CELL_SIZE/2,
                           text=str(current_index+1), font=("Arial", 16), fill="black")
        current_index += 1
        if current_index == len(path):
            messagebox.showinfo("Success", "You successfully followed the path!")
            canvas.unbind("<Button-1>")
    else:
        canvas.create_rectangle(x0, y0, x1, y1, fill="red", outline="black")
        messagebox.showerror("Error", "Wrong cell! The game will reset.")
        reset_game()

# ---------------------------
# Home Button Functionality
# ---------------------------
def go_home():
    stop_timer()
    if canvas:
        canvas.unbind("<Button-1>")
    # Destroy game frame so old grid removed
    global game_frame
    game_frame.destroy()
    # Show title screen again
    title_frame.pack(padx=10, pady=10)

# ---------------------------
# Start the Tkinter Event Loop
# ---------------------------
root.mainloop()
