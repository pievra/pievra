var _pievraUser=null;
var _mode='form';

// Auth check on load
(function(){
  var tok=localStorage.getItem('pievra_token')||'';
  var opts={credentials:'include',cache:'no-store'};
  if(tok) opts.headers={'Authorization':'Bearer '+tok};
  fetch('/auth/me',opts)
  .then(function(r){return r.ok?r.json():null;})
  .then(function(u){
    if(u&&u.email){
      _pievraUser=u;
      var gate=document.getElementById('plannerGate');
      if(gate){gate.style.display='none';gate.style.visibility='hidden';}
      var sb=document.getElementById('nav-signup-btn');
      if(sb) sb.style.display='none';
      var si=document.querySelector('button.btn-ghost');
      if(si){si.textContent='Dashboard';si.setAttribute('onclick',"window.location.href='/dashboard'");}
    } else {
      var gate=document.getElementById('plannerGate');
      if(gate) gate.style.display='flex';
    }
  }).catch(function(){
    var gate=document.getElementById('plannerGate');
    if(gate) gate.style.display='flex';
  });
})();

function setMode(m){
  _mode=m;
  var cd=document.getElementById('planner-chat-mode');
  var fd=document.querySelector('.planner-form');
  var bf=document.getElementById('btn-form-mode');
  var bc=document.getElementById('btn-chat-mode');
  if(m==='chat'){
    if(cd) cd.style.display='block';
    if(fd) fd.style.display='none';
    if(bc){bc.style.background='#0a0e1a';bc.style.color='white';bc.style.border='none';}
    if(bf){bf.style.background='none';bf.style.color='#3d4460';bf.style.border='1px solid #e2e4ed';}
  } else {
    if(cd) cd.style.display='none';
    if(fd) fd.style.display='block';
    if(bf){bf.style.background='#0a0e1a';bf.style.color='white';bf.style.border='none';}
    if(bc){bc.style.background='none';bc.style.color='#3d4460';bc.style.border='1px solid #e2e4ed';}
  }
}

function useChatExample(btn){
  var inp=document.getElementById('chat-input');
  if(inp) inp.value=btn.textContent.trim();
}

function addChatMsg(role,text){
  var msgs=document.getElementById('chat-messages');
  if(!msgs) return;
  var d=document.createElement('div');
  d.style.cssText='margin-bottom:10px;display:flex;gap:8px;align-items:flex-start';
  var icon=role==='user'?'You':'AI';
  var bg=role==='user'?'rgba(255,255,255,.08)':'rgba(0,196,167,.12)';
  var color=role==='user'?'rgba(255,255,255,.9)':'#00c4a7';
  d.innerHTML='<span style="font-size:13px;font-weight:700;flex-shrink:0;color:'+color+'">'+icon+'</span>'
    +'<div style="background:'+bg+';border-radius:8px;padding:8px 12px;font-size:13px;color:'+color+';line-height:1.5;flex:1">'+text+'</div>';
  msgs.appendChild(d);
  msgs.scrollTop=msgs.scrollHeight;
}

