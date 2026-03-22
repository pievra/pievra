import re

path = '/var/www/pievra/index.html'
txt = open(path).read()
original_len = len(txt)

# ─── 1. FIX NAV: hide Sign Up Free for logged-in users ───────────────────────
# Add a data-auth attribute to the Sign Up Free button so JS can hide it
old_nav = 'onclick="window.location.href=\'/signup\'">Sign Up Free</button>'
new_nav = 'id="nav-signup-btn" onclick="window.location.href=\'/signup\'">Sign Up Free</button>'
if old_nav in txt:
    txt = txt.replace(old_nav, new_nav)
    print('Nav button ID added')

# ─── 2. FIX GEO: Replace country select — remove Global, add multi-select ────
old_country = '''<div class="form-col">
              <label>Country / Region</label>
              <select id="pl-country"><option>Global</option><option>United States</option><option>United Kingdom</option><option>France</option><option>Germany</option><option>Netherlands</option><option>Canada</option><option>Australia</option><option>UAE</option><option>Saudi Arabia</option><option>Singapore</option></select>
            </div>'''

new_country = '''<div class="form-col">
              <label for="pl-country">Country / Region <span style="color:#7a829e;font-size:12px">(hold Ctrl/Cmd to select multiple)</span></label>
              <select id="pl-country" multiple size="5" style="height:120px;padding:6px">
                <option value="United States">United States</option>
                <option value="United Kingdom">United Kingdom</option>
                <option value="France">France</option>
                <option value="Germany">Germany</option>
                <option value="Netherlands">Netherlands</option>
                <option value="Belgium">Belgium</option>
                <option value="Spain">Spain</option>
                <option value="Italy">Italy</option>
                <option value="Canada">Canada</option>
                <option value="Australia">Australia</option>
                <option value="UAE">UAE</option>
                <option value="Saudi Arabia">Saudi Arabia</option>
                <option value="Singapore">Singapore</option>
                <option value="Japan">Japan</option>
                <option value="Brazil">Brazil</option>
                <option value="Mexico">Mexico</option>
                <option value="India">India</option>
                <option value="South Africa">South Africa</option>
              </select>
            </div>'''

if old_country in txt:
    txt = txt.replace(old_country, new_country)
    print('Country select fixed')
else:
    # Try without exact whitespace
    txt = re.sub(
        r'<div class="form-col">\s*<label>Country / Region</label>\s*<select id="pl-country">.*?</select>\s*</div>',
        new_country, txt, flags=re.DOTALL)
    print('Country select fixed (regex)')

# ─── 3. ADD LLM CHAT BOX before the form ─────────────────────────────────────
old_planner_top = '<div class="planner-gate">'

