import os
import threading
import shutil
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, Toplevel, Listbox
from collections import defaultdict

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
def get_disk_usage(path, log_file, error_logs):
    total_size = 0
    ext_usage = defaultdict(int)

    try:
        for root, dirs, files in os.walk(path, onerror=lambda e: error_logs.append(f"Error accessing directory '{path}': {str(e)}")):
            for name in files:
                filepath = os.path.join(root, name)
                try:
                    size = os.path.getsize(filepath)
                    total_size += size
                    ext = os.path.splitext(name)[1]
                    ext_usage[ext] += size
                except Exception as e:
                    error_logs.append(f"Error processing file '{filepath}': {str(e)}")

    except PermissionError as e:
        error_logs.append(f"Permission denied: {str(e)}")

    return total_size, ext_usage

class DiskUsageApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Disk Usage Analyzer")
        self.geometry("900x600")
        self.error_logs = []
        self.analysis_running = False  # Add flag to track if the analysis is running
        self.create_widgets()

    def create_widgets(self):
        # Frame for the buttons
        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        # Directory selection button
        self.select_dir_btn = ttk.Button(button_frame, text="Select Directory", command=self.select_directory)
        self.select_dir_btn.pack(side=tk.LEFT)

        # Delete directory button
        self.delete_btn = ttk.Button(button_frame, text="Delete Selected Directory", command=self.delete_directory)
        self.delete_btn.pack(side=tk.LEFT)

        # Error log button
        self.error_log_btn = ttk.Button(button_frame, text="View Error Logs", command=self.show_error_logs)
        self.error_log_btn.pack(side=tk.LEFT)

        # Tree view frame
        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Treeview widget for displaying directory structure and sizes
        self.tree = ttk.Treeview(tree_frame, columns=("size", "percent"), show="tree")
        self.tree.heading("size", text="Size", command=lambda: self.sort_tree("size"))
        self.tree.heading("percent", text="Percentage", command=lambda: self.sort_tree("percent"))
        self.tree.heading("#0", text="Name", command=lambda: self.sort_tree("name"))
        self.tree.column("size", width=150)
        self.tree.column("percent", width=100)
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Timer display
        self.timer_label = ttk.Label(self, text="Time Elapsed: 00:00")
        self.timer_label.pack(pady=5)

        # Progress bar to show the analysis progress
        self.progress = ttk.Progressbar(self, orient="horizontal", mode="indeterminate")
        self.progress.pack(fill=tk.X, padx=10, pady=5)

        # Frame for the file extension usage
        ext_frame = ttk.Frame(self)
        ext_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(ext_frame, text="File Extension Usage").pack()
        self.extension_list = tk.Listbox(ext_frame, height=8)
        self.extension_list.pack(fill=tk.X)

    def select_directory(self):
        path = filedialog.askdirectory()
        if path:
            self.start_analysis(path)

    def start_analysis(self, path):
        self.clear_tree()
        self.error_logs.clear()
        self.analysis_running = True  # Set the flag when analysis starts
        self.progress.start()

        self.start_time = time.time()
        self.update_timer()

        self.analysis_thread = threading.Thread(target=self.analyze_directory, args=(path,))
        self.analysis_thread.start()

    def update_timer(self):
        if self.analysis_running:  # Only update timer if analysis is running
            elapsed_time = int(time.time() - self.start_time)
            minutes, seconds = divmod(elapsed_time, 60)
            self.timer_label.config(text=f"Time Elapsed: {minutes:02}:{seconds:02}")
            self.after(1000, self.update_timer)

    def analyze_directory(self, path):
        total_size, ext_usage = get_disk_usage(path, None, self.error_logs)

        self.tree.insert('', 'end', text=path, values=(format_size(total_size), "100%"))
        self.populate_tree(path, total_size)
        self.populate_extensions(ext_usage)

        self.progress.stop()
        self.analysis_running = False  # Stop the timer when analysis completes

    def populate_tree(self, path, total_size):
        def recursive_insert(parent, path, total_size):
            try:
                dir_size, _ = get_disk_usage(path, None, self.error_logs)
                percentage = (dir_size / total_size * 100) if total_size else 0
                node_id = self.tree.insert(parent, 'end', text=os.path.basename(path), values=(format_size(dir_size), f"{percentage:.2f}%"))
                for entry in os.scandir(path):
                    if entry.is_dir(follow_symlinks=False):
                        recursive_insert(node_id, entry.path, total_size)
            except PermissionError as e:
                self.error_logs.append(f"Permission denied: {str(e)}")

        recursive_insert('', path, total_size)

    def populate_extensions(self, ext_usage):
        sorted_ext_usage = sorted(ext_usage.items(), key=lambda x: x[1], reverse=True)
        for ext, size in sorted_ext_usage:
            self.extension_list.insert(tk.END, f"{ext}: {format_size(size)}")

    def sort_tree(self, sort_by):
        items = [(self.tree.set(k, sort_by), k) for k in self.tree.get_children("")]
        if sort_by == "size":
            items.sort(key=lambda x: float(x[0].replace(" GB", "")), reverse=True)
        else:
            items.sort()
        for index, (val, k) in enumerate(items):
            self.tree.move(k, "", index)

    def delete_directory(self):
        selected_item = self.tree.selection()
        if selected_item:
            dir_name = self.tree.item(selected_item)["text"]
            confirm = messagebox.askyesno("Delete Directory", f"Are you sure you want to delete {dir_name}?")
            if confirm:
                shutil.rmtree(dir_name)
                self.tree.delete(selected_item)
                messagebox.showinfo("Success", f"{dir_name} deleted successfully.")

    def show_error_logs(self):
        error_window = Toplevel(self)
        error_window.title("Error Logs")
        error_window.geometry("500x400")

        error_listbox = Listbox(error_window)
        error_listbox.pack(fill=tk.BOTH, expand=True)

        for error in self.error_logs:
            error_listbox.insert(tk.END, error)

    def clear_tree(self):
        self.tree.delete(*self.tree.get_children())
        self.extension_list.delete(0, tk.END)

if __name__ == "__main__":
    app = DiskUsageApp()
    app.mainloop()
