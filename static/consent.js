/* Cookie consent banner - GDPR/CNIL compliant
   Blocks Google Analytics until user grants consent.
   Equal prominence for Accept/Refuse (CNIL requirement). */
(function(){
  var GA_ID = 'G-7ZCHRYL3H1';
  var CONSENT_KEY = 'pievra_cookie_consent';

  function getConsent() {
    try { return localStorage.getItem(CONSENT_KEY); } catch(e) { return null; }
  }

  function setConsent(val) {
    try { localStorage.setItem(CONSENT_KEY, val); } catch(e) {}
  }

  function loadGA() {
    if (document.getElementById('ga-script')) return;
    var s = document.createElement('script');
    s.id = 'ga-script';
    s.async = true;
    s.src = 'https://www.googletagmanager.com/gtag/js?id=' + GA_ID;
    document.head.appendChild(s);
    window.dataLayer = window.dataLayer || [];
    function gtag(){dataLayer.push(arguments);}
    window.gtag = gtag;
    gtag('js', new Date());
    gtag('config', GA_ID);
  }

  function removeBanner() {
    var b = document.getElementById('cookie-consent-banner');
    if (b) b.remove();
  }

  function showBanner() {
    if (document.getElementById('cookie-consent-banner')) return;
    var d = document.createElement('div');
    d.id = 'cookie-consent-banner';
    d.setAttribute('role', 'dialog');
    d.setAttribute('aria-label', 'Cookie consent');
    d.innerHTML =
      '<div style="max-width:960px;margin:0 auto;display:flex;align-items:center;gap:20px;flex-wrap:wrap">' +
        '<p style="flex:1;min-width:240px;margin:0;font-size:14px;color:#1a1a2e;line-height:1.5">' +
          'We use cookies for analytics (Google Analytics) to understand how visitors use this site. ' +
          'No advertising or tracking cookies. <a href="/privacy#cookies" style="color:#009e86;text-decoration:underline">Cookie policy</a>' +
        '</p>' +
        '<div style="display:flex;gap:10px;flex-shrink:0">' +
          '<button id="cookie-refuse" style="padding:10px 20px;border:1.5px solid #e2e4ed;background:white;color:#3d4460;font-size:14px;font-weight:600;border-radius:8px;cursor:pointer;font-family:Inter,sans-serif">Refuse</button>' +
          '<button id="cookie-accept" style="padding:10px 20px;border:none;background:#0a0e1a;color:white;font-size:14px;font-weight:600;border-radius:8px;cursor:pointer;font-family:Inter,sans-serif">Accept</button>' +
        '</div>' +
      '</div>';
    d.style.cssText = 'position:fixed;bottom:0;left:0;right:0;z-index:10000;background:rgba(255,255,255,0.97);backdrop-filter:blur(12px);border-top:1px solid #e2e4ed;padding:16px 24px;box-shadow:0 -4px 24px rgba(0,0,0,0.08)';
    document.body.appendChild(d);

    document.getElementById('cookie-accept').onclick = function() {
      setConsent('granted');
      loadGA();
      removeBanner();
    };
    document.getElementById('cookie-refuse').onclick = function() {
      setConsent('refused');
      removeBanner();
    };
  }

  // Check consent state on load
  var consent = getConsent();
  if (consent === 'granted') {
    loadGA();
  } else if (consent !== 'refused') {
    // No decision yet - show banner
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', showBanner);
    } else {
      showBanner();
    }
  }
})();
