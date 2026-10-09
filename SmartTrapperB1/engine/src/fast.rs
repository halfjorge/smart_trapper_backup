//! Fast, exact replacements for the engine's repeated full-image passes.
//!
//! Every function here produces bit-for-bit the same result as the original
//! slow version it replaces (the originals are kept in the tests below and
//! compared on random masks). Pure std, so it can be tested with plain
//! `rustc --test src/fast.rs`.

/// Half-open rectangle [x0,x1) x [y0,y1) in image pixels.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Rect {
    pub x0: u32,
    pub y0: u32,
    pub x1: u32,
    pub y1: u32,
}

impl Rect {
    pub fn full(w: u32, h: u32) -> Rect {
        Rect { x0: 0, y0: 0, x1: w, y1: h }
    }
    pub fn width(&self) -> u32 {
        self.x1.saturating_sub(self.x0)
    }
    pub fn height(&self) -> u32 {
        self.y1.saturating_sub(self.y0)
    }
    pub fn is_empty(&self) -> bool {
        self.width() == 0 || self.height() == 0
    }
    pub fn grow(&self, by: u32, w: u32, h: u32) -> Rect {
        Rect {
            x0: self.x0.saturating_sub(by),
            y0: self.y0.saturating_sub(by),
            x1: (self.x1.saturating_add(by)).min(w),
            y1: (self.y1.saturating_add(by)).min(h),
        }
    }
    pub fn intersect(&self, o: &Rect) -> Rect {
        let x0 = self.x0.max(o.x0);
        let y0 = self.y0.max(o.y0);
        Rect { x0, y0, x1: self.x1.min(o.x1).max(x0), y1: self.y1.min(o.y1).max(y0) }
    }
}

/// Bounding box of non-zero pixels (full-image mask), or None if empty.
pub fn bbox(mask: &[u8], w: u32, h: u32) -> Option<Rect> {
    let (wu, hu) = (w as usize, h as usize);
    let (mut x0, mut x1, mut y0, mut y1) = (usize::MAX, 0usize, usize::MAX, 0usize);
    for y in 0..hu {
        let row = &mask[y * wu..(y + 1) * wu];
        if let Some(first) = row.iter().position(|&v| v != 0) {
            let last = row.iter().rposition(|&v| v != 0).unwrap();
            x0 = x0.min(first);
            x1 = x1.max(last + 1);
            y0 = y0.min(y);
            y1 = y + 1;
        }
    }
    if x0 == usize::MAX {
        None
    } else {
        Some(Rect { x0: x0 as u32, y0: y0 as u32, x1: x1 as u32, y1: y1 as u32 })
    }
}

// ---------------------------------------------------------------------------
// Compact storage: 1 bit per pixel (an 81 MP mask = ~10 MB instead of 81 MB)
// ---------------------------------------------------------------------------

#[derive(Clone)]
pub struct Bits {
    words: Vec<u64>,
    len: usize,
}

impl Bits {
    pub fn pack(mask: &[u8]) -> Bits {
        let mut words = vec![0u64; mask.len().div_ceil(64)];
        for (wi, chunk) in mask.chunks(64).enumerate() {
            let mut v = 0u64;
            for (b, &m) in chunk.iter().enumerate() {
                if m != 0 {
                    v |= 1u64 << b;
                }
            }
            words[wi] = v;
        }
        Bits { words, len: mask.len() }
    }

    pub fn unpack_into(&self, out: &mut Vec<u8>) {
        out.clear();
        out.resize(self.len, 0);
        for (wi, chunk) in out.chunks_mut(64).enumerate() {
            let v = self.words[wi];
            if v == 0 {
                continue;
            }
            for (b, o) in chunk.iter_mut().enumerate() {
                *o = ((v >> b) & 1) as u8;
            }
        }
    }

    pub fn unpack(&self) -> Vec<u8> {
        let mut v = Vec::new();
        self.unpack_into(&mut v);
        v
    }
}

// ---------------------------------------------------------------------------
// Square (8-neighbour) dilation / erosion of any radius in O(pixels)
// ---------------------------------------------------------------------------

/// Same result as calling the engine's 8-neighbour `dilate` `r` times:
/// a pixel is on if any pixel within a (2r+1)x(2r+1) square is on.
/// Works on a window `win` of a full-size mask; pixels outside the window are
/// treated as off. Returns a win.width() x win.height() buffer.
pub fn box_dilate_window(mask: &[u8], w: u32, win: Rect, r: u32) -> Vec<u8> {
    box_filter_window(mask, w, win, r, false)
}

