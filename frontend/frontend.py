import os

def export_frontend_to_txt():
    # Name of the output file
    output_filename = "all_frontend_code.txt"
    
    # Folders to completely skip
    ignored_dirs = {
        'node_modules', '.next', 'build', 'dist', 
        '.git', '.emergent', 'coverage', '.cache'
    }
    
    # File extensions to include
    allowed_extensions = {
        '.js', '.jsx', '.ts', '.tsx', '.css', 
        '.json', '.html', '.config.js', '.local'
    }

    print(f"Starting export... looking for files in: {os.getcwd()}")
    
    file_count = 0
    with open(output_filename, 'w', encoding='utf-8') as outfile:
        for root, dirs, files in os.walk('.'):
            # Skip ignored directories
            dirs[:] = [d for d in dirs if d not in ignored_dirs]

            for file in files:
                # Check if file extension is in our allowed list
                if any(file.endswith(ext) for ext in allowed_extensions):
                    # Skip the output file itself and lock files
                    if file == output_filename or file == 'package-lock.json':
                        continue
                        
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, '.')
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as infile:
                            content = infile.read()
                            
                            # Write a header for each file
                            outfile.write(f"\n{'='*80}\n")
                            outfile.write(f"FILE: {relative_path}\n")
                            outfile.write(f"{'='*80}\n\n")
                            
                            outfile.write(content)
                            outfile.write("\n\n")
                            
                            print(f"Added: {relative_path}")
                            file_count += 1
                    except Exception as e:
                        print(f"Could not read {relative_path}: {e}")

    print(f"\nDone! Combined {file_count} files into '{output_filename}'.")

if __name__ == "__main__":
    export_frontend_to_txt()