/* Assertions run inside the page, so the runner needs no browser-automation
   library: Chrome loads the fixture, the harness drives it, and the results
   are written into #u-test-results for `run.py` to read out of the DOM. */
(function () {
  "use strict";

  var results = [];
  function check(name, fn) {
    try {
      var outcome = fn();
      if (outcome === true || outcome === undefined) results.push({ name: name, ok: true });
      else results.push({ name: name, ok: false, detail: String(outcome) });
    } catch (err) {
      results.push({ name: name, ok: false, detail: err && err.message ? err.message : String(err) });
    }
  }

  function $(sel, root) { return (root || document).querySelector(sel); }
  function $$(sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); }
  function wait(ms) { return new Promise(function (r) { setTimeout(r, ms); }); }
  function near(a, b, slack) { return Math.abs(a - b) <= (slack || 1.5); }

  async function run() {
    /* ── boot ─────────────────────────────────────────────── */
    check("html gets the js class", function () {
      return document.documentElement.classList.contains("js") || "no .js class";
    });

    check("markup contains no inline handlers", function () {
      var html = document.documentElement.innerHTML;
      return !/\son(click|change|submit)=/i.test(html) || "found an inline handler";
    });

    check("reveal marks content visible", function () {
      var n = $$(".u-reveal.is-in").length;
      return n > 0 || "nothing was revealed";
    });

    /* ── check (quiz) ─────────────────────────────────────── */
    check("quiz: selecting sets aria-pressed", function () {
      var opt = $('#check-a [data-u-answer="a"]');
      opt.click();
      return opt.getAttribute("aria-pressed") === "true" || "aria-pressed not set";
    });

    check("quiz: a wrong answer is marked wrong and the right one is shown", function () {
      $("#check-a [data-u-mark]").click();
      var wrong = $('#check-a [data-u-answer="a"]').getAttribute("data-verdict");
      var right = $('#check-a [data-u-answer="b"]').getAttribute("data-verdict");
      var result = $("#check-a [data-u-result]");
      if (wrong !== "wrong") return "picked answer not marked wrong, got " + wrong;
      if (right !== "right") return "correct answer not revealed";
      if (result.getAttribute("data-state") !== "wrong") return "result state wrong";
      return result.textContent.indexOf("Think again") > -1 || "explanation missing";
    });

    check("quiz: options lock after marking", function () {
      return $('#check-a [data-u-answer="a"]').disabled === true || "options still enabled";
    });

    check("quiz: reset clears everything", function () {
      $("#check-a [data-u-again]").click();
      var opt = $('#check-a [data-u-answer="a"]');
      if (opt.disabled) return "still disabled";
      if (opt.getAttribute("data-verdict")) return "verdict still set";
      return !$("#check-a [data-u-result]").getAttribute("data-state") || "result still showing";
    });

    check("quiz: marking with nothing picked asks for an answer", function () {
      $("#check-a [data-u-mark]").click();
      return $("#check-a [data-u-result]").getAttribute("data-state") === "empty" || "no empty state";
    });

    /* ── trace ────────────────────────────────────────────── */
    check("trace: first step lights its own node", function () {
      $("#trace-a [data-u-next]").click();
      var lit = $('#trace-a [data-u-node="one"]').getAttribute("data-lit");
      return lit === "true" || "node not lit";
    });

    check("trace: caption and counter advance", function () {
      var caption = $("#trace-a [data-u-caption]").textContent;
      var count = $("#trace-a [data-u-count]").textContent;
      if (caption.indexOf("Start at one") === -1) return "caption not set: " + caption;
      return count.indexOf("1 / 2") > -1 || "counter reads " + count;
    });

    // The regression test for the bug that started this project: two traces
    // reusing node names must each animate against their own nodes.
    check("trace: a second trace with the same node names pulses inside itself", function () {
      $("#trace-b [data-u-next]").click();
      $("#trace-b [data-u-next]").click();
      var trace = $("#trace-b");
      var pulse = $("#trace-b [data-u-pulse]");
      var box = trace.getBoundingClientRect();
      var own = $('#trace-b [data-u-node="one"]').getBoundingClientRect();
      var got = parseFloat(pulse.style.getPropertyValue("--from-y"));
      var want = own.top + own.height / 2 - box.top;
      if (isNaN(got)) return "no pulse coordinates were set";
      if (got < 0) return "pulse resolved to an element outside this trace (--from-y " + got + ")";
      return near(got, want, 2) || "pulse from-y " + got + " but own node is at " + want;
    });

    check("trace: a malformed steps attribute does not break its own controls", function () {
      var broken = $("#trace-broken");
      broken.querySelector("[data-u-next]").click();
      return broken.querySelector("[data-u-count]").textContent.indexOf("0 / 0") > -1 ||
        "expected an empty step list, got " + broken.querySelector("[data-u-count]").textContent;
    });

    check("trace: restart clears the lit node", function () {
      $("#trace-a [data-u-restart]").click();
      return $('#trace-a [data-u-node="one"]').getAttribute("data-lit") === "false" || "still lit";
    });

    /* ── isolation: components after the broken one still work ─ */
    check("isolation: a component after the broken trace still works", function () {
      $('#check-b [data-u-answer="x"]').click();
      $("#check-b [data-u-mark]").click();
      return $("#check-b [data-u-result]").getAttribute("data-state") === "right" ||
        "the quiz after the broken trace did not respond";
    });

    /* ── thread ───────────────────────────────────────────── */
    check("thread: messages start hidden", function () {
      var shown = $$("#thread-a [data-u-msg]").filter(function (m) { return !m.hidden; });
      return shown.length === 0 || shown.length + " messages were visible at rest";
    });

    $("#thread-a [data-u-next]").click();
    await wait(900);

    check("thread: next reveals exactly one message", function () {
      var shown = $$("#thread-a [data-u-msg]").filter(function (m) { return !m.hidden; });
      if (shown.length !== 1) return shown.length + " messages visible";
      return $("#thread-a [data-u-count]").textContent.indexOf("1 / 2") > -1 || "counter did not advance";
    });

    check("thread: replay hides them again", function () {
      $("#thread-a [data-u-restart]").click();
      var shown = $$("#thread-a [data-u-msg]").filter(function (m) { return !m.hidden; });
      return shown.length === 0 || "still showing " + shown.length;
    });

    /* ── match ────────────────────────────────────────────── */
    check("match: tap a chip then a slot places it", function () {
      $('#match-a [data-u-chip="alpha"]').click();
      $('#match-a [data-u-slot="alpha"]').click();
      return $('#match-a [data-u-slot="alpha"]').getAttribute("data-u-holds") === "alpha" || "not placed";
    });

    check("match: marking scores placed slots", function () {
      $('#match-a [data-u-chip="alpha"]').click();
      $('#match-a [data-u-slot="beta"]').click();
      $("#match-a [data-u-mark]").click();
      var right = $('#match-a [data-u-slot="alpha"]').getAttribute("data-verdict");
      var wrong = $('#match-a [data-u-slot="beta"]').getAttribute("data-verdict");
      var summary = $("#match-a [data-u-result]").textContent;
      if (right !== "right") return "correct slot marked " + right;
      if (wrong !== "wrong") return "incorrect slot marked " + wrong;
      return summary.indexOf("1 of 2") > -1 || "summary reads: " + summary;
    });

    check("match: reset restores the empty label", function () {
      $("#match-a [data-u-again]").click();
      var slot = $('#match-a [data-u-slot="alpha"]');
      if (slot.getAttribute("data-u-holds")) return "still holding a chip";
      return slot.textContent.indexOf("Drop or tap") > -1 || "label not restored";
    });

    /* ── hunt ─────────────────────────────────────────────── */
    check("hunt: a wrong line explains why it is wrong", function () {
      $('#hunt-a [data-u-line="ok"]').click();
      var result = $("#hunt-a [data-u-result]");
      if (result.getAttribute("data-state") !== "wrong") return "no wrong state";
      return result.textContent.indexOf("fine") > -1 || "hint not shown";
    });

    check("hunt: the bug line wins and locks the rest", function () {
      $('#hunt-a [data-u-line="bug"]').click();
      var result = $("#hunt-a [data-u-result]");
      if (result.getAttribute("data-state") !== "right") return "no right state";
      if (result.textContent.indexOf("divides by zero") === -1) return "explanation missing";
      return $('#hunt-a [data-u-line="ok"]').disabled === true || "other lines still clickable";
    });

    /* ── map ──────────────────────────────────────────────── */
    check("map: clicking a part writes its description", function () {
      var parts = $$("#map-a [data-u-part]");
      parts[1].click();
      if (parts[1].getAttribute("aria-pressed") !== "true") return "not pressed";
      if (parts[0].getAttribute("aria-pressed") !== "false") return "previous part still pressed";
      return $("#map-a [data-u-readout]").textContent.indexOf("second piece") > -1 || "readout not written";
    });

    /* ── stack ────────────────────────────────────────────── */
    check("stack: switching tabs shows exactly one pane", function () {
      $('#stack-a [data-u-tab="two"]').click();
      var visible = $$("#stack-a .stack__pane").filter(function (p) { return !p.hidden; });
      if (visible.length !== 1) return visible.length + " panes visible";
      if (visible[0].getAttribute("data-u-pane") !== "two") return "wrong pane visible";
      return $('#stack-a [data-u-tab="two"]').getAttribute("aria-selected") === "true" || "tab not selected";
    });

    /* ── gloss ────────────────────────────────────────────── */
    check("gloss: the definition is in the top layer, not inline", function () {
      var def = document.getElementById("g-dag");
      if (!def) return "no definition element";
      if (!("popover" in HTMLElement.prototype)) return true; // fallback path covered by course.js
      return def.hasAttribute("popover") || "definition is not a popover";
    });

    check("gloss: opening it makes it visible", function () {
      var term = $('[popovertarget="g-dag"]');
      var def = document.getElementById("g-dag");
      term.click();
      if (!("popover" in HTMLElement.prototype)) return def.style.display === "block" || "not shown";
      return def.matches(":popover-open") || "popover did not open";
    });

    /* ── disclosure parts (no engine involved, must still work) ─ */
    check("depth: the short answer is visible and the mechanism is folded away", function () {
      var short = $("#depth-a .depth__short");
      var more = document.getElementById("depth-a-more");
      if (!short || short.offsetHeight === 0) return "the short answer is not visible";
      return more.open === false || "the mechanism layer starts open";
    });

    check("depth: opening a layer reveals it", function () {
      var more = document.getElementById("depth-a-more");
      more.querySelector("summary").click();
      if (!more.open) return "summary click did not open it";
      return more.querySelector(".depth__body").offsetHeight > 0 || "body still collapsed";
    });

    check("defend: the answer is hidden until the reader has tried", function () {
      var reveal = document.getElementById("defend-a-reveal");
      if (reveal.open) return "the answer is visible before the reader thinks";
      return $("#defend-a .defend__q").offsetHeight > 0 || "the question is not visible";
    });

    check("defend: revealing shows both the strong and the weak answer", function () {
      var reveal = document.getElementById("defend-a-reveal");
      reveal.querySelector("summary").click();
      var body = reveal.querySelector(".defend__body");
      if (!reveal.open || body.offsetHeight === 0) return "did not open";
      return reveal.querySelector(".defend__weak") !== null || "no weak-answer warning";
    });

    check("tradeoff: all four cells and a source are present", function () {
      var cells = $$("#tradeoff-a .tradeoff__cell").length;
      if (cells !== 4) return cells + " cells, expected 4";
      return $("#tradeoff-a .tradeoff__src") !== null || "no source cited";
    });

    /* ── learning-schedule parts (details-based, no engine) ──── */
    check("fieldwork: the answer is folded until the reader has been to the repo", function () {
      var d = document.getElementById("fieldwork-a-check");
      if (d.open) return "the answer is visible before the prediction";
      d.querySelector("summary").click();
      return (d.open && d.querySelector(".fieldwork__answer").offsetHeight > 0) || "did not open";
    });

    check("recall: prompts are visible, answers folded", function () {
      var q = $("#recall-a .recall__q");
      var a = document.getElementById("recall-a-answer");
      if (!q || q.offsetHeight === 0) return "the prompt is not visible";
      return a.open === false || "the answer starts open, which defeats retrieval";
    });

    check("territory: every row carries a coverage status", function () {
      var rows = $$("#territory-a .territory__row");
      var ok = rows.every(function (r) { return r.querySelector(".territory__status"); });
      return (rows.length === 2 && ok) || "a row has no status chip";
    });

    /* ── figures (rendered at build time, no engine involved) ── */
    check("figure: the svg is announced as an image with a name and a description", function () {
      var svg = $(".figure svg.fig");
      if (!svg) return "no figure found";
      if (svg.getAttribute("role") !== "img") return "role is " + svg.getAttribute("role");
      var ids = (svg.getAttribute("aria-labelledby") || "").split(/\s+/);
      if (ids.length < 2) return "aria-labelledby does not point at both title and desc";
      return ids.every(function (id) { return document.getElementById(id); })
        || "aria-labelledby points at an id that does not exist";
    });

    check("figure: its inner shapes are hidden from the accessibility tree", function () {
      var group = $(".figure svg.fig > g");
      return (group && group.getAttribute("aria-hidden") === "true")
        || "the drawing is not aria-hidden, so every shape is announced separately";
    });

    check("figure: it carries a caption and a described-in-words alternative", function () {
      if (!$(".figure .figure__caption")) return "no caption";
      return $(".figure .figure__alt") !== null || "no text alternative";
    });

    check("figure: it scales to its column rather than overflowing", function () {
      var fig = $(".figure");
      var svg = $(".figure svg.fig");
      if (svg.getBoundingClientRect().width > fig.getBoundingClientRect().width + 1
          && fig.scrollWidth <= fig.clientWidth + 1) {
        return "the drawing is wider than its container and the container does not scroll";
      }
      return true;
    });

    /* ── layout ───────────────────────────────────────────── */
    check("layout: the page never scrolls sideways", function () {
      var doc = document.documentElement;
      return doc.scrollWidth <= doc.clientWidth + 1 ||
        "scrollWidth " + doc.scrollWidth + " > viewport " + doc.clientWidth;
    });

    // Chrome refuses to open a window narrower than ~500px, so a true phone
    // viewport is measured inside an iframe, where media queries still apply.
    await new Promise(function (done) {
      var frame = document.createElement("iframe");
      frame.width = "375";
      frame.height = "700";
      frame.style.cssText = "position:fixed;left:-9999px;top:0;border:0;";
      frame.src = location.pathname + "?embedded=1";
      frame.onload = function () {
        try {
          var d = frame.contentDocument.documentElement;
          check("layout: no sideways scroll at a true 375px viewport", function () {
            if (d.clientWidth !== 375) return "iframe viewport was " + d.clientWidth + "px";
            return d.scrollWidth <= d.clientWidth + 1 ||
              "scrollWidth " + d.scrollWidth + " at 375px";
          });
          check("layout: controls wrap rather than overflow at 375px", function () {
            var rows = Array.prototype.slice.call(
              frame.contentDocument.querySelectorAll(".trace__controls, .thread__controls, .stack__tabs, .match__actions, .check__actions"));
            var bad = rows.filter(function (r) { return r.scrollWidth > r.clientWidth + 1; });
            return bad.length === 0 || bad.length + " control row(s) overflow their container";
          });
        } catch (err) {
          check("layout: 375px viewport check", function () { return "iframe unreadable: " + err.message; });
        }
        frame.remove();
        done();
      };
      document.body.appendChild(frame);
    });

    check("layout: no element extends past the right edge", function () {
      var w = document.documentElement.clientWidth;
      // Something inside a box that scrolls horizontally on purpose — a wide
      // diagram, a wide table — is contained, not overflowing.
      function inScroller(el) {
        for (var p = el.parentElement; p && p !== document.body; p = p.parentElement) {
          var ox = getComputedStyle(p).overflowX;
          if ((ox === "auto" || ox === "scroll") && p.scrollWidth > p.clientWidth) return true;
        }
        return false;
      }
      var over = $$("main *").filter(function (el) {
        return el.getBoundingClientRect().right > w + 1 && !inScroller(el);
      }).map(function (el) { return (el.className && el.className.baseVal !== undefined
        ? el.className.baseVal : el.className) || el.tagName; });
      return over.length === 0 || "past the edge: " + Array.from(new Set(over)).slice(0, 4).join(", ");
    });

    /* ── colour contrast ──────────────────────────────────── */
    function lum(rgb) {
      var p = rgb.match(/[\d.]+/g).slice(0, 3).map(function (v) {
        var c = v / 255;
        return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
      });
      return 0.2126 * p[0] + 0.7152 * p[1] + 0.0722 * p[2];
    }
    function contrast(a, b) {
      var la = lum(a), lb = lum(b);
      return (Math.max(la, lb) + 0.05) / (Math.min(la, lb) + 0.05);
    }

    var scheme = matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    var pageBg = getComputedStyle(document.body).backgroundColor;

    [
      ["body text", getComputedStyle(document.querySelector(".chapter__lede")).color, pageBg, 4.5],
      ["chapter eyebrow", getComputedStyle(document.querySelector(".chapter__eyebrow")).color, pageBg, 4.5],
      ["rail label", getComputedStyle(document.querySelector(".u-rail__link")).color, pageBg, 4.5],
      ["quiz option text", getComputedStyle(document.querySelector(".check__opt")).color,
        getComputedStyle(document.querySelector(".check__opt")).backgroundColor, 4.5]
    ].forEach(function (row) {
      check("contrast (" + scheme + "): " + row[0] + " clears AA", function () {
        var got = contrast(row[1], row[2]);
        return got >= row[3] || got.toFixed(2) + ":1, needs " + row[3];
      });
    });

    check("contrast (" + scheme + "): label on a filled button clears AA", function () {
      var btn = document.querySelector(".btn--primary");
      var cs = getComputedStyle(btn);
      var got = contrast(cs.color, cs.backgroundColor);
      return got >= 4.5 || got.toFixed(2) + ":1, needs 4.5";
    });

    /* ── report ───────────────────────────────────────────── */
    var report = {
      viewport: document.documentElement.clientWidth,
      scheme: matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light",
      passed: results.filter(function (r) { return r.ok; }).length,
      failed: results.filter(function (r) { return !r.ok; }).length,
      results: results
    };
    var out = document.getElementById("u-test-results");
    out.textContent = JSON.stringify(report);
    out.hidden = false;

    // Served over http by run.py; opened directly from disk when a human is
    // eyeballing the fixture, in which case the DOM copy above is the output.
    if (location.protocol.indexOf("http") === 0) {
      fetch("/__results", { method: "POST", body: JSON.stringify(report) });
    }
  }

  // The 375px check loads this same page in an iframe; that copy must not
  // start its own suite.
  if (location.search.indexOf("embedded") === -1) {
    window.addEventListener("load", function () { setTimeout(run, 60); });
  }
})();
