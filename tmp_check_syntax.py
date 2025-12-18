import ast,sys
p = "zkeco_modern/agent/management/commands/tray_agent.py"
s = open(p, "r", encoding="utf-8").read()
ast.parse(s)
print('AST_OK')
