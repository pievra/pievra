/**
 * Pievra Platform Widgets
 * - Protocol Status Tickers
 * - Go-Live Consent Modal
 * - Serial Number Display
 */

(function() {
  var PROTO_COLORS = {
    AdCP: '#dbeafe', MCP: '#dcfce7', UCP: '#f3e8ff', ARTF: '#fef9c3', A2A: '#ffe4e6'
  };
  var PROTO_TEXT = {
    AdCP: '#1e40af', MCP: '#166534', UCP: '#7e22ce', ARTF: '#854d0e', A2A: '#be123c'
  };

  // ── PROTOCOL STATUS TICKERS ───────────────────────────────────────────────

  window.PievraProtocolTicker = {
    render: function(containerId) {
      var el = document.getElementById(containerId);
      if (!el) return;
      el.innerHTML = '<div style="display:flex;gap:6px;flex-wrap:wrap;align-items:center">' +
        Object.keys(PROTO_COLORS).map(function(p) {
          return '<span id="ptick-'+p+'" style="display:inline-flex;align-items:center;gap:4px;'+
            'background:'+PROTO_COLORS[p]+';color:'+PROTO_TEXT[p]+';'+
            'font-size:11px;font-weight:700;padding:3px 8px;border-radius:20px;'+
            'cursor:pointer" onclick="PievraProtocolTicker.showDetail(\''+p+'\')" '+
            'title="Click for details">'+
            '<span id="ptick-dot-'+p+'" style="width:6px;height:6px;border-radius:50%;'+
            'background:currentColor;opacity:.4"></span>'+
            p+'<span id="ptick-label-'+p+'" style="opacity:.7;font-weight:400"></span>'+
          '</span>';
        }).join('') +
      '</div>';
      PievraProtocolTicker.fetch();
    },

    fetch: function() {
      fetch('/api/protocol/status')
        .then(function(r){ return r.json(); })
        .then(function(d) {
          window._protocolStatus = d;
          Object.entries(d.protocols || {}).forEach(function(e) {
            var proto = e[0], info = e[1];
            var dot = document.getElementById('ptick-dot-'+proto);
            var label = document.getElementById('ptick-label-'+proto);
            if (dot) dot.style.opacity = info.live ? '1' : '.3';
            if (label) label.textContent = info.live ? ' Live' : ' Sim';
          });
        })
        .catch(function(){});
    },

    showDetail: function(proto) {
      var d = window._protocolStatus;
      if (!d) return;
      var info = d.protocols[proto];
      if (!info) return;
      var modal = document.createElement('div');
      modal.style.cssText = 'position:fixed;inset:0;background:rgba(10,14,26,.7);z-index:10000;'+
        'display:flex;align-items:center;justify-content:center;padding:20px';
      var constraints = '';
      if (proto === 'ARTF' && d.artf_constraints) {
        var c = d.artf_constraints;
        constraints = '<div style="background:white;border:1px solid #e2e4ed;border-radius:10px;padding:14px;margin-top:12px">'+
          '<div style="font-size:12px;font-weight:700;color:#0a0e1a;margin-bottom:8px">ARTF Prebid Server - Current Constraints</div>'+
          '<div style="font-size:12px;color:#7a829e;line-height:1.6">'+
          '<b>Environments:</b> '+c.environments.join(', ')+'<br>'+
          '<b>Formats:</b> '+c.formats.join(', ')+'<br>'+
          '<b>Bidders:</b> '+c.bidders.join(', ')+'<br>'+
          '<b>Mode:</b> '+c.mode+'<br>'+
          '<span style="color:#854d0e">&#9888; '+c.note+'</span>'+
          '</div></div>';
      }
      modal.innerHTML = '<div style="background:#f4f5f9;border-radius:16px;padding:28px;max-width:480px;width:100%">'+
        '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px">'+
          '<div style="display:flex;align-items:center;gap:10px">'+
            '<span style="background:'+PROTO_COLORS[proto]+';color:'+PROTO_TEXT[proto]+';'+
            'font-size:13px;font-weight:800;padding:4px 12px;border-radius:20px">'+proto+'</span>'+
            '<span style="font-size:13px;color:'+(info.live?'#166534':'#854d0e')+'">'+
            (info.live?'&#x1F7E2; ':'&#x1F7E1; ')+info.label+'</span>'+
          '</div>'+
          '<button onclick="this.closest(\'div[style*=fixed]\').remove()" '+
          'style="border:none;background:none;font-size:18px;cursor:pointer;color:#7a829e">&times;</button>'+
        '</div>'+
        '<p style="font-size:14px;color:#3d4460;line-height:1.6;margin-bottom:4px">'+info.desc+'</p>'+
        constraints+
        '<div style="margin-top:16px;font-size:11px;color:#7a829e">'+
          'Protocol status is updated in real time. Simulation mode uses verified market benchmarks '+
          'and IAB-spec compliant data objects. Live connections activate automatically when DSP/SSP '+
          'API keys are added in Settings.</div>'+
      '</div>';
      modal.onclick = function(e){ if(e.target===modal) modal.remove(); };
      document.body.appendChild(modal);
    }
  };

  // ── GO-LIVE CONSENT MODAL ─────────────────────────────────────────────────

  window.PievraConsent = {
    show: function(campaignId, campaignSn, flightSn, budget, onSuccess) {
      var modal = document.createElement('div');
      modal.id = 'consent-modal-'+campaignId;
      modal.style.cssText = 'position:fixed;inset:0;background:rgba(10,14,26,.85);z-index:10000;'+
        'display:flex;align-items:center;justify-content:center;padding:20px;overflow-y:auto';

      var now = new Date().toISOString().replace('T',' ').substring(0,19)+' UTC';
      var budgetFmt = '$'+parseInt(budget||0).toLocaleString();

      modal.innerHTML = '<div style="background:white;border-radius:16px;padding:32px;max-width:560px;width:100%;'+
        'box-shadow:0 24px 80px rgba(0,0,0,.3)">'+

        // Header
        '<div style="display:flex;align-items:center;gap:12px;margin-bottom:20px">'+
          '<div style="width:44px;height:44px;background:#fef9c3;border-radius:12px;display:flex;'+
          'align-items:center;justify-content:center;font-size:22px">&#x26A0;&#xFE0F;</div>'+
          '<div><div style="font-family:Manrope,sans-serif;font-weight:800;font-size:18px;color:#0a0e1a">'+
          'Campaign Activation Consent</div>'+
          '<div style="font-size:13px;color:#7a829e">Required before your campaign goes live</div></div>'+
        '</div>'+

        // Serial numbers
        '<div style="background:#f4f5f9;border-radius:10px;padding:14px;margin-bottom:20px;font-size:12px;'+
        'font-family:monospace;color:#3d4460;line-height:2">'+
          '<div><b>Campaign SN:</b> '+campaignSn+'</div>'+
          '<div><b>Flight SN:</b> '+flightSn+'</div>'+
          '<div><b>Total Budget:</b> '+budgetFmt+'</div>'+
          '<div><b>Timestamp:</b> '+now+'</div>'+
        '</div>'+

        // Warning box
        '<div style="background:#fef2f2;border:1px solid #fecaca;border-radius:10px;padding:16px;margin-bottom:20px">'+
          '<div style="font-weight:700;color:#991b1b;font-size:13px;margin-bottom:8px">'+
          '&#x1F4B3; Billing Notice - Please Read Carefully</div>'+
          '<div style="font-size:13px;color:#7f1d1d;line-height:1.6">'+
          'By activating this campaign you agree that <b>the full budget of '+budgetFmt+' will be charged '+
          'based on impressions delivered</b>, regardless of campaign performance, ROAS or conversion outcomes. '+
          '<br><br>'+
          '<b>Pievra acts as an intermediary platform only.</b> Pievra does not guarantee any specific '+
          'number of conversions, clicks, revenue or return on ad spend. '+
          'Pievra bears no liability for campaign results.</div>'+
        '</div>'+

        // Consent checkboxes
        '<div style="display:flex;flex-direction:column;gap:12px;margin-bottom:20px">'+

          '<label style="display:flex;align-items:flex-start;gap:10px;cursor:pointer;font-size:13px;color:#3d4460">'+
            '<input type="checkbox" id="consent-billing-'+campaignId+'" style="width:16px;height:16px;margin-top:1px;accent-color:#00c4a7;flex-shrink:0">'+
            '<span>I understand and accept that the full campaign budget of <b>'+budgetFmt+'</b> will be charged '+
            'on impressions delivered, with no performance guarantees. <b style="color:#dc2626">Required.</b></span>'+
          '</label>'+

          '<label style="display:flex;align-items:flex-start;gap:10px;cursor:pointer;font-size:13px;color:#3d4460">'+
            '<input type="checkbox" id="consent-intermediary-'+campaignId+'" style="width:16px;height:16px;margin-top:1px;accent-color:#00c4a7;flex-shrink:0">'+
            '<span>I acknowledge that Pievra operates as an intermediary only and bears no liability for '+
            'campaign performance, third-party platform availability or ad delivery outcomes. '+
            '<b style="color:#dc2626">Required.</b></span>'+
          '</label>'+

          '<label style="display:flex;align-items:flex-start;gap:10px;cursor:pointer;font-size:13px;color:#3d4460">'+
            '<input type="checkbox" id="consent-gdpr-'+campaignId+'" style="width:16px;height:16px;margin-top:1px;accent-color:#00c4a7;flex-shrink:0">'+
            '<span>I confirm that the campaign targeting complies with GDPR (EU) 2016/679, TCF 2.2 and all '+
            'applicable data protection laws in the target markets. I hold the legal basis for any audience '+
            'data used. <b style="color:#dc2626">Required.</b></span>'+
          '</label>'+

          '<label style="display:flex;align-items:flex-start;gap:10px;cursor:pointer;font-size:13px;color:#3d4460">'+
            '<input type="checkbox" id="consent-tc-'+campaignId+'" style="width:16px;height:16px;margin-top:1px;accent-color:#00c4a7;flex-shrink:0">'+
            '<span>I have read and agree to the <a href="/advertising-terms" target="_blank" style="color:#00c4a7">'+
            'Advertising Terms & Conditions</a> and <a href="/privacy" target="_blank" style="color:#00c4a7">'+
            'Privacy Policy</a>. <b style="color:#dc2626">Required.</b></span>'+
          '</label>'+

        '</div>'+

        // Signature field
        '<div style="margin-bottom:20px">'+
          '<label style="font-size:12px;font-weight:700;color:#7a829e;text-transform:uppercase;'+
          'letter-spacing:.06em;display:block;margin-bottom:6px">Electronic Signature (full name)</label>'+
          '<input type="text" id="consent-sig-'+campaignId+'" placeholder="Type your full name to confirm" '+
          'style="width:100%;padding:10px 14px;border:1px solid #e2e4ed;border-radius:8px;'+
          'font-size:14px;color:#0a0e1a;background:#f4f5f9;font-family:Inter,sans-serif">'+
        '</div>'+

        // Error message
        '<div id="consent-err-'+campaignId+'" style="display:none;background:#fef2f2;border:1px solid #fecaca;'+
        'border-radius:8px;padding:10px 14px;font-size:13px;color:#991b1b;margin-bottom:14px"></div>'+

        // GDPR notice
        '<div style="font-size:11px;color:#7a829e;line-height:1.6;margin-bottom:20px">'+
          'This consent is recorded with timestamp, IP address and campaign serial numbers under '+
          'GDPR Art.6(1)(b) - performance of contract. Records are retained for 7 years per EU '+
          'accounting law. <a href="/privacy" target="_blank" style="color:#00c4a7">Privacy Policy</a>.'+
        '</div>'+

        // Buttons
        '<div style="display:flex;gap:10px">'+
          '<button onclick="document.getElementById(\'consent-modal-'+campaignId+'\').remove()" '+
          'style="flex:1;padding:12px;border:1px solid #e2e4ed;background:none;border-radius:10px;'+
          'font-size:14px;font-weight:600;color:#7a829e;cursor:pointer;font-family:Inter">Cancel</button>'+
          '<button id="consent-submit-'+campaignId+'" '+
          'onclick="PievraConsent.submit(\''+campaignId+'\',\''+campaignSn+'\',\''+flightSn+'\','+onSuccess+')" '+
          'style="flex:2;padding:12px;border:none;background:#0a0e1a;color:white;border-radius:10px;'+
          'font-size:14px;font-weight:700;cursor:pointer;font-family:Inter">'+
          '&#x1F680; Activate Campaign</button>'+
        '</div>'+

      '</div>';
      document.body.appendChild(modal);
    },

    submit: function(campaignId, campaignSn, flightSn, onSuccess) {
      var billing = document.getElementById('consent-billing-'+campaignId);
      var intermediary = document.getElementById('consent-intermediary-'+campaignId);
      var gdpr = document.getElementById('consent-gdpr-'+campaignId);
      var tc = document.getElementById('consent-tc-'+campaignId);
      var sig = document.getElementById('consent-sig-'+campaignId);
      var err = document.getElementById('consent-err-'+campaignId);
      var btn = document.getElementById('consent-submit-'+campaignId);

      err.style.display = 'none';

      if (!billing.checked) { err.textContent='Please accept the billing terms.'; err.style.display='block'; return; }
      if (!intermediary.checked) { err.textContent='Please acknowledge Pievra\'s intermediary role.'; err.style.display='block'; return; }
      if (!gdpr.checked) { err.textContent='Please confirm GDPR compliance.'; err.style.display='block'; return; }
      if (!tc.checked) { err.textContent='Please accept the Advertising T&Cs.'; err.style.display='block'; return; }
      if (!sig.value.trim() || sig.value.trim().length < 3) { err.textContent='Please enter your full name as electronic signature.'; err.style.display='block'; return; }

      btn.textContent = 'Activating...';
      btn.disabled = true;

      var tok = localStorage.getItem('pievra_token') || '';
      fetch('/api/campaign/'+campaignId+'/consent', {
        method: 'POST',
        credentials: 'include',
        headers: {'Content-Type':'application/json','Authorization':'Bearer '+tok},
        body: JSON.stringify({
          billing_accepted: true,
          intermediary_accepted: true,
          gdpr_accepted: true,
          tc_accepted: true,
          signature: sig.value.trim(),
          campaign_sn: campaignSn,
          flight_sn: flightSn
        })
      })
      .then(function(r){ return r.json(); })
      .then(function(d) {
        if (d.status === 'consent_recorded') {
          document.getElementById('consent-modal-'+campaignId).remove();
          if (typeof onSuccess === 'function') onSuccess(d);
          else window.location.reload();
        } else {
          err.textContent = d.error || 'Activation failed. Please try again.';
          err.style.display = 'block';
          btn.textContent = '&#x1F680; Activate Campaign';
          btn.disabled = false;
        }
      })
      .catch(function() {
        err.textContent = 'Network error. Please try again.';
        err.style.display = 'block';
        btn.textContent = '&#x1F680; Activate Campaign';
        btn.disabled = false;
      });
    }
  };

  // ── SERIAL NUMBER BADGE ────────────────────────────────────────────────────

  window.PievraSerialBadge = {
    render: function(containerId, customerSn, campaignSn, flightSn) {
      var el = document.getElementById(containerId);
      if (!el) return;
      el.innerHTML = '<div style="background:#f4f5f9;border-radius:10px;padding:12px 16px;'+
        'font-family:monospace;font-size:11px;color:#7a829e;line-height:1.8">'+
        (customerSn ? '<div><span style="color:#0a0e1a;font-weight:700">Customer:</span> '+customerSn+'</div>' : '')+
        (campaignSn ? '<div><span style="color:#0a0e1a;font-weight:700">Campaign:</span> '+campaignSn+'</div>' : '')+
        (flightSn ? '<div><span style="color:#0a0e1a;font-weight:700">Flight SN:</span> '+flightSn+'</div>' : '')+
        (flightSn ? '<div style="margin-top:4px;font-size:10px;color:#7a829e">'+
          '&#x1F4CB; IAB OpenRTB 2.6 dealid - GDPR Art.6(1)(b)</div>' : '')+
      '</div>';
    }
  };

  // Auto-init tickers if container exists
  document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('protocol-tickers')) {
      PievraProtocolTicker.render('protocol-tickers');
    }
  });

})();
