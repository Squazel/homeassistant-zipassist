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

  const SECTIONS = [
    {
      t: "Info & Status",
      i: "mdi:information-outline",
      g: true,
      e: [
        ["status", "Status"],
        ["last_sync", "Last Sync"],
        ["serial_number", "Serial"],
        ["firmware_version", "Firmware"],
        ["wifi_signal_strength", "WiFi Signal"],
        ["system_fault", "Fault"],
        ["sleep_mode_status", "Sleep Mode"],
      ],
    },
    {
      t: "Filter Life",
      i: "mdi:air-filter",
      g: true,
      e: [
        ["filter_litres_remaining", "Filter (Litres)"],
        ["filter_days_remaining", "Filter (Days)"],
        ["filter_estimated_days", "Est. Days"],
      ],
    },
    {
      t: "Usage",
      i: "mdi:water-percent",
      g: true,
      e: [
        ["average_daily_usage", "Avg Daily"],
        ["peak_hourly_usage", "Peak Hourly"],
        ["energy_total", "Energy Total"],
        ["energy_since_last_log", "Since Last Log"],
      ],
    },
    {
      t: "Safety & Security",
      i: "mdi:shield-lock",
      e: [
        ["safety_lock", "Safety Lock"],
        ["hot_isolation", "Hot Isolation"],
        ["sync_period", "Sync Period"],
      ],
    },
    {
      t: "Temperature",
      i: "mdi:thermometer",
      e: [
        ["boiling_temp", "Boiling Temp"],
        ["chilled_temp", "Chilled Temp"],
      ],
    },
    {
      t: "Dispense Settings",
      i: "mdi:timer-outline",
      e: [
        ["boiling_duration", "Boiling"],
        ["chilled_duration", "Chilled"],
        ["sparkling_duration", "Sparkling"],
        ["ambient_duration", "Ambient"],
      ],
    },
    {
      t: "Filter Limits",
      i: "mdi:water-filter",
      e: [
        ["internal_filter_litres", "Int. Litres"],
        ["internal_filter_days", "Int. Days"],
        ["external_filter_litres", "Ext. Litres"],
        ["external_filter_days", "Ext. Days"],
      ],
    },
    {
      t: "On/Off Timers",
      i: "mdi:power-plug",
      e: (function () {
        const out = [["energy_mode", "Active Mode"]];
        out.push(
          ["energy_everyday_on_active", "Everyday — On"],
          ["energy_everyday_on_time", "Everyday — On Time"],
          ["energy_everyday_off_active", "Everyday — Off"],
          ["energy_everyday_off_time", "Everyday — Off Time"]
        );
        out.push(
          ["energy_weekday_on_active", "Wkday — On"],
          ["energy_weekday_on_time", "Wkday — On Time"],
          ["energy_weekday_off_active", "Wkday — Off"],
          ["energy_weekday_off_time", "Wkday — Off Time"]
        );
        out.push(
          ["energy_weekend_on_active", "Wkend — On"],
          ["energy_weekend_on_time", "Wkend — On Time"],
          ["energy_weekend_off_active", "Wkend — Off"],
          ["energy_weekend_off_time", "Wkend — Off Time"]
        );
        const days = [
          "mon",
          "Mon",
          "tue",
          "Tue",
          "wed",
          "Wed",
          "thu",
          "Thu",
          "fri",
          "Fri",
          "sat",
          "Sat",
          "sun",
          "Sun",
        ];
        for (let i = 0; i < days.length; i += 2) {
          out.push(
            ["energy_daily_" + days[i] + "_on_active", days[i + 1] + " — On"],
            ["energy_daily_" + days[i] + "_on_time", days[i + 1] + " — On Time"],
            ["energy_daily_" + days[i] + "_off_active", days[i + 1] + " — Off"],
            ["energy_daily_" + days[i] + "_off_time", days[i + 1] + " — Off Time"]
          );
        }
        return out;
      })(),
    },
    {
      t: "Sleep Mode",
      i: "mdi:sleep",
      e: [["sleep_mode", "Sleep Mode"]],
    },
  ];

  const STYLE = `
    :host {
      display: block;
    }
    ha-card {
      padding: 16px;
    }
    .header {
      display: flex;
      align-items: center;
      gap: 10px;
      padding-bottom: 12px;
      margin-bottom: 8px;
      border-bottom: 1px solid var(--divider-color);
    }
    .header .name {
      font-size: 1.2em;
      font-weight: 600;
      color: var(--primary-text-color);
      flex: 1;
    }
    .header ha-icon {
      color: var(--primary-color);
    }
    .section {
      margin-bottom: 14px;
    }
    .section:last-child {
      margin-bottom: 0;
    }
    .section-heading {
      display: flex;
      align-items: center;
      gap: 6px;
      width: 100%;
      margin: 0 0 6px;
      padding: 4px 0;
      border: none;
      background: transparent;
      font: inherit;
      font-size: 0.8em;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: var(--secondary-text-color);
      cursor: pointer;
      text-align: left;
    }
    .section-heading ha-icon {
      --mdc-icon-size: 16px;
    }
    .section-heading .chevron {
      margin-left: auto;
      transition: transform 0.2s;
      --mdc-icon-size: 14px;
    }
    .section-heading .chevron.open {
      transform: rotate(180deg);
    }
    .section-body.collapsed {
      display: none;
    }
    .info-tiles {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
      gap: 6px;
    }
    .info-tile {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 8px 10px;
      border-radius: 8px;
      background: var(--secondary-background-color, rgba(0, 0, 0, 0.02));
      border: 1px solid var(--divider-color);
      cursor: pointer;
    }
    .info-tile ha-icon {
      color: var(--primary-color);
      --mdc-icon-size: 20px;
    }
    .tile-value {
      font-size: 0.9em;
      font-weight: 500;
      color: var(--primary-text-color);
    }
    .tile-label {
      font-size: 0.7em;
      color: var(--secondary-text-color);
    }
    .entity-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      padding: 6px 0;
      min-height: 40px;
      border-bottom: 1px solid var(--divider-color);
    }
    .entity-row:last-child {
      border-bottom: none;
    }
    .entity-label {
      font-size: 0.85em;
      color: var(--primary-text-color);
      flex: 1;
      cursor: pointer;
      min-width: 0;
    }
    .entity-control {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-shrink: 0;
    }
    .entity-value {
      font-size: 0.85em;
      color: var(--primary-text-color);
      max-width: 12em;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .entity-value.muted {
      color: var(--secondary-text-color);
    }
    input[type="number"],
    input[type="time"],
    select {
      font: inherit;
      font-size: 0.85em;
      color: var(--primary-text-color);
      background: var(--card-background-color, var(--primary-background-color));
      border: 1px solid var(--divider-color);
      border-radius: 6px;
      padding: 4px 6px;
      max-width: 8.5em;
    }
    input[type="number"] {
      width: 5.5em;
    }
    input[type="time"] {
      width: 7em;
    }
    select {
      max-width: 11em;
    }
    ha-switch {
      --mdc-switch-checked-track-color: var(--primary-color);
    }
    .fallback-toggle {
      position: relative;
      display: inline-block;
      width: 44px;
      height: 24px;
      flex-shrink: 0;
    }
    .fallback-toggle input {
      opacity: 0;
      width: 0;
      height: 0;
    }
    .fallback-toggle .slider {
      position: absolute;
      cursor: pointer;
      inset: 0;
      background: #ccc;
      border-radius: 24px;
      transition: 0.2s;
    }
    .fallback-toggle .slider::before {
      content: "";
      position: absolute;
      height: 18px;
      width: 18px;
      left: 3px;
      bottom: 3px;
      background: #fff;
      border-radius: 50%;
      transition: 0.2s;
    }
    .fallback-toggle input:checked + .slider {
      background: var(--primary-color);
    }
    .fallback-toggle input:checked + .slider::before {
      transform: translateX(20px);
    }
    .no-data {
      text-align: center;
      color: var(--secondary-text-color);
      font-style: italic;
      padding: 20px;
    }
    .more-info-btn {
      border: none;
      background: transparent;
      color: var(--secondary-text-color);
      cursor: pointer;
      padding: 2px;
      display: inline-flex;
    }
    .more-info-btn ha-icon {
      --mdc-icon-size: 18px;
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

  function extractKey(uniqueId, entityId) {
    if (uniqueId) {
      // zipassist_<hydrotapId>_<key> — hydrotap id may be UUID or other id
      const m = String(uniqueId).match(/^zipassist_.+?_(.+)$/);
      if (m) return m[1];
    }
    return entityId;
  }

  function buildEntityMap(hass, deviceId) {
    const ents = {};
    const entities = (hass && hass.entities) || {};
    for (const eid of Object.keys(entities)) {
      const ereg = entities[eid];
      if (!ereg || ereg.device_id !== deviceId) continue;
      const platform = ereg.platform || ereg.integration;
      if (platform && platform !== "zipassist") continue;
      if (!platform) {
        const uid = ereg.unique_id || "";
        if (!String(uid).startsWith("zipassist_")) continue;
      }
      const key = extractKey(ereg.unique_id, eid);
      ents[key] = eid;
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
        if (el.classList && el.classList.contains("section-heading")) {
          const ck = el.getAttribute("data-ck");
          if (!ck) return;
          this._collapsed[ck] = !this._collapsed[ck];
          this._scheduleRender(true);
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
      if (domain === "switch") {
        const checked = !!t.checked;
        this._hass.callService("switch", checked ? "turn_on" : "turn_off", {
          entity_id: eid,
        });
        return;
      }
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
        '<div class="header"><ha-icon icon="mdi:water-pump"></ha-icon>' +
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
        if (customElements.get("ha-switch")) {
          return (
            '<ha-switch data-eid="' +
            esc(entityId) +
            '"' +
            (on ? " checked" : "") +
            disabled +
            "></ha-switch>"
          );
        }
        return (
          '<label class="fallback-toggle" data-eid="' +
          esc(entityId) +
          '"><input type="checkbox" data-eid="' +
          esc(entityId) +
          '"' +
          (on ? " checked" : "") +
          disabled +
          '><span class="slider"></span></label>'
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
          " />"
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
        '<span class="entity-value' +
        (available ? "" : " muted") +
        '">' +
        esc(formatState(entityId, this._hass)) +
        "</span>"
      );
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

      if (!deviceId) {
        this._renderEmpty("Select a HydroTap device in the card configuration.");
        return;
      }

      const ents = buildEntityMap(hass, deviceId);
      const sig = this._signature(deviceId, ents);
      if (sig === this._lastSignature) return;
      this._lastSignature = sig;

      if (!Object.keys(ents).length) {
        this._renderEmpty("No ZipAssist entities found for this device.");
        return;
      }

      const dev = (hass.devices && hass.devices[deviceId]) || {};
      const title = config.title || dev.name_by_user || dev.name || CARD_NAME;

      let html = "<style>" + STYLE + "</style><ha-card>";
      html +=
        '<div class="header"><ha-icon icon="mdi:water-pump"></ha-icon><span class="name">' +
        esc(title) +
        "</span></div>";

      for (let si = 0; si < SECTIONS.length; si++) {
        const sec = SECTIONS[si];
        const avail = [];
        for (let ii = 0; ii < sec.e.length; ii++) {
          const key = sec.e[ii][0];
          const label = sec.e[ii][1];
          const eid = ents[key];
          if (eid && hass.states[eid]) {
            avail.push({ id: eid, label: label, key: key });
          }
        }
        if (!avail.length) continue;

        const ck = deviceId + "||" + sec.t;
        const collapsed = !!this._collapsed[ck];

        html += '<div class="section">';
        html +=
          '<button type="button" class="section-heading" data-ck="' +
          esc(ck) +
          '" aria-expanded="' +
          (collapsed ? "false" : "true") +
          '">';
        html +=
          '<ha-icon icon="' +
          esc(sec.i || "mdi:circle") +
          '"></ha-icon><span>' +
          esc(sec.t) +
          "</span>";
        html +=
          '<ha-icon class="chevron' +
          (collapsed ? "" : " open") +
          '" icon="mdi:chevron-down"></ha-icon></button>';
        html +=
          '<div class="section-body' + (collapsed ? " collapsed" : "") + '">';

        if (sec.g) {
          html += '<div class="info-tiles">';
          for (let ai = 0; ai < avail.length; ai++) {
            const ae = avail[ai];
            const st = hass.states[ae.id] || {};
            const ico =
              (st.attributes && st.attributes.icon) || "mdi:circle-outline";
            html +=
              '<div class="info-tile" data-more-info="' +
              esc(ae.id) +
              '" title="More info">';
            html +=
              '<ha-icon icon="' +
              esc(ico) +
              '"></ha-icon><div><div class="tile-label">' +
              esc(ae.label) +
              '</div><div class="tile-value">' +
              esc(formatState(ae.id, hass)) +
              "</div></div></div>";
          }
          html += "</div>";
        } else {
          html += '<div class="entity-rows">';
          for (let aj = 0; aj < avail.length; aj++) {
            const be = avail[aj];
            const st = hass.states[be.id];
            const domain = domainOf(be.id);
            html += '<div class="entity-row">';
            html +=
              '<span class="entity-label" data-more-info="' +
              esc(be.id) +
              '">' +
              esc(be.label) +
              "</span>";
            html += '<div class="entity-control">';
            if (
              domain !== "switch" &&
              domain !== "number" &&
              domain !== "select" &&
              domain !== "time"
            ) {
              html +=
                '<span class="entity-value">' +
                esc(formatState(be.id, hass)) +
                "</span>";
            }
            html += this._renderControl(be.id, st);
            html +=
              '<button type="button" class="more-info-btn" data-more-info="' +
              esc(be.id) +
              '" title="More info" aria-label="More info"><ha-icon icon="mdi:information-outline"></ha-icon></button>';
            html += "</div></div>";
          }
          html += "</div>";
        }
        html += "</div></div>";
      }

      html += "</ha-card>";
      this._root.innerHTML = html;

      const switches = this._root.querySelectorAll("ha-switch[data-eid]");
      for (let s = 0; s < switches.length; s++) {
        const sw = switches[s];
        const eid = sw.getAttribute("data-eid");
        const st = hass.states[eid];
        sw.checked = !!(st && st.state === "on");
        sw.disabled = !stateAvailable(st);
      }
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
