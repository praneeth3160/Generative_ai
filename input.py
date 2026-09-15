import streamlit as st
import os

os.makedirs("FILES/orginal", exist_ok=True)


language_map = {
    "py": "Python",
    "cpp": "C++",
    "c": "C"
    }

def upload_file():

    upload = st.file_uploader("Upload your code file .py for now", type=["py", "cpp", "c"])
    
    if upload is None:
        return None
    
    ext = upload.name.split('.')[-1]
    language = language_map.get(ext, 'Unknown')

    st.write(f"Language: {language}")

    code = upload.read().decode("utf-8")
    
    path = os.path.join("FILES", "orginal", upload.name)
    with open(path, "wb") as f:
        f.write(upload.getbuffer())

    return {
        "file_name": upload.name,
        "language": language,
        "file_path": path,
        "Code": code
    }



