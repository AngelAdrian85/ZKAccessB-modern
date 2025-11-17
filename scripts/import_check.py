import importlib
pkgs = ['IPython','boto','south','MySQLdb','psycopg2','pygraphviz','PIL','requests']
for p in pkgs:
    try:
        importlib.import_module(p)
        print(p + ' OK')
    except Exception as e:
        print(p + ' FAIL: ' + repr(e))
