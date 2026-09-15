import os

def create_files(code):
    os.makedirs("FILES/working", exist_ok=True)

    path = os.path.join("FILES", "working", "current.py")

    with open(path, "w", encoding="utf-8") as f:
        f.write(code)

    return path