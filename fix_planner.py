import re, json

path = '/var/www/pievra/index.html'
txt = open(path).read()

# Step 1: Add IDs to all planner form fields
replacements = [
    # Brand input
    ('<div class="form-col"><label>Advertiser / Brand</label><input type="text" placeholder="e.g. Nike, Samsung, L\'Oréal..."/>',
     '<div class="form-col"><label for="pl-brand">Advertiser / Brand <span style="color:#dc2626">*</span></label><input type="text" id="pl-brand" placeholder="e.g. Nike, Samsung, L\'Oréal..."/>'),
    # Campaign name input
    ('<div class="form-col"><label>Product / Campaign Name</label><input type="text" placeholder="e.g. Air Max 2026 launch..."/>',
     '<div class="form-col"><label for="pl-name">Product / Campaign Name <span style="color:#dc2626">*</span></label><input type="text" id="pl-name" placeholder="e.g. Air Max 2026 launch..."/>'),
    # Description textarea
    ('<label>Campaign Description <span class="hint">— goals, messaging, requirements</span></label>\n            <textarea placeholder=',
     '<label for="pl-desc">Campaign Description <span class="hint">— goals, messaging, requirements</span> <span style="color:#dc2626">*</span></label>\n            <textarea id="pl-desc" placeholder='),
    # Budget
    ('<div class="form-col"><label>Budget (USD)</label><input type="text" value="50000"/>',
     '<div class="form-col"><label for="pl-budget">Budget (USD)</label><input type="text" id="pl-budget" value="50000"/>'),
    # KPI
    ('<div class="form-col"><label>KPI Target <span class="hint">— auto-suggested, edit freely</span></label><input type="text" value="ROAS > 2.5"/>',
     '<div class="form-col"><label for="pl-kpi">KPI Target <span class="hint">— auto-suggested, edit freely</span></label><input type="text" id="pl-kpi" value="ROAS > 2.5"/>'),
    # Age select
    ('<div class="form-col">\n              <label>Age Range</label>\n              <select>',
     '<div class="form-col">\n              <label>Age Range</label>\n              <select id="pl-age">'),
    # Country select
    ('<div class="form-col">\n              <label>Country / Region</label>\n              <select>',
     '<div class="form-col">\n              <label>Country / Region</label>\n              <select id="pl-country">'),
    # City input
    ('<div class="form-col"><label>City <span class="hint">— optional, for hyperlocal</span></label><input type="text" placeholder="e.g. Paris, Dubai, London..."/>',
     '<div class="form-col"><label for="pl-city">City <span class="hint">— optional, for hyperlocal</span></label><input type="text" id="pl-city" placeholder="e.g. Paris, Dubai, London..."/>'),
    # Flight start
    ('<div class="form-col"><label>Flight Start</label><input type="text" placeholder="YYYY-MM-DD"/>',
     '<div class="form-col"><label for="pl-start">Flight Start</label><input type="text" id="pl-start" placeholder="YYYY-MM-DD"/>'),
    # Flight end
    ('<div class="form-col"><label>Flight End</label><input type="text" placeholder="YYYY-MM-DD"/>',
     '<div class="form-col"><label for="pl-end">Flight End</label><input type="text" id="pl-end" placeholder="YYYY-MM-DD"/>'),
    # Frequency cap
    ('<div class="form-col"><label>Frequency Cap (per user)</label><input type="text" value="5"/>',
     '<div class="form-col"><label for="pl-freq">Frequency Cap (per user)</label><input type="text" id="pl-freq" value="5"/>'),
]

count = 0
for old, new in replacements:
    if old in txt:
        txt = txt.replace(old, new, 1)
        count += 1
        print(f'  Fixed: {old[:50]}...')
    else:
        print(f'  NOT FOUND: {old[:50]}...')

print(f'Added {count} IDs')

# Step 2: Remove the old inline pievraGen script and replace with clean version
old_script_marker = '<script>\nfunction pievraGen(){'
if old_script_marker in txt:
    # Find and remove the old inline script
    start = txt.find(old_script_marker)
    end = txt.find('</script>', start) + 9
    txt = txt[:start] + txt[end:]
    print('Removed old pievraGen script')

