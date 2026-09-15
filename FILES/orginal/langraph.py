import json
from langgraph.graph import StateGraph, START, END
from typing import TypedDict
from static_analysis import run_ruff, parse_ruff
from prompt_build import lang_prompt,new_code_prompt
from generator import generate_lang,generate_code
from file_manager import create_files

class LensState(TypedDict):

    original_code: str
    current_code: str

    ruff_analysis: list[dict]
    llm_analysis: list[dict]
    combine_analysis: list[dict]

    iterative: int
    max_iterative: int


def ruff_analysis(state: LensState):
    path = create_files(state["current_code"])
    ruff = run_ruff(path)
    r_a = parse_ruff(ruff)

    return {'ruff_analysis': r_a['findings']}

def llm_analysis(state: LensState):
    prompt = lang_prompt(state["current_code"])
    answer = generate_lang(prompt)

    return {"llm_analysis": answer}

def combine_analysis(state: LensState):
    combined = []

    for issue in state["ruff_analysis"]:
        combined.append({
            "source": "ruff",
            **issue
        })

    for issue in state["llm_analysis"]:
        combined.append({
            "source": "llm",
            **issue
        })

    return {
        "combine_analysis": combined
    }

def check_status(state: LensState):
    if not state["combine_analysis"]:
        return "finish"

    if state["iterative"] >= state["max_iterative"]:
        return "stop"
    
    return "fix"

def generate_fix(state: LensState):
    analysis_text = json.dumps(state["combine_analysis"], indent = 2)
    prompt = new_code_prompt(analysis_text, state["current_code"])

    code = generate_code(prompt)

    return {"current_code": code, "iterative": state["iterative"]+1}


def langraph():
    graph = StateGraph(LensState)
    graph.add_node('ruff_analysis', ruff_analysis)
    graph.add_node('llm_analysis', llm_analysis)
    graph.add_node('combine_analysis', combine_analysis)
    graph.add_node('generate_fix', generate_fix)

    graph.add_edge(START, "ruff_analysis")
    graph.add_edge(START, "llm_analysis")
    graph.add_edge("ruff_analysis", "combine_analysis")
    graph.add_edge("llm_analysis", "combine_analysis")
    graph.add_conditional_edges("combine_analysis", check_status, {"finish": END, "stop": END, "fix": "generate_fix"})
    graph.add_edge("generate_fix", "ruff_analysis")
    graph.add_edge("generate_fix", "llm_analysis")



    workflow = graph.compile()

    return workflow