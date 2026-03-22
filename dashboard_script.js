var U=null;
var _allCampaigns=[];
var fmt=function(d){return d?new Date(d).toLocaleDateString('en-GB',{day:'numeric',month:'short',year:'numeric'}):'--';};
var greet=function(){var h=new Date().getHours();return h<12?'Good morning':h<18?'Good afternoon':'Good evening';};

function authFetch(url,opts){
  var tok=localStorage.getItem('pievra_token')||'';
  opts=opts||{};
  opts.credentials='include';
  if(tok){opts.headers=opts.headers||{};opts.headers['Authorization']='Bearer '+tok;}
  return fetch(url,opts);
}

function init(){
  authFetch('/auth/me').then(function(r){
    if(!r.ok){localStorage.removeItem('pievra_token');localStorage.removeItem('pievra_user');window.location='/signin';return null;}
    return r.json();
  }).then(function(u){
    if(!u)return;
    U=u;render(U);
    document.getElementById('load').style.display='none';
    loadCampaigns();
    if(new URLSearchParams(location.search).get('welcome')){
      al('st','Welcome! Your account is verified.','ok');
      history.replaceState({},'','/dashboard');
    }
  }).catch(function(){window.location='/signin';});
}

function render(u){
  var ini=u.email[0].toUpperCase();
  document.getElementById('av').textContent=ini;
  document.getElementById('dde').textContent=u.email;
  var pc=u.plan.charAt(0).toUpperCase()+u.plan.slice(1);
  document.getElementById('ddp').textContent=pc+' plan';
  document.getElementById('ntag').textContent=pc;
  if(u.plan==='pro')document.getElementById('ntag').classList.add('pro');
  document.getElementById('greet').textContent=greet()+' ';
  document.getElementById('osub').textContent='Welcome back, '+u.email;
  document.getElementById('aemail').textContent=u.email;
  document.getElementById('asince').textContent=fmt(u.created_at);
  document.getElementById('alast').textContent=u.last_login?fmt(u.last_login):'First session';
  var pf={community:'5 agents - All protocols - SDK - Sandbox',pro:'Unlimited agents - Analytics - PDF export - Priority support',enterprise:'Dedicated fleet - SSO - White-label - SLA'};
  document.getElementById('plfeats').textContent=pf[u.plan]||'';
  document.getElementById('plbadge').textContent='Plan: '+pc;
  document.getElementById('sem').value=u.email;
  document.getElementById('spl').value=pc;
  document.getElementById('ssi').value=fmt(u.created_at);
  updCards(u.plan);
}

function updCards(plan){
  var plans=['community','pro','enterprise'];
  plans.forEach(function(p,i){
    var c=document.getElementById('uc'+i),b=document.getElementById('pb'+i);
    if(!c||!b)return;
    if(p===plan){c.classList.add('cur');b.textContent='Current plan';b.disabled=true;b.className='btn bo';}
    else{c.classList.remove('cur');if(b.disabled){b.disabled=false;if(p==='pro'){b.textContent='Upgrade to Pro';b.className='btn bt';}else if(p==='community'){b.textContent='Get started';b.className='btn bo';}else{b.textContent='Contact sales';b.className='btn bi';}}}
  });
}

function go(id){
  document.querySelectorAll('.pnl').forEach(function(p){p.classList.remove('on');});
  document.querySelectorAll('.sb-btn').forEach(function(b){b.classList.remove('on');});
  var pm={overview:'pov',campaigns:'pca',protocols:'ppr',agents:'pag',plan:'ppl',settings:'pst',security:'pse'};
  var sm={overview:'sov',campaigns:'sca',protocols:'spr',agents:'sag',plan:'spl',settings:'sst',security:'sse'};
  var pel=document.getElementById(pm[id]);if(pel)pel.classList.add('on');
  var sel=document.getElementById(sm[id]);if(sel)sel.classList.add('on');
  document.getElementById('ddd').classList.remove('open');
  window.scrollTo(0,0);
  if(id==='campaigns')loadCampaigns();
}

function toggleDD(){document.getElementById('ddd').classList.toggle('open');}
document.addEventListener('click',function(e){if(!e.target.closest('.nwrap'))document.getElementById('ddd').classList.remove('open');});

function doLogout(){
  authFetch('/auth/logout',{method:'POST'}).then(function(){
    localStorage.removeItem('pievra_user');localStorage.removeItem('pievra_token');
    window.location='/signin';
  });
}

