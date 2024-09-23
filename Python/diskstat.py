import os
import shutil
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
def get_disk_usage(path, log_file):
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
                    log_file.write(f"FileNotFoundError: {fnf_error}\n")
                except PermissionError as perm_error:
                    log_file.write(f"PermissionError: {perm_error}\n")
                except OSError as os_error:
                    log_file.write(f"OSError: {os_error}\n")

    except OSError as os_error:
        log_file.write(f"OSError while accessing directory: {os_error}\n")
    
    return total_size, ext_usage

# Function to display the disk usage tree
def print_tree_view(path, depth, total_size, log_file):
    dir_size, _ = get_disk_usage(path, log_file)
    percentage = (dir_size / total_size * 100) if total_size else 0
    log_file.write(f"{'  ' * depth}{os.path.basename(path)}/ - {format_size(dir_size)} ({percentage:.2f}%)\n")
    
    try:
        # Recursively go into subdirectories
        for entry in os.scandir(path):
            if entry.is_dir(follow_symlinks=False):
                print_tree_view(entry.path, depth + 1, total_size, log_file)
    
    except PermissionError as perm_error:
        log_file.write(f"{'  ' * (depth + 1)}PermissionError: {perm_error}\n")
    except OSError as os_error:
        log_file.write(f"{'  ' * (depth + 1)}OSError: {os_error}\n")

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

# Main program
def main():
    while True:
        path = input("Enter the directory path to analyze: ").strip()
        
        # Open the log file for writing the output
        with open('disk_usage_log.txt', 'w') as log_file:
            
            # Print disk space info
            print_disk_info(path, log_file)

            # Calculate total disk usage for the directory
            total_size, ext_usage = get_disk_usage(path, log_file)
            
            # Print tree view of disk usage
            log_file.write("\nDisk Usage Tree View:\n")
            print_tree_view(path, 0, total_size, log_file)

            # Print sorted extensions by usage
            print_sorted_extensions(ext_usage, log_file)

        print("The output has been saved to 'disk_usage_log.txt'.")

        # Ask if the user wants to analyze another directory
        restart = input("\nDo you want to analyze another directory? (y/n): ").strip().lower()
        if restart != 'y':
            break

    print("Exiting the program.")

if __name__ == "__main__":
    main()
