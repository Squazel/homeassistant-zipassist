(function () {
  "use strict";

  // ────────────────────────────────────────────────────────────────────
  // Sections — mirrors the ZipAssist website's HydroTap detail page
  // ────────────────────────────────────────────────────────────────────

  var SECTIONS = [
    { title: "Info & Status", icon: "mdi:information-outline", tile: true, items: [
      { k: "status", l: "Status" }, { k: "last_sync", l: "Last Sync" }, { k: "serial_number", l: "Serial" },
      { k: "firmware_version", l: "Firmware" }, { k: "wifi_signal_strength", l: "WiFi Signal" },
      { k: "system_fault", l: "Fault" }, { k: "sleep_mode_status", l: "Sleep Mode" },
    ]},
    { title: "Filter Life", icon: "mdi:air-filter", tile: true, items: [
      { k: "filter_litres_remaining", l: "Filter (Litres)" }, { k: "filter_days_remaining", l: "Filter (Days)" },
      { k: "filter_estimated_days", l: "Est. Days" },
    ]},
    { title: "Usage", icon: "mdi:water-percent", tile: true, items: [
      { k: "average_daily_usage", l: "Avg Daily" }, { k: "peak_hourly_usage", l: "Peak Hourly" },
      { k: "energy_total", l: "Energy Total" }, { k: "energy_since_last_log", l: "Since Last Log" },
    ]},
    { title: "Safety & Security", icon: "mdi:shield-lock", items: [
      { k: "safety_lock", l: "Safety Lock" }, { k: "hot_isolation", l: "Hot Isolation" }, { k: "sync_period", l: "Sync Period" },
    ]},
    { title: "Temperature", icon: "mdi:thermometer", items: [
      { k: "boiling_temp", l: "Boiling Temp" }, { k: "chilled_temp", l: "Chilled Temp" },
    ]},
    { title: "Dispense Settings", icon: "mdi:timer-outline", items: [
      { k: "boiling_duration", l: "Boiling" }, { k: "chilled_duration", l: "Chilled" },
      { k: "sparkling_duration", l: "Sparkling" }, { k: "ambient_duration", l: "Ambient" },
    ]},
    { title: "Filter Limits", icon: "mdi:water-filter", items: [
      { k: "internal_filter_litres", l: "Int. Litres" }, { k: "internal_filter_days", l: "Int. Days" },
      { k: "external_filter_litres", l: "Ext. Litres" }, { k: "external_filter_days", l: "Ext. Days" },
    ]},
    { title: "On/Off Timers", icon: "mdi:power-plug", items: [
      { k: "energy_mode", l: "Active Mode" },
      { k: "energy_everyday_on_active", l: "Everyday — On" }, { k: "energy_everyday_on_time", l: "Everyday — On Time" },
      { k: "energy_everyday_off_active", l: "Everyday — Off" }, { k: "energy_everyday_off_time", l: "Everyday — Off Time" },
      { k: "energy_weekday_on_active", l: "Wkday — On" }, { k: "energy_weekday_on_time", l: "Wkday — On Time" },
      { k: "energy_weekday_off_active", l: "Wkday — Off" }, { k: "energy_weekday_off_time", l: "Wkday — Off Time" },
      { k: "energy_weekend_on_active", l: "Wkend — On" }, { k: "energy_weekend_on_time", l: "Wkend — On Time" },
      { k: "energy_weekend_off_active", l: "Wkend — Off" }, { k: "energy_weekend_off_time", l: "Wkend — Off Time" },
      // Daily mon–sun
      { k: "energy_daily_mon_on_active", l: "Mon — On" }, { k: "energy_daily_mon_on_time", l: "Mon — On Time" },
      { k: "energy_daily_mon_off_active", l: "Mon — Off" }, { k: "energy_daily_mon_off_time", l: "Mon — Off Time" },
      { k: "energy_daily_tue_on_active", l: "Tue — On" }, { k: "energy_daily_tue_on_time", l: "Tue — On Time" },
      { k: "energy_daily_tue_off_active", l: "Tue — Off" }, { k: "energy_daily_tue_off_time", l: "Tue — Off Time" },
      { k: "energy_daily_wed_on_active", l: "Wed — On" }, { k: "energy_daily_wed_on_time", l: "Wed — On Time" },
      { k: "energy_daily_wed_off_active", l: "Wed — Off" }, { k: "energy_daily_wed_off_time", l: "Wed — Off Time" },
      { k: "energy_daily_thu_on_active", l: "Thu — On" }, { k: "energy_daily_thu_on_time", l: "Thu — On Time" },
      { k: "energy_daily_thu_off_active", l: "Thu — Off" }, { k: "energy_daily_thu_off_time", l: "Thu — Off Time" },
      { k: "energy_daily_fri_on_active", l: "Fri — On" }, { k: "energy_daily_fri_on_time", l: "Fri — On Time" },
      { k: "energy_daily_fri_off_active", l: "Fri — Off" }, { k: "energy_daily_fri_off_time", l: "Fri — Off Time" },
      { k: "energy_daily_sat_on_active", l: "Sat — On" }, { k: "energy_daily_sat_on_time", l: "Sat — On Time" },
      { k: "energy_daily_sat_off_active", l: "Sat — Off" }, { k: "energy_daily_sat_off_time", l: "Sat — Off Time" },
      { k: "energy_daily_sun_on_active", l: "Sun — On" }, { k: "energy_daily_sun_on_time", l: "Sun — On Time" },
      { k: "energy_daily_sun_off_active", l: "Sun — Off" }, { k: "energy_daily_sun_off_time", l: "Sun — Off Time" },
    ]},
    { title: "Sleep Mode", icon: "mdi:sleep", items: [{ k: "sleep_mode", l: "Sleep Mode" }]},
  ];

  // ────────────────────────────────────────────────────────────────────
  // Helpers
  // ────────────────────────────────────────────────────────────────────

  function findIds(hass) {
    var ks = Object.keys(hass.states), out = [];
    for (var i = 0; i < ks.length; i++) {
      var id = ks[i];
      if (id.indexOf("zipassist") === -1) continue;
      var dot = id.indexOf(".");
      if (dot === -1) continue;
      var d = id.substring(0, dot);
      if (d === "sensor" || d === "switch" || d === "number" || d === "select" || d === "time" || d === "binary_sensor")
        out.push(id);
    }
    return out;
  }

  function groupByDevice(ids, hass) {
    var g = {};
    for (var i = 0; i < ids.length; i++) {
      var eid = ids[i], st = hass.states[eid];
      var dn = ((st && st.attributes && st.attributes.device) || {}).name || "Unknown";
      if (!g[dn]) g[dn] = {};
      var uid = (st && st.attributes && st.attributes.unique_id) || "";
      var m = uid.match(/^zipassist_[a-f0-9-]{36}_(.+)$/);
      var key = m ? m[1] : eid;
      if (!g[dn][key]) g[dn][key] = eid;
    }
    return g;
  }

  function fmtVal(eid, hass) {
    var st = hass.states[eid];
    if (!st || st.state === "unavailable" || st.state === "unknown") return "—";
    var raw = st.state, num = parseFloat(raw);
    if (!isNaN(num)) {
      var u = (st.attributes && st.attributes.unit_of_measurement) || "";
      return Math.round(num * 100) / 100 + (u ? " " + u : "");
    }
    return raw === "on" ? "On" : raw === "off" ? "Off" : raw;
  }

  function esc(s) { return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;"); }

  // ────────────────────────────────────────────────────────────────────
  // Card
  // ────────────────────────────────────────────────────────────────────

  var ZipAssistCard = function () {
    var el = document.createElement("div");
    el.innerHTML = "<div class='card'><div class='no-data'>Loading...</div></div>";
    return Reflect.construct(HTMLElement, [], ZipAssistCard);
  };
  ZipAssistCard.prototype = Object.create(HTMLElement.prototype);
  ZipAssistCard.prototype.constructor = ZipAssistCard;

  Object.defineProperty(ZipAssistCard.prototype, "hass", {
    set: function (h) {
      this._hass = h;
      if (this._config) this._render();
    },
  });

  ZipAssistCard.prototype.setConfig = function (config) {
    this._config = config || {};
    this._render();
  };

  ZipAssistCard.prototype.getCardSize = function () { return 8; };

  ZipAssistCard.prototype._render = function () {
    var hass = this._hass, config = this._config;
    if (!hass || !config) return;

    var ids = findIds(hass);
    if (ids.length === 0) {
      this.innerHTML = '<div class="card"><div class="no-data">No ZipAssist entities found. Set up the ZipAssist CMMS integration first.</div></div>';
      return;
    }

    var groups = groupByDevice(ids, hass);
    var names = Object.keys(groups).sort();

    if (config.device) {
      var dv = config.device.toLowerCase();
      names = names.filter(function (n) { return n === config.device || n.toLowerCase().indexOf(dv) !== -1; });
    }

    var html = '';
    for (var di = 0; di < names.length; di++) {
      var dName = names[di], ents = groups[dName], title = config.title || dName;
      html += '<div class="card">';
      html += '<div class="card-header"><ha-icon icon="mdi:water-pump"></ha-icon><span class="name">' + esc(title) + '</span></div>';

      for (var si = 0; si < SECTIONS.length; si++) {
        var sec = SECTIONS[si];
        var avail = [];
        for (var ii = 0; ii < sec.items.length; ii++) {
          var item = sec.items[ii], eid = ents[item.k];
          if (eid && hass.states[eid]) avail.push({ id: eid, label: item.l, key: item.k });
        }
        if (!avail.length) continue;

        var ck = dName + "||" + sec.title;
        var sc = (this._sc || {})[ck] || false;

        html += '<div class="section">';
        html += '<div class="section-heading" data-ck="' + esc(ck) + '">';
        html += '<ha-icon icon="' + (sec.icon || "mdi:circle") + '"></ha-icon>';
        html += '<span>' + esc(sec.title) + '</span>';
        html += '<ha-icon class="s-chevron' + (sc ? '' : ' open') + '" icon="mdi:chevron-down"></ha-icon>';
        html += '</div>';
        html += '<div class="section-body' + (sc ? ' collapsed' : '') + '">';

        if (sec.tile) {
          html += '<div class="info-tiles">';
          for (var ai = 0; ai < avail.length; ai++) {
            var ae = avail[ai];
            var ico = ((hass.states[ae.id] || {}).attributes || {}).icon || "mdi:circle";
            html += '<div class="info-tile"><ha-icon icon="' + ico + '"></ha-icon>';
            html += '<div><div class="tile-label">' + esc(ae.label) + '</div>';
            html += '<div class="tile-value">' + esc(fmtVal(ae.id, hass)) + '</div></div></div>';
          }
          html += '</div>';
        } else {
          html += '<div class="entity-rows">';
          for (var aj = 0; aj < avail.length; aj++) {
            var be = avail[aj], st2 = hass.states[be.id];
            var sw = be.id.indexOf("switch.") === 0, on = st2 && st2.state === "on";
            html += '<div class="entity-row">';
            html += '<span class="entity-label">' + esc(be.label) + '</span>';
            html += '<div class="entity-control">';
            html += '<span class="entity-value">' + esc(fmtVal(be.id, hass)) + '</span>';
            if (sw) {
              html += '<label class="toggle" data-eid="' + esc(be.id) + '">';
              html += '<input type="checkbox"' + (on ? ' checked' : '') + '><span class="slider"></span></label>';
            }
            html += '</div></div>';
          }
          html += '</div>';
        }
        html += '</div></div>';
      }
      html += '</div>';
    }

    this.innerHTML = html;

    // Wire events
    var self = this;
    var togs = this.querySelectorAll(".toggle");
    for (var ti = 0; ti < togs.length; ti++) {
      togs[ti].addEventListener("change", function () {
        var eid = this.getAttribute("data-eid");
        var svc = this.querySelector("input").checked ? "turn_on" : "turn_off";
        hass.callService("switch", svc, { entity_id: eid });
      });
    }
    var heads = this.querySelectorAll("[data-ck]");
    for (var hi = 0; hi < heads.length; hi++) {
      heads[hi].addEventListener("click", function () {
        var k = this.getAttribute("data-ck");
        if (!self._sc) self._sc = {};
        self._sc[k] = !self._sc[k];
        self._render();
      });
    }
  };

  // ────────────────────────────────────────────────────────────────────
  // Styles
  // ────────────────────────────────────────────────────────────────────

  var styleEl = document.createElement("style");
  styleEl.textContent = [
    "zipassist-card{display:block}",
    "zipassist-card .card{background:var(--ha-card-background,var(--card-background-color,#fff));border-radius:var(--ha-card-border-radius,12px);box-shadow:var(--ha-card-box-shadow,0 2px 2px 0 rgba(0,0,0,.14));border:var(--ha-card-border-width,1px) solid var(--ha-card-border-color,var(--divider-color,#e0e0e0));padding:16px}",
    "zipassist-card .card-header{display:flex;align-items:center;gap:10px;padding-bottom:12px;margin-bottom:8px;border-bottom:1px solid var(--divider-color,#e0e0e0)}",
    "zipassist-card .card-header .name{font-size:1.2em;font-weight:600;color:var(--primary-text-color);flex:1}",
    "zipassist-card .card-header ha-icon{color:var(--primary-color,#03a9f4)}",
    "zipassist-card .section{margin-bottom:14px}",
    "zipassist-card .section:last-child{margin-bottom:0}",
    "zipassist-card .section-heading{display:flex;align-items:center;gap:6px;margin-bottom:6px;font-size:.8em;font-weight:600;text-transform:uppercase;letter-spacing:.5px;color:var(--secondary-text-color);cursor:pointer;user-select:none}",
    "zipassist-card .section-heading ha-icon{color:var(--secondary-text-color);--mdc-icon-size:16px}",
    "zipassist-card .section-heading .s-chevron{margin-left:auto;transition:transform .2s;--mdc-icon-size:14px}",
    "zipassist-card .section-heading .s-chevron.open{transform:rotate(180deg)}",
    "zipassist-card .section-body.collapsed{display:none}",
    "zipassist-card .info-tiles{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:8px}",
    "zipassist-card .info-tile{display:flex;align-items:center;gap:8px;padding:8px 10px;border-radius:8px;background:var(--card-background-color,rgba(0,0,0,.02));border:1px solid var(--divider-color,rgba(0,0,0,.06))}",
    "zipassist-card .info-tile ha-icon{color:var(--primary-color,#03a9f4)}",
    "zipassist-card .info-tile .tile-value{font-size:.9em;font-weight:500;color:var(--primary-text-color)}",
    "zipassist-card .info-tile .tile-label{font-size:.7em;color:var(--secondary-text-color)}",
    "zipassist-card .entity-row{display:flex;align-items:center;justify-content:space-between;padding:4px 0;min-height:36px;border-bottom:1px solid var(--divider-color,rgba(0,0,0,.06))}",
    "zipassist-card .entity-row:last-child{border-bottom:none}",
    "zipassist-card .entity-label{font-size:.85em;color:var(--primary-text-color);flex:1}",
    "zipassist-card .entity-control{display:flex;align-items:center;gap:8px}",
    "zipassist-card .entity-value{font-size:.85em;color:var(--primary-text-color)}",
    "zipassist-card .toggle{position:relative;display:inline-block;width:44px;height:24px;flex-shrink:0}",
    "zipassist-card .toggle input{opacity:0;width:0;height:0}",
    "zipassist-card .toggle .slider{position:absolute;cursor:pointer;top:0;left:0;right:0;bottom:0;background:#ccc;border-radius:24px;transition:.3s}",
    "zipassist-card .toggle .slider::before{content:'';position:absolute;height:18px;width:18px;left:3px;bottom:3px;background:#fff;border-radius:50%;transition:.3s}",
    "zipassist-card .toggle input:checked+.slider{background:var(--primary-color,#03a9f4)}",
    "zipassist-card .toggle input:checked+.slider::before{transform:translateX(20px)}",
    "zipassist-card .no-data{text-align:center;color:var(--secondary-text-color);font-style:italic;padding:20px}",
  ].join("\n");
  document.head.appendChild(styleEl);

  // ────────────────────────────────────────────────────────────────────
  // Registration
  // ────────────────────────────────────────────────────────────────────

  customElements.define("zipassist-card", ZipAssistCard);

  console.info("%c ZIPASSIST-CARD %c Loaded automatically ",
    "color:orange;font-weight:bold;background:black",
    "color:white;font-weight:bold;background:dimgray");

  window.customCards = window.customCards || [];
  window.customCards.push({
    type: "custom:zipassist-card",
    name: "ZipAssist HydroTap",
    description: "ZipAssist CMMS HydroTap monitoring & control card",
    preview: true,
  });
})();
