import json, datetime
G = '/home/claude/work/guide/'
log = json.load(open(G + 'demo_log.json'))
T = {  # value per file type: standard, geometric, overlay, tonal
}
def types_row(std, geo, ovl, ton):
    return f'''<table class="types"><tr><th>Standard poster</th><th>Geometric / flat</th><th>Overlay / Multiply</th><th>Tonal / grayscale</th></tr>
<tr><td>{std}</td><td>{geo}</td><td>{ovl}</td><td>{ton}</td></tr></table>'''
def setting(title, what, when, types, img, caption, extra=''):
    return f'''<section class="page">
<div class="kicker2">4. Settings</div>
<h2>{title}</h2>
<p class="what">{what}</p>
<div class="when"><b>When to change it:</b> {when}</div>
<div class="tlabel">Starting value for each file type</div>
{types}
<figure><img src="{G}{img}"><figcaption>{caption}</figcaption></figure>
{extra}
</section>'''

ON, OFF = '<span class="on">ON</span>', '<span class="off">off</span>'
pages = []
pages.append(f'''<section class="page cover">
<div class="kicker">The Half and Half · screen-print shop</div>
<h1>Smart Trapper</h1>
<p class="sub">How to use it</p>
<ol class="toc">
<li><b>Quick start</b> - trapping a poster in four clicks</li>
<li><b>What kind of file is this?</b> - the four file types</li>
<li><b>What the messages mean</b> - finished, warnings, stopped</li>
<li><b>Every setting, with pictures</b> - what it does and when to change it</li>
<li><b>The optional buttons</b> - Clean Colors and Cut Top Key</li>
<li><b>Installing on the Mac</b> and <b>if something goes wrong</b></li>
</ol>
<p class="note">Every picture in this guide was made by the real Smart Trapper engine on small test drawings
(the knockout / Clean Colors pictures are drawings that explain the idea). Pixels are shown large so you can see them.
Real posters are 300 ppi, so 5 px is about 0.4 mm.</p>
<p class="draft">DRAFT {datetime.date.today():%d %b %Y} - for Sara's review</p>
</section>''')

pages.append(f'''<section class="page">
<h2>1. Quick start</h2>
<div class="two">
<div>
<p><b>Before you start,</b> the poster file should be set up the usual way:</p>
<ul>
<li><b>Top layer = the key</b> (black line work), whatever it is called.</li>
<li><b>Bottom layer = the paper</b> (blank).</li>
<li>The <b>colour layers in between</b>, in printing order (the trapper never changes the order).</li>
<li>RGB, 300 ppi.</li>
</ul>
<ol class="steps">
<li><b>Open the poster</b> in Photoshop and open the Smart Trapper panel (Plugins menu).</li>
<li><b>Pick "What kind of file is this?"</b> at the top of the panel (see 2.). Most posters are <b>Standard poster</b>.</li>
<li><i>Optional:</i> click <b>Clean Colors</b> if the colours have off-colour specks (see 5. The optional buttons).</li>
<li><b>Click the orange Run Trapper button.</b> It does the whole job: knockout, traps, layer groups, import. A big poster takes about a minute.</li>
<li>Read the message at the end (see 3. What the messages mean). <b>"RUN TRAPPER FINISHED"</b> means you're done.</li>
</ol>
<p>Each colour ends up in a <b>COLOR__</b> group with a <b>CLEAN__</b> layer (the colour) and <b>TRAP__</b> layers (the traps).
With all layers on, the poster should look exactly like it did before.</p>
<p><b>Undo:</b> step back in the History panel to before Run Trapper.</p>
</div>
<div class="shots"><img src="{G}shot_picker.png"><img src="{G}shot_actions.png"></div>
</div>
</section>''')

