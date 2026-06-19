var supplyChart, storeChart, weekChart;

function chartGridColor() {
  return getComputedStyle(document.documentElement).getPropertyValue('--border-soft').trim() || '#f0f0f0';
}

function initCharts(data) {
  if (typeof Chart === 'undefined') { return; }
  var gc = chartGridColor();
  var c = document.getElementById('chartSupplyStatus');
  if (!c) { return; }
  try {
    if (supplyChart) { supplyChart.destroy(); }
    supplyChart = new Chart(c, {
      type: 'doughnut',
      data: {
        labels: ['In Stock', 'Low Stock', 'Out of Stock'],
        datasets: [{
          data: [data.ok_count, data.low_count, data.critical_count],
          backgroundColor: ['#16a34a', '#eab308', '#dc2626'],
          borderWidth: 0
        }]
      },
      options: {
        responsive: true, maintainAspectRatio: true,
        cutout: '64%',
        plugins: {
          legend: { position: 'bottom', labels: { padding: 10, boxWidth: 10, font: { size: 10 } } }
        }
      }
    });
  } catch(e) { console.error('Supply chart error:', e); }

  try {
    if (storeChart) { storeChart.destroy(); }
    storeChart = new Chart(document.getElementById('chartByStore'), {
      type: 'bar',
      data: {
        labels: data.shortage_by_store.map(function(s) { return s.store; }),
        datasets: [
          { label: 'Shortage', data: data.shortage_by_store.map(function(s) { return s.count; }), backgroundColor: '#dc2626', borderRadius: 4 },
          { label: 'Not Available', data: data.una_by_store.map(function(s) { return s.count; }), backgroundColor: '#eab308', borderRadius: 4 }
        ]
      },
      options: {
        responsive: true, maintainAspectRatio: true,
        plugins: { legend: { position: 'top', labels: { boxWidth: 10, font: { size: 10 } } } },
        scales: { x: { grid: { display: false } }, y: { beginAtZero: true, grid: { color: gc } } }
      }
    });
  } catch(e) { console.error('Store chart error:', e); }

  try {
    if (weekChart) { weekChart.destroy(); }
    weekChart = new Chart(document.getElementById('chartByWeek'), {
      type: 'line',
      data: {
        labels: data.shortage_by_week.map(function(w) { return w.week; }),
        datasets: [
          { label: 'Shortage', data: data.shortage_by_week.map(function(w) { return w.count; }), borderColor: '#dc2626', backgroundColor: 'rgba(220,38,38,.08)', tension: .4, fill: true, pointRadius: 3 },
          { label: 'Not Available', data: data.una_by_week.map(function(w) { return w.count; }), borderColor: '#eab308', backgroundColor: 'rgba(234,179,8,.08)', tension: .4, fill: true, pointRadius: 3 }
        ]
      },
      options: {
        responsive: true, maintainAspectRatio: true,
        plugins: { legend: { position: 'top', labels: { boxWidth: 10, font: { size: 10 } } } },
        scales: { x: { grid: { display: false } }, y: { beginAtZero: true, grid: { color: gc } } }
      }
    });
  } catch(e) { console.error('Week chart error:', e); }
}

