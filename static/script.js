// ── Sidebar active link ──
var currentPath = window.location.pathname;
document.querySelectorAll('.sidebar .nav-link').forEach(function(link) {
  var href = link.getAttribute('href');
  if (!href) return;
  var baseHref = href.split('#')[0];
  if (currentPath === baseHref) {
    link.classList.add('active');
  }
});

// auto-expand sidebar group containing the active link
document.querySelectorAll('.section-group').forEach(function(group) {
  var links = group.querySelectorAll('.nav-link');
  var hasActive = false;
  links.forEach(function(l) { if (l.classList.contains('active')) hasActive = true; });
  if (hasActive) {
    group.style.maxHeight = group.scrollHeight + 'px';
    var toggle = document.querySelector('.section-toggle[data-target="' + group.id.replace('group-', '') + '"]');
    if (toggle) {
      toggle.setAttribute('aria-expanded', 'true');
      localStorage.setItem('sidebar_' + group.id.replace('group-', ''), 'expanded');
    }
  }
});

// ── Auto-dismiss alerts ──
document.querySelectorAll('.alert-dismissible').forEach(function(a) {
  setTimeout(function() {
    try { var bs = new bootstrap.Alert(a); bs.close(); } catch(e) {}
  }, 4500);
});

// ── Table sorting ──
document.querySelectorAll('.table.sortable thead th').forEach(function(th, idx) {
  if (th.querySelector('.no-sort')) return;
  th.style.cursor = 'pointer';
  th.addEventListener('click', function() {
    var tbody = th.closest('table').querySelector('tbody');
    var rows = Array.from(tbody.querySelectorAll('tr'));
    var key = function(row) {
      var val = (row.children[idx] || {}).textContent.trim().toLowerCase();
      var num = parseFloat(val.replace(/[^0-9.\-]/g, ''));
      return isNaN(num) ? val : num;
    };
    var dir = th.getAttribute('data-sort') === 'asc' ? -1 : 1;
    rows.sort(function(a, b) {
      var va = key(a), vb = key(b);
      if (va < vb) return -1 * dir;
      if (va > vb) return 1 * dir;
      return 0;
    });
    rows.forEach(function(r) { tbody.appendChild(r); });
    // reset arrows
    th.closest('thead').querySelectorAll('th').forEach(function(h) { h.removeAttribute('data-sort'); h.style.color = ''; });
    th.setAttribute('data-sort', dir === 1 ? 'asc' : 'desc');
    th.style.color = 'var(--teal)';
  });
});

// ── Form validation styling ──
document.addEventListener('invalid', function(e) {
  if (e.target && e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT' || e.target.tagName === 'TEXTAREA') {
    e.target.classList.add('is-invalid');
  }
}, true);
document.addEventListener('blur', function(e) {
  if (e.target && (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT' || e.target.tagName === 'TEXTAREA')) {
    if (e.target.checkValidity && !e.target.checkValidity()) {
      e.target.classList.add('is-invalid');
    } else {
      e.target.classList.remove('is-invalid');
    }
  }
}, true);
document.querySelectorAll('form').forEach(function(f) {
  f.addEventListener('submit', function() {
    [].slice.call(this.querySelectorAll('.is-invalid')).forEach(function(el) { el.classList.remove('is-invalid'); });
  });
});

// ── Offline queue ──
var OFFLINE_QUEUE_KEY = 'pulse_offline_queue';
function enqueueOffline(data) {
  var queue = JSON.parse(localStorage.getItem(OFFLINE_QUEUE_KEY) || '[]');
  queue.push({ data: data, ts: new Date().toISOString() });
  localStorage.setItem(OFFLINE_QUEUE_KEY, JSON.stringify(queue));
}
function flushOfflineQueue() {
  var raw = localStorage.getItem(OFFLINE_QUEUE_KEY);
  if (!raw) return;
  var queue = JSON.parse(raw);
  if (queue.length === 0) return;
  var remaining = [];
  queue.forEach(function(item) {
    var meta = document.querySelector('meta[name="csrf-token"]');
    fetch('/api/offline/replay', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': meta ? meta.getAttribute('content') : '' },
      body: JSON.stringify(item.data)
    }).then(function(r) {
      if (!r.ok) remaining.push(item);
    }).catch(function() {
      remaining.push(item);
    });
  });
  localStorage.setItem(OFFLINE_QUEUE_KEY, JSON.stringify(remaining));
}
window.addEventListener('online', flushOfflineQueue);

