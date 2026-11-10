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

  // Publications: show the first few, expand to all on request, filter by research interest.
  var list = function (selector) { return Array.prototype.slice.call(document.querySelectorAll(selector)); };
  var pubs = document.getElementById("pubs-list");
  var pubsToggle = document.querySelector(".pubs-toggle");
  var pubRows = list("#pubs-list .pub-row");
  var chips = list(".pub-filters .chip");
  var activeArea = "";

  if (pubs && pubsToggle) {
    pubsToggle.addEventListener("click", function () {
      var expand = pubs.classList.contains("is-collapsed");
      pubs.classList.toggle("is-collapsed", !expand);
      pubsToggle.setAttribute("aria-expanded", String(expand));
      pubsToggle.textContent = expand ? pubsToggle.dataset.less : pubsToggle.dataset.more;
      if (!expand) document.getElementById("publications").scrollIntoView({ block: "start" });
    });
  }

  // One filter state: the chips above the list show it; the "N papers" links on the research cards set it.
  function setFilter(area) {
    activeArea = area || "";
    pubRows.forEach(function (row) { row.classList.toggle("is-out", !!activeArea && row.dataset.area !== activeArea); });
    if (pubs) pubs.classList.toggle("is-filtering", !!activeArea);
    chips.forEach(function (chip) {
      var on = chip.dataset.filter === activeArea;
      chip.classList.toggle("is-active", on);
      chip.setAttribute("aria-pressed", String(on));
    });
  }
  chips.forEach(function (chip) {
    chip.addEventListener("click", function () {
      setFilter(chip.dataset.filter === activeArea ? "" : chip.dataset.filter);
    });
  });
  list("a[data-filter]").forEach(function (link) {
    link.addEventListener("click", function (ev) {
      ev.preventDefault();
      setFilter(link.dataset.filter);
      document.getElementById("publications").scrollIntoView({ block: "start" });
    });
  });

  // Copy buttons (email, BibTeX, install command). The label reports what actually happened.
  function copyText(text) {
    var legacy = function () {
      return new Promise(function (resolve, reject) {
        var ta = document.createElement("textarea");
        ta.value = text;
        ta.setAttribute("readonly", "");
        ta.style.cssText = "position:fixed;top:0;left:0;opacity:0";
        document.body.appendChild(ta);
        ta.select();
        var ok = false;
        try { ok = document.execCommand("copy"); } catch (e) {}
        document.body.removeChild(ta);
        if (ok) { resolve(); } else { reject(); }
      });
    };
    if (navigator.clipboard && window.isSecureContext) {
      return navigator.clipboard.writeText(text).catch(legacy);
    }
    return legacy();
  }
  document.querySelectorAll("[data-copy]").forEach(function (btn) {
    var target = btn.querySelector("[data-copy-label]") || btn;
    var label = target.textContent;
    var timer;
    var show = function (text, copied) {
      btn.style.minWidth = btn.offsetWidth + "px"; // keep the width while the label changes
      target.textContent = text;
      btn.classList.toggle("is-copied", copied);
      clearTimeout(timer);
      timer = setTimeout(function () {
        target.textContent = label;
        btn.classList.remove("is-copied");
        btn.style.minWidth = "";
      }, 1600);
    };
    btn.addEventListener("click", function () {
      copyText(btn.dataset.copy).then(
        function () { show(btn.dataset.done || "Copied", true); },
        function () { show("Copy failed", false); }
      );
    });
  });
})();