/// Same result as calling the engine's 8-neighbour `erode` `r` times
/// (image border counts as off): a pixel stays on only if every pixel within
/// the (2r+1)x(2r+1) square is inside the image and on.
pub fn box_erode_full(mask: &[u8], w: u32, h: u32, r: u32) -> Vec<u8> {
    box_filter_window(mask, w, Rect::full(w, h), r, true)
}

fn box_filter_window(mask: &[u8], w: u32, win: Rect, r: u32, erode: bool) -> Vec<u8> {
    let ww = win.width() as usize;
    let wh = win.height() as usize;
    let mut out = vec![0u8; ww * wh];
    if ww == 0 || wh == 0 {
        return out;
    }
    if r == 0 {
        for y in 0..wh {
            let src = (win.y0 as usize + y) * w as usize + win.x0 as usize;
            for x in 0..ww {
                out[y * ww + x] = (mask[src + x] != 0) as u8;
            }
        }
        return out;
    }
    let r = r as usize;
    let full = 2 * r + 1;

    // Horizontal pass: count of on-pixels in [x-r, x+r] within the window.
    let mut tmp = vec![0u8; ww * wh];
    let mut pref = vec![0u32; ww + 1];
    for y in 0..wh {
        let src = (win.y0 as usize + y) * w as usize + win.x0 as usize;
        for x in 0..ww {
            pref[x + 1] = pref[x] + (mask[src + x] != 0) as u32;
        }
        for x in 0..ww {
            let lo = x.saturating_sub(r);
            let hi = (x + r + 1).min(ww);
            let c = pref[hi] - pref[lo];
            tmp[y * ww + x] = if erode { (c as usize == full) as u8 } else { (c > 0) as u8 };
        }
    }
    // Vertical pass on the horizontal result, row by row (cache-friendly):
    // keep a running per-column count of rows [y-r, y+r].
    let mut cnt = vec![0u32; ww];
    for y in 0..r.min(wh) {
        for x in 0..ww {
            cnt[x] += tmp[y * ww + x] as u32;
        }
    }
    for y in 0..wh {
        let add = y + r;
        if add < wh {
            let row = &tmp[add * ww..(add + 1) * ww];
            for x in 0..ww {
                cnt[x] += row[x] as u32;
            }
        }
        if y > r {
            let row = &tmp[(y - r - 1) * ww..(y - r) * ww];
            for x in 0..ww {
                cnt[x] -= row[x] as u32;
            }
        }
        let o = &mut out[y * ww..(y + 1) * ww];
        if erode {
            let span_ok = y >= r && y + r < wh; // window fully inside the image
            for x in 0..ww {
                o[x] = (span_ok && cnt[x] as usize == full) as u8;
            }
        } else {
            for x in 0..ww {
                o[x] = (cnt[x] > 0) as u8;
            }
        }
    }
    out
}

/// Same as the engine's `pair_boundary_seed` (pixels of `a` with an
/// 8-neighbour in `b`), but only scans where that is possible and returns the
/// result as a window plus its tight bounding box. None = no contact.
pub fn pair_boundary_seed_window(
    a: &[u8],
    b: &[u8],
    w: u32,
    h: u32,
    a_box: Rect,
    b_box: Rect,
) -> Option<(Rect, Vec<u8>)> {
    let scan = a_box.intersect(&b_box.grow(1, w, h));
    if scan.is_empty() {
        return None;
    }
    let (wi, hi) = (w as i64, h as i64);
    let sw = scan.width() as usize;
    let mut seed = vec![0u8; sw * scan.height() as usize];
    let mut any = false;
    let (mut x0, mut y0, mut x1, mut y1) = (u32::MAX, u32::MAX, 0u32, 0u32);
    const N8: [(i64, i64); 8] = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)];
    for y in scan.y0..scan.y1 {
        for x in scan.x0..scan.x1 {
            let idx = y as usize * w as usize + x as usize;
            if a[idx] == 0 {
                continue;
            }
            for (dx, dy) in N8 {
                let nx = x as i64 + dx;
                let ny = y as i64 + dy;
                if nx < 0 || ny < 0 || nx >= wi || ny >= hi {
                    continue;
                }
                if b[(ny * wi + nx) as usize] != 0 {
                    seed[(y - scan.y0) as usize * sw + (x - scan.x0) as usize] = 1;
                    any = true;
                    x0 = x0.min(x);
                    y0 = y0.min(y);
                    x1 = x1.max(x + 1);
                    y1 = y1.max(y + 1);
                    break;
                }
            }
        }
    }
    if !any {
        return None;
    }
    // Crop the scan-window seed down to its tight bounding box.
    let sb = Rect { x0, y0, x1, y1 };
    let cw = sb.width() as usize;
    let mut out = vec![0u8; cw * sb.height() as usize];
    for y in 0..sb.height() as usize {
        let src = (sb.y0 - scan.y0) as usize + y;
        let sx = (sb.x0 - scan.x0) as usize;
        out[y * cw..(y + 1) * cw].copy_from_slice(&seed[src * sw + sx..src * sw + sx + cw]);
    }
    Some((sb, out))
}

