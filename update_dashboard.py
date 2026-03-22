import re

path = '/var/www/pievra/dashboard/index.html'
txt = open(path).read()

# Find the campaigns panel and replace with full campaign management UI
old_campaigns = '''    <!-- CAMPAIGNS -->
    <div class="pnl" id="pca">
      <div class="ptitle">Campaigns</div><div class="psub">Your cross-protocol campaign history</div>
      <div class="card"><div class="empty"><div class="ei">&#x1F5FA;</div><div class="et">No campaigns yet</div><div class="eb">Plan your first campaign using the Campaign Planner. Pievra auto-selects the optimal protocol stack.</div>
      <a href="/#planner" style="display:inline-block;margin-top:14px;padding:10px 20px;background:var(--ink);color:#fff;border-radius:10px;text-decoration:none;font-weight:600;font-size:14px">Plan a campaign &#x2192;</a></div></div>
    </div>'''

new_campaigns = '''    <!-- CAMPAIGNS -->
    <div class="pnl" id="pca">
      <div class="ptitle">Campaigns</div>
      <div class="psub">Your active and draft campaigns</div>
      <div id="camp-alert" class="alrt" style="display:none"></div>

      <!-- Tabs -->
      <div style="display:flex;gap:0;border:1px solid var(--border);border-radius:10px;overflow:hidden;margin-bottom:20px;width:fit-content">
        <button id="tab-active" onclick="showCampTab('active')" style="padding:9px 20px;background:var(--ink);color:white;border:none;font-size:13px;font-weight:600;cursor:pointer">Active</button>
        <button id="tab-draft" onclick="showCampTab('draft')" style="padding:9px 20px;background:none;border:none;font-size:13px;font-weight:600;color:var(--muted);cursor:pointer">Drafts</button>
      </div>

      <div id="camp-active-list"></div>
      <div id="camp-draft-list" style="display:none"></div>

      <div style="margin-top:16px">
        <a href="/#planner" style="display:inline-flex;align-items:center;gap:8px;background:var(--ink);color:white;font-weight:600;font-size:14px;padding:11px 20px;border-radius:10px;text-decoration:none">
          + New Campaign
        </a>
      </div>
    </div>

    <!-- CAMPAIGN EDIT MODAL -->
    <div class="moverlay" id="editmod">
      <div class="mbox" style="max-width:600px;width:95%;max-height:90vh;overflow-y:auto">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:20px">
          <h3 style="font-family:Manrope;font-weight:800;font-size:17px;color:var(--ink)">Edit Campaign</h3>
          <button onclick="document.getElementById('editmod').classList.remove('open')" style="background:none;border:none;font-size:20px;cursor:pointer;color:var(--muted)">&#x00D7;</button>
        </div>
        <input type="hidden" id="edit-id"/>
        <div class="fr"><label class="fl">Brand / Advertiser</label><input class="fi" id="edit-brand" type="text" placeholder="e.g. Nike"/></div>
        <div class="fr"><label class="fl">Campaign Name</label><input class="fi" id="edit-name" type="text" placeholder="e.g. Air Max 2026 Launch"/></div>
        <div class="fr"><label class="fl">Description</label><textarea class="fi" id="edit-desc" rows="3" style="resize:vertical" placeholder="Campaign goals, messaging, requirements..."></textarea></div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:14px">
          <div><label class="fl">Budget (USD)</label><input class="fi" id="edit-budget" type="text"/></div>
          <div><label class="fl">KPI Target</label><input class="fi" id="edit-kpi" type="text"/></div>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:14px">
          <div><label class="fl">Objective</label>
            <select class="fi" id="edit-obj">
              <option>Awareness</option><option>Consideration</option><option>Conversion</option><option>Retention</option>
            </select>
          </div>
          <div><label class="fl">Buying Model</label>
            <select class="fi" id="edit-buy">
              <option>CPM</option><option>CPC</option><option>CPA</option><option>CPL</option><option>CPCV</option>
            </select>
          </div>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:14px">
          <div><label class="fl">Status</label>
            <select class="fi" id="edit-status">
              <option value="active">Active</option>
              <option value="draft">Draft</option>
              <option value="paused">Paused</option>
            </select>
          </div>
          <div><label class="fl">&nbsp;</label>
            <button class="btn br" style="width:100%" onclick="confirmDeleteCamp()">Delete Campaign</button>
          </div>
        </div>
        <div style="display:flex;gap:10px;margin-top:4px">
          <button class="btn bo" style="flex:1" onclick="document.getElementById('editmod').classList.remove('open')">Cancel</button>
          <button class="btn bi" style="flex:1" onclick="saveEditCamp()">Save Changes</button>
        </div>
      </div>
    </div>'''