function upgr(plan){
  var i=['community','pro','enterprise'].indexOf(plan);
  var b=document.getElementById('pb'+i);
  b.innerHTML='...';b.disabled=true;
  authFetch('/auth/upgrade',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({plan:plan})})
  .then(function(r){return r.json().then(function(d){return{ok:r.ok,d:d};});})
  .then(function(res){
    if(!res.ok){al('pl',res.d.detail||'Failed.','er');return;}
    U.plan=plan;render(U);al('pl','Plan updated. Stripe payment coming soon.','ok');
  }).catch(function(){al('pl','Error.','er');})
  .finally(function(){b.disabled=false;updCards(U?U.plan:'community');});
}

function salesContact(){window.location='mailto:legal@pievra.com?subject=Enterprise%20Plan%20Enquiry';}

function changePw(){
  var p1=document.getElementById('sp1').value,p2=document.getElementById('sp2').value;
  if(p1.length<8){al('st','Password must be at least 8 characters.','er');return;}
  if(p1!==p2){al('st','Passwords do not match.','er');return;}
  authFetch('/auth/reset',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:U.email})})
  .then(function(){al('st','A reset link has been sent to '+U.email,'ok');document.getElementById('sp1').value='';document.getElementById('sp2').value='';})
  .catch(function(){al('st','Network error.','er');});
}

function exportData(){
  var d={email:U.email,plan:U.plan,member_since:U.created_at,last_login:U.last_login,exported_at:new Date().toISOString()};
  var a=document.createElement('a');
  a.href=URL.createObjectURL(new Blob([JSON.stringify(d,null,2)],{type:'application/json'}));
  a.download='pievra-data.json';a.click();
  al('st','Data downloaded.','ok');
}

function delAccount(){
  authFetch('/auth/account',{method:'DELETE'}).then(function(r){
    if(r.ok){localStorage.removeItem('pievra_user');localStorage.removeItem('pievra_token');window.location='/?deleted=1';}
  }).catch(function(){al('st','Error. Please try again.','er');});
}

function al(sec,msg,type){
  var m={ca:'camp-alert',pl:'apl',st:'ast',se:'ase'};
  var el=document.getElementById(m[sec]||'ast');if(!el)return;
  el.textContent=msg;el.className='alrt '+(type==='ok'?'aok':'aer');el.style.display='block';
  if(type==='ok')setTimeout(function(){el.style.display='none';},5000);
}

// CAMPAIGNS
function loadCampaigns(){
  authFetch('/api/campaigns')
  .then(function(r){return r.ok?r.json():null;})
  .then(function(d){
    if(!d)return;
    _allCampaigns=d.campaigns||[];
    var active=_allCampaigns.filter(function(c){return c.status==='active'||c.status==='paused';});
    var drafts=_allCampaigns.filter(function(c){return c.status==='draft';});
    renderList('camp-active-list',active,'active');
    renderList('camp-draft-list',drafts,'draft');
    var sc=document.getElementById('stat-campaigns');
    if(sc)sc.textContent=_allCampaigns.length;
  }).catch(function(){});
}

function showCampTab(tab){
  var btnA=document.getElementById('tab-active'),btnD=document.getElementById('tab-draft');
  var listA=document.getElementById('camp-active-list'),listD=document.getElementById('camp-draft-list');
  if(tab==='active'){
    if(btnA){btnA.style.background='var(--ink)';btnA.style.color='white';}
    if(btnD){btnD.style.background='none';btnD.style.color='var(--muted)';}
    if(listA)listA.style.display='block';if(listD)listD.style.display='none';
  } else {
    if(btnD){btnD.style.background='var(--ink)';btnD.style.color='white';}
    if(btnA){btnA.style.background='none';btnA.style.color='var(--muted)';}
    if(listD)listD.style.display='block';if(listA)listA.style.display='none';
  }
}

