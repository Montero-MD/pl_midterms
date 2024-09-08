import os
from collections import defaultdict
import tkinter as tk
from tkinter import filedialog, ttk, messagebox

# Function to calculate disk usage
def get_disk_usage(path):
    """Recursively calculate disk usage for each directory and file."""
    total_size = 0
    ext_usage = defaultdict(int)

    try:
        for entry in os.scandir(path):
            if entry.is_dir(follow_symlinks=False):
                sub_size, sub_ext_usage = get_disk_usage(entry.path)
                total_size += sub_size
                for ext, size in sub_ext_usage.items():
                    ext_usage[ext] += size
            else:
                size = entry.stat().st_size
                total_size += size
                _, ext = os.path.splitext(entry.name)
                ext_usage[ext] += size
    except PermissionError:
        print(f"Permission Denied: {path}")

    return total_size, ext_usage

# Function to display directory tree view
def display_tree_view(tree, path, total_space, parent=''):
    """Recursively display the directory tree view with percentage usage."""
    size, _ = get_disk_usage(path)
    percentage = (size / total_space) * 100 if total_space else 0
    item_id = tree.insert(parent, 'end', text=f"{os.path.basename(path)}/ - {size} bytes ({percentage:.2f}%)")

    try:
        for entry in os.scandir(path):
            if entry.is_dir(follow_symlinks=False):
                display_tree_view(tree, entry.path, total_space, item_id)
    except PermissionError:
        tree.insert(item_id, 'end', text=f"Permission Denied: {path}")

# Function to display sorted file extensions
def display_sorted_extensions(tree, ext_usage):
    """Display a sorted list of file extensions by total usage."""
    sorted_ext = sorted(ext_usage.items(), key=lambda x: x[1], reverse=True)
    for ext, size in sorted_ext:
        tree.insert('', 'end', text=f"{ext}: {size} bytes")

# Function to handle directory selection
def analyze_directory():
    path = filedialog.askdirectory()
    if not path:
        return

    total_size, ext_usage = get_disk_usage(path)

    tree.delete(*tree.get_children())  # Clear the tree view
    display_tree_view(tree, path, total_size)

    ext_tree.delete(*ext_tree.get_children())  # Clear the extension list
    display_sorted_extensions(ext_tree, ext_usage)

# GUI setup
root = tk.Tk()
root.title("Disk Usage Analyzer")

frame = ttk.Frame(root, padding="10")
frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

button = ttk.Button(frame, text="Select Directory", command=analyze_directory)
button.grid(row=0, column=0, pady=5)

tree = ttk.Treeview(frame)
tree.heading("#0", text="Disk Usage Tree View", anchor='w')
tree.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

ext_frame = ttk.Frame(root, padding="10")
ext_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

ext_tree = ttk.Treeview(ext_frame)
ext_tree.heading("#0", text="File Extension Usage", anchor='w')
ext_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

root.mainloop()
