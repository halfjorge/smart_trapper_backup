import sys; sys.path.insert(0, '/home/claude/work/guide')
from demo_lib import *
G = '/home/claude/work/guide/'
KEYC = (25, 25, 25)
YEL, RED, BLUE, GREEN, OLIVE, LBLUE, GREY = (245, 200, 40), (215, 45, 40), (40, 80, 190), (60, 150, 80), (128, 128, 40), (90, 170, 230), (150, 150, 150)
log = {}
def S(r, **kw): return composite(r, **kw)

# ---------- Round traps ----------
H, W = 80, 120
blue = rect(blank(H, W), 12, 60, 10, 70); red = rect(blank(H, W), 30, 74, 48, 110)
key = rect(blank(H, W), 0, 4, 0, W)
ko = knockout([('blue', blue), ('red', red)], key)
cols = [dict(name='blue', rgb=BLUE, alpha=ko['blue']), dict(name='red', rgb=RED, alpha=ko['red'])]
K = dict(rgb=KEYC, alpha=key)
rs = {lab: run('round_' + lab, H, W, cols, K, dict(trapShape=shape)) for lab, shape in [('off', 'square'), ('on', 'round')]}
sh = {'red': (0, 4)}
panel_grid([[S(rs['off'], show_traps=True), S(rs['on'], show_traps=True)], [S(rs['off'], shifts=sh), S(rs['on'], shifts=sh)]],
           ['Round traps OFF (square)', 'Round traps ON'], G + 'img_round.png', scale=4,
           row_titles=['Traps\n(striped)', 'Press off\nregister\n(red moved\nright 4 px)'])
log['round'] = {k: v['trap_px'] for k, v in rs.items()}

# ---------- Close key halo ----------
H, W = 70, 110
key = rect(blank(H, W), 30, 38, 0, W)                 # thick key line
yel = rect(blank(H, W), 6, 28, 8, 102)                 # stops 2 px short of the key (paper gap)
red = rect(blank(H, W), 38, 64, 8, 102)                # touches the key properly
ko = knockout([('yellow', yel), ('red', red)], key)
cols = [dict(name='yellow', rgb=YEL, alpha=ko['yellow']), dict(name='red', rgb=RED, alpha=ko['red'])]
K = dict(rgb=KEYC, alpha=key)
rs = {lab: run('halo_' + lab, H, W, cols, K, dict(closeKeyHaloPx=v)) for lab, v in [('off', 0), ('on', 2)]}
panel_grid([[S(rs['off'], show_traps=True, key_alpha_scale=0.3), S(rs['on'], show_traps=True, key_alpha_scale=0.3)],
            [S(rs['off']), S(rs['on'])]],
           ['Close key halo OFF', 'Close key halo ON'], G + 'img_halo.png', scale=4,
           row_titles=['Traps\n(key shown\nsee-through)', 'What prints'])
log['halo'] = {k: v['trap_px'] for k, v in rs.items()}

# ---------- Overlay / Multiply layers ----------
H, W = 80, 120
yel = rect(blank(H, W), 10, 70, 8, 70); blu = disk(H, W, 40, 78, 28)
key = rect(blank(H, W), 74, 79, 0, W)
K = dict(rgb=KEYC, alpha=key)
ko_off = knockout([('yellow', yel), ('blue', blu)], key)                       # box off: blue cuts yellow
ko_on = knockout([('yellow', yel), ('blue', blu)], key, skip_cutters=('blue',))  # box on: overlays don't cut
mk = lambda ko: [dict(name='yellow', rgb=YEL, alpha=ko['yellow']), dict(name='blue', rgb=(110, 170, 235), alpha=ko['blue'], blend='multiply')]
client = dict(H=H, W=W, colors=mk({'yellow': yel, 'blue': blu}), key=K, clean={'yellow': yel / 255., 'blue': blu / 255.}, trap={'yellow': 0 * yel, 'blue': 0 * blu})
r_off = run('overlay_off', H, W, mk(ko_off), K, dict(overlayMode=False))
r_on = run('overlay_on', H, W, mk(ko_on), K, dict(overlayMode=True))
panel_grid([[S(client), S(r_off), S(r_on)]], ['The artwork (client file)', 'Treated as solid (WRONG)', 'Overlay type (right)'],
           G + 'img_overlay.png', scale=3)
log['overlay'] = dict(off=r_off['trap_px'], on=r_on['trap_px'])