/// Squared Euclidean distance from every pixel to the nearest on-pixel of
/// `mask` (w x h), exact up to `cap` px. Anything farther (or no on-pixel at
/// all) gets `(cap+1)^2`. Pixels outside the image never count as on.
pub fn capped_dist_sq(mask: &[u8], w: usize, h: usize, cap: u32) -> Vec<u16> {
    let c = cap as usize;
    let far = ((c + 1) * (c + 1)) as u16;
    // Horizontal pass: distance along the row to the nearest on-pixel, capped at c+1.
    let lim = (c + 1) as u8;
    let mut hd = vec![lim; w * h];
    for y in 0..h {
        let row = &mask[y * w..(y + 1) * w];
        let out = &mut hd[y * w..(y + 1) * w];
        let mut last: Option<usize> = None;
        for x in 0..w {
            if row[x] != 0 { last = Some(x); }
            if let Some(l) = last { out[x] = ((x - l).min(c + 1)) as u8; }
        }
        last = None;
        for x in (0..w).rev() {
            if row[x] != 0 { last = Some(x); }
            if let Some(l) = last { let v = ((l - x).min(c + 1)) as u8; if v < out[x] { out[x] = v; } }
        }
    }
    // Vertical pass: min over rows within c of dx^2 + dy^2.
    let mut out = vec![far; w * h];
    for y in 0..h {
        let o = &mut out[y * w..(y + 1) * w];
        let lo = y.saturating_sub(c);
        let hi = (y + c).min(h - 1);
        for yy in lo..=hi {
            let dy = if yy > y { yy - y } else { y - yy };
            let dy2 = (dy * dy) as u16;
            let r = &hd[yy * w..(yy + 1) * w];
            for x in 0..w {
                let dx = r[x] as usize;
                if dx <= c {
                    let v = (dx * dx) as u16 + dy2;
                    if v < o[x] { o[x] = v; }
                }
            }
        }
        for v in o.iter_mut() { if *v as usize > c * c { *v = far; } }
    }
    out
}

/// Round dilation: on where the nearest on-pixel is within `r` px (true
/// Euclidean distance), i.e. growth by a disk instead of a square.
pub fn disk_dilate(mask: &[u8], w: usize, h: usize, r: u32) -> Vec<u8> {
    let r2 = (r * r) as u16;
    capped_dist_sq(mask, w, h, r).iter().map(|v| (*v <= r2) as u8).collect()
}

/// Compute one trap exactly like the original engine:
///   trap = dilate_n(boundary_seed(a,b), r) & allow & !a
/// Returns (window, window mask) or None when the trap is empty.
pub fn compute_pair_trap(
    a: &[u8],
    b: &[u8],
    allow: &[u8],
    w: u32,
    h: u32,
    a_box: Rect,
    b_box: Rect,
    r: u32,
    round: bool,
) -> Option<(Rect, Vec<u8>)> {
    let (sb, seed) = pair_boundary_seed_window(a, b, w, h, a_box, b_box)?;
    let win = sb.grow(r, w, h);
    // Dilate the seed window into the bigger window. Build a small source
    // canvas the size of `win` holding the seed, then box-dilate it.
    let ww = win.width() as usize;
    let mut canvas = vec![0u8; ww * win.height() as usize];
    let sw = sb.width() as usize;
    for y in 0..sb.height() as usize {
        let dst = (sb.y0 - win.y0) as usize + y;
        let dx0 = (sb.x0 - win.x0) as usize;
        canvas[dst * ww + dx0..dst * ww + dx0 + sw].copy_from_slice(&seed[y * sw..(y + 1) * sw]);
    }
    let mut trap = if round {
        disk_dilate(&canvas, ww, win.height() as usize, r)
    } else {
        box_dilate_window(&canvas, ww as u32, Rect::full(ww as u32, win.height()), r)
    };
    drop(canvas);
    let mut any = false;
    for y in 0..win.height() as usize {
        let row = (win.y0 as usize + y) * w as usize + win.x0 as usize;
        let t = &mut trap[y * ww..(y + 1) * ww];
        for x in 0..ww {
            let i = row + x;
            let on = t[x] != 0 && allow[i] != 0 && a[i] == 0;
            t[x] = on as u8;
            any |= on;
        }
    }
    if any {
        Some((win, trap))
    } else {
        None
    }
}

