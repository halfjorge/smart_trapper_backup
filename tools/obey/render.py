# Multiply-preview render of a crop (like Sara's Photoshop view: every ink layer multiplied over paper).
# Usage: python3 render.py DIR x0 y0 x1 y1 out.png [scale] [prefix]
#   DIR has layers.json + m_<i>.npy (prefix 'm_') or j_<i>.npy (fixed masks, prefix 'j_')
import sys, json, numpy as np
from PIL import Image
W, H = 9600, 12000; RB = W // 8

def crop(path, x0, y0, x1, y1):
    P = np.load(path, mmap_mode='r')
    return np.unpackbits(np.asarray(P[y0*RB:y1*RB])).reshape(y1-y0, W)[:, x0:x1].astype(bool)

def ink_layers(D):
    Ls = json.load(open(f'{D}/layers.json'))
    return [l for l in Ls if l['visible'] and l.get('pixels') and
            (l['name'].startswith('CLEAN__') or l['name'].startswith('TRAP__') or l['name'] == 'Key')]

def render(D, box, prefix='m_', key_alpha=1.0):
    x0, y0, x1, y1 = box
    img = np.ones((y1-y0, x1-x0, 3)) * np.array([248, 239, 229]) / 255
    for l in ink_layers(D):
        m = crop(f'{D}/{prefix}{l["index"]}.npy', x0, y0, x1, y1)
        c = np.array(l['colour']) / 255
        if l['name'] == 'Key':
            c = 1 - key_alpha * (1 - c)
        img[m] *= c
    return (img * 255).clip(0, 255).astype(np.uint8)

if __name__ == '__main__':
    D = sys.argv[1]; box = tuple(int(v) for v in sys.argv[2:6]); out = sys.argv[6]
    s = float(sys.argv[7]) if len(sys.argv) > 7 else 1
    pre = sys.argv[8] if len(sys.argv) > 8 else 'm_'
    im = Image.fromarray(render(D, box, pre, 0.75))
    if s != 1: im = im.resize((int(im.width*s), int(im.height*s)), Image.NEAREST)
    im.save(out)

def render_small(D, s, prefix='m_', key_alpha=0.75, strip=600):
    rows = []
    for y in range(0, H, strip):
        a = render(D, (0, y, W, min(H, y+strip)), prefix, key_alpha)
        im = Image.fromarray(a).resize((int(W*s), int((min(H, y+strip)-y)*s)), Image.BILINEAR)
        rows.append(np.asarray(im))
    return Image.fromarray(np.vstack(rows))
