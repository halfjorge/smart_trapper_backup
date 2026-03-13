use anyhow::{Context, Result};
use clap::Parser;
use std::fs::File;
use std::io::BufWriter;
use png::{BitDepth, ColorType, Encoder, PixelDimensions, Unit};
use serde::{Deserialize, Serialize};
use std::collections::{HashMap, VecDeque};
use std::fs;
use std::path::{Path, PathBuf};

fn default_tolerance() -> u32 { 5 }

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

fn read_mask_rgba(path:&Path)->Result<(u32,u32,Vec<u8>)>{
    let img=image::open(path)?.to_rgba8();
    let (w,h)=img.dimensions();
    Ok((w,h,img.into_raw()))
}

fn alpha_to_bit_with_threshold(w:u32,h:u32,rgba:&[u8],alpha_threshold:u32)->Vec<u8>{
    let mut out=vec![0u8;(w*h)as usize];
    let threshold=alpha_threshold.min(255) as u8;
    for i in 0..(w*h)as usize{
        out[i]=if rgba[i*4+3]>=threshold{1}else{0};
    }
    out
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

fn dilate_n(mut mask:Vec<u8>,w:u32,h:u32,steps:u32)->Vec<u8>{
    for _ in 0..steps{
        mask=dilate(&mask,w,h);
    }
    mask
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

fn apply_edge_bias(mut mask:Vec<u8>,w:u32,h:u32,edge_bias_px:i32)->Vec<u8>{
    if edge_bias_px>0{
        for _ in 0..edge_bias_px{
            mask=dilate(&mask,w,h);
        }
    }else if edge_bias_px<0{
        for _ in 0..(-edge_bias_px){
            mask=erode(&mask,w,h);
        }
    }
    mask
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

    // Only permit cleanup growth in/near key regions so artwork interiors don't swell.
    let allow_radius=edge_bias_px.ceil().max(1.0) as u32;
    let allow_mask=dilate_n(key_mask.to_vec(),w,h,allow_radius+1);

    let whole=edge_bias_px.floor() as i32;
    let frac=edge_bias_px-(whole as f32);
    for _ in 0..whole{
        mask=constrained_dilate(&mask,&allow_mask,other_colors_union,w,h);
    }

    let min_neighbors=frac_neighbor_threshold(frac);
    if min_neighbors<=8{
        mask=constrained_selective_dilate(&mask,&allow_mask,other_colors_union,w,h,min_neighbors);
    }
    mask
}

fn any_on(m:&[u8])->bool{ m.iter().any(|&v|v!=0) }

fn write_mask_png(path:&Path,mask:&[u8],w:u32,h:u32,resolution_dpi:f64)->Result<()>{
    let mut raw = vec![0u8; (w as usize) * (h as usize) * 4];
    for y in 0..h{
        for x in 0..w{
            let idx=(y*w+x)as usize;
            let a=if mask[idx]!=0{255}else{0};
            let p = idx * 4;
            raw[p] = 255;
            raw[p + 1] = 255;
            raw[p + 2] = 255;
            raw[p + 3] = a;
        }
    }

    let file = File::create(path)?;
    let writer = BufWriter::new(file);
    let mut enc = Encoder::new(writer, w, h);
    enc.set_color(ColorType::Rgba);
    enc.set_depth(BitDepth::Eight);
    if resolution_dpi > 0.0 {
        let ppm = (resolution_dpi / 0.0254).round().max(1.0) as u32;
        enc.set_pixel_dims(Some(PixelDimensions {
            xppu: ppm,
            yppu: ppm,
            unit: Unit::Meter,
        }));
    }
    let mut png_writer = enc.write_header()?;
    png_writer.write_image_data(&raw)?;
    Ok(())
}

fn dirs8()->[(i32,i32);8]{
    [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]
}

fn edt(mask:&[u8],w:u32,h:u32)->Vec<f32>{
    let n=(w*h)as usize;
    let mut dist=vec![1e9f32;n];
    let mut q=VecDeque::new();

    for i in 0..n{
        if mask[i]!=0{ dist[i]=0.0; q.push_back(i); }
    }

    while let Some(idx)=q.pop_front(){
        let x=(idx as u32%w)as i32;
        let y=(idx as u32/w)as i32;

        for (dx,dy) in [(1,0),(-1,0),(0,1),(0,-1)]{
            let nx=x+dx;
            let ny=y+dy;
            if nx<0||ny<0||nx>=w as i32||ny>=h as i32{continue;}
            let nidx=(ny as u32*w+nx as u32)as usize;
            if dist[nidx]>dist[idx]+1.0{
                dist[nidx]=dist[idx]+1.0;
                q.push_back(nidx);
            }
        }
    }
    dist
}

fn main()->Result<()>{
    let args=Args::parse();

    let job_folder=PathBuf::from(&args.job_folder);
    let job:JobFile=serde_json::from_str(
        &fs::read_to_string(job_folder.join("job.json"))?
    )?;

    let w=job.widthPx;
    let h=job.heightPx;
    let n=(w*h)as usize;

    let trap_px=args.trap_px.unwrap_or(job.tolerance as i32).max(0);
    let use_cleanup=job.preflightCleanup;
    let alpha_threshold=if use_cleanup {
        job.alphaThreshold.max(1)
    } else {
        1
    };
    let edge_bias_px=if use_cleanup { job.edgeBiasPx } else { 0.0 };

    // Load plates in stack order (bottom -> top).
    // job.colors is exported bottom -> top, then KEY sits above all colors.
    let mut plate_names=Vec::new();
    let mut plates=Vec::new();
    let mut cleaned_color_masks:Vec<(String,Vec<u8>)>=Vec::new();

    let mut raw_color_masks:Vec<(String,Vec<u8>)>=Vec::new();
    for c in &job.colors{
        let f=job.files.iter().find(|f|f.name==c.name).unwrap();
        let (mw,mh,rgba)=read_mask_rgba(&job_folder.join(&f.png))?;
        if mw!=w||mh!=h{ anyhow::bail!("mask size mismatch"); }
        let plate=alpha_to_bit_with_threshold(w,h,&rgba,alpha_threshold);
        raw_color_masks.push((c.name.clone(), plate));
    }

    let key_file=job.files.iter()
        .find(|f|f.kind=="KEY" || f.name==job.keyLayerName)
        .context("missing KEY mask file in job.json")?;
    let (kw,kh,key_rgba)=read_mask_rgba(&job_folder.join(&key_file.png))?;
    if kw!=w||kh!=h{ anyhow::bail!("key mask size mismatch"); }
    let key_mask=alpha_to_bit_with_threshold(w,h,&key_rgba,alpha_threshold);

    for i in 0..raw_color_masks.len(){
        let color_name=raw_color_masks[i].0.clone();
        let mut plate=raw_color_masks[i].1.clone();
        if use_cleanup && edge_bias_px!=0.0{
            let mut others_union=vec![0u8;n];
            for j in 0..raw_color_masks.len(){
                if i==j{ continue; }
                let om=&raw_color_masks[j].1;
                for k in 0..n{
                    if om[k]!=0{ others_union[k]=1; }
                }
            }
            plate=apply_edge_bias_key_constrained(plate,w,h,edge_bias_px,&key_mask,&others_union);
        }
        plate_names.push(color_name.clone());
        cleaned_color_masks.push((color_name, plate.clone()));
        plates.push(plate);
    }

    if job.cutTopKey {
        for plate in plates.iter_mut() {
            for i in 0..n {
                if key_mask[i] != 0 {
                    plate[i] = 0;
                }
            }
        }
    }

    plate_names.push(job.keyLayerName.clone());
    plates.push(key_mask);

    // Detect touching boundaries
    let mut pair_boundary:HashMap<(usize,usize),Vec<u8>>=HashMap::new();
    let neigh=dirs8();

    for y in 0..h as i32{
        for x in 0..w as i32{
            let idx=(y as u32*w+x as u32)as usize;

            for (dx,dy) in neigh{
                let nx=x+dx;
                let ny=y+dy;
                if nx<0||ny<0||nx>=w as i32||ny>=h as i32{continue;}
                let nidx=(ny as u32*w+nx as u32)as usize;

                for a in 0..plates.len(){
                    if plates[a][idx]==0{continue;}
                    for b in 0..plates.len(){
                        if a==b{continue;}
                        if plates[b][nidx]==0{continue;}

                        let lower=a.min(b);
                        let upper=a.max(b);
                        pair_boundary.entry((lower,upper))
                            .or_insert_with(||vec![0u8;n])[idx]=1;
                    }
                }
            }
        }
    }

    let traps_dir=job_folder.join("traps");
    if traps_dir.exists(){ fs::remove_dir_all(&traps_dir)?; }
    fs::create_dir_all(&traps_dir)?;

    let clean_masks_dir=job_folder.join("clean_masks");
    if clean_masks_dir.exists(){ fs::remove_dir_all(&clean_masks_dir)?; }
    fs::create_dir_all(&clean_masks_dir)?;

    for (name,mask) in &cleaned_color_masks{
        let file_name=format!("CLEAN__{}.png",sanitize(name));
        write_mask_png(&clean_masks_dir.join(&file_name),mask,w,h,job.resolution)?;
    }

    let mut out=TrapsOut{traps:vec![]};

    for ((lower,upper),_) in pair_boundary{
        let dist=edt(&plates[lower],w,h);
        let mut trap_mask=vec![0u8;n];

        for i in 0..n{
            if plates[upper][i]!=0 && dist[i]<=trap_px as f32{
                trap_mask[i]=1;
            }
        }

        if !any_on(&trap_mask){continue;}

        let src=plate_names[lower].clone();
        let tgt=plate_names[upper].clone();

        let file_name=format!("TRAP__{}_over_{}.png",sanitize(&src),sanitize(&tgt));
        let out_path=traps_dir.join(&file_name);

        write_mask_png(&out_path,&trap_mask,w,h,job.resolution)?;

        out.traps.push(TrapSpec{
            source:src,
            target:tgt,
            png:format!("traps/{}",file_name),
        });
    }

    fs::write(
        job_folder.join("traps.json"),
        serde_json::to_string_pretty(&out)?,
    )?;

    Ok(())
}
