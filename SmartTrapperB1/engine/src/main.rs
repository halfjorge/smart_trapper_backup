#![allow(non_snake_case, dead_code)]

mod fast;

use anyhow::{Context, Result};
use clap::Parser;
use std::fs::File;
use std::io::{BufReader, BufWriter, Write};
use png::{BitDepth, ColorType, Encoder, PixelDimensions, Unit};
use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;
use std::time::Instant;
use std::fs;
use std::path::{Path, PathBuf};

fn default_tolerance() -> u32 { 5 }
fn default_key_trap_pullback() -> u32 { 1 }
fn default_color_trap_pullback() -> u32 { 0 } // older job.json files: unchanged results

#[derive(Parser, Debug)]
#[command(name="smart_trapper_b1", about="Phase 2 trapper (spread-only + paper island removal)")]
struct Args {
    job_folder: String,
    trap_px: Option<i32>,
}

#[derive(Debug, Deserialize)]
struct JobFile {
    docName: String,
    widthPx: u32,
    heightPx: u32,
    resolution: f64,

    #[serde(default="default_tolerance")]
    tolerance: u32,

    #[serde(default)]
    cutTopKey: bool,

    #[serde(default)]
    preflightCleanup: bool,

    #[serde(default)]
    alphaThreshold: u32,

    #[serde(default)]
    edgeBiasPx: f32,

    #[serde(default="default_key_trap_pullback")]
    keyTrapPullbackPx: u32,

    // Rule 10 (no new butt registration): a trap into a colour stops this many
    // px short of any edge where that colour meets something that would not
    // hide the trap (paper, or a colour below the source). 0 = old behaviour.
    #[serde(default="default_color_trap_pullback")]
    colorTrapPullbackPx: u32,

    // "round": traps grow by a circle (same width in every direction), and a
    // trap pixel under another colour is kept only if it is at least as close
    // to its own colour as to any open area where it would show. Missing or
    // anything else = the original square growth (older job.json files).
    #[serde(default)]
    trapShape: String,

    // "Close key halo": paper gaps up to this many px wide between a colour
    // and the key are filled with that colour (artist-error halos around the
    // key line work, e.g. Phish). 0 / missing = off (older job.json files).
    #[serde(default)]
    closeKeyHaloPx: u32,

    keyLayerName: String,
    paperLayerName: String,

    colors: Vec<ColorMeta>,
    files: Vec<FileMeta>,
}

#[derive(Debug, Deserialize)]
struct ColorMeta {
    name: String,
    blendMode: String,
    opacity: f64,
    fillOpacity: f64,
}

#[derive(Debug, Deserialize, Clone)]
struct FileMeta {
    kind: String,
    name: String,
    blendMode: String,
    opacity: f64,
    fillOpacity: f64,
    png: String,
}

#[derive(Debug, Serialize)]
struct TrapSpec {
    source: String,
    target: String,
    png: String,
}

#[derive(Debug, Serialize)]
struct TrapsOut {
    traps: Vec<TrapSpec>,
}

fn sanitize(s:&str)->String{
    s.chars().map(|c| if "/\\:*?\"<>|".contains(c){'_' } else {c}).collect()
}

fn dilate(mask:&[u8],w:u32,h:u32)->Vec<u8>{
    let mut out=mask.to_vec();
    for y in 0..h as i32{
        for x in 0..w as i32{
            let idx=(y as u32*w+x as u32)as usize;
            if mask[idx]!=0{
                out[idx]=1;
                continue;
            }
            for (dx,dy) in dirs8(){
                let nx=x+dx;
                let ny=y+dy;
                if nx<0||ny<0||nx>=w as i32||ny>=h as i32{continue;}
                let nidx=(ny as u32*w+nx as u32)as usize;
                if mask[nidx]!=0{
                    out[idx]=1;
                    break;
                }
            }
        }
    }
    out
}

