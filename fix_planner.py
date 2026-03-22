import re

path = '/var/www/pievra/index.html'
txt = open(path).read()

print("=== BEFORE ===")
# Show all generate-btn buttons
for m in re.finditer(r'<button[^>]*generate-btn[^>]*>[^<]*</button>', txt, re.DOTALL):
    print(repr(m.group()[:120]))
print()

# Fix ALL generate-btn buttons — both the gate one and the main one
# The gate button at line 650 - change to go to signup for non-auth users
txt = re.sub(
    r'(<button[^>]*class="generate-btn"[^>]*)onclick="submitGate\(\)"([^>]*>)',
    r'\1onclick="pievraGen()"\2',
    txt
)

# Also fix the date inputs
txt = txt.replace(
    '<input type="text" id="pl-start" placeholder="YYYY-MM-DD"/>',
    '<input type="date" id="pl-start"/>'
)
txt = txt.replace(
    '<input type="date" id="pl-start" style="padding:10px 14px"/>',
    '<input type="date" id="pl-start"/>'
)
txt = txt.replace(
    '<input type="text" id="pl-end" placeholder="YYYY-MM-DD"/>',
    '<input type="date" id="pl-end"/>'
)
txt = txt.replace(
    '<input type="date" id="pl-end" style="padding:10px 14px"/>',
    '<input type="date" id="pl-end"/>'
)

# Add Nginx route for campaign edit API
# Update campaign API Nginx route to include PUT/DELETE
print("=== AFTER ===")
for m in re.finditer(r'<button[^>]*generate-btn[^>]*>[^<]*</button>', txt, re.DOTALL):
    print(repr(m.group()[:120]))

# Verify date inputs
print("pl-start type=date:", 'type="date" id="pl-start"' in txt or 'id="pl-start"/>' in txt)
print("pievraGen remaining submitGate:", txt.count('class="generate-btn"') , 'buttons,', txt.count('onclick="submitGate()"'), 'submitGate calls on generate-btn')

open(path, 'w').write(txt)
print(f"SAVED {len(txt)} bytes")