// ---------------------------------------------------------------------------
// Ink colour of an exported layer PNG (replaces the bridge's slow Python scan)
// ---------------------------------------------------------------------------

/// Running tally with exactly the bridge's rule: among pixels with the highest
/// alpha seen, the most common RGB wins; ties go to the colour seen first.
pub struct InkTally {
    best_alpha: i32,
    counts: std::collections::HashMap<u32, (u64, u64)>, // rgb -> (count, first_seen)
    order: u64,
    last_key: u32,
    last_valid: bool,
}

impl Default for InkTally {
    fn default() -> Self {
        InkTally { best_alpha: -1, counts: Default::default(), order: 0, last_key: 0, last_valid: false }
    }
}

impl InkTally {
    #[inline]
    pub fn add(&mut self, r: u8, g: u8, b: u8, a: u8) {
        let a = a as i32;
        if a <= 0 {
            return;
        }
        if a > self.best_alpha {
            self.best_alpha = a;
            self.counts.clear();
            self.last_valid = false;
        }
        if a != self.best_alpha {
            return;
        }
        let key = ((r as u32) << 16) | ((g as u32) << 8) | b as u32;
        if self.last_valid && key == self.last_key {
            self.counts.get_mut(&key).unwrap().0 += 1;
            return;
        }
        let order = self.order;
        let e = self.counts.entry(key).or_insert((0, order));
        if e.0 == 0 {
            self.order += 1;
        }
        e.0 += 1;
        self.last_key = key;
        self.last_valid = true;
    }

    /// (r, g, b, alpha) or None if the layer had no visible pixels.
    pub fn result(&self) -> Option<(u8, u8, u8, u8)> {
        if self.best_alpha <= 0 {
            return None;
        }
        let (key, _) = self
            .counts
            .iter()
            .max_by(|(_, (ca, oa)), (_, (cb, ob))| ca.cmp(cb).then(ob.cmp(oa)))?;
        Some(((key >> 16) as u8, (key >> 8) as u8, *key as u8, self.best_alpha as u8))
    }
}

// ---------------------------------------------------------------------------
// Tests: compare against the original engine functions, copied verbatim.
// ---------------------------------------------------------------------------

#[cfg(test)]
mod tests {
    use super::*;