function sendChat(){
  var inp=document.getElementById('chat-input');
  var btn=document.getElementById('chat-send-btn');
  if(!inp||!inp.value.trim()) return;
  var msg=inp.value.trim();
  var tok=localStorage.getItem('pievra_token')||'';
  var authOpts={credentials:'include',cache:'no-store'};
  if(tok) authOpts.headers={'Authorization':'Bearer '+tok};
  fetch('/auth/me',authOpts)
  .then(function(r){return r.ok?r.json():null;})
  .then(function(u){
    if(!u){window.location.href='/signup';return;}
    _pievraUser=u;
    addChatMsg('user',msg);
    inp.value='';
    if(btn){btn.textContent='Thinking...';btn.disabled=true;}
    var hdrs={'Content-Type':'application/json'};
    if(tok) hdrs['Authorization']='Bearer '+tok;
    fetch('/api/campaign/parse',{method:'POST',credentials:'include',headers:hdrs,body:JSON.stringify({message:msg})})
    .then(function(r){return r.json();})
    .then(function(d){
      if(btn){btn.textContent='Generate \u2192';btn.disabled=false;}
      if(d.plan){
        addChatMsg('assistant','Campaign plan generated!');
        showResult(d.plan,d.campaign_id);
      } else if(d.parsed){
        fillFormFromParsed(d.parsed);
        addChatMsg('assistant','Campaign form filled. Review and click Generate.');
        setTimeout(function(){setMode('form');},2000);
      } else {
        addChatMsg('assistant','Processing your brief...');
        var hdrs2={'Content-Type':'application/json'};
        if(tok) hdrs2['Authorization']='Bearer '+tok;
        fetch('/api/campaign',{method:'POST',credentials:'include',headers:hdrs2,body:JSON.stringify({brand:'',campaign_name:'Chat Campaign',description:msg,objective:'Awareness',buying_model:'CPM',budget:'50000',protocols:['AdCP','MCP','ARTF']})})
        .then(function(r){return r.json();})
        .then(function(d2){if(d2.plan){showResult(d2.plan,d2.campaign_id);}});
      }
    })
    .catch(function(){
      if(btn){btn.textContent='Generate \u2192';btn.disabled=false;}
      addChatMsg('assistant','Network error. Please try again.');
    });
  })
  .catch(function(){window.location.href='/signup';});
}

function fillFormFromParsed(p){
  if(p.brand&&document.getElementById('pl-brand')) document.getElementById('pl-brand').value=p.brand;
  if(p.campaign_name&&document.getElementById('pl-name')) document.getElementById('pl-name').value=p.campaign_name;
  if(p.description&&document.getElementById('pl-desc')) document.getElementById('pl-desc').value=p.description;
  if(p.budget&&document.getElementById('pl-budget')) document.getElementById('pl-budget').value=p.budget;
  if(p.kpi&&document.getElementById('pl-kpi')) document.getElementById('pl-kpi').value=p.kpi;
}

function setFieldError(el,msg){
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
  var errors=false;
  clearFieldError(brand);clearFieldError(name);clearFieldError(desc);
  if(!brand||!brand.value.trim()){setFieldError(brand,'Please enter the advertiser / brand name');errors=true;}
  if(!name||!name.value.trim()){setFieldError(name,'Please enter the campaign name');errors=true;}
  if(!desc||!desc.value.trim()){setFieldError(desc,'Please describe your campaign goals');errors=true;}
  if(errors){
    var ex=document.getElementById('pl-error-banner');
    if(ex) ex.remove();
    var banner=document.createElement('div');
    banner.id='pl-error-banner';
    banner.style.cssText='background:#fef2f2;border:1px solid #fecaca;color:#991b1b;padding:12px 16px;border-radius:10px;font-size:14px;margin-bottom:16px;display:flex;align-items:center;gap:10px';
    banner.innerHTML='<span style="font-size:18px">&#x26A0;</span><span>Please complete the required fields highlighted in red.</span>';
    var genBtn=document.querySelector('.generate-btn');
    if(genBtn&&genBtn.parentNode) genBtn.parentNode.insertBefore(banner,genBtn);
    var firstErr=document.querySelector('input[style*="dc2626"],textarea[style*="dc2626"]');
    if(firstErr) firstErr.scrollIntoView({behavior:'smooth',block:'center'});
  }
  return !errors;
}

