import sys
print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")
print(f"Python sys.path: {sys.path}")
try:
    import tkinter
    print("tkinter imported successfully!")
except ModuleNotFoundError as e:
    print(f"Failed to import tkinter: {e}")