// ── Session timeout countdown (8h session, warn at 30min) ──
(function() {
  var SESSION_KEY = 'pulse_session_start';
  if (!sessionStorage.getItem(SESSION_KEY)) {
    sessionStorage.setItem(SESSION_KEY, Date.now().toString());
  }
  var SESSION_MS = 8 * 60 * 60 * 1000;
  var WARN_MS = 30 * 60 * 1000;
  function checkSession() {
    var elapsed = Date.now() - parseInt(sessionStorage.getItem(SESSION_KEY) || '0');
    var remaining = SESSION_MS - elapsed;
    if (remaining <= 0) {
      window.location.href = '/logout';
    } else if (remaining <= WARN_MS) {
      var mins = Math.ceil(remaining / 60000);
      var warning = document.getElementById('sessionWarning');
      if (!warning) {
        var w = document.createElement('div');
        w.id = 'sessionWarning';
        w.style.cssText = 'position:fixed;bottom:1rem;right:1rem;z-index:9999;background:var(--amber, #eab308);color:#1a1a2e;padding:.5rem 1rem;border-radius:8px;font-size:.8rem;font-weight:500;box-shadow:0 4px 12px rgba(0,0,0,.15);cursor:pointer';
        w.textContent = '⏰ Session expires in ' + mins + ' min';
        w.onclick = function() { window.location.href = '/'; };
        document.body.appendChild(w);
      }
    }
  }
  setInterval(checkSession, 60000);
  checkSession();
})();

// ── Loading overlay for imports ──
function showProcessingOverlay(msg) {
  msg = msg || 'Processing...';
  var overlay = document.createElement('div');
  overlay.id = 'processingOverlay';
  overlay.style.cssText = 'position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,.35);z-index:9998;display:flex;align-items:center;justify-content:center';
  overlay.innerHTML = '<div style="background:var(--card);padding:1.5rem 2.5rem;border-radius:12px;box-shadow:0 8px 32px rgba(0,0,0,.2);text-align:center;font-size:.95rem"><div class="spinner" style="width:32px;height:32px;border-width:3px;margin:0 auto .75rem"></div>' + msg + '</div>';
  document.body.appendChild(overlay);
  // disable all submit buttons
  document.querySelectorAll('button[type="submit"]').forEach(function(b) { b.disabled = true; });
}
function hideProcessingOverlay() {
  var o = document.getElementById('processingOverlay');
  if (o) o.remove();
  document.querySelectorAll('button[type="submit"]').forEach(function(b) { b.disabled = false; });
}
(function() {
  document.querySelectorAll('form[action*="import"], form[action*="export"]').forEach(function(f) {
    f.addEventListener('submit', function() { showProcessingOverlay('Processing...'); });
  });
})();

// ── Password strength indicator ──
function initPasswordStrength(inputId, indicatorId) {
  var input = document.getElementById(inputId);
  var indicator = document.getElementById(indicatorId);
  if (!input || !indicator) return;
  input.addEventListener('input', function() {
    var v = input.value;
    var s = 0;
    if (v.length >= 8) s++;
    if (v.length >= 12) s++;
    if (/[a-z]/.test(v) && /[A-Z]/.test(v)) s++;
    if (/\d/.test(v)) s++;
    if (/[^a-zA-Z0-9]/.test(v)) s++;
    var labels = ['Weak', 'Fair', 'Good', 'Strong', 'Very Strong'];
    var colors = ['#dc2626', '#eab308', '#16a34a', '#059669', '#0d9488'];
    var idx = Math.min(s, 4);
    indicator.textContent = v.length > 0 ? labels[idx] : '';
    indicator.style.color = v.length > 0 ? colors[idx] : 'transparent';
  });
}

