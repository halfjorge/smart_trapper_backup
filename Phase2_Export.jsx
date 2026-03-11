#target photoshop
app.bringToFront();

(function () {
  var prevDialogs = app.displayDialogs;
  app.displayDialogs = DialogModes.NO;

  function cTID(s){ return charIDToTypeID(s); }
  function sTID(s){ return stringIDToTypeID(s); }

  function sanitize(name) {
    return String(name).replace(/[\/\\:\*\?"<>\|]/g, "_");
  }

  function stringifyJSON(obj) {
    try { if (typeof JSON !== "undefined" && JSON && JSON.stringify) return JSON.stringify(obj, null, 2); } catch(e){}
    function esc(s){ return String(s).replace(/\\/g,"\\\\").replace(/"/g,'\\"').replace(/\r/g,"\\r").replace(/\n/g,"\\n").replace(/\t/g,"\\t"); }
    function ser(x, indent){
      indent = indent || ""; var next = indent + "  ";
      if (x === null || x === undefined) return "null";
      var t = typeof x;
      if (t === "number") return isFinite(x) ? String(x) : "null";
      if (t === "boolean") return x ? "true" : "false";
      if (t === "string") return '"' + esc(x) + '"';
      if (x instanceof Array){
        if (x.length === 0) return "[]";
        var a=[]; for (var i=0;i<x.length;i++) a.push(next + ser(x[i], next));
        return "[\n" + a.join(",\n") + "\n" + indent + "]";
      }
      var parts=[];
      for (var k in x){ if(!x.hasOwnProperty(k)) continue; parts.push(next + '"' + esc(k) + '": ' + ser(x[k], next)); }
      return "{\n" + parts.join(",\n") + "\n" + indent + "}";
    }
    return ser(obj, "");
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

  function selectLayerShapeBestEffort(doc){
    doc.selection.deselect();
    try { selectTransparencyOfActiveLayer(); if(hasSelection(doc)) return true; } catch(e){}
    doc.selection.deselect();
    return false;
  }

  function snapshotTopVisibility(doc){
    var s=[]; for (var i=0;i<doc.layers.length;i++) s[i]=doc.layers[i].visible;
    return s;
  }
  function restoreTopVisibility(doc, snap){
    for (var i=0;i<doc.layers.length;i++){ try{ doc.layers[i].visible = snap[i]; }catch(e){} }
  }

  function savePngFast(doc, fileObj){
    var opts = new PNGSaveOptions();
    opts.interlaced = false;
    doc.saveAs(fileObj, opts, true, Extension.LOWERCASE);
  }

  function duplicateSelectionToAlpha(doc, alphaName){
    var ch = doc.channels.add();
    ch.name = alphaName;
    doc.selection.store(ch);
    return ch;
  }

  function findAlphaByName(doc, alphaName){
    for(var i=0;i<doc.channels.length;i++){
      if(doc.channels[i].name === alphaName) return doc.channels[i];
    }
    return null;
  }

  function thresholdActiveChannel(level){
    var d = new ActionDescriptor();
    d.putInteger(cTID("Lvl "), level);
    executeAction(cTID("Thrs"), d, DialogModes.NO);
  }

  function selectChannelByName(doc, name){
    app.activeDocument = doc;
    var d = new ActionDescriptor();
    var r = new ActionReference();
    r.putName(cTID("Chnl"), name);
    d.putReference(cTID("null"), r);
    d.putBoolean(cTID("MkVs"), false);
    executeAction(cTID("slct"), d, DialogModes.NO);
  }

  function restoreCompositeChannels(doc){
    try { doc.activeChannels = doc.componentChannels; } catch(e){}
  }

  function applyCleanupToSelection(doc, alphaThreshold, edgeBiasPx){
    var tmp = null;
    try{
      if(!hasSelection(doc)) return false;

      tmp = doc.channels.add();
      tmp.name = "__TMP_EXPORT_CLEAN__";
      doc.selection.store(tmp);
      doc.selection.deselect();

      selectChannelByName(doc, tmp.name);
      thresholdActiveChannel(alphaThreshold);
      restoreCompositeChannels(doc);

      doc.selection.load(tmp, SelectionType.REPLACE);

      if(edgeBiasPx > 0){
        try { doc.selection.expand(edgeBiasPx); } catch(e0){}
      } else if(edgeBiasPx < 0){
        try { doc.selection.contract(Math.abs(edgeBiasPx)); } catch(e1){}
      }

      return hasSelection(doc);
    } finally {
      try { if(tmp) tmp.remove(); } catch(e2){}
      try { restoreCompositeChannels(doc); } catch(e3){}
    }
  }

  function layerMeta(L){
    var bm="(unknown)", op=100, fop=100;
    try { bm = L.blendMode.toString(); } catch(e){}
    try { op = L.opacity; } catch(e){}
    try { fop = L.fillOpacity; } catch(e){}
    return { blendMode: bm, opacity: op, fillOpacity: fop };
  }

  function exportLayerMaskPNG(doc, layer, label, masksFolder, applyCleanup){
    var snap = snapshotTopVisibility(doc);
    var oldDoc = app.activeDocument;
    var oldRuler = app.preferences.rulerUnits;
    var srcAlpha = null;
    var maskDoc = null;
    var tmpAlpha = null;
    var alphaThreshold = Number($.global.PHASE2_ALPHA_THRESHOLD);
    var edgeBiasPx = Number($.global.PHASE2_EDGE_BIAS_PX);

    try{
      app.preferences.rulerUnits = Units.PIXELS;
      app.activeDocument = doc;

      for (var i=0;i<doc.layers.length;i++){ try{ doc.layers[i].visible = false; }catch(e){} }
      layer.visible = true;
      doc.activeLayer = layer;

      if(!selectLayerShapeBestEffort(doc)){
        return null;
      }

      if(applyCleanup){
        if(isNaN(alphaThreshold)) alphaThreshold = 8;
        if(isNaN(edgeBiasPx)) edgeBiasPx = 0;
        if(!applyCleanupToSelection(doc, alphaThreshold, edgeBiasPx)){
          return null;
        }
      }

      srcAlpha = duplicateSelectionToAlpha(doc, "__TMP_EXPORT_MASK__");

      maskDoc = app.documents.add(
        doc.width,
        doc.height,
        doc.resolution,
        "mask_tmp",
        NewDocumentMode.RGB,
        DocumentFill.TRANSPARENT,
        1.0,
        BitsPerChannelType.EIGHT
      );

      app.activeDocument = doc;
      srcAlpha.duplicate(maskDoc, ElementPlacement.PLACEATEND);

      app.activeDocument = maskDoc;
      tmpAlpha = findAlphaByName(maskDoc, "__TMP_EXPORT_MASK__");
      if(!tmpAlpha) throw new Error("exportLayerMaskPNG: duplicated alpha missing in temp doc");

      maskDoc.selection.deselect();
      maskDoc.selection.load(tmpAlpha, SelectionType.REPLACE);

      var trapLayer = maskDoc.artLayers.add();
      trapLayer.name = "MASK";
      maskDoc.activeLayer = trapLayer;

      var white = new SolidColor();
      white.rgb.red = 255;
      white.rgb.green = 255;
      white.rgb.blue = 255;

      maskDoc.selection.fill(white, ColorBlendMode.NORMAL, 100, false);
      maskDoc.selection.deselect();

      try { tmpAlpha.remove(); } catch(e0){}

      var fileName = label + "_" + sanitize(layer.name) + ".png";
      var outFile = new File(masksFolder.fsName + "/" + fileName);
      savePngFast(maskDoc, outFile);

      return fileName;
    } finally {
      try{
        if(maskDoc) maskDoc.close(SaveOptions.DONOTSAVECHANGES);
      }catch(e1){}
      try{
        app.activeDocument = doc;
        if(srcAlpha) srcAlpha.remove();
      }catch(e2){}
      try { restoreTopVisibility(doc, snap); } catch(e3){}
      try { app.activeDocument = oldDoc; } catch(e4){}
      try { app.preferences.rulerUnits = oldRuler; } catch(e5){}
    }
  }

  try {
    if (!app.documents.length) { alert("No document open."); return; }

    var doc = app.activeDocument;

    var keyLayer   = doc.layers[0];
    var paperLayer = doc.layers[doc.layers.length - 1];

var baseFolder = Folder.selectDialog("Select BASE folder (job folder will be created inside)");
if (!baseFolder) return;

function pad(n){ return (n<10) ? "0"+n : ""+n; }
var d = new Date();
var stamp = d.getFullYear()+"-"+pad(d.getMonth()+1)+"-"+pad(d.getDate())+"__"+
            pad(d.getHours())+"-"+pad(d.getMinutes())+"-"+pad(d.getSeconds());

var docBase = doc.name.replace(/\.[^\.]+$/, "");
var exportFolder = new Folder(baseFolder.fsName + "/" + docBase + "__" + stamp);

if (!exportFolder.exists) exportFolder.create();



    var masksFolder = new Folder(exportFolder.fsName + "/masks");
    if (!masksFolder.exists) masksFolder.create();

    var colorLayers = [];
    for (var i = doc.layers.length - 2; i >= 1; i--) {
      var L = doc.layers[i];
      if (L.typename === "ArtLayer" && L.visible) colorLayers.push(L);
    }

    var job = {
      docName: doc.name,
      widthPx: Math.round(doc.width.as("px")),
      heightPx: Math.round(doc.height.as("px")),
      resolution: doc.resolution,
      keyLayerName: keyLayer.name,
      paperLayerName: paperLayer.name,
      colors: [],
      files: []
    };

    var km = layerMeta(keyLayer);
    var doClean = ($.global.PHASE2_DO_CLEAN === true);

    var keyMask = exportLayerMaskPNG(doc, keyLayer, "KEY", masksFolder, false);
    job.files.push({
      kind:"KEY",
      name:keyLayer.name,
      blendMode: km.blendMode,
      opacity: km.opacity,
      fillOpacity: km.fillOpacity,
      png:"masks/" + keyMask
    });

    for (var c = 0; c < colorLayers.length; c++) {
      var layer = colorLayers[c];
      var m = layerMeta(layer);
      var mask = exportLayerMaskPNG(doc, layer, (c + 1), masksFolder, doClean);

      job.colors.push({
        name: layer.name,
        blendMode: m.blendMode,
        opacity: m.opacity,
        fillOpacity: m.fillOpacity
      });

      job.files.push({
        kind:"COLOR",
        name: layer.name,
        blendMode: m.blendMode,
        opacity: m.opacity,
        fillOpacity: m.fillOpacity,
        png:"masks/" + mask
      });
    }

    var jobFile = new File(exportFolder.fsName + "/job.json");
    jobFile.open("w");
    jobFile.encoding = "UTF8";
    jobFile.write(stringifyJSON(job));
    jobFile.close();

    // 🔥 REQUIRED FOR CONTROLLER
    $.global.PHASE2_LAST_EXPORT_FOLDER = exportFolder.fsName;

    alert("Export complete.\n\nFolder:\n" + exportFolder.fsName);

  } catch (eTop) {
    alert("Export failed:\n" + eTop);
  } finally {
    try { app.displayDialogs = prevDialogs; } catch(e3) {}
  }

})();
