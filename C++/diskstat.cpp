// Disk Usage Statistics Ver. 1 (C++)
// Developed by Matthew David G. Montero -- BSCS 4A
// For the subject "CCS238 - Programming Languages"

// To use the program, just enter the directory of your choice. 
// It will then analyze the disk usage of the entered directory
// and will display the following:
    // 1. basic information of the drive
    // 2. directory's disk usage (along with its percentage) in a directory-tree-like view.
    // 3. the disk usage of file extensions found within the directory.

#include <iostream> // for reading input and writing output
#include <filesystem> // for accessing directories and files
#include <unordered_map> // for storing key-value pairs
#include <map> // for sorting and displaying key-value pairs in order
#include <iomanip> // for setting the precision of floats

using namespace std;
namespace fs = filesystem;

string format_size(uintmax_t size)
{
    const char *units[] = {"B", "KB", "MB", "GB", "TB", "PB"};
    int unit_index = 0;
    double converted_size = size;

    while (converted_size >= 1024 && unit_index < 5)
    {
        converted_size /= 1024;
        ++unit_index;
    }

    ostringstream out;
    out << fixed << setprecision(2) << converted_size << " " << units[unit_index];
    return out.str();
}

struct DiskUsage
{
    uintmax_t size = 0;
    unordered_map<string, uintmax_t> ext_usage;
};

DiskUsage get_disk_usage(const fs::path &path)
{
    DiskUsage du;
    try
    {
        for (const auto &entry : fs::directory_iterator(path))
        {
            if (entry.is_directory())
            {
                // Recursively calculate directory size
                DiskUsage sub_dir_usage = get_disk_usage(entry.path());
                du.size += sub_dir_usage.size;
                for (const auto &[ext, size] : sub_dir_usage.ext_usage)
                {
                    du.ext_usage[ext] += size;
                }
            }
            else if (entry.is_regular_file())
            {
                // Calculate file size
                uintmax_t size = entry.file_size();
                du.size += size;

                // Get file extension
                string ext = entry.path().extension().string();
                du.ext_usage[ext] += size;
            }
        }
    }
    catch (const fs::filesystem_error &e)
    {
        cerr << "Error accessing: " << path << " (" << e.what() << ")\n";
    }
    return du;
}

void print_tree_view(const fs::path &path, int depth, uintmax_t total_size)
{
    DiskUsage du = get_disk_usage(path);
    double percentage = total_size ? (static_cast<double>(du.size) / total_size * 100) : 0;
    cout << string(depth * 2, ' ') << path.filename().string() << "/ - "
         << format_size(du.size) << " (" << fixed << setprecision(2) << percentage << "%)\n";

    try
    {
        for (const auto &entry : fs::directory_iterator(path))
        {
            if (entry.is_directory())
            {
                print_tree_view(entry.path(), depth + 1, total_size);
            }
        }
    }
    catch (const fs::filesystem_error &e)
    {
        cerr << string((depth + 1) * 2, ' ') << "Error accessing: " << path << " (" << e.what() << ")\n";
    }
}

void print_sorted_extensions(const unordered_map<string, uintmax_t> &ext_usage)
{
    map<uintmax_t, string, greater<>> sorted_ext;
    for (const auto &[ext, size] : ext_usage)
    {
        sorted_ext.insert({size, ext});
    }

    cout << "\nFile Extension Usage:\n";
    for (const auto &[size, ext] : sorted_ext)
    {
        cout << ext << ": " << format_size(size) << '\n';
    }
}

void print_disk_info(const fs::path &path)
{
    // Find root directory for the given path
    fs::path root_path = path.root_path();
    if (root_path.empty())
    {
        cerr << "Unable to determine the root directory for: " << path << "\n";
        return;
    }

    try
    {
        auto space_info = fs::space(path);
        cout << "\nDisk Usage Information for '" << path << "':\n";
        cout << "Total space: " << format_size(space_info.capacity) << "\n";
        cout << "Used space:  " << format_size(space_info.capacity - space_info.free) << "\n";
        cout << "Free space:  " << format_size(space_info.free) << "\n\n";
    }
    catch (const fs::filesystem_error &e)
    {
        cerr << "Error retrieving disk information for: " << path << " (" << e.what() << ")\n";
    }
}

int main()
{
    char choice;
    do
    {
        string path_str;
        cout << "Enter the directory path to analyze: ";
        getline(cin, path_str);
        fs::path path(path_str);

        // Print disk space info for the path
        print_disk_info(path);

        DiskUsage du = get_disk_usage(path);

        cout << "\nDisk Usage Tree View:\n";
        print_tree_view(path, 0, du.size);

        print_sorted_extensions(du.ext_usage);

        // Ask if the user wants to analyze another directory
        cout << "\nDo you want to analyze another directory? (y/n): ";
        cin >> choice;
        cin.ignore();  // clears the newline character left in the input buffer, so that future getline() calls work correctly.

    } while (choice == 'y' || choice == 'Y');

    cout << "Exiting the program." << endl;

    return 0;
}
