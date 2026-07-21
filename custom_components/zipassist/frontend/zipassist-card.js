/**
 * ZipAssist HydroTap Lovelace card.
 *
 * Loaded via the integration's static path + add_extra_js_url.
 * Uses shadow DOM, ha-card, and native custom elements (no external CDN).
 *
 * Styled to match the official ZipAssist HydroTap management page:
 * full-width red section bars, SHOW/HIDE collapse, Zip-style YES/NO toggles,
 * nested On/Off Timers tabs, and Internal/External filter sub-groups.
 */
(function () {
  "use strict";

  var CARD_TYPE = "zipassist-card";
  var CARD_NAME = "ZipAssist HydroTap";
  var CARD_DESCRIPTION =
    "ZipAssist CMMS HydroTap monitoring and control card";
  var DOC_URL =
    "https://github.com/Squazel/homeassistant-zipassist/blob/main/docs/dashboards.md";

  // ── Zip brand tokens ────────────────────────────────────────────────
  var ZIP_RED = "#E61837";
  var ZIP_GREEN = "#28B62C";

  // ── Section definitions (official site order) ───────────────────────
  // type: "info" = device info block (non-collapsible, no red bar)
  // type: "settings" = red-bar collapsible panel
  // type: "timers" = special nested-tabs panel
  // type: "filters" = internal/external sub-group panel

  var SECTIONS = [
    // 1. Device info (non-collapsible header block)
    {
      t: "Device Info",
      type: "info",
      e: [
        ["status", "Status"],
        ["serial_number", "Serial Number"],
        ["firmware_version", "Firmware"],
        ["last_sync", "Last Sync"],
        ["wifi_signal_strength", "WiFi Signal"],
        ["sleep_mode_status", "Sleep Mode Status"],
        ["filter_litres_remaining", "Filter (Litres)"],
        ["filter_days_remaining", "Filter (Days)"],
        ["filter_estimated_days", "Est. Filter Days"],
        ["average_daily_usage", "Avg Daily Usage"],
        ["peak_hourly_usage", "Peak Hourly Usage"],
        ["energy_total", "Energy Total"],
        ["energy_since_last_log", "Energy Since Last Log"],
      ],
    },
    // 2. Safety Settings
    {
      t: "SAFETY SETTINGS",
      type: "settings",
      e: [
        ["safety_lock", "Safety Lock Enabled"],
        ["hot_isolation", "Hot Isolation Enabled"],
      ],
    },
    // 3. Sync Time
    {
      t: "SYNC TIME",
      type: "settings",
      e: [["sync_period", "Sync Period"]],
    },
    // 4. System Fault Alerts
    {
      t: "SYSTEM FAULT ALERTS",
      type: "settings",
      e: [
        ["system_fault", "System Fault"],
        ["system_fault_details", "Fault Details"],
      ],
    },
    // 5. Filters (sub-grouped)
    {
      t: "FILTERS",
      type: "filters",
      e: [
        ["filter_litres_remaining", "Litres Remaining"],
        ["filter_days_remaining", "Days Remaining"],
        ["filter_estimated_days", "Est. Days"],
        ["internal_filter_litres", "Internal Litres Limit"],
        ["internal_filter_days", "Internal Days Limit"],
        ["external_filter_litres", "External Litres Limit"],
        ["external_filter_days", "External Days Limit"],
      ],
    },
    // 6. Dispense Settings
    {
      t: "DISPENSE SETTINGS",
      type: "settings",
      e: [
        ["boiling_duration", "Boiling Duration"],
        ["chilled_duration", "Chilled Duration"],
        ["sparkling_duration", "Sparkling Duration"],
        ["ambient_duration", "Ambient Duration"],
      ],
    },
    // 7. Temperature Settings
    {
      t: "TEMPERATURE SETTINGS",
      type: "settings",
      e: [
        ["boiling_temp", "Boiling Temperature"],
        ["chilled_temp", "Chilled Temperature"],
      ],
    },
    // 8. On/Off Timers (nested tabs)
    {
      t: "ON/OFF TIMERS",
      type: "timers",
      e: [], // handled specially
    },
    // 9. Sleep Mode
    {
      t: "SLEEP MODE",
      type: "settings",
      e: [["sleep_mode", "Sleep Mode"]],
    },
  ];

  // ── Timer mode definitions ──────────────────────────────────────────
  var TIMER_MODES = [
    {
      label: "Everyday",
      modeValue: "Everyday",
      groups: [
        {
          label: "Everyday",
          rows: [
            { key: "energy_everyday_on_active", label: "On", isSwitch: true },
            { key: "energy_everyday_on_time", label: "On Time", isTime: true },
            { key: "energy_everyday_off_active", label: "Off", isSwitch: true },
            { key: "energy_everyday_off_time", label: "Off Time", isTime: true },
          ],
        },
      ],
    },
    {
      label: "Weekday / Weekend",
      modeValue: "WeekdayWeekend",
      groups: [
        {
          label: "Weekday",
          rows: [
            { key: "energy_weekday_on_active", label: "On", isSwitch: true },
            { key: "energy_weekday_on_time", label: "On Time", isTime: true },
            { key: "energy_weekday_off_active", label: "Off", isSwitch: true },
            { key: "energy_weekday_off_time", label: "Off Time", isTime: true },
          ],
        },
        {
          label: "Weekend",
          rows: [
            { key: "energy_weekend_on_active", label: "On", isSwitch: true },
            { key: "energy_weekend_on_time", label: "On Time", isTime: true },
            { key: "energy_weekend_off_active", label: "Off", isSwitch: true },
            { key: "energy_weekend_off_time", label: "Off Time", isTime: true },
          ],
        },
      ],
    },
    {
      label: "Daily",
      modeValue: "Daily",
      groups: (function () {
        var dayNames = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
        var dayKeys = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"];
        return dayNames.map(function (name, idx) {
          var dk = dayKeys[idx];
          return {
            label: name,
            rows: [
              { key: "energy_daily_" + dk + "_on_active", label: "On", isSwitch: true },
              { key: "energy_daily_" + dk + "_on_time", label: "On Time", isTime: true },
              { key: "energy_daily_" + dk + "_off_active", label: "Off", isSwitch: true },
              { key: "energy_daily_" + dk + "_off_time", label: "Off Time", isTime: true },
            ],
          };
        });
      })(),
    },
  ];

  // ── CSS ─────────────────────────────────────────────────────────────
  var STYLE = [
    ":host { display: block; }",
    "ha-card { padding: 0; overflow: hidden; }",

    /* Card header */
    ".card-header { display: flex; align-items: center; gap: 10px; padding: 14px 16px; border-bottom: 1px solid var(--divider-color, #e0e0e0); }",
    ".card-header .name { font-size: 1.15em; font-weight: 600; color: var(--primary-text-color); flex: 1; }",
    ".card-header ha-icon { color: var(--primary-color); }",

    /* Device info block */
    ".device-info { padding: 12px 16px; }",
    ".device-info .info-row { display: flex; align-items: center; min-height: 36px; padding: 4px 0; border-bottom: 1px solid var(--divider-color, rgba(0,0,0,0.06)); }",
    ".device-info .info-row:last-child { border-bottom: none; }",
    ".device-info .info-label { flex: 0 0 40%; font-size: 0.85em; color: var(--secondary-text-color); }",
    ".device-info .info-value { flex: 1; font-size: 0.9em; font-weight: 500; color: var(--primary-text-color); cursor: pointer; }",
    ".device-info .info-value.muted { color: var(--secondary-text-color); }",

    /* Red section bar */
    ".zip-section { margin: 0; }",
    ".zip-section-bar { display: flex; align-items: center; width: 100%; padding: 10px 15px; border: none; background: " + ZIP_RED + "; color: #FFFFFF; font: inherit; font-size: 0.9em; font-weight: 600; text-transform: uppercase; letter-spacing: 0.3px; cursor: pointer; text-align: left; box-sizing: border-box; min-height: 40px; line-height: 1.3; }",
    ".zip-section-bar:focus-visible { outline: 2px solid #FFFFFF; outline-offset: -4px; }",
    ".zip-section-bar .bar-title { flex: 1; }",
    ".zip-section-bar .bar-toggle { display: flex; align-items: center; gap: 4px; font-size: 0.8em; font-weight: 400; text-transform: none; letter-spacing: 0; opacity: 0.9; }",
    ".zip-section-bar .bar-chevron { transition: transform 0.2s; font-size: 0.85em; }",
    ".zip-section-bar .bar-chevron.open { transform: rotate(180deg); }",

    /* Section body */
    ".zip-section-body { background: var(--card-background-color, #FFFFFF); }",
    ".zip-section-body.collapsed { display: none; }",

    /* Settings rows */
    ".zip-row { display: flex; align-items: center; justify-content: space-between; gap: 10px; padding: 10px 16px; min-height: 48px; border-bottom: 1px solid var(--divider-color, rgba(0,0,0,0.06)); }",
    ".zip-row:last-child { border-bottom: none; }",
    ".zip-row-label { font-size: 0.88em; color: var(--primary-text-color); flex: 1; cursor: pointer; min-width: 0; }",
    ".zip-row-control { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }",
    ".zip-row-value { font-size: 0.88em; color: var(--primary-text-color); max-width: 14em; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }",
    ".zip-row-value.muted { color: var(--secondary-text-color); }",

    /* Zip toggle (YES/NO segmented control) */
    ".zip-toggle { display: inline-flex; border-radius: 0; overflow: hidden; flex-shrink: 0; font-size: 0.82em; font-weight: 700; line-height: 1; }",
    ".zip-toggle button { border: none; padding: 6px 14px; cursor: pointer; font: inherit; font-weight: 700; color: #FFFFFF; min-width: 44px; text-align: center; transition: opacity 0.15s; }",
    ".zip-toggle button:first-child { background: " + ZIP_GREEN + "; }",
    ".zip-toggle button:last-child { background: " + ZIP_RED + "; }",
    ".zip-toggle button.active { opacity: 1; }",
    ".zip-toggle button:not(.active) { opacity: 0.35; }",
    ".zip-toggle button:focus-visible { outline: 2px solid var(--primary-color); outline-offset: 1px; z-index: 1; }",
    ".zip-toggle.disabled button { opacity: 0.25; cursor: not-allowed; }",

    /* Inputs */
    "input[type='number'], input[type='time'], select { font: inherit; font-size: 0.85em; color: var(--primary-text-color); background: var(--card-background-color, #FFFFFF); border: 1px solid var(--divider-color, #ccc); border-radius: 4px; padding: 5px 8px; }",
    "input[type='number'] { width: 5.5em; }",
    "input[type='time'] { width: 7em; }",
    "select { max-width: 12em; }",
    ".zip-unit { font-size: 0.8em; color: var(--secondary-text-color); margin-left: 2px; }",

    /* More-info button */
    ".zip-more-info { border: none; background: transparent; color: var(--secondary-text-color); cursor: pointer; padding: 2px; display: inline-flex; align-items: center; }",
    ".zip-more-info ha-icon { --mdc-icon-size: 18px; }",

    /* Timers panel */
    ".timers-body { padding: 0; }",
    ".timers-mode-select { padding: 12px 16px 8px; border-bottom: 1px solid var(--divider-color, rgba(0,0,0,0.06)); }",
    ".timers-mode-select label { font-size: 0.85em; color: var(--secondary-text-color); margin-right: 8px; }",
    ".timers-tabs { display: flex; border-bottom: 2px solid var(--divider-color, #e0e0e0); margin: 0 16px; }",
    ".timers-tab { flex: 1; padding: 10px 8px; border: none; background: transparent; font: inherit; font-size: 0.82em; font-weight: 600; color: var(--secondary-text-color); cursor: pointer; text-align: center; border-bottom: 2px solid transparent; margin-bottom: -2px; transition: color 0.15s, border-color 0.15s; }",
    ".timers-tab.active { color: " + ZIP_RED + "; border-bottom-color: " + ZIP_RED + "; }",
    ".timers-tab:focus-visible { outline: 2px solid var(--primary-color); outline-offset: -2px; }",
    ".timers-tab-content { padding: 0; }",
    ".timers-tab-content.hidden { display: none; }",
    ".timers-subgroup { padding: 0; }",
    ".timers-subgroup-title { font-size: 0.8em; font-weight: 700; text-transform: uppercase; color: var(--secondary-text-color); padding: 10px 16px 4px; letter-spacing: 0.5px; }",

    /* Filters panel */
    ".filters-body { padding: 0; }",
    ".filters-subgroup { padding: 0; }",
    ".filters-subgroup-title { font-size: 0.8em; font-weight: 700; text-transform: uppercase; color: var(--secondary-text-color); padding: 10px 16px 4px; letter-spacing: 0.5px; }",
    ".filters-readout { padding: 6px 16px; font-size: 0.85em; color: var(--primary-text-color); }",

    /* Empty / no-data */
    ".no-data { text-align: center; color: var(--secondary-text-color); font-style: italic; padding: 24px 16px; }",
  ].join("\n");

  // ── Utility functions ───────────────────────────────────────────────

  function esc(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function domainOf(entityId) {
    var i = entityId.indexOf(".");
    return i > 0 ? entityId.slice(0, i) : "";
  }

  // Section keys (entity description keys) vs entity_id object_id suffixes.
  var KEY_ALIASES = {
    boiling_temp: ["boiling_temperature", "boiling_temp"],
    chilled_temp: ["chilled_temperature", "chilled_temp"],
    boiling_duration: ["boiling_dispense_duration", "boiling_duration"],
    chilled_duration: ["chilled_dispense_duration", "chilled_duration"],
    sparkling_duration: ["sparkling_dispense_duration", "sparkling_duration"],
    ambient_duration: ["ambient_dispense_duration", "ambient_duration"],
    energy_total: ["total_energy", "energy_total"],
    energy_since_last_log: ["energy_since_last_log"],
    internal_filter_litres: ["internal_filter_litres_limit", "internal_filter_litres"],
    internal_filter_days: ["internal_filter_days_limit", "internal_filter_days"],
    external_filter_litres: ["external_filter_litres_limit", "external_filter_litres"],
    external_filter_days: ["external_filter_days_limit", "external_filter_days"],
    litres_filtered_internal: ["internal_litres_filtered", "litres_filtered_internal"],
    litres_filtered_external: ["external_litres_filtered", "litres_filtered_external"],
    days_filtered_internal: ["internal_days_filtered", "days_filtered_internal"],
    days_filtered_external: ["external_days_filtered", "days_filtered_external"],
    sync_period: ["sync_period", "sync_period_minutes"],
    system_fault: ["system_fault"],
    system_fault_details: ["system_fault_details"],
  };

  function objectId(entityId) {
    var i = String(entityId).indexOf(".");
    return i >= 0 ? String(entityId).slice(i + 1) : String(entityId);
  }

  function extractKeyFromUniqueId(uniqueId) {
    if (!uniqueId) return null;
    var m = String(uniqueId).match(/^zipassist_.+?_(.+)$/);
    return m ? m[1] : null;
  }

  function suffixesForKey(key) {
    var aliases = KEY_ALIASES[key];
    return aliases && aliases.length ? aliases.slice() : [key];
  }

  function entityMatchesKey(entityId, key) {
    var oid = objectId(entityId);
    var suffixes = suffixesForKey(key);
    for (var i = 0; i < suffixes.length; i++) {
      var s = suffixes[i];
      if (oid === s || oid.endsWith("_" + s)) return true;
    }
    return false;
  }

  function collectDeviceEntityIds(hass, deviceId) {
    var out = [];
    var entities = (hass && hass.entities) || {};
    var eids = Object.keys(entities);
    for (var i = 0; i < eids.length; i++) {
      var eid = eids[i];
      var ereg = entities[eid];
      if (!ereg) continue;
      if (deviceId && ereg.device_id && ereg.device_id !== deviceId) continue;
      var platform = ereg.platform || ereg.integration || "";
      var uid = ereg.unique_id || "";
      var onDevice = !!(deviceId && ereg.device_id === deviceId);
      var looksOurs =
        platform === "zipassist" ||
        String(uid).indexOf("zipassist_") === 0 ||
        onDevice;
      if (!looksOurs) continue;
      out.push(eid);
    }
    if (deviceId && out.length === 0) {
      for (var j = 0; j < eids.length; j++) {
        var eid2 = eids[j];
        var ereg2 = entities[eid2];
        if (ereg2 && ereg2.device_id === deviceId) out.push(eid2);
      }
    }
    return out;
  }

  // Collect all known keys from SECTIONS + TIMER_MODES
  function allKnownKeys() {
    var known = {};
    for (var si = 0; si < SECTIONS.length; si++) {
      var list = SECTIONS[si].e || [];
      for (var ki = 0; ki < list.length; ki++) {
        known[list[ki][0]] = true;
      }
    }
    for (var mi = 0; mi < TIMER_MODES.length; mi++) {
      var groups = TIMER_MODES[mi].groups || [];
      for (var gi = 0; gi < groups.length; gi++) {
        var rows = groups[gi].rows || [];
        for (var ri = 0; ri < rows.length; ri++) {
          known[rows[ri].key] = true;
        }
      }
    }
    known["energy_mode"] = true;
    return Object.keys(known);
  }

  function buildEntityMap(hass, deviceId) {
    var ents = {};
    var eids = collectDeviceEntityIds(hass, deviceId);
    var entities = (hass && hass.entities) || {};

    // 1) Prefer unique_id suffix when HA exposes it
    for (var i = 0; i < eids.length; i++) {
      var eid = eids[i];
      var ereg = entities[eid] || {};
      var k = extractKeyFromUniqueId(ereg.unique_id || "");
      if (k) ents[k] = eid;
    }

    // 2) Match section keys / aliases against entity_id object_id suffixes
    var keys = allKnownKeys();
    for (var k = 0; k < keys.length; k++) {
      var key = keys[k];
      if (ents[key]) continue;
      for (var e = 0; e < eids.length; e++) {
        if (entityMatchesKey(eids[e], key)) {
          ents[key] = eids[e];
          break;
        }
      }
    }
    return ents;
  }

  function findZipAssistDeviceId(hass) {
    try {
      if (!hass) return null;
      var devices = hass.devices || {};
      var entities = hass.entities || {};
      var eids = entities && typeof entities === "object" ? Object.keys(entities) : [];
      for (var i = 0; i < eids.length; i++) {
        var ereg = entities[eids[i]];
        if (!ereg || !ereg.device_id) continue;
        var platform = ereg.platform || ereg.integration;
        var uid = ereg.unique_id || "";
        if (platform === "zipassist" || String(uid).startsWith("zipassist_")) {
          return ereg.device_id;
        }
      }
      var dids = devices && typeof devices === "object" ? Object.keys(devices) : [];
      for (var j = 0; j < dids.length; j++) {
        var d = devices[dids[j]];
        var idents = (d && d.identifiers) || [];
        for (var k = 0; k < idents.length; k++) {
          var pair = idents[k];
          if (Array.isArray(pair) && pair[0] === "zipassist") return dids[j];
        }
      }
    } catch (_e) {
      /* picker must never throw */
    }
    return null;
  }

  function formatState(entityId, hass) {
    var st = hass.states[entityId];
    if (!st || st.state === "unavailable" || st.state === "unknown") return "\u2014";
    var raw = st.state;
    var num = Number(raw);
    if (!Number.isNaN(num) && raw !== "" && String(raw).trim() !== "") {
      var unit = (st.attributes && st.attributes.unit_of_measurement) || "";
      var rounded = Math.round(num * 100) / 100;
      return unit ? rounded + " " + unit : String(rounded);
    }
    if (raw === "on") return "On";
    if (raw === "off") return "Off";
    return raw;
  }

  function stateAvailable(st) {
    return !!(st && st.state !== "unavailable" && st.state !== "unknown");
  }

  // ── Card class ──────────────────────────────────────────────────────

  function ZipAssistCard() {
    HTMLElement.call(this);
    this._hass = undefined;
    this._config = {};
    this._collapsed = {};
    this._activeTimerTab = "";
    this._root = this.attachShadow({ mode: "open" });
    this._boundClick = this._onClick.bind(this);
    this._boundChange = this._onChange.bind(this);
    this._renderScheduled = false;
    this._lastSignature = "";
  }

  ZipAssistCard.prototype = Object.create(HTMLElement.prototype);
  ZipAssistCard.prototype.constructor = ZipAssistCard;

  // Static methods
  ZipAssistCard.getStubConfig = function (hass) {
    try {
      if (hass) {
        var device = findZipAssistDeviceId(hass);
        if (device) {
          return { device: device };
        }
      }
    } catch (_e) {}
    return { title: CARD_NAME };
  };

  ZipAssistCard.getConfigForm = function () {
    return {
      schema: [
        {
          name: "device",
          required: true,
          selector: {
            device: { filter: { integration: "zipassist" } },
          },
        },
        { name: "title", selector: { text: {} } },
      ],
    };
  };

  // Instance methods
  ZipAssistCard.prototype.setConfig = function (config) {
    if (!config || typeof config !== "object") {
      this._config = { title: CARD_NAME };
    } else {
      this._config = Object.assign({}, config);
    }
    try {
      this._render();
    } catch (_e) {
      this._renderEmpty("ZipAssist card failed to render.");
    }
  };

  Object.defineProperty(ZipAssistCard.prototype, "hass", {
    get: function () { return this._hass; },
    set: function (hass) {
      this._hass = hass;
      this._scheduleRender(false);
    },
  });

  ZipAssistCard.prototype.getCardSize = function () {
    return 8;
  };

  ZipAssistCard.prototype.getGridOptions = function () {
    return {
      columns: 12,
      min_columns: 6,
      min_rows: 4,
    };
  };

  ZipAssistCard.prototype.connectedCallback = function () {
    this._root.addEventListener("click", this._boundClick);
    this._root.addEventListener("change", this._boundChange);
    this._render();
  };

  ZipAssistCard.prototype.disconnectedCallback = function () {
    this._root.removeEventListener("click", this._boundClick);
    this._root.removeEventListener("change", this._boundChange);
  };

  ZipAssistCard.prototype._scheduleRender = function (force) {
    if (force) this._lastSignature = "";
    if (this._renderScheduled) return;
    this._renderScheduled = true;
    var self = this;
    Promise.resolve().then(function () {
      self._renderScheduled = false;
      self._render();
    });
  };

  ZipAssistCard.prototype._signature = function (deviceId, ents) {
    var h = this._hass;
    if (!h) return "no-hass";
    var parts = [deviceId || "", this._config.title || ""];
    var keys = Object.keys(ents).sort();
    for (var i = 0; i < keys.length; i++) {
      var eid = ents[keys[i]];
      var st = h.states[eid];
      parts.push(eid, st ? st.state : "", st ? st.last_updated : "");
    }
    var ckeys = Object.keys(this._collapsed).sort();
    for (var j = 0; j < ckeys.length; j++) {
      parts.push(ckeys[j], this._collapsed[ckeys[j]] ? "1" : "0");
    }
    parts.push("timerTab", this._activeTimerTab || "");
    return parts.join("|");
  };

  ZipAssistCard.prototype._fireMoreInfo = function (entityId) {
    this.dispatchEvent(
      new CustomEvent("hass-more-info", {
        bubbles: true,
        composed: true,
        detail: { entityId: entityId },
      })
    );
  };

  ZipAssistCard.prototype._onClick = function (ev) {
    var path = typeof ev.composedPath === "function" ? ev.composedPath() : [];
    for (var i = 0; i < path.length; i++) {
      var el = path[i];
      if (!el || !el.getAttribute) continue;

      // Section bar toggle
      if (el.classList && el.classList.contains("zip-section-bar")) {
        var ck = el.getAttribute("data-ck");
        if (!ck) return;
        this._collapsed[ck] = !this._collapsed[ck];
        this._scheduleRender(true);
        return;
      }

      // Zip toggle button
      if (el.classList && el.classList.contains("zip-toggle-btn")) {
        var eid = el.getAttribute("data-eid");
        var action = el.getAttribute("data-action");
        if (eid && action && this._hass) {
          this._hass.callService("switch", action, { entity_id: eid });
        }
        return;
      }

      // Timer tab
      if (el.classList && el.classList.contains("timers-tab")) {
        var tab = el.getAttribute("data-tab");
        if (tab) {
          this._activeTimerTab = tab;
          this._scheduleRender(true);
        }
        return;
      }

      // More info
      var moreInfo = el.getAttribute("data-more-info");
      if (moreInfo) {
        ev.preventDefault();
        this._fireMoreInfo(moreInfo);
        return;
      }
    }
  };

  ZipAssistCard.prototype._onChange = function (ev) {
    var t = ev.target;
    if (!t || !this._hass) return;
    var eid = t.getAttribute && t.getAttribute("data-eid");
    if (!eid && t.closest) {
      var host = t.closest("[data-eid]");
      if (host) eid = host.getAttribute("data-eid");
    }
    if (!eid) return;
    var domain = domainOf(eid);
    if (domain === "number" && t.tagName === "INPUT") {
      var value = Number(t.value);
      if (Number.isNaN(value)) return;
      this._hass.callService("number", "set_value", {
        entity_id: eid,
        value: value,
      });
      return;
    }
    if (domain === "select" && t.tagName === "SELECT") {
      this._hass.callService("select", "select_option", {
        entity_id: eid,
        option: t.value,
      });
      return;
    }
    if (domain === "time" && t.tagName === "INPUT") {
      var time = t.value || "";
      if (/^\d{2}:\d{2}$/.test(time)) time = time + ":00";
      this._hass.callService("time", "set_value", {
        entity_id: eid,
        time: time,
      });
    }
  };

  ZipAssistCard.prototype._renderEmpty = function (message) {
    this._root.innerHTML =
      "<style>" +
      STYLE +
      "</style><ha-card>" +
      '<div class="card-header"><ha-icon icon="mdi:water-pump"></ha-icon>' +
      '<span class="name">' +
      esc(CARD_NAME) +
      "</span></div>" +
      '<div class="no-data">' +
      esc(message) +
      "</div></ha-card>";
    this._lastSignature = message;
  };

  // ── Row renderers ───────────────────────────────────────────────────

  ZipAssistCard.prototype._renderZipToggle = function (entityId, st) {
    var on = st && st.state === "on";
    var available = stateAvailable(st);
    var cls = "zip-toggle" + (available ? "" : " disabled");
    return (
      '<span class="' + cls + '" data-eid="' + esc(entityId) + '">' +
      '<button type="button" class="zip-toggle-btn' + (on ? " active" : "") + '" data-eid="' + esc(entityId) + '" data-action="turn_on" aria-pressed="' + (on ? "true" : "false") + '"' + (available ? "" : " disabled") + '>YES</button>' +
      '<button type="button" class="zip-toggle-btn' + (on ? "" : " active") + '" data-eid="' + esc(entityId) + '" data-action="turn_off" aria-pressed="' + (on ? "false" : "true") + '"' + (available ? "" : " disabled") + '>NO</button>' +
      "</span>"
    );
  };

  ZipAssistCard.prototype._renderNumberInput = function (entityId, st) {
    var available = stateAvailable(st);
    var disabled = available ? "" : " disabled";
    var minAttr = "";
    var maxAttr = "";
    if (st) {
      var min = st.attributes.min != null ? st.attributes.min : (st.attributes.min_value != null ? st.attributes.min_value : null);
      var max = st.attributes.max != null ? st.attributes.max : (st.attributes.max_value != null ? st.attributes.max_value : null);
      if (min != null) minAttr = ' min="' + esc(min) + '"';
      if (max != null) maxAttr = ' max="' + esc(max) + '"';
    }
    var step = (st && st.attributes.step != null) ? st.attributes.step : 1;
    var val = available ? (st ? st.state : "") : "";
    var unit = (st && st.attributes && st.attributes.unit_of_measurement) || "";
    return (
      '<input type="number" data-eid="' + esc(entityId) + '" value="' + esc(val) + '"' +
      minAttr + maxAttr + ' step="' + esc(step) + '"' + disabled + " />" +
      (unit ? '<span class="zip-unit">' + esc(unit) + "</span>" : "")
    );
  };

  ZipAssistCard.prototype._renderSelect = function (entityId, st) {
    var available = stateAvailable(st);
    var disabled = available ? "" : " disabled";
    var options = (st && st.attributes.options) || [];
    var html = '<select data-eid="' + esc(entityId) + '"' + disabled + ">";
    for (var i = 0; i < options.length; i++) {
      var opt = options[i];
      var sel = (st && st.state === opt) ? " selected" : "";
      html += '<option value="' + esc(opt) + '"' + sel + ">" + esc(opt) + "</option>";
    }
    html += "</select>";
    return html;
  };

  ZipAssistCard.prototype._renderTimeInput = function (entityId, st) {
    var available = stateAvailable(st);
    var disabled = available ? "" : " disabled";
    var val = available ? String(st ? st.state : "") : "";
    if (/^\d{2}:\d{2}:\d{2}/.test(val)) val = val.slice(0, 5);
    return (
      '<input type="time" data-eid="' + esc(entityId) + '" value="' + esc(val) + '"' + disabled + " />"
    );
  };

  ZipAssistCard.prototype._renderSensorValue = function (entityId) {
    return (
      '<span class="zip-row-value">' +
      esc(formatState(entityId, this._hass)) +
      "</span>"
    );
  };

  // ── Section renderers ───────────────────────────────────────────────

  ZipAssistCard.prototype._renderSectionBar = function (title, ck, collapsed) {
    return (
      '<button type="button" class="zip-section-bar" data-ck="' + esc(ck) +
      '" aria-expanded="' + (collapsed ? "false" : "true") + '">' +
      '<span class="bar-title">' + esc(title) + "</span>" +
      '<span class="bar-toggle">' +
      (collapsed ? "SHOW" : "HIDE") +
      ' <span class="bar-chevron' + (collapsed ? "" : " open") + '">\u25BC</span>' +
      "</span></button>"
    );
  };

  ZipAssistCard.prototype._renderSettingsRow = function (entityId, label, st) {
    var domain = domainOf(entityId);
    var html = '<div class="zip-row">';
    html +=
      '<span class="zip-row-label" data-more-info="' + esc(entityId) + '">' +
      esc(label) + "</span>";
    html += '<div class="zip-row-control">';

    if (domain === "switch") {
      html += this._renderZipToggle(entityId, st);
    } else if (domain === "number") {
      html += this._renderNumberInput(entityId, st);
    } else if (domain === "select") {
      html += this._renderSelect(entityId, st);
    } else if (domain === "time") {
      html += this._renderTimeInput(entityId, st);
    } else {
      html += this._renderSensorValue(entityId);
    }

    html +=
      '<button type="button" class="zip-more-info" data-more-info="' +
      esc(entityId) + '" title="More info" aria-label="More info">' +
      '<ha-icon icon="mdi:information-outline"></ha-icon></button>';
    html += "</div></div>";
    return html;
  };

  // ── Device info block ───────────────────────────────────────────────

  ZipAssistCard.prototype._renderDeviceInfo = function (ents, hass) {
    var sec = SECTIONS[0]; // Device Info is always first
    var html = '<div class="device-info">';
    var hasAny = false;
    for (var ii = 0; ii < sec.e.length; ii++) {
      var key = sec.e[ii][0];
      var label = sec.e[ii][1];
      var eid = ents[key];
      if (!eid || !hass.states[eid]) continue;
      hasAny = true;
      var st = hass.states[eid];
      var available = stateAvailable(st);
      html += '<div class="info-row">';
      html += '<span class="info-label">' + esc(label) + "</span>";
      html +=
        '<span class="info-value' + (available ? "" : " muted") +
        '" data-more-info="' + esc(eid) + '">' +
        esc(formatState(eid, hass)) + "</span>";
      html += "</div>";
    }
    html += "</div>";
    return hasAny ? html : "";
  };

  // ── Settings panel ──────────────────────────────────────────────────

  ZipAssistCard.prototype._renderSettingsPanel = function (sec, ents, hass, deviceId) {
    var avail = [];
    for (var ii = 0; ii < sec.e.length; ii++) {
      var key = sec.e[ii][0];
      var label = sec.e[ii][1];
      var eid = ents[key];
      if (eid && hass.states[eid]) {
        avail.push({ id: eid, label: label, key: key });
      }
    }
    if (!avail.length) return "";

    var ck = deviceId + "||" + sec.t;
    var collapsed = !!this._collapsed[ck];

    var html = '<div class="zip-section">';
    html += this._renderSectionBar(sec.t, ck, collapsed);
    html += '<div class="zip-section-body' + (collapsed ? " collapsed" : "") + '">';
    for (var aj = 0; aj < avail.length; aj++) {
      var be = avail[aj];
      html += this._renderSettingsRow(be.id, be.label, hass.states[be.id]);
    }
    html += "</div></div>";
    return html;
  };

  // ── Filters panel ───────────────────────────────────────────────────

  ZipAssistCard.prototype._renderFiltersPanel = function (sec, ents, hass, deviceId) {
    var readouts = [];
    var internalLimits = [];
    var externalLimits = [];

    for (var ii = 0; ii < sec.e.length; ii++) {
      var key = sec.e[ii][0];
      var label = sec.e[ii][1];
      var eid = ents[key];
      if (!eid || !hass.states[eid]) continue;
      if (key.indexOf("internal_") === 0) {
        internalLimits.push({ id: eid, label: label, key: key });
      } else if (key.indexOf("external_") === 0) {
        externalLimits.push({ id: eid, label: label, key: key });
      } else {
        readouts.push({ id: eid, label: label, key: key });
      }
    }

    if (!readouts.length && !internalLimits.length && !externalLimits.length) return "";

    var ck = deviceId + "||" + sec.t;
    var collapsed = !!this._collapsed[ck];

    var html = '<div class="zip-section">';
    html += this._renderSectionBar(sec.t, ck, collapsed);
    html += '<div class="zip-section-body' + (collapsed ? " collapsed" : "") + '">';
    html += '<div class="filters-body">';

    // Readouts (filter life remaining)
    if (readouts.length) {
      html += '<div class="filters-readout">';
      for (var ri = 0; ri < readouts.length; ri++) {
        var r = readouts[ri];
        html +=
          '<div class="zip-row"><span class="zip-row-label" data-more-info="' +
          esc(r.id) + '">' + esc(r.label) + "</span>" +
          '<div class="zip-row-control">' +
          this._renderSensorValue(r.id) +
          '<button type="button" class="zip-more-info" data-more-info="' +
          esc(r.id) + '" title="More info" aria-label="More info">' +
          '<ha-icon icon="mdi:information-outline"></ha-icon></button>' +
          "</div></div>";
      }
      html += "</div>";
    }

    // Internal filter limits
    if (internalLimits.length) {
      html += '<div class="filters-subgroup">';
      html += '<div class="filters-subgroup-title">Internal Filter Limits</div>';
      for (var ili = 0; ili < internalLimits.length; ili++) {
        var il = internalLimits[ili];
        html += this._renderSettingsRow(il.id, il.label.replace("Internal ", ""), hass.states[il.id]);
      }
      html += "</div>";
    }

    // External filter limits
    if (externalLimits.length) {
      html += '<div class="filters-subgroup">';
      html += '<div class="filters-subgroup-title">External Filter Limits</div>';
      for (var eli = 0; eli < externalLimits.length; eli++) {
        var el = externalLimits[eli];
        html += this._renderSettingsRow(el.id, el.label.replace("External ", ""), hass.states[el.id]);
      }
      html += "</div>";
    }

    html += "</div></div></div>";
    return html;
  };

  // ── Timers panel ────────────────────────────────────────────────────

  ZipAssistCard.prototype._renderTimersPanel = function (ents, hass, deviceId) {
    var energyModeEid = ents["energy_mode"];
    var hasAnyTimer = false;
    for (var mi = 0; mi < TIMER_MODES.length; mi++) {
      var groups = TIMER_MODES[mi].groups || [];
      for (var gi = 0; gi < groups.length; gi++) {
        var rows = groups[gi].rows || [];
        for (var ri = 0; ri < rows.length; ri++) {
          if (ents[rows[ri].key] && hass.states[ents[rows[ri].key]]) {
            hasAnyTimer = true;
            break;
          }
        }
        if (hasAnyTimer) break;
      }
      if (hasAnyTimer) break;
    }
    if (!hasAnyTimer && !energyModeEid) return "";

    var ck = deviceId + "||ON/OFF TIMERS";
    var collapsed = !!this._collapsed[ck];

    // Determine active tab
    var activeTab = this._activeTimerTab;
    if (!activeTab) {
      if (energyModeEid && hass.states[energyModeEid]) {
        var currentMode = hass.states[energyModeEid].state;
        for (var ti = 0; ti < TIMER_MODES.length; ti++) {
          if (currentMode === TIMER_MODES[ti].modeValue ||
              currentMode === TIMER_MODES[ti].label) {
            activeTab = String(ti);
            break;
          }
        }
      }
      if (!activeTab) activeTab = "0";
    }

    var html = '<div class="zip-section">';
    html += this._renderSectionBar("ON/OFF TIMERS", ck, collapsed);
    html += '<div class="zip-section-body' + (collapsed ? " collapsed" : "") + '">';
    html += '<div class="timers-body">';

    // Energy mode select
    if (energyModeEid && hass.states[energyModeEid]) {
      html += '<div class="timers-mode-select">';
      html += '<label>Active Mode:</label>';
      html += this._renderSelect(energyModeEid, hass.states[energyModeEid]);
      html += "</div>";
    }

    // Tabs
    html += '<div class="timers-tabs">';
    for (var tbi = 0; tbi < TIMER_MODES.length; tbi++) {
      var isActive = (String(tbi) === activeTab);
      html +=
        '<button type="button" class="timers-tab' + (isActive ? " active" : "") +
        '" data-tab="' + tbi + '" role="tab" aria-selected="' + (isActive ? "true" : "false") + '">' +
        esc(TIMER_MODES[tbi].label) + "</button>";
    }
    html += "</div>";

    // Tab content
    for (var tci = 0; tci < TIMER_MODES.length; tci++) {
      var isVisible = (String(tci) === activeTab);
      html += '<div class="timers-tab-content' + (isVisible ? "" : " hidden") + '" role="tabpanel">';

      var modeGroups = TIMER_MODES[tci].groups || [];
      for (var mgi = 0; mgi < modeGroups.length; mgi++) {
        var group = modeGroups[mgi];
        if (modeGroups.length > 1) {
          html += '<div class="timers-subgroup">';
          html += '<div class="timers-subgroup-title">' + esc(group.label) + "</div>";
        }

        for (var rowi = 0; rowi < group.rows.length; rowi++) {
          var row = group.rows[rowi];
          var eid = ents[row.key];
          if (!eid || !hass.states[eid]) continue;
          var st = hass.states[eid];
          html += '<div class="zip-row">';
          html +=
            '<span class="zip-row-label" data-more-info="' + esc(eid) + '">' +
            esc(row.label) + "</span>";
          html += '<div class="zip-row-control">';
          if (row.isSwitch) {
            html += this._renderZipToggle(eid, st);
          } else if (row.isTime) {
            html += this._renderTimeInput(eid, st);
          }
          html +=
            '<button type="button" class="zip-more-info" data-more-info="' +
            esc(eid) + '" title="More info" aria-label="More info">' +
            '<ha-icon icon="mdi:information-outline"></ha-icon></button>';
          html += "</div></div>";
        }

        if (modeGroups.length > 1) {
          html += "</div>";
        }
      }

      html += "</div>";
    }

    html += "</div></div></div>";
    return html;
  };

  // ── Main render ─────────────────────────────────────────────────────

  ZipAssistCard.prototype._render = function () {
    var hass = this._hass;
    var config = this._config || {};

    if (!hass) {
      this._renderEmpty("Waiting for Home Assistant\u2026");
      return;
    }

    var deviceId = config.device;
    if (deviceId && hass.devices && !hass.devices[deviceId]) {
      var needle = String(deviceId).toLowerCase();
      var dids = Object.keys(hass.devices);
      for (var i = 0; i < dids.length; i++) {
        var d = hass.devices[dids[i]];
        var name = ((d && (d.name_by_user || d.name)) || "").toLowerCase();
        if (name && name.indexOf(needle) !== -1) {
          deviceId = dids[i];
          break;
        }
      }
    }

    if (!deviceId) {
      deviceId = findZipAssistDeviceId(hass);
      if (deviceId && !config.device) {
        this._config = Object.assign({}, config, { device: deviceId });
      }
    }

    if (!deviceId) {
      this._renderEmpty(
        "No HydroTap device found. Open the card editor and select a ZipAssist device."
      );
      return;
    }

    var ents = buildEntityMap(hass, deviceId);
    var sig = this._signature(deviceId, ents);
    if (sig === this._lastSignature) return;
    this._lastSignature = sig;

    if (!Object.keys(ents).length) {
      this._renderEmpty(
        "No entities found for this device yet. Check the integration loaded entities, then refresh the dashboard."
      );
      return;
    }

    var dev = (hass.devices && hass.devices[deviceId]) || {};
    var title = config.title || dev.name_by_user || dev.name || CARD_NAME;

    var html = "<style>" + STYLE + "</style><ha-card>";

    // Card header
    html +=
      '<div class="card-header"><ha-icon icon="mdi:water-pump"></ha-icon>' +
      '<span class="name">' + esc(title) + "</span></div>";

    // Render sections in order
    for (var si = 0; si < SECTIONS.length; si++) {
      var sec = SECTIONS[si];
      if (sec.type === "info") {
        html += this._renderDeviceInfo(ents, hass);
      } else if (sec.type === "settings") {
        html += this._renderSettingsPanel(sec, ents, hass, deviceId);
      } else if (sec.type === "filters") {
        html += this._renderFiltersPanel(sec, ents, hass, deviceId);
      } else if (sec.type === "timers") {
        html += this._renderTimersPanel(ents, hass, deviceId);
      }
    }

    html += "</ha-card>";
    this._root.innerHTML = html;
  };

  // ── Register ────────────────────────────────────────────────────────

  if (!customElements.get(CARD_TYPE)) {
    customElements.define(CARD_TYPE, ZipAssistCard);
  }

  // Picker metadata
  window.customCards = window.customCards || [];
  var cardInfo = {
    type: CARD_TYPE,
    name: CARD_NAME,
    description: CARD_DESCRIPTION,
    preview: false,
    documentationURL: DOC_URL,
  };
  var updated = false;
  for (var i = 0; i < window.customCards.length; i++) {
    if (window.customCards[i].type === CARD_TYPE) {
      window.customCards[i] = cardInfo;
      updated = true;
      break;
    }
  }
  if (!updated) {
    window.customCards.push(cardInfo);
  }
})();