fn erode(mask:&[u8],w:u32,h:u32)->Vec<u8>{
    let mut out=mask.to_vec();
    for y in 0..h as i32{
        for x in 0..w as i32{
            let idx=(y as u32*w+x as u32)as usize;
            if mask[idx]==0{
                out[idx]=0;
                continue;
            }
            for (dx,dy) in dirs8(){
                let nx=x+dx;
                let ny=y+dy;
                if nx<0||ny<0||nx>=w as i32||ny>=h as i32{
                    out[idx]=0;
                    break;
                }
                let nidx=(ny as u32*w+nx as u32)as usize;
                if mask[nidx]==0{
                    out[idx]=0;
                    break;
                }
            }
        }
    }
    out
}

fn selective_dilate(mask:&[u8],w:u32,h:u32,min_neighbors_on:u8)->Vec<u8>{
    let mut out=mask.to_vec();
    for y in 0..h as i32{
        for x in 0..w as i32{
            let idx=(y as u32*w+x as u32)as usize;
            if mask[idx]!=0{
                out[idx]=1;
                continue;
            }
            let mut on_count=0u8;
            for (dx,dy) in dirs8(){
                let nx=x+dx;
                let ny=y+dy;
                if nx<0||ny<0||nx>=w as i32||ny>=h as i32{continue;}
                let nidx=(ny as u32*w+nx as u32)as usize;
                if mask[nidx]!=0{
                    on_count+=1;
                }
            }
            if on_count>=min_neighbors_on{
                out[idx]=1;
            }
        }
    }
    out
}

fn pair_boundary_seed(a:&[u8],b:&[u8],w:u32,h:u32)->Vec<u8>{
    let mut seed=vec![0u8;(w*h)as usize];
    for y in 0..h as i32{
        for x in 0..w as i32{
            let idx=(y as u32*w+x as u32)as usize;
            if a[idx]==0{ continue; }
            for (dx,dy) in dirs8(){
                let nx=x+dx;
                let ny=y+dy;
                if nx<0||ny<0||nx>=w as i32||ny>=h as i32{continue;}
                let nidx=(ny as u32*w+nx as u32)as usize;
                if b[nidx]!=0{
                    seed[idx]=1;
                    break;
                }
            }
        }
    }
    seed
}

fn constrained_dilate(mask:&[u8],allow:&[u8],block:&[u8],w:u32,h:u32)->Vec<u8>{
    let mut out=mask.to_vec();
    for y in 0..h as i32{
        for x in 0..w as i32{
            let idx=(y as u32*w+x as u32)as usize;
            if mask[idx]!=0{
                out[idx]=1;
                continue;
            }
            if allow[idx]==0 || block[idx]!=0{
                continue;
            }
            for (dx,dy) in dirs8(){
                let nx=x+dx;
                let ny=y+dy;
                if nx<0||ny<0||nx>=w as i32||ny>=h as i32{continue;}
                let nidx=(ny as u32*w+nx as u32)as usize;
                if mask[nidx]!=0{
                    out[idx]=1;
                    break;
                }
            }
        }
    }
    out
}

fn constrained_selective_dilate(mask:&[u8],allow:&[u8],block:&[u8],w:u32,h:u32,min_neighbors_on:u8)->Vec<u8>{
    let mut out=mask.to_vec();
    for y in 0..h as i32{
        for x in 0..w as i32{
            let idx=(y as u32*w+x as u32)as usize;
            if mask[idx]!=0{
                out[idx]=1;
                continue;
            }
            if allow[idx]==0 || block[idx]!=0{
                continue;
            }
            let mut on_count=0u8;
            for (dx,dy) in dirs8(){
                let nx=x+dx;
                let ny=y+dy;
                if nx<0||ny<0||nx>=w as i32||ny>=h as i32{continue;}
                let nidx=(ny as u32*w+nx as u32)as usize;
                if mask[nidx]!=0{
                    on_count+=1;
                }
            }
            if on_count>=min_neighbors_on{
                out[idx]=1;
            }
        }
    }
    out
}

