// Pievra shared navigation - injected on all pages for consistency
// All content is hardcoded (no user input), safe to use DOM methods
(function() {
  window.__pievraNavLoaded = true;
  var nav = document.querySelector('nav');
  if (!nav) { window.__pievraNavError = 'no nav found'; return; }

  var path = window.location.pathname;

  // Clear existing nav content
  while (nav.firstChild) nav.removeChild(nav.firstChild);

  // Set nav styles (CSS Grid for true centering)
  nav.setAttribute('style',
    'background:var(--surface,#FEFDFB);height:64px;display:grid;grid-template-columns:1fr auto 1fr;' +
    'align-items:center;padding:0 40px;position:sticky;top:0;z-index:100;' +
    'border-bottom:1px solid var(--border,#E4E4E7);'
  );
  nav.className = '';

  var links = [
    { href: '/marketplace', label: 'Marketplace' },
    { href: '/partners', label: 'Partners' },
    { href: '/news', label: 'News' },
    { href: '/news/analytics', label: 'Analytics' },
    { href: '/careers', label: 'Careers' }
  ];

  var linkStyleBase = {
    color: 'var(--ink-muted,#71717A)', textDecoration: 'none', fontSize: '14px',
    fontWeight: '500', padding: '8px 14px', borderRadius: '8px', transition: 'all .2s'
  };

  function applyStyles(el, styles) {
    for (var key in styles) el.style[key] = styles[key];
  }

  function createLink(href, label, isActive, extra) {
    var a = document.createElement('a');
    a.href = href;
    a.textContent = label;
    applyStyles(a, linkStyleBase);
    if (isActive) {
      a.style.color = 'var(--ink,#18181B)';
      a.style.background = 'var(--surface-2,#F9F8F6)';
    }
    if (extra) applyStyles(a, extra);
    return a;
  }

  // Logo (left)
  var logoWrap = document.createElement('div');
  logoWrap.style.justifySelf = 'start';
  var logoLink = document.createElement('a');
  logoLink.href = '/';
  logoLink.style.textDecoration = 'none';
  logoLink.style.display = 'inline-block';
  var logoSpan = document.createElement('span');
  applyStyles(logoSpan, {
    fontFamily: "'Instrument Serif', serif", fontStyle: 'italic',
    fontSize: '24px', color: 'var(--ink,#18181B)', letterSpacing: '-0.5px'
  });
  logoSpan.textContent = 'pievra';
  var dot = document.createElement('span');
  dot.style.color = 'var(--accent,#F97316)';
  dot.textContent = '.';
  logoSpan.appendChild(dot);
  logoLink.appendChild(logoSpan);
  logoWrap.appendChild(logoLink);

  // Center links
  var center = document.createElement('div');
  applyStyles(center, { display: 'flex', gap: '4px', alignItems: 'center', justifySelf: 'center' });
  for (var i = 0; i < links.length; i++) {
    var l = links[i];
    var isActive = path === l.href || (l.href !== '/' && path.indexOf(l.href) === 0);
    center.appendChild(createLink(l.href, l.label, isActive));
  }

  // Auth (right)
  var right = document.createElement('div');
  applyStyles(right, { display: 'flex', gap: '4px', alignItems: 'center', justifySelf: 'end' });
  right.appendChild(createLink('/signin', 'Sign In', false));
  right.appendChild(createLink('/signup', 'Sign Up Free', false, {
    background: 'var(--accent,#F97316)', color: 'white', fontWeight: '700'
  }));

  nav.appendChild(logoWrap);
  nav.appendChild(center);
  nav.appendChild(right);
})();
