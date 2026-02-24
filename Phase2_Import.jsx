#target photoshop
app.bringToFront();

(function () {

  var prevDialogs = app.displayDialogs;
  app.displayDialogs = DialogModes.NO;

  // ======================
  // DEBUG LOG
  // ======================
  var LOG = [];
  function log(s){ LOG.push(String(s)); }
  function flushLog(folder){
    try{
      var f = new File(folder.fsName + "/import_debug_log.txt");
      f.open("w");
      f.encoding = "UTF8";
      f.write(LOG.join("\r\n"));
      f.close();
    }catch(e){}
  }

  // ======================
  // Helpers
  // ======================
  function safeTrim(s){ return String(s).replace(/^\s+|\s+$/g, ""); }
  function sanitizeName(name){ return safeTrim(String(name).replace(/[\/\\:\*\?"<>\|]/g, "_")); }
  function cTID(s){ return charIDToTypeID(s); }
  function sTID(s){ return stringIDToTypeID(s); }

  function hasSelection(doc){
    try { doc.selection.bounds; return true; }
    catch(e){ return false; }
  }

  function resetPsState(doc){
    try { app.displayDialogs = DialogModes.NO; } catch(_) {}
    try { if (doc) app.activeDocument = doc; } catch(_) {}
    try { if (doc) doc.selection.deselect(); } catch(_) {}
    // Avoid accumulating samplers if used anywhere
    try { while (doc && doc.colorSamplers && doc.colorSamplers.length) doc.colorSamplers[0].remove(); } catch(_) {}
  }

  function promoteBackgroundIfNeeded(doc){
    try{
      // If this doc has a background layer, turn it into a normal layer so transparency selection works.
      if (doc.backgroundLayer) {
        doc.backgroundLayer.isBackgroundLayer = false;
      }
    } catch(_) {}
  }

  function selectTransparencyOfActiveLayer(){
    var idChnl = cTID("Chnl");
    var refSel = new ActionReference();
    refSel.putProperty(idChnl, cTID("fsel"));
    var refTrsp = new ActionReference();
    refTrsp.putEnumerated(idChnl, idChnl, cTID("Trsp"));
    var desc = new ActionDescriptor();
    desc.putReference(cTID("null"), refSel);
    desc.putReference(cTID("T   "), refTrsp);
    executeAction(cTID("setd"), desc, DialogModes.NO);
  }

  function selectVectorMask(){
    var desc = new ActionDescriptor();
    var ref = new ActionReference();
    ref.putProperty(cTID("Chnl"), cTID("fsel"));
    desc.putReference(cTID("null"), ref);
    var ref2 = new ActionReference();
    ref2.putEnumerated(cTID("Path"), cTID("Ordn"), sTID("vectorMask"));
    desc.putReference(cTID("T   "), ref2);
    executeAction(cTID("setd"), desc, DialogModes.NO);
  }

  function selectLayerMask(){
    var desc = new ActionDescriptor();
    var ref = new ActionReference();
    ref.putProperty(cTID("Chnl"), cTID("fsel"));
    desc.putReference(cTID("null"), ref);
    var ref2 = new ActionReference();
    ref2.putEnumerated(cTID("Chnl"), cTID("Chnl"), cTID("Msk "));
    desc.putReference(cTID("T   "), ref2);
    executeAction(cTID("setd"), desc, DialogModes.NO);
  }

  function selectLayerShapeBestEffort(doc, label){
    doc.selection.deselect();

    try { selectTransparencyOfActiveLayer(); if(hasSelection(doc)){ log("  ["+label+"] selection=TRANSPARENCY"); return true; } }
    catch(e1){ log("  ["+label+"] transparency err: " + e1); }

    try { doc.selection.deselect(); selectVectorMask(); if(hasSelection(doc)){ log("  ["+label+"] selection=VECTOR_MASK"); return true; } }
    catch(e2){ log("  ["+label+"] vector err: " + e2); }

    try { doc.selection.deselect(); selectLayerMask(); if(hasSelection(doc)){ log("  ["+label+"] selection=LAYER_MASK"); return true; } }
    catch(e3){ log("  ["+label+"] mask err: " + e3); }

    doc.selection.deselect();
    log("  ["+label+"] FAILED selection");
    return false;
  }

  // JSON.parse fallback
  function parseJSON(txt){
    txt = String(txt);
    try { if (typeof JSON !== "undefined" && JSON && JSON.parse) return JSON.parse(txt); } catch(e1){}
    try { return eval("(" + txt + ")"); } catch(e2){
      throw new Error("Could not parse JSON: " + e2);
    }
  }

  function readTextFile(path){
    var f = new File(path);
    if(!f.exists) throw new Error("Missing file: " + path);
    f.open("r");
    f.encoding = "UTF8";
    var t = f.read();
    f.close();
    return t;
  }

  function readTextFileMaybe(pathNoExt) {
    // Try exact, then common extensions
    var candidates = [
      pathNoExt,
      pathNoExt + ".txt",
      pathNoExt + ".log",
      pathNoExt + ".json"
    ];

    for (var i = 0; i < candidates.length; i++) {
      var f = new File(candidates[i]);
      if (f.exists) {
        try {
          f.encoding = "UTF8";
          f.lineFeed = "unix";
          if (f.open("r")) {
            var txt = f.read();
            f.close();
            return { path: f.fsName, text: txt };
          }
        } catch (e) {
          try { if (f.opened) f.close(); } catch(_) {}
          return { path: f.fsName, text: "(FAILED TO READ: " + e + ")" };
        }
      }
    }
    return { path: candidates[0], text: "(MISSING FILE)" };
  }

  function writeCombinedReport(jobFolder) {
    try {
      var folder = (jobFolder instanceof Folder) ? jobFolder : new Folder(jobFolder);
      if (!folder.exists) return;

      var outFile = new File(folder.fsName + "/combined_report.txt");
      outFile.encoding = "UTF8";
      outFile.lineFeed = "unix";
      if (!outFile.open("w")) return;

      function section(title, basePathNoExt) {
        var r = readTextFileMaybe(basePathNoExt);
        outFile.writeln("");
        outFile.writeln("==================================================");
        outFile.writeln(title);
        outFile.writeln("PATH: " + r.path);
        outFile.writeln("==================================================");
        outFile.writeln(r.text);
      }

      outFile.writeln("SMART TRAPPER COMBINED REPORT");
      outFile.writeln("Generated: " + (new Date()).toString());
      outFile.writeln("Folder: " + folder.fsName);

      // Your folder has sometimes no extensions; sometimes .txt/.json exist.
      section("IMPORT DEBUG LOG", folder.fsName + "/import_debug_log");
      section("TRAPPER LOG",       folder.fsName + "/trapper_log");
      section("JOB JSON",          folder.fsName + "/job");     // job or job.json
      section("TRAPS JSON",        folder.fsName + "/traps");   // traps or traps.json
      section("ERROR LEVEL",       folder.fsName + "/errorlevel");

      outFile.close();
      try { log("Wrote combined report: " + outFile.fsName); } catch(_) {}
    } catch (e) {
      try { log("FAILED to write combined report: " + e); } catch(_) {}
    }
  }

  // ---- Cleanup old traps
  function removeOldTrapLayers(container){
    for (var i = container.layers.length - 1; i >= 0; i--){
      var L = container.layers[i];

      if (L.typename === "ArtLayer" && L.name.indexOf("TRAP__") === 0){
        try { L.remove(); } catch(e) {}
        continue;
      }
      if (L.typename === "LayerSet"){
        removeOldTrapLayers(L);
      }
    }
  }

  // ---- Visibility solo (TOP-LEVEL only) for sampling
  function snapshotTopLevelVisibility(doc){
    var snap = [];
    for(var i=0;i<doc.layers.length;i++) snap[i] = doc.layers[i].visible;
    return snap;
  }
  function restoreTopLevelVisibility(doc, snap){
    for(var i=0;i<doc.layers.length;i++){
      try { doc.layers[i].visible = snap[i]; } catch(e){}
    }
  }
  function topLevelAncestor(layer){
    var p = layer;
    while(p && p.parent && p.parent.typename !== "Document") p = p.parent;
    return p;
  }
  function soloLayerTopLevel(doc, layer){
    var snap = snapshotTopLevelVisibility(doc);
    for(var i=0;i<doc.layers.length;i++){
      try { doc.layers[i].visible = false; } catch(e){}
    }
    var anc = topLevelAncestor(layer);
    try { anc.visible = true; } catch(e){}
    try { layer.visible = true; } catch(e){}
    return snap;
  }

  function revealLayerChain(layer){
    var p = layer;
    while(p && p.parent && p.parent.typename !== "Document"){
      try { p.visible = true; } catch(e){}
      p = p.parent;
    }
    try { layer.visible = true; } catch(e){}
  }

  function centerPointFromLayerBounds(layer){
    var b = layer.bounds;
    var L = b[0].as("px");
    var T = b[1].as("px");
    var R = b[2].as("px");
    var B = b[3].as("px");
    if(!(R > L) || !(B > T)) throw new Error("Invalid layer bounds: " + layer.name);
    return [Math.floor((L + R) / 2), Math.floor((T + B) / 2)];
  }

  // ---- Find sample point by scanning inside selection bounds
  function findSamplePointByScan(doc, scanStep){
    if(!hasSelection(doc)) return null;

    var b = doc.selection.bounds;
    var L = Math.floor(b[0].as("px"));
    var T = Math.floor(b[1].as("px"));
    var R = Math.floor(b[2].as("px"));
    var B = Math.floor(b[3].as("px"));

    var tmp = doc.channels.add();
    tmp.name = "__TMP_SEL_SCAN__";
    doc.selection.store(tmp);
    doc.selection.deselect();

    function testPoint(x,y){
      doc.selection.deselect();
      doc.selection.select([[x,y],[x+1,y],[x+1,y+1],[x,y+1]]);
      doc.selection.load(tmp, SelectionType.INTERSECT);
      return hasSelection(doc);
    }

    var found = null;
    for(var y2=T+1; y2<=B-2; y2+=scanStep){
      for(var x2=L+1; x2<=R-2; x2+=scanStep){
        if(testPoint(x2,y2)){ found = [x2,y2]; break; }
      }
      if(found) break;
    }

    doc.selection.deselect();
    try { tmp.remove(); } catch(e){}
    return found;
  }

  // ---- Sample SOURCE ink color (once per source)
  // Returns a SolidColor sampled from center using DOM colorSamplers; on failure returns null.
  function sampleLayerInkColor(doc, layer){
    var step = "init";
    var sampler = null;
    var snap = null;
    var oldActive = null;

    try {
      step = "activate_doc";
      app.activeDocument = doc;

      step = "prep_visibility";
      snap = soloLayerTopLevel(doc, layer);
      oldActive = doc.activeLayer;
      doc.activeLayer = layer;
      revealLayerChain(layer);

      step = "compute_center";
      var b = layer.bounds;
      var left = b[0].as("px"), top = b[1].as("px"), right = b[2].as("px"), bottom = b[3].as("px");
      var x = Math.round((left + right) / 2);
      var y = Math.round((top + bottom) / 2);
      log("  [SAMPLE] center " + layer.name + " @ (" + x + "," + y + ")");

      step = "add_sampler";
      sampler = doc.colorSamplers.add([x, y]);

      step = "read_color";
      var c = sampler.color;
      var out = new SolidColor();
      out.rgb.red = c.rgb.red;
      out.rgb.green = c.rgb.green;
      out.rgb.blue = c.rgb.blue;

      step = "cleanup";
      try { sampler.remove(); } catch (_) {}
      sampler = null;
      restoreTopLevelVisibility(doc, snap);
      try { doc.activeLayer = oldActive; } catch(e){}

      app.foregroundColor = out;
      log("  [SAMPLE] ok " + layer.name);
      return out;

    } catch (e) {
      log("SAMPLE_INK_FAIL step=" + step + " err=" + e + (e.line ? (" line=" + e.line) : ""));
      try { if (sampler) sampler.remove(); } catch (_) {}
      try { if (snap) restoreTopLevelVisibility(doc, snap); } catch (_) {}
      try { if (oldActive) doc.activeLayer = oldActive; } catch (_) {}
      return null;
    }
  }

  // ================================
  // INK COLOR RESOLUTION (NO BLACK TRAPS)
  // ================================
  function makeSolidColorRGB(r,g,b){
    var c = new SolidColor();
    c.rgb.red = r;
    c.rgb.green = g;
    c.rgb.blue = b;
    return c;
  }

  function setForegroundRGB(rgb) {
    var c = makeSolidColorRGB(rgb.r, rgb.g, rgb.b);
    app.foregroundColor = c;
  }

  function getSolidFillRGBFromLayer(layer) {
    // Works for ArtLayer with kind == LayerKind.SOLIDFILL
    try {
      var ref = new ActionReference();
      ref.putIdentifier(charIDToTypeID("Lyr "), layer.id);
      var desc = executeActionGet(ref);

      // adjustment[0].color.{red, green, blue}
      var adjList = desc.getList(stringIDToTypeID("adjustment"));
      if (!adjList || adjList.count === 0) return null;

      var adj0 = adjList.getObjectValue(0);
      var colorDesc = adj0.getObjectValue(stringIDToTypeID("color"));
      if (!colorDesc) return null;

      return {
        r: colorDesc.getDouble(stringIDToTypeID("red")),
        g: colorDesc.getDouble(stringIDToTypeID("green")),
        b: colorDesc.getDouble(stringIDToTypeID("blue"))
      };
    } catch (e) {
      return null;
    }
  }

  function getSolidFillLayerColor(layer){
    try{
      if (!layer) return null;
      if (layer.kind !== LayerKind.SOLIDFILL) return null;
      // Many PS versions expose SOLIDFILL RGB via layer.adjustment = [r,g,b]
      var a = layer.adjustment;
      if (!a || a.length < 3) return null;
      return makeSolidColorRGB(a[0], a[1], a[2]);
    }catch(e){
      return null;
    }
  }

  // Depth-first search for first solid-fill layer within a LayerSet/group
  function findFirstSolidFillLayer(layerSet) {
    for (var i = 0; i < layerSet.layers.length; i++) {
      var lyr = layerSet.layers[i];
      if (lyr.typename === "ArtLayer" && lyr.kind === LayerKind.SOLIDFILL) return lyr;
      if (lyr.typename === "LayerSet") {
        var hit = findFirstSolidFillLayer(lyr);
        if (hit) return hit;
      }
    }
    return null;
  }

  // Fallback pixel sampling
  function trySampleRGBAt(doc, x, y) {
    // This can fail on some PS versions, so always try/catch.
    try {
      var s = doc.colorSamplers.add([x, y]);
      var c = s.color;

      // Convert whatever we got into RGB-ish numbers
      var rgb = null;
      try {
        rgb = { r: c.rgb.red, g: c.rgb.green, b: c.rgb.blue };
      } catch (e1) {
        // If not RGB, let Photoshop convert:
        var tmp = new SolidColor();
        tmp = c; // sometimes works; if not, we give up
        rgb = { r: tmp.rgb.red, g: tmp.rgb.green, b: tmp.rgb.blue };
      }

      s.remove();
      return rgb;
    } catch (e) {
      return null;
    }
  }

  var FALLBACK_RGB_BY_NAME = {
    "Yellow": [255, 217, 0],
    "Orange": [255, 110, 0],
    "Light Blue": [60, 180, 255],
    "Peach Fat": [255, 170, 150],
    "Mint": [120, 230, 190],
    "\"Light\" Purple": [200, 150, 255],
    "Purple FLAT": [120, 60, 200],
    "Blue": [0, 90, 255]
  };

  function getFallbackColorByName(name){
    var rgb = FALLBACK_RGB_BY_NAME[name];
    if (!rgb) return null;
    return makeSolidColorRGB(rgb[0], rgb[1], rgb[2]);
  }

  function sampleInkAtPoint(doc, samplePoint) {
    if (!samplePoint || samplePoint.x == null || samplePoint.y == null) return null;
    return trySampleRGBAt(doc, samplePoint.x, samplePoint.y);
  }

  function getInkRGBForSourceBase(sourceBaseLayer, sourceName, doc) {
    // 1) If it's a SOLIDFILL layer, pull its RGB (best + exact)
    try {
      if (sourceBaseLayer &&
          sourceBaseLayer.typename === "ArtLayer" &&
          sourceBaseLayer.kind === LayerKind.SOLIDFILL) {
        var solidRgb = getSolidFillRGBFromLayer(sourceBaseLayer);
        if (solidRgb) return { rgb: solidRgb, method: "solidfill" };
      }
    } catch (e) {}

    // 2) Sample while source base layer is active (DOM colorSampler, no actions)
    try {
      if (doc && sourceBaseLayer) {
        var snap = soloLayerTopLevel(doc, sourceBaseLayer);
        var oldActive = doc.activeLayer;
        doc.activeLayer = sourceBaseLayer;
        revealLayerChain(sourceBaseLayer);
        var pt = centerPointFromLayerBounds(sourceBaseLayer);
        var s = doc.colorSamplers.add([pt[0], pt[1]]);
        var c = s.color;
        var sampledRgb = { r: c.rgb.red, g: c.rgb.green, b: c.rgb.blue };
        try { s.remove(); } catch(_){}
        restoreTopLevelVisibility(doc, snap);
        try { doc.activeLayer = oldActive; } catch(_){}
        return { rgb: sampledRgb, method: "sampler" };
      }
    } catch (eSampler) {
      log("TRAP_COLOR_FALLBACK reason=sampler_fail source=" + sourceName + " err=" + eSampler + (eSampler.line ? (" line=" + eSampler.line) : ""));
    }

    // 3) Deterministic palette-by-name
    var fb = getFallbackColorByName(sourceName);
    if (fb) {
      log("TRAP_COLOR_FALLBACK reason=name_palette source=" + sourceName);
      return {
        rgb: { r: fb.rgb.red, g: fb.rgb.green, b: fb.rgb.blue },
        method: "fallback"
      };
    }

    // 4) Absolute last resort (visible)
    log("TRAP_COLOR_FALLBACK reason=forced_magenta source=" + sourceName);
    return { rgb: { r: 255, g: 0, b: 255 }, method: "fallback" };
  }

  // ---- Grouping helpers
  function wrapLayerInGroup(doc, layer, groupName){
    var g = doc.layerSets.add();
    g.name = groupName;
    g.move(layer, ElementPlacement.PLACEBEFORE);
    layer.move(g, ElementPlacement.INSIDE);
    return g;
  }

  function findColorGroup(doc, sourceLayerName){
    var want = "COLOR__" + sanitizeName(sourceLayerName);
    function walk(container){
      for(var i=0;i<container.layerSets.length;i++){
        var g = container.layerSets[i];
        if(g.name === want) return g;
        var hit = walk(g);
        if(hit) return hit;
      }
      return null;
    }
    return walk(doc);
  }

  function findArtLayerByName(container, name){
    for(var i=0;i<container.layers.length;i++){
      var L = container.layers[i];
      if(L.typename === "ArtLayer" && L.name === name) return L;
      if(L.typename === "LayerSet"){
        var hit = findArtLayerByName(L, name);
        if(hit) return hit;
      }
    }
    return null;
  }

  function createTrapLayerInSourceGroup(doc, sourceGroup, sourceBaseLayer, trapName){
    var newL = doc.artLayers.add();
    newL.name = trapName;
    newL.move(sourceGroup, ElementPlacement.INSIDE);
    try { newL.move(sourceBaseLayer, ElementPlacement.PLACEBEFORE); } catch(e){}
    return newL;
  }

  function applySourceAppearanceToTrap(trapLayer, sourceLayer){
    try { trapLayer.blendMode = sourceLayer.blendMode; } catch(e){}
    try { trapLayer.opacity = sourceLayer.opacity; } catch(e){}
    try { trapLayer.fillOpacity = sourceLayer.fillOpacity; } catch(e){}
    try { trapLayer.visible = sourceLayer.visible; } catch(e){}
  }

  // ======================
  // ALIGNMENT FIX:
  // Open PNG -> get its alpha bounds (srcL/srcT)
  // Paste into host -> get pasted alpha bounds (dstL/dstT)
  // Translate pasted by (src - dst) -> select alpha -> delete temp
  // ======================
  function selectionFromTrapPngIntoHost_ALIGN_BY_BOUNDS(hostDoc, pngFile){
    resetPsState(hostDoc);

    if(!pngFile || !pngFile.exists){
      log("MISSING trap png: " + (pngFile ? pngFile.fsName : "<null>"));
      return false;
    }

    var trapDoc = null;
    var pasted = null;
    var step = "init";
    try{
      step = "displayDialogs"; log("  STEP: displayDialogs");
      app.displayDialogs = DialogModes.NO;

      step = "open"; log("  STEP: open");
      trapDoc = app.open(pngFile);
      step = "afterOpen"; log("  STEP: afterOpen (layers=" + trapDoc.layers.length + ")");
      step = "promoteBg"; log("  STEP: promoteBg");
      promoteBackgroundIfNeeded(trapDoc);
      step = "activeLayer"; log("  STEP: activeLayer");
      try { trapDoc.activeLayer = trapDoc.layers[0]; } catch(_){}
      step = "selectTransparency"; log("  STEP: selectTransparency");
      step = "trapDeselect"; log("  STEP: trapDeselect");
      trapDoc.selection.deselect();
      step = "trapLoadTransparency"; log("  STEP: trapLoadTransparency");
      selectTransparencyOfActiveLayer();
      step = "trapHasSelection"; log("  STEP: trapHasSelection");
      if(!hasSelection(trapDoc)){
        log("  STEP_FAIL: trap transparency selection empty");
        try { trapDoc.close(SaveOptions.DONOTSAVECHANGES); } catch(_){}
        trapDoc = null;
        resetPsState(hostDoc);
        return false;
      }

      step = "trapBounds"; log("  STEP: trapBounds");
      var sb = trapDoc.selection.bounds;
      var srcL = sb[0].as("px");
      var srcT = sb[1].as("px");

      step = "selectAll"; log("  STEP: selectAll");
      trapDoc.selection.selectAll();
      step = "copy"; log("  STEP: copy");
      trapDoc.selection.copy();

      step = "closeTrap"; log("  STEP: close trap doc");
      trapDoc.close(SaveOptions.DONOTSAVECHANGES);
      trapDoc = null;

      step = "activateHost"; log("  STEP: activateHost");
      app.activeDocument = hostDoc;
      step = "paste"; log("  STEP: paste");
      hostDoc.paste();
      pasted = hostDoc.activeLayer;

      step = "bounds"; log("  STEP: bounds");
      var hb = pasted.bounds;
      var dstL = hb[0].as("px");
      var dstT = hb[1].as("px");

      var dx = srcL - dstL;
      var dy = srcT - dstT;

      step = "translate"; log("  STEP: translate dx=" + dx + " dy=" + dy);
      pasted.translate(dx, dy);

      step = "hostDeselect"; log("  STEP: hostDeselect");
      hostDoc.selection.deselect();
      step = "setHostActivePasted"; log("  STEP: setHostActivePasted");
      hostDoc.activeLayer = pasted;
      step = "selectTransparencyHost"; log("  STEP: selectTransparencyHost");
      selectTransparencyOfActiveLayer();
      step = "hostHasSelection"; log("  STEP: hostHasSelection");
      var ok = hasSelection(hostDoc);

      step = "cleanup"; log("  STEP: cleanup pasted (ok=" + ok + ")");
      try { pasted.remove(); } catch(_){}

      step = "done"; log("  STEP: done");
      return ok;
    } catch(e){
      log("TRAP_FAIL step=" + step + " file=" + pngFile.fsName + " err=" + e + " line=" + ((e && e.line) ? e.line : "n/a"));
      try{ if(trapDoc) trapDoc.close(SaveOptions.DONOTSAVECHANGES); }catch(_){}
      try{ if(pasted) pasted.remove(); }catch(_){}
      resetPsState(hostDoc);
      return false;
    }
  }

  // =======================================================
  // DEBUG OVERLAY IMPORT (AUTO PLACE debug_*.png AT TOP)
  // =======================================================

  function ensureTopDebugGroup(doc){
    var g = null;
    for(var i=0;i<doc.layerSets.length;i++){
      if(doc.layerSets[i].name === "DEBUG__MASKS"){ g = doc.layerSets[i]; break; }
    }
    if(!g){
      g = doc.layerSets.add();
      g.name = "DEBUG__MASKS";
    }
    try { g.move(doc.layers[0], ElementPlacement.PLACEBEFORE); } catch(e){}
    return g;
  }

  function pastePngIntoHostAsLayer_ALIGN_BY_BOUNDS(hostDoc, pngFile, layerName){
    if(!pngFile.exists) return null;

    var d = app.open(pngFile);
    d.activeLayer = d.layers[0];
    d.selection.deselect();

    // Get source alpha bounds (for translation)
    try { selectTransparencyOfActiveLayer(); } catch(e0){}
    var srcL = 0, srcT = 0;
    if(hasSelection(d)){
      var sb = d.selection.bounds;
      srcL = sb[0].as("px");
      srcT = sb[1].as("px");
    }

    d.selection.selectAll();
    d.selection.copy();
    d.close(SaveOptions.DONOTSAVECHANGES);

    app.activeDocument = hostDoc;
    hostDoc.paste();
    var pasted = hostDoc.activeLayer;
    pasted.name = layerName;

    // Translate pasted so its alpha bounds match the source bounds
    hostDoc.selection.deselect();
    hostDoc.activeLayer = pasted;

    try { selectTransparencyOfActiveLayer(); } catch(e1){}
    if(hasSelection(hostDoc)){
      var hb = hostDoc.selection.bounds;
      var dstL = hb[0].as("px");
      var dstT = hb[1].as("px");
      var dx = srcL - dstL;
      var dy = srcT - dstT;
      try { pasted.translate(dx, dy); } catch(eMove){}
    }

    hostDoc.selection.deselect();
    return pasted;
  }

  function listDebugPngs(jobFolder){
    var files = jobFolder.getFiles(function(f){
      if(!(f instanceof File)) return false;
      var n = f.name.toLowerCase();
      if(n.indexOf("debug_") !== 0) return false;
      return n.slice(-4) === ".png";
    });

    files.sort(function(a,b){
      var A = a.name.toLowerCase(), B = b.name.toLowerCase();
      return (A < B) ? -1 : (A > B) ? 1 : 0;
    });

    return files;
  }

  function importDebugMasksToTop(doc, jobFolder){
    var debugFiles = listDebugPngs(jobFolder);
    if(!debugFiles || debugFiles.length === 0){
      log("No debug_*.png files found to import.");
      return;
    }

    var g = ensureTopDebugGroup(doc);

    for(var i=0;i<debugFiles.length;i++){
      var f = debugFiles[i];
      var layerName = "DEBUG__" + f.name.replace(/\.png$/i, "");

      log("Import debug png: " + f.fsName);

      var L = pastePngIntoHostAsLayer_ALIGN_BY_BOUNDS(doc, f, layerName);
      if(!L) continue;

      try { L.move(g, ElementPlacement.INSIDE); } catch(e1){}
      // put newest at top inside group
      try { L.move(g.layers[0], ElementPlacement.PLACEBEFORE); } catch(e2){}

      // overlay-friendly defaults
      try { L.blendMode = BlendMode.NORMAL; } catch(e3){}
      try { L.opacity = 100; } catch(e4){}
      try { L.visible = true; } catch(e5){}
    }

    try { g.move(doc.layers[0], ElementPlacement.PLACEBEFORE); } catch(e6){}
  }

  // ======================
  // MAIN
  // ======================
  var folder = null;

  try{
    if(!documents.length){
      alert("Open your PSD first, then run this importer.");
      return;
    }

    var hostDoc = app.activeDocument;

    // If controller provided folder, use it.
// Otherwise fall back to manual selection.
if ($.global.PHASE2_IMPORT_FOLDER) {
    folder = new Folder($.global.PHASE2_IMPORT_FOLDER);
    log("Using controller-provided folder: " + folder.fsName);
} else {
    folder = Folder.selectDialog("Select JOB folder (contains traps.json + traps/ + debug_*.png)");
}

if(!folder) return;

    log("Folder: " + folder.fsName);

    var trapsObj = parseJSON(readTextFile(folder.fsName + "/traps.json"));
    if(!trapsObj || !trapsObj.traps || trapsObj.traps.length === 0){
      log("No traps found in traps.json");
      flushLog(folder);
      alert("No traps found. See import_debug_log.txt");
      return;
    }

    // Ensure COLOR__ groups exist (wrap visible ArtLayers between KEY and PAPER if needed)
    if(hostDoc.layers.length < 3){
      alert("PSD needs at least 3 top-level layers (KEY top, PAPER bottom, colors in between).");
      return;
    }

    var colorsBottomToTop = [];
    for(var i = hostDoc.layers.length - 2; i >= 1; i--){
      var L = hostDoc.layers[i];
      if(L.typename === "ArtLayer" && L.visible) colorsBottomToTop.push(L);
    }

    for(var c=0;c<colorsBottomToTop.length;c++){
      var base = colorsBottomToTop[c];
      var existing = findColorGroup(hostDoc, base.name);
      if(!existing){
        log("Wrapping missing group for: " + base.name);
        wrapLayerInGroup(hostDoc, base, "COLOR__" + sanitizeName(base.name));
      }
    }

    var imported = 0;

    log("Removing old TRAP__ layers...");
    removeOldTrapLayers(hostDoc);

    var skippedSel = 0;
    var jobFolder = folder;

    for(var t=0; t<trapsObj.traps.length; t++){
      var spec = trapsObj.traps[t]; // {source, target, png}
      log("--- Trap #" + (t+1) + " " + spec.source + " over " + spec.target);
      resetPsState(hostDoc);

      var pngFile = new File(jobFolder.fsName + "/" + spec.png);
      log("  TRAP PNG path: " + pngFile.fsName + " exists=" + pngFile.exists);
      var step = "init";

      try {
        step = "before_import_trap_png";
        log("  STEP: " + step);

        step = "find_sourceGroup";
        log("  STEP: " + step);
        var sourceGroup = findColorGroup(hostDoc, spec.source);
        if(!sourceGroup){
          log("  SKIP: missing COLOR__ group for source: " + spec.source);
          resetPsState(hostDoc);
          continue;
        }

        step = "find_sourceBase";
        log("  STEP: " + step);
        var sourceBase = findArtLayerByName(sourceGroup, spec.source);
        if(!sourceBase){
          log("  SKIP: no base ArtLayer named '" + spec.source + "' inside " + sourceGroup.name);
          resetPsState(hostDoc);
          continue;
        }

        step = "verify_png_exists";
        log("  STEP: " + step);
        if(!pngFile.exists){
          log("  SKIP: missing PNG: " + pngFile.fsName);
          resetPsState(hostDoc);
          continue;
        }

        step = "deselect_before_import";
        log("  STEP: " + step);
        hostDoc.selection.deselect();

        // Build selection aligned to correct pixel coords
        step = "call_importTrapPng";
        log("  STEP: " + step);
        var okSel = selectionFromTrapPngIntoHost_ALIGN_BY_BOUNDS(hostDoc, pngFile);
        step = "after_importTrapPng";
        log("  STEP: " + step);
        if(!okSel){
          log("  SKIP trap (no selection): " + spec.png);
          resetPsState(hostDoc);
          skippedSel++;
          continue;
        }

        step = "create_trap_layer";
        log("  STEP: " + step);
        var trapName = "TRAP__" + sanitizeName(spec.source) + "_over_" + sanitizeName(spec.target);
        var trapLayer = createTrapLayerInSourceGroup(hostDoc, sourceGroup, sourceBase, trapName);
        applySourceAppearanceToTrap(trapLayer, sourceBase);

        step = "fill_trap_selection";
        log("  STEP: " + step);
        var ink = getInkRGBForSourceBase(sourceBase, spec.source, hostDoc);
        var trapColor = makeSolidColorRGB(ink.rgb.r, ink.rgb.g, ink.rgb.b);

        log("TRAP_COLOR source=" + spec.source +
            " rgb=(" + ink.rgb.r + "," + ink.rgb.g + "," + ink.rgb.b + ")" +
            " method=" + ink.method);

        var prevFg = null;
        try {
          prevFg = makeSolidColorRGB(app.foregroundColor.rgb.red, app.foregroundColor.rgb.green, app.foregroundColor.rgb.blue);
        } catch(_ePrev) {}
        app.foregroundColor = trapColor;
        hostDoc.activeLayer = trapLayer;
        hostDoc.selection.fill(trapColor, ColorBlendMode.NORMAL, 100, false);
        if (prevFg) {
          try { app.foregroundColor = prevFg; } catch(_eRestore) {}
        }
        hostDoc.selection.deselect();

        step = "done";
        log("  STEP: " + step);
        imported++;
        log("  Imported: " + trapName + " (in " + sourceGroup.name + ")");
      } catch(eTrap){
        log("TRAP_FAIL step=" + step + " err=" + eTrap + (eTrap.line ? (" line=" + eTrap.line) : ""));
        log("  SKIP trap exception: " + spec.png + " :: " + eTrap);
        resetPsState(hostDoc);
        skippedSel++;
        continue;
      }
    }

    log("=== SUMMARY ===");
    log("Imported: " + imported);
    log("Skipped (selection load fail): " + skippedSel);

    // NEW: auto-import debug overlays
    log("Importing debug_*.png masks to top of stack...");
    importDebugMasksToTop(hostDoc, folder);

    alert("Import complete.\nImported: " + imported + "\n\nSee import_debug_log.txt");

  } catch(eTop){
    log("FATAL: " + eTop);
    alert("Import failed.\nSee import_debug_log.txt in the export folder.");
  } finally {
    try { if(folder) flushLog(folder); } catch(e4){}
    try { if(folder) writeCombinedReport(folder); } catch(e5){}
    try { app.displayDialogs = prevDialogs; } catch(e3) {}
  }

})();
