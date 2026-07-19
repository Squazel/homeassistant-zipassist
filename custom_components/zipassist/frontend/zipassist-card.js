import {
  LitElement,
  html,
  css,
} from "https://unpkg.com/lit-element@2.4.0/lit-element.js?module";

// ─────────────────────────────────────────────────────────────────────────────
// Entity key definitions — all 70 entity keys across 6 platforms
// ─────────────────────────────────────────────────────────────────────────────

const SENSOR_KEYS = [
  "filter_litres_remaining", "filter_days_remaining", "filter_estimated_days",
  "average_daily_usage", "peak_hourly_usage", "last_sync", "status",
  "serial_number", "firmware_version", "system_fault_details",
  "wifi_signal_strength", "energy_since_last_log", "energy_total",
  "sleep_mode_status", "litres_filtered_internal", "litres_filtered_external",
  "days_filtered_internal", "days_filtered_external",
];

const NUMBER_KEYS = [
  "boiling_temp", "chilled_temp",
  "boiling_duration", "chilled_duration", "sparkling_duration", "ambient_duration",
  "internal_filter_litres", "internal_filter_days",
  "external_filter_litres", "external_filter_days",
];

const SWITCH_KEYS = [
  "safety_lock", "hot_isolation",
  ...["everyday", ...["mon","tue","wed","thu","fri","sat","sun"].flatMap(d =>
    [`daily_${d}`, `daily_${d}`])].flatMap(p => [`energy_${p}_on_active`, `energy_${p}_off_active`]),
  "energy_weekday_on_active","energy_weekday_off_active",
  "energy_weekend_on_active","energy_weekend_off_active",
];

const SELECT_KEYS = ["sleep_mode", "energy_mode", "sync_period"];

const TIME_KEYS = [
  "energy_everyday_on_time","energy_everyday_off_time",
  ...["mon","tue","wed","thu","fri","sat","sun"].flatMap(d =>
    [`energy_daily_${d}_on_time`, `energy_daily_${d}_off_time`]),
  "energy_weekday_on_time","energy_weekday_off_time",
  "energy_weekend_on_time","energy_weekend_off_time",
];

// ─────────────────────────────────────────────────────────────────────────────
// Section layout — mirrors the ZipAssist website's HydroTap detail page
// ─────────────────────────────────────────────────────────────────────────────

