#!/bin/bash
# Fix 1: Apply atomic button fix
curl -s "https://raw.githubusercontent.com/pievra/pievra/main/fix_planner.py" -o /tmp/atomic_fix.py && python3 /tmp/atomic_fix.py

# Fix 2: Update Nginx to allow PUT/DELETE on campaign routes
python3 -c "
c = open('/etc/nginx/sites-available/pievra.com').read()
old = '    location /api/campaign {\n        proxy_pass http://127.0.0.1:8003;\n        proxy_set_header Host \$host;\n        proxy_set_header X-Real-IP \$remote_addr;\n    }\n    location /api/campaigns {\n        proxy_pass http://127.0.0.1:8003;\n        proxy_set_header Host \$host;\n    }'
new = '    location ~ ^/api/campaigns? {\n        proxy_pass http://127.0.0.1:8003;\n        proxy_set_header Host \$host;\n        proxy_set_header X-Real-IP \$remote_addr;\n    }'
if old in c:
    c = c.replace(old, new)
    open('/etc/nginx/sites-available/pievra.com','w').write(c)
    open('/etc/nginx/sites-enabled/pievra.com','w').write(c)
    print('Nginx PATCHED')
else:
    print('Nginx pattern not found - checking existing')
    import re
    m = re.search(r'location.*?campaign.*?\{', c)
    if m: print('Found:', m.group())
"
nginx -t && systemctl reload nginx && echo "NGINX OK"

# Fix 3: Update dashboard
curl -s "https://raw.githubusercontent.com/pievra/pievra/main/update_dashboard.py" -o /tmp/upd.py && python3 /tmp/upd.py

# Verify
echo "=== VERIFICATION ==="
curl -s https://pievra.com/ | grep -c 'onclick="pievraGen()"'
curl -s https://pievra.com/ | grep -c 'onclick="submitGate()"'
curl -s -o /dev/null -w "%{http_code}" https://pievra.com/dashboard
