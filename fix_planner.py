import re, json

path = '/var/www/pievra/index.html'
txt = open(path).read()
print(f"File size: {len(txt)} bytes")

# ── 1. FIX GENERATE BUTTON onclick ─────────────────────────────────────────
# Find all variations and fix them
fixes = [
    ('onclick="submitGate()">\n          🐙 Generate Campaign Plan', 'onclick="pievraGen()">\n          🐙 Generate Campaign Plan'),
    ("onclick=\"submitGate()\">\n          \U0001f419 Generate Campaign Plan", "onclick=\"pievraGen()\">\n          \U0001f419 Generate Campaign Plan"),
    ('onclick="submitGate()">🐙 Generate Campaign Plan', 'onclick="pievraGen()">🐙 Generate Campaign Plan'),
    ('onclick="submitGate()">', 'onclick="pievraGen()">'),  # catch-all for generate-btn context
]
for old, new in fixes:
    if old in txt:
        txt = txt.replace(old, new)
        print(f"Fixed generate button: {old[:50]}")

# Verify - find generate-btn and show its onclick
m = re.search(r'class="generate-btn"[^>]*onclick="([^"]+)"', txt)
if m:
    print(f"Generate btn onclick: {m.group(1)}")
else:
    m2 = re.search(r'generate-btn.*?onclick="([^"]+)"', txt, re.DOTALL)
    if m2:
        print(f"Generate btn onclick (loose): {m2.group(1)}")
    else:
        # Force replace using regex
        txt = re.sub(
            r'(class="generate-btn"[^>]*?)onclick="[^"]*"',
            r'\1onclick="pievraGen()"',
            txt
        )
        print("Generate button fixed via regex")

# ── 2. FIX FLIGHT DATE INPUTS → date type ──────────────────────────────────
txt = txt.replace(
    '<input type="text" id="pl-start" placeholder="YYYY-MM-DD"/>',
    '<input type="date" id="pl-start" style="padding:10px 14px"/>'
)
txt = txt.replace(
    '<input type="text" id="pl-end" placeholder="YYYY-MM-DD"/>',
    '<input type="date" id="pl-end" style="padding:10px 14px"/>'
)
print("Date inputs fixed")

# ── 3. FIX CHAT SEND BUTTON — ensure sendChat is called inline ─────────────
old_chat_btn = 'onclick="sendChat()" id="chat-send-btn"'
new_chat_btn = 'onclick="if(typeof sendChat===\'function\'){sendChat();}else{console.error(\'sendChat not defined\');}" id="chat-send-btn"'
if old_chat_btn in txt:
    txt = txt.replace(old_chat_btn, new_chat_btn)
    print("Chat send button fixed")

# ── 4. REMOVE ALL OLD SCRIPTS except the comprehensive one ─────────────────
# Remove duplicate/old auth-planner script references
old_scripts_to_remove = [
    '<script src="/static/auth-planner.js"></script>',
    '<script src="/auth-planner.js"></script>',
]
for s in old_scripts_to_remove:
    if s in txt:
        txt = txt.replace(s, '')
        print(f"Removed: {s}")

open(path, 'w').write(txt)
print(f"DONE — saved {len(txt)} bytes")

# Verify final state
m = re.search(r'class="generate-btn".*?onclick="([^"]+)"', txt, re.DOTALL)
print(f"Final generate btn onclick: {m.group(1) if m else 'NOT FOUND'}")
print(f"pl-start type: {'date' if 'id=\"pl-start\" style' in txt or 'type=\"date\" id=\"pl-start\"' in txt else 'TEXT - NOT FIXED'}")
print(f"pievraGen defined: {'function pievraGen()' in txt}")