function loadTrendChart() {
  var trendC = document.getElementById('trendChart');
  if (!trendC) return;
  if (window._trendChart) { window._trendChart.destroy(); window._trendChart = null; }
  var trGc = chartGridColor();
  try {
    var trendCtx = trendC.getContext('2d');
    var p = getFilterValues();
    var qs = Object.keys(p).map(function(k){return k+'='+p[k]}).join('&');
    csrfFetch('/api/trends'+(qs?'?'+qs:'')).then(function(r){return r.json()}).then(function(td){
      window._trendChart = new Chart(trendCtx, {
        type: 'bar',
        data: {
          labels: td.map(function(t){return t.label}),
          datasets: [
            { label: 'Shortage', data: td.map(function(t){return t.shortage}), backgroundColor: '#b91c1c55', borderColor: '#b91c1c', borderWidth: 1.5, borderRadius: 3 },
            { label: 'Not Available', data: td.map(function(t){return t.una}), backgroundColor: '#e8a31755', borderColor: '#e8a317', borderWidth: 1.5, borderRadius: 3 },
            { label: 'Total', data: td.map(function(t){return t.total}), type: 'line', borderColor: '#0d9488', backgroundColor: 'transparent', borderWidth: 1.5, pointRadius: 2, tension: .3, yAxisID: 'y' }
          ]
        },
        options: {
          responsive: true, maintainAspectRatio: false,
          plugins: { legend: { position: 'top', labels: { boxWidth: 10, font: { size: 9 } } } },
          scales: {
            x: { grid: { display: false }, ticks: { font: { size: 8 } } },
            y: { beginAtZero: true, ticks: { stepSize: 1, font: { size: 9 } }, grid: { color: trGc } }
          }
        }
      });
    }).catch(function(e){});
  } catch(e) {}
}

function updateDashboard(data) {
  document.getElementById('statTotalItems').textContent = data.total_items;
  document.getElementById('statCritTotal').textContent = data.crit_total;
  document.getElementById('statNoncritTotal').textContent = data.noncrit_total;
  document.getElementById('statOk').textContent = data.ok_count;
  document.getElementById('statLow').textContent = data.low_count;
  document.getElementById('statCritical').textContent = data.critical_count;
  document.querySelectorAll('.stat-num').forEach(function(el) { el.classList.remove('stat-pulse'); void el.offsetWidth; el.classList.add('stat-pulse'); });

  if (supplyChart) {
    supplyChart.data.datasets[0].data = [data.ok_count, data.low_count, data.critical_count];
    supplyChart.update();
  }
  if (storeChart) {
    storeChart.data.labels = data.shortage_by_store.map(function(s) { return s.store; });
    storeChart.data.datasets[0].data = data.shortage_by_store.map(function(s) { return s.count; });
    storeChart.data.datasets[1].data = data.una_by_store.map(function(s) { return s.count; });
    storeChart.update();
  }
  if (weekChart) {
    weekChart.data.labels = data.shortage_by_week.map(function(w) { return w.week; });
    weekChart.data.datasets[0].data = data.shortage_by_week.map(function(w) { return w.count; });
    weekChart.data.datasets[1].data = data.una_by_week.map(function(w) { return w.count; });
    weekChart.update();
  }

  var ct = document.querySelector('#criticalTable tbody');
  if (ct) {
    var h = '';
    data.out_of_stock.forEach(function(i) { h += safeHTML`<tr><td><code>${i.code}</code></td><td>${i.name}</td><td>${i.store}</td><td><span class="badge bg-danger">Critical</span></td><td style="text-align:center"><strong>${i.stock}</strong></td><td style="text-align:center">${i.critical}</td><td><span class="badge bg-danger">Out of Stock</span></td><td></td></tr>`; });
    data.critical_items.forEach(function(i) { h += safeHTML`<tr><td><code>${i.code}</code></td><td>${i.name}</td><td>${i.store}</td><td><span class="badge bg-danger">Critical</span></td><td style="text-align:center"><strong>${i.stock}</strong></td><td style="text-align:center">${i.critical}</td><td><span class="badge bg-warning" style="color:#1a1a2e">Low</span></td><td></td></tr>`; });
    if (!data.out_of_stock.length && !data.critical_items.length) h = '<tr><td colspan="8" class="text-center text-muted" style="padding:2rem">All supplies are at healthy levels</td></tr>';
    ct.innerHTML = h;
  }

  var rt = document.querySelector('#recentTable tbody');
  if (rt) {
    var h2 = '';
    data.recent.forEach(function(r) {
      var b = r.status === 'Shortage' ? 'badge-outline-danger' : 'badge-outline-warning';
      h2 += safeHTML`<tr><td><code>${r.item.split(' - ')[0]}</code> ${r.item.split(' - ').slice(1).join(' - ')}</td><td>${r.store}</td><td>${r.unit}</td><td>${r.ward}</td><td><span class="${b}">${r.status}</span></td><td>${r.week}</td><td>${r.date}</td></tr>`;
    });
    if (!data.recent.length) h2 = '<tr><td colspan="7" class="text-center text-muted" style="padding:2rem">No reports yet</td></tr>';
    rt.innerHTML = h2;
  }
}