const SECTIONS = [
  {
    title: "Info & Status",
    icon: "mdi:information-outline",
    entities: [
      { key: "status", domain: "sensor", label: "Status" },
      { key: "last_sync", domain: "sensor", label: "Last Sync" },
      { key: "serial_number", domain: "sensor", label: "Serial" },
      { key: "firmware_version", domain: "sensor", label: "Firmware" },
      { key: "wifi_signal_strength", domain: "sensor", label: "WiFi Signal" },
      { key: "system_fault", domain: "binary_sensor", label: "Fault" },
      { key: "sleep_mode_status", domain: "sensor", label: "Sleep Mode" },
    ],
  },
  {
    title: "Filter Life",
    icon: "mdi:air-filter",
    entities: [
      { key: "filter_litres_remaining", domain: "sensor", label: "Filter (Litres)" },
      { key: "filter_days_remaining", domain: "sensor", label: "Filter (Days)" },
      { key: "filter_estimated_days", domain: "sensor", label: "Est. Days" },
    ],
  },
  {
    title: "Usage",
    icon: "mdi:water-percent",
    entities: [
      { key: "average_daily_usage", domain: "sensor", label: "Avg Daily" },
      { key: "peak_hourly_usage", domain: "sensor", label: "Peak Hourly" },
      { key: "energy_total", domain: "sensor", label: "Energy Total" },
      { key: "energy_since_last_log", domain: "sensor", label: "Since Last Log" },
    ],
  },
  {
    title: "Safety & Security",
    icon: "mdi:shield-lock",
    entities: [
      { key: "safety_lock", domain: "switch", label: "Safety Lock" },
      { key: "hot_isolation", domain: "switch", label: "Hot Isolation" },
      { key: "sync_period", domain: "select", label: "Sync Period" },
    ],
  },
  {
    title: "Temperature",
    icon: "mdi:thermometer",
    entities: [
      { key: "boiling_temp", domain: "number", label: "Boiling Temp" },
      { key: "chilled_temp", domain: "number", label: "Chilled Temp" },
    ],
  },
  {
    title: "Dispense Settings",
    icon: "mdi:timer-outline",
    entities: [
      { key: "boiling_duration", domain: "number", label: "Boiling" },
      { key: "chilled_duration", domain: "number", label: "Chilled" },
      { key: "sparkling_duration", domain: "number", label: "Sparkling" },
      { key: "ambient_duration", domain: "number", label: "Ambient" },
    ],
  },
  {
    title: "Filter Limits",
    icon: "mdi:water-filter",
    entities: [
      { key: "internal_filter_litres", domain: "number", label: "Int. Litres" },
      { key: "internal_filter_days", domain: "number", label: "Int. Days" },
      { key: "external_filter_litres", domain: "number", label: "Ext. Litres" },
      { key: "external_filter_days", domain: "number", label: "Ext. Days" },
    ],
  },
  {
    title: "On/Off Timers",
    icon: "mdi:power-plug",
    entities: [
      { key: "energy_mode", domain: "select", label: "Active Mode" },
      // Everyday
      { key: "energy_everyday_on_active", domain: "switch", label: "Everydy — On" },
      { key: "energy_everyday_on_time", domain: "time", label: "Everydy — On Time" },
      { key: "energy_everyday_off_active", domain: "switch", label: "Everydy — Off" },
      { key: "energy_everyday_off_time", domain: "time", label: "Everydy — Off Time" },
      // Weekday/Weekend
      { key: "energy_weekday_on_active", domain: "switch", label: "Wkday — On" },
      { key: "energy_weekday_on_time", domain: "time", label: "Wkday — On Time" },
      { key: "energy_weekday_off_active", domain: "switch", label: "Wkday — Off" },
      { key: "energy_weekday_off_time", domain: "time", label: "Wkday — Off Time" },
      { key: "energy_weekend_on_active", domain: "switch", label: "Wkend — On" },
      { key: "energy_weekend_on_time", domain: "time", label: "Wkend — On Time" },
      { key: "energy_weekend_off_active", domain: "switch", label: "Wkend — Off" },
      { key: "energy_weekend_off_time", domain: "time", label: "Wkend — Off Time" },
      // Daily
      ...["Mon","Tue","Wed","Thu","Fri","Sat","Sun"].flatMap((d,i) => {
        const day = ["mon","tue","wed","thu","fri","sat","sun"][i];
        return [
          { key: `energy_daily_${day}_on_active`, domain: "switch", label: `${d} — On` },
          { key: `energy_daily_${day}_on_time`, domain: "time", label: `${d} — On Time` },
          { key: `energy_daily_${day}_off_active`, domain: "switch", label: `${d} — Off` },
          { key: `energy_daily_${day}_off_time`, domain: "time", label: `${d} — Off Time` },
        ];
      }),
    ],
  },
  {
    title: "Sleep Mode",
    icon: "mdi:sleep",
    entities: [
      { key: "sleep_mode", domain: "select", label: "Sleep Mode" },
    ],
  },
];

// ─────────────────────────────────────────────────────────────────────────────
// Card
// ─────────────────────────────────────────────────────────────────────────────

class ZipAssistCard extends LitElement {
  static get properties() {
    return {
      hass: {},
      config: {},
    };
  }

