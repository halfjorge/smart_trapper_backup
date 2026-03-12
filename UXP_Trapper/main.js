const { entrypoints } = require("uxp");
const { app, core, constants, action } = require("photoshop");
const { localFileSystem, formats } = require("uxp").storage;

const STORAGE_KEY = "smartTrapperSettings";
const EXPORT_ENGINE_VERSION = "dom-save-v4-rgb-convert-debug";
const DEFAULT_JOB_FOLDER = "C:\\Users\\Valued Customer\\Desktop\\TrapJobs";
const DEFAULT_LOG_FOLDER = "C:\\Users\\Valued Customer\\Desktop\\trapper\\UXP_Trapper\\status_logs";

const DEFAULTS = {
  fullDebug: false,
  cutTopKey: false,
  preflightCleanup: false,
  alphaThreshold: 8,
  edgeBiasPx: 0,
  trapPx: 5,
  mode: "auto",
  bridgeUrl: "http://127.0.0.1:8765",
  jobFolder: DEFAULT_JOB_FOLDER,
  logFolder: DEFAULT_LOG_FOLDER
};

function panelMarkup() {
  return `
    <div class="app">
      <div class="hero">
        <div class="eyebrow">Photoshop UXP Panel</div>
        <div class="hero-title">Smart Trapper</div>
        <div class="hero-copy">Single-panel control surface for the existing trapper workflow. This panel stores settings, inspects the active document, and is prepared to hand jobs to a local bridge service.</div>
      </div>

      <div class="panel">
        <div class="section-title">Document</div>
        <button id="refreshDocBtn" class="button secondary">Refresh</button>
        <div id="docSummary" class="summary">No document loaded.</div>
        <div id="layerSummary" class="summary subtle">Waiting for analysis.</div>
      </div>

      <div class="panel">
        <div class="section-title">Run Settings</div>
        <div class="setting-box">
          <label>
            <input id="fullDebug" type="checkbox">
            <span>Full debug logging</span>
          </label>
        </div>
        <div class="setting-box">
          <label>
            <input id="cutTopKey" type="checkbox">
            <span>Cut top key layer out of visible colors</span>
          </label>
        </div>
        <div class="setting-box">
          <label>
            <input id="preflightCleanup" type="checkbox">
            <span>Preflight cleanup</span>
          </label>
        </div>
        <div class="field">
          <div class="field-label">Alpha threshold</div>
          <input id="alphaThreshold" type="number" min="0" max="255" step="1">
        </div>
        <div class="field">
          <div class="field-label">Edge bias (px)</div>
          <input id="edgeBiasPx" type="number" step="1">
        </div>
        <div class="field">
          <div class="field-label">Trap width (px)</div>
          <input id="trapPx" type="number" min="0" step="1">
        </div>
        <div class="field">
          <div class="field-label">Mode</div>
          <select id="mode">
            <option value="auto">Auto detect</option>
            <option value="plates">Plates</option>
            <option value="overprint">Overprint</option>
          </select>
        </div>
      </div>

      <div class="panel">
        <div class="section-title">Bridge</div>
        <div class="field">
          <div class="field-label">Bridge URL</div>
          <div id="bridgeUrlDisplay" class="bridge-display"></div>
        </div>
        <div class="field">
          <div class="field-label">Existing Job Folder</div>
          <div id="jobFolderDisplay" class="bridge-display muted"></div>
        </div>
        <button id="editBridgeBtn" class="button secondary">Edit URL</button>
        <button id="selectJobFolderBtn" class="button secondary">Select Job Folder</button>
        <button id="clearJobFolderBtn" class="button secondary">Clear Job Folder</button>
        <button id="testBridgeBtn" class="button secondary">Test Bridge</button>
        <button id="saveSettingsBtn" class="button secondary">Save Settings</button>
        <div class="hint">The bridge can already run the Rust engine on an existing exported job folder. Full Photoshop export/import parity will be wired into this panel next.</div>
      </div>

      <div class="panel">
        <div class="section-title">Logs</div>
        <div class="field">
          <div class="field-label">Snapshot Log Folder</div>
          <div id="logFolderDisplay" class="bridge-display muted"></div>
        </div>
        <button id="selectLogFolderBtn" class="button secondary">Select Log Folder</button>
        <button id="clearLogFolderBtn" class="button secondary">Clear Log Folder</button>
      </div>

      <div class="panel">
        <div class="section-title">Actions</div>
        <button id="runBtn" class="button primary full">Run Trapper</button>
        <button id="exportMasksBtn" class="button secondary full">Export Masks To Job Folder</button>
        <button id="prepareImportBtn" class="button secondary full">Prepare Import Structure</button>
        <button id="importPlanBtn" class="button secondary full">Build Import Plan</button>
        <button id="importTrapsBtn" class="button secondary full">Import Traps</button>
        <button id="createJobBtn" class="button secondary full">Create Job Folder Skeleton</button>
        <button id="exportConfigBtn" class="button secondary full">Export Settings Snapshot</button>
      </div>

      <div class="panel">
        <div class="section-title">Status</div>
        <button id="saveStatusBtn" class="button secondary">Save Status Snapshot</button>
        <div class="status-shell">
          <div id="status" class="status" tabindex="0"></div>
        </div>
      </div>
    </div>
  `;
}

