import os
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from collections import defaultdict

def convert_bytes(size):
    """Convert bytes to its largest possible unit."""
    units = ['bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']
    unit_index = 0

    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1

    return f"{size:.2f} {units[unit_index]}"

def get_disk_usage(path):
    """Recursively calculate disk usage for each directory and file."""
    total_size = 0
    ext_usage = defaultdict(int)
    dir_sizes = []

    try:
        for entry in os.scandir(path):
            if entry.is_dir(follow_symlinks=False):
                # Recursively get size for directories
                sub_size, sub_ext_usage, _ = get_disk_usage(entry.path)
                total_size += sub_size
                dir_sizes.append((entry.name, sub_size))  # Store directory name and size
                for ext, size in sub_ext_usage.items():
                    ext_usage[ext] += size
            else:
                # Get size for files
                size = entry.stat().st_size
                total_size += size

                # Get file extension
                _, ext = os.path.splitext(entry.name)
                ext_usage[ext] += size
                dir_sizes.append((entry.name, size))  # Store file name and size
    except PermissionError:
        print(f"Permission Denied: {path}")

    return total_size, ext_usage, dir_sizes

def print_tree_view(path, depth=0, total_space=0, sort_by="Name"):
    """Get the directory tree view with percentage usage."""
    size, _, dir_sizes = get_disk_usage(path)
    percentage = (size / total_space) * 100 if total_space else 0
    converted_size = convert_bytes(size)
    tree_output = f"{'  ' * depth}{os.path.basename(path)}/ - {converted_size} ({percentage:.2f}%)\n"

    # Sort directories and files by the selected option
    if sort_by == "Name":
        dir_sizes.sort(key=lambda x: x[0].lower())  # Sort by name (case insensitive)
    elif sort_by == "Size":
        dir_sizes.sort(key=lambda x: x[1], reverse=True)  # Sort by size (largest first)

    try:
        for entry_name, entry_size in dir_sizes:
            entry_path = os.path.join(path, entry_name)
            if os.path.isdir(entry_path):
                tree_output += print_tree_view(entry_path, depth + 1, total_space, sort_by)
            else:
                percentage = (entry_size / total_space) * 100 if total_space else 0
                converted_entry_size = convert_bytes(entry_size)
                tree_output += f"{'  ' * (depth + 1)}{entry_name} - {converted_entry_size} ({percentage:.2f}%)\n"
    except PermissionError:
        tree_output += f"{'  ' * (depth + 1)}Permission Denied: {path}\n"

    return tree_output

def print_sorted_extensions(ext_usage):
    """Get a sorted list of file extensions by total usage."""
    sorted_ext = sorted(ext_usage.items(), key=lambda x: x[1], reverse=True)
    ext_output = "\nFile Extension Usage:\n"
    for ext, size in sorted_ext:
        converted_size = convert_bytes(size)
        ext_output += f"{ext}: {converted_size}\n"
    return ext_output

def analyze_directory():
    """Function to analyze the selected directory and display results."""
    path = path_entry.get()
    sort_by = sort_var.get()
    total_size, ext_usage, _ = get_disk_usage(path)

    # Display Tree View
    tree_view_output = print_tree_view(path, total_space=total_size, sort_by=sort_by)
    tree_view_text.delete(1.0, tk.END)
    tree_view_text.insert(tk.END, tree_view_output)

    # Display Sorted Extensions
    ext_usage_output = print_sorted_extensions(ext_usage)
    ext_usage_text.delete(1.0, tk.END)
    ext_usage_text.insert(tk.END, ext_usage_output)

def browse_directory():
    """Open a file dialog to select a directory."""
    directory = filedialog.askdirectory()
    path_entry.delete(0, tk.END)
    path_entry.insert(0, directory)

# Create the main window
root = tk.Tk()
root.title("Disk Usage Analyzer")

# Directory selection
frame = ttk.Frame(root, padding="10")
frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

path_label = ttk.Label(frame, text="Directory Path:")
path_label.grid(row=0, column=0, padx=5, pady=5)

path_entry = ttk.Entry(frame, width=50)
path_entry.grid(row=0, column=1, padx=5, pady=5)

browse_button = ttk.Button(frame, text="Browse", command=browse_directory)
browse_button.grid(row=0, column=2, padx=5, pady=5)

analyze_button = ttk.Button(frame, text="Analyze", command=analyze_directory)
analyze_button.grid(row=0, column=3, padx=5, pady=5)

# Sorting options
sort_var = tk.StringVar(value="Name")
sort_label = ttk.Label(frame, text="Sort By:")
sort_label.grid(row=1, column=0, padx=5, pady=5)

name_radio = ttk.Radiobutton(frame, text="Name", variable=sort_var, value="Name")
name_radio.grid(row=1, column=1, padx=5, pady=5)

size_radio = ttk.Radiobutton(frame, text="Size", variable=sort_var, value="Size")
size_radio.grid(row=1, column=2, padx=5, pady=5)

# Results Display
tree_view_label = ttk.Label(frame, text="Disk Usage Tree View:")
tree_view_label.grid(row=2, column=0, columnspan=4, padx=5, pady=5)

tree_view_text = tk.Text(frame, width=80, height=15)
tree_view_text.grid(row=3, column=0, columnspan=4, padx=5, pady=5)

ext_usage_label = ttk.Label(frame, text="File Extension Usage:")
ext_usage_label.grid(row=4, column=0, columnspan=4, padx=5, pady=5)

ext_usage_text = tk.Text(frame, width=80, height=10)
ext_usage_text.grid(row=5, column=0, columnspan=4, padx=5, pady=5)

root.mainloop()
