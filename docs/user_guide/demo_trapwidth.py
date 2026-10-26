import sys; sys.path.insert(0, '/home/claude/work/guide')
from demo_lib import *
H, W = 80, 130
yel = rect(blank(H, W), 10, 70, 8, 80); red = disk(H, W, 40, 85, 30)
key = rect(blank(H, W), 72, 78, 0, W)    # a key rule along the bottom
ko = knockout([('yellow', yel), ('red', red)], key)
cols = [dict(name='yellow', rgb=(245, 200, 40), alpha=ko['yellow']), dict(name='red', rgb=(215, 45, 40), alpha=ko['red'])]
K = dict(rgb=(25, 25, 25), alpha=key)
rows_t, rows_s, titles = [], [], []
for tp in [0, 3, 5, 8]:
    r = run(f'trapwidth_{tp}', H, W, cols, K, {}, trap_px=tp)
    rows_t.append(composite(r, show_traps=True)); rows_s.append(composite(r, shifts={'red': (0, 3), 'yellow': (0, -1)}))
    titles.append('No trap' if tp == 0 else f'Trap width {tp}'); print(tp, 'trap px', r['trap_px'])
panel_grid([rows_t, rows_s], titles, '/home/claude/work/guide/img_trapwidth.png', scale=3,
           row_titles=['Traps\n(white stripes =\nhidden trap)', 'Press off\nregister\nby 4 px'])
