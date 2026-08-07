/**
 * Shared UI: mobile menus, sticky header shadow, button ripples, marketing drawer.
 */
(function () {
  function onReady(fn) {
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", fn);
    else fn();
  }

  function initMarketingNav() {
    var header = document.querySelector(".js-site-header");
    if (!header) return;
    var toggle = document.querySelector(".js-nav-toggle");
    var drawer = document.querySelector(".js-mobile-drawer");
    var closeBtn = document.querySelector(".js-mobile-close");
    var backdrop = drawer && drawer.querySelector(".mobile-drawer__backdrop");

    function setOpen(open) {
      if (!drawer) return;
      drawer.classList.toggle("is-open", open);
      document.body.style.overflow = open ? "hidden" : "";
    }

    if (toggle && drawer) {
      toggle.addEventListener("click", function () {
        setOpen(!drawer.classList.contains("is-open"));
      });
    }
    if (closeBtn) closeBtn.addEventListener("click", function () { setOpen(false); });
    if (backdrop) backdrop.addEventListener("click", function () { setOpen(false); });

    window.addEventListener(
      "scroll",
      function () {
        header.classList.toggle("is-scrolled", window.scrollY > 8);
      },
      { passive: true }
    );
  }

  function initAppSidebar() {
    var openBtn = document.querySelector(".js-sidebar-open");
    var sidebar = document.querySelector(".js-sidebar");
    var backdrop = document.querySelector(".js-sidebar-backdrop");
    var closeBtn = document.querySelector(".js-sidebar-close");

    function setOpen(open) {
      if (!sidebar) return;
      sidebar.classList.toggle("is-open", open);
      if (backdrop) backdrop.classList.toggle("is-visible", open);
      document.body.style.overflow = open ? "hidden" : "";
    }

    if (openBtn) openBtn.addEventListener("click", function () { setOpen(true); });
    if (closeBtn) closeBtn.addEventListener("click", function () { setOpen(false); });
    if (backdrop) backdrop.addEventListener("click", function () { setOpen(false); });
  }

  function initRipples() {
    document.body.addEventListener(
      "click",
      function (e) {
        var btn = e.target.closest(".btn--ripple");
        if (!btn || btn.disabled) return;
        var rect = btn.getBoundingClientRect();
        var x = e.clientX - rect.left;
        var y = e.clientY - rect.top;
        var ripple = document.createElement("span");
        ripple.className = "ripple";
        ripple.style.left = x + "px";
        ripple.style.top = y + "px";
        btn.appendChild(ripple);
        setTimeout(function () {
          ripple.remove();
        }, 600);
      },
      true
    );
  }

  onReady(function () {
    initMarketingNav();
    initAppSidebar();
    initRipples();
  });
})();
