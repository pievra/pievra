path = '/var/www/pievra/advertise.html'
txt = open(path).read()

# 1. Replace placement plan section in the form
old_plan_field = '''    <div class="field"><label>Placement plan</label>
      <select id="plan">
        <option value="Standard - $500/mo">Standard — $500/month</option>
        <option value="Pro - $1,500/mo">Pro — $1,500/month</option>
        <option value="Enterprise - Custom">Enterprise — Custom pricing</option>
      </select>
    </div>'''

new_plan_field = '''    <div class="field"><label>Placement type</label>
      <select id="plan">
        <option value="Standard Listing - $0.07 CPI">Standard Listing — $0.07 CPI &middot; $25/day min</option>
        <option value="Hero Placement - $0.18 CPI">Hero Placement — $0.18 CPI &middot; $50/day min</option>
        <option value="Sponsored Newsletter - $0.35 CPI">Sponsored Newsletter — $0.35 CPI &middot; $100/send min</option>
        <option value="Enterprise - Managed Campaign">Enterprise — Managed Campaign (custom rate)</option>
      </select>
    </div>
    <div class="field">
      <label>Daily budget (USD)</label>
      <input type="number" id="daily-budget" placeholder="e.g. 50" min="25" step="25"/>
      <div style="font-size:12px;color:var(--muted);margin-top:4px">Minimum $25/day for Standard, $50/day for Hero. Leave blank for Newsletter or Enterprise.</div>
    </div>
    <div class="field">
      <label style="display:flex;align-items:flex-start;gap:8px;cursor:pointer;font-weight:400;color:var(--soft)">
        <input type="checkbox" id="need-invoice" style="width:16px;height:16px;margin-top:2px;accent-color:var(--teal);flex-shrink:0"/>
        <span>I need a VAT / tax invoice for this campaign. Invoices are issued within 5 business days of each billing period. <strong style="color:var(--ink)">Please include your company name, registered address and VAT number in the description field below.</strong></span>
      </label>
    </div>
    <div class="field">
      <label style="display:flex;align-items:flex-start;gap:8px;cursor:pointer;font-weight:400;color:var(--soft)">
        <input type="checkbox" id="agree-tc" style="width:16px;height:16px;margin-top:2px;accent-color:var(--teal);flex-shrink:0"/>
        <span>I have read and agree to the <a href="/advertising-terms" target="_blank" style="color:var(--teal);font-weight:600">Advertising Terms &amp; Conditions</a> and <a href="/privacy" target="_blank" style="color:var(--teal);font-weight:600">Privacy Policy</a>. <strong style="color:#dc2626">Required.</strong></span>
      </label>
    </div>'''

if old_plan_field in txt:
    txt = txt.replace(old_plan_field, new_plan_field)
    print('Plan field updated')
else:
    print('Plan field NOT FOUND')

# 2. Update submitForm to include new fields + T&C validation
old_submit = '''  var fname = document.getElementById('fname').value.trim();
  var lname = document.getElementById('lname').value.trim();
  var email = document.getElementById('email').value.trim();
  var company = document.getElementById('company').value.trim();
  var plan = document.getElementById('plan').value;
  var desc = document.getElementById('desc').value.trim();
  var err = document.getElementById('err');
  var btn = document.getElementById('sbtn');

  err.style.display = 'none';
  if(!fname || !lname){err.textContent='Please enter your full name.';err.style.display='block';return;}
  if(!email || email.indexOf('@') === -1){err.textContent='Please enter a valid work email.';err.style.display='block';return;}
  if(!company){err.textContent='Please enter your company or agent name.';err.style.display='block';return;}

  var protos = Array.from(document.getElementById('protocols').selectedOptions).map(o=>o.value);'''

new_submit = '''  var fname = document.getElementById('fname').value.trim();
  var lname = document.getElementById('lname').value.trim();
  var email = document.getElementById('email').value.trim();
  var company = document.getElementById('company').value.trim();
  var plan = document.getElementById('plan').value;
  var desc = document.getElementById('desc').value.trim();
  var budget = document.getElementById('daily-budget') ? document.getElementById('daily-budget').value : '';
  var needInvoice = document.getElementById('need-invoice') ? document.getElementById('need-invoice').checked : false;
  var agreedTC = document.getElementById('agree-tc') ? document.getElementById('agree-tc').checked : false;
  var err = document.getElementById('err');
  var btn = document.getElementById('sbtn');

  err.style.display = 'none';
  if(!fname || !lname){err.textContent='Please enter your full name.';err.style.display='block';return;}
  if(!email || email.indexOf('@') === -1){err.textContent='Please enter a valid work email.';err.style.display='block';return;}
  if(!company){err.textContent='Please enter your company or agent name.';err.style.display='block';return;}
  if(!agreedTC){err.textContent='You must accept the Advertising Terms & Conditions to proceed.';err.style.display='block';return;}

  var protos = Array.from(document.getElementById('protocols').selectedOptions).map(o=>o.value);'''

if old_submit in txt:
    txt = txt.replace(old_submit, new_submit)
    print('Submit validation updated')
else:
    print('Submit validation NOT FOUND')

# 3. Update fetch body to include new fields
old_body = '''JSON.stringify({fname,lname,email,company,protocols:protos,plan,description:desc})'''
new_body = '''JSON.stringify({fname,lname,email,company,protocols:protos,plan,daily_budget:budget,need_invoice:needInvoice,description:desc})'''
if old_body in txt:
    txt = txt.replace(old_body, new_body)
    print('Fetch body updated')

# 4. Add legal compliance footer section before </div> at end of main
old_footer_start = '''<footer>'''
new_compliance = '''  <!-- Legal compliance bar -->
  <div style="border-top:1px solid var(--border);padding-top:24px;margin-top:0">
    <div style="display:flex;align-items:flex-start;gap:24px;flex-wrap:wrap">
      <div style="flex:1;min-width:200px">
        <div style="font-size:11px;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;margin-bottom:6px">Legal compliance</div>
        <div style="font-size:13px;color:var(--muted);line-height:1.6">All advertising on Pievra is governed by the <a href="/advertising-terms" style="color:var(--teal)">Advertising T&amp;Cs</a>. Impressions are verified. Protocol claims are independently tested. GDPR-compliant analytics.</div>
      </div>
      <div style="flex:1;min-width:200px">
        <div style="font-size:11px;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;margin-bottom:6px">Invoice requests</div>
        <div style="font-size:13px;color:var(--muted);line-height:1.6">VAT invoices issued within 5 business days. Email <a href="mailto:legal@pievra.com" style="color:var(--teal)">legal@pievra.com</a> with company name, address and VAT number.</div>
      </div>
      <div style="flex:1;min-width:200px">
        <div style="font-size:11px;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;margin-bottom:6px">Standards</div>
        <div style="font-size:13px;color:var(--muted);line-height:1.6">Pievra advertising complies with IAB Tech Lab standards, EU Digital Services Act, CAP Code (UK) and US FTC guidelines on digital advertising.</div>
      </div>
    </div>
  </div>

</div>

<footer>'''

txt = txt.replace(old_footer_start, new_compliance, 1)
print('Legal compliance section added')

open(path, 'w').write(txt)
print(f'DONE — {len(txt)} bytes')
