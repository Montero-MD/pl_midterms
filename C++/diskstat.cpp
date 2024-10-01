// Disk Usage Statistics Ver. 2 (C++)
// Developed by Matthew David G. Montero -- BSCS 4A
// For the subject "CCS238 - Programming Languages"

// To use the program, just enter the directory of your choice.
// It will then analyze the disk usage of the entered directory
// and will print the following to a text file:
//     1. basic information of the drive
//     2. directory's disk usage (along with its percentage) in a directory-tree-like view.
//     3. the disk usage of file extensions found within the directory.

#include <iostream>   // for input and output operations
#include <fstream>    // for reading from and/or writing to files
#include <filesystem> // for navigating directories, path checking, retrieving file metadata
#include <map>        // for storing key-value pairs; file extensions and their file sizes
#include <vector>     // for having dynamic arrays; error summary
#include <thread>     // for working with multiple threads; loading animation and timer
#include <chrono>     // for timer
#include <iomanip>    // for easy manipulation of printed texts; percentage output and timer
#include <string>     // for easy string manipulation; directory paths
#include <mutex>      // for ensuring outputs from multiple threads don't overlap; loading animation and timer
#include <windows.h>  // Windows-specific disk space functions
#include <algorithm>  // for sorting file extension usage

namespace fs = std::filesystem;
using namespace std;

// Global loading flag for animation
bool loading = false;
mutex print_mutex;

// Function to convert sizes to human-readable format
string format_size(uintmax_t size)
{
    const vector<string> units = {"B", "KB", "MB", "GB", "TB", "PB"};
    size_t unit_index = 0;
    double converted_size = static_cast<double>(size);

    while (converted_size >= 1024 && unit_index < units.size() - 1)
    {
        converted_size /= 1024;
        ++unit_index;
    }
    ostringstream out;
    out << fixed << setprecision(2) << converted_size << " " << units[unit_index];
    return out.str();
}

// Function to recursively calculate disk usage
uintmax_t get_disk_usage(const fs::path &path, map<string, uintmax_t> &ext_usage, vector<string> &error_logs)
{
    uintmax_t total_size = 0;

    try
    {
        for (const auto &entry : fs::recursive_directory_iterator(path))
        {
            if (entry.is_regular_file())
            {
                uintmax_t size = entry.file_size();
                total_size += size;

                // Extract file extension and accumulate its size
                string ext = entry.path().extension().string();
                ext_usage[ext] += size;
            }
        }
    }
    catch (const fs::filesystem_error &e)
    {
        error_logs.push_back(e.what());
    }

    return total_size;
}

// Function to display disk usage tree
void print_tree_view(const fs::path &path, int depth, uintmax_t total_size, ofstream &log_file, map<string, uintmax_t> &ext_usage, vector<string> &error_logs)
{
    uintmax_t dir_size = get_disk_usage(path, ext_usage, error_logs);
    double percentage = total_size > 0 ? (dir_size * 100.0) / total_size : 0;

    log_file << string(depth * 2, ' ') << path.filename().string() << "/ - " << format_size(dir_size) << " (" << fixed << setprecision(2) << percentage << "%)\n";

    try
    {
        for (const auto &entry : fs::directory_iterator(path))
        {
            if (entry.is_directory())
            {
                print_tree_view(entry.path(), depth + 1, total_size, log_file, ext_usage, error_logs);
            }
        }
    }
    catch (const fs::filesystem_error &e)
    {
        error_logs.push_back(e.what());
    }
}

// Function to display sorted file extension usage
void print_sorted_extensions(const map<string, uintmax_t> &ext_usage, ofstream &log_file)
{
    vector<pair<string, uintmax_t>> sorted_ext_usage(ext_usage.begin(), ext_usage.end());
    sort(sorted_ext_usage.begin(), sorted_ext_usage.end(), [](const auto &a, const auto &b)
         { return b.second < a.second; });

    log_file << "\nFile Extension Usage (sorted by usage):\n";
    for (const auto &[ext, size] : sorted_ext_usage)
    {
        log_file << ext << ": " << format_size(size) << "\n";
    }
}

// Function to display disk space information (Windows specific)
void print_disk_info(const string &path, ofstream &log_file)
{
    ULARGE_INTEGER free_bytes_available, total_bytes, free_bytes;
    std::wstring w_path(path.begin(), path.end());
    if (GetDiskFreeSpaceExW(w_path.c_str(), &free_bytes_available, &total_bytes, &free_bytes))
    {
        log_file << "\nDisk Usage Information for '" << path << "':\n";
        log_file << "Total space: " << format_size(total_bytes.QuadPart) << "\n";
        log_file << "Used space: " << format_size(total_bytes.QuadPart - free_bytes.QuadPart) << "\n";
        log_file << "Free space: " << format_size(free_bytes.QuadPart) << "\n\n";
    }
    else
    {
        log_file << "Error retrieving disk space information.\n";
    }
}

