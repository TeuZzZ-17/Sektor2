import os
import time
import sys

def assemble_and_launch():
    print("--- SEKTOR BUILDER SYSTEM ---")
    files = ['1.py', '2.py', '3.py', '4.py', '5.py']
    output_file = 'editor.py'

    # 1. Check for file existence
    missing = [f for f in files if not os.path.exists(f)]
    if missing:
        print(f"ERROR: The following files are missing: {missing}")
        return

    # 2. Assembly
    print("Assembling blocks...", end="")
    try:
        with open(output_file, 'w', encoding='utf-8') as outfile:
            for fname in files:
                with open(fname, 'r', encoding='utf-8') as infile:
                    # Note in English: START OF BLOCK
                    outfile.write(f"\n# --- START {fname} ---\n")
                    outfile.write(infile.read())
                    # Note in English: Safety newline between blocks
                    outfile.write("\n")
        print(" DONE!")
    except Exception as e:
        print(f"\nERROR during writing: {e}")
        return

    # 3. Launch
    print(f"Launching {output_file}...")
    print("-" * 30)

    # Use the current python interpreter to launch the editor
    try:
        if sys.platform == "win32":
            os.system(f"python {output_file}")
        else:
            os.system(f"python3 {output_file}")
    except Exception as e:
        print(f"Error during launch: {e}")

if __name__ == "__main__":
    assemble_and_launch()
