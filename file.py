from input import upload_file
from static_analysis import run_ruff,parse_ruff
from summary import metadata
from prompt_build import format_meta,format_ruff,format_history,build_prompt,chat_prompt
from generator import generate_llm
import streamlit as st
import ast

@st.dialog("Summary")
def show():
    st.markdown(st.session_state["final_answer"])

st.title("Code Lens")

data = upload_file()

if data is not None:

    with open(data["file_path"], 'r', encoding="utf-8") as f:
        code = f.read()
    tree = ast.parse(code)

    ruff_analysis = parse_ruff(run_ruff(data["file_path"]))
    meta = metadata(data,tree)
    p_b = build_prompt(data["Code"], format_meta(meta), format_ruff(ruff_analysis))

    if "final_answer" not in st.session_state:
        st.session_state["final_answer"] = None

    if st.session_state["final_answer"] is None:
        with st.spinner("Reviewing the code..."):
            st.session_state["final_answer"] = generate_llm(p_b)
    
    col1, col2 = st.columns([1,1])
    with col1:
        st.write("📄 Summary - ")
    with col2:
        if st.button("View Review"):
            show()

    # CHAT
    st.divider()

    if "c" not in st.session_state:
        st.session_state["c"] = data["Code"]
    if "m" not in st.session_state:
        st.session_state["m"] = meta
    if "r_a" not in st.session_state:
        st.session_state["r_a"] = ruff_analysis

    st.subheader("💬 Chat with your Code")
    st.caption("Ask follow-up questions about the uploaded code.")

    question = st.chat_input("Ask anything about your code...")
    with st.container(border=True):
        if "messages" not in st.session_state:
                st.session_state.messages = []
        
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if question:
            st.session_state.messages.append(
            {
                "role": "user",
                "content": question
            }
            )

            with st.chat_message("user"):
                st.markdown(question)

            history = format_history(st.session_state.messages[-5:])

            c_p = chat_prompt(st.session_state["c"], st.session_state["m"], st.session_state["r_a"], history, question)
            with st.chat_message("assistant"):
                with st.spinner("Thinking......."):
                    chat_answer = generate_llm(c_p)

                st.markdown(chat_answer)
            st.session_state.messages.append(
                {
                "role": "assistant",
                "content": chat_answer
                }
                )


