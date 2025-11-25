import pathlib
p = pathlib.Path('mysql/bin/mysqldump.exe')
with p.open('rb') as f:
    b = f.read(2)
print('Header bytes repr:', b, 'ints:', b[0], b[1])
