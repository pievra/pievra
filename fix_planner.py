import re

path = '/var/www/pievra/index.html'
txt = open(path).read()

# Step 1: Remove ALL previous auth script blocks we added (there may be multiple)
# Find and remove every <script> block containing checkAuthAndUnlock or handleGenerate
cleaned = re.sub(r'<script>\s*\(function\(\).*?\}\)\(\);\s*</script>', '', txt, flags=re.DOTALL)
cleaned = re.sub(r'<script>\s*// Check if user is logged in.*?</script>', '', cleaned, flags=re.DOTALL)
print('Removed old auth scripts. Remaining handleGenerate:', cleaned.count('handleGenerate'))

# Step 2: Write the clean auth JS to a separate file (avoids all quote/bash issues)
auth_js = open('/var/www/pievra/auth-planner.js').read() if __import__('os').path.exists('/var/www/pievra/auth-planner.js') else None

# Step 3: Replace generate button onclick
cleaned = cleaned.replace(
    "onclick=\"handleGenerate()\"",
    "onclick=\"pievraHandleGenerate()\""
)
print('Generate button:', cleaned.count('pievraHandleGenerate()'))

# Step 4: Replace get plan button onclick  
cleaned = cleaned.replace(
    'onclick="handleGetPlan()">Get Plan',
    'onclick="pievraHandleGetPlan()">Get Plan'
)

# Step 5: Add external script reference before </body>
script_tag = '\n<script src="/auth-planner.js"></script>\n</body>'
if '</body>' in cleaned:
    cleaned = cleaned.replace('</body>', script_tag)
    print('Added external script tag')

open(path, 'w').write(cleaned)
print('DONE - index.html updated')