  static get styles() {
    return css`
      :host {
        display: block;
      }

      .card {
        background: var(--ha-card-background, var(--card-background-color, #fff));
        border-radius: var(--ha-card-border-radius, 12px);
        box-shadow: var(--ha-card-box-shadow, 0 2px 2px 0 rgba(0,0,0,0.14));
        border: var(--ha-card-border-width, 1px) solid var(--ha-card-border-color, var(--divider-color, #e0e0e0));
        padding: 16px;
      }

      .card-header {
        display: flex;
        align-items: center;
        gap: 10px;
        padding-bottom: 12px;
        margin-bottom: 8px;
        border-bottom: 1px solid var(--divider-color, #e0e0e0);
        cursor: pointer;
        user-select: none;
      }
      .card-header .name {
        font-size: 1.2em;
        font-weight: 600;
        color: var(--primary-text-color);
        flex: 1;
      }
      .card-header .chevron {
        transition: transform 0.2s;
        color: var(--secondary-text-color);
      }
      .card-header .chevron.open {
        transform: rotate(180deg);
      }
      .card-header ha-icon {
        color: var(--primary-color, #03a9f4);
      }

      /* ── sections ── */
      .sections.collapsed {
        display: none;
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
        margin-bottom: 6px;
        font-size: 0.8em;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: var(--secondary-text-color);
        cursor: pointer;
        user-select: none;
      }
      .section-heading ha-icon {
        color: var(--secondary-text-color);
        --mdc-icon-size: 16px;
      }
      .section-heading .s-chevron {
        margin-left: auto;
        transition: transform 0.2s;
        --mdc-icon-size: 14px;
      }
      .section-heading .s-chevron.open {
        transform: rotate(180deg);
      }

      .section-body.collapsed {
        display: none;
      }

      /* ── entity rows ── */
      .entity-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 4px 0;
        min-height: 36px;
        border-bottom: 1px solid var(--divider-color, rgba(0,0,0,0.06));
      }
      .entity-row:last-child {
        border-bottom: none;
      }
      .entity-label {
        font-size: 0.85em;
        color: var(--primary-text-color);
        flex: 1;
      }
      .entity-control {
        display: flex;
        align-items: center;
        gap: 4px;
      }

      /* ── compact tiles in top sections ── */
      .info-tiles {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
        gap: 8px;
      }
      .info-tile {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 8px 10px;
        border-radius: 8px;
        background: var(--card-background-color, rgba(0,0,0,0.02));
        border: 1px solid var(--divider-color, rgba(0,0,0,0.06));
      }
      .info-tile ha-icon {
        color: var(--primary-color, #03a9f4);
      }
      .info-tile .tile-value {
        font-size: 0.9em;
        font-weight: 500;
        color: var(--primary-text-color);
      }
      .info-tile .tile-label {
        font-size: 0.7em;
        color: var(--secondary-text-color);
      }

      /* ── toggle switch styling ── */
      .toggle {
        position: relative;
        display: inline-block;
        width: 44px;
        height: 24px;
        flex-shrink: 0;
      }
      .toggle input {
        opacity: 0;
        width: 0;
        height: 0;
      }
      .toggle .slider {
        position: absolute;
        cursor: pointer;
        top: 0; left: 0; right: 0; bottom: 0;
        background: #ccc;
        border-radius: 24px;
        transition: 0.3s;
      }
      .toggle .slider::before {
        content: "";
        position: absolute;
        height: 18px;
        width: 18px;
        left: 3px;
        bottom: 3px;
        background: white;
        border-radius: 50%;
        transition: 0.3s;
      }
      .toggle input:checked + .slider {
        background: var(--primary-color, #03a9f4);
      }
      .toggle input:checked + .slider::before {
        transform: translateX(20px);
      }

      /* ── no data ── */
      .no-data {
        text-align: center;
        color: var(--secondary-text-color);
        font-style: italic;
        padding: 20px;
      }

      /* ── HA entity-row compatibility ── */
      .entity-control ha-switch,
      .entity-control ha-select,
      .entity-control ha-time-input,
      .entity-control ha-entity-toggle {
        --mdc-icon-size: 20px;
      }
    `;
  }

