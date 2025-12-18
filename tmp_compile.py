import py_compile,sys
try:
    py_compile.compile(r'c:\Users\AngelAdrian\Desktop\Acces\ZKAccessB\zkeco_modern\agent\management\commands\tray_agent.py', doraise=True)
    print('OK')
except py_compile.PyCompileError as e:
    print('FAIL')
    print(e)
    sys.exit(1)