// Function to display loading animation
void loading_animation_with_timer(chrono::steady_clock::time_point start_time)
{
    const vector<char> animation = {'|', '/', '-', '\\'};
    size_t idx = 0;

    while (loading)
    {
        this_thread::sleep_for(chrono::milliseconds(100));
        chrono::duration<double> elapsed = chrono::steady_clock::now() - start_time;
        int minutes = static_cast<int>(elapsed.count()) / 60;
        int seconds = static_cast<int>(elapsed.count()) % 60;

        lock_guard<mutex> lock(print_mutex);
        cout << "\r" << animation[idx] << " Analyzing... Time Elapsed: " << minutes << " min " << setw(2) << setfill('0') << seconds << " sec";
        cout.flush();
        idx = (idx + 1) % animation.size();
    }
}

// Function to log errors
void log_errors(ofstream &log_file, const vector<string> &error_logs)
{
    if (!error_logs.empty())
    {
        log_file << "\nError Summary:\n";
        for (const auto &error : error_logs)
        {
            log_file << error << "\n";
        }
    }
}

// Main program
int main()
{
    while (true)
    {
        system("cls"); // clear screen (Windows-specific)

        int choice;

        // Get the current working directory
        fs::path current_directory = fs::current_path();

        // Define the log directory path
        fs::path log_directory = current_directory / "Disk Usage Logs";

        cout << "=== Disk Usage Statistics ===\n";
        cout << "[1] Analyze Directory\n";
        cout << "[2] Exit the Program\n\n";
        cout << "Enter your choice: ";
        cin >> choice;

        if (choice == 1)
        {
            while (true)
            {

                system("cls");
                cout << "=== Directory Analysis ===\n";
                cout << "Note: If you wish to enter a root directory, enter the drive letter with a colon and a backslash.\n";
                cout << "Example: 'C:\\'\n\n";
                cout << "Enter the directory path to analyze: ";

                string path;
                cin >> path;
                if (fs::exists(path) && fs::is_directory(path))
                {
                    // Prepare for logging
                    string log_dir = "Disk Usage Logs (C++)";
                    fs::create_directory(log_dir);

                    // Check if the provided path is a root directory
                    string log_file_path;
                    if (path.length() == 3 && path[1] == ':' && path[2] == '\\') // Example: "C:\"
                    {
                        log_file_path = log_dir + "\\" + path[0] + " -- Disk Usage Log.txt"; // Use drive letter as filename
                    }
                    else
                    {
                        log_file_path = log_dir + "\\" + fs::path(path).filename().string() + " -- Disk Usage Log.txt";
                    }

                    ofstream log_file(log_file_path);

                    if (!log_file.is_open())
                    {
                        cerr << "Error: Could not open log file.\n";
                        continue;
                    }

                    map<string, uintmax_t> ext_usage;
                    vector<string> error_logs;
                    auto start_time = chrono::steady_clock::now();

                    // Start loading animation
                    loading = true;
                    thread animation_thread(loading_animation_with_timer, start_time);

                    // Log disk info
                    print_disk_info(path, log_file);

                    // Get total size and print tree view
                    uintmax_t total_size = get_disk_usage(path, ext_usage, error_logs);
                    log_file << "\nDisk Usage Tree View:\n";
                    print_tree_view(path, 0, total_size, log_file, ext_usage, error_logs);

                    // Print sorted extensions
                    print_sorted_extensions(ext_usage, log_file);

                    // Log any errors
                    log_errors(log_file, error_logs);

                    loading = false;
                    animation_thread.join();

                    chrono::duration<double> elapsed = chrono::steady_clock::now() - start_time;
                    int minutes = static_cast<int>(elapsed.count()) / 60;
                    int seconds = static_cast<int>(elapsed.count()) % 60;

                    cout << "\n\nAnalysis complete! The output has been saved as '" << log_file_path << "'.\nSave Directory: '" << log_directory.string() << "'" << endl;
                    cout << "Time Completed: " << minutes << " min " << setw(2) << setfill('0') << seconds << " sec\n";
                }
                else
                {
                    cerr << "\nError: Invalid directory path. Please enter a valid directory.\n";
                }

                while (true)
                {
                    string restart;
                    cout << "\nDo you want to analyze another directory? (Y/n): ";
                    cin >> restart;

                    // Convert input to lowercase and remove extra spaces
                    transform(restart.begin(), restart.end(), restart.begin(), ::tolower);

                    if (restart == "y")
                    {
                        break;
                    }
                    else if (restart == "n")
                    {
                        cout << "\nSession Terminated... Goodbye.\n";
                        system("pause");
                        return 0;
                    }
                    else
                    {
                        cout << "\n\nInvalid input. Please enter 'y' to continue or 'n' to quit.";
                    }
                }
            }
        }
        else if (choice == 2)
        {
            cout << "\nSession Terminated... Goodbye.\n";
            system("pause");
            return 0;
        }
        else
        {
            cout << "\n\nInvalid input. Please enter 'y' to continue or 'n' to quit.";
        }
    }
    return 0;
}