function applyMonthYearPreset(preset) {
  var now = new Date();
  var m = document.getElementById('filterMonth');
  var y = document.getElementById('filterYear');
  if (preset === 'this-month') {
    m.value = now.getMonth() + 1;
    y.value = now.getFullYear();
  } else if (preset === 'last-month') {
    var d = new Date(now.getFullYear(), now.getMonth() - 1, 1);
    m.value = d.getMonth() + 1;
    y.value = d.getFullYear();
  } else if (preset === 'this-year') {
    m.value = '';
    y.value = now.getFullYear();
  }
  document.getElementById('customRangeWrap').style.display = 'none';
  document.getElementById('customRangeToggle').textContent = 'Custom ▾';
  document.getElementById('filterFrom').value = '';
  document.getElementById('filterTo').value = '';
  applyFilters();
}

function hasActiveFilter() {
  var p = getFilterValues();
  return !!(p.month || p.year || p.from || p.to);
}

function showChartPlaceholders(show) {
  document.querySelectorAll('.chart-placeholder').forEach(function(el) {
    el.style.display = show ? 'flex' : 'none';
  });
}

function destroyAllCharts() {
  if (supplyChart) { supplyChart.destroy(); supplyChart = null; }
  if (storeChart) { storeChart.destroy(); storeChart = null; }
  if (weekChart) { weekChart.destroy(); weekChart = null; }
  if (window._trendChart) { window._trendChart.destroy(); window._trendChart = null; }
}

function getFilterValues() {
  var p = {};
  var m = document.getElementById('filterMonth');
  var y = document.getElementById('filterYear');
  var f = document.getElementById('filterFrom');
  var t = document.getElementById('filterTo');
  var customVis = document.getElementById('customRangeWrap').style.display !== 'none';
  if (customVis) {
    if (f && f.value) p.from = f.value;
    if (t && t.value) p.to = t.value;
  } else {
    if (m && m.value) p.month = m.value;
    if (y && y.value) p.year = y.value;
  }
  return p;
}

function apiUrl() {
  var p = getFilterValues();
  var q = Object.keys(p).map(function(k) { return k + '=' + p[k]; }).join('&');
  return '/api/dashboard' + (q ? '?' + q : '');
}

function fetchDashboard() {
  var els = document.querySelectorAll('.chart-canvas-wrap');
  els.forEach(function(el) { el.style.opacity = '0.5'; });
  csrfFetch(apiUrl()).then(function(r){return r.json()}).then(function(d){
    els.forEach(function(el) { el.style.opacity = '1'; });
    if (!supplyChart || !storeChart || !weekChart) {
      initCharts(d);
    }
    updateDashboard(d);
    loadTrendChart();
  }).catch(function(){
    els.forEach(function(el) { el.style.opacity = '1'; });
  });
}

function pollDashboard() {
  if (!hasActiveFilter()) return;
  csrfFetch(apiUrl()).then(function(r){return r.json()}).then(function(d){updateDashboard(d)}).catch(function(){});
}

function applyFilters() {
  var p = getFilterValues();
  var qs = Object.keys(p).map(function(k) { return k + '=' + encodeURIComponent(p[k]); }).join('&');
  var url = window.location.pathname + (qs ? '?' + qs : '');
  history.replaceState(null, '', url);
  if (hasActiveFilter()) {
    showChartPlaceholders(false);
    fetchDashboard();
  } else {
    showChartPlaceholders(true);
    destroyAllCharts();
    csrfFetch('/api/dashboard').then(function(r){return r.json()}).then(function(d){updateDashboard(d)}).catch(function(){});
  }
}

