(function() {
  var user = null;

  function hidePlanner() {
    var gate = document.getElementById('plannerGate');
    if (gate) { gate.style.display='none'; gate.style.visibility='hidden'; gate.style.pointerEvents='none'; }
    var overlay = document.querySelector('.gate-overlay');
    if (overlay) overlay.style.display='none';
  }

  function updateNav(u) {
    var btn = document.querySelector('button.btn-ghost');
    if (btn) { btn.textContent='Dashboard'; btn.setAttribute('onclick',"window.location.href='/dashboard'"); }
  }

  function collectForm() {
    var brand = document.querySelector('input[placeholder*="Nike"]');
    var name = document.querySelector('input[placeholder*="Air Max"]');
    var desc = document.querySelector('textarea');
    var budget = document.querySelector('input[value="50000"]') || document.querySelector('input[placeholder*="budget"]');
    var kpi = document.querySelectorAll('input[type="text"]')[3];
    var activeObj = document.querySelector('.toggle-btn.active[onclick*="obj"]');
    var activeBuy = document.querySelector('.toggle-btn.active[onclick*="buy"]');
    var protocols = [];
    document.querySelectorAll('.toggle-btn.active[onclick*="proto"]').forEach(function(b){protocols.push(b.textContent.trim().split('\n')[0]);});
    if(!protocols.length) protocols=['AdCP','MCP','ARTF'];
    var envs=[];
    document.querySelectorAll('.toggle-btn.active[onclick*="env"]').forEach(function(b){envs.push(b.textContent.trim().split('\n')[0]);});
    if(!envs.length) envs=['CTV','Display'];
    return {
      brand: brand?brand.value.trim():'',
      campaign_name: name?name.value.trim():'',
      description: desc?desc.value.trim():'',
      budget: budget?budget.value.trim():'50000',
      kpi: kpi?kpi.value.trim():'',
      objective: activeObj?activeObj.querySelector('.sub,span')?activeObj.childNodes[0].textContent.trim():activeObj.textContent.trim():'Awareness',
      buying_model: activeBuy?activeBuy.childNodes[0].textContent.trim():'CPM',
      protocols: protocols,
      environments: envs
    };
  }

  function showResult(plan) {
    var existing = document.getElementById('campaign-result-panel');
    if (existing) existing.remove();

    var imp = parseInt(plan.projected_kpis.estimated_impressions).toLocaleString();
    var reach = parseInt(plan.projected_kpis.estimated_reach).toLocaleString();

    var panel = document.createElement('div');
    panel.id = 'campaign-result-panel';
    panel.style.cssText = 'background:#fff;border:2px solid #00c4a7;border-radius:16px;padding:32px;margin-top:24px;box-shadow:0 4px 24px rgba(0,196,167,0.15)';
    panel.innerHTML =
      '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:20px">' +
        '<div style="display:flex;align-items:center;gap:10px">' +
          '<div style="width:36px;height:36px;background:#00c4a7;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:18px">✅</div>' +
          '<div><div style="font-family:Manrope;font-weight:800;font-size:18px;color:#0a0e1a">Campaign Plan Generated</div>' +
          '<div style="font-size:13px;color:#7a829e">'+(plan.brand||'Your campaign')+' · '+plan.objective+'</div></div>' +
        '</div>' +
        '<a href="/dashboard" style="background:#0a0e1a;color:#00c4a7;font-weight:700;font-size:13px;padding:10px 18px;border-radius:10px;text-decoration:none">View in Dashboard →</a>' +
      '</div>' +
      '<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:20px">' +
        '<div style="background:#f4f5f9;border-radius:12px;padding:16px;text-align:center"><div style="font-family:Manrope;font-weight:800;font-size:22px;color:#009e86">'+imp+'</div><div style="font-size:12px;color:#7a829e;margin-top:4px">Est. Impressions</div></div>' +
        '<div style="background:#f4f5f9;border-radius:12px;padding:16px;text-align:center"><div style="font-family:Manrope;font-weight:800;font-size:22px;color:#0a0e1a">$'+plan.projected_kpis.estimated_cpm+'</div><div style="font-size:12px;color:#7a829e;margin-top:4px">Est. CPM</div></div>' +
        '<div style="background:#f4f5f9;border-radius:12px;padding:16px;text-align:center"><div style="font-family:Manrope;font-weight:800;font-size:22px;color:#0a0e1a">'+plan.projected_kpis.estimated_roas+'x</div><div style="font-size:12px;color:#7a829e;margin-top:4px">Est. ROAS</div></div>' +
        '<div style="background:#f4f5f9;border-radius:12px;padding:16px;text-align:center"><div style="font-family:Manrope;font-weight:800;font-size:22px;color:#0a0e1a">'+plan.arbitrage_saving.split('%')[0]+'%</div><div style="font-size:12px;color:#7a829e;margin-top:4px">CPM saving vs single-protocol</div></div>' +
      '</div>' +
      '<div style="margin-bottom:16px"><div style="font-size:13px;font-weight:600;color:#0a0e1a;margin-bottom:10px">RECOMMENDED AGENTS</div>' +
      plan.recommended_agents.map(function(a){
        return '<div style="display:flex;align-items:center;justify-content:space-between;padding:10px 14px;background:#f4f5f9;border-radius:10px;margin-bottom:6px">' +
          '<div><div style="font-size:14px;font-weight:600;color:#0a0e1a">'+a.name+'</div>' +
          '<div style="font-size:12px;color:#7a829e">'+a.protocol+' · Floor CPM $'+a.cpm_floor+'</div></div>' +
          '<div style="font-size:12px;font-weight:600;color:#166534;background:#dcfce7;padding:4px 10px;border-radius:20px">'+Math.round(a.viewability*100)+'% viewability</div>' +
        '</div>';
      }).join('') +
      '</div>' +
      '<div style="display:flex;gap:10px;align-items:center;padding:14px;background:#e0faf6;border-radius:10px;font-size:13px;color:#009e86;font-weight:600">' +
        '<span style="font-size:18px">⚡</span>' +
        'Cross-protocol arbitrage: '+plan.arbitrage_saving+' · '+plan.flight_recommendation +
      '</div>';

    // Insert after the generate button
    var genBtn = document.querySelector('.generate-btn');
    if (genBtn && genBtn.parentNode) {
      genBtn.parentNode.insertBefore(panel, genBtn.nextSibling);
      panel.scrollIntoView({behavior:'smooth', block:'start'});
    } else {
      document.getElementById('planner').appendChild(panel);
    }
  }

  function checkAuth() {
    return fetch('/auth/me', {credentials:'include', cache:'no-store'})
      .then(function(r){ return r.ok ? r.json() : null; })
      .then(function(u){
        if (u && u.email) { user=u; hidePlanner(); updateNav(u); }
        return user;
      }).catch(function(){ return null; });
  }

  window.pievraHandleGenerate = function() {
    checkAuth().then(function(u) {
      if (!u) { window.location.href='/signup'; return; }

      var btn = document.querySelector('.generate-btn');
      if (btn) { btn.textContent='Generating plan...'; btn.disabled=true; btn.style.opacity='0.7'; }

      var formData = collectForm();
      if (!formData.brand && !formData.campaign_name) {
        if (btn) { btn.textContent='Generate Campaign Plan'; btn.disabled=false; btn.style.opacity='1'; }
        alert('Please fill in at least the Brand and Campaign Name fields.');
        return;
      }

      fetch('/api/campaign', {
        method:'POST',
        credentials:'include',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify(formData)
      })
      .then(function(r){ return r.json(); })
      .then(function(d){
        if (d.plan) {
          showResult(d.plan);
          if (btn) { btn.textContent='✅ Plan Generated — Generate Again'; btn.disabled=false; btn.style.opacity='1'; }
        } else {
          alert('Error generating plan. Please try again.');
          if (btn) { btn.textContent='Generate Campaign Plan'; btn.disabled=false; btn.style.opacity='1'; }
        }
      })
      .catch(function(){
        alert('Network error. Please try again.');
        if (btn) { btn.textContent='Generate Campaign Plan'; btn.disabled=false; btn.style.opacity='1'; }
      });
    });
  };

  window.pievraHandleGetPlan = function() {
    if (user) { window.pievraHandleGenerate(); return; }
    var emailEl = document.querySelector('.gate-input-row input');
    var email = emailEl ? emailEl.value.trim() : '';
    if (!email || email.indexOf('@')===-1) { window.location.href='/signup'; return; }
    fetch('/api/signup', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({email:email, source:'campaign-planner'})})
    .then(function(){ hidePlanner(); var b=document.createElement('div'); b.style.cssText='position:fixed;top:80px;left:50%;transform:translateX(-50%);background:#00c4a7;color:#0a0e1a;font-weight:700;padding:14px 28px;border-radius:12px;z-index:9999;font-size:15px'; b.textContent='Check your inbox for your Pievra access link.'; document.body.appendChild(b); setTimeout(function(){b.remove();},6000); })
    .catch(function(){ window.location.href='/signup'; });
  };

  if (document.readyState==='loading') {
    document.addEventListener('DOMContentLoaded', checkAuth);
  } else { checkAuth(); }
})();
