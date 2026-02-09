import re

files = [
    '/workspaces/Memory-Pawnshop/script/chapters/chapter_12.md',
    '/workspaces/Memory-Pawnshop/script/chapters/chapter_13.md',
    '/workspaces/Memory-Pawnshop/script/chapters/chapter_47.md',
    '/workspaces/Memory-Pawnshop/script/chapters/chapter_52.md',
    '/workspaces/Memory-Pawnshop/script/chapters/chapter_53.md',
    '/workspaces/Memory-Pawnshop/script/chapters/chapter_54.md',
    '/workspaces/Memory-Pawnshop/script/chapters/chapter_55.md',
    '/workspaces/Memory-Pawnshop/script/chapters/chapter_58.md',
    '/workspaces/Memory-Pawnshop/script/chapters/chapter_65.md',
]
for f in files:
    with open(f, 'r', encoding='utf-8') as fh:
        text = fh.read()
    count = len(re.findall(r'[\u4e00-\u9fff]', text))
    name = f.split('/')[-1]
    status = 'PASS' if count >= 2000 else 'FAIL'
    print(f'{name:20s}  {count:5d} chars  {status}')
