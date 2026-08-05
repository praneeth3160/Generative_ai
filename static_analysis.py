import subprocess
import streamlit as st
import sys 
import json


def run_ruff(path):
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", path, "--output-format=json"],
        capture_output=True,
        text=True
    )
    
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return []

def parse_ruff(raw_json):
        
    findings = []
    for item in raw_json:
        findings.append({
            "line": item["location"]["row"],
            "code": item["code"],
            "message": item["message"],
        })

    return {
        "tool": "ruff",
        "total_issues": len(findings),
        "findings": findings
    }
    
