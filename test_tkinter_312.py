import sys
print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")
print(f"Python sys.path: {sys.path}")
try:
    import tkinter
    print("tkinter imported successfully on 3.12!")
except ModuleNotFoundError as e:
    print(f"Failed to import tkinter on 3.12: {e}")
