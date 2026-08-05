from input import upload_file
from static_analysis import run_ruff,parse_ruff
from summary import metadata
from prompt_build import format_meta,format_ruff,build_prompt
from generator import genearte_llm
import streamlit as st
import ast

data = upload_file()

if data is not None:

    with open(data["file_path"], 'r', encoding="utf-8") as f:
        code = f.read()
    tree = ast.parse(code)

    ruff_analysis = parse_ruff(run_ruff(data["file_path"]))
    meta = metadata(data,tree)
    p_b = build_prompt(data["Code"], format_meta(meta), format_ruff(ruff_analysis))

    with st.spinner("Reviewing the code......"):
        final_answer = genearte_llm(p_b)

    st.subheader("Summary")
    with st.expander("📋 View AI Review"):
        st.markdown(final_answer)



