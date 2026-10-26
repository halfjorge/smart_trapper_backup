# Simple illustrations of the Photoshop-side buttons (NOT engine output - drawn to explain the idea).
import sys; sys.path.insert(0, '/home/claude/work/guide')
from demo_lib import *
G = '/home/claude/work/guide/'
H, W = 60, 80
def layer_tile(alpha, rgb, specks=None):
    img = np.ones((H, W, 3)) * 255; yy, xx = np.mgrid[:H, :W]
    img[((yy // 6 + xx // 6) % 2) == 0] = 232            # checkerboard = transparent
    a = (alpha / 255.)[..., None]; col = np.ones((H, W, 3)) * np.array(rgb, float)
    if specks is not None: col[specks] = [190, 120, 60]
    return np.clip(img * (1 - a) + col * a, 0, 255).astype(np.uint8)
key = rect(blank(H, W), 26, 32, 0, W); red = disk(H, W, 30, 50, 22); yel = rect(blank(H, W), 8, 52, 6, 60)
# knockout
ko = knockout([('yellow', yel), ('red', red)], key)
panel_grid([[layer_tile(key, (25, 25, 25)), layer_tile(red, (215, 45, 40)), layer_tile(yel, (245, 200, 40))],
            [layer_tile(key, (25, 25, 25)), layer_tile(ko['red'], (215, 45, 40)), layer_tile(ko['yellow'], (245, 200, 40))]],
           ['Key (top layer)', 'Red', 'Yellow'], G + 'img_knockout.png', scale=3, row_titles=['Before\n(each layer\non its own)', 'After\nknockout'])
# cut top key only
ck = {n: a.copy() for n, a in [('red', red), ('yellow', yel)]}
for n in ck: ck[n][key > 127] = 0
panel_grid([[layer_tile(key, (25, 25, 25)), layer_tile(ck['red'], (215, 45, 40)), layer_tile(ck['yellow'], (245, 200, 40))]],
           ['Key', 'Red', 'Yellow'], G + 'img_cutkey.png', scale=3, row_titles=['After Cut\nTop Key'])
# clean colors
rng = np.random.default_rng(2); sp = (rng.random((H, W)) < 0.05) & (red > 0)
panel_grid([[layer_tile(red, (215, 45, 40), specks=sp), layer_tile(red, (215, 45, 40))]], ['Before', 'After Clean Colors'],
           G + 'img_cleancolors.png', scale=3)
print('ok')
