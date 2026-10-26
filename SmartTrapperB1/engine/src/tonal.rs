// "Tonal inks (grayscale layers)" mode (Sara, 2026-10-26, from the DMB Fall Tour 2026 seps).
// Off / missing in job.json = the normal engine, unchanged. On: every colour is one ink whose TONE is in
// its alpha (grain, soft streaks), and the key is solid line work plus a stipple texture with holes.
//
//  - an ink is every pixel with any tone (alpha > 0), not just pixels over the alpha threshold
//  - traps go ONLY under solid key line work: key alpha 255, opened (cross, 2x) to drop the stipple, and
//    1 px back from any non-solid key (line edges, paper specks inside lines) - plus the soft anti-aliased
//    edge of a line on the ink side (key >= 50%, within 2 px of the ink, touching line work); otherwise a
//    2 px key shift opens a hairline there
//  - square growth, trap_px steps, all inks at once, so a line between two inks is split down the middle
//  - each trap pixel copies the ink's tone from the pixel mirrored across the ink edge (same distance
//    inside), falling back to the nearest ink pixel
//  - CLEAN = the ink's original tones, untouched; no ink-to-ink traps (left as is, agreed 2026-10-26);
//    the solid-ink extras (halo, round, smooth, bevel, follow-visible, pullback) are not used
// Outputs are the same files as the normal engine: mask_colors.json, clean_masks/, traps/, traps.json.
use super::*;

fn erode_cross(m: &[u8], w: usize, h: usize) -> Vec<u8> {
    let mut o = vec![0u8; m.len()];
    for y in 0..h {
        for x in 0..w {
            let k = y * w + x;
            if m[k] == 0 { continue; }
            let up = y > 0 && m[k - w] != 0;
            let dn = y + 1 < h && m[k + w] != 0;
            let lf = x > 0 && m[k - 1] != 0;
            let rt = x + 1 < w && m[k + 1] != 0;
            o[k] = (up && dn && lf && rt) as u8;
        }
    }
    o
}

fn dilate_cross(m: &[u8], w: usize, h: usize) -> Vec<u8> {
    let mut o = m.to_vec();
    for y in 0..h {
        for x in 0..w {
            let k = y * w + x;
            if m[k] != 0 { continue; }
            if (y > 0 && m[k - w] != 0) || (y + 1 < h && m[k + w] != 0)
                || (x > 0 && m[k - 1] != 0) || (x + 1 < w && m[k + 1] != 0) { o[k] = 1; }
        }
    }
    o
}

/// 3x3 square erosion (pixels outside the image count as off, like scipy's default).
fn erode_sq(m: &[u8], w: usize, h: usize) -> Vec<u8> {
    let mut o = vec![0u8; m.len()];
    for y in 1..h.saturating_sub(1) {
        for x in 1..w.saturating_sub(1) {
            let k = y * w + x;
            if m[k] == 0 { continue; }
            let mut all = true;
            'n: for dy in [-1i64, 0, 1] {
                for dx in [-1i64, 0, 1] {
                    if m[(k as i64 + dy * w as i64 + dx) as usize] == 0 { all = false; break 'n; }
                }
            }
            o[k] = all as u8;
        }
    }
    o
}

/// 3x3 square dilation.
fn dilate_sq(m: &[u8], w: usize, h: usize) -> Vec<u8> {
    let mut o = m.to_vec();
    for y in 0..h {
        for x in 0..w {
            let k = y * w + x;
            if m[k] != 0 { continue; }
            let y0 = y.saturating_sub(1); let y1 = (y + 1).min(h - 1);
            let x0 = x.saturating_sub(1); let x1 = (x + 1).min(w - 1);
            'n: for yy in y0..=y1 {
                for xx in x0..=x1 {
                    if m[yy * w + xx] != 0 { o[k] = 1; break 'n; }
                }
            }
        }
    }
    o
}

