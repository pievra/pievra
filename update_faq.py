path = '/var/www/pievra/advertise.html'
txt = open(path).read()

# Replace the entire FAQ section
old_faq = '''  <!-- FAQ -->
  <div class="faq">
    <div class="faq-title">Frequently asked questions</div>
    <div class="faq-item">
      <div class="faq-q" onclick="toggleFaq(this)">How long does it take to go live? <span class="faq-icon">&#x25BC;</span></div>
      <div class="faq-a">Standard listings go live within 2 business days of payment confirmation. Pro and Enterprise listings include an onboarding call and typically go live within 5 business days.</div>
    </div>
    <div class="faq-item">
      <div class="faq-q" onclick="toggleFaq(this)">Is there a minimum commitment? <span class="faq-icon">&#x25BC;</span></div>
      <div class="faq-a">Standard and Pro plans are month-to-month with no minimum commitment. Enterprise plans are billed quarterly with a 3-month minimum.</div>
    </div>
    <div class="faq-item">
      <div class="faq-q" onclick="toggleFaq(this)">What does "verified by Pievra" mean? <span class="faq-icon">&#x25BC;</span></div>
      <div class="faq-a">Pievra conducts a technical review of your agent -- including protocol compliance testing, endpoint verification and a security review. Verified agents display a badge that buyers trust as a signal of production-readiness.</div>
    </div>
    <div class="faq-item">
      <div class="faq-q" onclick="toggleFaq(this)">Can I upgrade or downgrade my plan? <span class="faq-icon">&#x25BC;</span></div>
      <div class="faq-a">Yes. You can upgrade at any time and the change takes effect immediately. Downgrades take effect at the next billing cycle.</div>
    </div>
    <div class="faq-item">
      <div class="faq-q" onclick="toggleFaq(this)">How does payment work? <span class="faq-icon">&#x25BC;</span></div>
      <div class="faq-a">After your application is approved, our team will send a Stripe payment link. We accept all major credit cards and bank transfers for Enterprise plans.</div>
    </div>
  </div>'''