fn frac_neighbor_threshold(frac:f32)->u8{
    if frac<=0.0 { 255 }
    else if frac<0.34 { 4 }
    else if frac<0.67 { 3 }
    else { 2 }
}

fn apply_edge_bias_f32(mut mask:Vec<u8>,w:u32,h:u32,edge_bias_px:f32)->Vec<u8>{
    if edge_bias_px>0.0{
        let whole=edge_bias_px.floor() as i32;
        let frac=edge_bias_px-(whole as f32);
        for _ in 0..whole{
            mask=dilate(&mask,w,h);
        }
        let min_neighbors=frac_neighbor_threshold(frac);
        if min_neighbors<=8{
            mask=selective_dilate(&mask,w,h,min_neighbors);
        }
    }else if edge_bias_px<0.0{
        let amount=(-edge_bias_px).max(0.0);
        let whole=amount.floor() as i32;
        let frac=amount-(whole as f32);
        for _ in 0..whole{
            mask=erode(&mask,w,h);
        }
        let min_neighbors=frac_neighbor_threshold(frac);
        if min_neighbors<=8{
            // Fractional shrink: keep only pixels with at least threshold on-neighbors.
            // Implemented by eroding once then recovering stable core for small fractions.
            let er=erode(&mask,w,h);
            let mut out=mask.clone();
            for y in 0..h as i32{
                for x in 0..w as i32{
                    let idx=(y as u32*w+x as u32)as usize;
                    if mask[idx]==0{ continue; }
                    let mut on_count=0u8;
                    for (dx,dy) in dirs8(){
                        let nx=x+dx;
                        let ny=y+dy;
                        if nx<0||ny<0||nx>=w as i32||ny>=h as i32{continue;}
                        let nidx=(ny as u32*w+nx as u32)as usize;
                        if mask[nidx]!=0{ on_count+=1; }
                    }
                    if on_count<min_neighbors{ out[idx]=er[idx]; }
                }
            }
            mask=out;
        }
    }
    mask
}

fn apply_edge_bias_key_constrained(
    mut mask:Vec<u8>,
    w:u32,
    h:u32,
    edge_bias_px:f32,
    key_mask:&[u8],
    other_colors_union:&[u8],
)->Vec<u8>{
    if edge_bias_px<=0.0{
        return apply_edge_bias_f32(mask,w,h,edge_bias_px);
    }

    // Only permit cleanup growth inside actual key coverage.
    // Do not allow edge bias to expand into paper around the key edge.
    let allow_mask=key_mask.to_vec();

    let whole=edge_bias_px.floor() as i32;
    let frac=edge_bias_px-(whole as f32);
    for _ in 0..whole{
        mask=constrained_dilate(&mask,&allow_mask,other_colors_union,w,h);
    }

    let min_neighbors=frac_neighbor_threshold(frac);
    if min_neighbors<=8{
        mask=constrained_selective_dilate(&mask,&allow_mask,other_colors_union,w,h,min_neighbors);
    }

    // A narrow under-key heal pass helps close tiny white seams without allowing
    // cleanup growth out into paper. This restores the useful effect of the old
    // second bias pass, but keeps it key-constrained inside the engine.
    mask=constrained_selective_dilate(&mask,&allow_mask,other_colors_union,w,h,3);

    mask
}

fn dirs8()->[(i32,i32);8]{
    [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]
}


// ---------------------------------------------------------------------------
// PNG I/O
// ---------------------------------------------------------------------------

