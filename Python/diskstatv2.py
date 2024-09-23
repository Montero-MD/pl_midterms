import os
import shutil
from collections import defaultdict
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import threading

# Function to convert sizes to human-readable format
def format_size(size):
    units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    unit_index = 0
    converted_size = float(size)
    
    while converted_size >= 1024 and unit_index < len(units) - 1:
        converted_size /= 1024
        unit_index += 1
    
    return f'{converted_size:.2f} {units[unit_index]}'

# Function to recursively calculate disk usage
def get_disk_usage(path, progress_callback=None):
    total_size = 0
    ext_usage = defaultdict(int)
    num_files = sum([len(files) for r, d, files in os.walk(path)])  # Count total files
    file_count = 0

    try:
        # Recursively walk through the directory
        for root, dirs, files in os.walk(path):
            for name in files:
                file_count += 1
                try:
                    filepath = os.path.join(root, name)
                    size = os.path.getsize(filepath)  # Get file size
                    total_size += size

                    # Get file extension and accumulate its size
                    ext = os.path.splitext(name)[1]
                    ext_usage[ext] += size

                    # Update progress bar
                    if progress_callback:
                        progress_callback(file_count / num_files * 100)
                
                except (FileNotFoundError, PermissionError, OSError) as e:
                    # Log the error but continue the analysis
                    print(f"Warning: Skipping file {filepath} due to error: {e}")
    
    except OSError as os_error:
        print(f"OSError while accessing directory: {os_error}")
    
    return total_size, ext_usage


# GUI class for disk usage analyzer
class DiskUsageApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Disk Usage Analyzer")
        self.root.geometry("800x600")

        # Setup the toolbar
        self.toolbar = tk.Frame(self.root)
        self.toolbar.pack(side=tk.TOP, fill=tk.X)

        self.analyze_button = tk.Button(self.toolbar, text="Analyze New Directory", command=self.analyze_directory)
        self.analyze_button.pack(side=tk.LEFT, padx=2, pady=2)

        self.delete_button = tk.Button(self.toolbar, text="Delete Files", command=self.delete_selected_files)
        self.delete_button.pack(side=tk.LEFT, padx=2, pady=2)

        # Setup the treeview for directory structure
        self.tree = ttk.Treeview(self.root)
        self.tree.pack(fill=tk.BOTH, expand=True)

        self.tree['columns'] = ("size", "percentage")
        self.tree.column("#0", width=400, minwidth=400)
        self.tree.column("size", width=100, minwidth=100, anchor=tk.E)
        self.tree.column("percentage", width=100, minwidth=100, anchor=tk.E)

        self.tree.heading("#0", text="Directory/File", anchor=tk.W)
        self.tree.heading("size", text="Size", anchor=tk.W)
        self.tree.heading("percentage", text="Percentage", anchor=tk.W)

        # Setup the progress bar
        self.progress = ttk.Progressbar(self.root, orient="horizontal", length=100, mode="determinate")
        self.progress.pack(side=tk.BOTTOM, fill=tk.X)

    def update_progress(self, value):
        self.progress["value"] = value
        self.root.update_idletasks()

    def analyze_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.tree.delete(*self.tree.get_children())  # Clear treeview
            self.progress["value"] = 0

            # Run disk analysis in a separate thread to avoid blocking the GUI
            threading.Thread(target=self.start_analysis, args=(directory,)).start()

    def start_analysis(self, path):
        total_size, ext_usage = get_disk_usage(path, self.update_progress)
        self.insert_tree_view(path, 0, total_size)
    
    def insert_tree_view(self, path, parent, total_size):
        dir_size, _ = get_disk_usage(path)
        percentage = (dir_size / total_size * 100) if total_size else 0
        node = self.tree.insert(parent, 'end', text=os.path.basename(path), values=(format_size(dir_size), f"{percentage:.2f}%"))

        try:
            for entry in os.scandir(path):
                if entry.is_dir(follow_symlinks=False):
                    self.insert_tree_view(entry.path, node, total_size)
        except PermissionError as perm_error:
            print(f"PermissionError: {perm_error}")
        except OSError as os_error:
            print(f"OSError: {os_error}")

    def delete_selected_files(self):
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showinfo("Delete Files", "No files or directories selected.")
            return

        # Confirm before deleting
        confirm = messagebox.askyesno("Delete Files", "Are you sure you want to delete the selected files?")
        if confirm:
            for item in selected_items:
                file_path = self.tree.item(item, "text")
                try:
                    if os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                    else:
                        os.remove(file_path)
                    self.tree.delete(item)
                except Exception as e:
                    messagebox.showerror("Error", f"Error deleting {file_path}: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = DiskUsageApp(root)
    root.mainloop()