// ── column visibility toggle ──
function toggleCol(colIdx) {
  var tbl = document.querySelector('table.sortable');
  if (!tbl) return;
  var cb = document.querySelector('input[data-col="' + colIdx + '"]');
  if (!cb) return;
  var visible = cb.checked;
  tbl.querySelectorAll('thead tr th, tbody tr td').forEach(function(cell) {
    if (cell.cellIndex === colIdx) {
      cell.style.display = visible ? '' : 'none';
    }
  });
}
// close column menu on outside click
document.addEventListener('click', function(e) {
  var menus = document.querySelectorAll('.col-vis-toggle');
  menus.forEach(function(m) {
    if (!m.contains(e.target)) {
      var menu = m.querySelector('.col-vis-menu');
      if (menu) menu.classList.remove('open');
    }
  });
});

// ── Guided Tour ──
var tourSteps = [
  {
    selector: '#sidebar',
    title: 'Sidebar Navigation',
    desc: 'This is your main navigation. Click "Supplies" or "Equipment" to expand each section. Use the search bar above to quickly find anything.',
    pos: 'right'
  },
  {
    selector: '.stat-grid',
    title: 'Dashboard Stat Cards',
    desc: 'These cards show real-time status: Out of Stock (red), Low Stock (amber), and In Stock (green). Keep an eye on the red ones!',
    pos: 'bottom'
  },
  {
    selector: '.card-body .d-flex.flex-wrap',
    title: 'Date Range Filter',
    desc: 'Use the From → To date pickers to filter the dashboard by a specific time period. The charts and tables update automatically.',
    pos: 'bottom'
  },
  {
    selector: '.realtime-bar',
    title: 'Real-Time Updates',
    desc: 'The dashboard refreshes every few seconds — all connected computers see the same live data. No need to refresh your browser.',
    pos: 'top'
  },
  {
    selector: '.topbar-right',
    title: 'Topbar Tools',
    desc: 'Here you can toggle Dark Mode ☽, view stock alerts 🔔, get help ?, and access your Account menu (password, preferences, logout).',
    pos: 'bottom'
  },
  {
    selector: '.account-trigger',
    title: 'Your Account',
    desc: 'Click your name to change your password, set preferences, or logout. Admins can also manage staff and view system settings here.',
    pos: 'bottom'
  }
];

var tourCurrent = -1;
var tourActive = false;
var tourOverlay, tourTooltip;

function startTour(startStep) {
  if (tourActive) endTour();
  startStep = startStep || 0;
  tourCurrent = startStep;
  tourActive = true;

  tourOverlay = document.createElement('div');
  tourOverlay.className = 'tour-overlay';
  tourOverlay.style.opacity = '0';
  document.body.appendChild(tourOverlay);
  requestAnimationFrame(function() { tourOverlay.style.opacity = '1'; });

  tourTooltip = document.createElement('div');
  tourTooltip.className = 'tour-tooltip';
  document.body.appendChild(tourTooltip);

  showTourStep(tourCurrent);
}

