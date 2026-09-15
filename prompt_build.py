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

def format_history(messages):
    history = ""

    for msg in messages:
        history += f'{msg["role"].capitalize()}: {msg["content"]}\n\n'

    return history

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

def chat_prompt(code,meta,ruff_analysis,memory,question):
    prompt = f'''
You are a senior Python software engineer and AI coding assistant.

The user has already uploaded a Python source file and is asking follow-up questions about it.

Instructions:

- Answer the user's question using the provided source code as the primary source of truth.
- Use the metadata to understand the structure of the code.
- Use the Ruff findings only as supporting evidence.
- If the question refers to previous messages, use the conversation history.
- If you are uncertain about something, clearly say so instead of guessing.
- Do not invent functions or variables that do not exist.

When appropriate, include corrected code snippets or improved implementations to support your explanation.

------------------------------------
METADATA
{meta}
------------------------------------

------------------------------------
RUFF ANALYSIS
{ruff_analysis}
------------------------------------

------------------------------------
SOURCE CODE
{code}
------------------------------------

------------------------------------
RECENT CONVERSATION
{memory}
------------------------------------

------------------------------------
USER QUESTION
{question}
------------------------------------

'''
    return prompt

def lang_prompt(code):
    prompt = f'''
You are a senior Python software engineer performing a deep code analysis.

Analyze the following Python source code and identify potential problems that
may not be detected by traditional static analysis tools.

Look for:

- Logical bugs
- Runtime errors
- Incorrect program behavior
- Edge cases
- Exception handling problems
- Infinite loops
- Incorrect conditions
- Resource management problems
- Performance issues
- Security problems
- Maintainability problems

Do not report something as a definite bug if it is only a possibility.
Clearly distinguish between confirmed problems and potential problems.

For every issue, provide:
- issue type
- line number if identifiable
- severity
- description
- reason
- suggested fix

If no issues are found, return an empty list.

SOURCE CODE:
--------------------
{code}
--------------------'''

    return prompt

def new_code_prompt(analysis, code):
    prompt = f'''
You are a senior Python software engineer.

Your task is to fix the problems identified in the analysis and return the
complete corrected Python source code.

You are given:

1. The current Python source code.
2. Analysis produced by static analysis tools and AI analysis.

IMPORTANT RULES:

- Fix the identified issues.
- Preserve the original functionality of the program.
- Do not remove functionality simply to silence an error.
- Do not introduce unnecessary changes.
- Do not invent functions, variables, classes, or dependencies.
- Do not rewrite the entire program unless it is necessary to fix the issues.
- Consider both the Ruff findings and the AI-detected issues.
- Make the smallest reasonable changes required to fix the problems.
- Ensure the resulting code is syntactically valid Python.
- Ensure imports are correct.
- Ensure variables and functions are properly defined.
- Handle identified runtime and logical issues appropriately.

After making the changes, mentally review the corrected code for additional
obvious problems.

Return ONLY the complete corrected Python source code.
Do not return explanations.
Do not use Markdown code fences.
Do not include ```python.
Do not include any text before or after the code.

-----------------------------
ANALYSIS
{analysis}
-----------------------------

CURRENT SOURCE CODE
-----------------------------
{code}
-----------------------------
'''
    return prompt