pages.append(f'''<section class="page">
<h2>2. What kind of file is this?</h2>
<p>Picking a type fills in the usual settings for that kind of file. You can still change any setting afterwards -
the panel then says <b>"ADJUSTED from ..."</b>, lists what you changed, and shows a button to put the usual settings back.</p>
<div class="typegrid">
<div><h3>Standard poster</h3><p>Solid flat colours with black line work. <b>Most posters.</b></p><img src="{G}img_trapwidth.png" class="thumb"></div>
<div><h3>Geometric / flat shapes</h3><p>Hard edges, straight lines, sharp corners (e.g. Obey). Square traps keep corners filled; inside corners stay square.</p><img src="{G}img_round.png" class="thumb"></div>
<div><h3>Overlay / Multiply layers</h3><p>Any layer set to <b>Multiply / Darken</b> (or another blend mode), or under 100% opacity. Colours under those layers are kept so the overprint mix still prints.</p><img src="{G}img_overlay.png" class="thumb"></div>
<div><h3>Tonal / grayscale</h3><p>Every colour is a <b>grayscale / textured</b> layer with tones in it (e.g. DMB Fall Tour). No knockout; tones are kept.</p><img src="{G}img_tonal.png" class="thumb"></div>
</div>
<table class="vals"><tr><th></th><th>Standard</th><th>Geometric</th><th>Overlay</th><th>Tonal</th></tr>
<tr><td>Trap width</td><td>5</td><td>5</td><td>5</td><td>5</td></tr>
<tr><td>Round traps</td><td>{ON}</td><td>{OFF}</td><td>{ON}</td><td>{ON}</td></tr>
<tr><td>Smooth traps under the key</td><td>{OFF}</td><td>{ON}</td><td>{OFF}</td><td>{OFF}</td></tr>
<tr><td>Bevel trap corners</td><td>{OFF}</td><td>{OFF}</td><td>{OFF}</td><td>{OFF}</td></tr>
<tr><td>Key traps follow the colour you see</td><td>{OFF}</td><td>{OFF}</td><td>{OFF}</td><td>{OFF}</td></tr>
<tr><td>File has transparent / overlay layers</td><td>{OFF}</td><td>{OFF}</td><td>{ON}</td><td>{OFF}</td></tr>
<tr><td>Tonal inks</td><td>{OFF}</td><td>{OFF}</td><td>{OFF}</td><td>{ON}</td></tr>
<tr><td>Close key halo</td><td>{OFF}</td><td>{OFF}</td><td>{OFF}</td><td>{OFF}</td></tr>
<tr><td>Preflight cleanup / Alpha threshold / Edge bias</td><td colspan="4">{ON} / 90 / 1 for every type</td></tr>
<tr><td>Key trap pullback / Colour trap pullback</td><td colspan="4">1 / 0 for every type</td></tr>
</table>
<p class="small">Not sure? Pick Standard poster. If the file has Multiply / transparent layers, Run Trapper will stop and tell you to pick Overlay.</p>
</section>''')

pages.append('''<section class="page">
<h2>3. What the messages mean</h2>
<p>Run Trapper always ends with one message.</p>
<div class="msg ok"><b>RUN TRAPPER FINISHED</b><br>Done. It also says which file type was used and how many traps were imported.</div>
<div class="msg warn"><b>RUN TRAPPER FINISHED - WITH WARNINGS</b><br>Done, but look at the list under "Please check before printing" - e.g. a colour that didn't get its CLEAN layer, or a trap layer that didn't import.
If you're unsure, click <b>Save Status Snapshot</b> and send it to Sara.</div>
<div class="msg stop"><b>RUN TRAPPER STOPPED - checks</b> + "Nothing in your file has been changed."<br>It found a problem before touching the file. Fix it and click Run Trapper again:</div>
<table class="vals left">
<tr><th>The message says</th><th>What to do</th></tr>
<tr><td>No document is open</td><td>Open the poster first.</td></tr>
<tr><td>Needs at least 3 visible layers</td><td>Key on top, paper at the bottom, colours in between - and visible.</td></tr>
<tr><td>Already has trapper layers (COLOR__ ...)</td><td>This file was trapped already. Open the original file, or step back in History.</td></tr>
<tr><td>The helper program is not running</td><td>Restart the Mac (the helper starts by itself), then try again. Still stuck: tell Sara.</td></tr>
<tr><td>Not RGB / not 300 ppi</td><td>Image &gt; Mode &gt; RGB Color, or Image &gt; Image Size: Resolution 300 (Resample on).</td></tr>
<tr><td>A setting looks wrong</td><td>Fix the setting it names (e.g. Trap width 0), or re-pick the file type.</td></tr>
<tr><td>Has transparent / overlay layers</td><td>Pick <b>Overlay / Multiply layers</b> as the file type.</td></tr>
</table>
<div class="msg stop"><b>RUN TRAPPER STOPPED - Step 1, 2, 3 or 4</b><br>Something went wrong part-way. The message says what was already done to the file.
<b>Step back in the History panel to before Run Trapper</b>, then click <b>Save Status Snapshot</b> and send it to Sara.
"The engine made 0 traps" usually means a setting is off - re-pick the file type and try again.</div>
</section>''')