    fn dirs8() -> [(i32, i32); 8] {
        [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
    }
    fn dilate(mask: &[u8], w: u32, h: u32) -> Vec<u8> {
        let mut out = mask.to_vec();
        for y in 0..h as i32 {
            for x in 0..w as i32 {
                let idx = (y as u32 * w + x as u32) as usize;
                if mask[idx] != 0 {
                    out[idx] = 1;
                    continue;
                }
                for (dx, dy) in dirs8() {
                    let nx = x + dx;
                    let ny = y + dy;
                    if nx < 0 || ny < 0 || nx >= w as i32 || ny >= h as i32 {
                        continue;
                    }
                    let nidx = (ny as u32 * w + nx as u32) as usize;
                    if mask[nidx] != 0 {
                        out[idx] = 1;
                        break;
                    }
                }
            }
        }
        out
    }
    fn erode(mask: &[u8], w: u32, h: u32) -> Vec<u8> {
        let mut out = mask.to_vec();
        for y in 0..h as i32 {
            for x in 0..w as i32 {
                let idx = (y as u32 * w + x as u32) as usize;
                if mask[idx] == 0 {
                    out[idx] = 0;
                    continue;
                }
                for (dx, dy) in dirs8() {
                    let nx = x + dx;
                    let ny = y + dy;
                    if nx < 0 || ny < 0 || nx >= w as i32 || ny >= h as i32 {
                        out[idx] = 0;
                        break;
                    }
                    let nidx = (ny as u32 * w + nx as u32) as usize;
                    if mask[nidx] == 0 {
                        out[idx] = 0;
                        break;
                    }
                }
            }
        }
        out
    }
    fn dilate_n(mut m: Vec<u8>, w: u32, h: u32, n: u32) -> Vec<u8> {
        for _ in 0..n {
            m = dilate(&m, w, h);
        }
        m
    }
    fn erode_n(mut m: Vec<u8>, w: u32, h: u32, n: u32) -> Vec<u8> {
        for _ in 0..n {
            m = erode(&m, w, h);
        }
        m
    }
    fn pair_boundary_seed(a: &[u8], b: &[u8], w: u32, h: u32) -> Vec<u8> {
        let mut seed = vec![0u8; (w * h) as usize];
        for y in 0..h as i32 {
            for x in 0..w as i32 {
                let idx = (y as u32 * w + x as u32) as usize;
                if a[idx] == 0 {
                    continue;
                }
                for (dx, dy) in dirs8() {
                    let nx = x + dx;
                    let ny = y + dy;
                    if nx < 0 || ny < 0 || nx >= w as i32 || ny >= h as i32 {
                        continue;
                    }
                    let nidx = (ny as u32 * w + nx as u32) as usize;
                    if b[nidx] != 0 {
                        seed[idx] = 1;
                        break;
                    }
                }
            }
        }
        seed
    }
    /// Original pair rule, full image.
    fn original_trap(a: &[u8], b: &[u8], allow: &[u8], w: u32, h: u32, r: u32) -> Vec<u8> {
        let seed = pair_boundary_seed(a, b, w, h);
        let da = dilate_n(seed, w, h, r);
        (0..a.len()).map(|i| (da[i] != 0 && allow[i] != 0 && a[i] == 0) as u8).collect()
    }

    // Small deterministic PRNG so tests need no crates.
    struct Rng(u64);
    impl Rng {
        fn next(&mut self) -> u64 {
            self.0 ^= self.0 << 13;
            self.0 ^= self.0 >> 7;
            self.0 ^= self.0 << 17;
            self.0
        }
        fn below(&mut self, n: u64) -> u64 {
            self.next() % n.max(1)
        }
    }

    /// Blobby random mask (rectangles + noise) so there are real edges.
    fn random_mask(rng: &mut Rng, w: u32, h: u32, blobs: u32, noise: u64) -> Vec<u8> {
        let mut m = vec![0u8; (w * h) as usize];
        for _ in 0..blobs {
            let x0 = rng.below(w as u64) as u32;
            let y0 = rng.below(h as u64) as u32;
            let x1 = (x0 + 1 + rng.below((w / 2) as u64) as u32).min(w);
            let y1 = (y0 + 1 + rng.below((h / 2) as u64) as u32).min(h);
            for y in y0..y1 {
                for x in x0..x1 {
                    m[(y * w + x) as usize] = 1;
                }
            }
        }
        for v in m.iter_mut() {
            if rng.below(1000) < noise {
                *v ^= 1;
            }
        }
        m
    }

    fn embed(win: Rect, buf: &[u8], w: u32, h: u32) -> Vec<u8> {
        let mut full = vec![0u8; (w * h) as usize];
        let ww = win.width() as usize;
        for y in 0..win.height() as usize {
            let d = (win.y0 as usize + y) * w as usize + win.x0 as usize;
            full[d..d + ww].copy_from_slice(&buf[y * ww..(y + 1) * ww]);
        }
        full
    }

    #[test]
    fn dilate_matches_original() {
        let mut rng = Rng(0x1234_5678_9abc_def0);
        for case in 0..60 {
            let w = 1 + rng.below(70) as u32;
            let h = 1 + rng.below(50) as u32;
            let m = { let nb = 1 + rng.below(4) as u32; random_mask(&mut rng, w, h, nb, 5) };
            let r = rng.below(8) as u32;
            let want = dilate_n(m.clone(), w, h, r);
            let got = box_dilate_window(&m, w, Rect::full(w, h), r);
            assert_eq!(got, want, "case {case} w={w} h={h} r={r}");
        }
    }

    #[test]
    fn erode_matches_original_including_border() {
        let mut rng = Rng(42);
        for case in 0..60 {
            let w = 1 + rng.below(60) as u32;
            let h = 1 + rng.below(60) as u32;
            let m = { let nb = 1 + rng.below(5) as u32; random_mask(&mut rng, w, h, nb, 3) };
            let r = rng.below(5) as u32;
            assert_eq!(box_erode_full(&m, w, h, r), erode_n(m.clone(), w, h, r), "case {case} r={r}");
        }
        // Fully-on image: border pixels must erode away like the original.
        let (w, h) = (9, 7);
        let on = vec![1u8; 63];
        assert_eq!(box_erode_full(&on, w, h, 2), erode_n(on.clone(), w, h, 2));
    }

    #[test]
    fn pair_trap_matches_original() {
        let mut rng = Rng(7);
        let mut nonempty = 0;
        for case in 0..150 {
            let w = 2 + rng.below(80) as u32;
            let h = 2 + rng.below(60) as u32;
            let a = { let nb = 1 + rng.below(3) as u32; random_mask(&mut rng, w, h, nb, 2) };
            let b = { let nb = 1 + rng.below(3) as u32; random_mask(&mut rng, w, h, nb, 2) };
            // Sometimes allow = b, sometimes an eroded key-like mask.
            let allow = if case % 3 == 0 { erode_n(b.clone(), w, h, 1) } else { b.clone() };
            let r = rng.below(7) as u32;
            let want = original_trap(&a, &b, &allow, w, h, r);
            let (ab, bb) = (bbox(&a, w, h), bbox(&b, w, h));
            let got = match (ab, bb) {
                (Some(ab), Some(bb)) => compute_pair_trap(&a, &b, &allow, w, h, ab, bb, r, false)
                    .map(|(win, buf)| embed(win, &buf, w, h))
                    .unwrap_or_else(|| vec![0u8; (w * h) as usize]),
                _ => vec![0u8; (w * h) as usize],
            };
            if want.iter().any(|&v| v != 0) {
                nonempty += 1;
            }
            assert_eq!(got, want, "case {case} w={w} h={h} r={r}");
        }
        assert!(nonempty > 50, "test should exercise real traps, got {nonempty}");
    }

    #[test]
    fn bits_roundtrip() {
        let mut rng = Rng(99);
        for len in [0usize, 1, 63, 64, 65, 1000, 4097] {
            let m: Vec<u8> = (0..len).map(|_| (rng.below(2)) as u8).collect();
            assert_eq!(Bits::pack(&m).unpack(), m);
        }
    }

    /// The bridge's Python rule, transcribed, for comparison.
    fn python_rule(px: &[(u8, u8, u8, u8)]) -> Option<(u8, u8, u8, u8)> {
        let mut best: i32 = -1;
        let mut hits: Vec<((u8, u8, u8), u64)> = Vec::new(); // insertion-ordered dict
        for &(r, g, b, a) in px {
            let a = a as i32;
            if a <= 0 {
                continue;
            }
            if a > best {
                best = a;
                hits.clear();
            }
            if a == best {
                if let Some(e) = hits.iter_mut().find(|e| e.0 == (r, g, b)) {
                    e.1 += 1;
                } else {
                    hits.push(((r, g, b), 1));
                }
            }
        }
        if best <= 0 || hits.is_empty() {
            return None;
        }
        // Python max() returns the first maximal item in insertion order.
        let mut top = hits[0];
        for &h in &hits[1..] {
            if h.1 > top.1 {
                top = h;
            }
        }
        Some((top.0 .0, top.0 .1, top.0 .2, best as u8))
    }

    #[test]
    fn ink_tally_matches_bridge_rule() {
        let mut rng = Rng(5);
        for _ in 0..300 {
            let n = rng.below(200) as usize;
            let palette = 1 + rng.below(4);
            let px: Vec<_> = (0..n)
                .map(|_| {
                    let c = rng.below(palette) as u8;
                    let a = [0u8, 0, 128, 254, 255][rng.below(5) as usize];
                    (c * 40, 255 - c, c, a)
                })
                .collect();
            let mut t = InkTally::default();
            for &(r, g, b, a) in &px {
                t.add(r, g, b, a);
            }
            assert_eq!(t.result(), python_rule(&px), "{px:?}");
        }
    }
}
