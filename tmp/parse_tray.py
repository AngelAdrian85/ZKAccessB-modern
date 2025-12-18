import ast, sys
p = r"C:\Users\AngelAdrian\Desktop\Acces\ZKAccessB\zkeco_modern\agent\management\commands\tray_agent.py"
try:
    src = open(p, 'r', encoding='utf-8').read()
    ast.parse(src)
    print('AST OK')
except SyntaxError as e:
    print('SyntaxError:', e)
    print('lineno', e.lineno, 'offset', e.offset)
    lines = src.splitlines()
    for i in range(max(0, e.lineno-5), min(len(lines), e.lineno+5)):
        print(f"{i+1}: {lines[i]}")
    sys.exit(1)
except Exception as e:
    print('Other error', e)
    raise