pages.append(setting('Trap width (px)',
 'How far each colour spreads <b>under</b> the colour above it (and under the key), so a slightly off-register press never shows a white gap. The striped areas are the hidden traps.',
 'Almost never. 5 px at 300 ppi covers our usual press drift (about 5 px). Wider than 12 is flagged as unusual.',
 types_row('5', '5', '5', '5'), 'img_trapwidth.png',
 'Bottom row: the red printed 4 px off. With no trap, or a trap smaller than the drift, a white gap opens up. At 5 px and more it stays closed.'))

pages.append(setting('Round traps (follow own colour)',
 'ON: traps grow the same distance in every direction and stop where they would get closer to open paper than to their own colour, so a trap never wraps round the end of a shape. OFF: square traps.',
 'Leave ON for normal posters (organic shapes). Turn OFF for geometric art with sharp corners: round traps can leave rounded bumps at joints and shave corners there. The Geometric type does this for you.',
 types_row(ON, OFF, ON, ON), 'img_round.png',
 f'Square traps (left) carry the blue round the end of the shape - when the red moves right, a blue tab shows. Round traps stop flush (engine: {log["round"]["off"]} trap px square, {log["round"]["on"]} round).'))

pages.append(setting('Close key halo',
 'Fills a thin paper gap (2 px or less) between a colour and the key with that colour, then traps it under the key as normal. For artwork where the colours don\'t quite reach the line work, so a thin paper outline shows round the key.',
 'Only on files with that problem (e.g. Phish). Leave OFF when the artist meant those thin paper lines (e.g. cream highlight strokes beside the key) - it would fill them. Open paper is never filled.',
 types_row(OFF, OFF, OFF, OFF), 'img_halo.png',
 'The yellow stops 2 px short of the key. OFF: a thin paper line prints between yellow and key. ON: the gap is filled and the yellow traps under the key like the red. (You may see a 1-2 px lip where the fill meets the end of a shape.)'))

pages.append(setting('File has transparent / overlay layers',
 'For files with layers set to Multiply, Darken or another blend mode, or with opacity / fill under 100%. Colours under those layers are kept (the overprint mix is part of the art) and get no trap under them. The overlay layer is still cut back under the key, with the normal trap, and keeps its blend mode.',
 'Whenever the file has such layers - pick the Overlay / Multiply file type. If you forget, Run Trapper stops and tells you.',
 types_row(OFF, OFF, ON, OFF), 'img_overlay.png',
 'A Multiply blue over yellow prints green where they overlap. Treated as solid (middle) the yellow is cut out from under the blue, so the green is lost. With the Overlay type (right) it prints like the artwork.'))

pages.append(setting('Tonal inks (grayscale layers)',
 'For files where every colour is a grayscale / textured layer (tones, soft edges, a stipple key). Inks keep their tones. Traps go only under solid key line work - never under the stipple - and carry the ink\'s own tone. Inks are not knocked out under each other or under the key.',
 'Whenever the colours are grayscale builds - pick the Tonal / grayscale file type. Leave OFF for normal solid-colour files.',
 types_row(OFF, OFF, OFF, ON), 'img_tonal.png',
 'Standard settings (middle) turn every tone into solid ink and lose the light areas. The Tonal type keeps the tones, and when the key prints off (bottom row) the inks carry on under where the line was. On a thin line the two inks share it (each gets half), as in our hand-trapped files.'))

pages.append(setting('Smooth traps under the key',
 'Trims thin slivers ("fingers") of trap under the key where a key line narrows to a point. Every colour always keeps at least 1-2 px of overlap next to itself. Only traps under the key are touched; nothing visible changes.',
 'Optional tidy-up, mostly for geometric art. Harmless either way.',
 types_row(OFF, ON, OFF, OFF), 'img_smooth.png',
 f'Where the key lines taper to a point over paper, the trap gets squeezed into thin slivers. Pink = what smoothing trims ({log["smooth"]["removed"]} px here).'))

pages.append(setting('Bevel trap corners next to paper',
 'Where a trap under the key runs up to a paper gap in the key (e.g. a cream letter stroke cutting through the line work), the end of the trap is cut at an angle instead of a square corner sitting right against the paper.',
 'Only for art like the Frankenstein lettering. Leave OFF on geometric art: it cuts the square inside corners we want to keep (that\'s why the Geometric type has it off).',
 types_row(OFF, OFF, OFF, OFF), 'img_bevel.png',
 f'Pink = trap cut away next to the paper slot ({log["bevel"]["removed"]} px here). Traps straight across a key line keep their full width.'))