function collectFormData(){
  var getActive=function(g){
    var el=document.querySelector('.toggle-btn.active[onclick*="'+g+'"]');
    return el?el.childNodes[0].textContent.trim():null;
  };
  var countries=[];
  var cs=document.getElementById('pl-country');
  if(cs) Array.from(cs.selectedOptions).forEach(function(o){countries.push(o.value);});
  var envs=[];
  document.querySelectorAll('.env-btn.active').forEach(function(b){envs.push(b.textContent.trim().replace(/^[^\w]/,'').trim());});
  var interests=[];
  document.querySelectorAll('.interest-tag.active').forEach(function(b){interests.push(b.textContent.trim());});
  return {
    brand:(document.getElementById('pl-brand')||{value:''}).value.trim(),
    campaign_name:(document.getElementById('pl-name')||{value:''}).value.trim(),
    description:(document.getElementById('pl-desc')||{value:''}).value.trim(),
    budget:(document.getElementById('pl-budget')||{value:'50000'}).value.trim(),
    kpi:(document.getElementById('pl-kpi')||{value:'ROAS > 2.5'}).value.trim(),
    objective:getActive('obj')||'Awareness',
    buying_model:getActive('buy')||'CPM',
    age_range:(document.getElementById('pl-age')||{value:'All Ages'}).value,
    countries:countries,
    city:(document.getElementById('pl-city')||{value:''}).value.trim(),
    flight_start:(document.getElementById('pl-start')||{value:''}).value.trim(),
    flight_end:(document.getElementById('pl-end')||{value:''}).value.trim(),
    brand_safety:getActive('bs')||'Standard',
    environments:envs.length?envs:['Web Display'],
    audiences:interests,
    protocols:['AdCP','MCP','ARTF']
  };
}

function showResult(p,campaignId){
  var imp=parseInt(p.projected_kpis.estimated_impressions).toLocaleString();
  var el=document.getElementById('campaign-result-panel');
  if(el) el.remove();
  var ex=document.getElementById('pl-error-banner');
  if(ex) ex.remove();
  var panel=document.createElement('div');
  panel.id='campaign-result-panel';
  panel.style.cssText='background:#fff;border:2px solid #00c4a7;border-radius:16px;padding:28px;margin-top:20px';
  panel.innerHTML=
    '<div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;margin-bottom:20px">'
    +'<div style="display:flex;align-items:center;gap:12px">'
    +'<div style="width:40px;height:40px;background:#00c4a7;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:18px">&#x2705;</div>'
    +'<div><div style="font-family:Manrope,sans-serif;font-weight:800;font-size:18px;color:#0a0e1a">'+(p.brand||'Campaign')+' Plan Ready</div>'
    +'<div style="font-size:13px;color:#7a829e">'+p.objective+' &middot; '+p.buying_model+(campaignId?' &middot; #'+campaignId:'')+'</div></div></div>'
    +'<a href="/dashboard" style="background:#0a0e1a;color:#00c4a7;font-weight:700;font-size:13px;padding:10px 18px;border-radius:10px;text-decoration:none;white-space:nowrap">Dashboard &#x2192;</a>'
    +'</div>'
    +'<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:18px">'
    +'<div style="background:#f4f5f9;border-radius:12px;padding:16px;text-align:center"><div style="font-family:Manrope,sans-serif;font-weight:800;font-size:22px;color:#009e86">'+imp+'</div><div style="font-size:12px;color:#7a829e;margin-top:3px">Impressions</div></div>'
    +'<div style="background:#f4f5f9;border-radius:12px;padding:16px;text-align:center"><div style="font-family:Manrope,sans-serif;font-weight:800;font-size:22px;color:#0a0e1a">$'+p.projected_kpis.estimated_cpm+'</div><div style="font-size:12px;color:#7a829e;margin-top:3px">CPM</div></div>'
    +'<div style="background:#f4f5f9;border-radius:12px;padding:16px;text-align:center"><div style="font-family:Manrope,sans-serif;font-weight:800;font-size:22px;color:#0a0e1a">'+p.projected_kpis.estimated_roas+'x</div><div style="font-size:12px;color:#7a829e;margin-top:3px">ROAS</div></div>'
    +'<div style="background:#f4f5f9;border-radius:12px;padding:16px;text-align:center"><div style="font-family:Manrope,sans-serif;font-weight:800;font-size:22px;color:#0a0e1a">23%</div><div style="font-size:12px;color:#7a829e;margin-top:3px">CPM saving</div></div>'
    +'</div>'
    +'<div style="font-size:12px;font-weight:700;color:#0a0e1a;letter-spacing:.06em;margin-bottom:10px">RECOMMENDED AGENTS</div>'
    +p.recommended_agents.map(function(a){
      return '<div style="display:flex;align-items:center;justify-content:space-between;padding:10px 14px;background:#f4f5f9;border-radius:10px;margin-bottom:6px">'
        +'<div><div style="font-size:14px;font-weight:600;color:#0a0e1a">'+a.name+'</div>'
        +'<div style="font-size:12px;color:#7a829e">'+a.protocol+' &middot; Floor $'+a.cpm_floor+'</div></div>'
        +'<span style="font-size:11px;font-weight:700;color:#166534;background:#dcfce7;padding:4px 9px;border-radius:20px">'+Math.round(a.viewability*100)+'% viewability</span>'
        +'</div>';
    }).join('')
    +'<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:14px">'
    +'<div style="padding:12px 14px;background:#e0faf6;border-radius:10px;font-size:13px;color:#009e86;font-weight:600">&#x26A1; '+p.arbitrage_saving+'</div>'
    +'<div style="padding:12px 14px;background:#f4f5f9;border-radius:10px;font-size:13px;color:#3d4460">'+p.flight_recommendation+'</div>'
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
  if(btn){btn.textContent='Generate Campaign Plan';btn.disabled=false;btn.style.opacity='1';}
}

