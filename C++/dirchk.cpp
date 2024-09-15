#include <iostream>
#include <filesystem>
#include <map>
#include <unordered_map>
#include <iomanip> // for setprecision

namespace fs = std::filesystem;

std::string format_size(uintmax_t size) {
    const char* units[] = {"B", "KB", "MB", "GB", "TB", "PB"};
    int unit_index = 0;
    double converted_size = size;

    while (converted_size >= 1024 && unit_index < 5) {
        converted_size /= 1024;
        ++unit_index;
    }
    
    std::ostringstream out;
    out << std::fixed << std::setprecision(2) << converted_size << " " << units[unit_index];
    return out.str();
}

struct DiskUsage {
    uintmax_t size = 0;
    std::unordered_map<std::string, uintmax_t> ext_usage;
};

DiskUsage get_disk_usage(const fs::path& path) {
    DiskUsage du;
    try {
        for (const auto& entry : fs::directory_iterator(path)) {
            if (entry.is_directory()) {
                // Recursively calculate directory size
                DiskUsage sub_dir_usage = get_disk_usage(entry.path());
                du.size += sub_dir_usage.size;
                for (const auto& [ext, size] : sub_dir_usage.ext_usage) {
                    du.ext_usage[ext] += size;
                }
            } else if (entry.is_regular_file()) {
                // Calculate file size
                uintmax_t size = entry.file_size();
                du.size += size;
                
                // Get file extension
                std::string ext = entry.path().extension().string();
                du.ext_usage[ext] += size;
            }
        }
    } catch (const fs::filesystem_error& e) {
        std::cerr << "Error accessing: " << path << " (" << e.what() << ")\n";
    }
    return du;
}

void print_tree_view(const fs::path& path, int depth, uintmax_t total_size) {
    DiskUsage du = get_disk_usage(path);
    double percentage = total_size ? (static_cast<double>(du.size) / total_size * 100) : 0;
    std::cout << std::string(depth * 2, ' ') << path.filename().string() << "/ - " 
              << format_size(du.size) << " (" << std::fixed << std::setprecision(2) << percentage << "%)\n";
    
    try {
        for (const auto& entry : fs::directory_iterator(path)) {
            if (entry.is_directory()) {
                print_tree_view(entry.path(), depth + 1, total_size);
            }
        }
    } catch (const fs::filesystem_error& e) {
        std::cerr << std::string((depth + 1) * 2, ' ') << "Error accessing: " << path << " (" << e.what() << ")\n";
    }
}

void print_sorted_extensions(const std::unordered_map<std::string, uintmax_t>& ext_usage) {
    std::map<uintmax_t, std::string, std::greater<>> sorted_ext;
    for (const auto& [ext, size] : ext_usage) {
        sorted_ext.insert({size, ext});
    }

    std::cout << "\nFile Extension Usage:\n";
    for (const auto& [size, ext] : sorted_ext) {
        std::cout << ext << ": " << format_size(size) << '\n';
    }
}

void print_disk_info(const fs::path& path) {
    try {
        auto space_info = fs::space(path);
        std::cout << "\nDisk Usage Information for '" << path << "':\n";
        std::cout << "Total space: " << format_size(space_info.capacity) << "\n";
        std::cout << "Used space:  " << format_size(space_info.capacity - space_info.free) << "\n";
        std::cout << "Free space:  " << format_size(space_info.free) << "\n\n";
    } catch (const fs::filesystem_error& e) {
        std::cerr << "Error retrieving disk information for: " << path << " (" << e.what() << ")\n";
    }
}

int main() {
    std::string path_str;
    std::cout << "Enter the directory path to analyze: ";
    std::getline(std::cin, path_str);
    fs::path path(path_str);

    // Print disk space info for the path
    print_disk_info(path);

    DiskUsage du = get_disk_usage(path);

    std::cout << "\nDisk Usage Tree View:\n";
    print_tree_view(path, 0, du.size);

    print_sorted_extensions(du.ext_usage);
    return 0;
}
