import os
with open('test_spawn.log', 'w', encoding='utf-8') as f:
    f.write('Test spawn OK\n')
    f.write('CWD: ' + os.getcwd() + '\n')
    f.write('ENV: ' + str(dict(os.environ)) + '\n')
