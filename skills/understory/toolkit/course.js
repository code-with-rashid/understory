/* ============================================================
   UNDERSTORY — course engine
   Copy verbatim into a course. Never hand-edit.

   Two rules make this hard to break from markup:
     1. Nothing is wired by inline onclick. Every component is
        found by its data-u attribute, so markup cannot call a
        function that does not exist.
     2. Every component instance is looked up and initialised
        inside its own container, in its own try/catch. One bad
        instance cannot take down the others.
   ============================================================ */
(function () {
  "use strict";

  var reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function all(sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); }
  function one(sel, root) { return (root || document).querySelector(sel); }
  function on(el, ev, fn) { if (el) el.addEventListener(ev, fn); }

  var parts = {};
  function part(name, fn) { parts[name] = fn; }

  function boot() {
    document.documentElement.classList.add("js");
    Object.keys(parts).forEach(function (name) {
      all('[data-u="' + name + '"]').forEach(function (el, i) {
        try {
          parts[name](el);
        } catch (err) {
          console.error("[understory] " + name + " #" + (i + 1) + " failed to start:", err);
        }
      });
    });
  }

  /* ── RAIL & PROGRESS ────────────────────────────────────── */
  part("rail", function (rail) {
    var links = all("[data-u-goto]", rail);
    var bar = one('[data-u="progress"]');
    var chapters = links
      .map(function (l) { return document.getElementById(l.getAttribute("data-u-goto")); })
      .filter(Boolean);

    links.forEach(function (link) {
      on(link, "click", function () {
        var target = document.getElementById(link.getAttribute("data-u-goto"));
        if (target) target.scrollIntoView({ behavior: reduced ? "auto" : "smooth", block: "start" });
      });
    });

    function paint() {
      var doc = document.documentElement;
      var scrollable = doc.scrollHeight - window.innerHeight;
      if (bar) bar.style.width = (scrollable > 0 ? (window.scrollY / scrollable) * 100 : 0) + "%";

      var mid = window.scrollY + window.innerHeight / 2;
      chapters.forEach(function (chapter, i) {
        var link = links[i];
        var top = chapter.offsetTop;
        var bottom = top + chapter.offsetHeight;
        var current = mid >= top && mid < bottom;
        link.setAttribute("aria-current", current ? "true" : "false");
        link.setAttribute("data-seen", window.scrollY + window.innerHeight > top ? "true" : "false");
        if (current) link.scrollIntoView({ block: "nearest", inline: "nearest" });
      });
    }

    var ticking = false;
    on(window, "scroll", function () {
      if (ticking) return;
      ticking = true;
      window.requestAnimationFrame(function () { paint(); ticking = false; });
    });
    on(window, "resize", paint);
    paint();

    on(document, "keydown", function (e) {
      if (/^(INPUT|TEXTAREA|SELECT)$/.test(e.target.tagName) || e.metaKey || e.ctrlKey) return;
      var step = e.key === "j" || e.key === "J" ? 1 : (e.key === "k" || e.key === "K" ? -1 : 0);
      if (!step) return;
      var mid = window.scrollY + window.innerHeight / 2;
      var at = 0;
      chapters.forEach(function (c, i) { if (mid >= c.offsetTop) at = i; });
      var next = chapters[at + step];
      if (next) { next.scrollIntoView({ behavior: reduced ? "auto" : "smooth" }); e.preventDefault(); }
    });
  });

  /* ── REVEAL ─────────────────────────────────────────────── */
  function revealAll() { all(".u-reveal").forEach(function (el) { el.classList.add("is-in"); }); }

  function startReveal() {
    if (reduced || !("IntersectionObserver" in window)) { revealAll(); return; }
    try {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          entry.target.classList.add("is-in");
          io.unobserve(entry.target);
        });
      }, { rootMargin: "0px 0px -6% 0px", threshold: 0.05 });
      all(".u-reveal").forEach(function (el) { io.observe(el); });
    } catch (err) {
      console.error("[understory] reveal failed, showing everything:", err);
      revealAll();
    }
  }

  /* ── GLOSS ──────────────────────────────────────────────── */
  var popoverOK = typeof HTMLElement !== "undefined" && "popover" in HTMLElement.prototype;

  part("gloss", function (term) {
    var def = document.getElementById(term.getAttribute("popovertarget") || "");
    if (!def) return;

    function place() {
      var a = term.getBoundingClientRect();
      var d = def.getBoundingClientRect();
      var left = Math.min(Math.max(8, a.left + a.width / 2 - d.width / 2), window.innerWidth - d.width - 8);
      var above = a.top - d.height - 10;
      def.style.left = left + "px";
      def.style.top = (above > 8 ? above : a.bottom + 10) + "px";
    }

    if (popoverOK) {
      on(def, "toggle", function (e) { if (e.newState === "open") place(); });
      on(window, "resize", function () { if (def.matches(":popover-open")) place(); });
      return;
    }

    // Older engines: same behaviour, manual show/hide.
    def.style.display = "none";
    function show() { def.style.display = "block"; place(); }
    function hide() { def.style.display = "none"; }
    on(term, "click", function (e) {
      e.stopPropagation();
      def.style.display === "block" ? hide() : show();
    });
    on(document, "click", hide);
    on(document, "keydown", function (e) { if (e.key === "Escape") hide(); });
  });

  /* ── CHECK (quiz) ───────────────────────────────────────── */
  part("check", function (check) {
    all("[data-u-question]", check).forEach(function (q) {
      var opts = all("[data-u-answer]", q);
      var result = one("[data-u-result]", q);
      opts.forEach(function (opt) {
        opt.setAttribute("aria-pressed", "false");
        on(opt, "click", function () {
          opts.forEach(function (o) { o.setAttribute("aria-pressed", "false"); });
          opt.setAttribute("aria-pressed", "true");
        });
      });
    });

    on(one("[data-u-mark]", check), "click", function () {
      all("[data-u-question]", check).forEach(function (q) {
        var opts = all("[data-u-answer]", q);
        var picked = opts.filter(function (o) { return o.getAttribute("aria-pressed") === "true"; })[0];
        var result = one("[data-u-result]", q);
        var right = q.getAttribute("data-u-correct");

        if (!picked) {
          if (result) {
            result.textContent = "Pick an answer first.";
            result.setAttribute("data-state", "empty");
          }
          return;
        }
        opts.forEach(function (o) { o.disabled = true; });
        var won = picked.getAttribute("data-u-answer") === right;
        picked.setAttribute("data-verdict", won ? "right" : "wrong");
        if (!won) {
          opts.forEach(function (o) {
            if (o.getAttribute("data-u-answer") === right) o.setAttribute("data-verdict", "right");
          });
        }
        if (result) {
          result.textContent = (won ? "Yes. " : "Not quite. ") +
            (q.getAttribute(won ? "data-u-if-right" : "data-u-if-wrong") || "");
          result.setAttribute("data-state", won ? "right" : "wrong");
        }
      });
    });

    on(one("[data-u-again]", check), "click", function () {
      all("[data-u-answer]", check).forEach(function (o) {
        o.disabled = false;
        o.setAttribute("aria-pressed", "false");
        o.removeAttribute("data-verdict");
      });
      all("[data-u-result]", check).forEach(function (r) {
        r.textContent = "";
        r.removeAttribute("data-state");
      });
    });
  });

  /* ── TRACE (step-through flow) ──────────────────────────── */
  part("trace", function (trace) {
    var steps = [];
    try {
      steps = JSON.parse(trace.getAttribute("data-u-steps") || "[]");
    } catch (err) {
      console.error("[understory] trace steps are not valid JSON — an apostrophe inside a " +
                    "single-quoted attribute is the usual cause:", err);
    }

    var caption = one("[data-u-caption]", trace);
    var counter = one("[data-u-count]", trace);
    var pulse = one("[data-u-pulse]", trace);
    var at = 0;

    // Nodes are resolved inside this container only, so two traces on one
    // page may use the same node names without colliding.
    function node(name) { return name ? one('[data-u-node="' + name + '"]', trace) : null; }

    function count() { if (counter) counter.textContent = at + " / " + steps.length; }

    function sendPulse(fromName, toName) {
      var from = node(fromName), to = node(toName);
      if (!pulse || !from || !to) {
        if (!from || !to) console.warn("[understory] trace: no node named", fromName, "or", toName);
        return;
      }
      if (reduced) return;
      var box = trace.getBoundingClientRect();
      var a = from.getBoundingClientRect();
      var b = to.getBoundingClientRect();
      pulse.style.setProperty("--from-x", (a.left + a.width / 2 - box.left) + "px");
      pulse.style.setProperty("--from-y", (a.top + a.height / 2 - box.top) + "px");
      pulse.style.setProperty("--to-x", (b.left + b.width / 2 - box.left) + "px");
      pulse.style.setProperty("--to-y", (b.top + b.height / 2 - box.top) + "px");
      pulse.classList.remove("is-moving");
      void pulse.offsetWidth;
      pulse.classList.add("is-moving");
    }

    function advance() {
      if (at >= steps.length) return;
      var step = steps[at];
      all("[data-u-node]", trace).forEach(function (n) { n.setAttribute("data-lit", "false"); });
      var lit = node(step.at);
      if (lit) lit.setAttribute("data-lit", "true");
      else if (step.at) console.warn("[understory] trace: no node named", step.at);
      if (step.from && step.to) sendPulse(step.from, step.to);
      if (caption) caption.textContent = step.say || "";
      at++;
      count();
    }

    on(one("[data-u-next]", trace), "click", advance);
    on(one("[data-u-restart]", trace), "click", function () {
      at = 0;
      all("[data-u-node]", trace).forEach(function (n) { n.setAttribute("data-lit", "false"); });
      if (caption) caption.textContent = caption.getAttribute("data-u-idle") || "";
      count();
    });
    count();
  });

  /* ── THREAD (component dialogue) ────────────────────────── */
  part("thread", function (thread) {
    var msgs = all("[data-u-msg]", thread);
    var typing = one("[data-u-typing]", thread);
    var typingWho = one("[data-u-typing-who]", thread);
    var counter = one("[data-u-count]", thread);
    var at = 0;
    var timer = null;

    function count() { if (counter) counter.textContent = at + " / " + msgs.length; }

    function reveal(msg) {
      msg.hidden = false;
      if (!reduced) {
        msg.classList.add("is-new");
        setTimeout(function () { msg.classList.remove("is-new"); }, 320);
      }
      at++;
      count();
    }

    function next() {
      if (at >= msgs.length) return false;
      var msg = msgs[at];
      var who = one("[data-u-who]", msg);
      if (typing && !reduced) {
        if (typingWho && who) {
          typingWho.textContent = who.textContent.trim();
          typingWho.style.background = who.style.background;
        }
        typing.hidden = false;
        setTimeout(function () { typing.hidden = true; reveal(msg); }, 650);
      } else {
        reveal(msg);
      }
      return true;
    }

    function reset() {
      if (timer) { clearInterval(timer); timer = null; }
      at = 0;
      msgs.forEach(function (m) { m.hidden = true; });
      if (typing) typing.hidden = true;
      count();
    }

    on(one("[data-u-next]", thread), "click", next);
    on(one("[data-u-playall]", thread), "click", function () {
      if (timer) return;
      timer = setInterval(function () {
        if (!next()) { clearInterval(timer); timer = null; }
      }, reduced ? 120 : 1000);
    });
    on(one("[data-u-restart]", thread), "click", reset);

    msgs.forEach(function (m) { m.hidden = true; });
    count();
  });

  /* ── MATCH (drag, drop, or tap) ─────────────────────────── */
  part("match", function (match) {
    var chips = all("[data-u-chip]", match);
    var slots = all("[data-u-slot]", match);
    var result = one("[data-u-result]", match);
    var armed = null;

    function place(slot, chip) {
      slot.textContent = chip.textContent;
      slot.setAttribute("data-u-holds", chip.getAttribute("data-u-chip"));
      slot.removeAttribute("data-verdict");
      chip.setAttribute("data-used", "true");
      if (armed) { armed.classList.remove("is-armed"); armed = null; }
    }

    function chipFor(key) {
      return chips.filter(function (c) { return c.getAttribute("data-u-chip") === key; })[0];
    }

    chips.forEach(function (chip) {
      chip.setAttribute("draggable", "true");

      on(chip, "dragstart", function (e) {
        e.dataTransfer.setData("text/plain", chip.getAttribute("data-u-chip"));
        chip.classList.add("is-lifted");
      });
      on(chip, "dragend", function () { chip.classList.remove("is-lifted"); });

      // Tap-to-place: works on touch, and is the keyboard path too.
      on(chip, "click", function () {
        if (armed === chip) { chip.classList.remove("is-armed"); armed = null; return; }
        if (armed) armed.classList.remove("is-armed");
        armed = chip;
        chip.classList.add("is-armed");
      });
    });

    slots.forEach(function (slot) {
      on(slot, "dragover", function (e) { e.preventDefault(); slot.classList.add("is-over"); });
      on(slot, "dragleave", function () { slot.classList.remove("is-over"); });
      on(slot, "drop", function (e) {
        e.preventDefault();
        slot.classList.remove("is-over");
        var chip = chipFor(e.dataTransfer.getData("text/plain"));
        if (chip) place(slot, chip);
      });
      on(slot, "click", function () { if (armed) place(slot, armed); });
      on(slot, "keydown", function (e) {
        if ((e.key === "Enter" || e.key === " ") && armed) { e.preventDefault(); place(slot, armed); }
      });
    });

    on(one("[data-u-mark]", match), "click", function () {
      var filled = 0, right = 0;
      slots.forEach(function (slot) {
        var holds = slot.getAttribute("data-u-holds");
        if (!holds) return;
        filled++;
        var ok = holds === slot.getAttribute("data-u-slot");
        slot.setAttribute("data-verdict", ok ? "right" : "wrong");
        if (ok) right++;
      });
      if (!result) return;
      if (!filled) {
        result.textContent = "Put a chip in a slot first.";
        result.setAttribute("data-state", "empty");
      } else if (right === slots.length) {
        result.textContent = "All " + slots.length + " matched.";
        result.setAttribute("data-state", "right");
      } else {
        result.textContent = right + " of " + slots.length + " matched — the red ones are worth another look.";
        result.setAttribute("data-state", "wrong");
      }
    });

    on(one("[data-u-again]", match), "click", function () {
      slots.forEach(function (slot) {
        slot.textContent = slot.getAttribute("data-u-empty") || "Drop or tap here";
        slot.removeAttribute("data-u-holds");
        slot.removeAttribute("data-verdict");
      });
      chips.forEach(function (c) { c.removeAttribute("data-used"); c.classList.remove("is-armed"); });
      if (armed) { armed = null; }
      if (result) { result.textContent = ""; result.removeAttribute("data-state"); }
    });
  });

  /* ── HUNT (spot the bug) ────────────────────────────────── */
  part("hunt", function (hunt) {
    var lines = all("[data-u-line]", hunt);
    var result = one("[data-u-result]", hunt);

    lines.forEach(function (line) {
      on(line, "click", function () {
        var isBug = line.getAttribute("data-u-line") === "bug";
        if (isBug) {
          line.setAttribute("data-verdict", "right");
          lines.forEach(function (l) { l.disabled = true; });
          if (result) {
            result.textContent = "Found it. " + (line.getAttribute("data-u-why") || "");
            result.setAttribute("data-state", "right");
          }
        } else {
          line.setAttribute("data-verdict", "wrong");
          if (result) {
            result.textContent = line.getAttribute("data-u-why") || "Not this line — keep looking.";
            result.setAttribute("data-state", "wrong");
          }
          setTimeout(function () {
            line.removeAttribute("data-verdict");
            if (result) result.removeAttribute("data-state");
          }, 2200);
        }
      });
    });
  });

  /* ── MAP (architecture) ─────────────────────────────────── */
  part("map", function (map) {
    var partsList = all("[data-u-part]", map);
    var readout = one("[data-u-readout]", map);
    partsList.forEach(function (item) {
      item.setAttribute("aria-pressed", "false");
      on(item, "click", function () {
        partsList.forEach(function (p) { p.setAttribute("aria-pressed", "false"); });
        item.setAttribute("aria-pressed", "true");
        if (readout) readout.textContent = item.getAttribute("data-u-part") || "";
      });
    });
  });

  /* ── STACK (layer toggle) ───────────────────────────────── */
  part("stack", function (stack) {
    var tabs = all("[data-u-tab]", stack);
    tabs.forEach(function (tab) {
      on(tab, "click", function () {
        tabs.forEach(function (t) {
          var pane = one('[data-u-pane="' + t.getAttribute("data-u-tab") + '"]', stack);
          var chosen = t === tab;
          t.setAttribute("aria-selected", chosen ? "true" : "false");
          if (pane) pane.hidden = !chosen;
        });
      });
      on(tab, "keydown", function (e) {
        var i = tabs.indexOf(tab);
        var to = e.key === "ArrowRight" ? tabs[i + 1] : (e.key === "ArrowLeft" ? tabs[i - 1] : null);
        if (to) { e.preventDefault(); to.focus(); to.click(); }
      });
    });
  });

  /* ── GO ─────────────────────────────────────────────────── */
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () { boot(); startReveal(); });
  } else {
    boot();
    startReveal();
  }
})();