function renderList(cid,camps,type){
  var el=document.getElementById(cid);if(!el)return;
  if(!camps||!camps.length){
    el.innerHTML='<div style="text-align:center;padding:36px 20px;color:var(--muted)"><div style="font-size:32px;margin-bottom:10px">'+(type==='active'?'&#x1F5FA;':'&#x1F4CB;')+'</div><div style="font-size:15px;font-weight:600;color:var(--ink);margin-bottom:6px">No '+(type==='active'?'active':'draft')+' campaigns</div><a href="/#planner" style="display:inline-block;margin-top:12px;padding:10px 18px;background:var(--ink);color:#fff;border-radius:10px;text-decoration:none;font-weight:600;font-size:13px">+ New Campaign</a></div>';
    return;
  }
  el.innerHTML=camps.map(function(c){
    var p=c.plan_json||{},kpis=p.projected_kpis||{};
    var imp=kpis.estimated_impressions?parseInt(kpis.estimated_impressions).toLocaleString():'--';
    var cpm=kpis.estimated_cpm?'$'+kpis.estimated_cpm:'--';
    var roas=kpis.estimated_roas?kpis.estimated_roas+'x':'--';
    var sc={'active':'#166534','draft':'#713f12','paused':'#1e40af'}[c.status]||'#3d4460';
    var sb={'active':'#dcfce7','draft':'#fef9c3','paused':'#dbeafe'}[c.status]||'#f4f5f9';
    return '<div style="background:#fff;border:1px solid var(--border);border-radius:14px;padding:20px;margin-bottom:12px">'
      +'<div style="display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:12px">'
      +'<div><div style="font-family:Manrope,sans-serif;font-weight:700;font-size:15px;color:var(--ink)">'+(c.brand||'Untitled')+' - '+(c.campaign_name||'Campaign')+'</div>'
      +'<div style="font-size:12px;color:var(--muted);margin-top:3px">'+c.objective+' - '+c.buying_model+' - $'+c.budget+' - '+fmt(c.created_at)+'</div></div>'
      +'<div style="display:flex;align-items:center;gap:8px">'
      +'<span style="font-size:11px;font-weight:700;color:'+sc+';background:'+sb+';padding:3px 10px;border-radius:20px">'+c.status.toUpperCase()+'</span>'
      +'<button onclick="openEdit('+c.id+')" style="background:none;border:1px solid var(--border);color:var(--soft);font-size:12px;font-weight:600;padding:5px 12px;border-radius:8px;cursor:pointer">Edit</button>'
      +'</div></div>'
      +(kpis.estimated_impressions?'<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px">'
        +'<div style="background:var(--surf);border-radius:8px;padding:10px;text-align:center"><div style="font-weight:700;font-size:15px;color:#009e86">'+imp+'</div><div style="font-size:11px;color:var(--muted)">Impressions</div></div>'
        +'<div style="background:var(--surf);border-radius:8px;padding:10px;text-align:center"><div style="font-weight:700;font-size:15px;color:var(--ink)">'+cpm+'</div><div style="font-size:11px;color:var(--muted)">CPM</div></div>'
        +'<div style="background:var(--surf);border-radius:8px;padding:10px;text-align:center"><div style="font-weight:700;font-size:15px;color:var(--ink)">'+roas+'</div><div style="font-size:11px;color:var(--muted)">ROAS</div></div>'
        +'</div>':'')
      +'</div>';
  }).join('');
}

function openEdit(id){
  var c=_allCampaigns.find(function(x){return x.id===id;});if(!c)return;
  document.getElementById('edit-id').value=id;
  document.getElementById('edit-brand').value=c.brand||'';
  document.getElementById('edit-name').value=c.campaign_name||'';
  document.getElementById('edit-desc').value=c.description||'';
  document.getElementById('edit-budget').value=c.budget||'50000';
  document.getElementById('edit-kpi').value=c.kpi||'';
  document.getElementById('edit-obj').value=c.objective||'Awareness';
  document.getElementById('edit-buy').value=c.buying_model||'CPM';
  document.getElementById('edit-status').value=c.status||'active';
  document.getElementById('editmod').classList.add('open');
}

function saveEdit(){
  var id=document.getElementById('edit-id').value;if(!id)return;
  var data={brand:document.getElementById('edit-brand').value,campaign_name:document.getElementById('edit-name').value,description:document.getElementById('edit-desc').value,budget:document.getElementById('edit-budget').value,kpi:document.getElementById('edit-kpi').value,objective:document.getElementById('edit-obj').value,buying_model:document.getElementById('edit-buy').value,status:document.getElementById('edit-status').value,protocols:['AdCP','MCP','ARTF']};
  authFetch('/api/campaign/'+id,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)})
  .then(function(){document.getElementById('editmod').classList.remove('open');loadCampaigns();al('ca','Campaign updated.','ok');})
  .catch(function(){alert('Error saving.');});
}

function confirmDeleteCamp(){
  if(!confirm('Delete this campaign?'))return;
  var id=document.getElementById('edit-id').value;
  authFetch('/api/campaign/'+id,{method:'DELETE'})
  .then(function(){document.getElementById('editmod').classList.remove('open');loadCampaigns();})
  .catch(function(){alert('Error.');});
}

init();
