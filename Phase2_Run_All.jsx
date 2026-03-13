#target photoshop
app.bringToFront();

(function () {

  // --- Paths (same folder as this Run_All.jsx) ---
  var IS_WINDOWS = $.os.toLowerCase().indexOf("windows") >= 0;
  var base = File($.fileName).parent.fsName;
  var EXPORT_SCRIPT = File(base + "/Phase2_Export.jsx").fsName;
  var IMPORT_SCRIPT = File(base + "/Phase2_Import.jsx").fsName;
  var ENGINE_NAME = IS_WINDOWS ? "smart_trapper_b1.exe" : "smart_trapper_b1";

  function quoteForCmd(s){
    return '"' + String(s).replace(/"/g, '""') + '"';
  }

  function quoteForSh(s){
    return "'" + String(s).replace(/'/g, "'\"'\"'") + "'";
  }

  function cTID(s){ return charIDToTypeID(s); }

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

  function findTopArtLayer(doc){
    for(var i=0;i<doc.layers.length;i++){
      if(doc.layers[i].typename === "ArtLayer") return doc.layers[i];
    }
    return null;
  }

  function knockOutTopKeyFromColorLayers(doc){
    var keyLayer = findTopArtLayer(doc);
    var oldActive = doc.activeLayer;
    var keyMask = null;
    var changed = 0;

    if(!keyLayer) throw new Error("Could not find a top ArtLayer to use as KEY.");

    try{
      app.activeDocument = doc;
      doc.activeLayer = keyLayer;
      if(!selectLayerShapeBestEffort(doc)){
        throw new Error("Could not build key selection from top layer '" + keyLayer.name + "'");
      }

      keyMask = doc.channels.add();
      keyMask.name = "__TMP_KEY_KNOCKOUT__";
      doc.selection.store(keyMask, SelectionType.REPLACE);
      doc.selection.deselect();

      for(var i=0; i<doc.layers.length - 1; i++){
        var layer = doc.layers[i];
        if(layer.typename !== "ArtLayer") continue;
        if(layer === keyLayer) continue;
        if(!layer.visible) continue;

        doc.activeLayer = layer;
        doc.selection.deselect();
        doc.selection.load(keyMask, SelectionType.REPLACE);
        if(!hasSelection(doc)) continue;
        doc.selection.clear();
        changed++;
        doc.selection.deselect();
      }
    } finally {
      try { doc.selection.deselect(); } catch(e0){}
      try { if(keyMask) keyMask.remove(); } catch(e1){}
      try { doc.activeLayer = oldActive; } catch(e2){}
    }

    return { keyLayerName: keyLayer.name, changedCount: changed };
  }

  function chooseEngineExecutable(initialPath){
    var candidate = new File(initialPath);
    if(candidate.exists) return candidate.fsName;

    var picked = File.openDialog(
      "Select the Smart Trapper engine executable (" + ENGINE_NAME + ")",
      function(f){
        if(!(f instanceof File)) return false;
        return f.name === ENGINE_NAME;
      }
    );
    return picked ? picked.fsName : null;
  }

  // Prefer engine build output relative to this bundle, with file-picker fallback.
  var TRAPPER_EXE = chooseEngineExecutable(base + "/SmartTrapperB1/engine/target/release/" + ENGINE_NAME);
  if (!TRAPPER_EXE) { alert("Engine executable not found."); return; }

  function runEngine(jobFolder, trapPx, enginePath, trapperLogPath, errLvlPath, scriptPath){
    var script = new File(scriptPath);
    if(script.exists){
      try { script.remove(); } catch(e0){}
    }

    if(IS_WINDOWS){
      if(!script.open("w")) throw new Error("Cannot write runner script: " + script.fsName);
      script.writeln("@echo off");
      script.writeln("echo RUNNING> " + quoteForCmd(trapperLogPath));
      script.writeln(quoteForCmd(enginePath) + " " + quoteForCmd(jobFolder) + " " + trapPx +
        " 1>>" + quoteForCmd(trapperLogPath) + " 2>>&1");
      script.writeln("echo ERRORLEVEL:%ERRORLEVEL%>> " + quoteForCmd(trapperLogPath));
      script.writeln("echo %ERRORLEVEL%> " + quoteForCmd(errLvlPath));
      script.close();
      app.system('cmd.exe /c ""' + script.fsName + '""');
      return;
    }

    if(!script.open("w")) throw new Error("Cannot write runner script: " + script.fsName);
    script.writeln("#!/bin/sh");
    script.writeln("echo RUNNING > " + quoteForSh(trapperLogPath));
    script.writeln(quoteForSh(enginePath) + " " + quoteForSh(jobFolder) + " " + trapPx +
      " 1>>" + quoteForSh(trapperLogPath) + " 2>&1");
    script.writeln("status=$?");
    script.writeln("echo ERRORLEVEL:$status >> " + quoteForSh(trapperLogPath));
    script.writeln("echo $status > " + quoteForSh(errLvlPath));
    script.close();
    app.system("/bin/sh " + quoteForSh(script.fsName));
  }

  if (!app.documents.length) { alert("Open PSD first."); return; }
  var doc = app.activeDocument;

  // ----------------------------
  // Blend Mode Detection + Prompt
  // Default = PLATES
  // ----------------------------
  function isBlendLikeLayer(L){
    try {
      if (L.typename !== "ArtLayer") return false;
      if (!L.visible) return false;
      if (L.blendMode !== BlendMode.NORMAL) return true;
      if (L.opacity !== 100) return true;
      if (L.fillOpacity !== 100) return true;
    } catch(e){}
    return false;
  }

  var hasBlend = false;
  for (var i=0; i<doc.layers.length; i++){
    if (isBlendLikeLayer(doc.layers[i])) { hasBlend = true; break; }
  }

  $.global.PHASE2_MODE = "plates"; // "plates" | "overprint"

  if (hasBlend) {
    var okPlates = confirm(
      "Non-normal blend/transparency layers detected.\n\n" +
      "OK  = Continue in PLATE mode (AUTO-KNOCKOUT ON)\n\n" +
      "Cancel = Switch to OVERPRINT mode\n" +
      "(keeps intentional overlaps; traps outer boundary only)"
    );
    $.global.PHASE2_MODE = okPlates ? "plates" : "overprint";
  }

  var fullDebug = confirm(
    "Do you want full debug logging?\n\n" +
    "Yes = verbose debug log (slower)\n" +
    "No = normal log (faster)"
  );
  $.global.PHASE2_FULL_DEBUG = (fullDebug === true);

  var doKeyKnockout = confirm(
    "Do you want to cut the top key layer out of all other visible color layers?\n\n" +
    "Yes = knock out the top layer before export/trapping\n" +
    "No = leave the color layers unchanged"
  );
  if(doKeyKnockout){
    try{
      var knockoutInfo = knockOutTopKeyFromColorLayers(doc);
      alert(
        "Key knockout applied.\n\n" +
        "Key layer: " + knockoutInfo.keyLayerName + "\n" +
        "Layers changed: " + knockoutInfo.changedCount
      );
    } catch(eKey){
      alert("Key knockout failed.\n\n" + eKey);
      return;
    }
  }

  $.global.PHASE2_DO_CLEAN = false;
  $.global.PHASE2_ALPHA_THRESHOLD = 8;
  $.global.PHASE2_EDGE_BIAS_PX = 0;

  function configurePreflightCleanupForPipeline(){
    var doClean = confirm("Plate cleanup before export/trapping?\n\nYes = clean fuzzy edges first\nNo = use original masks");
    if(doClean === null || typeof doClean === "undefined") return false;
    if(!doClean){
      $.global.PHASE2_DO_CLEAN = false;
      return true;
    }

    alert(
      "Preflight cleanup settings\n\n" +
      "Alpha threshold: higher removes more faint/fuzzy pixels.\n" +
      "Edge bias: positive expands, negative contracts, zero keeps size."
    );

    var alphaInput = prompt("Alpha threshold (0-255). Higher = stronger cleanup.", String($.global.PHASE2_ALPHA_THRESHOLD));
    if(alphaInput === null) return false;
    var alphaValue = parseInt(String(alphaInput), 10);
    if(isNaN(alphaValue) || alphaValue < 0 || alphaValue > 255){
      alert("Alpha threshold must be a whole number from 0 to 255.");
      return false;
    }

    var edgeInput = prompt("Edge bias in pixels. Positive expands, negative contracts.", String($.global.PHASE2_EDGE_BIAS_PX));
    if(edgeInput === null) return false;
    var edgeValue = parseInt(String(edgeInput), 10);
    if(isNaN(edgeValue)){
      alert("Edge bias must be a whole number in pixels.");
      return false;
    }

    $.global.PHASE2_DO_CLEAN = true;
    $.global.PHASE2_ALPHA_THRESHOLD = alphaValue;
    $.global.PHASE2_EDGE_BIAS_PX = edgeValue;
    return true;
  }

  if (!configurePreflightCleanupForPipeline()) return;

  // ===============================
  // 1) RUN EXPORT
  // ===============================
  var exportFile = new File(EXPORT_SCRIPT);
  if (!exportFile.exists) { alert("Export script not found:\n" + EXPORT_SCRIPT); return; }

  $.global.PHASE2_LAST_EXPORT_FOLDER = null;
  $.evalFile(exportFile);

  if (!$.global.PHASE2_LAST_EXPORT_FOLDER) {
    alert("Export did not return folder path (PHASE2_LAST_EXPORT_FOLDER).");
    return;
  }

  var jobFolder = $.global.PHASE2_LAST_EXPORT_FOLDER;

  // ===============================
  // 2) TRAP PROMPT (scaled default: 5px @ 300dpi)
  // ===============================
  var docRes = doc.resolution;
  var scaledDefault = Math.round(5 * (docRes / 300.0));
  if (scaledDefault < 0) scaledDefault = 0;

  var trapPxStr = prompt(
    "Trap width in pixels.\nBaseline: 5px @ 300dpi\nDocument: " + docRes + " dpi",
    String(scaledDefault)
  );
  if (trapPxStr === null) return;

  var trapPx = parseFloat(trapPxStr);
  if (isNaN(trapPx) || trapPx < 0) trapPx = scaledDefault;
  trapPx = Math.round(trapPx);

  // ===============================
  // 3) RUN RUST (via .BAT)
  // ===============================
  var exeFile = new File(TRAPPER_EXE);
  if (!exeFile.exists) { alert("TRAPPER_EXE not found:\n" + TRAPPER_EXE); return; }

  var trapperLogPath = new File(jobFolder + "/trapper_log.txt").fsName;
  var errLvlPath     = new File(jobFolder + "/errorlevel.txt").fsName;
  var runnerPath     = new File(jobFolder + (IS_WINDOWS ? "/run_trapper.bat" : "/run_trapper.sh")).fsName;

  try { var a = new File(trapperLogPath); if (a.exists) a.remove(); } catch(e1){}
  try { var b = new File(errLvlPath);     if (b.exists) b.remove(); } catch(e2){}
  try { var c = new File(runnerPath);     if (c.exists) c.remove(); } catch(e3){}

  runEngine(jobFolder, trapPx, TRAPPER_EXE, trapperLogPath, errLvlPath, runnerPath);

  var trapsCheck = new File(jobFolder + "/traps.json");
  if (!trapsCheck.exists) {
    alert("Rust did not generate traps.json.\n\nCheck:\n" + trapperLogPath + "\n" + errLvlPath);
    return;
  }

  // ===============================
  // 4) RUN IMPORT
  // ===============================
  $.global.PHASE2_IMPORT_FOLDER = jobFolder;

  var importFile = new File(IMPORT_SCRIPT);
  if (!importFile.exists) { alert("Import script not found:\n" + IMPORT_SCRIPT); return; }

  $.evalFile(importFile);

})();
