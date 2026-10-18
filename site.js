// Spark Gears Initiative — shared interactions
(() => {
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---------- Mobile menu ---------- */
  const menuBtn = document.querySelector(".menu-btn");
  const navLinks = document.getElementById("nav-links");
  if (menuBtn && navLinks) {
    const setOpen = (open) => {
      menuBtn.setAttribute("aria-expanded", String(open));
      navLinks.classList.toggle("open", open);
    };
    menuBtn.addEventListener("click", () => setOpen(menuBtn.getAttribute("aria-expanded") !== "true"));
    navLinks.addEventListener("click", (e) => { if (e.target.closest("a")) setOpen(false); });
    document.addEventListener("keydown", (e) => { if (e.key === "Escape") setOpen(false); });
  }

  /* ---------- Breadboard hero ---------- */
  const board = document.querySelector(".board");
  if (board) {
    const ctx = board.getContext("2d");
    const YELLOW = [255, 194, 51];
    let cols = 0, rows = 0, gap = 22, energy = new Float32Array(0);
    let w = 0, h = 0, dpr = 1, running = false, visible = true;
    const pulses = [];
    let lastPulse = 0;

    const resize = () => {
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      w = board.clientWidth;
      h = board.clientHeight;
      gap = w < 600 ? 18 : 22;
      board.width = Math.round(w * dpr);
      board.height = Math.round(h * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      cols = Math.ceil(w / gap) + 1;
      rows = Math.ceil(h / gap) + 1;
      energy = new Float32Array(cols * rows);
      draw();
    };

    const draw = () => {
      ctx.clearRect(0, 0, w, h);
      const off = gap / 2;
      for (let r = 0; r < rows; r++) {
        // breadboard has a center channel with no holes
        if (r % 14 === 7) continue;
        for (let c = 0; c < cols; c++) {
          const e = energy[r * cols + c];
          const x = off + c * gap, y = off + r * gap;
          if (e > 0.03) {
            const s = 4 + e * 6;
            ctx.fillStyle = `rgba(${YELLOW[0]},${YELLOW[1]},${YELLOW[2]},${0.35 + e * 0.65})`;
            ctx.fillRect(x - s / 2, y - s / 2, s, s);
          } else {
            ctx.fillStyle = "rgba(23,21,15,0.12)";
            ctx.fillRect(x - 2, y - 2, 4, 4);
          }
        }
      }
    };

    const excite = (px, py, radius) => {
      const c0 = Math.max(0, Math.floor((px - radius) / gap)), c1 = Math.min(cols - 1, Math.ceil((px + radius) / gap));
      const r0 = Math.max(0, Math.floor((py - radius) / gap)), r1 = Math.min(rows - 1, Math.ceil((py + radius) / gap));
      for (let r = r0; r <= r1; r++) {
        for (let c = c0; c <= c1; c++) {
          const dx = gap / 2 + c * gap - px, dy = gap / 2 + r * gap - py;
          const d = Math.sqrt(dx * dx + dy * dy);
          if (d < radius) {
            const i = r * cols + c;
            energy[i] = Math.max(energy[i], 1 - d / radius);
          }
        }
      }
    };

    const tick = (t) => {
      if (!running) return;
      // a "signal" occasionally runs along a row, like current through a strip
      if (t - lastPulse > 1600 && pulses.length < 3) {
        lastPulse = t;
        const dir = Math.random() < 0.5 ? 1 : -1;
        pulses.push({ r: Math.floor(Math.random() * rows), c: dir > 0 ? 0 : cols - 1, dir, speed: 0.35 + Math.random() * 0.25 });
      }
      for (let i = pulses.length - 1; i >= 0; i--) {
        const p = pulses[i];
        p.c += p.dir * p.speed;
        const ci = Math.round(p.c);
        if (ci < 0 || ci >= cols) { pulses.splice(i, 1); continue; }
        energy[p.r * cols + ci] = 1;
      }
      let active = false;
      for (let i = 0; i < energy.length; i++) {
        if (energy[i] > 0.01) { energy[i] *= 0.955; active = true; }
      }
      if (active || pulses.length) draw();
      requestAnimationFrame(tick);
    };

    const start = () => {
      if (running || reduceMotion || !visible) return;
      running = true;
      requestAnimationFrame(tick);
    };

    const hero = board.parentElement;
    const onPoint = (e) => {
      const rect = board.getBoundingClientRect();
      excite(e.clientX - rect.left, e.clientY - rect.top, e.pointerType === "touch" ? 60 : 72);
      if (reduceMotion) draw();
    };
    hero.addEventListener("pointermove", onPoint, { passive: true });
    hero.addEventListener("pointerdown", onPoint, { passive: true });

    new IntersectionObserver(([entry]) => {
      visible = entry.isIntersecting;
      if (visible) start(); else running = false;
    }).observe(hero);

    let resizeTimer;
    window.addEventListener("resize", () => {
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(resize, 120);
    });
    resize();
    start();
  }

  /* ---------- Horizontal rail ---------- */
  document.querySelectorAll("[data-rail]").forEach((root) => {
    const rail = root.querySelector(".rail");
    const prev = root.querySelector("[data-prev]");
    const next = root.querySelector("[data-next]");
    const bar = root.querySelector(".rail-progress span");
    const step = () => (rail.firstElementChild?.getBoundingClientRect().width || 300) + 18;
    const update = () => {
      const max = rail.scrollWidth - rail.clientWidth;
      if (prev) prev.disabled = rail.scrollLeft <= 4;
      if (next) next.disabled = rail.scrollLeft >= max - 4;
      if (bar) {
        const visibleShare = rail.clientWidth / rail.scrollWidth;
        bar.style.width = `${visibleShare * 100}%`;
        bar.style.transform = `translateX(${max > 0 ? (rail.scrollLeft / max) * ((1 - visibleShare) / visibleShare) * 100 : 0}%)`;
      }
    };
    prev?.addEventListener("click", () => rail.scrollBy({ left: -step(), behavior: reduceMotion ? "auto" : "smooth" }));
    next?.addEventListener("click", () => rail.scrollBy({ left: step(), behavior: reduceMotion ? "auto" : "smooth" }));
    rail.addEventListener("scroll", update, { passive: true });
    window.addEventListener("resize", update);
    update();
  });

  /* ---------- Lightbox ---------- */
  const lightbox = document.querySelector(".lightbox");
  let lbItems = [], lbIndex = 0;
  const lbImg = lightbox?.querySelector("img");
  const lbTitle = lightbox?.querySelector(".lb-top p");
  const lbCount = lightbox?.querySelector(".lb-bottom span");

  const lbShow = (i) => {
    lbIndex = (i + lbItems.length) % lbItems.length;
    const item = lbItems[lbIndex];
    lbImg.src = item.src;
    lbImg.alt = item.alt;
    lbCount.textContent = `${lbIndex + 1} / ${lbItems.length}`;
  };

  const openLightbox = (items, index, title) => {
    if (!lightbox) return;
    lbItems = items;
    lbTitle.textContent = title;
    lbShow(index);
    lightbox.showModal();
  };

  if (lightbox) {
    lightbox.querySelector("[data-lb-close]").addEventListener("click", () => lightbox.close());
    lightbox.querySelector("[data-lb-prev]").addEventListener("click", () => lbShow(lbIndex - 1));
    lightbox.querySelector("[data-lb-next]").addEventListener("click", () => lbShow(lbIndex + 1));
    lightbox.addEventListener("keydown", (e) => {
      if (e.key === "ArrowLeft") lbShow(lbIndex - 1);
      if (e.key === "ArrowRight") lbShow(lbIndex + 1);
    });
    lightbox.addEventListener("click", (e) => { if (e.target.classList.contains("lb-stage")) lightbox.close(); });
    let startX = null;
    lightbox.addEventListener("touchstart", (e) => { startX = e.touches[0].clientX; }, { passive: true });
    lightbox.addEventListener("touchend", (e) => {
      if (startX === null) return;
      const dx = e.changedTouches[0].clientX - startX;
      if (Math.abs(dx) > 50) lbShow(lbIndex + (dx < 0 ? 1 : -1));
      startX = null;
    });
  }

  /* ---------- Entry galleries ---------- */
  document.querySelectorAll(".gallery").forEach((gallery) => {
    const main = gallery.querySelector(".gallery-main");
    if (!main) return; // photo placeholder, nothing to open
    const mainImg = main.querySelector("img");
    const thumbs = [...gallery.querySelectorAll(".thumb")];
    const items = thumbs.length
      ? thumbs.map((t) => ({ src: t.dataset.full, alt: t.querySelector("img").alt }))
      : [{ src: mainImg.src, alt: mainImg.alt }];
    let current = 0;
    const title = gallery.closest(".entry")?.querySelector("h2")?.textContent || "";

    thumbs.forEach((thumb, i) => {
      thumb.addEventListener("click", () => {
        current = i;
        mainImg.src = items[i].src;
        mainImg.alt = items[i].alt;
        thumbs.forEach((t, j) => t.setAttribute("aria-current", String(j === i)));
      });
    });
    main.addEventListener("click", () => openLightbox(items, current, title));
  });

  /* ---------- Impact filters ---------- */
  const filters = [...document.querySelectorAll(".filter")];
  if (filters.length) {
    const entries = [...document.querySelectorAll(".entry")];
    filters.forEach((btn) => {
      const kind = btn.dataset.filter;
      const n = kind === "all" ? entries.length : entries.filter((e) => e.dataset.kind === kind).length;
      btn.querySelector("b").textContent = n;
      btn.addEventListener("click", () => {
        filters.forEach((f) => f.setAttribute("aria-pressed", String(f === btn)));
        entries.forEach((e) => { e.hidden = kind !== "all" && e.dataset.kind !== kind; });
      });
    });
  }

  /* ---------- Tabs (program picker) ---------- */
  document.querySelectorAll("[role=tablist]").forEach((list) => {
    const tabs = [...list.querySelectorAll("[role=tab]")];
    const select = (tab) => {
      tabs.forEach((t) => {
        const on = t === tab;
        t.setAttribute("aria-selected", String(on));
        t.tabIndex = on ? 0 : -1;
        document.getElementById(t.getAttribute("aria-controls")).hidden = !on;
      });
    };
    tabs.forEach((tab, i) => {
      tab.addEventListener("click", () => select(tab));
      tab.addEventListener("keydown", (e) => {
        const d = e.key === "ArrowDown" || e.key === "ArrowRight" ? 1 : e.key === "ArrowUp" || e.key === "ArrowLeft" ? -1 : 0;
        if (!d) return;
        e.preventDefault();
        const t = tabs[(i + d + tabs.length) % tabs.length];
        select(t);
        t.focus();
      });
    });
  });

  /* ---------- Sub-nav active state ---------- */
  const subLinks = [...document.querySelectorAll(".subnav a")];
  if (subLinks.length) {
    const sections = subLinks.map((a) => document.querySelector(a.getAttribute("href")));
    const io = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        const i = sections.indexOf(entry.target);
        subLinks.forEach((a, j) => a.classList.toggle("active", i === j));
      });
    }, { rootMargin: "-45% 0px -50% 0px" });
    sections.forEach((s) => s && io.observe(s));
  }
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
=======
>>>>>>> Stashed changes

  /* ---------- PDF preview ---------- */
  const viewer = document.querySelector(".pdf-viewer");
  if (viewer) {
    const PDFJS = "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/";
    const pages = viewer.querySelector(".pdf-pages");
    const title = viewer.querySelector("#pdf-title");
    const meta = viewer.querySelector(".pdf-meta");
    const download = viewer.querySelector(".pdf-download");
    const codeToggle = viewer.querySelector(".pdf-code-toggle");
    const codePanel = viewer.querySelector(".pdf-code");
    const codeList = viewer.querySelector(".pdf-code-list");
    const wide = window.matchMedia("(min-width: 861px)");
    let lib = null, snippets = null, job = 0, pendingPage = 0, settlePage = 0;

    const loadSnippets = () => snippets || (snippets = fetch("downloads/code-snippets.json")
      .then((r) => (r.ok ? r.json() : {}))
      .catch(() => ({})));

    const setCodeOpen = (open) => {
      codePanel.hidden = !open;
      codeToggle.setAttribute("aria-expanded", String(open));
      viewer.classList.toggle("code-open", open);
    };

    const copyText = async (text) => {
      try {
        await navigator.clipboard.writeText(text);
      } catch {
        // older browsers, or clipboard blocked: copy through a hidden textarea
        const ta = Object.assign(document.createElement("textarea"), { value: text });
        ta.setAttribute("readonly", "");
        ta.style.cssText = "position:fixed;opacity:0";
        viewer.appendChild(ta);
        ta.select();
        document.execCommand("copy");
        ta.remove();
      }
    };

    const goToPage = (n, instant = false) => {
      const canvas = pages.querySelectorAll("canvas")[n - 1];
      if (!canvas) { pendingPage = n; return; }
      pendingPage = 0;
      pages.scrollTo({ top: canvas.offsetTop - 16, behavior: instant || reduceMotion ? "auto" : "smooth" });
      if (!wide.matches) setCodeOpen(false);
    };

    const COPY_ICON = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15V6a2 2 0 0 1 2-2h9"/></svg>';
    const DONE_ICON = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>';

    const showSnippets = (items) => {
      codeList.replaceChildren(...items.map((item) => {
        const li = document.createElement("li");
        li.className = "pdf-snippet";
        const top = document.createElement("div");
        top.className = "pdf-snippet-top";
        top.append(Object.assign(document.createElement("strong"), { textContent: item.title }));
        if (item.page) {
          const jump = Object.assign(document.createElement("button"), { type: "button", textContent: `Go to page ${item.page}` });
          jump.addEventListener("click", () => goToPage(item.page));
          top.append(jump);
        }
        const pre = Object.assign(document.createElement("pre"), { textContent: item.code });
        pre.setAttribute("aria-hidden", "true");
        const copy = document.createElement("button");
        copy.type = "button";
        copy.className = "pdf-copy";
        copy.innerHTML = `${COPY_ICON}<span>Copy code</span>`;
        copy.setAttribute("aria-label", `Copy code: ${item.title}`);
        let timer;
        copy.addEventListener("click", async () => {
          await copyText(item.code);
          copy.classList.add("copied");
          copy.innerHTML = `${DONE_ICON}<span>Copied</span>`;
          clearTimeout(timer);
          timer = setTimeout(() => {
            copy.classList.remove("copied");
            copy.innerHTML = `${COPY_ICON}<span>Copy code</span>`;
          }, 1800);
        });
        li.append(top, pre, copy);
        return li;
      }));
      codeToggle.querySelector(".btn-label").textContent = `Code (${items.length})`;
    };

    const loadLib = () => lib || (lib = new Promise((resolve, reject) => {
      const s = document.createElement("script");
      s.src = PDFJS + "pdf.min.js";
      s.onload = () => {
        window.pdfjsLib.GlobalWorkerOptions.workerSrc = PDFJS + "pdf.worker.min.js";
        resolve(window.pdfjsLib);
      };
      s.onerror = () => { lib = null; reject(new Error("pdf.js failed to load")); };
      document.head.appendChild(s);
    }));

    const status = (text) => {
      pages.replaceChildren(Object.assign(document.createElement("p"), { className: "pdf-status", textContent: text }));
    };

    const render = async (url, id) => {
      const pdfjs = await loadLib();
      const doc = await pdfjs.getDocument(url).promise;
      if (id !== job) return;
      meta.textContent = `PDF · ${doc.numPages} ${doc.numPages === 1 ? "page" : "pages"}`;
      pages.replaceChildren();
      const width = Math.min(pages.clientWidth - 24, 860);
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      for (let n = 1; n <= doc.numPages; n++) {
        const page = await doc.getPage(n);
        if (id !== job) return;
        const base = page.getViewport({ scale: 1 });
        const vp = page.getViewport({ scale: (width / base.width) * dpr });
        const canvas = document.createElement("canvas");
        canvas.width = Math.round(vp.width);
        canvas.height = Math.round(vp.height);
        canvas.setAttribute("role", "img");
        canvas.setAttribute("aria-label", `Page ${n} of ${doc.numPages}`);
        pages.appendChild(canvas);
        await page.render({ canvasContext: canvas.getContext("2d"), viewport: vp }).promise;
        if (pendingPage === n) { goToPage(n, true); settlePage = n; }
      }
      // later pages can nudge the layout while rendering, so land the jump again at the end
      if (settlePage && id === job) { goToPage(settlePage, true); settlePage = 0; }
    };

    const open = (link) => {
      const url = link.getAttribute("href");
      const name = link.dataset.pdfTitle || link.closest(".card")?.querySelector("h3")?.textContent || link.textContent.trim();
      const id = ++job;
      title.textContent = name;
      meta.textContent = "PDF";
      download.href = url;
      download.setAttribute("download", url.split("/").pop());
      status("Loading preview…");
      pendingPage = settlePage = 0;
      codeToggle.hidden = true;
      setCodeOpen(false);
      viewer.showModal();
      pages.scrollTop = 0;
      loadSnippets().then((all) => {
        const items = all[url.split("/").pop()];
        if (id !== job || !items?.length) return;
        showSnippets(items);
        codeToggle.hidden = false;
        setCodeOpen(wide.matches);
      });
      render(url, id).catch(() => {
        if (id !== job) return;
        // no pdf.js (offline or blocked): fall back to the browser's own viewer
        const frame = document.createElement("iframe");
        frame.src = url;
        frame.title = name;
        pages.replaceChildren(frame);
      });
    };

    document.querySelectorAll("a[data-pdf]").forEach((link) => {
      link.addEventListener("click", (e) => {
        if (e.metaKey || e.ctrlKey || e.shiftKey || e.button !== 0) return;
        e.preventDefault();
        open(link);
      });
    });
    viewer.querySelector("[data-pdf-close]").addEventListener("click", () => viewer.close());
    codeToggle.addEventListener("click", () => setCodeOpen(codePanel.hidden));
    viewer.addEventListener("click", (e) => { if (e.target === viewer) viewer.close(); });
    viewer.addEventListener("close", () => { job++; pages.replaceChildren(); });
  }
<<<<<<< Updated upstream
=======
>>>>>>> 3b6b7ae1383f3d6551069a74070a55c515411292
>>>>>>> Stashed changes
})();
