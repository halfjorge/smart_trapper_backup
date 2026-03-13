#target photoshop
app.bringToFront();

(function () {

  var prevDialogs = app.displayDialogs;
  app.displayDialogs = DialogModes.NO;

  // ======================
  // DEBUG LOG
  // ======================
  var LOG = [];
  var FULL_DEBUG = ($.global.PHASE2_FULL_DEBUG === true);
  function log(s){ LOG.push(String(s)); }
  function debugLog(s){ if(FULL_DEBUG) LOG.push(String(s)); }
  function logDocState(doc, label){
    try{
      debugLog("[" + label + "] doc=" + doc.name);
    }catch(e){}
    try{
      debugLog("[" + label + "] activeLayer=" + (doc.activeLayer ? doc.activeLayer.name : "null"));
    }catch(e){}
    try{
      var chNames = [];
      for(var i=0;i<doc.activeChannels.length;i++) chNames.push(doc.activeChannels[i].name);
      debugLog("[" + label + "] activeChannels=" + chNames.join(", "));
    }catch(e){}
    try{
      debugLog("[" + label + "] hasSelection=" + hasSelection(doc));
    }catch(e){}
    try{
      if(hasSelection(doc)){
        var b = doc.selection.bounds;
        debugLog("[" + label + "] selBounds=" +
          b[0].as("px") + "," + b[1].as("px") + "," +
          b[2].as("px") + "," + b[3].as("px"));
      }
    }catch(e){}
  }

  function step(label, fn){
    debugLog("STEP BEGIN: " + label);
    try{
      var out = fn();
      debugLog("STEP OK: " + label);
      return out;
    }catch(e){
      log("STEP FAIL: " + label + " :: " + e);
      throw e;
    }
  }
  function flushLog(folder){
    var body = LOG.join("\r\n");
    var primaryErr = null;

    if(folder){
      try{
        var targetFolder = (folder instanceof Folder) ? folder : new Folder(String(folder));
        if(!targetFolder.exists){
          throw new Error("Folder does not exist: " + targetFolder.fsName);
        }

        var out = new File(targetFolder.fsName + "/import_debug_log.txt");
        if(!out.open("w")){
          throw new Error("Cannot open log for writing: " + out.fsName);
        }
        out.encoding = "UTF8";
        out.write(body);
        out.close();
        return out.fsName;
      }catch(e1){
        primaryErr = e1;
      }
    }

    try{
      var fallback = new File(Folder.desktop.fsName + "/import_debug_log_FALLBACK.txt");
      if(!fallback.open("w")){
        throw new Error("Cannot open fallback log for writing: " + fallback.fsName);
      }
      fallback.encoding = "UTF8";
      fallback.write(body);
      fallback.close();
      return fallback.fsName;
    }catch(e2){
      var msg = "Failed to write debug log.\n";
      if(primaryErr) msg += "Primary write error: " + primaryErr + "\n";
      msg += "Fallback write error: " + e2;
      alert(msg);
      return null;
    }
  }

  // ======================
  // Helpers
  // ======================
  function safeTrim(s){ return String(s).replace(/^\s+|\s+$/g, ""); }
  function sanitizeName(name){ return safeTrim(String(name).replace(/[\/\\:\*\?"<>\|]/g, "_")); }
  function cTID(s){ return charIDToTypeID(s); }
  function sTID(s){ return stringIDToTypeID(s); }
  var ALPHA_THRESHOLD = 8; // 0-255
  var EDGE_BIAS_PX = 0; // +expand / -contract
  var INK_COLOR_CACHE = {};

  function configurePreflightCleanupOptions(){
    alert(
      "Preflight cleanup settings\n\n" +
      "Alpha threshold: higher removes more faint/fuzzy pixels.\n" +
      "Edge bias: positive expands, negative contracts, zero keeps size."
    );

    var alphaInput = prompt("Alpha threshold (0-255). Higher = stronger cleanup.", String(ALPHA_THRESHOLD));
    if(alphaInput === null) return false;

    var alphaValue = parseInt(String(alphaInput), 10);
    if(isNaN(alphaValue) || alphaValue < 0 || alphaValue > 255){
      alert("Alpha threshold must be a whole number from 0 to 255.");
      return false;
    }

    var edgeInput = prompt("Edge bias in pixels. Positive expands, negative contracts.", String(EDGE_BIAS_PX));
    if(edgeInput === null) return false;

    var edgeValue = parseInt(String(edgeInput), 10);
    if(isNaN(edgeValue)){
      alert("Edge bias must be a whole number in pixels.");
      return false;
    }

    ALPHA_THRESHOLD = alphaValue;
    EDGE_BIAS_PX = edgeValue;
    log("Preflight cleanup settings: alphaThreshold=" + ALPHA_THRESHOLD + ", edgeBiasPx=" + EDGE_BIAS_PX);
    return true;
  }

  if (typeof JSON === "undefined") JSON = {};
  if (!JSON.parse){
    JSON.parse = function (text){
      var s = String(text);
      var i = 0;
      var len = s.length;

      function error(msg){
        throw new Error(msg + " at " + i);
      }
      function ch(){
        return s.charAt(i);
      }
      function isWs(c){
        return c === " " || c === "\t" || c === "\n" || c === "\r";
      }
      function skipWs(){
        while(i < len && isWs(ch())) i++;
      }
      function expect(c){
        if(ch() !== c) error("Expected '" + c + "'");
        i++;
      }
      function parseString(){
        var out = "";
        expect("\"");
        while(i < len){
          var c = ch();
          i++;
          if(c === "\"") return out;
          if(c === "\\"){
            if(i >= len) error("Unterminated escape");
            var e = ch();
            i++;
            if(e === "\"" || e === "\\" || e === "/"){ out += e; continue; }
            if(e === "b"){ out += "\b"; continue; }
            if(e === "f"){ out += "\f"; continue; }
            if(e === "n"){ out += "\n"; continue; }
            if(e === "r"){ out += "\r"; continue; }
            if(e === "t"){ out += "\t"; continue; }
            if(e === "u"){
              var hex = s.substr(i, 4);
              if(!/^[0-9a-fA-F]{4}$/.test(hex)) error("Invalid unicode escape");
              out += String.fromCharCode(parseInt(hex, 16));
              i += 4;
              continue;
            }
            error("Invalid escape");
          } else {
            if(c < " ") error("Invalid control character");
            out += c;
          }
        }
        error("Unterminated string");
      }
      function parseNumber(){
        var start = i;
        if(ch() === "-") i++;
        if(ch() === "0"){
          i++;
        } else {
          if(ch() < "1" || ch() > "9") error("Invalid number");
          while(ch() >= "0" && ch() <= "9") i++;
        }
        if(ch() === "."){
          i++;
          if(ch() < "0" || ch() > "9") error("Invalid number");
          while(ch() >= "0" && ch() <= "9") i++;
        }
        if(ch() === "e" || ch() === "E"){
          i++;
          if(ch() === "+" || ch() === "-") i++;
          if(ch() < "0" || ch() > "9") error("Invalid exponent");
          while(ch() >= "0" && ch() <= "9") i++;
        }
        var n = Number(s.slice(start, i));
        if(!isFinite(n)) error("Invalid number");
        return n;
      }
      function parseLiteral(word, value){
        if(s.substr(i, word.length) !== word) error("Unexpected token");
        i += word.length;
        return value;
      }
      function parseArray(){
        var arr = [];
        expect("[");
        skipWs();
        if(ch() === "]"){ i++; return arr; }
        while(true){
          arr.push(parseValue());
          skipWs();
          if(ch() === ","){
            i++;
            skipWs();
            continue;
          }
          if(ch() === "]"){
            i++;
            return arr;
          }
          error("Expected ',' or ']'");
        }
      }
      function parseObject(){
        var obj = {};
        expect("{");
        skipWs();
        if(ch() === "}"){ i++; return obj; }
        while(true){
          if(ch() !== "\"") error("Expected string key");
          var key = parseString();
          skipWs();
          expect(":");
          skipWs();
          obj[key] = parseValue();
          skipWs();
          if(ch() === ","){
            i++;
            skipWs();
            continue;
          }
          if(ch() === "}"){
            i++;
            return obj;
          }
          error("Expected ',' or '}'");
        }
      }
      function parseValue(){
        skipWs();
        var c = ch();
        if(c === "\"") return parseString();
        if(c === "{") return parseObject();
        if(c === "[") return parseArray();
        if(c === "-" || (c >= "0" && c <= "9")) return parseNumber();
        if(c === "t") return parseLiteral("true", true);
        if(c === "f") return parseLiteral("false", false);
        if(c === "n") return parseLiteral("null", null);
        error("Unexpected token");
      }

      var result = parseValue();
      skipWs();
      if(i !== len) error("Trailing characters");
      return result;
    };
  }

  function hasSelection(doc){
    try { doc.selection.bounds; return true; }
    catch(e){ return false; }
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

  function logicalInkName(name){
    name = String(name);
    return (name.indexOf("CLEAN__") === 0) ? name.substring(7) : name;
  }

  function findChannelByName(doc, channelName){
    for(var i=0;i<doc.channels.length;i++){
      if(doc.channels[i].name === channelName) return doc.channels[i];
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

  function ensureCompositeChannels(doc){
    try{
      doc.activeChannels = doc.componentChannels;
    }catch(e){
      try{
        restoreCompositeChannels(doc);
      }catch(e2){}
    }
  }

  function cleanInkLayersNonDestructive(hostDoc){
    log("CLEAN: begin preflight alpha-threshold cleanup");

    var targets = [];
    for(var i = hostDoc.layers.length - 2; i >= 1; i--){
      var L = hostDoc.layers[i];
      if(L.typename === "ArtLayer" && L.visible) targets.push(L);
    }

    var oldActive = hostDoc.activeLayer;
    var oldFg = app.foregroundColor;
    var oldChannels = null;
    try { oldChannels = hostDoc.activeChannels; } catch(e0){}

    for(var t=0; t<targets.length; t++){
      var orig = targets[t];
      var cleanName = "CLEAN__" + orig.name;
      var tmp = null;
      var layerChannels = null;
      try { layerChannels = hostDoc.activeChannels; } catch(e0a){}

      try {
        try {
          cacheLayerInkColor(orig.name, sampleLayerInkColor(hostDoc, orig));
        } catch(sampleErr){
          log("  [CLEAN_SAMPLE_FALLBACK] " + orig.name + " " + sampleErr);
        }

        // Always rebuild selection from transparency for cleanup.
        hostDoc.activeLayer = orig;
        hostDoc.selection.deselect();
        try { selectTransparencyOfActiveLayer(); } catch(e1){}
        if(!hasSelection(hostDoc)){
          log("CLEAN SKIP: " + orig.name + " (no selection)");
          hostDoc.selection.deselect();
          continue;
        }

        var stale = findChannelByName(hostDoc, "__TMP_CLEAN_ALPHA__");
        if(stale){ try { stale.remove(); } catch(e3){} }

        tmp = hostDoc.channels.add();
        tmp.name = "__TMP_CLEAN_ALPHA__";
        hostDoc.selection.store(tmp);
        hostDoc.selection.deselect();

        selectChannelByName(hostDoc, tmp.name);
        thresholdActiveChannel(ALPHA_THRESHOLD);
        restoreCompositeChannels(hostDoc);

        hostDoc.selection.load(tmp, SelectionType.REPLACE);

        if(EDGE_BIAS_PX > 0){
          try { hostDoc.selection.expand(EDGE_BIAS_PX); } catch(e5){}
        } else if(EDGE_BIAS_PX < 0){
          try { hostDoc.selection.contract(Math.abs(EDGE_BIAS_PX)); } catch(e6){}
        }

        var clean = hostDoc.artLayers.add();
        clean.name = cleanName;
        clean.move(orig, ElementPlacement.PLACEBEFORE);
        hostDoc.activeLayer = clean;
        fillSelectionWithLayerColor(orig.name);
        hostDoc.selection.deselect();

        orig.visible = false;
        clean.visible = true;
        log("CLEAN: " + orig.name + " -> " + clean.name);
      } catch(layerErr) {
        log("CLEAN ERROR: " + orig.name + " " + layerErr);
        hostDoc.selection.deselect();
      } finally {
        if(tmp){ try { tmp.remove(); } catch(e7){} }
        if(layerChannels){
          try { hostDoc.activeChannels = layerChannels; } catch(e8){}
        } else if(oldChannels){
          try { hostDoc.activeChannels = oldChannels; } catch(e9){}
        } else {
          restoreCompositeChannels(hostDoc);
        }
      }
    }

    hostDoc.selection.deselect();
    try { app.foregroundColor = oldFg; } catch(e10){}
    try { hostDoc.activeLayer = oldActive; } catch(e11){}
    if(oldChannels){
      try { hostDoc.activeChannels = oldChannels; } catch(e12){}
    }
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

  function parseJSON(txt){
    try {
      return JSON.parse(String(txt));
    } catch(e1){
      throw new Error("Could not parse JSON: " + e1);
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

  // ---- Find sample point by scanning inside selection bounds
  function findSamplePointByScan(doc, scanStep){
    log("SCAN START step=" + scanStep);
    if(!hasSelection(doc)){
      log("SCAN ABORT: no selection");
      return null;
    }

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
    log("SCAN BOUNDS RAW: " + [rawL,rawT,rawR,rawB].join(","));
    log("SCAN BOUNDS CLAMPED: " + [L,T,R,B].join(","));

    if(L >= R || T >= B){
      log("SCAN ABORT: clamped bounds are empty");
      return null;
    }

    var tmp = null;
    try{
      tmp = step("channels.add tmp scan", function(){
        var ch = doc.channels.add();
        ch.name = "__TMP_SEL_SCAN__";
        return ch;
      });

      step("selection.store tmp scan", function(){
        doc.selection.store(tmp);
      });

      step("selection.deselect after store", function(){
        doc.selection.deselect();
      });

      step("restoreCompositeChannels after tmp store", function(){
        restoreCompositeChannels(doc);
      });

      function testPoint(x,y){
        debugLog("TEST POINT: " + x + "," + y);
        step("restoreCompositeChannels testPoint", function(){
          restoreCompositeChannels(doc);
        });
        step("selection.deselect testPoint", function(){
          doc.selection.deselect();
        });
        step("selection.select 1px box", function(){
          doc.selection.select([[x,y],[x+1,y],[x+1,y+1],[x,y+1]]);
        });
        step("selection.load INTERSECT tmp", function(){
          doc.selection.load(tmp, SelectionType.INTERSECT);
        });
        return hasSelection(doc);
      }

      var found = null;
      for(var y2=Math.max(T, T+1); y2<=Math.min(maxY, B-2); y2+=scanStep){
        for(var x2=Math.max(L, L+1); x2<=Math.min(maxX, R-2); x2+=scanStep){
          if(testPoint(x2,y2)){
            found = [x2,y2];
            log("SCAN FOUND: " + found[0] + "," + found[1]);
            break;
          }
        }
        if(found) break;
      }

      step("selection.deselect end scan", function(){
        doc.selection.deselect();
      });
      step("restoreCompositeChannels end scan", function(){
        restoreCompositeChannels(doc);
      });

      return found;

    } catch(e){
      log("SCAN ERROR step=" + scanStep + " :: " + e);
      logDocState(doc, "scan-error-state");
      throw e;
    } finally {
      if(tmp){
        try { tmp.remove(); log("SCAN TMP REMOVED"); } catch(e2){ log("SCAN TMP REMOVE ERR: " + e2); }
      }
    }
  }

  function addCandidateProbe(points, seen, x, y, maxX, maxY){
    x = Math.max(0, Math.min(maxX, Math.floor(x)));
    y = Math.max(0, Math.min(maxY, Math.floor(y)));
    var key = x + "," + y;
    if(seen[key]) return;
    seen[key] = true;
    points.push([x, y]);
  }

  function findSamplePointByCandidates(doc){
    log("SCAN CANDIDATES START");
    if(!hasSelection(doc)){
      log("SCAN CANDIDATES ABORT: no selection");
      return null;
    }

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

    log("SCAN BOUNDS RAW: " + [rawL,rawT,rawR,rawB].join(","));
    log("SCAN BOUNDS CLAMPED: " + [L,T,R,B].join(","));

    if(L >= R || T >= B){
      log("SCAN CANDIDATES ABORT: clamped bounds are empty");
      return null;
    }

    var midX = Math.floor((L + R - 1) / 2);
    var midY = Math.floor((T + B - 1) / 2);
    var q1X = Math.floor((L + midX) / 2);
    var q3X = Math.floor((midX + R - 1) / 2);
    var q1Y = Math.floor((T + midY) / 2);
    var q3Y = Math.floor((midY + B - 1) / 2);
    var points = [];
    var seen = {};
    var tmp = null;
    var found = null;

    addCandidateProbe(points, seen, midX, midY, maxX, maxY);
    addCandidateProbe(points, seen, q1X, q1Y, maxX, maxY);
    addCandidateProbe(points, seen, q3X, q1Y, maxX, maxY);
    addCandidateProbe(points, seen, q1X, q3Y, maxX, maxY);
    addCandidateProbe(points, seen, q3X, q3Y, maxX, maxY);
    addCandidateProbe(points, seen, L + 1, T + 1, maxX, maxY);
    addCandidateProbe(points, seen, R - 2, T + 1, maxX, maxY);
    addCandidateProbe(points, seen, L + 1, B - 2, maxX, maxY);
    addCandidateProbe(points, seen, R - 2, B - 2, maxX, maxY);
    addCandidateProbe(points, seen, midX, T + 1, maxX, maxY);
    addCandidateProbe(points, seen, midX, B - 2, maxX, maxY);
    addCandidateProbe(points, seen, L + 1, midY, maxX, maxY);
    addCandidateProbe(points, seen, R - 2, midY, maxX, maxY);

    try{
      tmp = step("channels.add tmp candidate scan", function(){
        var ch = doc.channels.add();
        ch.name = "__TMP_SEL_SCAN__";
        return ch;
      });

      step("selection.store tmp candidate scan", function(){
        doc.selection.store(tmp);
      });

      step("selection.deselect after candidate store", function(){
        doc.selection.deselect();
      });

      step("restoreCompositeChannels after candidate store", function(){
        restoreCompositeChannels(doc);
      });

      for(var i=0;i<points.length;i++){
        var p = points[i];
        debugLog("CANDIDATE POINT: " + p[0] + "," + p[1]);
        step("restoreCompositeChannels candidate point", function(){
          restoreCompositeChannels(doc);
        });
        step("selection.deselect candidate point", function(){
          doc.selection.deselect();
        });
        step("selection.select 1px candidate box", function(){
          doc.selection.select([[p[0],p[1]],[p[0]+1,p[1]],[p[0]+1,p[1]+1],[p[0],p[1]+1]]);
        });
        step("selection.load INTERSECT candidate tmp", function(){
          doc.selection.load(tmp, SelectionType.INTERSECT);
        });
        if(hasSelection(doc)){
          found = p;
          log("SCAN CANDIDATE HIT: " + p[0] + "," + p[1]);
          break;
        }
      }

      if(!found){
        log("SCAN CANDIDATE MISS");
      }

      step("selection.deselect end candidate scan", function(){
        doc.selection.deselect();
      });
      step("selection.load REPLACE candidate tmp", function(){
        doc.selection.load(tmp, SelectionType.REPLACE);
      });
      step("restoreCompositeChannels end candidate scan", function(){
        restoreCompositeChannels(doc);
      });

      return found;
    } catch(e){
      log("SCAN CANDIDATES ERROR :: " + e);
      logDocState(doc, "scan-candidates-error-state");
      throw e;
    } finally {
      try { restoreCompositeChannels(doc); } catch(e1){}
      if(tmp){
        try { tmp.remove(); log("SCAN CANDIDATE TMP REMOVED"); } catch(e2){ log("SCAN CANDIDATE TMP REMOVE ERR: " + e2); }
      }
    }
  }

  // ---- Sample SOURCE ink color (once per source)
  function sampleLayerInkColor(doc, layer){
    log("SAMPLE START: " + layer.name);
    var oldDoc = app.activeDocument;
    var oldActive = doc.activeLayer;
    var tmpDoc = null;

    try{
      step("set activeLayer " + layer.name, function(){
        app.activeDocument = doc;
        doc.activeLayer = layer;
      });

      step("create isolated sample doc " + layer.name, function(){
        tmpDoc = app.documents.add(
          doc.width,
          doc.height,
          doc.resolution,
          "__TMP_INK_SAMPLE__",
          NewDocumentMode.RGB,
          DocumentFill.TRANSPARENT
        );
      });

      step("duplicate sample layer into temp doc " + layer.name, function(){
        app.activeDocument = doc;
        doc.activeLayer = layer;
        layer.duplicate(tmpDoc, ElementPlacement.PLACEATBEGINNING);
      });

      app.activeDocument = tmpDoc;
      tmpDoc.activeLayer = tmpDoc.layers[0];
      tmpDoc.selection.deselect();

      var gotSel = step("select transparency in temp doc " + layer.name, function(){
        selectTransparencyOfActiveLayer();
        return hasSelection(tmpDoc);
      });
      if(!gotSel){
        throw new Error("Could not create isolated selection for sampling: " + layer.name);
      }

      step("restoreCompositeChannels before isolated scan", function(){
        restoreCompositeChannels(tmpDoc);
      });

      var pt = null;
      step("find isolated sample point candidates", function(){
        pt = findSamplePointByCandidates(tmpDoc);
      });
      if(!pt){
        step("find isolated sample point 25", function(){
          pt = findSamplePointByScan(tmpDoc, 25);
        });
      }
      if(!pt){
        step("find isolated sample point 10", function(){
          pt = findSamplePointByScan(tmpDoc, 10);
        });
      }
      if(!pt){
        step("find isolated sample point 4", function(){
          pt = findSamplePointByScan(tmpDoc, 4);
        });
      }
      if(!pt){
        throw new Error("Could not find isolated sample point: " + layer.name);
      }

      log("SAMPLE POINT: " + layer.name + " @ (" + pt[0] + "," + pt[1] + ")");

      var c = null;
      step("color sampler isolated " + layer.name, function(){
        var ux = new UnitValue(pt[0], "px");
        var uy = new UnitValue(pt[1], "px");
        var s = tmpDoc.colorSamplers.add([ux, uy]);
        c = s.color;
        s.remove();
      });

      step("selection.deselect temp doc after sample", function(){
        tmpDoc.selection.deselect();
      });

      app.activeDocument = doc;
      doc.activeLayer = oldActive;
      app.foregroundColor = c;

      log("SAMPLE RGB: " + layer.name + " -> (" + c.rgb.red + "," + c.rgb.green + "," + c.rgb.blue + ")");
      return c;

    } catch(e){
      log("SAMPLE ERROR: " + layer.name + " :: " + e);
      try { app.activeDocument = doc; } catch(e0){}
      try { doc.selection.deselect(); } catch(e1){ log("cleanup deselect err: " + e1); }
      try { doc.activeLayer = oldActive; } catch(e2){ log("cleanup restore active err: " + e2); }
      throw e;
    } finally {
      if(tmpDoc){
        try{
          app.activeDocument = tmpDoc;
          tmpDoc.close(SaveOptions.DONOTSAVECHANGES);
        }catch(e3){
          log("cleanup temp sample doc err: " + e3);
        }
      }
      try { app.activeDocument = oldDoc; } catch(e4){}
    }
  }

  function cacheLayerInkColor(layerName, sampledColor){
    if(!sampledColor) throw new Error("No sampled color for layer: " + layerName);

    INK_COLOR_CACHE[layerName] = {
      r: sampledColor.rgb.red,
      g: sampledColor.rgb.green,
      b: sampledColor.rgb.blue
    };
    log("INK CACHE: " + layerName + " -> (" +
      INK_COLOR_CACHE[layerName].r + "," +
      INK_COLOR_CACHE[layerName].g + "," +
      INK_COLOR_CACHE[layerName].b + ")");
  }

  function getLayerInkColor(layerName){
    var c = INK_COLOR_CACHE[layerName];

    if(!c) throw new Error("Ink color not cached for layer: " + layerName);

    var sc = new SolidColor();
    sc.rgb.red = c.r;
    sc.rgb.green = c.g;
    sc.rgb.blue = c.b;
    return sc;
  }

  function setForegroundFromLayer(layerName){
    var sc = getLayerInkColor(layerName);
    app.foregroundColor = sc;
  }

  function fillSelectionWithLayerColor(layerName){
    var doc = app.activeDocument;

    setForegroundFromLayer(layerName);
    doc.selection.fill(app.foregroundColor, ColorBlendMode.NORMAL, 100, false);
  }

  function initializeInkColors(doc, layerList){
    for(var i = 0; i < layerList.length; i++){
      var layer = layerList[i];
      var sampled = sampleLayerInkColor(doc, layer);
      cacheLayerInkColor(layer.name, sampled);
    }
  }

  function printInkCache(){
    for(var k in INK_COLOR_CACHE){
      if(!INK_COLOR_CACHE.hasOwnProperty(k)) continue;
      var c = INK_COLOR_CACHE[k];
      $.writeln("[INK] " + k + " -> RGB(" + c.r + "," + c.g + "," + c.b + ")");
    }
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
    var want = "COLOR__" + sanitizeName(logicalInkName(sourceLayerName));
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

  function findSourceBaseLayer(sourceGroup, sourceName){
    var clean = findArtLayerByName(sourceGroup, "CLEAN__" + sourceName);
    if(clean) return clean;
    return findArtLayerByName(sourceGroup, sourceName);
  }

  function findSourceSamplingLayer(sourceGroup, sourceName){
    // Prefer the ORIGINAL layer for color sampling, even if cleanup created CLEAN__ layers.
    // This prevents white/incorrect trap fills when cleanup rebuilt the art layer.
    var orig = findArtLayerByName(sourceGroup, sourceName);
    if(orig) return orig;

    var clean = findArtLayerByName(sourceGroup, "CLEAN__" + sourceName);
    if(clean) return clean;

    return null;
  }

  function normalizeCleanLayerGrouping(doc){
    for(var i = 0; i < doc.layers.length; i++){
      var cleanLayer = doc.layers[i];
      if(!cleanLayer || cleanLayer.typename !== "ArtLayer") continue;
      if(cleanLayer.name.indexOf("CLEAN__") !== 0) continue;

      var inkName = logicalInkName(cleanLayer.name);
      var group = findColorGroup(doc, inkName);

      if(!group){
        group = wrapLayerInGroup(doc, cleanLayer, "COLOR__" + sanitizeName(inkName));
      } else if(cleanLayer.parent !== group){
        try { cleanLayer.move(group, ElementPlacement.INSIDE); } catch(e0){}
      }

      var orig = findArtLayerByName(group, inkName);
      if(orig && orig !== cleanLayer){
        try { cleanLayer.move(orig, ElementPlacement.PLACEBEFORE); } catch(e1){}
        try { orig.visible = false; } catch(e2){}
      }

      try { cleanLayer.visible = true; } catch(e3){}
    }
  }

  function getTrapOffsetFromSpec(spec){
    var left = null;
    var top = null;

    if(spec.hasOwnProperty("left")) left = Number(spec.left);
    if(spec.hasOwnProperty("top")) top = Number(spec.top);

    if(left === null && spec.hasOwnProperty("x")) left = Number(spec.x);
    if(top === null && spec.hasOwnProperty("y")) top = Number(spec.y);

    if(left === null && spec.hasOwnProperty("offsetX")) left = Number(spec.offsetX);
    if(top === null && spec.hasOwnProperty("offsetY")) top = Number(spec.offsetY);

    if((left === null || top === null) && spec.bounds && spec.bounds.length >= 2){
      left = Number(spec.bounds[0]);
      top = Number(spec.bounds[1]);
    }

    if((left === null || top === null) && spec.rect && spec.rect.length >= 2){
      left = Number(spec.rect[0]);
      top = Number(spec.rect[1]);
    }

    if(left === null || isNaN(left)) left = 0;
    if(top === null || isNaN(top)) top = 0;

    return { left:left, top:top };
  }

  function translateSelectionSafe(doc, dx, dy){
    if(!hasSelection(doc)) return;
    if(dx === 0 && dy === 0) return;

    var d = new ActionDescriptor();
    var r = new ActionReference();
    r.putProperty(charIDToTypeID("Chnl"), charIDToTypeID("fsel"));
    d.putReference(charIDToTypeID("null"), r);

    var o = new ActionDescriptor();
    o.putUnitDouble(charIDToTypeID("Hrzn"), charIDToTypeID("#Pxl"), dx);
    o.putUnitDouble(charIDToTypeID("Vrtc"), charIDToTypeID("#Pxl"), dy);
    d.putObject(charIDToTypeID("T   "), charIDToTypeID("Ofst"), o);

    executeAction(charIDToTypeID("move"), d, DialogModes.NO);
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
  function selectionFromTrapPngIntoHost_ALIGN_BY_BOUNDS(hostDoc, pngFile, spec){
    var srcDoc = null;
    var srcAlpha = null;
    var hostAlpha = null;

    try{
      app.activeDocument = hostDoc;
      hostDoc.selection.deselect();

      srcDoc = app.open(pngFile);
      srcDoc.activeLayer = srcDoc.layers[0];
      srcDoc.selection.deselect();

      // Build selection from PNG transparency
      try { selectTransparencyOfActiveLayer(); } catch(e0){}
      if(!hasSelection(srcDoc)){
        log("  PNG transparency produced no selection: " + pngFile.fsName);
        try { srcDoc.close(SaveOptions.DONOTSAVECHANGES); } catch(e1){}
        return false;
      }

      // Log source selection bounds
      try{
        var sb = srcDoc.selection.bounds;
        log("  SOURCE PNG selection bounds px: " +
          Math.floor(sb[0].as("px")) + "," +
          Math.floor(sb[1].as("px")) + "," +
          Math.floor(sb[2].as("px")) + "," +
          Math.floor(sb[3].as("px")));
      }catch(e2){}

      // Store source selection into a temp alpha channel in the PNG doc
      srcAlpha = srcDoc.channels.add();
      srcAlpha.name = "__TMP_TRAP_ALPHA_SRC__";
      srcDoc.selection.store(srcAlpha);
      srcDoc.selection.deselect();

      // Duplicate alpha channel directly into host doc
      srcDoc.activeChannels = [srcAlpha];
      srcAlpha.duplicate(hostDoc, ElementPlacement.PLACEATEND);

      // Close source PNG
      try { srcDoc.close(SaveOptions.DONOTSAVECHANGES); } catch(e3){}
      srcDoc = null;

      // Find duplicated host alpha channel by name
      app.activeDocument = hostDoc;
      hostAlpha = findChannelByName(hostDoc, "__TMP_TRAP_ALPHA_SRC__");
      if(!hostAlpha){
        log("  ERROR: duplicated host alpha channel not found");
        return false;
      }

      // Load host alpha channel as selection
      hostDoc.selection.deselect();
      hostDoc.selection.load(hostAlpha, SelectionType.REPLACE);

      // IMPORTANT: apply the original trap offset from traps.json
      var off = getTrapOffsetFromSpec(spec || {});
      log("  TRAP OFFSET from spec px: " + off.left + "," + off.top);

      if(off.left !== 0 || off.top !== 0){
        translateSelectionSafe(hostDoc, off.left, off.top);
      }

      // Intersect with actual canvas, just in case
      var canvasCh = null;
      try{
        canvasCh = hostDoc.channels.add();
        canvasCh.name = "__TMP_CANVAS_BOUNDS__";

        hostDoc.selection.deselect();
        hostDoc.selection.select([
          [0, 0],
          [hostDoc.width.as("px"), 0],
          [hostDoc.width.as("px"), hostDoc.height.as("px")],
          [0, hostDoc.height.as("px")]
        ]);
        hostDoc.selection.store(canvasCh);

        hostDoc.selection.deselect();
        hostDoc.selection.load(hostAlpha, SelectionType.REPLACE);
        if(off.left !== 0 || off.top !== 0){
          translateSelectionSafe(hostDoc, off.left, off.top);
        }
        hostDoc.selection.load(canvasCh, SelectionType.INTERSECT);
      }catch(eCanvas){
        log("  canvas intersect warning: " + eCanvas);
      }finally{
        if(canvasCh){
          try { canvasCh.remove(); } catch(e4){}
        }
      }

      var ok = hasSelection(hostDoc);

      if(ok){
        try{
          var fb = hostDoc.selection.bounds;
          log("  FINAL HOST selection bounds px: " +
            Math.floor(fb[0].as("px")) + "," +
            Math.floor(fb[1].as("px")) + "," +
            Math.floor(fb[2].as("px")) + "," +
            Math.floor(fb[3].as("px")));
        }catch(e5){}
      }else{
        log("  FINAL HOST selection is empty");
      }

      // Clean up temp host alpha channel
      try { hostAlpha.remove(); } catch(e6){}

      // Restore composite channels
      try { restoreCompositeChannels(hostDoc); } catch(e7){}

      return ok;

    } catch(err){
      log("  selectionFromTrapPngIntoHost_ALIGN_BY_BOUNDS ERROR: " + err);

      try{
        if(srcDoc) srcDoc.close(SaveOptions.DONOTSAVECHANGES);
      }catch(e8){}

      try{
        if(hostAlpha) hostAlpha.remove();
      }catch(e9){}

      try{
        restoreCompositeChannels(hostDoc);
      }catch(e10){}

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
    if(!app.documents.length){
      alert("Open your PSD first, then run this importer.");
      return;
    }

    var hostDoc = app.activeDocument;
    var usePipelineCleanupSettings = (typeof $.global.PHASE2_DO_CLEAN !== "undefined");
    var doClean = false;

    if(usePipelineCleanupSettings){
      doClean = ($.global.PHASE2_DO_CLEAN === true);
      if(doClean){
        ALPHA_THRESHOLD = Number($.global.PHASE2_ALPHA_THRESHOLD);
        EDGE_BIAS_PX = Number($.global.PHASE2_EDGE_BIAS_PX);
        if(isNaN(ALPHA_THRESHOLD)) ALPHA_THRESHOLD = 8;
        if(isNaN(EDGE_BIAS_PX)) EDGE_BIAS_PX = 0;
      }
    } else {
      doClean = confirm("Does this file need plate cleanup before trapping?\n\nYes = clean fuzzy edges\nNo = skip cleanup");
      if(doClean === null || typeof doClean === "undefined"){
        return;
      }
    }

    if(doClean){
      log("Preflight cleanup: ENABLED");
      if(!usePipelineCleanupSettings && !configurePreflightCleanupOptions()){
        log("Preflight cleanup configuration cancelled or invalid.");
        return;
      }
      cleanInkLayersNonDestructive(hostDoc);
    } else {
      log("Preflight cleanup: SKIPPED");
    }

    // If controller provided folder, use it.
    // Otherwise fall back to manual selection.
    if ($.global.PHASE2_IMPORT_FOLDER) {
      folder = new Folder($.global.PHASE2_IMPORT_FOLDER);
      log("Using controller-provided folder: " + folder.fsName);
    } else {
      folder = Folder.selectDialog("Select JOB folder (contains traps.json + traps/ + debug_*.png)");
    }

    if (!folder){
      log("Import cancelled: no job folder selected.");
      flushLog(null);
      return;
    }
    if (!(folder instanceof Folder)) folder = new Folder(String(folder));
    if (!folder.exists) {
      alert("JOB folder does not exist:\n" + folder.fsName);
      log("ERROR: JOB folder does not exist: " + folder.fsName);
      flushLog(null);
      return;
    }

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
      log("ERROR: PSD needs at least 3 top-level layers (KEY top, PAPER bottom, colors in between).");
      flushLog(folder);
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
      var baseInkName = logicalInkName(base.name);
      var existing = findColorGroup(hostDoc, baseInkName);
      if(!existing){
        log("Wrapping missing group for: " + base.name);
        wrapLayerInGroup(hostDoc, base, "COLOR__" + sanitizeName(baseInkName));
      }
    }

    normalizeCleanLayerGrouping(hostDoc);

    var imported = 0;

    log("Removing old TRAP__ layers...");
    removeOldTrapLayers(hostDoc);

    var skippedSel = 0;

    for(var t=0; t<trapsObj.traps.length; t++){
      var spec = trapsObj.traps[t]; // {source, target, png}
      log("--- Trap #" + (t+1) + " " + spec.source + " over " + spec.target);

      var sourceGroup = findColorGroup(hostDoc, spec.source);
      if(!sourceGroup){
        log("  SKIP: missing COLOR__ group for source: " + spec.source);
        continue;
      }

      var sourceBase = findSourceBaseLayer(sourceGroup, spec.source);
      if(!sourceBase){
        log("  SKIP: no base ArtLayer named 'CLEAN__" + spec.source + "' or '" + spec.source + "' inside " + sourceGroup.name);
        continue;
      }

      var sourceSampleLayer = findSourceSamplingLayer(sourceGroup, spec.source);
      if(!sourceSampleLayer){
        log("  SKIP: no sampling layer named '" + spec.source + "' or 'CLEAN__" + spec.source + "' inside " + sourceGroup.name);
        continue;
      }

      // Sample ink once per source
      if(!INK_COLOR_CACHE[spec.source]){
        cacheLayerInkColor(spec.source, sampleLayerInkColor(hostDoc, sourceSampleLayer));
      }

      var pngFile = new File(folder.fsName + "/" + spec.png);
      if(!pngFile.exists){
        log("  SKIP: missing PNG: " + pngFile.fsName);
        continue;
      }

      hostDoc.selection.deselect();
      log("  PNG: " + pngFile.fsName);

      var gotTrapSelection = false;
      try{
        gotTrapSelection = selectionFromTrapPngIntoHost_ALIGN_BY_BOUNDS(hostDoc, pngFile, spec);
        log("  selectionFromTrapPngIntoHost_ALIGN_BY_BOUNDS=" + gotTrapSelection);
      }catch(eSelBuild){
        log("  ERROR building selection from PNG: " + eSelBuild);
        hostDoc.selection.deselect();
        skippedSel++;
        continue;
      }

      if(!gotTrapSelection){
        log("  SKIP: could not load selection from trap PNG");
        hostDoc.selection.deselect();
        skippedSel++;
        continue;
      }

      if(!hasSelection(hostDoc)){
        log("  SKIP: selection builder returned true but host selection is empty");
        hostDoc.selection.deselect();
        skippedSel++;
        continue;
      }

      try{
        var sb = hostDoc.selection.bounds;
        log("  trap selection bounds px: " +
          sb[0].as("px") + "," + sb[1].as("px") + "," +
          sb[2].as("px") + "," + sb[3].as("px"));
      }catch(eBounds){
        log("  ERROR reading trap selection bounds: " + eBounds);
      }

      var trapName = "TRAP__" + sanitizeName(spec.source) + "_over_" + sanitizeName(spec.target);
      var trapLayer = createTrapLayerInSourceGroup(hostDoc, sourceGroup, sourceBase, trapName);
      applySourceAppearanceToTrap(trapLayer, sourceBase);

      hostDoc.activeLayer = trapLayer;

      try{
        ensureCompositeChannels(hostDoc);
        log("  fill fg color on " + trapName);
        fillSelectionWithLayerColor(spec.source);
        hostDoc.selection.deselect();
        imported++;
        log("  OK Imported: " + trapName + " (in " + sourceGroup.name + ")");
      }catch(eFill){
        log("  FILL ERROR on " + trapName + ": " + eFill);

        try{
          if(hasSelection(hostDoc)){
            var fb = hostDoc.selection.bounds;
            log("  fill-error selection bounds px: " +
              fb[0].as("px") + "," + fb[1].as("px") + "," +
              fb[2].as("px") + "," + fb[3].as("px"));
          }else{
            log("  fill-error: selection is empty");
          }
        }catch(eFillBounds){
          log("  fill-error bounds read failed: " + eFillBounds);
        }

        try{
          trapLayer.remove();
          log("  removed failed trap layer: " + trapName);
        }catch(eRemoveTrap){
          log("  could not remove failed trap layer: " + eRemoveTrap);
        }

        hostDoc.selection.deselect();
        throw eFill;
      }
    }

    log("=== SUMMARY ===");
    log("Imported: " + imported);
    log("Skipped (selection load fail): " + skippedSel);

    // NEW: auto-import debug overlays
    log("Importing debug_*.png masks to top of stack...");
    importDebugMasksToTop(hostDoc, folder);

    flushLog(folder);

    alert("Import complete.\nImported: " + imported + "\n\nSee import_debug_log.txt");

  } catch(eTop){
    log("FATAL: " + eTop);
    if(folder) flushLog(folder);
    else flushLog(null);
    alert("Import failed:\n" + eTop + "\n\nCheck import_debug_log.txt for the last STEP FAIL line.");
  } finally {
    try { app.displayDialogs = prevDialogs; } catch(e3) {}
  }

})();
