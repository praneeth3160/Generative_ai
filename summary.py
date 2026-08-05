import ast

def name_language(data):

    return data["file_name"], data["language"]

def function_name(tree):
    fun = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            par = [arg.arg for arg in node.args.args]
            sign = f"{node.name}({','.join(par)})"
            fun.append(sign)

    return fun

def classes_name(tree):
    clas = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            clas.append(node.name)

    return clas

def import_name(tree):
    imp = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for name in node.names:
                imp.append(name.name)

        elif isinstance(node, ast.ImportFrom):
            module = node.module
            for name in node.names:
                imp.append(f"{module}.{name.name}")

    return imp

def metadata(data,tree):
    n,l = name_language(data)
    f = function_name(tree)
    c = classes_name(tree)
    i = import_name(tree)

    return{
        "file_name" : n,
        "language" : l,
        "function_names" : f,
        "classes_names" : c,
        "imports_names" : i
    }