  setConfig(config) {
    this.config = {
      device: config.device || null,   // optional device_id filter
      title: config.title || "",
      collapsed: config.collapsed !== undefined ? config.collapsed : false,
      ...config,
    };
  }

  /* ── entity discovery ── */
  _findZipAssistEntities() {
    const allIds = Object.keys(this.hass.states);
    return allIds.filter(id => id.startsWith("sensor.") && id.includes("zipassist")
      || id.startsWith("switch.") && id.includes("zipassist")
      || id.startsWith("number.") && id.includes("zipassist")
      || id.startsWith("select.") && id.includes("zipassist")
      || id.startsWith("time.") && id.includes("zipassist")
      || id.startsWith("binary_sensor.") && id.includes("zipassist")
    );
  }

  _groupEntitiesByDevice(ids) {
    // Group by device name from attributes
    const groups = {};
    for (const eid of ids) {
      const state = this.hass.states[eid];
      const dName = state?.attributes?.device?.name || "Unknown";
      if (!groups[dName]) groups[dName] = {};
      // Extract entity key from unique_id
      const uid = state?.attributes?.unique_id || "";
      const keyMatch = uid.match(/^zipassist_[a-f0-9-]{36}_(.+)$/);
      const key = keyMatch ? keyMatch[1] : eid;
      if (!groups[dName][key]) groups[dName][key] = eid;
    }
    return groups;
  }

  _getEntityId(key, deviceEntities) {
    // Look up in the device's entity map
    return deviceEntities[key] || null;
  }

  /* ── HA service calls for toggles ── */
  _callService(domain, service, entityId, data) {
    this.hass.callService(domain, service, {
      entity_id: entityId,
      ...data,
    });
  }

  _renderToggle(entityId, state) {
    const isOn = state === "on" || state === true;
    return html`
      <label class="toggle">
        <input type="checkbox" .checked=${isOn}
          @change=${(e) => {
            const svc = isOn ? "turn_off" : "turn_on";
            this._callService("switch", svc, entityId);
          }} />
        <span class="slider"></span>
      </label>
    `;
  }

  _renderValue(entityId, domain) {
    const state = this.hass.states[entityId];
    if (!state) return html`<span class="tile-value">—</span>`;
    const raw = state.state;
    if (raw === "unavailable" || raw === "unknown") return html`<span class="tile-value">—</span>`;

    // Format numbers nicely
    if (domain === "sensor") {
      const num = parseFloat(raw);
      if (!isNaN(num)) {
        const unit = state.attributes?.unit_of_measurement || "";
        return html`<span class="tile-value">${Math.round(num * 100) / 100} ${unit}</span>`;
      }
      return html`<span class="tile-value">${raw}</span>`;
    }
    if (domain === "switch" || domain === "binary_sensor") {
      return html`<span class="tile-value">${raw === "on" ? "On" : "Off"}</span>`;
    }
    if (domain === "number" || domain === "time" || domain === "select") {
      return html`<span class="tile-value">${raw} ${state.attributes?.unit_of_measurement || ""}</span>`;
    }
    return html`<span class="tile-value">${raw}</span>`;
  }