# Step 3: Write new clean pievraGen inline before </body>
new_gen = r"""<script>
function pievraGen(){
  var brand=document.getElementById('pl-brand');
  var name=document.getElementById('pl-name');
  var desc=document.getElementById('pl-desc');
  var btn=document.querySelector('.generate-btn');

  // Reset validation styles
  [brand,name,desc].forEach(function(el){
    if(el){el.style.border='';el.style.outline='';}
  });

  // Validate required fields
  var errors=[];
  if(!brand||!brand.value.trim()){
    errors.push('Brand');
    if(brand){brand.style.border='2px solid #dc2626';brand.focus();}
  }
  if(!name||!name.value.trim()){
    errors.push('Campaign Name');
    if(name) name.style.border='2px solid #dc2626';
    if(!brand||!brand.value.trim()) name && name.focus();
  }
  if(!desc||!desc.value.trim()){
    errors.push('Campaign Description');
    if(desc) desc.style.border='2px solid #dc2626';
  }

  if(errors.length){
    // Show inline error message
    var existing=document.getElementById('pl-error-msg');
    if(existing) existing.remove();
    var err=document.createElement('div');
    err.id='pl-error-msg';
    err.style.cssText='background:#fef2f2;border:1px solid #fecaca;color:#991b1b;padding:12px 16px;border-radius:10px;font-size:14px;margin-bottom:12px;display:flex;align-items:center;gap:10px';
    err.innerHTML='<span style="font-size:18px">&#x26A0;</span><span>Please complete the required fields: <strong>'+errors.join(', ')+'</strong></span>';
    if(btn&&btn.parentNode) btn.parentNode.insertBefore(err,btn);
    if(brand&&!brand.value.trim()) brand.scrollIntoView({behavior:'smooth',block:'center'});
    return;
  }

  // Check auth
  fetch('/auth/me',{credentials:'include',cache:'no-store'})
  .then(function(r){return r.ok?r.json():null;})
  .then(function(u){
    if(!u){window.location.href='/signup';return;}

    // Remove any previous error/result
    var ex=document.getElementById('pl-error-msg');
    if(ex) ex.remove();

    if(btn){btn.innerHTML='<span style="display:inline-block;width:16px;height:16px;border:2px solid rgba(255,255,255,0.3);border-top-color:white;border-radius:50%;animation:piev-spin 0.6s linear infinite;vertical-align:middle;margin-right:8px"></span>Generating plan...';btn.disabled=true;}

    // Add spinner keyframes if not present
    if(!document.getElementById('piev-spin-style')){
      var s=document.createElement('style');
      s.id='piev-spin-style';
      s.textContent='@keyframes piev-spin{to{transform:rotate(360deg)}}';
      document.head.appendChild(s);
    }

    // Collect all form data
    var activeObj=document.querySelector('.toggle-btn.active[onclick*="obj"]');
    var activeBuy=document.querySelector('.toggle-btn.active[onclick*="buy"]');
    var activeBS=document.querySelector('.toggle-btn.active[onclick*="bs"]');
    var envs=[]; document.querySelectorAll('.env-btn.active').forEach(function(b){envs.push(b.textContent.trim());});
    var interests=[]; document.querySelectorAll('.interest-tag.active').forEach(function(b){interests.push(b.textContent.trim());});

    var getFirstText=function(el){return el?el.childNodes[0]?el.childNodes[0].textContent.trim():el.textContent.trim():null;};

    var data={
      brand:brand.value.trim(),
      campaign_name:name.value.trim(),
      description:desc.value.trim(),
      budget:document.getElementById('pl-budget')?document.getElementById('pl-budget').value.trim():'50000',
      kpi:document.getElementById('pl-kpi')?document.getElementById('pl-kpi').value.trim():'ROAS > 2.5',
      objective:getFirstText(activeObj)||'Awareness',
      buying_model:getFirstText(activeBuy)||'CPM',
      age_range:document.getElementById('pl-age')?document.getElementById('pl-age').value:'All Ages',
      country:document.getElementById('pl-country')?document.getElementById('pl-country').value:'Global',
      city:document.getElementById('pl-city')?document.getElementById('pl-city').value:'',
      flight_start:document.getElementById('pl-start')?document.getElementById('pl-start').value:'',
      flight_end:document.getElementById('pl-end')?document.getElementById('pl-end').value:'',
      freq_cap:document.getElementById('pl-freq')?document.getElementById('pl-freq').value:'5',
      brand_safety:getFirstText(activeBS)||'Standard',
      environments:envs.length?envs:['Web Display'],
      audiences:interests,
      protocols:['AdCP','MCP','ARTF']
    };

    fetch('/api/campaign',{method:'POST',credentials:'include',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)})
    .then(function(r){return r.json();})
    .then(function(d){
      if(btn){btn.textContent='Generate Campaign Plan';btn.disabled=false;}
      if(!d.plan){
        var err2=document.createElement('div');
        err2.style.cssText='background:#fef2f2;border:1px solid #fecaca;color:#991b1b;padding:12px 16px;border-radius:10px;font-size:14px;margin-bottom:12px';
        err2.textContent='Error generating plan. Please try again.';
        if(btn&&btn.parentNode) btn.parentNode.insertBefore(err2,btn);
        return;
      }
      var p=d.plan;
      var imp=parseInt(p.projected_kpis.estimated_impressions).toLocaleString();
      var reach=parseInt(p.projected_kpis.estimated_reach).toLocaleString();
      var el=document.getElementById('campaign-result-panel');
      if(el) el.remove();
      var panel=document.createElement('div');
      panel.id='campaign-result-panel';
      panel.style.cssText='background:#fff;border:2px solid #00c4a7;border-radius:16px;padding:28px;margin-top:20px';
      panel.innerHTML='<div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;margin-bottom:20px">'
        +'<div style="display:flex;align-items:center;gap:12px">'
        +'<div style="width:40px;height:40px;background:#00c4a7;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:18px">&#x2705;</div>'
        +'<div><div style="font-family:Manrope,sans-serif;font-weight:800;font-size:18px;color:#0a0e1a">'+(p.brand||data.brand)+' &#x2014; Plan Ready</div>'
        +'<div style="font-size:13px;color:#7a829e">'+p.objective+' &middot; '+p.buying_model+' &middot; Campaign #'+d.campaign_id+'</div></div></div>'
        +'<a href="/dashboard" style="background:#0a0e1a;color:#00c4a7;font-weight:700;font-size:13px;padding:10px 18px;border-radius:10px;text-decoration:none;white-space:nowrap">View in Dashboard &#x2192;</a>'
        +'</div>'
        +'<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:18px">'
        +'<div style="background:#f4f5f9;border-radius:12px;padding:16px;text-align:center"><div style="font-family:Manrope,sans-serif;font-weight:800;font-size:22px;color:#009e86">'+imp+'</div><div style="font-size:12px;color:#7a829e;margin-top:3px">Est. Impressions</div></div>'
        +'<div style="background:#f4f5f9;border-radius:12px;padding:16px;text-align:center"><div style="font-family:Manrope,sans-serif;font-weight:800;font-size:22px;color:#0a0e1a">$'+p.projected_kpis.estimated_cpm+'</div><div style="font-size:12px;color:#7a829e;margin-top:3px">Est. CPM</div></div>'
        +'<div style="background:#f4f5f9;border-radius:12px;padding:16px;text-align:center"><div style="font-family:Manrope,sans-serif;font-weight:800;font-size:22px;color:#0a0e1a">'+p.projected_kpis.estimated_roas+'x</div><div style="font-size:12px;color:#7a829e;margin-top:3px">Est. ROAS</div></div>'
        +'<div style="background:#f4f5f9;border-radius:12px;padding:16px;text-align:center"><div style="font-family:Manrope,sans-serif;font-weight:800;font-size:22px;color:#0a0e1a">23%</div><div style="font-size:12px;color:#7a829e;margin-top:3px">CPM saving</div></div>'
        +'</div>'
        +'<div style="font-size:13px;font-weight:600;color:#0a0e1a;margin-bottom:10px">RECOMMENDED AGENTS</div>'
        +p.recommended_agents.map(function(a){
          return '<div style="display:flex;align-items:center;justify-content:space-between;padding:10px 14px;background:#f4f5f9;border-radius:10px;margin-bottom:6px">'
            +'<div><div style="font-size:14px;font-weight:600;color:#0a0e1a">'+a.name+'</div>'
            +'<div style="font-size:12px;color:#7a829e">'+a.protocol+' &middot; Floor CPM $'+a.cpm_floor+'</div></div>'
            +'<span style="font-size:11px;font-weight:700;color:#166534;background:#dcfce7;padding:4px 9px;border-radius:20px">'+Math.round(a.viewability*100)+'% viewability</span>'
            +'</div>';
        }).join('')
        +'<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:14px">'
        +'<div style="padding:12px 14px;background:#e0faf6;border-radius:10px;font-size:13px;color:#009e86;font-weight:600">&#x26A1; '+p.arbitrage_saving+'</div>'
        +'<div style="padding:12px 14px;background:#f4f5f9;border-radius:10px;font-size:13px;color:#3d4460">&#x1F4C5; '+p.flight_recommendation+'</div>'
        +'</div>'
        +'<div style="margin-top:14px;display:flex;gap:10px">'
        +'<a href="/dashboard" style="flex:1;text-align:center;background:#0a0e1a;color:white;font-weight:700;font-size:14px;padding:12px;border-radius:10px;text-decoration:none">View in Dashboard</a>'
        +'<button onclick="document.getElementById(\'campaign-result-panel\').remove();document.querySelector(\'.generate-btn\').textContent=\'Generate Campaign Plan\';" style="flex:1;background:none;border:1px solid #e2e4ed;color:#3d4460;font-weight:600;font-size:14px;padding:12px;border-radius:10px;cursor:pointer">New Campaign</button>'
        +'</div>';
      var genBtn=document.querySelector('.generate-btn');
      if(genBtn&&genBtn.parentNode){genBtn.parentNode.insertBefore(panel,genBtn.nextSibling);}
      else{document.getElementById('planner').appendChild(panel);}
      panel.scrollIntoView({behavior:'smooth',block:'start'});
      // Update nav
      var navBtn=document.querySelector('button.btn-ghost');
      if(navBtn){navBtn.textContent='Dashboard';navBtn.setAttribute('onclick',"window.location.href='/dashboard'");}
    })
    .catch(function(){
      if(btn){btn.textContent='Generate Campaign Plan';btn.disabled=false;}
      var err3=document.createElement('div');
      err3.style.cssText='background:#fef2f2;border:1px solid #fecaca;color:#991b1b;padding:12px 16px;border-radius:10px;font-size:14px;margin-bottom:12px';
      err3.textContent='Network error. Please check your connection and try again.';
      if(btn&&btn.parentNode) btn.parentNode.insertBefore(err3,btn);
    });
  }).catch(function(){window.location.href='/signup';});
}

// Also handle the gate "Get Plan" button for non-logged users
window.pievraHandleGetPlan = function(){
  fetch('/auth/me',{credentials:'include',cache:'no-store'})
  .then(function(r){return r.ok?r.json():null;})
  .then(function(u){
    if(u){pievraGen();return;}
    var emailEl=document.querySelector('.gate-input-row input');
    var email=emailEl?emailEl.value.trim():'';
    if(!email||email.indexOf('@')===-1){window.location.href='/signup';return;}
    fetch('/api/signup',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:email,source:'campaign-planner'})})
    .then(function(){
      var gate=document.getElementById('plannerGate');
      if(gate) gate.style.display='none';
      var b=document.createElement('div');
      b.style.cssText='position:fixed;top:80px;left:50%;transform:translateX(-50%);background:#00c4a7;color:#0a0e1a;font-weight:700;padding:14px 28px;border-radius:12px;z-index:9999;font-size:15px';
      b.textContent='Check your inbox for your Pievra access link.';
      document.body.appendChild(b);
      setTimeout(function(){b.remove();},6000);
    }).catch(function(){window.location.href='/signup';});
  });
};

// On load: check auth and hide gate if logged in
(function(){
  function checkAndUnlock(){
    fetch('/auth/me',{credentials:'include',cache:'no-store'})
    .then(function(r){return r.ok?r.json():null;})
    .then(function(u){
      if(u&&u.email){
        var gate=document.getElementById('plannerGate');
        if(gate){gate.style.display='none';gate.style.visibility='hidden';}
        var navBtn=document.querySelector('button.btn-ghost');
        if(navBtn){navBtn.textContent='Dashboard';navBtn.setAttribute('onclick',"window.location.href='/dashboard'");}
      }
    }).catch(function(){});
  }
  if(document.readyState==='loading'){document.addEventListener('DOMContentLoaded',checkAndUnlock);}
  else{checkAndUnlock();}
})();
</script>"""

# Insert before </body>
if '</body>' in txt:
    txt = txt.replace('</body>', new_gen + '\n</body>', 1)
    print('New pievraGen script inserted')

open(path, 'w').write(txt)
print('DONE')