function createController(rootNode) {
  const els = {};
  let currentJobFolderEntry = null;
  let currentLogFolderEntry = null;
  let statusLog = "";
  let cleanPlacementOffset = null;

  function sanitize(name) {
    return String(name).replace(/[\/\\:*?"<>|]/g, "_");
  }

  function $(id) {
    return rootNode.querySelector("#" + id);
  }

  function bindEls() {
    [
      "refreshDocBtn",
      "fullDebug",
      "cutTopKey",
      "preflightCleanup",
      "alphaThreshold",
      "edgeBiasPx",
      "trapPx",
      "mode",
      "bridgeUrlDisplay",
      "jobFolderDisplay",
      "logFolderDisplay",
      "editBridgeBtn",
      "selectJobFolderBtn",
      "clearJobFolderBtn",
      "selectLogFolderBtn",
      "clearLogFolderBtn",
      "testBridgeBtn",
      "saveSettingsBtn",
      "runBtn",
      "exportMasksBtn",
      "prepareImportBtn",
      "importPlanBtn",
      "importTrapsBtn",
      "createJobBtn",
      "exportConfigBtn",
      "docSummary",
      "layerSummary",
      "saveStatusBtn",
      "status"
    ].forEach((id) => {
      els[id] = $(id);
    });
  }

  function setStatus(msg) {
    const text = String(msg);
    statusLog = text;
    els.status.textContent = statusLog;
    try {
      els.status.parentNode.scrollTop = 0;
    } catch (e) {}
  }

  function appendStatus(msg) {
    const text = String(msg);
    statusLog = statusLog ? (statusLog + "\n\n" + text) : text;
    els.status.textContent = statusLog;
    try {
      els.status.parentNode.scrollTop = els.status.parentNode.scrollHeight;
    } catch (e) {}
  }

  function nowMs() {
    return Date.now();
  }

  function elapsedMs(startMs) {
    return nowMs() - startMs;
  }

  async function showCompletionAlert(label) {
    const message = String(label) + " complete.";
    try {
      if (app && typeof app.showAlert === "function") {
        await app.showAlert(message);
        return;
      }
    } catch (e) {}
    try {
      window.alert(message);
    } catch (e) {}
  }

  function bindActionWithCompletionAlert(el, label, handler) {
    el.addEventListener("click", async () => {
      try {
        await handler();
      } finally {
        await showCompletionAlert(label);
      }
    });
  }

  function getSettings() {
    const normalizeFolderDisplayValue = (value, fallback) => {
      const text = String(value || "").trim();
      if (!text || text === "(none selected)") return fallback;
      return text;
    };
    return {
      fullDebug: !!els.fullDebug.checked,
      cutTopKey: !!els.cutTopKey.checked,
      preflightCleanup: !!els.preflightCleanup.checked,
      alphaThreshold: Number(els.alphaThreshold.value || DEFAULTS.alphaThreshold),
      edgeBiasPx: Number(els.edgeBiasPx.value || DEFAULTS.edgeBiasPx),
      trapPx: Number(els.trapPx.value || DEFAULTS.trapPx),
      mode: els.mode.value || DEFAULTS.mode,
      bridgeUrl: String(els.bridgeUrlDisplay.textContent || DEFAULTS.bridgeUrl).trim(),
      jobFolder: normalizeFolderDisplayValue(els.jobFolderDisplay.textContent, DEFAULTS.jobFolder),
      logFolder: normalizeFolderDisplayValue(els.logFolderDisplay.textContent, DEFAULTS.logFolder)
    };
  }

  function applySettings(settings) {
    const s = Object.assign({}, DEFAULTS, settings || {});
    els.fullDebug.checked = !!s.fullDebug;
    els.cutTopKey.checked = !!s.cutTopKey;
    els.preflightCleanup.checked = !!s.preflightCleanup;
    els.alphaThreshold.value = String(s.alphaThreshold);
    els.edgeBiasPx.value = String(s.edgeBiasPx);
    els.trapPx.value = String(s.trapPx);
    els.mode.value = s.mode;
    els.bridgeUrlDisplay.textContent = s.bridgeUrl;
    els.jobFolderDisplay.textContent = String(s.jobFolder || "").trim() || DEFAULTS.jobFolder;
    els.logFolderDisplay.textContent = String(s.logFolder || "").trim() || DEFAULTS.logFolder;
  }

  function loadSettings() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return applySettings(DEFAULTS);
      const parsed = JSON.parse(raw) || {};
      if (!String(parsed.jobFolder || "").trim() || parsed.jobFolder === "(none selected)") {
        parsed.jobFolder = DEFAULTS.jobFolder;
      }
      if (!String(parsed.logFolder || "").trim() || parsed.logFolder === "(none selected)") {
        parsed.logFolder = DEFAULTS.logFolder;
      }
      applySettings(parsed);
    } catch (e) {
      applySettings(DEFAULTS);
      setStatus("Settings load fallback:\n" + e);
    }
  }

  function saveSettings() {
    const settings = getSettings();
    localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
    setStatus("Settings saved.\n\n" + JSON.stringify(settings, null, 2));
  }

  async function ensureSubfolder(folderEntry, name) {
    try {
      return await folderEntry.getEntry(name);
    } catch (e) {
      return await folderEntry.createFolder(name);
    }
  }

  async function writeJsonFile(folderEntry, fileName, data) {
    const file = await folderEntry.createFile(fileName, { overwrite: true });
    await file.write(JSON.stringify(data, null, 2));
    return file;
  }

  async function writeTextFile(folderEntry, fileName, text) {
    const file = await folderEntry.createFile(fileName, { overwrite: true });
    await file.write(text);
    return file;
  }

  async function readJsonFile(folderEntry, fileName) {
    const file = await folderEntry.getEntry(fileName);
    const text = await file.read();
    return JSON.parse(text);
  }

  async function readOptionalJsonFile(folderEntry, fileName) {
    try {
      return await readJsonFile(folderEntry, fileName);
    } catch (e) {
      return null;
    }
  }

  function timeStampForFolderName() {
    return new Date().toISOString().replace(/[:.]/g, "-");
  }

  function statusStamp(label) {
    return "=== " + label + " @ " + new Date().toISOString() + " ===";
  }

  async function entryExists(folderEntry, name) {
    try {
      await folderEntry.getEntry(name);
      return true;
    } catch (e) {
      return false;
    }
  }

  async function looksLikeJobFolder(folderEntry) {
    const hasMasks = await entryExists(folderEntry, "masks");
    const hasTraps = await entryExists(folderEntry, "traps");
    const hasJob = await entryExists(folderEntry, "job.json");
    return hasMasks || hasTraps || hasJob;
  }

  async function createTimestampedJobFolderUnder(baseFolder, doc) {
    const safeTitle = String(doc.title || "document").replace(/[\\/:*?"<>|]/g, "_");
    const folderName = safeTitle + "__UXP__" + timeStampForFolderName();
    const jobFolder = await baseFolder.createFolder(folderName);
    await jobFolder.createFolder("masks");
    await jobFolder.createFolder("traps");
    currentJobFolderEntry = jobFolder;
    els.jobFolderDisplay.textContent = jobFolder.nativePath || folderName;
    return jobFolder;
  }

  async function tryBindFolderEntryFromPath(pathText) {
    const path = String(pathText || "").trim();
    if (!path || path === "(none selected)") return null;
    const normalized = path.replace(/\\/g, "/");
    try {
      return await localFileSystem.getEntryWithUrl("file:" + normalized);
    } catch (e) {
      return null;
    }
  }

  async function rebindFolderEntriesFromSettings() {
    const s = getSettings();
    currentJobFolderEntry = await tryBindFolderEntryFromPath(s.jobFolder);
    currentLogFolderEntry = await tryBindFolderEntryFromPath(s.logFolder);
  }

  async function ensureRunJobFolder(doc) {
    if (!currentJobFolderEntry) {
      throw new Error("No job/base folder selected. Create or select a folder first.");
    }

    if (await looksLikeJobFolder(currentJobFolderEntry)) {
      return currentJobFolderEntry;
    }

    return await createTimestampedJobFolderUnder(currentJobFolderEntry, doc);
  }

  function flattenTopLevelLayers(doc) {
    const out = [];
    if (!doc || !doc.layers) return out;
    for (const layer of doc.layers) out.push(layer);
    return out;
  }

  function topLevelLayerMeta(layer, index) {
    let blendMode = "(unknown)";
    let opacity = 100;
    let fillOpacity = 100;
    let visible = true;
    let kind = "(unknown)";

    try { blendMode = String(layer.blendMode); } catch (e) {}
    try { opacity = Number(layer.opacity); } catch (e) {}
    try { fillOpacity = Number(layer.fillOpacity); } catch (e) {}
    try { visible = !!layer.visible; } catch (e) {}
    try { kind = String(layer.kind); } catch (e) {}

    return {
      index,
      name: layer.name,
      kind,
      visible,
      blendMode,
      opacity,
      fillOpacity
    };
  }

  function buildCurrentJobSpec(doc) {
    const layers = flattenTopLevelLayers(doc).map((layer, index) => ({
      layer,
      meta: topLevelLayerMeta(layer, index)
    }));

    const keyLayer = layers.length ? layers[0] : null;
    const paperLayer = layers.length ? layers[layers.length - 1] : null;
    const colorLayersBottomToTop = [];

    for (let i = layers.length - 2; i >= 1; i -= 1) {
      const entry = layers[i];
      if (!entry) continue;
      if (!entry.meta.visible) continue;
      if (entry.meta.kind === "group") continue;
      colorLayersBottomToTop.push(entry);
    }

      const job = {
        docName: doc.title,
        widthPx: Math.round(Number(doc.width)),
        heightPx: Math.round(Number(doc.height)),
        resolution: Number(doc.resolution),
        cutTopKey: !!getSettings().cutTopKey,
        preflightCleanup: !!getSettings().preflightCleanup,
        alphaThreshold: Number(getSettings().alphaThreshold || DEFAULTS.alphaThreshold),
        edgeBiasPx: Number(getSettings().edgeBiasPx || DEFAULTS.edgeBiasPx),
        keyLayerName: keyLayer ? keyLayer.meta.name : "",
        paperLayerName: paperLayer ? paperLayer.meta.name : "",
        colors: [],
        files: []
      };

    if (keyLayer) {
      job.files.push({
        kind: "KEY",
        name: keyLayer.meta.name,
        blendMode: keyLayer.meta.blendMode,
        opacity: keyLayer.meta.opacity,
        fillOpacity: keyLayer.meta.fillOpacity,
        png: "masks/" + ("KEY_" + sanitize(keyLayer.meta.name) + ".png")
      });
    }

    colorLayersBottomToTop.forEach((entry, idx) => {
      job.colors.push({
        name: entry.meta.name,
        blendMode: entry.meta.blendMode,
        opacity: entry.meta.opacity,
        fillOpacity: entry.meta.fillOpacity
      });

      job.files.push({
        kind: "COLOR",
        name: entry.meta.name,
        blendMode: entry.meta.blendMode,
        opacity: entry.meta.opacity,
        fillOpacity: entry.meta.fillOpacity,
        png: "masks/" + ((idx + 1) + "_" + sanitize(entry.meta.name) + ".png")
      });
    });

    return {
      job,
      topLevelLayers: layers.map((entry) => entry.meta),
      inferred: {
        topKeyLayer: keyLayer ? keyLayer.meta.name : null,
        bottomPaperLayer: paperLayer ? paperLayer.meta.name : null,
        visibleColorLayersBottomToTop: colorLayersBottomToTop.map((entry) => entry.meta.name)
      }
    };
  }

  function sanitizeInkName(name) {
    return sanitize(String(name || "").trim());
  }

  function logicalInkName(name) {
    const text = String(name || "");
    return (text.indexOf("CLEAN__") === 0) ? text.substring(7) : text;
  }

  function isGroupLikeLayer(layer) {
    if (!layer) return false;
    try {
      if (layer.layers && layer.layers.length >= 0) {
        return true;
      }
    } catch (e) {}
    try {
      return layer.kind === "group";
    } catch (e) {
      return false;
    }
  }

  function layerIdOf(layer) {
    if (!layer) return null;
    return layer._id || layer.id || null;
  }

  async function selectLayerById(layerId, commandName) {
    if (!layerId) throw new Error("Missing layer ID for selection");
    return await core.executeAsModal(async () => {
      return await action.batchPlay(
        [{
          _obj: "select",
          _target: [{ _ref: "layer", _id: layerId }],
          makeVisible: false,
          _options: { dialogOptions: "dontDisplay" }
        }],
        {}
      );
    }, { commandName: commandName || "Select Layer" });
  }

  async function wrapLayerInGroupUxp(layer, groupName) {
    const layerId = layerIdOf(layer);
    if (!layerId) {
      throw new Error("Could not resolve layer ID for " + (layer ? layer.name : "(unknown layer)"));
    }

    await core.executeAsModal(async () => {
      await action.batchPlay(
        [
          {
            _obj: "select",
            _target: [{ _ref: "layer", _id: layerId }],
            makeVisible: false,
            _options: { dialogOptions: "dontDisplay" }
          },
          {
            _obj: "make",
            _target: [{ _ref: "layerSection" }],
            from: { _ref: "layer", _enum: "ordinal", _value: "targetEnum" },
            _options: { dialogOptions: "dontDisplay" }
          },
          {
            _obj: "set",
            _target: [{ _ref: "layer", _enum: "ordinal", _value: "targetEnum" }],
            to: {
              _obj: "layer",
              name: groupName
            },
            _options: { dialogOptions: "dontDisplay" }
          }
        ],
        {}
      );
    }, { commandName: "Prepare Import Structure" });
  }

  async function getEntryByRelativePath(folderEntry, relativePath) {
    const parts = String(relativePath || "").split(/[\\/]+/).filter(Boolean);
    let current = folderEntry;
    for (let i = 0; i < parts.length; i += 1) {
      current = await current.getEntry(parts[i]);
    }
    return current;
  }

  function toUint8Array(data) {
    if (!data) return null;
    if (data instanceof Uint8Array) return data;
    if (data instanceof ArrayBuffer) return new Uint8Array(data);
    if (data.buffer instanceof ArrayBuffer) return new Uint8Array(data.buffer);
    return null;
  }

  function parsePngDpiFromBytes(bytes) {
    if (!bytes || bytes.length < 8) return null;
    const sig = [137, 80, 78, 71, 13, 10, 26, 10];
    for (let i = 0; i < sig.length; i += 1) {
      if (bytes[i] !== sig[i]) return null;
    }

    let offset = 8;
    while (offset + 12 <= bytes.length) {
      const len =
        ((bytes[offset] << 24) >>> 0) +
        ((bytes[offset + 1] << 16) >>> 0) +
        ((bytes[offset + 2] << 8) >>> 0) +
        (bytes[offset + 3] >>> 0);
      const type = String.fromCharCode(
        bytes[offset + 4],
        bytes[offset + 5],
        bytes[offset + 6],
        bytes[offset + 7]
      );
      const dataStart = offset + 8;
      if (type === "pHYs" && len >= 9 && dataStart + len <= bytes.length) {
        const ppux =
          ((bytes[dataStart] << 24) >>> 0) +
          ((bytes[dataStart + 1] << 16) >>> 0) +
          ((bytes[dataStart + 2] << 8) >>> 0) +
          (bytes[dataStart + 3] >>> 0);
        const unit = bytes[dataStart + 8];
        if (unit === 1 && ppux > 0) {
          return ppux * 0.0254;
        }
      }
      offset = dataStart + len + 4;
    }
    return null;
  }

  async function getPngDpi(fileEntry) {
    try {
      const raw = await fileEntry.read({ format: formats.binary });
      const bytes = toUint8Array(raw);
      return parsePngDpiFromBytes(bytes);
    } catch (e) {
      return null;
    }
  }

  async function scaleTargetLayerPercent(scalePercent, commandName) {
    const pct = Number(scalePercent || 100);
    return await core.executeAsModal(async () => {
      return await action.batchPlay(
        [{
          _obj: "transform",
          _target: [{ _ref: "layer", _enum: "ordinal", _value: "targetEnum" }],
          freeTransformCenterState: { _enum: "quadCenterState", _value: "QCSAverage" },
          offset: {
            _obj: "offset",
            horizontal: { _unit: "pixelsUnit", _value: 0 },
            vertical: { _unit: "pixelsUnit", _value: 0 }
          },
          width: { _unit: "percentUnit", _value: pct },
          height: { _unit: "percentUnit", _value: pct },
          linked: true,
          _options: { dialogOptions: "dontDisplay" }
        }],
        {}
      );
    }, { commandName: commandName || "Scale Placed Layer" });
  }

  async function translateTargetLayerPixels(dx, dy, commandName) {
    const deltaX = Number(dx || 0);
    const deltaY = Number(dy || 0);
    return await core.executeAsModal(async () => {
      return await action.batchPlay(
        [{
          _obj: "move",
          _target: [{ _ref: "layer", _enum: "ordinal", _value: "targetEnum" }],
          to: {
            _obj: "offset",
            horizontal: { _unit: "pixelsUnit", _value: deltaX },
            vertical: { _unit: "pixelsUnit", _value: deltaY }
          },
          _options: { dialogOptions: "dontDisplay" }
        }],
        {}
      );
    }, { commandName: commandName || "Translate Target Layer" });
  }

  async function getTargetLayerBoundsPx() {
    const result = await core.executeAsModal(async () => {
      return await action.batchPlay(
        [{
          _obj: "get",
          _target: [{ _ref: "layer", _enum: "ordinal", _value: "targetEnum" }],
          _options: { dialogOptions: "dontDisplay" }
        }],
        {}
      );
    }, { commandName: "Get Target Layer Bounds" });

    const desc = (result && result[0]) || {};
    const b = desc.boundsNoEffects || desc.bounds || null;
    if (!b) return null;
    const left = Number((b.left && b.left._value) || b.left || 0);
    const top = Number((b.top && b.top._value) || b.top || 0);
    const right = Number((b.right && b.right._value) || b.right || 0);
    const bottom = Number((b.bottom && b.bottom._value) || b.bottom || 0);
    return {
      left,
      top,
      right,
      bottom,
      width: Math.max(0, right - left),
      height: Math.max(0, bottom - top)
    };
  }

  async function getLayerBoundsById(layerId, commandName) {
    if (!layerId) return null;
    const sel = await selectLayerById(layerId, commandName || "Select Layer For Bounds");
    if (batchPlayResultHasError(sel)) return null;
    return await getTargetLayerBoundsPx();
  }

  async function alignTargetToReferenceBounds(referenceBounds, labelPrefix, options) {
    const label = String(labelPrefix || "align");
    const opts = options || {};
    const allowScale = !!opts.allowScale;
    const allowMove = (typeof opts.allowMove === "boolean") ? opts.allowMove : true;
    let note = label + ": skipped";
    if (!referenceBounds || referenceBounds.width <= 0 || referenceBounds.height <= 0) {
      return { note, aligned: false, placedAfter: null };
    }

    let placedBefore = await getTargetLayerBoundsPx();
    if (!placedBefore || placedBefore.width <= 0 || placedBefore.height <= 0) {
      return { note: label + ": no target bounds", aligned: false, placedAfter: null };
    }

    const widthRatio = referenceBounds.width / placedBefore.width;
    const heightRatio = referenceBounds.height / placedBefore.height;
    const ratioDelta = Math.max(Math.abs(widthRatio - 1), Math.abs(heightRatio - 1));
    const refCx = (referenceBounds.left + referenceBounds.right) / 2;
    const refCy = (referenceBounds.top + referenceBounds.bottom) / 2;
    const dstCx = (placedBefore.left + placedBefore.right) / 2;
    const dstCy = (placedBefore.top + placedBefore.bottom) / 2;
    const centerDx0 = refCx - dstCx;
    const centerDy0 = refCy - dstCy;
    const centerDist = Math.max(Math.abs(centerDx0), Math.abs(centerDy0));
    const shouldScale = allowScale && ratioDelta > 0.15;
    const shouldMove = allowMove && centerDist > 10;
    let aligned = false;

    note =
      label +
      " ref=[" + fmtBounds(referenceBounds) + "]" +
      " dstBefore=[" + fmtBounds(placedBefore) + "]" +
      " ratioDelta=" + ratioDelta.toFixed(4) +
      " centerDx=" + centerDx0.toFixed(2) +
      " centerDy=" + centerDy0.toFixed(2);

    if (shouldScale) {
      const scalePct = ((widthRatio + heightRatio) / 2) * 100;
      const scaleResult = await scaleTargetLayerPercent(scalePct, "Align Placed Layer Scale");
      if (!batchPlayResultHasError(scaleResult)) {
        aligned = true;
        note += " | scaleFix=" + scalePct.toFixed(4) + "%";
        placedBefore = await getTargetLayerBoundsPx();
      } else {
        note += " | scaleFixFailed";
      }
    }

    if (shouldMove || shouldScale) {
      const current = placedBefore || (await getTargetLayerBoundsPx());
      if (current) {
        const curCx = (current.left + current.right) / 2;
        const curCy = (current.top + current.bottom) / 2;
        const moveDx = refCx - curCx;
        const moveDy = refCy - curCy;
        if (Math.abs(moveDx) > 0.5 || Math.abs(moveDy) > 0.5) {
          const moveResult = await translateTargetLayerPixels(moveDx, moveDy, "Align Placed Layer Offset");
          if (!batchPlayResultHasError(moveResult)) {
            aligned = true;
            const placedAfter = await getTargetLayerBoundsPx();
            note += " | moveFix=(" + moveDx.toFixed(2) + "," + moveDy.toFixed(2) + ")";
            note += " | dstAfter=[" + fmtBounds(placedAfter) + "]";
            return { note, aligned, placedAfter };
          }
          note += " | moveFixFailed";
        }
      }
    }

    return { note, aligned, placedAfter: await getTargetLayerBoundsPx() };
  }

  function fmtBounds(bounds) {
    if (!bounds) return "(none)";
    return (
      "L=" + bounds.left.toFixed(2) +
      " T=" + bounds.top.toFixed(2) +
      " R=" + bounds.right.toFixed(2) +
      " B=" + bounds.bottom.toFixed(2) +
      " W=" + bounds.width.toFixed(2) +
      " H=" + bounds.height.toFixed(2)
    );
  }

  async function placeTrapPngIntoDocument(fileEntry) {
    const token = localFileSystem.createSessionToken(fileEntry);
    const placeResult = await core.executeAsModal(async () => {
      return await action.batchPlay(
        [{
          _obj: "placeEvent",
          null: {
            _path: token,
            _kind: "local"
          },
          linked: false,
          _options: { dialogOptions: "dontDisplay" }
        }],
        {}
      );
    }, { commandName: "Import Trap PNG" });

    appendStatus("  place normalization: disabled (native placeEvent coordinates)");

    return placeResult;
  }

  async function renameTargetLayer(newName) {
    return await core.executeAsModal(async () => {
      return await action.batchPlay(
        [{
          _obj: "set",
          _target: [{ _ref: "layer", _enum: "ordinal", _value: "targetEnum" }],
          to: {
            _obj: "layer",
            name: newName
          },
          _options: { dialogOptions: "dontDisplay" }
        }],
        {}
      );
    }, { commandName: "Rename Trap Layer" });
  }

  async function applyColorOverlayToTargetLayer(rgb) {
    const color = rgb || {};
    return await core.executeAsModal(async () => {
      return await action.batchPlay(
        [{
          _obj: "set",
          _target: [{ _ref: "layer", _enum: "ordinal", _value: "targetEnum" }],
          to: {
            _obj: "layer",
            layerEffects: {
              _obj: "layerEffects",
              scale: { _unit: "percentUnit", _value: 100 },
              solidFill: {
                _obj: "solidFill",
                enabled: true,
                present: true,
                showInDialog: false,
                mode: { _enum: "blendMode", _value: "normal" },
                opacity: { _unit: "percentUnit", _value: 100 },
                color: {
                  _obj: "RGBColor",
                  red: Number(color.r || 0),
                  green: Number(color.g || 0),
                  blue: Number(color.b || 0)
                }
              }
            }
          },
          _options: { dialogOptions: "dontDisplay" }
        }],
        {}
      );
    }, { commandName: "Apply Trap Color Overlay" });
  }

  async function loadSelectionFromTargetTransparency() {
    return await core.executeAsModal(async () => {
      return await action.batchPlay(
        [{
          _obj: "set",
          _target: [{ _ref: "channel", _property: "selection" }],
          to: { _ref: "channel", _enum: "channel", _value: "transparencyEnum" },
          _options: { dialogOptions: "dontDisplay" }
        }],
        {}
      );
    }, { commandName: "Load Trap Transparency Selection" });
  }

  async function deselectSelection() {
    return await core.executeAsModal(async () => {
      return await action.batchPlay(
        [{
          _obj: "set",
          _target: [{ _ref: "channel", _property: "selection" }],
          to: { _enum: "ordinal", _value: "none" },
          _options: { dialogOptions: "dontDisplay" }
        }],
        {}
      );
    }, { commandName: "Deselect Selection" });
  }

  async function createLayerAboveCurrent(newName) {
    return await core.executeAsModal(async () => {
      return await action.batchPlay(
        [{
          _obj: "make",
          _target: [{ _ref: "layer" }],
          using: {
            _obj: "layer",
            name: newName
          },
          _options: { dialogOptions: "dontDisplay" }
        }],
        {}
      );
    }, { commandName: "Create Trap Fill Layer" });
  }

  async function fillSelectionWithRgb(rgb) {
    const color = rgb || {};
    return await core.executeAsModal(async () => {
      return await action.batchPlay(
        [{
          _obj: "fill",
          using: { _enum: "fillContents", _value: "color" },
          color: {
            _obj: "RGBColor",
            red: Number(color.r || 0),
            green: Number(color.g || 0),
            blue: Number(color.b || 0)
          },
          opacity: { _unit: "percentUnit", _value: 100 },
          mode: { _enum: "blendMode", _value: "normal" },
          _options: { dialogOptions: "dontDisplay" }
        }],
        {}
      );
    }, { commandName: "Fill Trap Selection" });
  }

  async function setLayerVisibilityById(layerId, visible, commandName) {
    if (!layerId) throw new Error("Missing layer ID for visibility set");
    const wantVisible = !!visible;
    return await core.executeAsModal(async () => {
      return await action.batchPlay(
        [{
          _obj: wantVisible ? "show" : "hide",
          _target: [{ _ref: "layer", _id: layerId }],
          _options: { dialogOptions: "dontDisplay" }
        }],
        {}
      );
    }, { commandName: commandName || (wantVisible ? "Show Layer" : "Hide Layer") });
  }

  async function hideOriginalLayersWhenCleanExists(doc) {
    const layers = flattenTopLevelLayers(doc);
    let hidden = 0;
    let failed = 0;
    let checkedGroups = 0;
    const details = [];
    for (let i = 0; i < layers.length; i += 1) {
      const group = layers[i];
      if (!group || !isGroupLikeLayer(group)) continue;
      if (String(group.name || "").indexOf("COLOR__") !== 0) continue;
      checkedGroups += 1;

      const logicalName = String(group.name || "").substring(7);
      const cleanName = "CLEAN__" + logicalName;
      const cleanLayer = findArtLayerByNameInfo(group, cleanName);
      const originalLayer = findArtLayerByNameInfo(group, logicalName);
      if (!cleanLayer || !originalLayer || cleanLayer.__descriptor || originalLayer.__descriptor) continue;

      const originalId = layerIdOf(originalLayer);
      if (!originalId) continue;
      try {
        await setLayerVisibilityById(originalId, false, "Hide Original Layer After CLEAN Sync");
        hidden += 1;
        details.push("  hidden: " + originalLayer.name + " (group " + group.name + ")");
      } catch (e) {
        failed += 1;
        details.push("  hide failed: " + originalLayer.name + " (group " + group.name + ") :: " + String(e));
      }
    }
    return { checkedGroups, hidden, failed, details };
  }

  async function buildCleanLayerInGroup(group, sourceName, maskColors, placementOptions) {
    if (!currentJobFolderEntry) {
      return { ok: false, message: "No job folder selected for clean layer import" };
    }

    const cleanFileName = "clean_masks/CLEAN__" + sanitize(sourceName) + ".png";
    const cleanPngEntry = await getEntryByRelativePath(currentJobFolderEntry, cleanFileName);
    const cleanPngDpi = await getPngDpi(cleanPngEntry);
    let docRes = 0;
    let docWidth = 0;
    let docHeight = 0;
    try {
      const d = app.activeDocument;
      docRes = Number(d.resolution || 0);
      docWidth = Number((d.width && d.width.value) || d.width || 0);
      docHeight = Number((d.height && d.height.value) || d.height || 0);
    } catch (e) {}
    const sourceColor = maskColors[sourceName] || null;
    if (!sourceColor) {
      return { ok: false, message: "No source color metadata for " + sourceName };
    }

    const cleanName = "CLEAN__" + sourceName;
    const existingClean = findArtLayerByNameInfo(group, cleanName);
    if (existingClean && !existingClean.__descriptor) {
      const existingCleanId = layerIdOf(existingClean);
      if (existingCleanId) {
        await deleteLayerById(existingCleanId, "Delete Existing CLEAN Layer");
      }
    }

    const originalLayer =
      findArtLayerByNameInfo(group, sourceName) ||
      findSourceBaseLayerInfo(group, sourceName);
    if (!originalLayer || originalLayer.__descriptor) {
      return { ok: false, message: "Original source layer not found for " + sourceName };
    }

    const originalLayerId = layerIdOf(originalLayer);
    if (!originalLayerId) {
      return { ok: false, message: "Missing original source layer ID for " + sourceName };
    }
    const sourceBounds = await getLayerBoundsById(originalLayerId, "Get Source Bounds For CLEAN");

    const placeResult = await placeTrapPngIntoDocument(cleanPngEntry);
    if (batchPlayResultHasError(placeResult)) {
      return { ok: false, message: "Clean PNG place failed\n" + summarizeBatchPlayResult(placeResult) };
    }

    let originalPlacedId = 0;
    try {
      const activeLayers = app.activeDocument.activeLayers || [];
      if (activeLayers.length) {
        originalPlacedId = Number(layerIdOf(activeLayers[0]) || 0);
      }
    } catch (e) {}

    const renameResult = await renameTargetLayer(cleanName + "__PLACED_TMP");
    if (batchPlayResultHasError(renameResult)) {
      return { ok: false, message: "Clean temp rename failed\n" + summarizeBatchPlayResult(renameResult) };
    }

    let placedBoundsBefore = await getTargetLayerBoundsPx();
    let placementFixNote = "placement check skipped";
    let observedOffset = null;
    if (sourceBounds && placedBoundsBefore && placedBoundsBefore.width > 0 && placedBoundsBefore.height > 0) {
      const widthRatio = sourceBounds.width / placedBoundsBefore.width;
      const heightRatio = sourceBounds.height / placedBoundsBefore.height;
      const ratioDelta = Math.max(
        Math.abs(widthRatio - 1),
        Math.abs(heightRatio - 1)
      );
      const sourceCenterX = (sourceBounds.left + sourceBounds.right) / 2;
      const sourceCenterY = (sourceBounds.top + sourceBounds.bottom) / 2;
      const placedCenterX = (placedBoundsBefore.left + placedBoundsBefore.right) / 2;
      const placedCenterY = (placedBoundsBefore.top + placedBoundsBefore.bottom) / 2;
      const centerDx = sourceCenterX - placedCenterX;
      const centerDy = sourceCenterY - placedCenterY;
      const centerDist = Math.max(Math.abs(centerDx), Math.abs(centerDy));
      const forcedOffset =
        (placementOptions && placementOptions.forcedOffset)
          ? {
              dx: Number(placementOptions.forcedOffset.dx || 0),
              dy: Number(placementOptions.forcedOffset.dy || 0)
            }
          : null;
      const shouldFixScale = ratioDelta > 0.15 && !forcedOffset;
      const shouldFixShift = centerDist > 10;
      placementFixNote =
        "source=[" + fmtBounds(sourceBounds) + "] placedBefore=[" + fmtBounds(placedBoundsBefore) + "] " +
        "ratioDelta=" + ratioDelta.toFixed(4) + " centerDx=" + centerDx.toFixed(2) + " centerDy=" + centerDy.toFixed(2);

      if (forcedOffset) {
        observedOffset = { dx: forcedOffset.dx, dy: forcedOffset.dy };
        placementFixNote +=
          " | usingForcedOffset=(" +
          observedOffset.dx.toFixed(2) + "," +
          observedOffset.dy.toFixed(2) + ")";
      } else if (ratioDelta <= 0.02) {
        observedOffset = { dx: centerDx, dy: centerDy };
      }

      if (shouldFixScale) {
        const scalePct = ((widthRatio + heightRatio) / 2) * 100;
        const scaleResult = await scaleTargetLayerPercent(scalePct, "Fix CLEAN Placed Scale");
        if (!batchPlayResultHasError(scaleResult)) {
          placedBoundsBefore = await getTargetLayerBoundsPx();
          placementFixNote += " | scaleFix=" + scalePct.toFixed(4) + "%";
        } else {
          placementFixNote += " | scaleFixFailed";
        }
      }

      if (shouldFixShift || shouldFixScale || observedOffset) {
        const currentBounds = placedBoundsBefore || (await getTargetLayerBoundsPx());
        if (currentBounds) {
          const curCx = (currentBounds.left + currentBounds.right) / 2;
          const curCy = (currentBounds.top + currentBounds.bottom) / 2;
          const moveDx = observedOffset ? observedOffset.dx : (sourceCenterX - curCx);
          const moveDy = observedOffset ? observedOffset.dy : (sourceCenterY - curCy);
          if (Math.abs(moveDx) > 0.5 || Math.abs(moveDy) > 0.5) {
            const moveResult = await translateTargetLayerPixels(moveDx, moveDy, "Fix CLEAN Placed Offset");
            if (!batchPlayResultHasError(moveResult)) {
              const placedAfter = await getTargetLayerBoundsPx();
              placementFixNote += " | moveFix=(" + moveDx.toFixed(2) + "," + moveDy.toFixed(2) + ")";
              placementFixNote += " | placedAfter=[" + fmtBounds(placedAfter) + "]";
            } else {
              placementFixNote += " | moveFixFailed";
            }
          }
        }
      }
    }

    const selectTransparency = await loadSelectionFromTargetTransparency();
    if (batchPlayResultHasError(selectTransparency)) {
      return { ok: false, message: "Clean transparency selection failed\n" + summarizeBatchPlayResult(selectTransparency) };
    }

    const selectOrig = await selectLayerById(originalLayerId, "Select Source Layer For CLEAN Fill");
    if (batchPlayResultHasError(selectOrig)) {
      return { ok: false, message: "Source layer select failed\n" + summarizeBatchPlayResult(selectOrig) };
    }

    const makeCleanLayer = await createLayerAboveCurrent(cleanName);
    if (batchPlayResultHasError(makeCleanLayer)) {
      return { ok: false, message: "CLEAN layer creation failed\n" + summarizeBatchPlayResult(makeCleanLayer) };
    }

    const fillResult = await fillSelectionWithRgb(sourceColor);
    if (batchPlayResultHasError(fillResult)) {
      return { ok: false, message: "CLEAN fill failed\n" + summarizeBatchPlayResult(fillResult) };
    }

    try {
      await deselectSelection();
    } catch (e) {}

    if (originalPlacedId) {
      await deleteLayerById(originalPlacedId, "Delete Original Placed CLEAN Temp");
    }

    try {
      await setLayerVisibilityById(originalLayerId, false, "Hide Original Source Layer");
    } catch (e) {}

    return {
      ok: true,
      cleanName,
      color: sourceColor,
      ratioDelta: (sourceBounds && placedBoundsBefore && placedBoundsBefore.width > 0 && placedBoundsBefore.height > 0)
        ? Math.max(
            Math.abs((sourceBounds.width / placedBoundsBefore.width) - 1),
            Math.abs((sourceBounds.height / placedBoundsBefore.height) - 1)
          )
        : null,
      observedOffset,
      placementFixNote,
      placementDebug: [
        "source=" + sourceName,
        "cleanPng=" + cleanFileName,
        "pngDpi=" + (cleanPngDpi ? cleanPngDpi.toFixed(4) : "missing"),
        "docRes=" + (docRes ? docRes.toFixed(4) : "unknown"),
        "docSize=" + docWidth + "x" + docHeight,
        "sourceBounds=[" + fmtBounds(sourceBounds) + "]",
        "placement=" + placementFixNote
      ].join(" | ")
    };
  }

  async function deleteLayerById(layerId, commandName) {
    if (!layerId) throw new Error("Missing layer ID for delete");
    return await core.executeAsModal(async () => {
      return await action.batchPlay(
        [{
          _obj: "delete",
          _target: [{ _ref: "layer", _id: layerId }],
          _options: { dialogOptions: "dontDisplay" }
        }],
        {}
      );
    }, { commandName: commandName || "Delete Layer" });
  }

  async function duplicateTargetLayerIntoGroup(groupLayer) {
    const groupId = layerIdOf(groupLayer);
    if (!groupId) throw new Error("Could not resolve destination group ID for " + groupLayer.name);
    const result = await core.executeAsModal(async () => {
      return await action.batchPlay(
        [{
          _obj: "duplicate",
          _target: [{ _ref: "layer", _enum: "ordinal", _value: "targetEnum" }],
          to: { _ref: "layer", _id: groupId },
          _options: { dialogOptions: "dontDisplay" }
        }],
        {}
      );
    }, { commandName: "Duplicate Trap Layer Into Group" });
    let duplicatedLayerId = null;
    let duplicatedLayerName = null;
    try {
      const activeLayers = app.activeDocument.activeLayers || [];
      if (activeLayers.length > 0) {
        duplicatedLayerId = Number(layerIdOf(activeLayers[0]) || 0) || null;
        duplicatedLayerName = activeLayers[0].name || null;
      }
    } catch (e) {}

    return {
      result,
      duplicatedLayerId,
      duplicatedLayerName
    };
  }

  function batchPlayResultHasError(result) {
    if (!result) return false;
    const items = Array.isArray(result) ? result : [result];
    for (let i = 0; i < items.length; i += 1) {
      const item = items[i];
      if (!item) continue;
      if (item._obj === "error") return true;
      if (typeof item.message === "string" && item.message) return true;
      if (typeof item.result === "number" && item.result < 0) return true;
    }
    return false;
  }

  function summarizeBatchPlayResult(result) {
    if (result == null) return "(no result)";
    const items = Array.isArray(result) ? result : [result];
    const lines = [];
    for (let i = 0; i < items.length; i += 1) {
      const item = items[i] || {};
      const obj = item._obj || "(no _obj)";
      const pieces = [obj];
      if (item.message) pieces.push("message=" + item.message);
      if (typeof item.result !== "undefined") pieces.push("result=" + item.result);
      if (item.name) pieces.push("name=" + item.name);
      lines.push(pieces.join(" | "));
    }
    return lines.join("\n");
  }

  function findColorGroupInfo(doc, sourceName) {
    const want = "COLOR__" + sanitizeInkName(sourceName);
    const walk = (container) => {
      const layers = container.layers || [];
      for (let i = 0; i < layers.length; i += 1) {
        const layer = layers[i];
        if (!isGroupLikeLayer(layer)) continue;
        if (layer.name === want) {
          return layer;
        }
        const hit = walk(layer);
        if (hit) return hit;
      }
      return null;
    };
    return walk(doc);
  }

  function findArtLayerByNameInfo(container, name) {
    const layers = container.layers || [];
    for (let i = 0; i < layers.length; i += 1) {
      const layer = layers[i];
      if (isGroupLikeLayer(layer)) {
        const hit = findArtLayerByNameInfo(layer, name);
        if (hit) return hit;
      } else if (layer.name === name) {
        return layer;
      }
    }
    return null;
  }

  function buildTopLevelColorFallbackIndex(doc) {
    const out = {};
    const layers = flattenTopLevelLayers(doc);
    for (let i = layers.length - 2; i >= 1; i -= 1) {
      const layer = layers[i];
      if (!layer) continue;
      if (isGroupLikeLayer(layer)) continue;
      if (!layer.visible) continue;
      const inkName = logicalInkName(layer.name);
      if (!out[inkName]) {
        out[inkName] = {
          name: "TOPLEVEL__" + sanitizeInkName(inkName),
          __virtual: true,
          layers: []
        };
      }
      out[inkName].layers.push(layer);
    }
    return out;
  }

  function normalizeLayerSectionValue(value) {
    if (value == null) return "";
    if (typeof value === "string") return value;
    try {
      if (value._value) return String(value._value);
    } catch (e) {}
    return String(value);
  }

  function parseDescriptorGroups(items) {
    const groups = {};
    const stack = [];

    for (let i = 0; i < items.length; i += 1) {
      const item = items[i];
      const section = normalizeLayerSectionValue(item.layerSection);
      const name = String(item.name || "");

      if (section === "layerSectionStart") {
        const group = { name, childNames: [], __descriptor: true };
        if (stack.length) {
          stack[stack.length - 1].childNames.push(name);
        }
        stack.push(group);
        groups[name] = group;
        continue;
      }

      if (section === "layerSectionEnd") {
        if (stack.length) stack.pop();
        continue;
      }

      if (stack.length) {
        stack[stack.length - 1].childNames.push(name);
      }
    }

    return groups;
  }

  async function buildDescriptorColorGroupIndex() {
    let count = 0;
    try {
      const countResult = await action.batchPlay(
        [{
          _obj: "get",
          _target: [
            { _property: "numberOfLayers" },
            { _ref: "document", _enum: "ordinal", _value: "targetEnum" }
          ],
          _options: { dialogOptions: "dontDisplay" }
        }],
        {}
      );
      count = Number((countResult[0] && countResult[0].numberOfLayers) || 0);
    } catch (e) {
      return {};
    }

    if (!count) return {};

    const commands = [];
    for (let i = 1; i <= count; i += 1) {
      commands.push({
        _obj: "get",
        _target: [{ _ref: "layer", _index: i }],
        _options: { dialogOptions: "dontDisplay" }
      });
    }

    let descriptors = [];
    try {
      descriptors = await action.batchPlay(commands, {});
    } catch (e) {
      return {};
    }

    const forward = parseDescriptorGroups(descriptors);
    const reverse = parseDescriptorGroups(descriptors.slice().reverse());
    const forwardCount = Object.keys(forward).filter((name) => name.indexOf("COLOR__") === 0).length;
    const reverseCount = Object.keys(reverse).filter((name) => name.indexOf("COLOR__") === 0).length;

    return (reverseCount > forwardCount) ? reverse : forward;
  }

  async function getLayerDescriptorDump() {
    let count = 0;
    try {
      const countResult = await action.batchPlay(
        [{
          _obj: "get",
          _target: [
            { _property: "numberOfLayers" },
            { _ref: "document", _enum: "ordinal", _value: "targetEnum" }
          ],
          _options: { dialogOptions: "dontDisplay" }
        }],
        {}
      );
      count = Number((countResult[0] && countResult[0].numberOfLayers) || 0);
    } catch (e) {
      return [];
    }

    if (!count) return [];

    const commands = [];
    for (let i = 1; i <= count; i += 1) {
      commands.push({
        _obj: "get",
        _target: [{ _ref: "layer", _index: i }],
        _options: { dialogOptions: "dontDisplay" }
      });
    }

    try {
      const descriptors = await action.batchPlay(commands, {});
      return descriptors.map((item, idx) => ({
        index: idx + 1,
        name: String(item.name || ""),
        layerSection: normalizeLayerSectionValue(item.layerSection)
      }));
    } catch (e) {
      return [];
    }
  }

  function findSourceBaseLayerInfo(sourceGroup, sourceName) {
    if (sourceGroup && sourceGroup.__virtual) {
      for (let i = 0; i < sourceGroup.layers.length; i += 1) {
        if (sourceGroup.layers[i].name === "CLEAN__" + sourceName) {
          return sourceGroup.layers[i];
        }
      }
      for (let i = 0; i < sourceGroup.layers.length; i += 1) {
        if (sourceGroup.layers[i].name === sourceName) {
          return sourceGroup.layers[i];
        }
      }
      return null;
    }

    if (sourceGroup && sourceGroup.__descriptor) {
      const cleanName = "CLEAN__" + sourceName;
      if (sourceGroup.childNames.indexOf(cleanName) >= 0) {
        return { name: cleanName, __descriptor: true };
      }
      if (sourceGroup.childNames.indexOf(sourceName) >= 0) {
        return { name: sourceName, __descriptor: true };
      }
      return null;
    }

    const clean = findArtLayerByNameInfo(sourceGroup, "CLEAN__" + sourceName);
    if (clean) return clean;
    return findArtLayerByNameInfo(sourceGroup, sourceName);
  }

  async function exportSingleMaskPng(sourceDoc, targetIndex, fileEntry) {
    const outPath = (fileEntry && (fileEntry.nativePath || fileEntry.name)) || "(unknown)";
    appendStatus("[mask-export] begin targetIndex=" + targetIndex + " file=" + outPath + " engine=" + EXPORT_ENGINE_VERSION);
    await core.executeAsModal(async () => {
      const duplicate = await sourceDoc.duplicate();
      let previousActive = null;
      try {
        try {
          previousActive = app.activeDocument || null;
        } catch (e) {
          previousActive = null;
        }
        try {
          app.activeDocument = duplicate;
        } catch (e) {}

        const dupLayers = flattenTopLevelLayers(duplicate);
        appendStatus("[mask-export] duplicate doc created; layerCount=" + dupLayers.length);
        try {
          appendStatus("[mask-export] duplicate mode(before): " + String(duplicate.mode));
        } catch (e) {}
        for (let i = 0; i < dupLayers.length; i += 1) {
          try {
            dupLayers[i].visible = i === targetIndex;
          } catch (e) {}
        }
        appendStatus("[mask-export] isolated visibility applied at index=" + targetIndex);

        // PNG export is reliable only when the temp export doc is RGB-compatible.
        try {
          const modeText = String(duplicate.mode || "");
          if (modeText.indexOf("RGB") < 0) {
            appendStatus("[mask-export] converting duplicate mode to RGB...");
            await action.batchPlay(
              [{
                _obj: "convertMode",
                to: { _class: "RGBColorMode" },
                _options: { dialogOptions: "dontDisplay" }
              }],
              {}
            );
            appendStatus("[mask-export] convertMode to RGB returned");
          }
        } catch (modeErr) {
          appendStatus("[mask-export] convertMode warning: " + String(modeErr));
        }
        try {
          appendStatus("[mask-export] duplicate mode(after): " + String(duplicate.mode));
        } catch (e) {}

        appendStatus("[mask-export] DOM saveAs.png start");
        await duplicate.saveAs.png(
          fileEntry,
          {
            compression: 6,
            interlaced: false
          },
          true
        );
        appendStatus("[mask-export] DOM saveAs.png returned");
      } finally {
        try {
          if (previousActive) app.activeDocument = previousActive;
        } catch (e) {}
        try {
          await duplicate.closeWithoutSaving();
          appendStatus("[mask-export] duplicate closed without saving");
        } catch (e) {
          appendStatus("[mask-export] duplicate closeWithoutSaving error: " + String(e));
          try {
            if (e && e.stack) {
              appendStatus("[mask-export] duplicate close stack:\n" + String(e.stack));
            }
          } catch (e2) {}
        }
      }
    }, { commandName: "Export Smart Trapper Mask" });
    appendStatus("[mask-export] modal complete for " + outPath);
  }

  async function getFileByteLength(fileEntry) {
    try {
      const bytes = await fileEntry.read({ format: formats.binary });
      if (!bytes) return 0;
      if (typeof bytes.byteLength === "number") return bytes.byteLength;
      if (typeof bytes.length === "number") return bytes.length;
      return 0;
    } catch (e) {
      return 0;
    }
  }

  async function sleepMs(ms) {
    return new Promise((resolve) => {
      setTimeout(resolve, ms);
    });
  }

  async function waitForNonZeroFileBytes(fileEntry, attempts, waitPerAttemptMs) {
    const maxAttempts = Math.max(1, Number(attempts || 1));
    for (let i = 0; i < maxAttempts; i += 1) {
      const size = await getFileByteLength(fileEntry);
      if (size > 0) return size;
      if (i < maxAttempts - 1) {
        await sleepMs(waitPerAttemptMs || 120);
      }
    }
    return 0;
  }

  async function sampleLayerColorByTopIndex(sourceDoc, targetIndex) {
    return await core.executeAsModal(async () => {
      const duplicate = await sourceDoc.duplicate();
      try {
        const dupLayers = flattenTopLevelLayers(duplicate);
        for (let i = 0; i < dupLayers.length; i += 1) {
          try {
            dupLayers[i].visible = i === targetIndex;
          } catch (e) {}
        }

        const boundsResult = await action.batchPlay(
          [{
            _obj: "get",
            _target: [{ _ref: "layer", _index: targetIndex + 1 }],
            _options: { dialogOptions: "dontDisplay" }
          }],
          {}
        );

        const desc = (boundsResult && boundsResult[0]) || {};
        const rawBounds = desc.boundsNoEffects || desc.bounds || null;
        if (!rawBounds) {
          return null;
        }

        const left = Math.max(0, Math.round(Number(rawBounds.left?._value || rawBounds.left || 0)));
        const top = Math.max(0, Math.round(Number(rawBounds.top?._value || rawBounds.top || 0)));
        const right = Math.max(left + 1, Math.round(Number(rawBounds.right?._value || rawBounds.right || 0)));
        const bottom = Math.max(top + 1, Math.round(Number(rawBounds.bottom?._value || rawBounds.bottom || 0)));
        const sampleX = Math.max(left, Math.min(right - 1, Math.round((left + right) / 2)));
        const sampleY = Math.max(top, Math.min(bottom - 1, Math.round((top + bottom) / 2)));

        const sampleResult = await action.batchPlay(
          [{
            _obj: "colorSampler",
            samplePoint: {
              horizontal: { _unit: "pixelsUnit", _value: sampleX },
              vertical: { _unit: "pixelsUnit", _value: sampleY }
            }
          }],
          {}
        );

        const sample = (sampleResult && sampleResult[0] && sampleResult[0].sampledData) || null;
        if (!sample || !sample.rgb) {
          return null;
        }

        return {
          r: Math.round(Number(sample.rgb.red || 0)),
          g: Math.round(Number(sample.rgb.green || 0)),
          b: Math.round(Number(sample.rgb.blue || 0))
        };
      } finally {
        try {
          await duplicate.closeWithoutSaving();
        } catch (e) {
          try {
            await duplicate.close(constants.SaveOptions.DONOTSAVECHANGES);
          } catch (e2) {}
        }
      }
    }, { commandName: "Sample Smart Trapper Layer Color" });
  }

  function isArtLikeLayer(layer) {
    try {
      return !!layer && !isGroupLikeLayer(layer);
    } catch (e) {
      return true;
    }
  }

  function detectBlendLikeLayers(layers) {
    return layers.filter((layer) => {
      try {
        return layer.visible && (
          String(layer.blendMode) !== "normal" &&
          String(layer.blendMode) !== "BlendMode.NORMAL" &&
          Number(layer.opacity) !== 100 ||
          Number(layer.fillOpacity) !== 100
        );
      } catch (e) {
        return false;
      }
    });
  }

  async function refreshDocumentSummary() {
    let doc = null;
    try {
      doc = app.activeDocument;
    } catch (e) {
      doc = null;
    }

    if (!doc) {
      els.docSummary.textContent = "No active document.";
      els.layerSummary.textContent = "Open a document to inspect the current layer stack.";
      return;
    }

    const layers = flattenTopLevelLayers(doc);
    const topArtLayer = layers.find((layer) => isArtLikeLayer(layer));
    const visibleArtLayers = layers.filter((layer) => {
      try {
        return layer.visible && isArtLikeLayer(layer);
      } catch (e) {
        return false;
      }
    });
    const blendLayers = detectBlendLikeLayers(layers);

    els.docSummary.textContent =
      "Name: " + doc.title + "\n" +
      "Mode: " + doc.mode + "\n" +
      "Size: " + doc.width + " x " + doc.height + "\n" +
      "Resolution: " + doc.resolution + "\n" +
      "Top layer used as KEY: " + (topArtLayer ? topArtLayer.name : "(none)");

    els.layerSummary.textContent =
      "Top-level layers: " + layers.length + "\n" +
      "Visible art layers: " + visibleArtLayers.length + "\n" +
      "Blend-like layers: " + blendLayers.length + "\n" +
      (blendLayers.length
        ? "Blend-like names: " + blendLayers.map((layer) => layer.name).join(", ")
        : "Blend-like names: none");
  }

  async function testBridge() {
    const { bridgeUrl } = getSettings();
    setStatus("Testing bridge:\n" + bridgeUrl);
    try {
      const response = await fetch(bridgeUrl.replace(/\/$/, "") + "/health");
      const text = await response.text();
      setStatus("Bridge response:\n" + text);
    } catch (e) {
      setStatus(
        "Bridge test failed.\n\n" +
        "This is expected until a local companion bridge is running.\n\n" +
        String(e)
      );
    }
  }

  async function selectJobFolder() {
    try {
      const folder = await localFileSystem.getFolder();
      if (!folder) {
        setStatus("Job folder selection cancelled.");
        return;
      }
      currentJobFolderEntry = folder;
      els.jobFolderDisplay.textContent = folder.nativePath || folder.name || "(selected)";
      setStatus("Job folder selected.\n\n" + els.jobFolderDisplay.textContent);
    } catch (e) {
      setStatus("Job folder selection failed.\n\n" + e);
    }
  }

  function clearJobFolder() {
    currentJobFolderEntry = null;
    els.jobFolderDisplay.textContent = "(none selected)";
    setStatus("Job folder cleared.");
  }

  async function selectLogFolder() {
    try {
      const folder = await localFileSystem.getFolder();
      if (!folder) {
        setStatus("Log folder selection cancelled.");
        return;
      }
      currentLogFolderEntry = folder;
      els.logFolderDisplay.textContent = folder.nativePath || folder.name || "(selected)";
      setStatus("Log folder selected.\n\n" + els.logFolderDisplay.textContent);
    } catch (e) {
      setStatus("Log folder selection failed.\n\n" + e);
    }
  }

  function clearLogFolder() {
    currentLogFolderEntry = null;
    els.logFolderDisplay.textContent = "(none selected)";
    setStatus("Log folder cleared.");
  }

  function editBridgeUrl() {
    const current = getSettings().bridgeUrl;
    const next = window.prompt("Bridge URL", current);
    if (next === null || typeof next === "undefined") {
      setStatus("Bridge URL edit cancelled.");
      return;
    }
    els.bridgeUrlDisplay.textContent = String(next).trim() || DEFAULTS.bridgeUrl;
    setStatus("Bridge URL updated.\n\n" + els.bridgeUrlDisplay.textContent);
  }

  async function exportSettingsSnapshot() {
    const file = await localFileSystem.getFileForSaving("smart_trapper_settings.json", {
      types: ["json"]
    });
    if (!file) {
      setStatus("Settings export cancelled.");
      return;
    }

    let documentMeta = null;
    try {
      const doc = app.activeDocument;
      if (doc) {
        documentMeta = {
          title: doc.title,
          mode: doc.mode,
          width: doc.width,
          height: doc.height,
          resolution: doc.resolution
        };
      }
    } catch (e) {}

    const snapshot = {
      generatedAt: new Date().toISOString(),
      settings: getSettings(),
      document: documentMeta
    };

    await file.write(JSON.stringify(snapshot, null, 2));
    setStatus("Settings snapshot written:\n" + file.nativePath);
  }

  async function saveStatusToFile() {
    const text = statusLog || els.status.textContent || "";
    try {
      const stamp = new Date().toISOString().replace(/[:.]/g, "-");
      const fileName = "smart_trapper_status_" + stamp + ".txt";

      let file = null;
      let savedTo = "";

      if (currentLogFolderEntry) {
        file = await currentLogFolderEntry.createFile(fileName, { overwrite: true });
        savedTo = file.nativePath || ((currentLogFolderEntry.nativePath || currentLogFolderEntry.name) + "/" + fileName);
      } else if (currentJobFolderEntry) {
        const statusFolder = await ensureSubfolder(currentJobFolderEntry, "uxp_status_logs");
        file = await statusFolder.createFile(fileName, { overwrite: true });
        savedTo = file.nativePath || (statusFolder.nativePath || statusFolder.name) + "/" + fileName;
      } else {
        const dataFolder = await localFileSystem.getDataFolder();
        const statusFolder = await ensureSubfolder(dataFolder, "status_logs");
        file = await statusFolder.createFile(fileName, { overwrite: true });
        savedTo = file.nativePath || (statusFolder.nativePath || statusFolder.name) + "/" + fileName;
      }

      await file.write(text);
      appendStatus("[Status snapshot saved]\n" + savedTo);
    } catch (e) {
      appendStatus("[Save Status failed]\n" + String(e));
    }
  }

  async function buildImportPlan() {
    let doc = null;
    try {
      doc = app.activeDocument;
    } catch (e) {
      doc = null;
    }

    if (!doc) {
      appendStatus("No active document. Open the target PSD before building an import plan.");
      return;
    }

    if (!currentJobFolderEntry) {
      appendStatus("No job folder selected. Select a job folder that contains traps.json.");
      return;
    }

    let trapsObj = null;
    try {
      trapsObj = await readJsonFile(currentJobFolderEntry, "traps.json");
    } catch (e) {
      appendStatus(
        "Could not read traps.json from the selected folder.\n\n" +
        (currentJobFolderEntry.nativePath || currentJobFolderEntry.name || "(selected)") +
        "\n\n" + String(e)
      );
      return;
    }

    try {
      doc = app.activeDocument;
    } catch (e) {}

    const traps = (trapsObj && trapsObj.traps) ? trapsObj.traps : [];
    if (!traps.length) {
      appendStatus("No traps found in traps.json.");
      return;
    }

    const lines = [];
    lines.push(statusStamp("Build Import Plan"));
    lines.push("");
    const fallbackIndex = buildTopLevelColorFallbackIndex(doc);
    const descriptorGroupIndex = await buildDescriptorColorGroupIndex();
    let readyCount = 0;
    let missingGroups = 0;
    let missingBaseLayers = 0;
    let missingPngs = 0;

    lines.push("UXP import plan");
    lines.push("");
    lines.push("Job folder:");
    lines.push(currentJobFolderEntry.nativePath || currentJobFolderEntry.name || "(selected)");
    lines.push("");
    lines.push("Trap count: " + traps.length);
    lines.push("");
    lines.push("Descriptor COLOR__ groups found: " + Object.keys(descriptorGroupIndex).filter((name) => name.indexOf("COLOR__") === 0).length);
    lines.push("");

    for (let i = 0; i < traps.length; i += 1) {
      const spec = traps[i];
      const wantedGroupName = "COLOR__" + sanitizeInkName(spec.source);
      const domGroup = findColorGroupInfo(doc, spec.source);
      const descriptorGroup = descriptorGroupIndex[wantedGroupName] || null;
      const topLevelFallback = fallbackIndex[logicalInkName(spec.source)] || null;
      const sourceGroup =
        domGroup ||
        descriptorGroup ||
        topLevelFallback ||
        null;
      const sourceBase = sourceGroup ? findSourceBaseLayerInfo(sourceGroup, spec.source) : null;

      let pngExists = false;
      try {
        await currentJobFolderEntry.getEntry(spec.png);
        pngExists = true;
      } catch (e) {
        pngExists = false;
      }

      if (!sourceGroup) missingGroups += 1;
      if (!sourceBase) missingBaseLayers += 1;
      if (!pngExists) missingPngs += 1;
      if (sourceGroup && sourceBase && pngExists) readyCount += 1;

      lines.push(
        (i + 1) + ". " + spec.source + " over " + spec.target
      );
      lines.push(
        "   source group: " +
        (sourceGroup
          ? (
              sourceGroup.__virtual
                ? ("TOP-LEVEL MATCH (" + sourceGroup.name + ")")
                : sourceGroup.__descriptor
                  ? ("DESCRIPTOR MATCH (" + sourceGroup.name + ")")
                  : sourceGroup.name
            )
          : "MISSING")
      );
      lines.push("   lookup hits: DOM=" + (domGroup ? "Y" : "N") + " | DESC=" + (descriptorGroup ? "Y" : "N") + " | TOP=" + (topLevelFallback ? "Y" : "N"));
      lines.push("   source base: " + (sourceBase ? sourceBase.name : "MISSING"));
      lines.push("   trap png: " + spec.png + " -> " + (pngExists ? "OK" : "MISSING"));
    }

    lines.push("");
    lines.push("Summary");
    lines.push("Ready to import: " + readyCount + " / " + traps.length);
    lines.push("Missing COLOR__ groups: " + missingGroups);
    lines.push("Missing source base layers: " + missingBaseLayers);
    lines.push("Missing trap PNGs: " + missingPngs);
    lines.push("");
    lines.push("This is a planning pass only. No trap pixels have been imported yet.");

    appendStatus(lines.join("\n"));
  }

  async function importTraps() {
    let doc = null;
    try {
      doc = app.activeDocument;
    } catch (e) {
      doc = null;
    }

    if (!doc) {
      appendStatus("No active document. Open the target PSD before importing traps.");
      return;
    }

    if (!currentJobFolderEntry) {
      appendStatus("No job folder selected. Select a completed job folder before importing traps.");
      return;
    }

    let trapsObj = null;
    try {
      trapsObj = await readJsonFile(currentJobFolderEntry, "traps.json");
    } catch (e) {
      appendStatus("Could not read traps.json from the selected folder.\n\n" + String(e));
      return;
    }

    appendStatus(statusStamp("Import Traps"));
    const traps = (trapsObj && trapsObj.traps) ? trapsObj.traps : [];
    const maskColors = await readOptionalJsonFile(currentJobFolderEntry, "mask_colors.json") || {};
    appendStatus(
      "Mask color metadata source: " +
      (Object.keys(maskColors).length
        ? ("mask_colors.json (" + Object.keys(maskColors).length + " colors)")
        : "MISSING")
    );
    if (!Object.keys(maskColors).length) {
      appendStatus(
        "Import aborted.\n" +
        "mask_colors.json is missing for the currently selected job folder.\n" +
        "Run Trapper first and import from that exact run folder."
      );
      return;
    }
    if (!traps.length) {
      appendStatus("No traps found in traps.json.");
      return;
    }

    appendStatus("Beginning trap import...\nTrap count: " + traps.length);

    let placedCount = 0;
    let movedCount = 0;
    let failedCount = 0;

    for (let i = 0; i < traps.length; i += 1) {
      const spec = traps[i];
      const trapLayerName = "TRAP__" + spec.source + "_over_" + spec.target;
      try {
        const pngEntry = await getEntryByRelativePath(currentJobFolderEntry, spec.png);
        const group = findColorGroupInfo(doc, spec.source);
        if (!group) {
          throw new Error("Missing destination group COLOR__" + sanitizeInkName(spec.source));
        }
        const sourceBase = findSourceBaseLayerInfo(group, spec.source);
        const groupId = layerIdOf(group);
        if (!groupId) {
          throw new Error("Missing destination group ID for " + group.name);
        }

        appendStatus("Importing " + trapLayerName + "\n  png: " + spec.png + "\n  group: " + group.name);
        const selectResult = await selectLayerById(groupId, "Select Destination Group");
        appendStatus("  select group result:\n" + summarizeBatchPlayResult(selectResult));
        if (batchPlayResultHasError(selectResult)) {
          throw new Error("group select reported error\n" + summarizeBatchPlayResult(selectResult));
        }

        const placeResult = await placeTrapPngIntoDocument(pngEntry);
        appendStatus("  place result:\n" + summarizeBatchPlayResult(placeResult));
        if (batchPlayResultHasError(placeResult)) {
          throw new Error("placeEvent reported error\n" + summarizeBatchPlayResult(placeResult));
        }
        placedCount += 1;

        const renameResult = await renameTargetLayer(trapLayerName + "__PLACED_TMP");
        appendStatus("  rename result:\n" + summarizeBatchPlayResult(renameResult));
        if (batchPlayResultHasError(renameResult)) {
          throw new Error("rename reported error\n" + summarizeBatchPlayResult(renameResult));
        }
        if (cleanPlacementOffset && (Math.abs(cleanPlacementOffset.dx) > 0.5 || Math.abs(cleanPlacementOffset.dy) > 0.5)) {
          const trapMove = await translateTargetLayerPixels(
            cleanPlacementOffset.dx,
            cleanPlacementOffset.dy,
            "Apply Global CLEAN Offset To Trap Placement"
          );
          appendStatus(
            "  trap placement offset: (" +
            cleanPlacementOffset.dx.toFixed(2) + "," +
            cleanPlacementOffset.dy.toFixed(2) + ")\n" +
            summarizeBatchPlayResult(trapMove)
          );
        } else {
          appendStatus("  trap placement offset: none");
        }

        let originalPlacedId = 0;
        try {
          const activeLayers = app.activeDocument.activeLayers || [];
          if (activeLayers.length) {
            originalPlacedId = Number(layerIdOf(activeLayers[0]) || 0);
          }
        } catch (e) {}

        const sourceColor = maskColors[spec.source] || null;
        let selectionFillDone = false;
        if (sourceColor && sourceBase) {
          try {
            const selectTransparency = await loadSelectionFromTargetTransparency();
            appendStatus("  transparency selection result:\n" + summarizeBatchPlayResult(selectTransparency));
            if (batchPlayResultHasError(selectTransparency)) {
              throw new Error("transparency selection reported error\n" + summarizeBatchPlayResult(selectTransparency));
            }

            if (!sourceBaseId) {
              throw new Error("Missing source base layer ID for " + sourceBase.name);
            }

            const selectBase = await selectLayerById(sourceBaseId, "Select Source Base For Trap Fill");
            appendStatus("  select source base result:\n" + summarizeBatchPlayResult(selectBase));
            if (batchPlayResultHasError(selectBase)) {
              throw new Error("source base select reported error\n" + summarizeBatchPlayResult(selectBase));
            }

            const makeTrapLayer = await createLayerAboveCurrent(trapLayerName);
            appendStatus("  create trap pixel layer result:\n" + summarizeBatchPlayResult(makeTrapLayer));
            if (batchPlayResultHasError(makeTrapLayer)) {
              throw new Error("trap layer creation reported error\n" + summarizeBatchPlayResult(makeTrapLayer));
            }

            const fillResult = await fillSelectionWithRgb(sourceColor);
            appendStatus(
              "  fill selection result:\n" +
              summarizeBatchPlayResult(fillResult) +
              "\n  source color: RGB(" + sourceColor.r + "," + sourceColor.g + "," + sourceColor.b + ")"
            );
            if (batchPlayResultHasError(fillResult)) {
              throw new Error("fill reported error\n" + summarizeBatchPlayResult(fillResult));
            }

            const deselectResult = await deselectSelection();
            appendStatus("  deselect result:\n" + summarizeBatchPlayResult(deselectResult));

            if (originalPlacedId) {
              const deleteOriginal = await deleteLayerById(originalPlacedId, "Delete Original Placed Trap Layer");
              appendStatus("  delete original result:\n" + summarizeBatchPlayResult(deleteOriginal));
              if (batchPlayResultHasError(deleteOriginal)) {
                appendStatus("  delete warning: original placed trap layer may remain at top level");
              }
            }

            movedCount += 1;
            selectionFillDone = true;
            appendStatus("Imported OK: " + trapLayerName + " -> " + group.name + "\n  created as filled pixel layer");
          } catch (selectionFillErr) {
            appendStatus("  selection-fill fallback triggered:\n" + String(selectionFillErr));
            try {
              await deselectSelection();
            } catch (e) {}
          }
        } else {
          appendStatus("  selection-fill skipped: missing source color metadata or source base for " + spec.source);
        }

        if (!selectionFillDone) {
          try {
            if (sourceColor) {
              const colorResult = await applyColorOverlayToTargetLayer(sourceColor);
              appendStatus(
                "  color overlay result:\n" +
                summarizeBatchPlayResult(colorResult) +
                "\n  source color: RGB(" + sourceColor.r + "," + sourceColor.g + "," + sourceColor.b + ")"
              );
              if (batchPlayResultHasError(colorResult)) {
                appendStatus("  color overlay warning: Photoshop reported an error applying color overlay");
              }
            } else {
              appendStatus("  color overlay skipped: no source color metadata for " + spec.source);
            }

            const dupInfo = await duplicateTargetLayerIntoGroup(group);
            appendStatus(
              "  duplicate-to-group result:\n" +
              summarizeBatchPlayResult(dupInfo.result) +
              "\n  duplicate layer id: " + (dupInfo.duplicatedLayerId || "(missing)") +
              "\n  duplicate layer name: " + (dupInfo.duplicatedLayerName || "(missing)")
            );
            if (!batchPlayResultHasError(dupInfo.result)) {
              if (dupInfo.duplicatedLayerId && originalPlacedId && dupInfo.duplicatedLayerId !== originalPlacedId) {
                const deleteOriginal = await deleteLayerById(originalPlacedId, "Delete Original Placed Trap Layer");
                appendStatus("  delete original result:\n" + summarizeBatchPlayResult(deleteOriginal));
                if (batchPlayResultHasError(deleteOriginal)) {
                  appendStatus("  delete warning: original placed trap layer may remain at top level");
                }
              } else if (originalPlacedId) {
                appendStatus("  delete warning: duplicate layer was not resolved as a distinct layer; original left in place");
              } else {
                appendStatus("  delete warning: could not resolve original placed layer ID");
              }

              if (dupInfo.duplicatedLayerId && originalPlacedId && dupInfo.duplicatedLayerId !== originalPlacedId) {
                movedCount += 1;
                appendStatus("Imported OK: " + trapLayerName + " -> " + group.name + "\n  duplicated into destination group");
              } else {
                appendStatus("Imported with grouping warning: " + trapLayerName + "\n  duplicate did not produce a distinct grouped layer");
              }
            } else {
              appendStatus("Imported with grouping warning: " + trapLayerName + "\n  duplicate into destination group failed");
            }
          } catch (groupErr) {
            appendStatus("Imported with grouping warning: " + trapLayerName + "\n  " + String(groupErr));
          }
        }
      } catch (e) {
        failedCount += 1;
        appendStatus("Import failed: " + trapLayerName + "\n  " + String(e));
      }
    }

    appendStatus(
      "Trap import complete.\n" +
      "Placed: " + placedCount + "\n" +
      "Moved into destination groups: " + movedCount + "\n" +
      "Failed: " + failedCount
    );

    try {
      const cleanHide = await hideOriginalLayersWhenCleanExists(doc);
      appendStatus(
        "Post-import visibility cleanup:\n" +
        "COLOR__ groups checked: " + cleanHide.checkedGroups + "\n" +
        "Original layers hidden: " + cleanHide.hidden + "\n" +
        "Hide failures: " + cleanHide.failed +
        (cleanHide.details && cleanHide.details.length ? ("\n" + cleanHide.details.join("\n")) : "")
      );
    } catch (e) {
      appendStatus("Post-import visibility cleanup warning:\n" + String(e));
    }
  }

  async function prepareImportStructure() {
    let doc = null;
    try {
      doc = app.activeDocument;
    } catch (e) {
      doc = null;
    }

    if (!doc) {
      appendStatus("No active document. Open the target PSD before preparing import structure.");
      return;
    }

    const layers = flattenTopLevelLayers(doc);
    if (layers.length < 3) {
      appendStatus("PSD needs at least 3 top-level layers (KEY top, PAPER bottom, colors in between).");
      return;
    }

    const lines = [];
    let wrapped = 0;
    let skipped = 0;

    lines.push(statusStamp("Prepare Import Structure"));
    lines.push("");
    lines.push("Preparing import structure...");
    try {
      const settings = getSettings();
      lines.push(
        "Settings: preflightCleanup=" + (!!settings.preflightCleanup) +
        ", alphaThreshold=" + settings.alphaThreshold +
        ", edgeBiasPx=" + settings.edgeBiasPx +
        ", trapPx=" + settings.trapPx +
        ", mode=" + settings.mode
      );
    } catch (e) {
      lines.push("Settings: (unavailable) " + String(e));
    }
    try {
      lines.push(
        "Document: " + doc.title +
        " | mode=" + String(doc.mode) +
        " | res=" + Number(doc.resolution || 0).toFixed(4) +
        " | size=" + Number((doc.width && doc.width.value) || doc.width || 0) +
        "x" + Number((doc.height && doc.height.value) || doc.height || 0)
      );
    } catch (e) {
      lines.push("Document summary unavailable: " + String(e));
    }
    lines.push("Top-level layer inspection:");
    setStatus(lines.join("\n"));

    for (let i = layers.length - 2; i >= 1; i -= 1) {
      const layer = layers[i];
      if (!layer) continue;
      const meta = topLevelLayerMeta(layer, i);
      lines.push(
        "Inspect [" + i + "]: " + meta.name +
        " | kind=" + meta.kind +
        " | visible=" + meta.visible
      );
      if (!isArtLikeLayer(layer)) {
        skipped += 1;
        lines.push("  skip reason: not art-like");
        continue;
      }
      if (!layer.visible) {
        skipped += 1;
        lines.push("  skip reason: hidden");
        continue;
      }

      const inkName = logicalInkName(layer.name);
      const existing = findColorGroupInfo(doc, inkName);
      if (existing) {
        lines.push("Existing group: " + existing.name);
        continue;
      }

      const groupName = "COLOR__" + sanitizeInkName(inkName);
      try {
        lines.push("Wrapping: " + layer.name + " -> " + groupName);
        appendStatus(lines.join("\n"));
        await wrapLayerInGroupUxp(layer, groupName);
        wrapped += 1;
      } catch (e) {
        lines.push("Wrap failed: " + layer.name + " :: " + String(e));
      }
    }

    try {
      doc = app.activeDocument;
    } catch (e) {}
    await refreshDocumentSummary();

    const settings = getSettings();
    cleanPlacementOffset = null;
    lines.push("");
    lines.push("CLEAN sync:");
    if (!settings.preflightCleanup) {
      lines.push("  skipped: Preflight cleanup is off");
    } else if (!currentJobFolderEntry) {
      lines.push("  skipped: no selected job folder");
    } else {
      const maskColors = await readOptionalJsonFile(currentJobFolderEntry, "mask_colors.json") || {};
      let cleanBuilt = 0;
      let cleanSkipped = 0;
      let cleanGlobalOffset = null;
      let cleanMasksReady = true;
      try {
        await currentJobFolderEntry.getEntry("clean_masks");
      } catch (e) {
        cleanMasksReady = false;
      }

      if (!cleanMasksReady) {
        lines.push("  skipped: clean_masks folder not found in selected job folder");
        lines.push("  hint: run 'Run Trapper' first, then 'Prepare Import Structure'");
      } else {
        const freshLayers = flattenTopLevelLayers(doc);
        for (let i = freshLayers.length - 2; i >= 1; i -= 1) {
          const maybeGroup = freshLayers[i];
          if (!maybeGroup || !isGroupLikeLayer(maybeGroup)) continue;
          if (String(maybeGroup.name || "").indexOf("COLOR__") !== 0) continue;

          let sourceName = String(maybeGroup.name || "").substring(7);
          const origInGroup = findArtLayerByNameInfo(maybeGroup, sourceName);
          if (origInGroup && !origInGroup.__descriptor) {
            sourceName = logicalInkName(origInGroup.name);
          }

          try {
            const cleanResult = await buildCleanLayerInGroup(
              maybeGroup,
              sourceName,
              maskColors,
              { forcedOffset: cleanGlobalOffset }
            );
            if (cleanResult && cleanResult.ok) {
              const ratioDelta = Number(
                cleanResult && cleanResult.ratioDelta != null ? cleanResult.ratioDelta : 999
              );
              if (!cleanGlobalOffset && cleanResult.observedOffset && ratioDelta <= 0.02) {
                cleanGlobalOffset = {
                  dx: Number(cleanResult.observedOffset.dx || 0),
                  dy: Number(cleanResult.observedOffset.dy || 0)
                };
                lines.push(
                  "    captured clean global offset: (" +
                  cleanGlobalOffset.dx.toFixed(2) + "," +
                  cleanGlobalOffset.dy.toFixed(2) + ")"
                );
              }
              cleanBuilt += 1;
              lines.push(
                "  CLEAN " + sourceName + " -> " + cleanResult.cleanName +
                " RGB(" + cleanResult.color.r + "," + cleanResult.color.g + "," + cleanResult.color.b + ")"
              );
              if (cleanResult.placementDebug) {
                lines.push("    debug: " + cleanResult.placementDebug);
              }
            } else {
              cleanSkipped += 1;
              lines.push("  CLEAN skip " + sourceName + ": " + ((cleanResult && cleanResult.message) || "unknown"));
            }
          } catch (e) {
            cleanSkipped += 1;
            lines.push("  CLEAN error " + sourceName + ": " + String(e));
          }
        }
      }
      lines.push("  CLEAN built: " + cleanBuilt);
      lines.push("  CLEAN skipped: " + cleanSkipped);
      if (cleanGlobalOffset) {
        cleanPlacementOffset = {
          dx: Number(cleanGlobalOffset.dx || 0),
          dy: Number(cleanGlobalOffset.dy || 0)
        };
        lines.push(
          "  CLEAN global placement offset for trap import: (" +
          cleanPlacementOffset.dx.toFixed(2) + "," +
          cleanPlacementOffset.dy.toFixed(2) + ")"
        );
      } else {
        cleanPlacementOffset = null;
        lines.push("  CLEAN global placement offset for trap import: (none captured)");
      }
    }

    const descriptorDump = await getLayerDescriptorDump();
    lines.push("");
    lines.push("Prepare import structure complete.");
    lines.push("Wrapped into COLOR__ groups: " + wrapped);
    lines.push("Skipped layers: " + skipped);
    lines.push("");
    lines.push("Post-wrap descriptor dump:");
    for (let i = 0; i < descriptorDump.length; i += 1) {
      const item = descriptorDump[i];
      lines.push("  [" + item.index + "] " + item.name + " | layerSection=" + item.layerSection);
    }
    appendStatus(lines.join("\n"));
  }

  async function createJobFolderSkeleton() {
    let doc = null;
    try {
      doc = app.activeDocument;
    } catch (e) {
      doc = null;
    }

    if (!doc) {
      setStatus("No active document. Open a document before creating a job folder skeleton.");
      return;
    }

    let parentFolder = null;
    try {
      parentFolder = await localFileSystem.getFolder();
    } catch (e) {
      setStatus("Job skeleton folder selection failed.\n\n" + e);
      return;
    }

    if (!parentFolder) {
      setStatus("Job skeleton creation cancelled.");
      return;
    }

    try {
      const jobFolder = await createTimestampedJobFolderUnder(parentFolder, doc);

      const spec = buildCurrentJobSpec(doc);

      const payload = {
        generatedAt: new Date().toISOString(),
        source: "UXP_Trapper",
        document: {
          title: doc.title,
          mode: doc.mode,
          width: doc.width,
          height: doc.height,
          resolution: doc.resolution
        },
        settings: getSettings(),
        inferred: spec.inferred,
        topLevelLayers: spec.topLevelLayers
      };

      await writeJsonFile(jobFolder, "uxp_job_request.json", payload);
      await writeJsonFile(jobFolder, "job.json", spec.job);
      await writeTextFile(
        jobFolder,
        "README_uxp_job.txt",
        [
          "Smart Trapper UXP Job Skeleton",
          "",
          "This folder was created by the UXP panel.",
          "It is not a full export yet.",
          "",
          "Created folders:",
          "- masks",
          "- traps",
          "",
          "Created files:",
          "- job.json",
          "- uxp_job_request.json",
          "",
          "Next step:",
          "Port Photoshop export logic so this folder is populated with real masks/job.json for the Rust engine."
        ].join("\n")
      );

      setStatus(
        "Job folder skeleton created.\n\n" +
        "Folder:\n" + (jobFolder.nativePath || jobFolder.name || "(selected)") + "\n\n" +
        "Files:\n" +
        "- job.json\n" +
        "- uxp_job_request.json\n" +
        "- README_uxp_job.txt\n\n" +
        "Subfolders:\n" +
        "- masks\n" +
        "- traps"
      );
    } catch (e) {
      setStatus("Job folder skeleton creation failed.\n\n" + e);
    }
  }

  async function exportMasksToJobFolder() {
    let doc = null;
    try {
      doc = app.activeDocument;
    } catch (e) {
      doc = null;
    }

    if (!doc) {
      setStatus("No active document. Open a document before exporting masks.");
      return;
    }

    let runFolder = null;
    try {
      runFolder = await ensureRunJobFolder(doc);
    } catch (e) {
      setStatus(String(e));
      return;
    }

    const spec = buildCurrentJobSpec(doc);
    let masksFolder = null;
    try {
      masksFolder = await ensureSubfolder(runFolder, "masks");
      await ensureSubfolder(runFolder, "traps");
    } catch (e) {
      setStatus("Could not prepare masks/traps folders.\n\n" + e);
      return;
    }

    const exportTargets = [];

    if (spec.topLevelLayers.length) {
      exportTargets.push({
        index: 0,
        fileName: "KEY_" + sanitize(spec.topLevelLayers[0].name) + ".png",
        label: "KEY",
        layerName: spec.topLevelLayers[0].name
      });
    }

    const colorNames = spec.inferred.visibleColorLayersBottomToTop || [];
    for (let i = 0; i < colorNames.length; i += 1) {
      const layerName = colorNames[i];
      const topIndex = spec.topLevelLayers.findIndex((layer) => layer.name === layerName);
      if (topIndex < 0) continue;
      exportTargets.push({
        index: topIndex,
        fileName: (i + 1) + "_" + sanitize(layerName) + ".png",
        label: String(i + 1),
        layerName
      });
    }

    const statusLines = [];
    statusLines.push("Exporting masks to:");
    statusLines.push(runFolder.nativePath || runFolder.name || "(selected)");
    statusLines.push("");
    setStatus(statusLines.join("\n"));

    try {
      for (const target of exportTargets) {
        const outFile = await masksFolder.createFile(target.fileName, { overwrite: true });
        appendStatus("Exporting " + target.label + ": " + target.layerName);
        await exportSingleMaskPng(doc, target.index, outFile);
        const byteLen = await waitForNonZeroFileBytes(outFile, 12, 160);
        if (byteLen <= 0) {
          throw new Error(
            "Mask export wrote 0 bytes.\n" +
            "Layer: " + target.layerName + "\n" +
            "File: " + target.fileName + "\n" +
            "Masks folder: " + (masksFolder.nativePath || masksFolder.name || "(selected)")
          );
        }
        appendStatus("  bytes: " + byteLen);
      }

      const requestPayload = {
        generatedAt: new Date().toISOString(),
        source: "UXP_Trapper",
        document: {
          title: doc.title,
          mode: doc.mode,
          width: doc.width,
          height: doc.height,
          resolution: doc.resolution
        },
        settings: getSettings(),
        inferred: spec.inferred,
        topLevelLayers: spec.topLevelLayers,
        note: "Initial UXP export phase: isolated layer PNGs are written directly to masks/. Cleanup and key-cut parity are not yet ported."
      };

      await writeJsonFile(runFolder, "job.json", spec.job);
      await writeJsonFile(runFolder, "uxp_job_request.json", requestPayload);

      appendStatus("Export complete.\nMasks written: " + exportTargets.length + "\njob.json refreshed.");
    } catch (e) {
      appendStatus("Export failed:\n" + String(e));
    }
  }

  async function exportMasksToJobFolderForRun() {
    const runStartMs = nowMs();
    let doc = null;
    try {
      doc = app.activeDocument;
    } catch (e) {
      doc = null;
    }

    if (!doc) {
      throw new Error("No active document. Open a document before running the trapper.");
    }

    const runFolder = await ensureRunJobFolder(doc);
    const spec = buildCurrentJobSpec(doc);
    const masksFolder = await ensureSubfolder(runFolder, "masks");
    await ensureSubfolder(runFolder, "traps");

    const exportTargets = [];
    const maskColors = {};

    if (spec.topLevelLayers.length) {
      exportTargets.push({
        index: 0,
        fileName: "KEY_" + sanitize(spec.topLevelLayers[0].name) + ".png",
        label: "KEY",
        layerName: spec.topLevelLayers[0].name
      });
    }

    const colorNames = spec.inferred.visibleColorLayersBottomToTop || [];
    for (let i = 0; i < colorNames.length; i += 1) {
      const layerName = colorNames[i];
      const topIndex = spec.topLevelLayers.findIndex((layer) => layer.name === layerName);
      if (topIndex < 0) continue;
      exportTargets.push({
        index: topIndex,
        fileName: (i + 1) + "_" + sanitize(layerName) + ".png",
        label: String(i + 1),
        layerName
      });
    }

    const statusLines = [];
      statusLines.push("Exporting masks to:");
      statusLines.push(runFolder.nativePath || runFolder.name || "(selected)");
      statusLines.push("");
      statusLines.push("Export run start: " + new Date(runStartMs).toISOString());
      statusLines.push("Export engine: " + EXPORT_ENGINE_VERSION);
      setStatus(statusLines.join("\n"));

    for (const target of exportTargets) {
      const maskStartMs = nowMs();
      const outFile = await masksFolder.createFile(target.fileName, { overwrite: true });
      appendStatus("Exporting " + target.label + ": " + target.layerName);
      await exportSingleMaskPng(doc, target.index, outFile);
      const byteLen = await waitForNonZeroFileBytes(outFile, 12, 160);
      if (byteLen <= 0) {
        throw new Error(
          "Mask export wrote 0 bytes.\n" +
          "Layer: " + target.layerName + "\n" +
          "File: " + target.fileName + "\n" +
          "Masks folder: " + (masksFolder.nativePath || masksFolder.name || "(selected)")
        );
      }
      appendStatus("  bytes: " + byteLen);
      if (target.label !== "KEY") {
        try {
          const sampled = await sampleLayerColorByTopIndex(doc, target.index);
          if (sampled) {
            maskColors[target.layerName] = sampled;
            appendStatus("  sampled RGB: (" + sampled.r + "," + sampled.g + "," + sampled.b + ")");
          } else {
            appendStatus("  sampled RGB: (missing)");
          }
        } catch (e) {
          appendStatus("  sampled RGB failed: " + String(e));
        }
      }
      appendStatus("  export time ms: " + elapsedMs(maskStartMs));
    }

    let maskEntries = [];
    try {
      maskEntries = await masksFolder.getEntries();
    } catch (e) {
      throw new Error("Could not list masks folder after export: " + String(e));
    }
    const maskNames = maskEntries
      .filter((e) => !e.isFolder)
      .map((e) => e.name);
    appendStatus("Exported mask files on disk: " + maskNames.length + "\n" + (maskNames.join("\n") || "(none)"));

    const missingExpected = exportTargets
      .map((t) => t.fileName)
      .filter((name) => maskNames.indexOf(name) < 0);
    if (missingExpected.length) {
      throw new Error(
        "Mask export verification failed.\n" +
        "Missing files:\n" + missingExpected.join("\n") + "\n\n" +
        "Masks folder:\n" + (runFolder.nativePath || runFolder.name || "(selected)")
      );
    }

    const requestPayload = {
      generatedAt: new Date().toISOString(),
      source: "UXP_Trapper",
      document: {
        title: doc.title,
        mode: doc.mode,
        width: doc.width,
        height: doc.height,
        resolution: doc.resolution
      },
      settings: getSettings(),
      inferred: spec.inferred,
      topLevelLayers: spec.topLevelLayers,
      note: "Initial UXP export phase: isolated layer PNGs are written directly to masks/. Cleanup and key-cut parity are not yet ported."
    };

    await writeJsonFile(runFolder, "job.json", spec.job);
    await writeJsonFile(runFolder, "uxp_job_request.json", requestPayload);
    if (Object.keys(maskColors).length) {
      await writeJsonFile(runFolder, "mask_colors.json", maskColors);
    }

    appendStatus(
      "Export complete.\n" +
      "Masks written: " + exportTargets.length + "\n" +
      "job.json refreshed.\n" +
      (
        Object.keys(maskColors).length
          ? ("mask_colors.json written (" + Object.keys(maskColors).length + " colors).\n")
          : "mask_colors.json not written; bridge fallback sampling will be used.\n"
      ) +
      "Export total ms: " + elapsedMs(runStartMs)
    );

    return {
      jobFolder: runFolder.nativePath || runFolder.name || "",
      document: requestPayload.document,
      inferred: requestPayload.inferred,
      topLevelLayers: requestPayload.topLevelLayers,
      settings: requestPayload.settings,
      exportedMasks: exportTargets.length
    };
  }

  async function runTrapper() {
    try {
      const runStartMs = nowMs();
      appendStatus(statusStamp("Run Trapper"));
      appendStatus("Run start: " + new Date(runStartMs).toISOString());
      appendStatus("Export engine: " + EXPORT_ENGINE_VERSION);
      const bridgeBase = getSettings().bridgeUrl.replace(/\/$/, "");
      try {
        const healthStart = nowMs();
        const healthResp = await fetch(bridgeBase + "/health");
        const healthText = await healthResp.text();
        appendStatus("Bridge health preflight ms = " + elapsedMs(healthStart));
        appendStatus("Bridge health response:\n" + healthText);
      } catch (healthErr) {
        appendStatus("Bridge health preflight failed:\n" + String(healthErr));
      }
      const exportPhaseStartMs = nowMs();
      const exported = await exportMasksToJobFolderForRun();
      appendStatus("Run phase timing: export+job-write ms = " + elapsedMs(exportPhaseStartMs));
      const payload = {
        generatedAt: new Date().toISOString(),
        settings: getSettings(),
        document: exported.document,
        inferred: exported.inferred,
        topLevelLayers: exported.topLevelLayers,
        jobFolder: exported.jobFolder,
        exportedMasks: exported.exportedMasks
      };

      appendStatus(
        "Sending run request...\n" +
        JSON.stringify(payload, null, 2)
      );

      const bridgePhaseStartMs = nowMs();
      const response = await fetch(payload.settings.bridgeUrl.replace(/\/$/, "") + "/run", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
      });
      const text = await response.text();
      appendStatus("Run phase timing: bridge roundtrip ms = " + elapsedMs(bridgePhaseStartMs));
      appendStatus("Bridge HTTP status: " + response.status + " " + response.statusText);
      appendStatus("Bridge run response:\n" + text);

      let parsed = null;
      try {
        parsed = JSON.parse(text);
      } catch (e) {
        parsed = null;
      }

      const resolvedJobFolder = String(
        (parsed && parsed.jobFolder) ||
        exported.jobFolder ||
        payload.jobFolder ||
        ""
      );

      if (resolvedJobFolder) {
        try {
          const rebound = await localFileSystem.getEntryWithUrl(
            "file:" + resolvedJobFolder.replace(/\\/g, "/")
          );
          if (rebound) {
            currentJobFolderEntry = rebound;
            els.jobFolderDisplay.textContent = resolvedJobFolder;
          }
        } catch (e) {}
      }

      appendStatus("Run job folder:\n" + resolvedJobFolder);

      let maskColorsExists = false;
      let maskColorsPath = "";
      try {
        const maskColorsEntry = await getEntryByRelativePath(currentJobFolderEntry, "mask_colors.json");
        maskColorsExists = !!maskColorsEntry;
        maskColorsPath = maskColorsEntry.nativePath || "mask_colors.json";
      } catch (e) {
        maskColorsExists = false;
      }

      appendStatus(
        "Post-run color metadata:\n" +
        "mask_colors.json exists: " + (maskColorsExists ? "YES" : "NO") +
        (maskColorsPath ? ("\npath: " + maskColorsPath) : "")
      );
      appendStatus("Run total ms: " + elapsedMs(runStartMs));
    } catch (e) {
      appendStatus("Run Trapper failed.\n" + String(e));
      try {
        if (e && e.stack) appendStatus("Run Trapper stack:\n" + String(e.stack));
      } catch (e2) {}
    }
  }

  function wireEvents() {
    els.refreshDocBtn.addEventListener("click", refreshDocumentSummary);
    els.saveSettingsBtn.addEventListener("click", saveSettings);
    els.editBridgeBtn.addEventListener("click", editBridgeUrl);
    els.selectJobFolderBtn.addEventListener("click", selectJobFolder);
    els.clearJobFolderBtn.addEventListener("click", clearJobFolder);
    els.selectLogFolderBtn.addEventListener("click", selectLogFolder);
    els.clearLogFolderBtn.addEventListener("click", clearLogFolder);
    els.testBridgeBtn.addEventListener("click", testBridge);
    els.exportConfigBtn.addEventListener("click", exportSettingsSnapshot);
    bindActionWithCompletionAlert(els.createJobBtn, "Create Job Folder Skeleton", createJobFolderSkeleton);
    bindActionWithCompletionAlert(els.exportMasksBtn, "Export Masks To Job Folder", exportMasksToJobFolder);
    bindActionWithCompletionAlert(els.prepareImportBtn, "Prepare Import Structure", prepareImportStructure);
    bindActionWithCompletionAlert(els.importPlanBtn, "Build Import Plan", buildImportPlan);
    bindActionWithCompletionAlert(els.importTrapsBtn, "Import Traps", importTraps);
    els.saveStatusBtn.addEventListener("click", saveStatusToFile);
    bindActionWithCompletionAlert(els.runBtn, "Run Trapper", runTrapper);
  }

  async function init() {
    bindEls();
    loadSettings();
    await rebindFolderEntriesFromSettings();
    wireEvents();
    await refreshDocumentSummary();
    setStatus("Ready.\n\nThis panel is the UXP foundation for the trapper rewrite.");
  }

  return { init };
}

entrypoints.setup({
  plugin: {
    create() {},
    destroy() {}
  },
  panels: {
    "smart-trapper-panel": {
      async create(rootNode) {
        rootNode.innerHTML = panelMarkup();
        const controller = createController(rootNode);
        await controller.init();
      },
      show() {},
      hide() {},
      destroy() {}
    }
  }
});
