
let plan='community';
const L={community:'✓ Free - All features included'};
function sp(p,el){plan='community';}
document.getElementById('planbadge').textContent=L['community'];
function cpw(pw){const bar=document.getElementById('pwbar');
const s=[pw.length>=8,pw.length>=12,/[A-Z]/.test(pw),/[0-9]/.test(pw),/[^a-zA-Z0-9]/.test(pw)].filter(Boolean).length;
const cfg=['0%,transparent','25%,#dc2626','50%,#f59e0b','75%,#3b82f6','90%,#10b981','100%,#00c4a7'][s];
const[w,bg]=cfg.split(',');bar.style.width=w;bar.style.background=bg;}
function shErr(m){const e=document.getElementById('err');e.textContent=m;e.style.display='block';}
async function doReg(){
  const email=document.getElementById('em').value.trim(),pw=document.getElementById('pw').value;
  const gdpr=document.getElementById('gdpr').checked,mkt=document.getElementById('mkt').checked;
  const btn=document.getElementById('rbtn');
  if(!email||!email.includes('@')){shErr('Please enter a valid work email.');return;}
  if(pw.length<8){shErr('Password must be at least 8 characters.');return;}
  if(!gdpr){shErr('You must accept the Terms and Privacy Policy to continue.');return;}
  btn.innerHTML='<span class="sp"></span>Creating account...';btn.disabled=true;
  document.getElementById('err').style.display='none';
  try{const r=await fetch('/auth/register',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({email,password:pw,plan,gdpr_consent:true,marketing_consent:mkt})});
  const d=await r.json();
  if(!r.ok){shErr(d.detail||'Registration failed. Please try again.');return;}
  document.querySelector('.card').innerHTML='<div style="text-align:center;padding:20px 0"><div style="font-size:48px;margin-bottom:16px">📬</div><h2 style="font-family:Manrope;font-weight:800;font-size:22px;color:var(--ink);margin-bottom:12px">Check your inbox</h2><p style="color:var(--muted);font-size:14px;line-height:1.7;margin-bottom:20px">We sent a verification link to <strong style="color:var(--ink)">'+email+'</strong>.<br/>Click the link to activate your account.</p><p style="font-size:13px;color:var(--muted)">Didn't receive it? Check spam or <a href="/signin" style="color:var(--teal)">request a magic link</a>.</p></div>';}
  catch(e){shErr('Network error. Please try again.');}
  finally{btn.innerHTML='Create free account';btn.disabled=false;}
}
document.addEventListener('keydown',e=>{if(e.key==='Enter')doReg();});