  /* ── render ── */
  render() {
    if (!this.hass || !this.config) return html`<div>Loading...</div>`;

    const allIds = this._findZipAssistEntities();
    if (allIds.length === 0) {
      return html`
        <div class="card">
          <div class="no-data">
            No ZipAssist entities found. Set up the ZipAssist CMMS integration first.
          </div>
        </div>`;
    }

    const deviceGroups = this._groupEntitiesByDevice(allIds);
    const deviceNames = Object.keys(deviceGroups).sort();

    // Filter by device if configured
    const filteredDevices = this.config.device
      ? deviceNames.filter(n => n === this.config.device || n.toLowerCase().includes(this.config.device.toLowerCase()))
      : deviceNames;

    if (filteredDevices.length === 0) {
      return html`
        <div class="card">
          <div class="no-data">Device "${this.config.device}" not found.</div>
        </div>`;
    }

    return html`
      ${filteredDevices.map(dName => {
        const entities = deviceGroups[dName];
        const title = this.config.title || dName;
        const collapsed = this.config.collapsed;

        return html`
          <div class="card">
            <div class="card-header" @click=${() => { this.config.collapsed = !this.config.collapsed; this.requestUpdate(); }}>
              <ha-icon icon="mdi:water-pump"></ha-icon>
              <span class="name">${title}</span>
              <ha-icon class="chevron ${collapsed ? '' : 'open'}" icon="mdi:chevron-down"></ha-icon>
            </div>

            <div class="sections ${collapsed ? 'collapsed' : ''}">
              ${SECTIONS.map(section => this._renderSection(section, entities, dName))}
            </div>
          </div>
        `;
      })}
    `;
  }

  _renderSection(section, entities, deviceName) {
    // Filter to entities that exist for this device
    const available = section.entities
      .map(e => ({ ...e, entityId: this._getEntityId(e.key, entities) }))
      .filter(e => e.entityId !== null && this.hass.states[e.entityId] !== undefined);

    if (available.length === 0) return html``;

    // Determine if this is a "tile" section (Info/Filter/Usage) or a "control" section
    const isTileSection = ["Info & Status", "Filter Life", "Usage"].includes(section.title);

    // For tile sections, use info-tiles grid; for control sections, use entity rows
    const body = isTileSection
      ? html`<div class="info-tiles">
          ${available.map(e => {
            const state = this.hass.states[e.entityId];
            return html`
              <div class="info-tile">
                <ha-icon .icon=${state?.attributes?.icon || "mdi:circle"}></ha-icon>
                <div>
                  <div class="tile-label">${e.label}</div>
                  ${this._renderValue(e.entityId, e.domain)}
                </div>
              </div>`;
          })}
        </div>`
      : html`${available.map(e => {
          const state = this.hass.states[e.entityId];
          const domain = e.domain;
          return html`
            <div class="entity-row">
              <span class="entity-label">${e.label}</span>
              <div class="entity-control">
                ${this._renderValue(e.entityId, domain)}
                ${domain === "switch" ? this._renderToggle(e.entityId, state?.state) : ''}
              </div>
            </div>`;
        })}`;

    // Track collapse per section + device
    const collapseKey = `${deviceName}||${section.title}`;
    if (!this._sectionCollapse) this._sectionCollapse = {};
    const isCollapsed = this._sectionCollapse[collapseKey] || false;

    return html`
      <div class="section">
        <div class="section-heading" @click=${() => {
          this._sectionCollapse[collapseKey] = !this._sectionCollapse[collapseKey];
          this.requestUpdate();
        }}>
          <ha-icon icon="${section.icon || 'mdi:circle'}"></ha-icon>
          <span>${section.title}</span>
          <ha-icon class="s-chevron ${isCollapsed ? '' : 'open'}" icon="mdi:chevron-down"></ha-icon>
        </div>
        <div class="section-body ${isCollapsed ? 'collapsed' : ''}">
          ${body}
        </div>
      </div>`;
  }

  getCardSize() {
    return 6;  // Large card
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Registration
// ─────────────────────────────────────────────────────────────────────────────

customElements.define("zipassist-card", ZipAssistCard);

console.info(
  "%c  ZIPASSIST-CARD  %c  Loaded automatically with integration  ",
  "color: orange; font-weight: bold; background: black",
  "color: white; font-weight: bold; background: dimgray"
);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "zipassist-card",
  name: "ZipAssist HydroTap",
  description: "ZipAssist CMMS HydroTap monitoring & control card (auto-loaded with integration)",
  preview: true,
});
