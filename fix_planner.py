import re

path = '/var/www/pievra/index.html'
txt = open(path).read()

# Fix 1: Replace pievraGen to always re-fetch auth before generating
# Find the function and replace the first two lines
old = 'function pievraGen(){\n  if(!validateForm()) return;\n  if(!_pievraUser){window.location.href=\'/signup\';return;}'
new = '''function pievraGen(){
  if(!validateForm()) return;
  // Always re-check auth before generating
  fetch('/auth/me',{credentials:'include',cache:'no-store'})
  .then(function(r){return r.ok?r.json():null;})
  .then(function(u){
    if(!u){window.location.href='/signup';return;}
    _pievraUser=u;
    // Hide gate overlay
    var gate=document.getElementById('plannerGate');
    if(gate){gate.style.display='none';gate.style.visibility='hidden';}
    // Now run generate
    _doGenerate();
  }).catch(function(){window.location.href='/signup';});
}
function _doGenerate(){'''

if old in txt:
    txt = txt.replace(old, new, 1)
    print('pievraGen patched - now re-fetches auth')
    
    # Find end of pievraGen (the last closing brace of the fetch catch block)
    # Need to add a closing brace for _doGenerate
    # The old function ends with: }); \n}\n\n// Gate button
    old_end = '  });\n}\n\n// ── GATE BUTTON'
    new_end = '  });\n}\n\n// ── GATE BUTTON'
    # _doGenerate ends where pievraGen ended - add closing brace
    # Find the catch block end
    idx = txt.find('Network error. Please check your connection and try again.')
    if idx > 0:
        # Find the closing braces after this
        end = txt.find('});\n}', idx)
        if end > 0:
            txt = txt[:end+5] + '\n}' + txt[end+5:]
            print('Added closing brace for _doGenerate')
else:
    print('Pattern NOT FOUND - trying alternate fix')
    # Just remove the auth check and let the fetch handle it
    txt = re.sub(
        r'function pievraGen\(\)\{[^\n]*\n[^\n]*validateForm[^\n]*\n[^\n]*_pievraUser[^\n]*',
        '''function pievraGen(){
  if(!validateForm()) return;
  fetch('/auth/me',{credentials:'include',cache:'no-store'}).then(function(authR){
  var u=authR.ok?null:null;
  return authR.ok?authR.json():Promise.reject('auth');
  }).then(function(u){
  _pievraUser=u;
  var gate=document.getElementById('plannerGate');
  if(gate){gate.style.display='none';}
  _doGenerate2(u);
  }).catch(function(){window.location.href='/signup';});
}
function _doGenerate2(u){''',
        txt, count=1
    )
    print('Alternate pievraGen inserted')

# Fix 2: Make date inputs type=date
txt = txt.replace('id="pl-start"/>', 'id="pl-start" type="date"/>')
txt = txt.replace('id="pl-end"/>', 'id="pl-end" type="date"/>')

# Verify
print('pievraGen count:', txt.count('function pievraGen'))
print('_pievraUser re-fetch:', 'auth/me' in txt[txt.find('function pievraGen'):txt.find('function pievraGen')+500])

open(path, 'w').write(txt)
print('DONE -', len(txt), 'bytes')