/// Decode a mask PNG once. Returns the alpha channel (1 byte per pixel) and,
/// if asked, the layer's ink colour (same rule the bridge used).
fn read_png_alpha(path:&Path, want_color:bool)->Result<(u32,u32,Vec<u8>,Option<(u8,u8,u8,u8)>)>{
    let file=File::open(path).with_context(|| format!("cannot open {}", path.display()))?;
    let decoder=png::Decoder::new(BufReader::new(file));
    let mut reader=decoder.read_info()?;
    let info=reader.info();
    let w=info.width;
    let h=info.height;
    let bit_depth=info.bit_depth;
    let color_type=info.color_type;

    let channels = match color_type {
        ColorType::Rgba => 4usize,
        ColorType::Rgb => 3usize,
        ColorType::GrayscaleAlpha => 2usize,
        ColorType::Grayscale => 1usize,
        _ => anyhow::bail!("unsupported PNG color type {:?} for {}", color_type, path.display()),
    };
    let bps = match bit_depth {
        BitDepth::Eight => 1usize,
        BitDepth::Sixteen => 2usize,
        _ => anyhow::bail!("unsupported PNG bit depth {:?} for {}", bit_depth, path.display()),
    };
    let bpp = channels * bps;

    let mut alpha=vec![0u8;(w as usize)*(h as usize)];
    let mut tally=fast::InkTally::default();
    let mut row_idx=0usize;
    while let Some(row)=reader.next_row()? {
        let data=row.data();
        let base=row_idx*(w as usize);
        for x in 0..(w as usize){
            let p=x*bpp;
            // High byte of each sample (same as the original reader / bridge).
            let (r,g,b,a) = match color_type {
                ColorType::Rgba => (data[p], data[p+bps], data[p+2*bps], data[p+3*bps]),
                ColorType::Rgb => (data[p], data[p+bps], data[p+2*bps], 255u8),
                ColorType::GrayscaleAlpha => (data[p], data[p], data[p], data[p+bps]),
                _ => (data[p], data[p], data[p], 255u8),
            };
            alpha[base+x]=a;
            if want_color { tally.add(r,g,b,a); }
        }
        row_idx+=1;
    }
    Ok((w,h,alpha,if want_color { tally.result() } else { None }))
}

fn threshold(alpha:&[u8], t:u8)->Vec<u8>{
    alpha.iter().map(|&a| (a>=t) as u8).collect()
}

/// Write a white mask PNG. `win` + `buf` describe where the mask is on;
/// everything outside the window is transparent. Uses fast compression.
fn write_mask_png_window(path:&Path, w:u32, h:u32, win:fast::Rect, buf:&[u8], resolution_dpi:f64)->Result<()>{
    let file = File::create(path).with_context(|| format!("cannot write {}", path.display()))?;
    let writer = BufWriter::new(file);
    let mut enc = Encoder::new(writer, w, h);
    enc.set_color(ColorType::Rgba);
    enc.set_depth(BitDepth::Eight);
    enc.set_compression(png::Compression::Fast);
    if resolution_dpi > 0.0 {
        let ppm = (resolution_dpi / 0.0254).round().max(1.0) as u32;
        enc.set_pixel_dims(Some(PixelDimensions { xppu: ppm, yppu: ppm, unit: Unit::Meter }));
    }
    let mut png_writer = enc.write_header()?;
    let mut stream = png_writer.stream_writer()?;
    let mut row = vec![0u8; (w as usize) * 4];
    for px in row.chunks_mut(4) { px[0]=255; px[1]=255; px[2]=255; px[3]=0; }
    let ww = win.width() as usize;
    for y in 0..h{
        let inside = y>=win.y0 && y<win.y1;
        if inside {
            let wy=(y-win.y0) as usize;
            for x in 0..ww {
                row[(win.x0 as usize + x)*4+3] = if buf[wy*ww+x]!=0 {255} else {0};
            }
        }
        stream.write_all(&row)?;
        if inside {
            for x in 0..ww { row[(win.x0 as usize + x)*4+3]=0; }
        }
    }
    stream.finish()?;
    Ok(())
}

fn write_mask_png(path:&Path,mask:&[u8],w:u32,h:u32,resolution_dpi:f64)->Result<()>{
    write_mask_png_window(path,w,h,fast::Rect::full(w,h),mask,resolution_dpi)
}