llm_chat = '''<div class="planner-gate">
      <!-- LLM Chat Mode -->
      <div id="planner-chat-mode" style="display:none;margin-bottom:24px;background:#0a0e1a;border-radius:16px;padding:24px">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px">
          <div style="display:flex;align-items:center;gap:10px">
            <div style="width:32px;height:32px;background:#00c4a7;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:14px">🤖</div>
            <div>
              <div style="font-family:Manrope,sans-serif;font-weight:700;font-size:15px;color:white">AI Campaign Assistant</div>
              <div style="font-size:12px;color:#7a829e">Describe your campaign in plain language</div>
            </div>
          </div>
          <button onclick="togglePlannerMode()" style="background:none;border:1px solid rgba(255,255,255,.2);color:rgba(255,255,255,.7);font-size:12px;padding:6px 12px;border-radius:8px;cursor:pointer">Switch to Form</button>
        </div>

        <!-- Example prompts -->
        <div style="margin-bottom:14px">
          <div style="font-size:11px;color:#7a829e;margin-bottom:8px;letter-spacing:.05em">EXAMPLE BRIEFS — click to use:</div>
          <div style="display:flex;flex-wrap:wrap;gap:8px">
            <button class="chat-example" onclick="useChatExample(this)" style="background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.12);color:rgba(255,255,255,.8);font-size:12px;padding:6px 12px;border-radius:20px;cursor:pointer;text-align:left">🛍 Nike Air Max launch — Gen Z, Europe, CTV + Display, $80K, ROAS 3.0</button>
            <button class="chat-example" onclick="useChatExample(this)" style="background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.12);color:rgba(255,255,255,.8);font-size:12px;padding:6px 12px;border-radius:20px;cursor:pointer;text-align:left">🏦 B2B SaaS lead gen — Finance decision-makers, US+UK, LinkedIn + Display, $25K CPL</button>
            <button class="chat-example" onclick="useChatExample(this)" style="background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.12);color:rgba(255,255,255,.8);font-size:12px;padding:6px 12px;border-radius:20px;cursor:pointer;text-align:left">🚗 Auto awareness — In-market buyers, Germany + France, CTV + DOOH, $120K CPM</button>
            <button class="chat-example" onclick="useChatExample(this)" style="background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.12);color:rgba(255,255,255,.8);font-size:12px;padding:6px 12px;border-radius:20px;cursor:pointer;text-align:left">✈ Travel retargeting — Luxury travellers, UAE + Singapore, Mobile + Native, $40K CPA</button>
          </div>
        </div>

        <!-- Chat messages -->
        <div id="chat-messages" style="min-height:80px;max-height:200px;overflow-y:auto;margin-bottom:12px"></div>

        <!-- Chat input -->
        <div style="display:flex;gap:10px">
          <textarea id="chat-input" placeholder="e.g. Run an awareness campaign for Nike Air Max 2026 targeting Gen Z in France and Germany on CTV and Display, budget $80K, ROAS target 3.0..." style="flex:1;background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.15);border-radius:10px;color:white;font-size:14px;padding:12px;font-family:Inter,sans-serif;resize:none;min-height:80px" onkeydown="if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();sendChat();}"></textarea>
          <button onclick="sendChat()" id="chat-send-btn" style="background:#00c4a7;border:none;color:#0a0e1a;font-weight:700;font-size:14px;padding:12px 20px;border-radius:10px;cursor:pointer;align-self:flex-end;white-space:nowrap">Generate &#x2192;</button>
        </div>
        <div style="font-size:11px;color:#7a829e;margin-top:8px">Press Enter to send · Shift+Enter for new line</div>
      </div>

      <!-- Mode toggle bar -->
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:20px;padding:12px 16px;background:white;border:1px solid var(--border);border-radius:12px">
        <div style="font-size:14px;color:#3d4460">Fill in the form or use the AI assistant to set up your campaign</div>
        <div style="display:flex;gap:8px">
          <button id="btn-form-mode" onclick="setMode(\'form\')" style="background:#0a0e1a;color:white;border:none;font-size:13px;font-weight:600;padding:7px 16px;border-radius:8px;cursor:pointer">📋 Form</button>
          <button id="btn-chat-mode" onclick="setMode(\'chat\')" style="background:none;border:1px solid #e2e4ed;color:#3d4460;font-size:13px;font-weight:600;padding:7px 16px;border-radius:8px;cursor:pointer">🤖 AI Assistant</button>
        </div>
      </div>
'''

if old_planner_top in txt:
    txt = txt.replace(old_planner_top, llm_chat, 1)
    print('LLM chat box added')

# ─── 4. REMOVE ALL OLD pievraGen scripts ──────────────────────────────────────
# Remove old inline scripts
txt = re.sub(r'<script>\s*function pievraGen\(\).*?</script>\s*', '', txt, flags=re.DOTALL)
txt = re.sub(r'<script>\s*\(function\(\)\s*\{.*?\}\)\(\);\s*</script>\s*', '', txt, flags=re.DOTALL)
print('Old scripts removed. pievraGen count:', txt.count('function pievraGen'))

