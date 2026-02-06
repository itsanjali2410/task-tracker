"""
Script to export all backend code to exported.txt
"""
import os
from pathlib import Path

def export_backend_code(output_file='exported.txt'):
    backend_dir = Path('backend')

    if not backend_dir.exists():
        print(f"Error: {backend_dir} directory not found")
        return

    file_count = 0
    total_lines = 0

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("BACKEND APPLICATION CODE EXPORT\n")
        f.write("=" * 80 + "\n\n")

        for root, dirs, files in os.walk(backend_dir):
            # Skip __pycache__ directories
            dirs[:] = [d for d in dirs if d != '__pycache__']

            for file in sorted(files):
                # Skip hidden files
                if file.startswith('.'):
                    continue

                # ❌ Skip unwanted files
                if file in ('requirements.txt', '__init__.py'):
                    continue

                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, '.')

                try:
                    with open(file_path, 'r', encoding='utf-8') as file_obj:
                        content = file_obj.read()
                        lines = content.count('\n') + 1

                        f.write(f"\n{'=' * 80}\n")
                        f.write(f"FILE: {rel_path}\n")
                        f.write(f"{'=' * 80}\n\n")
                        f.write(content)

                        if not content.endswith('\n'):
                            f.write('\n')

                        file_count += 1
                        total_lines += lines
                        print(f"✓ Exported: {rel_path} ({lines} lines)")

                except Exception as e:
                    print(f"✗ Error reading {rel_path}: {e}")

    print(f"\n✓ Successfully exported {file_count} files to {output_file}")
    print(f"  Total lines: {total_lines}")

if __name__ == '__main__':
    export_backend_code()