function pievraGen(){
  if(!validateForm()) return;
  var tok=localStorage.getItem('pievra_token')||'';
  var opts={credentials:'include',cache:'no-store'};
  if(tok) opts.headers={'Authorization':'Bearer '+tok};
  fetch('/auth/me',opts)
  .then(function(r){return r.ok?r.json():null;})
  .then(function(u){
    if(!u){window.location.href='/signup';return;}
    _pievraUser=u;
    var gate=document.getElementById('plannerGate');
    if(gate){gate.style.display='none';gate.style.visibility='hidden';}
    var btn=document.querySelector('.generate-btn');
    if(btn){btn.textContent='Generating...';btn.disabled=true;btn.style.opacity='0.85';}
    var ex=document.getElementById('pl-error-banner');
    if(ex) ex.remove();
    var data=collectFormData();
    data.country=data.countries.join(', ');
    var hdrs={'Content-Type':'application/json'};
    if(tok) hdrs['Authorization']='Bearer '+tok;
    fetch('/api/campaign',{method:'POST',credentials:'include',headers:hdrs,body:JSON.stringify(data)})
    .then(function(r){return r.json();})
    .then(function(d){
      if(btn){btn.textContent='Generate Campaign Plan';btn.disabled=false;btn.style.opacity='1';}
      if(d.plan){
        showResult(d.plan,d.campaign_id);
      } else {
        var err=document.createElement('div');
        err.style.cssText='background:#fef2f2;border:1px solid #fecaca;color:#991b1b;padding:12px 16px;border-radius:10px;font-size:14px;margin-bottom:12px';
        err.textContent=d.error==='Not authenticated'?'Session expired. Please sign in again.':'Error generating plan. Please try again.';
        if(btn&&btn.parentNode) btn.parentNode.insertBefore(err,btn);
        if(d.error==='Not authenticated') setTimeout(function(){window.location.href='/signin';},2000);
      }
    })
    .catch(function(){
      if(btn){btn.textContent='Generate Campaign Plan';btn.disabled=false;btn.style.opacity='1';}
      var err=document.createElement('div');
      err.style.cssText='background:#fef2f2;border:1px solid #fecaca;color:#991b1b;padding:12px 16px;border-radius:10px;font-size:14px;margin-bottom:12px';
      err.textContent='Network error. Please try again.';
      if(btn&&btn.parentNode) btn.parentNode.insertBefore(err,btn);
    });
  })
  .catch(function(){window.location.href='/signup';});
}

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

document.addEventListener('input',function(e){
  var el=e.target;
  if(el.id&&el.id.startsWith('pl-')&&el.style.border&&el.style.border.includes('dc2626')){
    clearFieldError(el);
  }
});