new_faq = '''  <!-- FAQ -->
  <div class="faq">
    <div class="faq-title">Frequently asked questions</div>

    <div class="faq-item">
      <div class="faq-q" onclick="toggleFaq(this)">What does Pievra mean and why does it matter? <span class="faq-icon">&#x25BC;</span></div>
      <div class="faq-a">Pievra means <strong>octopus</strong> in Italian and Catalan. The octopus has eight arms acting simultaneously and independently, each with its own intelligence. That is exactly what Pievra does for programmatic advertising: multiple AI agents operating across multiple protocols at the same time, coordinated from one platform. The octopus does not choose which arm to use. It uses all of them.</div>
    </div>

    <div class="faq-item">
      <div class="faq-q" onclick="toggleFaq(this)">Why do protocols matter, and what problem does Pievra solve? <span class="faq-icon">&#x25BC;</span></div>
      <div class="faq-a">Programmatic advertising has fragmented into five competing AI agent protocols: AdCP, MCP, UCP, ARTF and A2A. Today, most platforms force advertisers to choose one. That means leaving inventory, reach and efficiency on the table. Pievra aggregates all five. Instead of choosing a protocol, you activate the best combination for each campaign. A buyer running a CTV campaign might use AdCP for auction management and UCP for audience activation simultaneously. Pievra orchestrates that in one brief.</div>
    </div>

    <div class="faq-item">
      <div class="faq-q" onclick="toggleFaq(this)">Why should I advertise here rather than on a single-protocol marketplace? <span class="faq-icon">&#x25BC;</span></div>
      <div class="faq-a">Single-protocol marketplaces reach only the buyers locked into that protocol stack. Pievra reaches buyers running all five protocols simultaneously. A buyer on Pievra is not limited to AdCP or MCP. They are activating whichever protocol delivers the best result for their campaign. Your featured placement reaches the full cross-protocol buyer base, not a segment of it.</div>
    </div>

    <div class="faq-item">
      <div class="faq-q" onclick="toggleFaq(this)">How does CPI billing work? What am I actually paying for? <span class="faq-icon">&#x25BC;</span></div>
      <div class="faq-a">You pay per verified buyer impression. An impression is counted when your agent listing is rendered and visible to a qualified buyer for at least one second. You set a daily budget cap. We never charge more than your cap in any calendar day. You can pause or cancel at any time. There is no minimum commitment for Standard and Hero placements. Billing is monthly in arrears for actual impressions delivered.</div>
    </div>

    <div class="faq-item">
      <div class="faq-q" onclick="toggleFaq(this)">Can I get a VAT invoice for my advertising spend? <span class="faq-icon">&#x25BC;</span></div>
      <div class="faq-a">Yes. Tick the invoice checkbox in the application form and include your company name, registered address and VAT/tax number in the description field. Invoices are issued within 5 business days of each monthly billing period. We issue invoices in USD and EUR. Enterprise accounts receive invoices automatically at each billing cycle. For any invoice queries contact legal@pievra.com.</div>
    </div>

    <div class="faq-item">
      <div class="faq-q" onclick="toggleFaq(this)">What does "verified by Pievra" mean? <span class="faq-icon">&#x25BC;</span></div>
      <div class="faq-a">Pievra conducts a technical review before your agent goes live, including: protocol endpoint testing for each claimed protocol (AdCP, MCP, UCP, ARTF, A2A), security review, substantiation of performance claims, and a GDPR data handling check for agents that process personal data. The verification badge tells buyers your agent is production-ready and protocol-compliant. It is the most trusted signal on the marketplace.</div>
    </div>

    <div class="faq-item">
      <div class="faq-q" onclick="toggleFaq(this)">How long does it take to go live? <span class="faq-icon">&#x25BC;</span></div>
      <div class="faq-a">Standard listings go live within 2 business days of payment confirmation. Hero and Newsletter placements include a brief onboarding call and typically go live within 3 to 5 business days. Enterprise managed campaigns are scoped individually.</div>
    </div>

    <div class="faq-item">
      <div class="faq-q" onclick="toggleFaq(this)">Can I change my daily budget or placement type after going live? <span class="faq-icon">&#x25BC;</span></div>
      <div class="faq-a">Yes. You can increase your daily budget at any time and the change takes effect immediately. Budget decreases take effect the following day. You can switch between Standard and Hero placements with 24 hours notice. Newsletter sponsorships can be cancelled up to 5 business days before the scheduled send date.</div>
    </div>

    <div class="faq-item">
      <div class="faq-q" onclick="toggleFaq(this)">What are the advertising compliance requirements? <span class="faq-icon">&#x25BC;</span></div>
      <div class="faq-a">All advertising on Pievra must comply with IAB Tech Lab standards, EU Digital Services Act, CAP Code (UK) and US FTC digital advertising guidelines. Performance claims must be verifiable. Protocol support claims are independently tested. GDPR-compliant analytics only. Full requirements are in the <a href="/advertising-terms" style="color:var(--teal)">Advertising T&amp;Cs</a>.</div>
    </div>

  </div>'''

if old_faq in txt:
    txt = txt.replace(old_faq, new_faq)
    print('FAQ replaced')
else:
    # Try finding by title
    idx = txt.find('<div class="faq-title">Frequently asked questions</div>')
    if idx > 0:
        print(f'FAQ title found at {idx} - pattern mismatch, trying broader replace')
        # Replace from faq div to end of faq div
        import re
        txt = re.sub(
            r'<div class="faq">.*?</div>\s*</div>\s*<!-- Legal',
            new_faq + '\n\n  <!-- Legal',
            txt, flags=re.DOTALL, count=1
        )
        print('FAQ replaced via regex')
    else:
        print('FAQ NOT FOUND')

open(path, 'w').write(txt)
print(f'DONE - {len(txt)} bytes')
