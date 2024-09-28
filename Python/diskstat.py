# Disk Usage Statistics Ver. 1 (Python)
# Developed by Matthew David G. Montero -- BSCS 4A
# For the subject "CCS238 - Programming Languages"

# To use the program, just enter the directory of your choice. 
# It will then analyze the disk usage of the entered directory
# and will print the following to a text file:
    # 1. basic information of the drive
    # 2. directory's disk usage (along with its percentage) in a directory-tree-like view.
    # 3. the disk usage of file extensions found within the directory.

import os
import shutil
import sys
import time
import threading
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
        # Iterate through the directory
        for root, dirs, files in os.walk(path):
            for name in files:
                try:
                    filepath = os.path.join(root, name)
                    size = os.path.getsize(filepath)
                    total_size += size

                    # Get file extension and accumulate its size
                    ext = os.path.splitext(name)[1]
                    ext_usage[ext] += size
                
                except FileNotFoundError as fnf_error:
                    error_logs['FileNotFoundError'].append(filepath)
                except PermissionError as perm_error:
                    error_logs['PermissionError'].append(filepath)
                except OSError as os_error:
                    error_logs['OSError'].append(filepath)

    except OSError as os_error:
        error_logs['OSError'].append(path)
    
    return total_size, ext_usage

# Function to display the disk usage tree
def print_tree_view(path, depth, total_size, log_file, error_logs):
    dir_size, _ = get_disk_usage(path, log_file, error_logs)
    percentage = (dir_size / total_size * 100) if total_size else 0
    log_file.write(f"{'  ' * depth}{os.path.basename(path)}/ - {format_size(dir_size)} ({percentage:.2f}%)\n")
    
    try:
        # Recursively go into subdirectories
        for entry in os.scandir(path):
            if entry.is_dir(follow_symlinks=False):
                print_tree_view(entry.path, depth + 1, total_size, log_file, error_logs)
    
    except PermissionError as perm_error:
        error_logs['PermissionError'].append(path)
    except OSError as os_error:
        error_logs['OSError'].append(path)

# Function to display sorted file extension usage
def print_sorted_extensions(ext_usage, log_file):
    sorted_ext_usage = sorted(ext_usage.items(), key=lambda x: x[1], reverse=True)
    
    log_file.write("\nFile Extension Usage (sorted by usage):\n")
    for ext, size in sorted_ext_usage:
        log_file.write(f"{ext}: {format_size(size)}\n")

# Function to display disk space information
def print_disk_info(path, log_file):
    try:
        total, used, free = shutil.disk_usage(path)
        log_file.write(f"\nDisk Usage Information for '{path}':\n")
        log_file.write(f"Total space: {format_size(total)}\n")
        log_file.write(f"Used space:  {format_size(used)}\n")
        log_file.write(f"Free space:  {format_size(free)}\n\n")
    
    except OSError as os_error:
        log_file.write(f"OSError while retrieving disk info: {os_error}\n")

# Function to log errors at the end of the report
def log_errors(log_file, error_logs):
    if any(error_logs.values()):
        log_file.write("\n\nError Summary:\n")
        
        if error_logs['FileNotFoundError']:
            log_file.write("\nMissing files (FileNotFoundError):\n")
            for path in error_logs['FileNotFoundError']:
                log_file.write(f"'{path}'\n")
        
        if error_logs['PermissionError']:
            log_file.write("\nFiles with restricted access (PermissionError):\n")
            for path in error_logs['PermissionError']:
                log_file.write(f"'{path}'\n")
        
        if error_logs['OSError']:
            log_file.write("\nLocked files / Files with path issues (OSError):\n")
            for path in error_logs['OSError']:
                log_file.write(f"'{path}'\n")

# Function to display the loading animation and timer
def loading_animation_with_timer(start_time, lock):
    animation = ['|', '/', '-', '\\']
    idx = 0
    
    while loading:
        with lock:
            elapsed_time = time.time() - start_time
            minutes, seconds = divmod(elapsed_time, 60)
            
            if minutes > 0:
                time_display = f"{int(minutes)} min {int(seconds):02d} sec"
            else:
                time_display = f"{int(seconds)} seconds"

            sys.stdout.write(f'\r{animation[idx]} Analyzing... Time Elapsed: {time_display}')
            sys.stdout.flush()
            idx = (idx + 1) % len(animation)
        time.sleep(0.1)

def clear_screen():
    if os.name == 'nt':  # 'nt' is for Windows
        os.system('cls')
    else:  # For Linux and macOS
        os.system('clear')

# Main program
def main():
    global loading
    
    while True:
        clear_screen()
        os.chdir(os.path.dirname(os.path.abspath(__file__)))

        print("=== Disk Usage Statistics ===")
        print("Note: If you wish to enter a root directory, enter the drive letter with a colon and a slash.")
        print("\nExample: 'C:\\'")
        
        path = os.path.abspath(input("\n\nEnter the directory path to analyze: ").strip())
        
        start_time = time.time()
        
        # Check if the input is a valid directory
        if os.path.isdir(path):
            logs = 'Disk Usage Logs'
            os.makedirs(logs, exist_ok=True)

            if os.path.splitdrive(path)[1] == os.sep:
                drive_label = os.path.splitdrive(path)[0].replace(':', '') 
                filename = os.path.join(logs, f"{drive_label} -- Disk Usage Log.txt")
            else:
                filename = os.path.join(logs, f"{os.path.basename(path)} -- Disk Usage Log.txt")

            error_logs = {
                'FileNotFoundError': [],
                'PermissionError': [],
                'OSError': []
            }

            loading = True
            
            # a thread lock is used to avoid two functions updating to the console at the same time
            lock = threading.Lock()
            animation_thread = threading.Thread(target=loading_animation_with_timer, args=(start_time, lock))
            animation_thread.start()
            
            with open(filename, 'w', encoding='utf-8') as log_file:
                print_disk_info(path, log_file)

                while True:
                    total_size, ext_usage = get_disk_usage(path, log_file, error_logs)
                    
                    if total_size > 0:
                        break
                
                log_file.write("\nDisk Usage Tree View:\n")
                print_tree_view(path, 0, total_size, log_file, error_logs)
                print_sorted_extensions(ext_usage, log_file)
                log_errors(log_file, error_logs)

            loading = False
            animation_thread.join()
            end_time = time.time()
            
            elapsed_time = end_time - start_time
            minutes, seconds = divmod(elapsed_time, 60)
            time_display = f"{int(minutes)} min {int(seconds):02d} sec" if minutes > 0 else f"{int(seconds):02d} seconds"
            
            print(f"\n\nAnalysis complete! The output has been saved as: '{filename}'.\nSave Directory: '{os.getcwd()}\\Disk Usage Logs'")
            print(f"\n\nTime elapsed: '{time_display}'.")
            
        else:
            print(f"\nError: '{path}' is not a valid directory. \nPlease enter a valid directory path.")

            
        while True:
            restart = input("\nDo you want to analyze another directory? (Y/n): ").strip().lower()
            if restart == 'y':
                break  # Restart the loop from the beginning
            elif restart == 'n':
                print("\n\nSession Terminated... Goodbye.")
                os.system("pause")
                return  # Exit the program
            else:
                print("\n\nInvalid input. Please enter 'Y' to continue or 'n' to quit.")


if __name__ == "__main__":
    main()