# ---------- Smooth traps under the key ----------
H, W = 70, 120
grn = rect(blank(H, W), 0, H, 0, 62)
key = poly(H, W, [(30, 24), (30, 46), (112, 35)])     # key line tapering to a point, running out over paper
key = np.maximum(key, poly(H, W, [(30, 10), (30, 18), (100, 6)]))
ko = knockout([('green', grn)], key)
cols = [dict(name='green', rgb=GREEN, alpha=ko['green'])]
K = dict(rgb=KEYC, alpha=key)
rs = {lab: run('smooth_' + lab, H, W, cols, K, dict(smoothKeyTraps=v)) for lab, v in [('off', False), ('on', True)]}
d, rem, add = diff_img(rs['off'], rs['on'])
panel_grid([[crop(S(rs['off'], show_traps=True, key_alpha_scale=0.25, key_outline=True), 0, 52, 20, W), crop(S(rs['on'], show_traps=True, key_alpha_scale=0.25, key_outline=True), 0, 52, 20, W), crop(d, 0, 52, 20, W)]],
           ['Smooth traps OFF', 'Smooth traps ON', 'Pink = trimmed away'], G + 'img_smooth.png', scale=5)
log['smooth'] = dict(off=rs['off']['trap_px'], on=rs['on']['trap_px'], removed=rem, added=add)

# ---------- Bevel trap corners next to paper ----------
H, W = 70, 110
key = rect(blank(H, W), 10, 32, 0, W); key[10:32, 50:58] = 0            # thick key band with a paper slot through it
red = rect(blank(H, W), 32, 66, 0, W)
ko = knockout([('red', red)], key)
cols = [dict(name='red', rgb=RED, alpha=ko['red'])]
K = dict(rgb=KEYC, alpha=key)
rs = {lab: run('bevel_' + lab, H, W, cols, K, dict(bevelKeyCorners=v)) for lab, v in [('off', False), ('on', True)]}
d, rem, add = diff_img(rs['off'], rs['on'])
panel_grid([[crop(S(rs[k], show_traps=True, key_alpha_scale=0.25, key_outline=True), 6, 40, 25, 85) for k in ('off', 'on')] + [crop(d, 6, 40, 25, 85)]],
           ['Bevel OFF (square)', 'Bevel ON', 'Pink = cut away'], G + 'img_bevel.png', scale=7)
log['bevel'] = dict(off=rs['off']['trap_px'], on=rs['on']['trap_px'], removed=rem, added=add)

# ---------- Key traps follow the colour you see ----------
H, W = 70, 110
key = rect(blank(H, W), 28, 40, 0, W)
olive = rect(blank(H, W), 42, 70, 0, W)                 # big olive area
bline = rect(blank(H, W), 40, 42, 0, W)                 # thin 2 px blue line between olive and the key
olive = np.maximum(olive, bline)                         # olive printed under the blue line too
ko = knockout([('olive', olive), ('blue', bline)], key)
cols = [dict(name='olive', rgb=OLIVE, alpha=ko['olive']), dict(name='blue', rgb=LBLUE, alpha=ko['blue'])]
K = dict(rgb=KEYC, alpha=key)
rs = {lab: run('follow_' + lab, H, W, cols, K, dict(keyTrapsFollowVisible=v)) for lab, v in [('off', False), ('on', True)]}
sh = {'key': (-4, 0)}
panel_grid([[S(rs['off']), S(rs['on'])], [S(rs['off'], shifts=sh), S(rs['on'], shifts=sh)]],
           ['Follow the colour you see OFF', 'ON'], G + 'img_follow.png', scale=4,
           row_titles=['In register', 'Key off\nregister\n(up 4 px)'])
log['follow'] = {k: v['trap_px'] for k, v in rs.items()}

# ---------- Key trap pullback ----------
H, W = 50, 90
key = rect(blank(H, W), 20, 25, 0, W)                    # thin (5 px) key line, paper below it
red = rect(blank(H, W), 0, 20, 0, W)                     # red above the line, touching it
ko = knockout([('red', red)], key)
cols = [dict(name='red', rgb=RED, alpha=ko['red'])]
K = dict(rgb=KEYC, alpha=key)
rs = {v: run(f'kpull_{v}', H, W, cols, K, dict(keyTrapPullbackPx=v)) for v in [0, 1, 2]}
panel_grid([[crop(S(rs[v], show_traps=True, key_alpha_scale=0.25, key_outline=True), 8, 36, 0, 50) for v in [0, 1, 2]],
            [crop(S(rs[v], shifts={'key': (-2, 0)}), 8, 36, 0, 50) for v in [0, 1, 2]]],
           ['Key trap pullback 0', 'Key trap pullback 1', 'Key trap pullback 2'], G + 'img_keypullback.png', scale=6,
           row_titles=['Traps under\nthe key', 'Key off\nregister\n(up 2 px)'])
log['keypullback'] = {k: v['trap_px'] for k, v in rs.items()}

