/**
 * ZipAssist HydroTap Lovelace card.
 *
 * Loaded via the integration's static path + add_extra_js_url.
 * Uses shadow DOM, ha-card, and native custom elements (no external CDN).
 */
(function () {
  "use strict";

  const CARD_TYPE = "zipassist-card";
  const CARD_NAME = "ZipAssist HydroTap";
  const CARD_DESCRIPTION =
    "ZipAssist CMMS HydroTap monitoring and control card";
  const DOC_URL =
    "https://github.com/Squazel/homeassistant-zipassist/blob/main/docs/dashboards.md";

  // ── Zip brand tokens ────────────────────────────────────────────────
  const ZIP_RED = "#E61837";
  const ZIP_GREEN = "#28B62C";

  // ── Section definitions (official site order) ───────────────────────
  // type: "info" = device info block (non-collapsible, no red bar)
  // type: "settings" = red-bar collapsible panel
  // type: "timers" = special nested-tabs panel
  // type: "filters" = internal/external sub-group panel

  const SECTIONS = [
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
  const TIMER_MODES = [
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
        const dayNames = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
        const dayKeys = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"];
        return dayNames.map((name, idx) => {
          const dk = dayKeys[idx];
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

  const STYLE = `
    :host {
      display: block;
    }
    ha-card {
      padding: 0;
      overflow: hidden;
    }

    /* ── Card header ── */
    .card-header {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 14px 16px;
      border-bottom: 1px solid var(--divider-color, #e0e0e0);
    }
    .card-header .name {
      font-size: 1.15em;
      font-weight: 600;
      color: var(--primary-text-color);
      flex: 1;
    }
    .card-header ha-icon {
      color: var(--primary-color);
    }

    /* ── Device info block ── */
    .device-info {
      padding: 12px 16px;
    }
    .device-info .info-row {
      display: flex;
      align-items: center;
      min-height: 36px;
      padding: 4px 0;
      border-bottom: 1px solid var(--divider-color, rgba(0,0,0,0.06));
    }
    .device-info .info-row:last-child {
      border-bottom: none;
    }
    .device-info .info-label {
      flex: 0 0 40%;
      font-size: 0.85em;
      color: var(--secondary-text-color);
    }
    .device-info .info-value {
      flex: 1;
      font-size: 0.9em;
      font-weight: 500;
      color: var(--primary-text-color);
      cursor: pointer;
    }
    .device-info .info-value.muted {
      color: var(--secondary-text-color);
    }

    /* ── Red section bar ── */
    .zip-section {
      margin: 0;
    }
    .zip-section-bar {
      display: flex;
      align-items: center;
      width: 100%;
      padding: 10px 15px;
      border: none;
      background: ${ZIP_RED};
      color: #FFFFFF;
      font: inherit;
      font-size: 0.9em;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.3px;
      cursor: pointer;
      text-align: left;
      box-sizing: border-box;
      min-height: 40px;
      line-height: 1.3;
    }
    .zip-section-bar:focus-visible {
      outline: 2px solid #FFFFFF;
      outline-offset: -4px;
    }
    .zip-section-bar .bar-title {
      flex: 1;
    }
    .zip-section-bar .bar-toggle {
      display: flex;
      align-items: center;
      gap: 4px;
      font-size: 0.8em;
      font-weight: 400;
      text-transform: none;
      letter-spacing: 0;
      opacity: 0.9;
    }
    .zip-section-bar .bar-chevron {
      transition: transform 0.2s;
      font-size: 0.85em;
    }
    .zip-section-bar .bar-chevron.open {
      transform: rotate(180deg);
    }

    /* ── Section body ── */
    .zip-section-body {
      background: var(--card-background-color, #FFFFFF);
    }
    .zip-section-body.collapsed {
      display: none;
    }

    /* ── Settings rows ── */
    .zip-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      padding: 10px 16px;
      min-height: 48px;
      border-bottom: 1px solid var(--divider-color, rgba(0,0,0,0.06));
    }
    .zip-row:last-child {
      border-bottom: none;
    }
    .zip-row-label {
      font-size: 0.88em;
      color: var(--primary-text-color);
      flex: 1;
      cursor: pointer;
      min-width: 0;
    }
    .zip-row-control {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-shrink: 0;
    }
    .zip-row-value {
      font-size: 0.88em;
      color: var(--primary-text-color);
      max-width: 14em;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .zip-row-value.muted {
      color: var(--secondary-text-color);
    }

    /* ── Zip toggle (YES/NO segmented control) ── */
    .zip-toggle {
      display: inline-flex;
      border-radius: 0;
      overflow: hidden;
      flex-shrink: 0;
      font-size: 0.82em;
      font-weight: 700;
      line-height: 1;
    }
    .zip-toggle button {
      border: none;
      padding: 6px 14px;
      cursor: pointer;
      font: inherit;
      font-weight: 700;
      color: #FFFFFF;
      min-width: 44px;
      text-align: center;
      transition: opacity 0.15s;
    }
    .zip-toggle button:first-child {
      background: ${ZIP_GREEN};
    }
    .zip-toggle button:last-child {
      background: ${ZIP_RED};
    }
    .zip-toggle button.active {
      opacity: 1;
    }
    .zip-toggle button:not(.active) {
      opacity: 0.35;
    }
    .zip-toggle button:focus-visible {
      outline: 2px solid var(--primary-color);
      outline-offset: 1px;
      z-index: 1;
    }
    .zip-toggle.disabled button {
      opacity: 0.25;
      cursor: not-allowed;
    }

    /* ── Inputs ── */
    input[type="number"],
    input[type="time"],
    select {
      font: inherit;
      font-size: 0.85em;
      color: var(--primary-text-color);
      background: var(--card-background-color, #FFFFFF);
      border: 1px solid var(--divider-color, #ccc);
      border-radius: 4px;
      padding: 5px 8px;
    }
    input[type="number"] {
      width: 5.5em;
    }
    input[type="time"] {
      width: 7em;
    }
    select {
      max-width: 12em;
    }
    .zip-unit {
      font-size: 0.8em;
      color: var(--secondary-text-color);
      margin-left: 2px;
    }

    /* ── More-info button ── */
    .zip-more-info {
      border: none;
      background: transparent;
      color: var(--secondary-text-color);
      cursor: pointer;
      padding: 2px;
      display: inline-flex;
      align-items: center;
    }
    .zip-more-info ha-icon {
      --mdc-icon-size: 18px;
    }

    /* ── Timers panel ── */
    .timers-body {
      padding: 0;
    }
    .timers-mode-select {
      padding: 12px 16px 8px;
      border-bottom: 1px solid var(--divider-color, rgba(0,0,0,0.06));
    }
    .timers-mode-select label {
      font-size: 0.85em;
      color: var(--secondary-text-color);
      margin-right: 8px;
    }
    .timers-tabs {
      display: flex;
      border-bottom: 2px solid var(--divider-color, #e0e0e0);
      margin: 0 16px;
    }
    .timers-tab {
      flex: 1;
      padding: 10px 8px;
      border: none;
      background: transparent;
      font: inherit;
      font-size: 0.82em;
      font-weight: 600;
      color: var(--secondary-text-color);
      cursor: pointer;
      text-align: center;
      border-bottom: 2px solid transparent;
      margin-bottom: -2px;
      transition: color 0.15s, border-color 0.15s;
    }
    .timers-tab.active {
      color: ${ZIP_RED};
      border-bottom-color: ${ZIP_RED};
    }
    .timers-tab:focus-visible {
      outline: 2px solid var(--primary-color);
      outline-offset: -2px;
    }
    .timers-tab-content {
      padding: 0;
    }
    .timers-tab-content.hidden {
      display: none;
    }
    .timers-subgroup {
      padding: 0;
    }
    .timers-subgroup-title {
      font-size: 0.8em;
      font-weight: 700;
      text-transform: uppercase;
      color: var(--secondary-text-color);
      padding: 10px 16px 4px;
      letter-spacing: 0.5px;
    }

    /* ── Filters panel ── */
    .filters-body {
      padding: 0;
    }
    .filters-subgroup {
      padding: 0;
    }
    .filters-subgroup-title {
      font-size: 0.8em;
      font-weight: 700;
      text-transform: uppercase;
      color: var(--secondary-text-color);
      padding: 10px 16px 4px;
      letter-spacing: 0.5px;
    }
    .filters-readout {
      padding: 6px 16px;
      font-size: 0.85em;
      color: var(--primary-text-color);
    }

    /* ── Empty / no-data ── */
    .no-data {
      text-align: center;
      color: var(--secondary-text-color);
      font-style: italic;
      padding: 24px 16px;
    }
  `;

  function esc(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function domainOf(entityId) {
    const i = entityId.indexOf(".");
    return i > 0 ? entityId.slice(0, i) : "";
  }

  // Section keys (entity description keys) vs entity_id object_id suffixes.
  // HA frontend often omits unique_id on hass.entities, and entity_ids are
  // built from translated names, not always the description key.
  const KEY_ALIASES = {
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
    const i = String(entityId).indexOf(".");
    return i >= 0 ? String(entityId).slice(i + 1) : String(entityId);
  }

  function extractKeyFromUniqueId(uniqueId) {
    if (!uniqueId) return null;
    const m = String(uniqueId).match(/^zipassist_.+?_(.+)$/);
    return m ? m[1] : null;
  }

  function suffixesForKey(key) {
    const aliases = KEY_ALIASES[key];
    return aliases && aliases.length ? aliases.slice() : [key];
  }

  function entityMatchesKey(entityId, key) {
    const oid = objectId(entityId);
    const suffixes = suffixesForKey(key);
    for (let i = 0; i < suffixes.length; i++) {
      const s = suffixes[i];
      if (oid === s || oid.endsWith("_" + s)) return true;
    }
    return false;
  }

  function collectDeviceEntityIds(hass, deviceId) {
    const out = [];
    const entities = (hass && hass.entities) || {};
    const eids = Object.keys(entities);
    for (let i = 0; i < eids.length; i++) {
      const eid = eids[i];
      const ereg = entities[eid];
      if (!ereg) continue;
      if (deviceId && ereg.device_id && ereg.device_id !== deviceId) continue;
      const platform = ereg.platform || ereg.integration || "";
      const uid = ereg.unique_id || "";
      const onDevice = !!(deviceId && ereg.device_id === deviceId);
      const looksOurs =
        platform === "zipassist" ||
        String(uid).indexOf("zipassist_") === 0 ||
        onDevice;
      if (!looksOurs) continue;
      out.push(eid);
    }
    // Fallback: any entity on device
    if (deviceId && out.length === 0) {
      for (let j = 0; j < eids.length; j++) {
        const eid2 = eids[j];
        const ereg2 = entities[eid2];
        if (ereg2 && ereg2.device_id === deviceId) out.push(eid2);
      }
    }
    return out;
  }

  function buildEntityMap(hass, deviceId) {
    const ents = {};
    const eids = collectDeviceEntityIds(hass, deviceId);
    const entities = (hass && hass.entities) || {};

    // 1) Prefer unique_id suffix when HA exposes it
    for (let i = 0; i < eids.length; i++) {
      const eid = eids[i];
      const ereg = entities[eid] || {};
      const k = extractKeyFromUniqueId(ereg.unique_id || "");
      if (k) ents[k] = eid;
    }

    // 2) Match section keys / aliases against entity_id object_id suffixes.
    // Collect all known keys from SECTIONS + TIMER_MODES
    const known = {};
    for (let si = 0; si < SECTIONS.length; si++) {
      const list = SECTIONS[si].e || [];
      for (let ki = 0; ki < list.length; ki++) {
        known[list[ki][0]] = true;
      }
    }
    for (let mi = 0; mi < TIMER_MODES.length; mi++) {
      const groups = TIMER_MODES[mi].groups || [];
      for (let gi = 0; gi < groups.length; gi++) {
        const rows = groups[gi].rows || [];
        for (let ri = 0; ri < rows.length; ri++) {
          known[rows[ri].key] = true;
        }
      }
    }
    known["energy_mode"] = true;
    const keys = Object.keys(known);
    for (let k = 0; k < keys.length; k++) {
      const key = keys[k];
      if (ents[key]) continue;
      for (let e = 0; e < eids.length; e++) {
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
      const devices = hass.devices || {};
      const entities = hass.entities || {};
      const eids = entities && typeof entities === "object" ? Object.keys(entities) : [];
      for (let i = 0; i < eids.length; i++) {
        const ereg = entities[eids[i]];
        if (!ereg || !ereg.device_id) continue;
        const platform = ereg.platform || ereg.integration;
        const uid = ereg.unique_id || "";
        if (platform === "zipassist" || String(uid).startsWith("zipassist_")) {
          return ereg.device_id;
        }
      }
      const dids = devices && typeof devices === "object" ? Object.keys(devices) : [];
      for (let j = 0; j < dids.length; j++) {
        const d = devices[dids[j]];
        const idents = (d && d.identifiers) || [];
        for (let k = 0; k < idents.length; k++) {
          const pair = idents[k];
          if (Array.isArray(pair) && pair[0] === "zipassist") return dids[j];
        }
      }
    } catch (_e) {
      /* picker must never throw */
    }
    return null;
  }

  function formatState(entityId, hass) {
    const st = hass.states[entityId];
    if (!st || st.state === "unavailable" || st.state === "unknown") return "—";
    const raw = st.state;
    const num = Number(raw);
    if (!Number.isNaN(num) && raw !== "" && String(raw).trim() !== "") {
      const unit = (st.attributes && st.attributes.unit_of_measurement) || "";
      const rounded = Math.round(num * 100) / 100;
      return unit ? rounded + " " + unit : String(rounded);
    }
    if (raw === "on") return "On";
    if (raw === "off") return "Off";
    return raw;
  }

  function stateAvailable(st) {
    return !!(st && st.state !== "unavailable" && st.state !== "unknown");
  }

  class ZipAssistCard extends HTMLElement {
    constructor() {
      super();
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

    static getStubConfig(hass) {
      // CRITICAL for picker: must be sync and never throw, or Lit until() spins forever.
      // preview:false means HA shows name/description only after this returns.
      try {
        if (hass) {
          var device = findZipAssistDeviceId(hass);
          if (device) {
            return { device: device };
          }
        }
      } catch (_e) {}
      return { title: CARD_NAME };
    }

    static getConfigForm() {
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
    }

    setConfig(config) {
      // Prefer not throwing: a throw during picker/editor setup can strand the UI.
      if (!config || typeof config !== "object") {
        this._config = { title: CARD_NAME };
      } else {
        this._config = Object.assign({}, config);
      }
      // Paint immediately so the editor never shows an empty/spinner frame.
      try {
        this._render();
      } catch (_e) {
        this._renderEmpty("ZipAssist card failed to render.");
      }
    }

    set hass(hass) {
      this._hass = hass;
      this._scheduleRender(false);
    }

    get hass() {
      return this._hass;
    }

    getCardSize() {
      return 8;
    }

    getGridOptions() {
      return {
        columns: 12,
        min_columns: 6,
        min_rows: 4,
      };
    }

    connectedCallback() {
      this._root.addEventListener("click", this._boundClick);
      this._root.addEventListener("change", this._boundChange);
      this._render();
    }

    disconnectedCallback() {
      this._root.removeEventListener("click", this._boundClick);
      this._root.removeEventListener("change", this._boundChange);
    }

    _scheduleRender(force) {
      if (force) this._lastSignature = "";
      if (this._renderScheduled) return;
      this._renderScheduled = true;
      Promise.resolve().then(() => {
        this._renderScheduled = false;
        this._render();
      });
    }

    _signature(deviceId, ents) {
      const h = this._hass;
      if (!h) return "no-hass";
      const parts = [deviceId || "", this._config.title || ""];
      const keys = Object.keys(ents).sort();
      for (let i = 0; i < keys.length; i++) {
        const eid = ents[keys[i]];
        const st = h.states[eid];
        parts.push(eid, st ? st.state : "", st ? st.last_updated : "");
      }
      const ckeys = Object.keys(this._collapsed).sort();
      for (let j = 0; j < ckeys.length; j++) {
        parts.push(ckeys[j], this._collapsed[ckeys[j]] ? "1" : "0");
      }
      parts.push("timerTab", this._activeTimerTab || "");
      return parts.join("|");
    }

    _fireMoreInfo(entityId) {
      this.dispatchEvent(
        new CustomEvent("hass-more-info", {
          bubbles: true,
          composed: true,
          detail: { entityId: entityId },
        })
      );
    }

    _onClick(ev) {
      const path = typeof ev.composedPath === "function" ? ev.composedPath() : [];
      for (let i = 0; i < path.length; i++) {
        const el = path[i];
        if (!el || !el.getAttribute) continue;

        // Section bar toggle
        if (el.classList && el.classList.contains("zip-section-bar")) {
          const ck = el.getAttribute("data-ck");
          if (!ck) return;
          this._collapsed[ck] = !this._collapsed[ck];
          this._scheduleRender(true);
          return;
        }

        // Zip toggle button
        if (el.classList && el.classList.contains("zip-toggle-btn")) {
          const eid = el.getAttribute("data-eid");
          const action = el.getAttribute("data-action");
          if (eid && action && this._hass) {
            this._hass.callService("switch", action, { entity_id: eid });
          }
          return;
        }

        // Timer tab
        if (el.classList && el.classList.contains("timers-tab")) {
          const tab = el.getAttribute("data-tab");
          if (tab) {
            this._activeTimerTab = tab;
            this._scheduleRender(true);
          }
          return;
        }

        const moreInfo = el.getAttribute("data-more-info");
        if (moreInfo) {
          ev.preventDefault();
          this._fireMoreInfo(moreInfo);
          return;
        }
      }
    }

    _onChange(ev) {
      const t = ev.target;
      if (!t || !this._hass) return;
      let eid = t.getAttribute && t.getAttribute("data-eid");
      if (!eid && t.closest) {
        const host = t.closest("[data-eid]");
        if (host) eid = host.getAttribute("data-eid");
      }
      if (!eid) return;
      const domain = domainOf(eid);
      if (domain === "number" && t.tagName === "INPUT") {
        const value = Number(t.value);
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
        let time = t.value || "";
        if (/^\d{2}:\d{2}$/.test(time)) time = time + ":00";
        this._hass.callService("time", "set_value", {
          entity_id: eid,
          time: time,
        });
      }
    }

    _renderEmpty(message) {
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
    }

    _renderControl(entityId, st) {
      const domain = domainOf(entityId);
      const available = stateAvailable(st);
      const disabled = available ? "" : " disabled";

      if (domain === "switch") {
        const on = st && st.state === "on";
        const cls = "zip-toggle" + (available ? "" : " disabled");
        return (
          '<span class="' + cls + '" data-eid="' + esc(entityId) + '">' +
          '<button type="button" class="zip-toggle-btn' + (on ? " active" : "") + '" data-eid="' + esc(entityId) + '" data-action="turn_on" aria-pressed="' + (on ? "true" : "false") + '"' + (available ? "" : " disabled") + '>YES</button>' +
          '<button type="button" class="zip-toggle-btn' + (on ? "" : " active") + '" data-eid="' + esc(entityId) + '" data-action="turn_off" aria-pressed="' + (on ? "false" : "true") + '"' + (available ? "" : " disabled") + '>NO</button>' +
          "</span>"
        );
      }

      if (domain === "number" && st) {
        const min =
          st.attributes.min != null
            ? st.attributes.min
            : st.attributes.min_value != null
              ? st.attributes.min_value
              : "";
        const max =
          st.attributes.max != null
            ? st.attributes.max
            : st.attributes.max_value != null
              ? st.attributes.max_value
              : "";
        const step = st.attributes.step != null ? st.attributes.step : 1;
        const val = available ? st.state : "";
        const unit = (st.attributes && st.attributes.unit_of_measurement) || "";
        return (
          '<input type="number" data-eid="' +
          esc(entityId) +
          '" value="' +
          esc(val) +
          '"' +
          (min !== "" ? ' min="' + esc(min) + '"' : "") +
          (max !== "" ? ' max="' + esc(max) + '"' : "") +
          ' step="' +
          esc(step) +
          '"' +
          disabled +
          " />" +
          (unit ? '<span class="zip-unit">' + esc(unit) + "</span>" : "")
        );
      }

      if (domain === "select" && st) {
        const options = st.attributes.options || [];
        let html = '<select data-eid="' + esc(entityId) + '"' + disabled + ">";
        for (let i = 0; i < options.length; i++) {
          const opt = options[i];
          const sel = st.state === opt ? " selected" : "";
          html +=
            '<option value="' +
            esc(opt) +
            '"' +
            sel +
            ">" +
            esc(opt) +
            "</option>";
        }
        html += "</select>";
        return html;
      }

      if (domain === "time" && st) {
        let val = available ? String(st.state) : "";
        if (/^\d{2}:\d{2}:\d{2}/.test(val)) val = val.slice(0, 5);
        return (
          '<input type="time" data-eid="' +
          esc(entityId) +
          '" value="' +
          esc(val) +
          '"' +
          disabled +
          " />"
        );
      }

      return (
        '<span class="zip-row-value' +
        (available ? "" : " muted") +
        '">' +
        esc(formatState(entityId, this._hass)) +
        "</span>"
      );
    }

    _renderSectionBar(title, ck, collapsed) {
      return (
        '<button type="button" class="zip-section-bar" data-ck="' + esc(ck) +
        '" aria-expanded="' + (collapsed ? "false" : "true") + '">' +
        '<span class="bar-title">' + esc(title) + "</span>" +
        '<span class="bar-toggle">' +
        (collapsed ? "SHOW" : "HIDE") +
        ' <span class="bar-chevron' + (collapsed ? "" : " open") + '">\u25BC</span>' +
        "</span></button>"
      );
    }

    _renderSettingsRow(entityId, label, st) {
      const domain = domainOf(entityId);
      let html = '<div class="zip-row">';
      html +=
        '<span class="zip-row-label" data-more-info="' + esc(entityId) + '">' +
        esc(label) + "</span>";
      html += '<div class="zip-row-control">';

      if (domain === "switch" || domain === "number" || domain === "select" || domain === "time") {
        html += this._renderControl(entityId, st);
      } else {
        html +=
          '<span class="zip-row-value">' +
          esc(formatState(entityId, this._hass)) +
          "</span>";
      }

      html +=
        '<button type="button" class="zip-more-info" data-more-info="' +
        esc(entityId) + '" title="More info" aria-label="More info">' +
        '<ha-icon icon="mdi:information-outline"></ha-icon></button>';
      html += "</div></div>";
      return html;
    }

    _renderDeviceInfo(ents, hass) {
      const sec = SECTIONS[0];
      let html = '<div class="device-info">';
      let hasAny = false;
      for (let ii = 0; ii < sec.e.length; ii++) {
        const key = sec.e[ii][0];
        const label = sec.e[ii][1];
        const eid = ents[key];
        if (!eid || !hass.states[eid]) continue;
        hasAny = true;
        const st = hass.states[eid];
        const available = stateAvailable(st);
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
    }

    _renderSettingsPanel(sec, ents, hass, deviceId) {
      const avail = [];
      for (let ii = 0; ii < sec.e.length; ii++) {
        const key = sec.e[ii][0];
        const label = sec.e[ii][1];
        const eid = ents[key];
        if (eid && hass.states[eid]) {
          avail.push({ id: eid, label: label, key: key });
        }
      }
      if (!avail.length) return "";

      const ck = deviceId + "||" + sec.t;
      const collapsed = !!this._collapsed[ck];

      let html = '<div class="zip-section">';
      html += this._renderSectionBar(sec.t, ck, collapsed);
      html += '<div class="zip-section-body' + (collapsed ? " collapsed" : "") + '">';
      for (let aj = 0; aj < avail.length; aj++) {
        const be = avail[aj];
        html += this._renderSettingsRow(be.id, be.label, hass.states[be.id]);
      }
      html += "</div></div>";
      return html;
    }

    _renderFiltersPanel(sec, ents, hass, deviceId) {
      const readouts = [];
      const internalLimits = [];
      const externalLimits = [];

      for (let ii = 0; ii < sec.e.length; ii++) {
        const key = sec.e[ii][0];
        const label = sec.e[ii][1];
        const eid = ents[key];
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

      const ck = deviceId + "||" + sec.t;
      const collapsed = !!this._collapsed[ck];

      let html = '<div class="zip-section">';
      html += this._renderSectionBar(sec.t, ck, collapsed);
      html += '<div class="zip-section-body' + (collapsed ? " collapsed" : "") + '">';
      html += '<div class="filters-body">';

      if (readouts.length) {
        html += '<div class="filters-readout">';
        for (let ri = 0; ri < readouts.length; ri++) {
          const r = readouts[ri];
          html +=
            '<div class="zip-row"><span class="zip-row-label" data-more-info="' +
            esc(r.id) + '">' + esc(r.label) + "</span>" +
            '<div class="zip-row-control">' +
            '<span class="zip-row-value">' + esc(formatState(r.id, hass)) + "</span>" +
            '<button type="button" class="zip-more-info" data-more-info="' +
            esc(r.id) + '" title="More info" aria-label="More info">' +
            '<ha-icon icon="mdi:information-outline"></ha-icon></button>' +
            "</div></div>";
        }
        html += "</div>";
      }

      if (internalLimits.length) {
        html += '<div class="filters-subgroup">';
        html += '<div class="filters-subgroup-title">Internal Filter Limits</div>';
        for (let ili = 0; ili < internalLimits.length; ili++) {
          const il = internalLimits[ili];
          html += this._renderSettingsRow(il.id, il.label.replace("Internal ", ""), hass.states[il.id]);
        }
        html += "</div>";
      }

      if (externalLimits.length) {
        html += '<div class="filters-subgroup">';
        html += '<div class="filters-subgroup-title">External Filter Limits</div>';
        for (let eli = 0; eli < externalLimits.length; eli++) {
          const el = externalLimits[eli];
          html += this._renderSettingsRow(el.id, el.label.replace("External ", ""), hass.states[el.id]);
        }
        html += "</div>";
      }

      html += "</div></div></div>";
      return html;
    }

    _renderTimersPanel(ents, hass, deviceId) {
      const energyModeEid = ents["energy_mode"];
      let hasAnyTimer = false;
      for (let mi = 0; mi < TIMER_MODES.length; mi++) {
        const groups = TIMER_MODES[mi].groups || [];
        for (let gi = 0; gi < groups.length; gi++) {
          const rows = groups[gi].rows || [];
          for (let ri = 0; ri < rows.length; ri++) {
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

      const ck = deviceId + "||ON/OFF TIMERS";
      const collapsed = !!this._collapsed[ck];

      let activeTab = this._activeTimerTab;
      if (!activeTab) {
        if (energyModeEid && hass.states[energyModeEid]) {
          const currentMode = hass.states[energyModeEid].state;
          for (let ti = 0; ti < TIMER_MODES.length; ti++) {
            if (currentMode === TIMER_MODES[ti].modeValue ||
                currentMode === TIMER_MODES[ti].label) {
              activeTab = String(ti);
              break;
            }
          }
        }
        if (!activeTab) activeTab = "0";
      }

      let html = '<div class="zip-section">';
      html += this._renderSectionBar("ON/OFF TIMERS", ck, collapsed);
      html += '<div class="zip-section-body' + (collapsed ? " collapsed" : "") + '">';
      html += '<div class="timers-body">';

      if (energyModeEid && hass.states[energyModeEid]) {
        html += '<div class="timers-mode-select">';
        html += '<label>Active Mode:</label>';
        html += this._renderControl(energyModeEid, hass.states[energyModeEid]);
        html += "</div>";
      }

      html += '<div class="timers-tabs">';
      for (let tbi = 0; tbi < TIMER_MODES.length; tbi++) {
        const isActive = (String(tbi) === activeTab);
        html +=
          '<button type="button" class="timers-tab' + (isActive ? " active" : "") +
          '" data-tab="' + tbi + '" role="tab" aria-selected="' + (isActive ? "true" : "false") + '">' +
          esc(TIMER_MODES[tbi].label) + "</button>";
      }
      html += "</div>";

      for (let tci = 0; tci < TIMER_MODES.length; tci++) {
        const isVisible = (String(tci) === activeTab);
        html += '<div class="timers-tab-content' + (isVisible ? "" : " hidden") + '" role="tabpanel">';

        const modeGroups = TIMER_MODES[tci].groups || [];
        for (let mgi = 0; mgi < modeGroups.length; mgi++) {
          const group = modeGroups[mgi];
          if (modeGroups.length > 1) {
            html += '<div class="timers-subgroup">';
            html += '<div class="timers-subgroup-title">' + esc(group.label) + "</div>";
          }

          for (let rowi = 0; rowi < group.rows.length; rowi++) {
            const row = group.rows[rowi];
            const eid = ents[row.key];
            if (!eid || !hass.states[eid]) continue;
            const st = hass.states[eid];
            html += '<div class="zip-row">';
            html +=
              '<span class="zip-row-label" data-more-info="' + esc(eid) + '">' +
              esc(row.label) + "</span>";
            html += '<div class="zip-row-control">';
            html += this._renderControl(eid, st);
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
    }

    _render() {
      const hass = this._hass;
      const config = this._config || {};

      if (!hass) {
        this._renderEmpty("Waiting for Home Assistant…");
        return;
      }

      let deviceId = config.device;
      // Allow optional friendly-name substring match for YAML users
      if (deviceId && hass.devices && !hass.devices[deviceId]) {
        const needle = String(deviceId).toLowerCase();
        const dids = Object.keys(hass.devices);
        for (let i = 0; i < dids.length; i++) {
          const d = hass.devices[dids[i]];
          const name = ((d && (d.name_by_user || d.name)) || "").toLowerCase();
          if (name && name.indexOf(needle) !== -1) {
            deviceId = dids[i];
            break;
          }
        }
      }

      // Auto-pick first ZipAssist device when config omitted device
      if (!deviceId) {
        deviceId = findZipAssistDeviceId(hass);
        if (deviceId && !config.device) {
          // Persist into local config so subsequent renders are stable
          this._config = Object.assign({}, config, { device: deviceId });
        }
      }

      if (!deviceId) {
        this._renderEmpty(
          "No HydroTap device found. Open the card editor and select a ZipAssist device."
        );
        return;
      }

      const ents = buildEntityMap(hass, deviceId);
      const sig = this._signature(deviceId, ents);
      if (sig === this._lastSignature) return;
      this._lastSignature = sig;

      if (!Object.keys(ents).length) {
        this._renderEmpty(
          "No entities found for this device yet. Check the integration loaded entities, then refresh the dashboard."
        );
        return;
      }

      const dev = (hass.devices && hass.devices[deviceId]) || {};
      const title = config.title || dev.name_by_user || dev.name || CARD_NAME;

      let html = "<style>" + STYLE + "</style><ha-card>";
      html +=
        '<div class="card-header"><ha-icon icon="mdi:water-pump"></ha-icon><span class="name">' +
        esc(title) +
        "</span></div>";

      for (let si = 0; si < SECTIONS.length; si++) {
        const sec = SECTIONS[si];
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
    }
  }

  // Define the element first so getCardElementClass / getStubConfig can resolve.
  if (!customElements.get(CARD_TYPE)) {
    customElements.define(CARD_TYPE, ZipAssistCard);
  }

  // Picker metadata: preview:false => static name/description tile (no live preview).
  // HA still awaits getStubConfig on the custom element class — keep that never-throwing.
  window.customCards = window.customCards || [];
  const cardInfo = {
    type: CARD_TYPE,
    name: CARD_NAME,
    description: CARD_DESCRIPTION,
    preview: false,
    documentationURL: DOC_URL,
  };
  let updated = false;
  for (let i = 0; i < window.customCards.length; i++) {
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