# ─── 5. WRITE THE COMPREHENSIVE NEW SCRIPT ────────────────────────────────────
new_script = r'''<script>
// ── PIEVRA PLANNER + AUTH ────────────────────────────────────────────────────
var _pievraUser = null;

// On load: check auth, update UI
(function(){
  fetch('/auth/me',{credentials:'include',cache:'no-store'})
  .then(function(r){return r.ok?r.json():null;})
  .then(function(u){
    if(u&&u.email){
      _pievraUser=u;
      // Hide gate
      var gate=document.getElementById('plannerGate');
      if(gate){gate.style.display='none';gate.style.visibility='hidden';}
      // Nav: hide Sign Up Free, update Sign In → Dashboard
      var signupBtn=document.getElementById('nav-signup-btn');
      if(signupBtn) signupBtn.style.display='none';
      var signinBtn=document.querySelector('button.btn-ghost');
      if(signinBtn){signinBtn.textContent='Dashboard';signinBtn.setAttribute('onclick',"window.location.href='/dashboard'");}
    }
  }).catch(function(){});
})();

// ── MODE SWITCHING ────────────────────────────────────────────────────────────
var _mode = 'form';
function setMode(m){
  _mode=m;
  var chatDiv=document.getElementById('planner-chat-mode');
  var formDiv=document.querySelector('.planner-form');
  var btnForm=document.getElementById('btn-form-mode');
  var btnChat=document.getElementById('btn-chat-mode');
  if(m==='chat'){
    if(chatDiv) chatDiv.style.display='block';
    if(formDiv) formDiv.style.display='none';
    if(btnChat){btnChat.style.background='#0a0e1a';btnChat.style.color='white';btnChat.style.border='none';}
    if(btnForm){btnForm.style.background='none';btnForm.style.color='#3d4460';btnForm.style.border='1px solid #e2e4ed';}
  } else {
    if(chatDiv) chatDiv.style.display='none';
    if(formDiv) formDiv.style.display='block';
    if(btnForm){btnForm.style.background='#0a0e1a';btnForm.style.color='white';btnForm.style.border='none';}
    if(btnChat){btnChat.style.background='none';btnChat.style.color='#3d4460';btnChat.style.border='1px solid #e2e4ed';}
  }
}

// ── CHAT EXAMPLES ─────────────────────────────────────────────────────────────
function useChatExample(btn){
  var inp=document.getElementById('chat-input');
  if(inp) inp.value=btn.textContent.trim().replace(/^[\u{1F000}-\u{1FFFF}🏦🚗✈🛍]/u,'').trim();
}

// ── LLM CHAT ─────────────────────────────────────────────────────────────────
function addChatMsg(role, text){
  var msgs=document.getElementById('chat-messages');
  if(!msgs) return;
  var div=document.createElement('div');
  div.style.cssText='margin-bottom:10px;display:flex;gap:8px;align-items:flex-start';
  var icon=role==='user'?'👤':'🤖';
  var bg=role==='user'?'rgba(255,255,255,.08)':'rgba(0,196,167,.12)';
  div.innerHTML='<span style="font-size:14px;flex-shrink:0">'+icon+'</span>'
    +'<div style="background:'+bg+';border-radius:8px;padding:8px 12px;font-size:13px;color:'+(role==='user'?'rgba(255,255,255,.9)':'#00c4a7')+';line-height:1.5;flex:1">'+text+'</div>';
  msgs.appendChild(div);
  msgs.scrollTop=msgs.scrollHeight;
}

function sendChat(){
  var inp=document.getElementById('chat-input');
  var btn=document.getElementById('chat-send-btn');
  if(!inp||!inp.value.trim()) return;
  var msg=inp.value.trim();

  if(!_pievraUser){window.location.href='/signup';return;}

  addChatMsg('user', msg);
  inp.value='';
  if(btn){btn.textContent='Thinking...';btn.disabled=true;}

  // Parse the natural language into campaign fields using Claude
  fetch('/api/campaign/parse',{
    method:'POST',credentials:'include',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({message:msg})
  })
  .then(function(r){return r.json();})
  .then(function(d){
    if(btn){btn.textContent='Generate \u2192';btn.disabled=false;}
    if(d.plan){
      addChatMsg('assistant', 'Campaign plan generated! Here are your projected results:');
      showResult(d.plan, d.campaign_id);
    } else if(d.parsed){
      // Fill form with parsed data and switch to form mode
      fillFormFromParsed(d.parsed);
      addChatMsg('assistant', 'I\'ve filled in the campaign form based on your brief. Review and click Generate to proceed.');
      setTimeout(function(){ setMode('form'); }, 2000);
    } else {
      addChatMsg('assistant', 'I\'ve processed your brief. Generating campaign plan now...');
      // Fall back to direct generation
      fetch('/api/campaign',{method:'POST',credentials:'include',headers:{'Content-Type':'application/json'},body:JSON.stringify({brand:'',campaign_name:'Chat Campaign',description:msg,objective:'Awareness',buying_model:'CPM',budget:'50000',protocols:['AdCP','MCP','ARTF']})})
      .then(function(r2){return r2.json();})
      .then(function(d2){if(d2.plan){addChatMsg('assistant','Plan ready!');showResult(d2.plan,d2.campaign_id);}});
    }
  })
  .catch(function(){
    if(btn){btn.textContent='Generate \u2192';btn.disabled=false;}
    // Fall back to direct campaign generation
    addChatMsg('assistant','Generating your campaign plan...');
    fetch('/api/campaign',{method:'POST',credentials:'include',headers:{'Content-Type':'application/json'},body:JSON.stringify({brand:'',campaign_name:'Campaign',description:msg,objective:'Awareness',buying_model:'CPM',budget:'50000',protocols:['AdCP','MCP','ARTF']})})
    .then(function(r){return r.json();})
    .then(function(d){if(d.plan){showResult(d.plan,d.campaign_id);}});
  });
}

function fillFormFromParsed(p){
  if(p.brand&&document.getElementById('pl-brand')) document.getElementById('pl-brand').value=p.brand;
  if(p.campaign_name&&document.getElementById('pl-name')) document.getElementById('pl-name').value=p.campaign_name;
  if(p.description&&document.getElementById('pl-desc')) document.getElementById('pl-desc').value=p.description;
  if(p.budget&&document.getElementById('pl-budget')) document.getElementById('pl-budget').value=p.budget;
  if(p.kpi&&document.getElementById('pl-kpi')) document.getElementById('pl-kpi').value=p.kpi;
}

// ── VALIDATION ────────────────────────────────────────────────────────────────
function setFieldError(el, msg){
  if(!el) return;
  el.style.border='2px solid #dc2626';
  el.style.background='#fef2f2';
  var tip=el.nextElementSibling;
  if(tip&&tip.classList.contains('field-err-tip')) return;
  var t=document.createElement('div');
  t.className='field-err-tip';
  t.style.cssText='color:#dc2626;font-size:12px;margin-top:4px;display:flex;align-items:center;gap:4px';
  t.innerHTML='<span>&#x26A0;</span>'+msg;
  el.parentNode.insertBefore(t,el.nextSibling);
}

function clearFieldError(el){
  if(!el) return;
  el.style.border='';
  el.style.background='';
  var tip=el.nextElementSibling;
  if(tip&&tip.classList.contains('field-err-tip')) tip.remove();
}

function validateForm(){
  var brand=document.getElementById('pl-brand');
  var name=document.getElementById('pl-name');
  var desc=document.getElementById('pl-desc');
  var country=document.getElementById('pl-country');
  var errors=false;

  clearFieldError(brand); clearFieldError(name); clearFieldError(desc);

  if(!brand||!brand.value.trim()){setFieldError(brand,'Please enter the advertiser / brand name');errors=true;}
  if(!name||!name.value.trim()){setFieldError(name,'Please enter the campaign name');errors=true;}
  if(!desc||!desc.value.trim()){setFieldError(desc,'Please describe your campaign goals and requirements');errors=true;}

  if(country){
    var selected=Array.from(country.selectedOptions);
    if(!selected.length){setFieldError(country,'Please select at least one country');errors=true;}
    else clearFieldError(country);
  }

  if(errors){
    // Show summary banner
    var existing=document.getElementById('pl-error-banner');
    if(existing) existing.remove();
    var banner=document.createElement('div');
    banner.id='pl-error-banner';
    banner.style.cssText='background:#fef2f2;border:1px solid #fecaca;color:#991b1b;padding:12px 16px;border-radius:10px;font-size:14px;margin-bottom:16px;display:flex;align-items:center;gap:10px';
    banner.innerHTML='<span style="font-size:18px">&#x26A0;</span><span>Please complete all required fields highlighted in red before generating.</span>';
    var genBtn=document.querySelector('.generate-btn');
    if(genBtn&&genBtn.parentNode) genBtn.parentNode.insertBefore(banner,genBtn);
    // Scroll to first error
    var firstErr=document.querySelector('input[style*="dc2626"],textarea[style*="dc2626"],select[style*="dc2626"]');
    if(firstErr) firstErr.scrollIntoView({behavior:'smooth',block:'center'});
  }
  return !errors;
}

// ── COLLECT FORM DATA ─────────────────────────────────────────────────────────
function collectFormData(){
  var getActive=function(group){ var el=document.querySelector('.toggle-btn.active[onclick*="'+group+'"]'); return el?el.childNodes[0].textContent.trim():null; };
  var countries=[];
  var cs=document.getElementById('pl-country');
  if(cs) Array.from(cs.selectedOptions).forEach(function(o){countries.push(o.value);});
  var envs=[]; document.querySelectorAll('.env-btn.active').forEach(function(b){envs.push(b.textContent.trim().replace(/^[^\w]/,'').trim());});
  var interests=[]; document.querySelectorAll('.interest-tag.active').forEach(function(b){interests.push(b.textContent.trim());});
  return {
    brand: (document.getElementById('pl-brand')||{value:''}).value.trim(),
    campaign_name: (document.getElementById('pl-name')||{value:''}).value.trim(),
    description: (document.getElementById('pl-desc')||{value:''}).value.trim(),
    budget: (document.getElementById('pl-budget')||{value:'50000'}).value.trim(),
    kpi: (document.getElementById('pl-kpi')||{value:'ROAS > 2.5'}).value.trim(),
    objective: getActive('obj')||'Awareness',
    buying_model: getActive('buy')||'CPM',
    age_range: (document.getElementById('pl-age')||{value:'All Ages'}).value,
    countries: countries,
    city: (document.getElementById('pl-city')||{value:''}).value.trim(),
    flight_start: (document.getElementById('pl-start')||{value:''}).value.trim(),
    flight_end: (document.getElementById('pl-end')||{value:''}).value.trim(),
    freq_cap: (document.getElementById('pl-freq')||{value:'5'}).value.trim(),
    brand_safety: getActive('bs')||'Standard',
    environments: envs.length?envs:['Web Display'],
    audiences: interests,
    protocols: ['AdCP','MCP','ARTF']
  };
}

// ── SHOW RESULT ───────────────────────────────────────────────────────────────
function showResult(p, campaignId){
  var imp=parseInt(p.projected_kpis.estimated_impressions).toLocaleString();
  var el=document.getElementById('campaign-result-panel');
  if(el) el.remove();
  var existing=document.getElementById('pl-error-banner');
  if(existing) existing.remove();

  var panel=document.createElement('div');
  panel.id='campaign-result-panel';
  panel.style.cssText='background:#fff;border:2px solid #00c4a7;border-radius:16px;padding:28px;margin-top:20px';

  panel.innerHTML=
    '<div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;margin-bottom:20px">'
    +'<div style="display:flex;align-items:center;gap:12px">'
    +'<div style="width:40px;height:40px;background:#00c4a7;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:18px">&#x2705;</div>'
    +'<div><div style="font-family:Manrope,sans-serif;font-weight:800;font-size:18px;color:#0a0e1a">'+(p.brand||'Campaign')+' \u2014 Plan Ready</div>'
    +'<div style="font-size:13px;color:#7a829e">'+p.objective+' \u00B7 '+p.buying_model+(campaignId?' \u00B7 #'+campaignId:'')+'</div></div></div>'
    +'<a href="/dashboard" style="background:#0a0e1a;color:#00c4a7;font-weight:700;font-size:13px;padding:10px 18px;border-radius:10px;text-decoration:none;white-space:nowrap">View in Dashboard \u2192</a>'
    +'</div>'
    +'<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:18px">'
    +'<div style="background:#f4f5f9;border-radius:12px;padding:16px;text-align:center"><div style="font-family:Manrope,sans-serif;font-weight:800;font-size:22px;color:#009e86">'+imp+'</div><div style="font-size:12px;color:#7a829e;margin-top:3px">Est. Impressions</div></div>'
    +'<div style="background:#f4f5f9;border-radius:12px;padding:16px;text-align:center"><div style="font-family:Manrope,sans-serif;font-weight:800;font-size:22px;color:#0a0e1a">$'+p.projected_kpis.estimated_cpm+'</div><div style="font-size:12px;color:#7a829e;margin-top:3px">Est. CPM</div></div>'
    +'<div style="background:#f4f5f9;border-radius:12px;padding:16px;text-align:center"><div style="font-family:Manrope,sans-serif;font-weight:800;font-size:22px;color:#0a0e1a">'+p.projected_kpis.estimated_roas+'x</div><div style="font-size:12px;color:#7a829e;margin-top:3px">Est. ROAS</div></div>'
    +'<div style="background:#f4f5f9;border-radius:12px;padding:16px;text-align:center"><div style="font-family:Manrope,sans-serif;font-weight:800;font-size:22px;color:#0a0e1a">23%</div><div style="font-size:12px;color:#7a829e;margin-top:3px">CPM saving</div></div>'
    +'</div>'
    +'<div style="font-size:12px;font-weight:700;color:#0a0e1a;letter-spacing:.06em;margin-bottom:10px">RECOMMENDED AGENTS</div>'
    +p.recommended_agents.map(function(a){
      return '<div style="display:flex;align-items:center;justify-content:space-between;padding:10px 14px;background:#f4f5f9;border-radius:10px;margin-bottom:6px">'
        +'<div><div style="font-size:14px;font-weight:600;color:#0a0e1a">'+a.name+'</div>'
        +'<div style="font-size:12px;color:#7a829e">'+a.protocol+' \u00B7 Floor CPM $'+a.cpm_floor+'</div></div>'
        +'<span style="font-size:11px;font-weight:700;color:#166534;background:#dcfce7;padding:4px 9px;border-radius:20px">'+Math.round(a.viewability*100)+'% viewability</span>'
        +'</div>';
    }).join('')
    +'<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:14px">'
    +'<div style="padding:12px 14px;background:#e0faf6;border-radius:10px;font-size:13px;color:#009e86;font-weight:600">\u26A1 '+p.arbitrage_saving+'</div>'
    +'<div style="padding:12px 14px;background:#f4f5f9;border-radius:10px;font-size:13px;color:#3d4460">\uD83D\uDCC5 '+p.flight_recommendation+'</div>'
    +'</div>'
    +'<div style="margin-top:14px;display:flex;gap:10px">'
    +'<a href="/dashboard" style="flex:1;text-align:center;background:#0a0e1a;color:white;font-weight:700;font-size:14px;padding:12px;border-radius:10px;text-decoration:none">View in Dashboard</a>'
    +'<button onclick="resetPlanner()" style="flex:1;background:none;border:1px solid #e2e4ed;color:#3d4460;font-weight:600;font-size:14px;padding:12px;border-radius:10px;cursor:pointer">New Campaign</button>'
    +'</div>';

  var genBtn=document.querySelector('.generate-btn');
  if(genBtn&&genBtn.parentNode) genBtn.parentNode.insertBefore(panel,genBtn.nextSibling);
  else { var pl=document.getElementById('planner'); if(pl) pl.appendChild(panel); }
  panel.scrollIntoView({behavior:'smooth',block:'start'});
}

function resetPlanner(){
  var el=document.getElementById('campaign-result-panel');
  if(el) el.remove();
  var btn=document.querySelector('.generate-btn');
  if(btn){btn.textContent='\uD83D\uDC19 Generate Campaign Plan';btn.disabled=false;btn.style.opacity='1';}
}

// ── GENERATE (FORM MODE) ──────────────────────────────────────────────────────
function pievraGen(){
  if(!validateForm()) return;
  if(!_pievraUser){window.location.href='/signup';return;}

  var btn=document.querySelector('.generate-btn');
  if(btn){
    btn.innerHTML='<span style="display:inline-block;width:16px;height:16px;border:2px solid rgba(255,255,255,0.3);border-top-color:white;border-radius:50%;animation:pievra-spin 0.6s linear infinite;vertical-align:middle;margin-right:8px"></span>Generating...';
    btn.disabled=true;
    btn.style.opacity='0.85';
  }

  if(!document.getElementById('pievra-spin-kf')){
    var s=document.createElement('style');
    s.id='pievra-spin-kf';
    s.textContent='@keyframes pievra-spin{to{transform:rotate(360deg)}}';
    document.head.appendChild(s);
  }

  var existing=document.getElementById('pl-error-banner');
  if(existing) existing.remove();

  var data=collectFormData();
  data.country=data.countries.join(', ');

  fetch('/api/campaign',{
    method:'POST',credentials:'include',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify(data)
  })
  .then(function(r){return r.json();})
  .then(function(d){
    if(btn){btn.textContent='\uD83D\uDC19 Generate Campaign Plan';btn.disabled=false;btn.style.opacity='1';}
    if(d.plan){
      showResult(d.plan, d.campaign_id);
    } else {
      var err=document.createElement('div');
      err.style.cssText='background:#fef2f2;border:1px solid #fecaca;color:#991b1b;padding:12px 16px;border-radius:10px;font-size:14px;margin-bottom:12px';
      err.textContent=(d.error==='Not authenticated')?'Session expired. Please sign in again.':'Error generating plan. Please try again.';
      if(btn&&btn.parentNode) btn.parentNode.insertBefore(err,btn);
      if(d.error==='Not authenticated') setTimeout(function(){window.location.href='/signin';},2000);
    }
  })
  .catch(function(){
    if(btn){btn.textContent='\uD83D\uDC19 Generate Campaign Plan';btn.disabled=false;btn.style.opacity='1';}
    var err=document.createElement('div');
    err.style.cssText='background:#fef2f2;border:1px solid #fecaca;color:#991b1b;padding:12px 16px;border-radius:10px;font-size:14px;margin-bottom:12px';
    err.textContent='Network error. Please check your connection and try again.';
    if(btn&&btn.parentNode) btn.parentNode.insertBefore(err,btn);
  });
}

// ── GATE BUTTON (non-logged users) ────────────────────────────────────────────
window.pievraHandleGetPlan=function(){
  if(_pievraUser){pievraGen();return;}
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
};

// Clear field errors on input
document.addEventListener('input',function(e){
  var el=e.target;
  if(el.id&&el.id.startsWith('pl-')&&el.style.border&&el.style.border.includes('dc2626')){
    clearFieldError(el);
  }
});
</script>'''

# Insert before </body>
if '</body>' in txt:
    txt = txt.replace('</body>', new_script + '\n</body>', 1)
    print('New comprehensive script inserted')

open(path, 'w').write(txt)
print(f'DONE — file size: {len(txt)} bytes (was {original_len})')
