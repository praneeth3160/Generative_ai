def format_meta(meta):
    line = []

    for key,value in meta.items():
        if isinstance(value, list):
            value = ", ".join(value) if value else "None"

        line.append(f"{key}:{value}")

    return "\n".join(line)

def format_ruff(ruff_analysis):
    lines = [f"tool: {ruff_analysis['tool']}", f"total_issues: {ruff_analysis['total_issues']}"]
    
    if not ruff_analysis["findings"]:
        lines.append("No issues found.")
    else:
        for f in ruff_analysis["findings"]:
            lines.append(f"Line {f['line']}: [{f['code']}] {f['message']}")
    
    return "\n".join(lines)


def build_prompt(code,meta,ruff_analysis):

    prompt = f''' You are a senior Python software engineer with expertise in code review, debugging, 
                software design, performance optimization, and Python best practices.
                
    Your task is to perform a professional review of the uploaded Python source code.
    You will receive:
        1. Source code
        2. Metadata describing the code structure
        3. Ruff static analysis findings
        Use the provided source code, metadata, and Ruff findings together to produce a comprehensive code review.
        Do not rely solely on the Ruff findings. Analyze the source code independently and use the metadata to understand 
        the overall structure of the program.
                
        Treat the Ruff findings as verified static analysis results.
        If Ruff reports no issues, do not assume the code is free of defects.
        Continue analyzing for logical, runtime, design, and maintainability problems.
        Instead:
            - Explain why each issue matters.
            - Suggest improvements.
            - Look for additional problems that Ruff cannot detect.

    ----------------------------
    METADATA:
    {meta}
    ----------------------------

    ----------------------------
    RUFF ANALYSIS:
    {ruff_analysis}
    ----------------------------

    ----------------------------    
    SOURCE CODE:
    {code}
    ----------------------------

    Return the review using the following format:
        -Executive Summary
        - Logical bugs
        - Runtime issues
        - Edge cases
        - Performance problems
        - Readability
        - Maintainability
        - Code organization
        - Best practices
        - Pythonic improvements
        - Security Conerns
        - Error Handling
    '''

    return prompt