if old_campaigns in txt:
    txt = txt.replace(old_campaigns, new_campaigns)
    print("Campaigns panel replaced")
else:
    print("NOT FOUND - trying partial match")
    idx = txt.find('id="pca"')
    if idx > 0:
        print(f"Found pca at {idx}")
        print(txt[idx:idx+200])

# Update the overview stat to load from API
old_stat = '<div class="stat"><div class="sv t">0</div><div class="sl">Campaigns</div></div>'
new_stat = '<div class="stat"><div class="sv t" id="stat-campaigns">0</div><div class="sl">Campaigns</div></div>'
txt = txt.replace(old_stat, new_stat, 1)

# Replace the campaigns JS section in the init script
old_js_marker = 'function nav(id){'
new_campaign_js = '''
var _allCampaigns = [];
var _campTab = 'active';

function showCampTab(tab){
  _campTab = tab;
  var btnA=document.getElementById('tab-active');
  var btnD=document.getElementById('tab-draft');
  var listA=document.getElementById('camp-active-list');
  var listD=document.getElementById('camp-draft-list');
  if(tab==='active'){
    if(btnA){btnA.style.background='var(--ink)';btnA.style.color='white';}
    if(btnD){btnD.style.background='none';btnD.style.color='var(--muted)';}
    if(listA) listA.style.display='block';
    if(listD) listD.style.display='none';
  } else {
    if(btnD){btnD.style.background='var(--ink)';btnD.style.color='white';}
    if(btnA){btnA.style.background='none';btnA.style.color='var(--muted)';}
    if(listA) listA.style.display='none';
    if(listD) listD.style.display='block';
  }
}

function loadCampaigns(){
  fetch('/api/campaigns',{credentials:'include'})
  .then(function(r){return r.ok?r.json():null;})
  .then(function(d){
    if(!d||!d.campaigns) return;
    _allCampaigns = d.campaigns;
    var active=d.campaigns.filter(function(c){return c.status==='active'||c.status==='paused';});
    var drafts=d.campaigns.filter(function(c){return c.status==='draft';});
    renderCampList('camp-active-list', active, 'active');
    renderCampList('camp-draft-list', drafts, 'draft');
    // Update stat
    var sc=document.getElementById('stat-campaigns');
    if(sc) sc.textContent=d.campaigns.length;
  }).catch(function(){});
}

var statusColor={'active':'#166534','draft':'#713f12','paused':'#1e40af'};
var statusBg={'active':'#dcfce7','draft':'#fef9c3','paused':'#dbeafe'};

function renderCampList(containerId, camps, type){
  var el=document.getElementById(containerId);
  if(!el) return;
  if(!camps.length){
    el.innerHTML='<div style="text-align:center;padding:36px 20px;color:var(--muted)">'
      +'<div style="font-size:32px;margin-bottom:10px">'+(type==='active'?'🗺':'📋')+'</div>'
      +'<div style="font-size:15px;font-weight:600;color:var(--ink);margin-bottom:6px">No '+(type==='active'?'active':'draft')+' campaigns</div>'
      +'<div style="font-size:13px">'+  (type==='active'?'Generate your first campaign in the Campaign Planner':'Save a campaign as draft to work on it later')+'</div>'
      +'<a href="/#planner" style="display:inline-block;margin-top:14px;padding:10px 18px;background:var(--ink);color:#fff;border-radius:10px;text-decoration:none;font-weight:600;font-size:13px">+ New Campaign</a>'
      +'</div>';
    return;
  }
  el.innerHTML=camps.map(function(c){
    var plan=c.plan_json||{};
    var kpis=plan.projected_kpis||{};
    var imp=kpis.estimated_impressions?parseInt(kpis.estimated_impressions).toLocaleString():'—';
    var cpm=kpis.estimated_cpm?'$'+kpis.estimated_cpm:'—';
    var roas=kpis.estimated_roas?kpis.estimated_roas+'x':'—';
    var date=c.created_at?new Date(c.created_at).toLocaleDateString('en-GB',{day:'numeric',month:'short',year:'numeric'}):'—';
    var sc=statusColor[c.status]||'#3d4460';
    var sb=statusBg[c.status]||'#f4f5f9';
    return '<div style="background:#fff;border:1px solid var(--border);border-radius:14px;padding:20px;margin-bottom:12px">'
      +'<div style="display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:12px">'
      +'<div>'
      +'<div style="font-family:Manrope,sans-serif;font-weight:700;font-size:15px;color:var(--ink)">'+(c.brand||'Untitled')+' — '+(c.campaign_name||'Campaign')+'</div>'
      +'<div style="font-size:12px;color:var(--muted);margin-top:3px">'+c.objective+' &middot; '+c.buying_model+' &middot; $'+c.budget+' budget &middot; Created '+date+'</div>'
      +'</div>'
      +'<div style="display:flex;align-items:center;gap:8px">'
      +'<span style="font-size:11px;font-weight:700;color:'+sc+';background:'+sb+';padding:3px 10px;border-radius:20px">'+c.status.toUpperCase()+'</span>'
      +'<button onclick="openEditCamp('+c.id+')" style="background:none;border:1px solid var(--border);color:var(--soft);font-size:12px;font-weight:600;padding:5px 12px;border-radius:8px;cursor:pointer">Edit</button>'
      +'</div></div>'
      +(kpis.estimated_impressions?'<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px">'
        +'<div style="background:var(--surf);border-radius:8px;padding:10px;text-align:center"><div style="font-weight:700;font-size:15px;color:#009e86">'+imp+'</div><div style="font-size:11px;color:var(--muted)">Est. Impressions</div></div>'
        +'<div style="background:var(--surf);border-radius:8px;padding:10px;text-align:center"><div style="font-weight:700;font-size:15px;color:var(--ink)">'+cpm+'</div><div style="font-size:11px;color:var(--muted)">Est. CPM</div></div>'
        +'<div style="background:var(--surf);border-radius:8px;padding:10px;text-align:center"><div style="font-weight:700;font-size:15px;color:var(--ink)">'+roas+'</div><div style="font-size:11px;color:var(--muted)">Est. ROAS</div></div>'
        +'</div>':'')
      +'</div>';
  }).join('');
}

function openEditCamp(id){
  var c=_allCampaigns.find(function(x){return x.id===id;});
  if(!c) return;
  var fd=c.form_data||{};
  document.getElementById('edit-id').value=id;
  document.getElementById('edit-brand').value=c.brand||'';
  document.getElementById('edit-name').value=c.campaign_name||'';
  document.getElementById('edit-desc').value=c.description||fd.description||'';
  document.getElementById('edit-budget').value=c.budget||'50000';
  document.getElementById('edit-kpi').value=c.kpi||fd.kpi||'';
  document.getElementById('edit-obj').value=c.objective||'Awareness';
  document.getElementById('edit-buy').value=c.buying_model||'CPM';
  document.getElementById('edit-status').value=c.status||'active';
  document.getElementById('editmod').classList.add('open');
}

function saveEditCamp(){
  var id=document.getElementById('edit-id').value;
  if(!id) return;
  var data={
    brand:document.getElementById('edit-brand').value,
    campaign_name:document.getElementById('edit-name').value,
    description:document.getElementById('edit-desc').value,
    budget:document.getElementById('edit-budget').value,
    kpi:document.getElementById('edit-kpi').value,
    objective:document.getElementById('edit-obj').value,
    buying_model:document.getElementById('edit-buy').value,
    status:document.getElementById('edit-status').value,
    protocols:['AdCP','MCP','ARTF']
  };
  fetch('/api/campaign/'+id,{method:'PUT',credentials:'include',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)})
  .then(function(r){return r.json();})
  .then(function(d){
    document.getElementById('editmod').classList.remove('open');
    loadCampaigns();
    var a=document.getElementById('camp-alert');
    if(a){a.textContent='Campaign updated successfully.';a.className='alrt aok';a.style.display='block';setTimeout(function(){a.style.display='none';},4000);}
  }).catch(function(){alert('Error saving. Please try again.');});
}

function confirmDeleteCamp(){
  var id=document.getElementById('edit-id').value;
  if(!id) return;
  if(!confirm('Delete this campaign? This cannot be undone.')) return;
  fetch('/api/campaign/'+id,{method:'DELETE',credentials:'include'})
  .then(function(){
    document.getElementById('editmod').classList.remove('open');
    loadCampaigns();
  }).catch(function(){alert('Error deleting.');});
}

function nav(id){'''

if old_js_marker in txt:
    txt = txt.replace(old_js_marker, new_campaign_js)
    print("Campaign JS inserted")

# Add loadCampaigns() call to init
old_init_end = 'document.getElementById(\'load\').style.display=\'none\';'
new_init_end = 'document.getElementById(\'load\').style.display=\'none\';\n    loadCampaigns();'
if old_init_end in txt:
    txt = txt.replace(old_init_end, new_init_end, 1)
    print("loadCampaigns() added to init")

open(path, 'w').write(txt)
print(f"DONE — {len(txt)} bytes")
