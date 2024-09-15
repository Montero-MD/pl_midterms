import os
import shutil
from collections import defaultdict

def format_size(size):
    """Convert bytes into the largest appropriate unit."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB', 'PB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} PB"

def get_disk_usage(path):
    """Recursively calculate disk usage for each directory and file."""
    total_size = 0
    ext_usage = defaultdict(int)

    try:
        for entry in os.scandir(path):
            if entry.is_dir(follow_symlinks=False):
                # Recursively get size for directories
                sub_size, sub_ext_usage = get_disk_usage(entry.path)
                total_size += sub_size
                for ext, size in sub_ext_usage.items():
                    ext_usage[ext] += size
            else:
                # Get size for files
                size = entry.stat().st_size
                total_size += size

                # Get file extension
                _, ext = os.path.splitext(entry.name)
                ext_usage[ext] += size
    except PermissionError:
        print(f"Permission Denied: {path}")

    return total_size, ext_usage

def print_tree_view(path, depth=0, total_space=0):
    """Print the directory tree view with percentage usage."""
    size, _ = get_disk_usage(path)
    percentage = (size / total_space) * 100 if total_space else 0
    print(f"{'  ' * depth}{os.path.basename(path)}/ - {format_size(size)} ({percentage:.2f}%)")

    try:
        for entry in os.scandir(path):
            if entry.is_dir(follow_symlinks=False):
                print_tree_view(entry.path, depth + 1, total_space)
    except PermissionError:
        print(f"{'  ' * (depth + 1)}Permission Denied: {path}")

def print_sorted_extensions(ext_usage):
    """Print a sorted list of file extensions by total usage."""
    sorted_ext = sorted(ext_usage.items(), key=lambda x: x[1], reverse=True)
    print("\nFile Extension Usage:")
    for ext, size in sorted_ext:
        print(f"{ext}: {format_size(size)}")

def print_disk_info(path):
    """Print the total, used, and free space of the disk where the path resides."""
    total, used, free = shutil.disk_usage(path)
    print(f"\nDisk Overview:")
    print(f"Total space: {format_size(total)}")
    print(f"Used space:  {format_size(used)}")
    print(f"Free space:  {format_size(free)}\n")

def main():
    path = input("Enter the directory path to analyze: ")

    # Print disk space info for the path
    print_disk_info(path)

    total_size, ext_usage = get_disk_usage(path)

    print("\nDisk Usage Tree View:")
    print_tree_view(path, total_space=total_size)

    print_sorted_extensions(ext_usage)

if __name__ == "__main__":
    main()