function showTourStep(idx) {
  if (idx < 0 || idx >= tourSteps.length) { endTour(); return; }
  tourCurrent = idx;
  var step = tourSteps[idx];
  var el = document.querySelector(step.selector);
  if (!el) { nextTourStep(); return; }

  removeTourHighlight();
  el.classList.add('tour-highlight');
  el.scrollIntoView({ block: 'center', behavior: 'smooth' });

  var total = tourSteps.length;
  var isLast = idx === total - 1;
  var isFirst = idx === 0;

  tourTooltip.innerHTML =
    '<div class="tour-tooltip-title">' + esc(step.title) + '</div>' +
    '<div class="tour-tooltip-desc">' + esc(step.desc) + '</div>' +
    '<div class="tour-tooltip-footer">' +
      '<span class="tour-step-indicator">' + (idx + 1) + ' of ' + total + '</span>' +
      '<div class="tour-btn-group">' +
        (isFirst ? '' : '<button class="tour-btn" onclick="prevTourStep()">Back</button>') +
        (isLast ? '<button class="tour-btn tour-btn-primary" onclick="endTour()">Done</button>' : '<button class="tour-btn tour-btn-primary" onclick="nextTourStep()">Next</button>') +
        '<button class="tour-btn tour-btn-skip" onclick="endTour()">Skip</button>' +
      '</div>' +
    '</div>' +
    '<div class="tour-tooltip-arrow"></div>';

  positionTourTooltip(el, step.pos);
}

function positionTourTooltip(el, pos) {
  var er = el.getBoundingClientRect();
  var tw = 340;
  var th = tourTooltip.offsetHeight || 200;
  var gap = 14;
  var left, top, actualPos = pos;

  // if screen too narrow, force bottom
  if (pos === 'right' && er.right + tw + gap > window.innerWidth) actualPos = 'bottom';
  if (pos === 'left' && er.left - tw - gap < 0) actualPos = 'bottom';
  if ((actualPos === 'bottom' || actualPos === 'top') && (er.bottom + th + gap > window.innerHeight && er.top - th - gap < 0)) actualPos = 'bottom';

  tourTooltip.setAttribute('data-pos', actualPos);

  switch (actualPos) {
    case 'right':
      left = Math.min(Math.max(8, er.right + gap), window.innerWidth - tw - 8);
      top = Math.min(Math.max(8, er.top + (er.height / 2) - (th / 2)), window.innerHeight - th - 8);
      break;
    case 'left':
      left = Math.min(Math.max(8, er.left - tw - gap), window.innerWidth - tw - 8);
      top = Math.min(Math.max(8, er.top + (er.height / 2) - (th / 2)), window.innerHeight - th - 8);
      break;
    case 'top':
      left = Math.min(Math.max(8, er.left + (er.width / 2) - (tw / 2)), window.innerWidth - tw - 8);
      top = Math.max(8, er.top - th - gap);
      break;
    default: // bottom
      left = Math.min(Math.max(8, er.left + (er.width / 2) - (tw / 2)), window.innerWidth - tw - 8);
      top = Math.min(Math.max(8, er.bottom + gap), window.innerHeight - th - 8);
  }
  tourTooltip.style.left = left + 'px';
  tourTooltip.style.top = top + 'px';
}

function nextTourStep() {
  if (!tourActive) return;
  showTourStep(tourCurrent + 1);
}

function prevTourStep() {
  if (!tourActive) return;
  showTourStep(tourCurrent - 1);
}

function endTour() {
  tourActive = false;
  tourCurrent = -1;
  removeTourHighlight();
  if (tourOverlay) { tourOverlay.style.opacity = '0'; setTimeout(function() { if (tourOverlay) tourOverlay.remove(); }, 200); }
  if (tourTooltip) { tourTooltip.remove(); tourTooltip = null; }
  localStorage.setItem('pulse_tour_seen', 'true');
}

function removeTourHighlight() {
  document.querySelectorAll('.tour-highlight').forEach(function(el) { el.classList.remove('tour-highlight'); });
}

// Auto-start tour for first-time users
document.addEventListener('DOMContentLoaded', function() {
  if (!localStorage.getItem('pulse_tour_seen')) {
    setTimeout(function() { startTour(0); }, 600);
  }
});

// ── Help Modal ──
function showHelpModal() {
  document.getElementById('helpModal').style.display = 'flex';
}
function hideHelpModal() {
  document.getElementById('helpModal').style.display = 'none';
}