pages.append(setting('Key traps follow the colour you see',
 'Under the key, the colour you see right next to the key line is put on top in the trap zone, so <b>that</b> is the colour that shows if the key prints off. A thin sliver (under 3 px) of another colour between them counts as the colour it lies against.',
 'For files where a thin line of one colour runs between a big colour area and the key (e.g. Peteschaw: olive under a thin blue line). Leave OFF on geometric art - on diagonals it can scatter single-pixel dots.',
 types_row(OFF, OFF, OFF, OFF), 'img_follow.png',
 'A 2 px blue line runs between the olive and the key. In register both look the same. When the key prints 4 px off, OFF shows a fat blue band; ON shows olive with the thin blue line, as in the artwork.'))

pages.append(setting('Key trap pullback (px)',
 'When a colour spreads under the key, it stops this many pixels short of the key\'s outer edge next to paper, so the trap can\'t peek out past a thin key line.',
 'Leave at 1. Higher values take more trap away on thin key lines: under this 5 px line, 2 keeps only about a third of the trap.',
 types_row('1', '1', '1', '1'), 'img_keypullback.png',
 f'A 5 px key line with paper below. When the key prints 2 px high, pullback 0 shows a 2 px red line on the paper, 1 shows 1 px, 2 shows none - but 2 also keeps the least trap (engine: {log["keypullback"]["0"]} / {log["keypullback"]["1"]} / {log["keypullback"]["2"]} trap px).'))

pages.append(setting('Colour trap pullback (px)',
 'A trap tucked under another colour stops this many pixels short of that colour\'s open edge (where it meets paper), so a sliver of trap can\'t peek out round small shapes. The last 1 px of overlap is always kept.',
 'Leave at 0. Use 2 only on files with lots of small dots sitting on a colour edge (e.g. Byrne\'s calendar dots). The effect is small.',
 types_row('0', '0', '0', '0'), 'img_colorpullback.png',
 f'A grey dot sitting on the edge of the red. Pink = the trap pixels that pullback 2 holds back from the dot\'s paper edge ({log["colorpullback_removed"]} px on this dot).'))

pages.append(setting('Preflight cleanup, Alpha threshold, Edge bias',
 '<b>Preflight cleanup</b> tidies each colour before trapping. <b>Alpha threshold</b> decides how solid a soft pixel must be to count as ink (90 = about 35%); fainter pixels become paper, the rest solid ink - screens need solid ink. <b>Edge bias</b> grows colours back by 1 px under the key so they always meet it (0 and 1 both mean 1).',
 'Keep Preflight cleanup ON, Alpha threshold 90, Edge bias 1. Lower the threshold (e.g. 30) only if thin soft details are disappearing.',
 types_row('ON / 90 / 1', 'ON / 90 / 1', 'ON / 90 / 1', 'ON / 90 / 1'), 'img_preflight.png',
 'A blurry blue shape with faint specks round it. OFF: every faint speck prints as a solid dot. Threshold 30 keeps more of the soft edge (and some specks); 90 gives a clean solid shape.',
 '<p class="small"><b>Full debug logging</b> currently does nothing - leave it off.</p>'))

pages.append(f'''<section class="page">
<h2>5. The optional buttons</h2>
<div class="two">
<div><h3>Clean Colors</h3>
<p>Refills every solid colour layer (and the key) with its main colour, removing off-colour specks. Shapes and soft edges stay the same. Skips the paper, overlay and grayscale layers.
Use it <b>before</b> Run Trapper when a colour looks speckled. One Ctrl+Z / Cmd+Z undoes it.</p>
<img src="{G}img_cleancolors.png" class="half"></div>
<div><h3>Cut Top Key From Colors</h3>
<p>Cuts the key's shape out of every colour layer underneath. You don't normally need it: <b>Run Trapper already does this</b> as part of the knockout. Blocked on tonal files.</p>
<img src="{G}img_cutkey.png" class="half"></div>
</div>
<h3>What "knockout" means (Run Trapper does it for you)</h3>
<p>Each layer is cut out of the layers underneath it, top to bottom, so colours don't print on top of each other. Run Trapper then adds the traps back as a small overlap.
Overlay layers don't cut (Overlay type), and tonal files are not knocked out at all (Tonal type).</p>
<img src="{G}img_knockout.png" class="wide">
</section>''')

