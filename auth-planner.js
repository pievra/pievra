(function() {
  var user = null;

  function hidePlanner() {
    var gate = document.getElementById('plannerGate');
    if (gate) {
      gate.style.display = 'none';
      gate.style.visibility = 'hidden';
      gate.style.pointerEvents = 'none';
    }
    var overlay = document.querySelector('.gate-overlay');
    if (overlay) {
      overlay.style.display = 'none';
    }
  }

  function showToast(msg) {
    var t = document.createElement('div');
    t.style.cssText = 'position:fixed;top:80px;left:50%;transform:translateX(-50%);background:#0a0e1a;color:#00c4a7;font-weight:700;padding:14px 28px;border-radius:12px;z-index:9999;font-size:15px;box-shadow:0 4px 24px rgba(0,196,167,0.3);white-space:nowrap';
    t.innerHTML = msg;
    document.body.appendChild(t);
    setTimeout(function(){ t.remove(); }, 7000);
  }

  function updateNav(u) {
    var btn = document.querySelector('button.btn-ghost');
    if (btn) {
      btn.textContent = 'Dashboard';
      btn.setAttribute('onclick', "window.location.href='/dashboard'");
    }
  }

  function checkAuth() {
    return fetch('/auth/me', {credentials: 'include', cache: 'no-store'})
      .then(function(r) { return r.ok ? r.json() : null; })
      .then(function(u) {
        if (u && u.email) {
          user = u;
          hidePlanner();
          updateNav(u);
        }
        return user;
      })
      .catch(function() { return null; });
  }

  window.pievraHandleGenerate = function() {
    checkAuth().then(function(u) {
      if (u) {
        hidePlanner();
        showToast('Campaign plan generated! <a href="/dashboard" style="color:#fff;margin-left:8px;text-decoration:underline">View Dashboard</a>');
        var btn = document.querySelector('.generate-btn');
        if (btn) { btn.textContent = 'Plan Generated!'; btn.style.background = '#009e86'; }
      } else {
        window.location.href = '/signup';
      }
    });
  };

  window.pievraHandleGetPlan = function() {
    if (user) {
      hidePlanner();
      showToast('Plan saved! <a href="/dashboard" style="color:#fff;margin-left:8px;text-decoration:underline">View in Dashboard</a>');
      return;
    }
    var emailEl = document.getElementById('gateEmailInput') || document.querySelector('.gate-input-row input');
    var email = emailEl ? emailEl.value.trim() : '';
    if (!email || email.indexOf('@') === -1) {
      window.location.href = '/signup';
      return;
    }
    fetch('/api/signup', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({email: email, source: 'campaign-planner'})
    }).then(function() {
      hidePlanner();
      var b = document.createElement('div');
      b.style.cssText = 'position:fixed;top:80px;left:50%;transform:translateX(-50%);background:#00c4a7;color:#0a0e1a;font-weight:700;padding:14px 28px;border-radius:12px;z-index:9999;font-size:15px';
      b.textContent = 'Check your inbox for your Pievra access link.';
      document.body.appendChild(b);
      setTimeout(function(){ b.remove(); }, 6000);
    }).catch(function() { window.location.href = '/signup'; });
  };

  // Run on load
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', checkAuth);
  } else {
    checkAuth();
  }
})();
