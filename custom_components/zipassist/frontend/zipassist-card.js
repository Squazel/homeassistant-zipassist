(function () {
  "use strict";

  var SECTIONS = [
    { t: "Info & Status", i: "mdi:information-outline", g: 1, e: [
      ["status","Status"],["last_sync","Last Sync"],["serial_number","Serial"],
      ["firmware_version","Firmware"],["wifi_signal_strength","WiFi Signal"],
      ["system_fault","Fault"],["sleep_mode_status","Sleep Mode"]]},
    { t: "Filter Life", i: "mdi:air-filter", g: 1, e: [
      ["filter_litres_remaining","Filter (Litres)"],["filter_days_remaining","Filter (Days)"],
      ["filter_estimated_days","Est. Days"]]},
    { t: "Usage", i: "mdi:water-percent", g: 1, e: [
      ["average_daily_usage","Avg Daily"],["peak_hourly_usage","Peak Hourly"],
      ["energy_total","Energy Total"],["energy_since_last_log","Since Last Log"]]},
    { t: "Safety & Security", i: "mdi:shield-lock", e: [
      ["safety_lock","Safety Lock"],["hot_isolation","Hot Isolation"],["sync_period","Sync Period"]]},
    { t: "Temperature", i: "mdi:thermometer", e: [
      ["boiling_temp","Boiling Temp"],["chilled_temp","Chilled Temp"]]},
    { t: "Dispense Settings", i: "mdi:timer-outline", e: [
      ["boiling_duration","Boiling"],["chilled_duration","Chilled"],
      ["sparkling_duration","Sparkling"],["ambient_duration","Ambient"]]},
    { t: "Filter Limits", i: "mdi:water-filter", e: [
      ["internal_filter_litres","Int. Litres"],["internal_filter_days","Int. Days"],
      ["external_filter_litres","Ext. Litres"],["external_filter_days","Ext. Days"]]},
    { t: "On/Off Timers", i: "mdi:power-plug", e: (function () {
      var out = [["energy_mode","Active Mode"]];
      out.push(["energy_everyday_on_active","Everyday — On"],["energy_everyday_on_time","Everyday — On Time"],
               ["energy_everyday_off_active","Everyday — Off"],["energy_everyday_off_time","Everyday — Off Time"]);
      out.push(["energy_weekday_on_active","Wkday — On"],["energy_weekday_on_time","Wkday — On Time"],
               ["energy_weekday_off_active","Wkday — Off"],["energy_weekday_off_time","Wkday — Off Time"]);
      out.push(["energy_weekend_on_active","Wkend — On"],["energy_weekend_on_time","Wkend — On Time"],
               ["energy_weekend_off_active","Wkend — Off"],["energy_weekend_off_time","Wkend — Off Time"]);
      var days = ["mon","Mon","tue","Tue","wed","Wed","thu","Thu","fri","Fri","sat","Sat","sun","Sun"];
      for (var i = 0; i < days.length; i += 2)
        out.push(["energy_daily_"+days[i]+"_on_active",days[i+1]+" — On"],
                 ["energy_daily_"+days[i]+"_on_time",days[i+1]+" — On Time"],
                 ["energy_daily_"+days[i]+"_off_active",days[i+1]+" — Off"],
                 ["energy_daily_"+days[i]+"_off_time",days[i+1]+" — Off Time"]);
      return out;
    })()},
    { t: "Sleep Mode", i: "mdi:sleep", e: [["sleep_mode","Sleep Mode"]]},
  ];

  function findIds(h) {
    var out = [], ks = Object.keys(h.states), doms = {sensor:1,switch:1,number:1,"select":1,time:1,binary_sensor:1};
    for (var i = 0; i < ks.length; i++) {
      var id = ks[i], dot = id.indexOf(".");
      if (dot < 0 || !doms[id.substring(0, dot)]) continue;
      var st = h.states[id];
      var uid = (st && st.attributes && st.attributes.unique_id) || "";
      if (uid.indexOf("zipassist_") === 0) out.push(id);
    }
    return out;
  }

  function groupByDevice(ids, h) {
    var g = {};
    for (var i = 0; i < ids.length; i++) {
      var eid = ids[i], st = h.states[eid];
      var dn = ((st && st.attributes && st.attributes.device) || {}).name || "Unknown";
      if (!g[dn]) g[dn] = {};
      var uid = (st && st.attributes && st.attributes.unique_id) || "";
      var m = uid.match(/^zipassist_[a-f0-9-]{36}_(.+)$/);
      if (!g[dn][m ? m[1] : eid]) g[dn][m ? m[1] : eid] = eid;
    }
    return g;
  }

  function fmt(eid, h) {
    var st = h.states[eid];
    if (!st || st.state === "unavailable" || st.state === "unknown") return "—";
    var raw = st.state, num = parseFloat(raw);
    if (!isNaN(num)) return Math.round(num * 100) / 100 + ((st.attributes || {}).unit_of_measurement ? " " + st.attributes.unit_of_measurement : "");
    return raw === "on" ? "On" : raw === "off" ? "Off" : raw;
  }

  function esc(s) { return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;"); }

  if (!document.getElementById("za-style")) {
    var s = document.createElement("style"); s.id = "za-style"; s.textContent = [
      "",".card{background:var(--ha-card-background,var(--card-background-color,#fff));border-radius:var(--ha-card-border-radius,12px);box-shadow:var(--ha-card-box-shadow,0 2px 2px 0 rgba(0,0,0,.14));border:var(--ha-card-border-width,1px) solid var(--ha-card-border-color,var(--divider-color,#e0e0e0));padding:16px}",
      ".card-header{display:flex;align-items:center;gap:10px;padding-bottom:12px;margin-bottom:8px;border-bottom:1px solid var(--divider-color,#e0e0e0)}",
      ".card-header .name{font-size:1.2em;font-weight:600;color:var(--primary-text-color);flex:1}",
      ".card-header ha-icon{color:var(--primary-color,#03a9f4)}",
      ".section{margin-bottom:14px}.section:last-child{margin-bottom:0}",
      ".section-heading{display:flex;align-items:center;gap:6px;margin-bottom:6px;font-size:.8em;font-weight:600;text-transform:uppercase;letter-spacing:.5px;color:var(--secondary-text-color);cursor:pointer}",
      ".section-heading ha-icon{--mdc-icon-size:16px}",
      ".section-heading .s-chevron{margin-left:auto;transition:transform .2s;--mdc-icon-size:14px}",
      ".section-heading .s-chevron.open{transform:rotate(180deg)}",
      ".section-body.collapsed{display:none}",
      ".info-tiles{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:6px}",
      ".info-tile{display:flex;align-items:center;gap:8px;padding:8px 10px;border-radius:8px;background:var(--card-background-color,rgba(0,0,0,.02));border:1px solid var(--divider-color,rgba(0,0,0,.06))}",
      ".info-tile ha-icon{color:var(--primary-color,#03a9f4)}",
      ".tile-value{font-size:.9em;font-weight:500;color:var(--primary-text-color)}",
      ".tile-label{font-size:.7em;color:var(--secondary-text-color)}",
      ".entity-row{display:flex;align-items:center;justify-content:space-between;padding:4px 0;min-height:36px;border-bottom:1px solid var(--divider-color,rgba(0,0,0,.06))}",
      ".entity-row:last-child{border-bottom:none}",
      ".entity-label{font-size:.85em;color:var(--primary-text-color);flex:1}",
      ".entity-control{display:flex;align-items:center;gap:8px}",
      ".entity-value{font-size:.85em;color:var(--primary-text-color)}",
      ".toggle{position:relative;display:inline-block;width:44px;height:24px;flex-shrink:0}",
      ".toggle input{opacity:0;width:0;height:0}",
      ".toggle .slider{position:absolute;cursor:pointer;top:0;left:0;right:0;bottom:0;background:#ccc;border-radius:24px;transition:.3s}",
      ".toggle .slider::before{content:'';position:absolute;height:18px;width:18px;left:3px;bottom:3px;background:#fff;border-radius:50%;transition:.3s}",
      ".toggle input:checked+.slider{background:var(--primary-color,#03a9f4)}",
      ".toggle input:checked+.slider::before{transform:translateX(20px)}",
      ".no-data{text-align:center;color:var(--secondary-text-color);font-style:italic;padding:20px}",
    ].join("");
    document.head.appendChild(s);
  }

  var ZipAssistCard = function () { HTMLElement.call(this); };
  ZipAssistCard.prototype = Object.create(HTMLElement.prototype);
  ZipAssistCard.prototype.constructor = ZipAssistCard;

  Object.defineProperty(ZipAssistCard.prototype, "hass", {
    set: function (h) { this._hass = h; if (this._config) this._render(); }
  });
  ZipAssistCard.prototype.setConfig = function (c) { this._config = c || {}; this._render(); };
  ZipAssistCard.prototype.getCardSize = function () { return 8; };

  ZipAssistCard.prototype._render = function () {
    var h = this._hass, c = this._config;
    if (!h || !c) return;

    var ids = findIds(h);
    if (!ids.length) {
      this.innerHTML = '<div class="card"><div class="no-data">No ZipAssist entities found.</div></div>';
      return;
    }

    var groups = groupByDevice(ids, h);
    var names = Object.keys(groups).sort();

    if (c.device) {
      var dv = c.device.toLowerCase();
      names = names.filter(function (n) { return n === c.device || n.toLowerCase().indexOf(dv) > -1; });
    }

    var html = '';
    for (var di = 0; di < names.length; di++) {
      var dn = names[di], ents = groups[dn], title = c.title || dn;
      html += '<div class="card"><div class="card-header"><ha-icon icon="mdi:water-pump"></ha-icon><span class="name">' + esc(title) + '</span></div>';

      for (var si = 0; si < SECTIONS.length; si++) {
        var sec = SECTIONS[si], avail = [];
        for (var ii = 0; ii < sec.e.length; ii++) {
          var it = sec.e[ii], eid = ents[it[0]];
          if (eid && h.states[eid]) avail.push({ id: eid, label: it[1] });
        }
        if (!avail.length) continue;

        var ck = dn + "||" + sec.t, sc = (this._sc || {})[ck] || false;

        html += '<div class="section"><div class="section-heading" data-ck="' + esc(ck) + '">';
        html += '<ha-icon icon="' + (sec.i || "mdi:circle") + '"></ha-icon><span>' + esc(sec.t) + '</span>';
        html += '<ha-icon class="s-chevron' + (sc ? '' : ' open') + '" icon="mdi:chevron-down"></ha-icon></div>';
        html += '<div class="section-body' + (sc ? ' collapsed' : '') + '">';

        if (sec.g) {
          html += '<div class="info-tiles">';
          for (var ai = 0; ai < avail.length; ai++) {
            var ae = avail[ai], ico = ((h.states[ae.id] || {}).attributes || {}).icon || "mdi:circle";
            html += '<div class="info-tile"><ha-icon icon="' + ico + '"></ha-icon><div><div class="tile-label">' + esc(ae.label) + '</div><div class="tile-value">' + esc(fmt(ae.id, h)) + '</div></div></div>';
          }
          html += '</div>';
        } else {
          html += '<div class="entity-rows">';
          for (var aj = 0; aj < avail.length; aj++) {
            var be = avail[aj], st2 = h.states[be.id], sw = be.id.indexOf("switch.") === 0, on = st2 && st2.state === "on";
            html += '<div class="entity-row"><span class="entity-label">' + esc(be.label) + '</span><div class="entity-control"><span class="entity-value">' + esc(fmt(be.id, h)) + '</span>';
            if (sw) html += '<label class="toggle" data-eid="' + esc(be.id) + '"><input type="checkbox"' + (on ? ' checked' : '') + '><span class="slider"></span></label>';
            html += '</div></div>';
          }
          html += '</div>';
        }
        html += '</div></div>';
      }
      html += '</div>';
    }

    this.innerHTML = html;
    var self = this;
    var togs = this.querySelectorAll(".toggle");
    for (var ti = 0; ti < togs.length; ti++) togs[ti].addEventListener("change", function () {
      var svc = this.querySelector("input").checked ? "turn_on" : "turn_off";
      h.callService("switch", svc, { entity_id: this.getAttribute("data-eid") });
    });
    var heads = this.querySelectorAll("[data-ck]");
    for (var hi = 0; hi < heads.length; hi++) heads[hi].addEventListener("click", function () {
      var k = this.getAttribute("data-ck");
      if (!self._sc) self._sc = {};
      self._sc[k] = !self._sc[k];
      self._render();
    });
  };

  customElements.define("zipassist-card", ZipAssistCard);

  window.customCards = window.customCards || [];
  window.customCards.push({
    type: "zipassist-card",
    name: "ZipAssist HydroTap",
    description: "ZipAssist CMMS HydroTap monitoring & control card",
    preview: true,
  });
})();