# ---------- Colour trap pullback ----------
H, W = 60, 110
red = rect(blank(H, W), 0, 30, 0, W)
grey = np.zeros((H, W), np.uint8)
for cx in range(10, W, 22): grey = np.maximum(grey, disk(H, W, 30, cx, 6))   # small grey dots sitting on red's edge
key = rect(blank(H, W), 55, 60, 0, W)
ko = knockout([('red', red), ('grey', grey)], key)
cols = [dict(name='red', rgb=RED, alpha=ko['red']), dict(name='grey', rgb=GREY, alpha=ko['grey'])]
K = dict(rgb=KEYC, alpha=key)
rs = {v: run(f'cpull_{v}', H, W, cols, K, dict(colorTrapPullbackPx=v)) for v in [0, 2]}
cr = lambda im: crop(im, 20, 40, 0, 22)
d, rem, add = diff_img(rs[0], rs[2], key_alpha_scale=1.0)
panel_grid([[cr(S(rs[v], show_traps=True)) for v in [0, 2]] + [cr(d)]],
           ['Pullback 0', 'Pullback 2', 'Pink = held back'], G + 'img_colorpullback.png', scale=12)
log['colorpullback_removed'] = rem
log['colorpullback'] = {k: v['trap_px'] for k, v in rs.items()}

# ---------- Preflight cleanup / alpha threshold ----------
H, W = 70, 110
yy, xx = np.mgrid[:H, :W]
d = np.sqrt((yy - 35) ** 2 + (xx - 45) ** 2)
soft = np.clip((30 - d) / 6 * 255 + 128, 0, 255).astype(np.uint8)        # blurry edge
rng = np.random.default_rng(3); fuzz = (rng.random((H, W)) < 0.04) & (d > 33) & (d < 45)
soft[fuzz] = rng.integers(20, 70, fuzz.sum())                             # faint specks outside the shape
key = rect(blank(H, W), 0, H, 92, 100)
cols = [dict(name='blue', rgb=BLUE, alpha=soft)]
K = dict(rgb=KEYC, alpha=key)
r_off = run('pre_off', H, W, cols, K, dict(preflightCleanup=False))
r_30 = run('pre_30', H, W, cols, K, dict(alphaThreshold=30))
r_90 = run('pre_90', H, W, cols, K, dict(alphaThreshold=90))
panel_grid([[S(r_off), S(r_30), S(r_90)]], ['Preflight cleanup OFF', 'ON, alpha threshold 30', 'ON, alpha threshold 90'],
           G + 'img_preflight.png', scale=4)
log['preflight'] = dict(off=r_off['trap_px'], a30=r_30['trap_px'], a90=r_90['trap_px'])
# ---------- Tonal inks ----------
H, W = 80, 120
yy, xx = np.mgrid[:H, :W]
key = rect(blank(H, W), 0, H, 56, 62)                                  # solid key line down the middle
rng = np.random.default_rng(5)
stip = (rng.random((H, W)) < 0.06) & (xx > 70) & (yy < 30)             # key stipple texture top right
key = np.maximum(key, stip.astype(np.uint8) * 255)
blu = np.clip(80 + 175 * (1 - np.hypot(yy - 40, xx - 25) / 45), 0, 255).astype(np.uint8); blu[:, 56:] = 0   # tonal blue, left
org = np.clip(70 + 150 * (xx - 62) / 58 + 25 * np.sin(yy / 4.0), 0, 255).astype(np.uint8); org[:, :62] = 0   # tonal orange, right
K = dict(rgb=KEYC, alpha=key)
cols = [dict(name='blue', rgb=(40, 90, 200), alpha=blu), dict(name='orange', rgb=(240, 120, 30), alpha=org)]
r_std = run('tonal_off', H, W, cols, K, dict(tonalInks=False))
r_ton = run('tonal_on', H, W, cols, K, dict(tonalInks=True))
client = dict(H=H, W=W, colors=cols, key=K, clean={'blue': blu / 255., 'orange': org / 255.}, trap={'blue': 0 * blu / 1., 'orange': 0 * org / 1.})
sh = {'key': (0, 3)}
panel_grid([[S(client), S(r_std), S(r_ton)], [S(client, shifts=sh), S(r_std, shifts=sh), S(r_ton, shifts=sh)]],
           ['The artwork', 'Standard settings (WRONG)', 'Tonal type (right)'], G + 'img_tonal.png', scale=3,
           row_titles=['In register', 'Key off\nregister\n(right 3 px)'])
log['tonal'] = dict(off=r_std['trap_px'], on=r_ton['trap_px'])
json.dump(log, open(G + 'demo_log.json', 'w'), indent=1); print(json.dumps(log))
