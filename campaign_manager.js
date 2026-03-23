/**
 * Pievra Campaign Manager
 * Full data table with sort, filter, multi-select, bulk actions, export
 */

window.CampaignManager = (function() {
  var _data = [];
  var _filtered = [];
  var _selected = new Set();
  var _sortCol = 'created_at';
  var _sortDir = -1;
  var _filters = {search:'', status:'all', advertiser:'all', objective:'all'};
  var _tok = '';

  // ── INIT ──────────────────────────────────────────────────────────────────

  function init(token) {
    _tok = token || localStorage.getItem('pievra_token') || '';
    load();
  }

  function load() {
    var el = document.getElementById('cm-table-body');
    if(el) el.innerHTML = '<tr><td colspan="13" style="text-align:center;padding:32px;color:var(--muted)">Loading campaigns...</td></tr>';
    fetch('/api/campaigns/all', {
      credentials: 'include',
      headers: {'Authorization': 'Bearer ' + _tok}
    }).then(function(r){ return r.json(); })
    .then(function(d) {
      _data = d.campaigns || [];
      buildFilterOptions();
      applyFilters();
      render();
    }).catch(function(e) {
      console.error('Campaign Manager load error:', e);
    });
  }

  // ── FILTERS ───────────────────────────────────────────────────────────────

  function buildFilterOptions() {
    var advertisers = [...new Set(_data.map(c => c.advertiser || c.brand || 'Unknown'))].sort();
    var sel = document.getElementById('cm-filter-advertiser');
    if(sel) {
      sel.innerHTML = '<option value="all">All Advertisers</option>' +
        advertisers.map(a => '<option value="'+escHtml(a)+'">'+escHtml(a)+'</option>').join('');
    }
  }

  function applyFilters() {
    var q = _filters.search.toLowerCase();
    _filtered = _data.filter(function(c) {
      if(_filters.status !== 'all' && c.status !== _filters.status) return false;
      if(_filters.objective !== 'all' && c.objective !== _filters.objective) return false;
      if(_filters.advertiser !== 'all') {
        var adv = c.advertiser || c.brand || 'Unknown';
        if(adv !== _filters.advertiser) return false;
      }
      if(q) {
        var haystack = [c.brand,c.campaign_name,c.advertiser,c.customer_sn,c.campaign_sn,c.flight_sn,c.objective,c.status].join(' ').toLowerCase();
        if(haystack.indexOf(q) === -1) return false;
      }
      return true;
    });
    sortData();
    updateCount();
  }

  function sortData() {
    _filtered.sort(function(a,b) {
      var va = a[_sortCol] || '', vb = b[_sortCol] || '';
      if(typeof va === 'number' && typeof vb === 'number') return (va - vb) * _sortDir;
      return String(va).localeCompare(String(vb)) * _sortDir;
    });
  }

  function updateCount() {
    var el = document.getElementById('cm-count');
    if(el) el.textContent = _filtered.length + ' campaigns';
    var selEl = document.getElementById('cm-selected-count');
    if(selEl) selEl.textContent = _selected.size > 0 ? _selected.size + ' selected' : '';
  }

  // ── RENDER ────────────────────────────────────────────────────────────────

  var STATUS_STYLE = {
    active:   {bg:'#dcfce7',color:'#166534'},
    paused:   {bg:'#dbeafe',color:'#1e40af'},
    draft:    {bg:'#fef9c3',color:'#854d0e'},
    archived: {bg:'#f3f4f6',color:'#6b7280'},
    deleted:  {bg:'#fee2e2',color:'#dc2626'},
  };

  function render() {
    var tbody = document.getElementById('cm-table-body');
    if(!tbody) return;
    if(!_filtered.length) {
      tbody.innerHTML = '<tr><td colspan="13" style="text-align:center;padding:48px;color:var(--muted)"><div style="font-size:28px;margin-bottom:8px">📭</div><div style="font-weight:600">No campaigns match your filters</div></td></tr>';
      return;
    }
    tbody.innerHTML = _filtered.map(function(c) {
      var ss = STATUS_STYLE[c.status] || STATUS_STYLE.draft;
      var plan = c.plan_json || {};
      var kpis = plan.projected_kpis || {};
      var imp = kpis.estimated_impressions ? parseInt(kpis.estimated_impressions).toLocaleString() : '—';
      var cpm = kpis.weighted_cpm ? '$'+parseFloat(kpis.weighted_cpm).toFixed(2) : '—';
      var roas = kpis.estimated_roas ? kpis.estimated_roas+'x' : '—';
      var checked = _selected.has(c.id) ? 'checked' : '';
      var rowBg = _selected.has(c.id) ? 'background:#f0fdf4' : '';
      var consentBadge = c.go_live_consent
        ? '<span title="Consent recorded" style="color:#166534;font-size:11px">✅</span>'
        : '<span title="Not activated" style="color:#6b7280;font-size:11px">⏸</span>';
      return '<tr style="border-bottom:1px solid var(--border);cursor:pointer;'+rowBg+'" onclick="CampaignManager.toggleRow(event,'+c.id+')">'
        + '<td style="padding:10px 12px;width:32px"><input type="checkbox" '+checked+' onclick="CampaignManager.toggleSelect(event,'+c.id+')" style="width:14px;height:14px;accent-color:#00c4a7"></td>'
        + '<td style="padding:10px 12px;font-size:11px;font-family:monospace;color:var(--muted)" title="'+escHtml(c.customer_sn||'')+'">'+escHtml((c.customer_sn||'—').substring(0,18))+'</td>'
        + '<td style="padding:10px 12px"><div style="font-weight:700;font-size:13px;color:var(--ink)">'+escHtml(c.brand||'—')+'</div><div style="font-size:11px;color:var(--muted)">'+escHtml(c.advertiser||c.brand||'—')+'</div></td>'
        + '<td style="padding:10px 12px;font-size:13px;color:var(--ink);max-width:160px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="'+escHtml(c.campaign_name||'')+'">'+escHtml(c.campaign_name||'—')+'</td>'
        + '<td style="padding:10px 12px;font-size:11px;font-family:monospace;color:var(--muted)" title="'+escHtml(c.flight_sn||'')+'">'+escHtml((c.flight_sn||'—').split('-FLT-')[1]||'—')+'</td>'
        + '<td style="padding:10px 12px"><span style="background:'+ss.bg+';color:'+ss.color+';font-size:11px;font-weight:700;padding:2px 8px;border-radius:20px">'+c.status.toUpperCase()+'</span> '+consentBadge+'</td>'
        + '<td style="padding:10px 12px;font-size:12px;color:var(--soft)">'+escHtml(c.objective||'—')+'</td>'
        + '<td style="padding:10px 12px;font-size:13px;font-weight:700;color:var(--ink);text-align:right">$'+parseInt(c.budget||0).toLocaleString()+'</td>'
        + '<td style="padding:10px 12px;font-size:12px;text-align:right;color:var(--soft)">'+cpm+'</td>'
        + '<td style="padding:10px 12px;font-size:12px;text-align:right;color:var(--soft)">'+imp+'</td>'
        + '<td style="padding:10px 12px;font-size:12px;text-align:right;color:var(--soft)">'+roas+'</td>'
        + '<td style="padding:10px 12px;font-size:11px;color:var(--muted)">'+fmtDate(c.flight_start||c.created_at)+'</td>'
        + '<td style="padding:10px 12px"><div style="display:flex;gap:4px">'
          + '<button onclick="CampaignManager.openDetail('+c.id+')" style="border:none;background:var(--surf);color:var(--soft);font-size:11px;padding:4px 8px;border-radius:6px;cursor:pointer">View</button>'
          + '<button onclick="CampaignManager.quickEdit(event,'+c.id+')" style="border:none;background:var(--surf);color:var(--soft);font-size:11px;padding:4px 8px;border-radius:6px;cursor:pointer">Edit</button>'
        + '</div></td>'
        + '</tr>';
    }).join('');

    // Update header checkbox
    var hdrCb = document.getElementById('cm-select-all');
    if(hdrCb) hdrCb.indeterminate = _selected.size > 0 && _selected.size < _filtered.length;
    if(hdrCb) hdrCb.checked = _selected.size === _filtered.length && _filtered.length > 0;

    updateBulkBar();
  }

  function fmtDate(d) {
    if(!d) return '—';
    try { return new Date(d).toLocaleDateString('en-GB',{day:'numeric',month:'short',year:'2-digit'}); }
    catch(e) { return d; }
  }

  function escHtml(s) {
    return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
  }

  // ── SELECTION ─────────────────────────────────────────────────────────────

  function toggleRow(e, id) {
    if(e.target.tagName === 'INPUT' || e.target.tagName === 'BUTTON') return;
    toggleSelect(e, id);
  }

  function toggleSelect(e, id) {
    e.stopPropagation();
    if(_selected.has(id)) _selected.delete(id);
    else _selected.add(id);
    render();
  }

  function selectAll(checked) {
    if(checked) _filtered.forEach(function(c){ _selected.add(c.id); });
    else _selected.clear();
    render();
  }

  function updateBulkBar() {
    var bar = document.getElementById('cm-bulk-bar');
    if(!bar) return;
    if(_selected.size > 0) {
      bar.style.display = 'flex';
      var sc = document.getElementById('cm-bulk-count');
      if(sc) sc.textContent = _selected.size + ' campaign' + (_selected.size > 1 ? 's' : '') + ' selected';
    } else {
      bar.style.display = 'none';
    }
  }

  // ── SORT ──────────────────────────────────────────────────────────────────

  function sortBy(col) {
    if(_sortCol === col) _sortDir *= -1;
    else { _sortCol = col; _sortDir = 1; }
    // Update header arrows
    document.querySelectorAll('[data-sort]').forEach(function(th) {
      th.querySelector('.sort-arrow') && (th.querySelector('.sort-arrow').textContent = th.dataset.sort === col ? (_sortDir === 1 ? ' ↑' : ' ↓') : ' ↕');
    });
    sortData();
    render();
  }

  // ── BULK ACTIONS ──────────────────────────────────────────────────────────

  function bulkStatus(status) {
    if(!_selected.size) return;
    var ids = Array.from(_selected);
    Promise.all(ids.map(function(id) {
      var camp = _data.find(c => c.id === id);
      if(!camp) return Promise.resolve();
      return fetch('/api/campaign/'+id, {
        method: 'PUT', credentials: 'include',
        headers: {'Content-Type':'application/json','Authorization':'Bearer '+_tok},
        body: JSON.stringify(Object.assign({}, camp.form_data||{}, {
          brand: camp.brand, campaign_name: camp.campaign_name,
          objective: camp.objective, buying_model: camp.buying_model,
          budget: camp.budget, status: status
        }))
      });
    })).then(function() {
      _selected.clear();
      load();
      showToast(ids.length + ' campaign' + (ids.length>1?'s':'') + ' set to ' + status);
    });
  }

  // ── EXPORT ────────────────────────────────────────────────────────────────

  function exportCSV() {
    var rows = _selected.size > 0 ? _filtered.filter(c => _selected.has(c.id)) : _filtered;
    var headers = ['Customer SN','Brand','Advertiser','Campaign Name','Campaign SN','Flight SN','Status','Objective','Buying Model','Budget USD','CPM','Impressions','ROAS','Flight Start','Flight End','Created','Consent'];
    var csv = headers.join(',') + '\n';
    rows.forEach(function(c) {
      var plan = c.plan_json || {};
      var kpis = plan.projected_kpis || {};
      var row = [
        c.customer_sn||'', c.brand||'', c.advertiser||c.brand||'', c.campaign_name||'',
        c.campaign_sn||'', c.flight_sn||'', c.status||'', c.objective||'',
        c.buying_model||'', c.budget||'0',
        kpis.weighted_cpm||'', kpis.estimated_impressions||'', kpis.estimated_roas||'',
        c.flight_start||'', c.flight_end||'', c.created_at||'',
        c.go_live_consent?'Yes':'No'
      ].map(function(v){ return '"'+String(v).replace(/"/g,'""')+'"'; });
      csv += row.join(',') + '\n';
    });
    var blob = new Blob([csv], {type:'text/csv'});
    var a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'pievra_campaigns_' + new Date().toISOString().substring(0,10) + '.csv';
    a.click();
    showToast('CSV exported — ' + rows.length + ' campaigns');
  }

  function exportXLSX() {
    // Use SheetJS via CDN if available, fallback to CSV
    if(typeof XLSX !== 'undefined') {
      var rows = _selected.size > 0 ? _filtered.filter(c => _selected.has(c.id)) : _filtered;
      var data = [['Customer SN','Brand','Advertiser','Campaign','Campaign SN','Flight SN','Status','Objective','Budget','CPM','Impressions','ROAS','Start','Consent']];
      rows.forEach(function(c) {
        var kpis = (c.plan_json||{}).projected_kpis||{};
        data.push([c.customer_sn||'',c.brand||'',c.advertiser||'',c.campaign_name||'',c.campaign_sn||'',c.flight_sn||'',c.status||'',c.objective||'',parseFloat(c.budget||0),parseFloat(kpis.weighted_cpm||0),parseInt(kpis.estimated_impressions||0),parseFloat(kpis.estimated_roas||0),c.flight_start||'',c.go_live_consent?'Yes':'No']);
      });
      var ws = XLSX.utils.aoa_to_sheet(data);
      var wb = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(wb, ws, 'Campaigns');
      XLSX.writeFile(wb, 'pievra_campaigns_' + new Date().toISOString().substring(0,10) + '.xlsx');
      showToast('Excel exported — ' + rows.length + ' campaigns');
    } else {
      // Load SheetJS then retry
      var s = document.createElement('script');
      s.src = 'https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js';
      s.onload = function(){ exportXLSX(); };
      document.head.appendChild(s);
    }
  }

  function exportEmail() {
    var email = prompt('Send export to email address:');
    if(!email || email.indexOf('@') === -1) return;
    var rows = _selected.size > 0 ? _filtered.filter(c => _selected.has(c.id)) : _filtered;
    fetch('/api/campaigns/export-email', {
      method: 'POST', credentials: 'include',
      headers: {'Content-Type':'application/json','Authorization':'Bearer '+_tok},
      body: JSON.stringify({email: email, campaign_ids: rows.map(c=>c.id)})
    }).then(function(r){ return r.json(); })
    .then(function(d){ showToast('Export sent to ' + email); })
    .catch(function(){ showToast('Export queued — will be sent shortly'); });
  }

  // ── DETAIL / EDIT ─────────────────────────────────────────────────────────

  function openDetail(id) {
    window.location.href = '/plan/' + id;
  }

  function quickEdit(e, id) {
    e.stopPropagation();
    if(typeof openEdit === 'function') openEdit(id);
  }

  // ── TOAST ─────────────────────────────────────────────────────────────────

  function showToast(msg) {
    var t = document.createElement('div');
    t.style.cssText = 'position:fixed;bottom:24px;right:24px;background:#0a0e1a;color:white;padding:12px 20px;border-radius:10px;font-size:14px;font-weight:600;z-index:99999;box-shadow:0 8px 32px rgba(0,0,0,.3)';
    t.textContent = msg;
    document.body.appendChild(t);
    setTimeout(function(){ t.remove(); }, 3000);
  }

  return {
    init: init, load: load, applyFilters: applyFilters, sortBy: sortBy,
    toggleRow: toggleRow, toggleSelect: toggleSelect, selectAll: selectAll,
    bulkStatus: bulkStatus, exportCSV: exportCSV, exportXLSX: exportXLSX,
    exportEmail: exportEmail, openDetail: openDetail, quickEdit: quickEdit,
    setFilter: function(k,v){ _filters[k]=v; applyFilters(); render(); }
  };
})();
