(function () {
  var shell = document.getElementById("portal-shell");
  var sidebarToggle = document.getElementById("sidebar-toggle");
  var mobileToggle = document.getElementById("mobile-sidebar-toggle");
  if (sidebarToggle && shell) {
    sidebarToggle.addEventListener("click", function () {
      shell.classList.toggle("is-collapsed");
    });
  }
  if (mobileToggle && shell) {
    mobileToggle.addEventListener("click", function () {
      shell.classList.toggle("is-mobile-open");
    });
  }
})();
