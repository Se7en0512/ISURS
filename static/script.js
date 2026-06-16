// highlight active nav link
var currentPath = window.location.pathname;
document.querySelectorAll('.sidebar .nav-link').forEach(function(link) {
  var href = link.getAttribute('href');
  if (currentPath === href || (href !== '/' && currentPath.startsWith(href))) {
    link.classList.add('active');
  }
});

// auto-dismiss alerts
document.querySelectorAll('.alert-dismissible').forEach(function(a) {
  setTimeout(function() {
    var bs = new bootstrap.Alert(a);
    bs.close();
  }, 4500);
});