fn find_file_meta<'a>(job:&'a JobFile,name:&str)->Result<&'a FileMeta>{
    job.files.iter().find(|f|f.name==name).context(format!("missing file meta for {}", name))
}

fn apply_key_cut_in_place(mask:&mut [u8], key_mask:&[u8]){
    for i in 0..mask.len(){
        if key_mask[i] != 0 {
            mask[i] = 0;
        }
    }
}

// ---------------------------------------------------------------------------
// Verification helper:  smart_trapper_b1 --compare-jobs <JOB_A> <JOB_B>
// Checks that two engine runs produced the same traps and clean masks.
// ---------------------------------------------------------------------------

fn compare_jobs(a:&Path, b:&Path)->Result<bool>{
    #[derive(Deserialize)]
    struct T { source:String, target:String, png:String }
    #[derive(Deserialize)]
    struct TO { traps:Vec<T> }
    let ta:TO=serde_json::from_str(&fs::read_to_string(a.join("traps.json"))?)?;
    let tb:TO=serde_json::from_str(&fs::read_to_string(b.join("traps.json"))?)?;
    let mut same=true;
    let la:Vec<_>=ta.traps.iter().map(|t|(t.source.clone(),t.target.clone(),t.png.clone())).collect();
    let lb:Vec<_>=tb.traps.iter().map(|t|(t.source.clone(),t.target.clone(),t.png.clone())).collect();
    if la!=lb {
        println!("DIFFERENT trap list: {} vs {}", la.len(), lb.len());
        same=false;
    }
    let mut files:Vec<String>=la.iter().map(|t|t.2.clone()).collect();
    if let Ok(rd)=fs::read_dir(a.join("clean_masks")) {
        for e in rd.flatten() { files.push(format!("clean_masks/{}", e.file_name().to_string_lossy())); }
    }
    files.sort();
    for f in &files {
        let pa=a.join(f); let pb=b.join(f);
        if !pb.exists() { println!("DIFFERENT: {} missing in second run", f); same=false; continue; }
        let (wa,ha,ma,_)=read_png_alpha(&pa,false)?;
        let (wb,hb,mb,_)=read_png_alpha(&pb,false)?;
        let diff = if (wa,ha)!=(wb,hb) { usize::MAX } else {
            ma.iter().zip(&mb).filter(|(x,y)| (**x!=0)!=(**y!=0)).count()
        };
        if diff==0 { println!("  same      {}", f); }
        else { println!("  DIFFERENT {} ({} pixels)", f, diff); same=false; }
    }
    println!("{}", if same {"RESULT: IDENTICAL"} else {"RESULT: DIFFERENT"});
    Ok(same)
}

// ---------------------------------------------------------------------------