document.querySelectorAll('canvas[id^="chart"], canvas#trendChart').forEach(function(c) {
  var wrap = c.parentElement;
  wrap.classList.add('chart-canvas-wrap');
  wrap.style.transition = 'opacity .25s ease';
});

document.querySelectorAll('.range-preset').forEach(function(btn) {
  btn.addEventListener('click', function(e) {
    e.preventDefault();
    applyMonthYearPreset(this.getAttribute('data-preset'));
  });
});

document.getElementById('customRangeToggle').addEventListener('click', function(e) {
  e.preventDefault();
  var wrap = document.getElementById('customRangeWrap');
  var isHidden = wrap.style.display === 'none' || !wrap.style.display;
  wrap.style.display = isHidden ? 'flex' : 'none';
  this.textContent = isHidden ? 'Custom ▴' : 'Custom ▾';
});

document.getElementById('filterMonth').addEventListener('change', applyFilters);
document.getElementById('filterYear').addEventListener('change', applyFilters);
document.getElementById('filterFrom').addEventListener('change', applyFilters);
document.getElementById('filterTo').addEventListener('change', applyFilters);
document.getElementById('filterBtn').addEventListener('click', applyFilters);
document.getElementById('clearFilters').addEventListener('click', function(e) {
  e.preventDefault();
  document.getElementById('filterMonth').value = '';
  document.getElementById('filterYear').value = '';
  document.getElementById('filterFrom').value = '';
  document.getElementById('filterTo').value = '';
  document.getElementById('customRangeWrap').style.display = 'none';
  document.getElementById('customRangeToggle').textContent = 'Custom ▾';
  history.replaceState(null, '', window.location.pathname);
  showChartPlaceholders(true);
  destroyAllCharts();
  csrfFetch('/api/dashboard').then(function(r){return r.json()}).then(function(d){updateDashboard(d)}).catch(function(){});
});

function showLoading(show) {
  var els = document.querySelectorAll('.stat-num');
  els.forEach(function(el) {
    if (show) {
      if (!el.getAttribute('data-val')) el.setAttribute('data-val', el.textContent);
      el.innerHTML = '<span class="skel-block" style="width:60%;height:1.4rem;margin:0 auto"></span>';
    } else if (el.getAttribute('data-val')) {
      el.textContent = el.getAttribute('data-val');
      el.removeAttribute('data-val');
    }
  });
  document.querySelectorAll('.table tbody').forEach(function(tb) {
    if (show) {
      if (!tb.getAttribute('data-html')) tb.setAttribute('data-html', tb.innerHTML);
      tb.innerHTML = '';
      for (var i = 0; i < 3; i++) {
        tb.innerHTML += '<tr><td colspan="8"><span class="skel-block" style="width:100%;height:1rem"></span></td></tr>';
      }
    } else if (tb.getAttribute('data-html')) {
      tb.innerHTML = tb.getAttribute('data-html');
      tb.removeAttribute('data-html');
    }
  });
}

document.addEventListener('DOMContentLoaded', function() {
  showLoading(true);
  try {
    window.pollInterval = parseInt(document.cookie.split('; ').find(function(r){return r.startsWith('poll=')})?.split('=')[1]) || 10000;
  } catch(e) { window.pollInterval = 10000; }
  document.getElementById('pollIntervalLabel').textContent = Math.round(window.pollInterval / 10) / 100 + 's';

  if (hasActiveFilter()) {
    showChartPlaceholders(false);
    csrfFetch(apiUrl()).then(function(r){return r.json()}).then(function(d){showLoading(false);initCharts(d);updateDashboard(d);loadTrendChart()}).catch(function(){showLoading(false)});
  } else {
    showLoading(false);
    showChartPlaceholders(true);
  }
  setInterval(pollDashboard, window.pollInterval || 10000);
});