/// Write a white PNG whose alpha is `alpha` (tones kept, not 0/255).
fn write_alpha_png(path: &Path, w: u32, h: u32, alpha: &[u8], resolution_dpi: f64) -> Result<()> {
    let file = File::create(path).with_context(|| format!("cannot write {}", path.display()))?;
    let mut enc = Encoder::new(BufWriter::new(file), w, h);
    enc.set_color(ColorType::Rgba);
    enc.set_depth(BitDepth::Eight);
    enc.set_compression(png::Compression::Fast);
    if resolution_dpi > 0.0 {
        let ppm = (resolution_dpi / 0.0254).round().max(1.0) as u32;
        enc.set_pixel_dims(Some(PixelDimensions { xppu: ppm, yppu: ppm, unit: Unit::Meter }));
    }
    let mut pw = enc.write_header()?;
    let mut stream = pw.stream_writer()?;
    let mut row = vec![255u8; (w as usize) * 4];
    for y in 0..h as usize {
        for x in 0..w as usize { row[x * 4 + 3] = alpha[y * w as usize + x]; }
        stream.write_all(&row)?;
    }
    stream.finish()?;
    Ok(())
}

pub fn run(job: &JobFile, job_folder: &Path, trap_px: u32, t0: Instant) -> Result<()> {
    let (wu, hu) = (job.widthPx, job.heightPx);
    let (w, h) = (wu as usize, hu as usize);
    let n = w * h;
    println!("[{:>6.1}s] tonal inks mode ON: traps only under solid key line work, tone carried from the ink edge, trap {} px",
        t0.elapsed().as_secs_f32(), trap_px);

    let key_meta = find_file_meta(job, &job.keyLayerName)?;
    let (kw, kh, key, _) = read_png_alpha(&job_folder.join(&key_meta.png), false)?;
    if kw != wu || kh != hu { anyhow::bail!("mask size mismatch for {}", job.keyLayerName); }

    let names: Vec<String> = job.colors.iter().map(|c| c.name.clone()).collect();
    if names.len() > 250 { anyhow::bail!("too many colours for tonal mode"); }
    let mut alphas: Vec<Vec<u8>> = Vec::new();
    let mut lab = vec![0u8; n];                  // top-most ink with any tone (1-based), 0 = none
    let mut ink: BTreeMap<String, serde_json::Value> = BTreeMap::new();
    for (i, name) in names.iter().enumerate() {
        let meta = find_file_meta(job, name)?;
        let (mw, mh, a, color) = read_png_alpha(&job_folder.join(&meta.png), true)?;
        if mw != wu || mh != hu { anyhow::bail!("mask size mismatch for {}", name); }
        for k in 0..n { if a[k] > 0 { lab[k] = (i + 1) as u8; } }
        if let Some((r, g, b, al)) = color { ink.insert(name.clone(), serde_json::json!({"r":r,"g":g,"b":b,"a":al})); }
        alphas.push(a);
    }
    println!("[{:>6.1}s] {} tonal inks loaded", t0.elapsed().as_secs_f32(), alphas.len());
    let mask_colors_path = job_folder.join("mask_colors.json");
    let existing_ok = fs::read_to_string(&mask_colors_path).ok()
        .and_then(|t| serde_json::from_str::<serde_json::Map<String, serde_json::Value>>(&t).ok())
        .map(|m| m.keys().any(|k| !k.starts_with("__")))
        .unwrap_or(false);
    if !existing_ok && !ink.is_empty() {
        fs::write(&mask_colors_path, serde_json::to_string_pretty(&ink)?)?;
    }

    // where a trap may go: solid line work (stipple removed), 1 px back from non-solid key
    let solid: Vec<u8> = key.iter().map(|&k| (k == 255) as u8).collect();
    let lines = {
        let e = erode_cross(&erode_cross(&solid, w, h), w, h);
        dilate_cross(&dilate_cross(&e, w, h), w, h)
    };
    let lines_in = erode_sq(&lines, w, h);
    let lines_out = dilate_sq(&lines, w, h);
    let inkany: Vec<u8> = lab.iter().map(|&l| (l > 0) as u8).collect();
    let near_ink = dilate_sq(&dilate_sq(&inkany, w, h), w, h);
    let mut allowed = vec![0u8; n];
    let mut soft_px = 0usize;
    for k in 0..n {
        if lab[k] != 0 { continue; }
        if lines_in[k] != 0 { allowed[k] = 1; }
        else if key[k] >= 128 && near_ink[k] != 0 && lines_out[k] != 0 { allowed[k] = 1; soft_px += 1; }
    }
    drop((solid, lines, lines_in, lines_out, near_ink, inkany));
    println!("[{:>6.1}s] trap zone: {} px of solid key line work ({} on the soft line edge next to an ink)",
        t0.elapsed().as_secs_f32(), allowed.iter().filter(|&&a| a != 0).count(), soft_px);

    // simultaneous square growth: each free pixel joins the ink with most 3x3 neighbours (ties: lower ink)
    let ninks = names.len();
    let mut own = lab.clone();
    for _step in 0..trap_px {
        let mut assign: Vec<(usize, u8)> = Vec::new();
        for y in 0..h {
            for x in 0..w {
                let k = y * w + x;
                if allowed[k] == 0 || own[k] != 0 { continue; }
                let mut counts = [0u8; 256];
                let y0 = y.saturating_sub(1); let y1 = (y + 1).min(h - 1);
                let x0 = x.saturating_sub(1); let x1 = (x + 1).min(w - 1);
                for yy in y0..=y1 { for xx in x0..=x1 { let o = own[yy * w + xx]; if o != 0 { counts[o as usize] += 1; } } }
                let (mut best, mut bestn) = (0u8, 0u8);
                for c in 1..=ninks { if counts[c] > bestn { bestn = counts[c]; best = c as u8; } }
                if best != 0 { assign.push((k, best)); }
            }
        }
        for (k, b) in assign { own[k] = b; }
    }

    // tone: mirror across the ink edge, fallback = nearest ink pixel (search radius covers the trap width)
    let rad = (trap_px as i64) * 2 + 2;
    let traps_dir = job_folder.join("traps");
    if traps_dir.exists() { fs::remove_dir_all(&traps_dir)?; }
    fs::create_dir_all(&traps_dir)?;
    let clean_dir = job_folder.join("clean_masks");
    if clean_dir.exists() { fs::remove_dir_all(&clean_dir)?; }
    fs::create_dir_all(&clean_dir)?;
    let mut out = TrapsOut { traps: Vec::new() };
    let (mut mirrored, mut fallback) = (0usize, 0usize);
    for (i, name) in names.iter().enumerate() {
        let id = (i + 1) as u8;
        let a = &alphas[i];
        let mut t = vec![0u8; n];
        let mut tp = 0usize;
        for y in 0..h as i64 {
            for x in 0..w as i64 {
                let k = (y as usize) * w + x as usize;
                if own[k] != id || lab[k] != 0 { continue; }
                // nearest pixel of this ink (smallest distance; ties: leftmost, then topmost - the same
                // choice as the approved DMB Tour run, so the grain matches it)
                let (mut bd, mut q) = (i64::MAX, (0i64, 0i64));
                for dx in -rad..=rad {
                    let xx = x + dx; if xx < 0 || xx >= w as i64 { continue; }
                    for dy in -rad..=rad {
                        let yy = y + dy; if yy < 0 || yy >= h as i64 { continue; }
                        if lab[(yy as usize) * w + xx as usize] != id { continue; }
                        let d = dy * dy + dx * dx;
                        if d < bd { bd = d; q = (yy, xx); }
                    }
                }
                if bd == i64::MAX { continue; }
                let (sy, sx) = (2 * q.0 - y, 2 * q.1 - x);
                let src = if sy >= 0 && sy < h as i64 && sx >= 0 && sx < w as i64 && lab[(sy as usize) * w + sx as usize] == id {
                    mirrored += 1; (sy as usize) * w + sx as usize
                } else { fallback += 1; (q.0 as usize) * w + q.1 as usize };
                t[k] = a[src];
                if t[k] > 0 { tp += 1; }
            }
        }
        write_alpha_png(&clean_dir.join(format!("CLEAN__{}.png", sanitize(name))), wu, hu, a, job.resolution)?;
        let file_name = format!("TRAP__{}_over_{}.png", sanitize(name), sanitize(&job.keyLayerName));
        write_alpha_png(&traps_dir.join(&file_name), wu, hu, &t, job.resolution)?;
        out.traps.push(TrapSpec { source: name.clone(), target: job.keyLayerName.clone(), png: format!("traps/{}", file_name) });
        println!("[{:>6.1}s] {} under {}: {} trap px (tone carried)", t0.elapsed().as_secs_f32(), name, job.keyLayerName, tp);
    }
    println!("[{:>6.1}s] tone source: {} px mirrored from inside the ink, {} px from the nearest ink pixel",
        t0.elapsed().as_secs_f32(), mirrored, fallback);
    fs::write(job_folder.join("traps.json"), serde_json::to_string_pretty(&out)?)?;
    println!("[{:>6.1}s] {} traps written (tonal)", t0.elapsed().as_secs_f32(), out.traps.len());
    println!("Done in {:.1}s", t0.elapsed().as_secs_f32());
    Ok(())
}
