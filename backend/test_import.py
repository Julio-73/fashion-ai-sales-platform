print("Testing import using global python + PYTHONPATH...", flush=True)
import sys
print(f"sys.path: {sys.path}", flush=True)

print("Importing sqlalchemy...", flush=True)
import sqlalchemy
print("Imported sqlalchemy successfully!", flush=True)

print("Importing app.main...", flush=True)
import app.main
print("Imported app.main successfully!", flush=True)