pages.append('''<section class="page">
<h2>6. Installing on the Mac</h2>
<p class="draft">This page will be finished when the install package is built and tested on the Mac.</p>
<ol class="steps">
<li>Double-click <b>Install Smart Trapper</b> on the Desktop.</li>
<li><b>The first time only</b>, the Mac may say it "can't be opened because Apple cannot check it". Click <b>Done</b> (not Move to Trash), then:
<ul><li>open <b>System Settings</b> &gt; <b>Privacy &amp; Security</b>,</li>
<li>scroll down to the message about Smart Trapper and click <b>Open Anyway</b>,</li>
<li>enter your Mac password, then click <b>Open</b>.</li></ul>
This happens because the program isn't registered with Apple (it is our own shop tool). After this once, it opens normally.</li>
<li>Open Photoshop: the panel is under <b>Plugins &gt; Smart Trapper</b>.</li>
<li>The <b>helper</b> (the part that does the trapping) starts by itself whenever the Mac starts. You never need to open it.</li>
</ol>
<h2>If something goes wrong</h2>
<ul>
<li><b>Undo the run:</b> History panel, click the step just before Run Trapper.</li>
<li><b>Send Sara the details:</b> click <b>Save Status Snapshot</b> (bottom of the panel) right after the problem, and send her the file it saves plus a screenshot.</li>
<li><b>Panel missing or blank:</b> quit and reopen Photoshop.</li>
<li><b>"Helper not running":</b> restart the Mac.</li>
<li><b>The settings got messed up:</b> pick the file type again (or click "Put back ... settings").</li>
</ul>
</section>''')

CSS = '''
@page { size: Letter; margin: 0.55in 0.6in; }
body { font-family: "DejaVu Sans", Arial, sans-serif; color: #1d1d1d; font-size: 10.5pt; line-height: 1.38; }
.page { page-break-after: always; }
.page:last-child { page-break-after: auto; }
h1 { font-size: 40pt; margin: 0.9in 0 0 0; color: #c2410c; }
h2 { font-size: 19pt; margin: 0 0 8px 0; color: #c2410c; border-bottom: 2px solid #f0d9c8; padding-bottom: 4px; }
h3 { font-size: 12pt; margin: 8px 0 4px 0; }
.kicker { text-transform: uppercase; letter-spacing: .12em; font-size: 9pt; color: #777; margin-top: .6in; }
.sub { font-size: 18pt; margin: 4px 0 30px 0; color: #444; }
.toc { font-size: 12pt; line-height: 1.9; }
.note { margin-top: 30px; color: #555; font-size: 9.5pt; }
.draft { color: #b91c1c; font-weight: bold; font-size: 9.5pt; }
.what { font-size: 11pt; }
.when { background: #fff7ed; border-left: 4px solid #f59e0b; padding: 6px 10px; margin: 8px 0; }
.tlabel { font-size: 8.5pt; color: #777; text-transform: uppercase; letter-spacing: .06em; margin-top: 10px; }
table { border-collapse: collapse; width: 100%; margin: 4px 0 10px 0; }
th, td { border: 1px solid #ddd; padding: 4px 6px; text-align: center; font-size: 9.5pt; }
th { background: #f5f5f5; }
table.left td, table.left th { text-align: left; }
table.vals td:first-child { text-align: left; }
.on { color: #15803d; font-weight: bold; } .off { color: #888; }
figure { margin: 10px 0 0 0; }
figure img { width: 100%; max-height: 5.6in; object-fit: contain; display: block; margin: 0 auto; }
figcaption { font-size: 9.5pt; color: #444; margin-top: 6px; }
.two { display: flex; gap: 22px; } .two > div { flex: 1; }
.shots { flex: 0 0 2.6in !important; } .shots img { width: 100%; margin-bottom: 10px; border-radius: 6px; }
.steps li { margin-bottom: 6px; }
.typegrid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px 18px; }
.typegrid p { margin: 2px 0 4px 0; font-size: 9.5pt; } .thumb { width: 100%; max-height: 1.35in; object-fit: contain; object-position: left; }
.msg { border-radius: 6px; padding: 7px 10px; margin: 8px 0; }
.msg.ok { background: #ecfdf5; border: 1px solid #86efac; } .msg.warn { background: #fffbeb; border: 1px solid #fcd34d; }
.msg.stop { background: #fef2f2; border: 1px solid #fca5a5; }
.small { font-size: 9pt; color: #555; }
.kicker2 { font-size: 8.5pt; color: #999; text-transform: uppercase; letter-spacing: .08em; margin-bottom: 2px; }
img.half { width: 100%; } .page figure { margin-top: 14px; } img.wide { width: 85%; display: block; margin: 6px auto; }
'''
html = f'<!doctype html><html><head><meta charset="utf-8"><title>Smart Trapper - how to use it</title><style>{CSS}</style></head><body>{"".join(pages)}</body></html>'
open(G + 'guide.html', 'w').write(html); print('pages', len(pages))
