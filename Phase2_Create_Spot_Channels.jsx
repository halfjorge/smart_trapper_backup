#target photoshop
app.bringToFront();

(function () {
  var prevDialogs = app.displayDialogs;
  var LOG_LINES = [];
  var LOG_FILE_PATH = null;
  var RUN_START_MS = new Date().getTime();

  function cTID(s){ return charIDToTypeID(s); }

  function log(msg){
    var now = new Date();
    var stamp =
      ("0" + now.getHours()).slice(-2) + ":" +
      ("0" + now.getMinutes()).slice(-2) + ":" +
      ("0" + now.getSeconds()).slice(-2);
    LOG_LINES.push("[" + stamp + "] " + String(msg));
  }

  function safeName(s){
    return String(s).replace(/[\\\/:\*\?"<>\|]/g, "_");
  }

  function writeTroubleshootingLog(doc){
    var now = new Date();
    var stamp =
      now.getFullYear() +
      ("0" + (now.getMonth() + 1)).slice(-2) +
      ("0" + now.getDate()).slice(-2) + "_" +
      ("0" + now.getHours()).slice(-2) +
      ("0" + now.getMinutes()).slice(-2) +
      ("0" + now.getSeconds()).slice(-2);
    var fileName = "spot_channel_debug_" + stamp + ".txt";
    var outFile = null;

    try{
      outFile = new File(new File($.fileName).parent.fsName + "/" + fileName);
    }catch(e0){}

    if(!outFile){
      try{
        outFile = new File(Folder.desktop.fsName + "/" + fileName);
      }catch(e1){}
    }

    if(!outFile) return null;

    outFile.encoding = "UTF8";
    outFile.lineFeed = "windows";
    if(!outFile.open("w")) return null;
    outFile.write(LOG_LINES.join("\r\n"));
    outFile.close();
    LOG_FILE_PATH = outFile.fsName;
    return LOG_FILE_PATH;
  }

  function hasSelection(doc){
    try { doc.selection.bounds; return true; } catch(e){ return false; }
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

  function restoreCompositeChannels(doc){
    try { doc.activeChannels = doc.componentChannels; } catch(e){}
  }

  function msSince(startMs){
    return (new Date().getTime() - startMs) + "ms";
  }

  function selectBoundsRectangle(doc, bounds){
    var L = Math.floor(bounds[0].as("px"));
    var T = Math.floor(bounds[1].as("px"));
    var R = Math.floor(bounds[2].as("px"));
    var B = Math.floor(bounds[3].as("px"));
    if(L >= R || T >= B) return false;
    doc.selection.select([[L, T], [R, T], [R, B], [L, B]]);
    return hasSelection(doc);
  }

  function trySelectLayerPixelsOrBounds(doc, layer, contextLabel){
    doc.selection.deselect();
    try { selectTransparencyOfActiveLayer(); } catch(e0){}
    if(hasSelection(doc)) return "transparency";

    try{
      var bounds = layer.bounds;
      if(selectBoundsRectangle(doc, bounds)){
        log("FALLBACK BOUNDS SELECTION: " + contextLabel + " -> " + layer.name);
        return "bounds";
      }
    }catch(e1){}

    return null;
  }

  function addProbePoint(points, seen, x, y, maxX, maxY){
    x = Math.max(0, Math.min(maxX, Math.floor(x)));
    y = Math.max(0, Math.min(maxY, Math.floor(y)));
    var key = x + "," + y;
    if(seen[key]) return;
    seen[key] = true;
    points.push([x, y]);
  }

  function findSamplePointByCandidates(doc){
    if(!hasSelection(doc)) return null;

    var b = doc.selection.bounds;
    var rawL = Math.floor(b[0].as("px"));
    var rawT = Math.floor(b[1].as("px"));
    var rawR = Math.floor(b[2].as("px"));
    var rawB = Math.floor(b[3].as("px"));
    var maxX = Math.max(0, Math.floor(doc.width.as("px")) - 1);
    var maxY = Math.max(0, Math.floor(doc.height.as("px")) - 1);
    var L = Math.max(0, rawL);
    var T = Math.max(0, rawT);
    var R = Math.min(maxX + 1, rawR);
    var B = Math.min(maxY + 1, rawB);

    log("SCAN BOUNDS RAW: " + [rawL, rawT, rawR, rawB].join(","));
    log("SCAN BOUNDS CLAMPED: " + [L, T, R, B].join(","));

    if(L >= R || T >= B) return null;

    var midX = Math.floor((L + R - 1) / 2);
    var midY = Math.floor((T + B - 1) / 2);
    var q1X = Math.floor((L + midX) / 2);
    var q3X = Math.floor((midX + R - 1) / 2);
    var q1Y = Math.floor((T + midY) / 2);
    var q3Y = Math.floor((midY + B - 1) / 2);
    var pts = [];
    var seen = {};
    var tmp = null;

    addProbePoint(pts, seen, midX, midY, maxX, maxY);
    addProbePoint(pts, seen, q1X, q1Y, maxX, maxY);
    addProbePoint(pts, seen, q3X, q1Y, maxX, maxY);
    addProbePoint(pts, seen, q1X, q3Y, maxX, maxY);
    addProbePoint(pts, seen, q3X, q3Y, maxX, maxY);
    addProbePoint(pts, seen, L + 1, T + 1, maxX, maxY);
    addProbePoint(pts, seen, R - 2, T + 1, maxX, maxY);
    addProbePoint(pts, seen, L + 1, B - 2, maxX, maxY);
    addProbePoint(pts, seen, R - 2, B - 2, maxX, maxY);
    addProbePoint(pts, seen, midX, T + 1, maxX, maxY);
    addProbePoint(pts, seen, midX, B - 2, maxX, maxY);
    addProbePoint(pts, seen, L + 1, midY, maxX, maxY);
    addProbePoint(pts, seen, R - 2, midY, maxX, maxY);

    try{
      tmp = doc.channels.add();
      tmp.name = "__TMP_SEL_SCAN__";
      doc.selection.store(tmp);
      doc.selection.deselect();
      restoreCompositeChannels(doc);

      for(var i = 0; i < pts.length; i++){
        var p = pts[i];
        doc.selection.deselect();
        doc.selection.select([[p[0], p[1]], [p[0] + 1, p[1]], [p[0] + 1, p[1] + 1], [p[0], p[1] + 1]]);
        doc.selection.load(tmp, SelectionType.INTERSECT);
        if(hasSelection(doc)){
          log("SAMPLE PROBE HIT: (" + p[0] + "," + p[1] + ")");
          return p;
        }
      }

      log("SAMPLE PROBE MISS: no hit in candidate points");
      return null;
    } finally {
      try { doc.selection.deselect(); } catch(e0){}
      try { if(tmp) tmp.remove(); } catch(e1){}
      try { restoreCompositeChannels(doc); } catch(e2){}
    }
  }

  function findSamplePointByScan(doc, scanStep){
    if(!hasSelection(doc)) return null;

    var b = doc.selection.bounds;
    var rawL = Math.floor(b[0].as("px"));
    var rawT = Math.floor(b[1].as("px"));
    var rawR = Math.floor(b[2].as("px"));
    var rawB = Math.floor(b[3].as("px"));
    var maxX = Math.max(0, Math.floor(doc.width.as("px")) - 1);
    var maxY = Math.max(0, Math.floor(doc.height.as("px")) - 1);
    var L = Math.max(0, rawL);
    var T = Math.max(0, rawT);
    var R = Math.min(maxX + 1, rawR);
    var B = Math.min(maxY + 1, rawB);

    if(L >= R || T >= B) return null;

    var tmp = null;
    try{
      tmp = doc.channels.add();
      tmp.name = "__TMP_SEL_SCAN__";
      doc.selection.store(tmp);
      doc.selection.deselect();
      restoreCompositeChannels(doc);

      for(var y = Math.max(T, T + 1); y <= Math.min(maxY, B - 2); y += scanStep){
        for(var x = Math.max(L, L + 1); x <= Math.min(maxX, R - 2); x += scanStep){
          doc.selection.deselect();
          doc.selection.select([[x, y], [x + 1, y], [x + 1, y + 1], [x, y + 1]]);
          doc.selection.load(tmp, SelectionType.INTERSECT);
          if(hasSelection(doc)) return [x, y];
        }
      }

      return null;
    } finally {
      try { doc.selection.deselect(); } catch(e0){}
      try { if(tmp) tmp.remove(); } catch(e1){}
      try { restoreCompositeChannels(doc); } catch(e2){}
    }
  }

  function sampleLayerInkColor(doc, layer){
    var oldDoc = app.activeDocument;
    var oldActive = doc.activeLayer;
    var tmpDoc = null;
    var sampleStartMs = new Date().getTime();

    try{
      log("SAMPLE START: " + layer.name);
      app.activeDocument = doc;
      doc.activeLayer = layer;

      tmpDoc = app.documents.add(
        doc.width,
        doc.height,
        doc.resolution,
        "__TMP_SPOT_SAMPLE__",
        NewDocumentMode.RGB,
        DocumentFill.TRANSPARENT
      );

      app.activeDocument = doc;
      doc.activeLayer = layer;
      layer.duplicate(tmpDoc, ElementPlacement.PLACEATBEGINNING);

      app.activeDocument = tmpDoc;
      tmpDoc.activeLayer = tmpDoc.layers[0];
      tmpDoc.selection.deselect();
      var sampleMaskMode = trySelectLayerPixelsOrBounds(tmpDoc, tmpDoc.activeLayer, "sample");
      if(!sampleMaskMode) throw new Error("No transparency or bounds selection for " + layer.name);
      log("SAMPLE MASK MODE: " + layer.name + " -> " + sampleMaskMode);

      restoreCompositeChannels(tmpDoc);

      var pt = findSamplePointByCandidates(tmpDoc);
      if(!pt) pt = findSamplePointByScan(tmpDoc, 25);
      if(!pt) pt = findSamplePointByScan(tmpDoc, 10);
      if(!pt) pt = findSamplePointByScan(tmpDoc, 4);
      if(!pt) throw new Error("Could not find sample point for " + layer.name);

      log("SAMPLE POINT: " + layer.name + " @ (" + pt[0] + "," + pt[1] + ")");

      var ux = new UnitValue(pt[0], "px");
      var uy = new UnitValue(pt[1], "px");
      var sampler = tmpDoc.colorSamplers.add([ux, uy]);
      var color = sampler.color;
      sampler.remove();
      log("SAMPLE OK: " + layer.name + " -> RGB(" +
        color.rgb.red + "," +
        color.rgb.green + "," +
        color.rgb.blue + ") in " + msSince(sampleStartMs));
      return color;
    } catch(eSample){
      log("SAMPLE ERROR: " + layer.name + " :: " + eSample + " after " + msSince(sampleStartMs));
      throw eSample;
    } finally {
      try{
        if(tmpDoc){
          app.activeDocument = tmpDoc;
          tmpDoc.close(SaveOptions.DONOTSAVECHANGES);
        }
      }catch(e0){}
      try { app.activeDocument = doc; } catch(e1){}
      try { doc.activeLayer = oldActive; } catch(e2){}
      try { app.activeDocument = oldDoc; } catch(e3){}
    }
  }

  function withOnlyLayerVisible(doc, layer, fn){
    var states = [];
    var oldActive = doc.activeLayer;
    var result;

    try{
      for(var i = 0; i < doc.layers.length; i++){
        states.push(doc.layers[i].visible);
        doc.layers[i].visible = (doc.layers[i] === layer);
      }
      doc.activeLayer = layer;
      result = fn();
    } finally {
      for(var j = 0; j < doc.layers.length && j < states.length; j++){
        try { doc.layers[j].visible = states[j]; } catch(e0){}
      }
      try { doc.activeLayer = oldActive; } catch(e1){}
    }

    return result;
  }

  function sampleLayerInkColorDirect(doc, layer){
    var oldDoc = app.activeDocument;
    var oldChannels = null;
    var sampleStartMs = new Date().getTime();

    try{
      log("DIRECT SAMPLE START: " + layer.name);
      app.activeDocument = doc;
      try { oldChannels = doc.activeChannels; } catch(e0){}

      return withOnlyLayerVisible(doc, layer, function(){
        var mode = trySelectLayerPixelsOrBounds(doc, layer, "direct-sample");
        if(!mode) throw new Error("No transparency or bounds selection for " + layer.name);
        log("DIRECT SAMPLE MASK MODE: " + layer.name + " -> " + mode);

        restoreCompositeChannels(doc);

        var pt = findSamplePointByCandidates(doc);
        if(!pt) pt = findSamplePointByScan(doc, 25);
        if(!pt) pt = findSamplePointByScan(doc, 10);
        if(!pt) pt = findSamplePointByScan(doc, 4);
        if(!pt) throw new Error("Could not find direct sample point for " + layer.name);

        log("DIRECT SAMPLE POINT: " + layer.name + " @ (" + pt[0] + "," + pt[1] + ")");

        var ux = new UnitValue(pt[0], "px");
        var uy = new UnitValue(pt[1], "px");
        var sampler = doc.colorSamplers.add([ux, uy]);
        var color = sampler.color;
        sampler.remove();
        log("DIRECT SAMPLE OK: " + layer.name + " -> RGB(" +
          color.rgb.red + "," +
          color.rgb.green + "," +
          color.rgb.blue + ") in " + msSince(sampleStartMs));
        return color;
      });
    } catch(eDirect){
      log("DIRECT SAMPLE ERROR: " + layer.name + " :: " + eDirect + " after " + msSince(sampleStartMs));
      throw eDirect;
    } finally {
      try { doc.selection.deselect(); } catch(e1){}
      if(oldChannels){
        try { doc.activeChannels = oldChannels; } catch(e2){}
      } else {
        try { restoreCompositeChannels(doc); } catch(e3){}
      }
      try { app.activeDocument = oldDoc; } catch(e4){}
    }
  }

  function sampleLayerInkColorWithFallback(doc, layer){
    try{
      return sampleLayerInkColor(doc, layer);
    } catch(e0){
      log("SAMPLE FALLBACK: " + layer.name + " -> direct document sampling");
      return sampleLayerInkColorDirect(doc, layer);
    }
  }

  function findExistingChannelByName(doc, name){
    for(var i = 0; i < doc.channels.length; i++){
      if(doc.channels[i].name === name) return doc.channels[i];
    }
    return null;
  }

  function removeChannelIfExists(doc, name){
    var ch = findExistingChannelByName(doc, name);
    if(!ch) return;
    try { ch.remove(); } catch(e){}
  }

  function createSpotChannelFromLayer(doc, layer){
    var oldActive = doc.activeLayer;
    var oldChannels = null;
    var layerStartMs = new Date().getTime();
    var maskMode = null;

    try { oldChannels = doc.activeChannels; } catch(e0){}

    try{
      app.activeDocument = doc;
      doc.activeLayer = layer;
      maskMode = trySelectLayerPixelsOrBounds(doc, layer, "spot");
      if(!maskMode) throw new Error("No transparency or bounds selection for " + layer.name);
      log("SPOT MASK MODE: " + layer.name + " -> " + maskMode);

      var sampled = sampleLayerInkColorWithFallback(doc, layer);

      app.activeDocument = doc;
      doc.activeLayer = layer;
      restoreCompositeChannels(doc);
      doc.selection.deselect();
      var storeMaskMode = trySelectLayerPixelsOrBounds(doc, layer, "spot-store");
      if(!storeMaskMode) throw new Error("Could not rebuild selection for storing " + layer.name);
      log("SPOT STORE MASK MODE: " + layer.name + " -> " + storeMaskMode);
      restoreCompositeChannels(doc);

      removeChannelIfExists(doc, layer.name);

      var spotChannel = doc.channels.add();
      spotChannel.name = layer.name;
      spotChannel.kind = ChannelType.SPOTCOLOR;
      try { spotChannel.opacity = 100; } catch(e1){}
      try { spotChannel.color = sampled; } catch(e2){}

      doc.selection.store(spotChannel, SelectionType.REPLACE);
      doc.selection.deselect();
      log("SPOT OK: " + layer.name + " -> RGB(" +
        sampled.rgb.red + "," +
        sampled.rgb.green + "," +
        sampled.rgb.blue + ") in " + msSince(layerStartMs));
      return true;
    } catch(eSpot){
      log("SPOT ERROR: " + layer.name + " :: " + eSpot + " after " + msSince(layerStartMs));
      return false;
    } finally {
      try { doc.selection.deselect(); } catch(e3){}
      if(oldChannels){
        try { doc.activeChannels = oldChannels; } catch(e4){}
      } else {
        try { restoreCompositeChannels(doc); } catch(e5){}
      }
      try { doc.activeLayer = oldActive; } catch(e6){}
    }
  }

  try{
    if(!app.documents.length){
      alert("Open your PSD first, then run this script.");
      return;
    }

    var doc = app.activeDocument;
    app.displayDialogs = DialogModes.ALL;
    log("DOC: " + doc.name);
    log("MODE: " + doc.mode);
    log("SIZE PX: " + Math.floor(doc.width.as("px")) + " x " + Math.floor(doc.height.as("px")));

    if(doc.layers.length < 3){
      throw new Error("Expected standard layer stack: KEY top, colors middle, PAPER bottom.");
    }

    app.displayDialogs = DialogModes.NO;

    var targets = [];
    for(var i = 0; i < doc.layers.length - 1; i++){
      var L = doc.layers[i];
      if(L.typename !== "ArtLayer") continue;
      if(!L.visible) continue;
      targets.push(L);
    }

    targets.reverse();
    log("CHANNEL BUILD ORDER: bottom-visible-art to top-visible-art");

    var created = 0;
    var failed = 0;

    for(var t = 0; t < targets.length; t++){
      log("--- LAYER " + (t + 1) + ": " + targets[t].name);
      if(createSpotChannelFromLayer(doc, targets[t])) created++;
      else failed++;
    }

    log("RUN COMPLETE in " + msSince(RUN_START_MS));
    writeTroubleshootingLog(doc);

    alert(
      "Spot channel creation complete.\n\n" +
      "Created: " + created + "\n" +
      "Failed: " + failed +
      (LOG_FILE_PATH ? "\n\nLog: " + LOG_FILE_PATH : "")
    );
  } catch(eTop){
    log("FATAL: " + eTop);
    log("RUN FAILED after " + msSince(RUN_START_MS));
    writeTroubleshootingLog(app.documents.length ? app.activeDocument : null);
    alert(
      "Spot channel creation failed.\n\n" +
      eTop +
      (LOG_FILE_PATH ? "\n\nLog: " + LOG_FILE_PATH : "")
    );
  } finally {
    try { app.displayDialogs = prevDialogs; } catch(e1){}
  }
})();