fn main()->Result<()>{
    let raw:Vec<String>=std::env::args().collect();
    if raw.len()==4 && raw[1]=="--compare-jobs" {
        let ok=compare_jobs(Path::new(&raw[2]),Path::new(&raw[3]))?;
        std::process::exit(if ok {0} else {2});
    }

    let args=Args::parse();
    let t0=Instant::now();

    let job_folder=PathBuf::from(&args.job_folder);
    let job:JobFile=serde_json::from_str(
        &fs::read_to_string(job_folder.join("job.json")).context("cannot read job.json")?
    ).context("job.json is not valid")?;

    let w=job.widthPx;
    let h=job.heightPx;
    let n=(w as usize)*(h as usize);

    let trap_px=args.trap_px.unwrap_or(job.tolerance as i32).max(0) as u32;
    let use_cleanup=job.preflightCleanup;
    let alpha_threshold=if use_cleanup {
        job.alphaThreshold.max(1)
    } else {
        1
    }.min(255) as u8;
    // Edge bias only grows colours inside the key's own (soft-edge) coverage. At
    // least 1 px of that is always applied when cleanup is on: client files are
    // usually knocked out a pixel short of the key's soft edge, and without the 1 px
    // the colours never touch the key, so nothing traps under the key lines
    // (Byrne at Edge bias 0: 40% of the key area had colour under it vs 64% at 1).
    // A negative value (deliberate choke) is left as it is.
    let edge_bias_px=if use_cleanup {
        let eb=job.edgeBiasPx;
        if eb>=0.0 && eb<1.0 {
            println!("[{:>6.1}s] edge bias {} raised to 1 (minimum, keeps colours touching the key)", t0.elapsed().as_secs_f32(), eb);
            1.0
        } else { eb }
    } else { 0.0 };
    let key_trap_pullback_px=job.keyTrapPullbackPx;

    // Key: decode once, derive both masks the old engine read separately.
    let key_meta=find_file_meta(&job,&job.keyLayerName)?;
    let (kw,kh,key_alpha,_)=read_png_alpha(&job_folder.join(&key_meta.png),false)?;
    if kw!=w||kh!=h{ anyhow::bail!("mask size mismatch for {}", job.keyLayerName); }
    let key_mask=threshold(&key_alpha,alpha_threshold);
    // Only the cleanup step needs the "any key ink" mask.
    let key_cover_mask=if use_cleanup && edge_bias_px!=0.0 { threshold(&key_alpha,1) } else { Vec::new() };
    drop(key_alpha);
    println!("[{:>6.1}s] key loaded", t0.elapsed().as_secs_f32());

    let color_names:Vec<String>=job.colors.iter().map(|c| c.name.clone()).collect();

    // Colours: decode each PNG exactly once; keep compact copies in memory.
    let mut plates:Vec<fast::Bits>=Vec::new();
    let mut coverage=vec![0u8;n];
    let mut ink:BTreeMap<String,serde_json::Value>=BTreeMap::new();
    for name in &color_names {
        let meta=find_file_meta(&job,name)?;
        let (mw,mh,alpha,color)=read_png_alpha(&job_folder.join(&meta.png),true)?;
        if mw!=w||mh!=h{ anyhow::bail!("mask size mismatch for {}", name); }
        let plate=threshold(&alpha,alpha_threshold);
        drop(alpha);
        for k in 0..n { if plate[k]!=0 { coverage[k]=coverage[k].saturating_add(1); } }
        if let Some((r,g,b,a))=color {
            ink.insert(name.clone(), serde_json::json!({"r":r,"g":g,"b":b,"a":a}));
        }
        plates.push(fast::Bits::pack(&plate));
    }
    println!("[{:>6.1}s] {} colour masks loaded", t0.elapsed().as_secs_f32(), plates.len());

    // Ink colours for the panel. Only written if the panel did not already
    // write them (this replaces the bridge's slow fallback scan).
    let mask_colors_path=job_folder.join("mask_colors.json");
    let existing_ok = fs::read_to_string(&mask_colors_path).ok()
        .and_then(|t| serde_json::from_str::<serde_json::Map<String,serde_json::Value>>(&t).ok())
        .map(|m| m.keys().any(|k| !k.starts_with("__")))
        .unwrap_or(false);
    if !existing_ok && !ink.is_empty() {
        fs::write(&mask_colors_path, serde_json::to_string_pretty(&ink)?)?;
        println!("[{:>6.1}s] mask_colors.json written ({} colours)", t0.elapsed().as_secs_f32(), ink.len());
    }

    let traps_dir=job_folder.join("traps");
    if traps_dir.exists(){ fs::remove_dir_all(&traps_dir)?; }
    fs::create_dir_all(&traps_dir)?;

    let clean_masks_dir=job_folder.join("clean_masks");
    if clean_masks_dir.exists(){ fs::remove_dir_all(&clean_masks_dir)?; }
    fs::create_dir_all(&clean_masks_dir)?;

    // Clean masks (unchanged rule). "Other colours" union comes from the
    // coverage count instead of re-reading every other PNG each time.
    // Close key halo: a paper pixel is part of a halo when it sits in a gap no
    // wider than `halo` px between the key and a colour (distance to key +
    // distance to that colour <= halo + 1.5). It is given to the nearest colour.
    // Open paper is never touched: it has no ink on the far side of the gap.
    let halo=job.closeKeyHaloPx;
    let mut halo_owner:Vec<u8>=Vec::new();   // 0 = none, else colour index + 1
    if halo>0 && !color_names.is_empty() && color_names.len()<255 {
        let cap=halo+1;
        let dk=fast::capped_dist_sq(&key_mask,w as usize,h as usize,cap);
        let far=((cap+1)*(cap+1)) as u16;
        let mut best=vec![far;n];
        halo_owner=vec![0u8;n];
        let mut tmp=Vec::new();
        for (i,p) in plates.iter().enumerate(){
            p.unpack_into(&mut tmp);
            let dc=fast::capped_dist_sq(&tmp,w as usize,h as usize,cap);
            for k in 0..n {
                if coverage[k]!=0 || key_mask[k]!=0 || dk[k]>=far || dc[k]>=far { continue; }
                if dc[k] < best[k] {
                    let gap=(dk[k] as f32).sqrt()+(dc[k] as f32).sqrt();
                    if gap <= halo as f32 + 1.5 { best[k]=dc[k]; halo_owner[k]=(i+1) as u8; }
                }
            }
        }
        let total=halo_owner.iter().filter(|v| **v!=0).count();
        println!("[{:>6.1}s] close key halo ({} px): {} paper px filled", t0.elapsed().as_secs_f32(), halo, total);
    }

    let mut cleans:Vec<fast::Bits>=Vec::new();
    let mut buf=Vec::new();
    for (i, color_name) in color_names.iter().enumerate() {
        plates[i].unpack_into(&mut buf);
        let mut plate=std::mem::take(&mut buf);
        if !halo_owner.is_empty() {
            let id=(i+1) as u8; let mut added=0usize;
            for k in 0..n { if halo_owner[k]==id { plate[k]=1; added+=1; } }
            if added>0 { println!("         key halo: {} +{} px", color_name, added); }
        }
        if use_cleanup && edge_bias_px!=0.0{
            let others_union:Vec<u8>=(0..n).map(|k| (coverage[k] > plate[k]) as u8).collect();
            plate=apply_edge_bias_key_constrained(plate,w,h,edge_bias_px,&key_cover_mask,&others_union);
        }
        let file_name=format!("CLEAN__{}.png",sanitize(color_name));
        write_mask_png(&clean_masks_dir.join(&file_name),&plate,w,h,job.resolution)?;
        if job.cutTopKey { apply_key_cut_in_place(&mut plate, &key_mask); }
        cleans.push(fast::Bits::pack(&plate));
        buf=plate;
    }
    drop(plates);
    drop(coverage);
    drop(halo_owner);
    println!("[{:>6.1}s] clean masks written", t0.elapsed().as_secs_f32());

    // Key target pullback is the same for every source colour: compute once.
    let key_allow=fast::box_erode_full(&key_mask,w,h,key_trap_pullback_px);
    let key_box=fast::bbox(&key_mask,w,h);

    let mut out=TrapsOut{traps:vec![]};

    // Pairwise trap rule (unchanged, boundary-seeded):
    // Trap(A over B) = (dilate(boundary(A touching B), trapPx) & target_allow) & !A
    let mut a=Vec::new();
    let mut b=Vec::new();
    let boxes:Vec<Option<fast::Rect>>=cleans.iter().map(|c|{ c.unpack_into(&mut a); fast::bbox(&a,w,h) }).collect();
    let color_pull=job.colorTrapPullbackPx;
    let round = job.trapShape.eq_ignore_ascii_case("round");
    println!("[{:>6.1}s] trap shape: {}", t0.elapsed().as_secs_f32(), if round {"round (follows own colour)"} else {"square"});
    let mut c=Vec::new();
    let mut b_allow:Vec<u8>=Vec::new();
    for ai in 0..color_names.len(){
        let src=color_names[ai].clone();
        let Some(a_box)=boxes[ai] else { continue };
        cleans[ai].unpack_into(&mut a);
        // Safe zone for traps of this source: pixels at least `color_pull` px
        // away from anything that would leave the trap showing, i.e. from
        // pixels covered by neither the source itself, any colour above it,
        // nor the key. The canvas edge does not count as showing.
        let mut safe:Vec<u8> = Vec::new();
        if color_pull>0 || round {
            let mut hidden:Vec<u8>=a.iter().zip(key_mask.iter()).map(|(x,k)| (*x!=0 || *k!=0) as u8).collect();
            for cj in (ai+1)..color_names.len(){
                cleans[cj].unpack_into(&mut c);
                for k in 0..n { hidden[k]|=c[k]; }
            }
            let showing:Vec<u8>=hidden.iter().map(|v| (*v==0) as u8).collect();
            drop(hidden);
            safe = if color_pull>0 {
                let grown=fast::box_dilate_window(&showing,w,fast::Rect::full(w,h),color_pull);
                grown.iter().map(|v| (*v==0) as u8).collect()
            } else { vec![1u8;n] };
            if round {
                // Keep only pixels at least as close to this colour as to open area,
                // except the first ring next to the colour (distance <= 1.42 px): that
                // ring is always kept so two colours never butt (rule 10). Without it,
                // fine detail / dithered areas lost their overlap wherever a third
                // colour was as close as the trapping colour.
                let d_own=fast::capped_dist_sq(&a,w as usize,h as usize,trap_px);
                let d_open=fast::capped_dist_sq(&showing,w as usize,h as usize,trap_px);
                for k in 0..n { if d_own[k] > d_open[k] && d_own[k] > 2 { safe[k]=0; } }
            }
            if color_pull>0 {
                // Colour trap pullback never removes the first ring (<= 1.42 px) next to
                // the source colour, so pulled-back traps still overlap by 1 px instead
                // of butting (rule 10). Only the rest of the trap is pulled back.
                let d_own=fast::capped_dist_sq(&a,w as usize,h as usize,2);
                for k in 0..n { if d_own[k] <= 2 { safe[k]=1; } }
            }
        }
        for bi in (ai+1)..=color_names.len(){
            let is_key = bi==color_names.len();
            let tgt = if is_key { job.keyLayerName.clone() } else { color_names[bi].clone() };
            let b_box = if is_key { key_box } else { boxes[bi] };
            let Some(b_box)=b_box else { continue };
            let (bm,allow):(&[u8],&[u8]) = if is_key {
                (&key_mask,&key_allow)
            } else {
                cleans[bi].unpack_into(&mut b);
                if color_pull>0 || round {
                    b_allow.clear();
                    b_allow.extend(b.iter().zip(safe.iter()).map(|(x,s)| x & s));
                    (&b,&b_allow)
                } else { (&b,&b) }
            };
            let Some((win,trap))=fast::compute_pair_trap(&a,bm,allow,w,h,a_box,b_box,trap_px,round) else { continue };

            let file_name=format!("TRAP__{}_over_{}.png",sanitize(&src),sanitize(&tgt));
            write_mask_png_window(&traps_dir.join(&file_name),w,h,win,&trap,job.resolution)?;

            out.traps.push(TrapSpec{
                source:src.clone(),
                target:tgt,
                png:format!("traps/{}",file_name),
            });
        }
    }
    println!("[{:>6.1}s] {} traps written", t0.elapsed().as_secs_f32(), out.traps.len());

    fs::write(
        job_folder.join("traps.json"),
        serde_json::to_string_pretty(&out)?,
    )?;

    println!("Done in {:.1}s", t0.elapsed().as_secs_f32());
    Ok(())
}
