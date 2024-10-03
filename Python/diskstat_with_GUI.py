import os
import threading
import shutil
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, Toplevel, Listbox
from collections import defaultdict
from queue import Queue


# Function to convert sizes to human-readable format
def format_size(size):
    units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    unit_index = 0
    converted_size = float(size)

    while converted_size >= 1024 and unit_index < len(units) - 1:
        converted_size /= 1024
        unit_index += 1

    return f'{converted_size:.2f} {units[unit_index]}'

# Function to parse human-readable size back into bytes (for sorting purposes)
def parse_size(size_str):
    size_str = size_str.replace(",", "")  # Remove commas if present
    units = {'B': 1, 'KB': 1024, 'MB': 1024**2, 'GB': 1024**3, 'TB': 1024**4, 'PB': 1024**5}
    size, unit = size_str.split()
    return float(size) * units[unit]

# Function to calculate disk usage for a directory
def calculate_usage(path, error_logs, result_queue):
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
        # Return the total size and extension usage
        return total_size, ext_usage
    except PermissionError as e:
        error_logs.append(f"Permission denied: {str(e)}")
        return total_size, ext_usage  # Return even on error

class DiskUsageApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Disk Usage Statistics")
        self.geometry("900x600")
        self.error_logs = []
        self.analysis_running = False  # Add flag to track if the analysis is running
        self.sort_by = tk.StringVar(value="name")  # Track sorting option
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

        # Exit program button
        self.exit_btn = ttk.Button(button_frame, text="Exit Program", command=self.quit)
        self.exit_btn.pack(side=tk.RIGHT)

        # Sorting radio buttons
        self.sort_name_radio = ttk.Radiobutton(button_frame, text="Sort by Name", variable=self.sort_by, value="name", command=self.sort_tree)
        self.sort_name_radio.pack(side=tk.LEFT)

        self.sort_size_radio = ttk.Radiobutton(button_frame, text="Sort by Size", variable=self.sort_by, value="size", command=self.sort_tree)
        self.sort_size_radio.pack(side=tk.LEFT)
        
        # Add a dropdown for sorting order (ascending/descending)
        self.sort_order = tk.StringVar(value="ascending")  # Default to ascending order
        self.sort_order_dropdown = ttk.Combobox(button_frame, textvariable=self.sort_order, values=["ascending", "descending"], state="readonly")
        self.sort_order_dropdown.pack(side=tk.LEFT, padx=5)

        # Bind the sorting order dropdown value change to trigger sorting
        self.sort_order_dropdown.bind("<<ComboboxSelected>>", lambda event: self.sort_tree())


        # Tree view frame
        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Treeview widget for displaying directory structure and sizes
        self.tree = ttk.Treeview(tree_frame, columns=("size", "percent"), show="tree")
        self.tree.heading("size", text="Size", command=lambda: self.sort_tree())
        self.tree.heading("percent", text="Percentage", command=lambda: self.sort_tree())
        self.tree.heading("#0", text="Name", command=lambda: self.sort_tree())
        self.tree.column("size", width=150)
        self.tree.column("percent", width=100)
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Timer display
        self.timer_label = ttk.Label(self, text="Time Elapsed: 00:00")
        self.timer_label.pack(pady=5)

        # Progress bar to show the analysis progress (hidden initially)
        self.progress = ttk.Progressbar(self, orient="horizontal", mode="indeterminate")
        self.progress.pack(fill=tk.X, padx=10, pady=5)
        self.progress.pack_forget()  # Hide progress bar initially

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
        self.error_log_btn.config(state=tk.DISABLED)  # Disable error log button
        self.analysis_running = True  # Set the flag when analysis starts
        self.progress.pack()  # Show the progress bar during analysis
        self.progress.start()

        self.start_time = time.time()
        self.update_timer()

        # Create a queue for results
        self.result_queue = Queue()
        self.analysis_thread = threading.Thread(target=self.analyze_directory, args=(path,))
        self.analysis_thread.start()
        self.after(100, self.check_analysis)

    def update_timer(self):
        if self.analysis_running:  # Only update timer if analysis is running
            elapsed_time = int(time.time() - self.start_time)
            minutes, seconds = divmod(elapsed_time, 60)
            self.timer_label.config(text=f"Time Elapsed: {minutes:02}:{seconds:02}")
            self.after(1000, self.update_timer)

    def analyze_directory(self, path):
        # Calculate usage of the selected directory and populate the tree
        total_size, ext_usage = calculate_usage(path, self.error_logs, self.result_queue)

        if self.error_logs:
            self.error_log_btn.config(state=tk.NORMAL)  # Enable error log button if there are errors

        self.tree.insert('', 'end', text=path, values=(format_size(total_size), "100%"))
        self.populate_tree(path, total_size)
        self.populate_extensions(ext_usage)

        self.analysis_running = False  # Stop the timer when analysis completes

    def check_analysis(self):
        if self.analysis_thread.is_alive():
            self.after(100, self.check_analysis)
        else:
            self.progress.stop()
            self.progress.pack_forget()  # Hide the progress bar after analysis completes
            self.analysis_running = False  # Stop the timer when analysis completes

    def populate_tree(self, path, total_size):
        def recursive_insert(parent, path, total_size):
            try:
                dir_size, ext_usage = calculate_usage(path, self.error_logs, self.result_queue)
                percentage = (dir_size / total_size * 100) if total_size else 0
                # Insert the full path as a value in the TreeView
                node_id = self.tree.insert(parent, 'end', text=os.path.basename(path), values=(format_size(dir_size), f"{percentage:.2f}%", path))
                
                # Iterate over directory entries
                for entry in os.scandir(path):
                    if entry.is_dir(follow_symlinks=False):
                        # Recursively insert directories
                        recursive_insert(node_id, entry.path, total_size)
                    elif entry.is_file(follow_symlinks=False):
                        # Insert files into the tree with the full path
                        try:
                            file_size = os.path.getsize(entry.path)
                            file_percentage = (file_size / total_size * 100) if total_size else 0
                            self.tree.insert(node_id, 'end', text=entry.name, values=(format_size(file_size), f"{file_percentage:.2f}%", entry.path))
                        except Exception as e:
                            self.error_logs.append(f"Error processing file '{entry.path}': {str(e)}")
            except PermissionError as e:
                self.error_logs.append(f"Permission denied: {str(e)}")

        # Start recursive insertion from the selected path
        recursive_insert('', path, total_size)


    def populate_extensions(self, ext_usage):
        sorted_ext_usage = sorted(ext_usage.items(), key=lambda x: x[1], reverse=True)
        for ext, size in sorted_ext_usage:
            self.extension_list.insert(tk.END, f"{ext}: {format_size(size)}")

    def sort_tree(self):
        sort_by = self.sort_by.get()
        sort_order = self.sort_order.get()  # Get the selected sort order (ascending/descending)

        # Sort the tree recursively
        def recursive_sort(node):
            children = self.tree.get_children(node)

            if sort_by == "name":
                sorted_children = sorted(children, key=lambda child: self.tree.item(child, "text").lower(), reverse=(sort_order == "descending"))
            elif sort_by == "size":
                sorted_children = sorted(children, key=lambda child: parse_size(self.tree.set(child, "size")), reverse=(sort_order == "descending"))

            # Rearrange items in sorted order
            for index, child in enumerate(sorted_children):
                self.tree.move(child, node, index)
                recursive_sort(child)  # Sort the children of each node recursively

        # Get the root node (header) and only sort its children
        root = self.tree.get_children('')
        if root:
            for child in root:
                recursive_sort(child)


    def delete_directory(self):
        selected_item = self.tree.selection()
        if selected_item:
            # Get the full path from the Treeview values (third value is the full path)
            node_id = selected_item[0]
            item_values = self.tree.item(node_id, 'values')
            full_path = item_values[2]  # The full path is stored as the third value

            # Safeguard: Ensure full path for file/folder exists
            if not os.path.exists(full_path):
                messagebox.showerror("Error", f"File or directory '{full_path}' not found.")
                return

            # Safeguard: Don't allow deletion of critical system directories
            system_dirs = ['C:\\Windows', 'C:\\System32']
            if any(full_path.startswith(sys_dir) for sys_dir in system_dirs):
                messagebox.showerror("Error", "Deletion of system files is not allowed.")
                return

            # Confirmation dialog
            confirm = messagebox.askyesno("Delete Directory", f"Are you sure you want to delete {full_path}?")
            if confirm:
                try:
                    # Delete the directory or file
                    if os.path.isdir(full_path):
                        shutil.rmtree(full_path)
                    else:
                        os.remove(full_path)
                    self.tree.delete(selected_item)
                    messagebox.showinfo("Success", f"{full_path} deleted successfully.")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to delete {full_path}: {str(e)}")


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
