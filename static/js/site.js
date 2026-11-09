// Small enhancements; the page works without them.
(function () {
  // Forget the theme choice saved by the earlier dark-mode toggle (the site now has one theme).
  try { localStorage.removeItem("theme"); } catch (e) {}

  // Nav border once the page scrolls.
  var nav = document.querySelector(".nav");
  if (nav) {
    var onScroll = function () { nav.classList.toggle("is-scrolled", window.scrollY > 8); };
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
  }

  // Reveal sections as they scroll into view.
  var items = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); }
      });
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.08 });
    items.forEach(function (el) { io.observe(el); });
  } else {
    items.forEach(function (el) { el.classList.add("in"); });
  }

  // Spotlight that follows the pointer on cards.
  document.querySelectorAll("[data-spotlight]").forEach(function (card) {
    card.addEventListener("pointermove", function (ev) {
      var r = card.getBoundingClientRect();
      card.style.setProperty("--mx", (ev.clientX - r.left) + "px");
      card.style.setProperty("--my", (ev.clientY - r.top) + "px");
    });
  });

  // Expandable "Representative work" lists.
  document.querySelectorAll(".rtoggle").forEach(function (btn) {
    btn.addEventListener("click", function () {
      btn.setAttribute("aria-expanded", String(btn.getAttribute("aria-expanded") !== "true"));
    });
  });

  // Publications: show the first few, expand to all on request.
  var pubs = document.getElementById("pubs-list");
  var pubsToggle = document.querySelector(".pubs-toggle");
  if (pubs && pubsToggle) {
    pubsToggle.addEventListener("click", function () {
      var expand = pubs.classList.contains("is-collapsed");
      pubs.classList.toggle("is-collapsed", !expand);
      pubsToggle.setAttribute("aria-expanded", String(expand));
      pubsToggle.textContent = expand ? pubsToggle.dataset.less : pubsToggle.dataset.more;
      if (!expand) document.getElementById("publications").scrollIntoView({ block: "start" });
    });
  }

  // Copy buttons (install command, email, BibTeX).
  document.querySelectorAll("[data-copy]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var label = btn.textContent;
      var done = function () {
        btn.textContent = btn.dataset.done || "Copied";
        setTimeout(function () { btn.textContent = label; }, 1500);
      };
      if (navigator.clipboard) { navigator.clipboard.writeText(btn.dataset.copy).then(done, done); } else { done(); }
    });
  });
})();
