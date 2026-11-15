/* =========================================================
   The Business Research Lab — Site Script (no dependencies)
   ========================================================= */
(function () {
  "use strict";
  const CFG = window.BRL_CONFIG || {};
  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => Array.from(el.querySelectorAll(s));
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---------- Header / nav ---------- */
  const header = $(".site-header");
  const onScroll = () => header && header.classList.toggle("is-scrolled", window.scrollY > 8);
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  const toggle = $(".nav-toggle");
  if (toggle) {
    toggle.addEventListener("click", () => {
      const open = document.body.classList.toggle("nav-open");
      toggle.setAttribute("aria-expanded", String(open));
    });
    $$(".nav a").forEach(a => a.addEventListener("click", () => {
      document.body.classList.remove("nav-open");
      toggle.setAttribute("aria-expanded", "false");
    }));
  }
  document.addEventListener("keydown", e => {
    if (e.key === "Escape") {
      document.body.classList.remove("nav-open");
      toggle && toggle.setAttribute("aria-expanded", "false");
      closeModal();
    }
  });

  /* ---------- Config-driven contact bits ---------- */
  $$("[data-cfg-email]").forEach(el => { el.textContent = CFG.email; el.href = "mailto:" + CFG.email; });
  $$("[data-cfg-location]").forEach(el => { el.textContent = CFG.location; });
  $$("[data-cfg-phone]").forEach(el => {
    if (!CFG.phone) { (el.closest("[data-cfg-wrap]") || el).remove(); return; }
    el.textContent = CFG.phone; el.href = "tel:" + CFG.phone.replace(/[^\d+]/g, "");
  });
  $$("[data-cfg-whatsapp]").forEach(el => {
    if (!CFG.whatsapp) { (el.closest("[data-cfg-wrap]") || el).remove(); return; }
    el.href = "https://wa.me/" + CFG.whatsapp;
  });
  $$("[data-cfg-linkedin]").forEach(el => {
    if (!CFG.linkedin) { (el.closest("[data-cfg-wrap]") || el).remove(); return; }
    el.href = CFG.linkedin;
  });
  $$("[data-year]").forEach(el => (el.textContent = new Date().getFullYear()));

  /* ---------- Plans: checkout links or contact fallback ---------- */
  $$("[data-plan]").forEach(btn => {
    const key = btn.dataset.plan;
    const url = CFG.plans && CFG.plans[key] && CFG.plans[key].checkoutUrl;
    if (url) {
      btn.href = url; btn.target = "_blank"; btn.rel = "noopener";
    } else {
      btn.addEventListener("click", e => {
        const sel = $("#contact-interest");
        if (sel) {
          e.preventDefault();
          sel.value = btn.dataset.interest || sel.value;
          $("#contacto").scrollIntoView({ behavior: reduceMotion ? "auto" : "smooth" });
          setTimeout(() => $("#contact-name") && $("#contact-name").focus({ preventScroll: true }), 600);
        }
      });
    }
  });

  /* ---------- Reveal on scroll ---------- */
  const io = "IntersectionObserver" in window && !reduceMotion
    ? new IntersectionObserver(entries => entries.forEach(en => {
        if (en.isIntersecting) { en.target.classList.add("is-visible"); io.unobserve(en.target); }
      }), { threshold: 0.12, rootMargin: "0px 0px -40px 0px" })
    : null;
  const observeReveals = (root = document) => $$(".reveal:not(.is-visible)", root).forEach(el => io ? io.observe(el) : el.classList.add("is-visible"));
  observeReveals();

  /* ---------- Flowing line art (hero canvas) ---------- */
  const canvas = $("#hero-canvas");
  if (canvas && canvas.getContext) {
    const ctx = canvas.getContext("2d");
    let w, h, dpr, t = 0, raf;
    const resize = () => {
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      w = canvas.clientWidth; h = canvas.clientHeight;
      canvas.width = w * dpr; canvas.height = h * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };
    const draw = () => {
      ctx.clearRect(0, 0, w, h);
      // La línea: un solo trazo terracota continuo, como la S del símbolo
      const pts = [];
      for (let x = 0; x <= w; x += 6) {
        const nx = x / w;
        if (nx < 0.38 && w > 900) continue;           // en escritorio, la línea vive a la derecha
        const u = w > 900 ? (nx - 0.38) / 0.62 : nx;
        const y = h * (0.97 - (w > 900 ? 0.6 : 0.2) * Math.pow(u, 1.15))
          + Math.sin(u * 6 + t) * 10 * (1 - u * 0.4)
          + Math.sin(u * 14 - t * 1.4) * 3;
        pts.push([x, y]);
      }
      // rango del pronóstico (arena), solo en el último tramo
      const k0 = Math.floor(pts.length * 0.72);
      ctx.beginPath();
      for (let i = k0; i < pts.length; i++) { const s = (i - k0) / (pts.length - k0); ctx.lineTo(pts[i][0], pts[i][1] - 6 - s * 48); }
      for (let i = pts.length - 1; i >= k0; i--) { const s = (i - k0) / (pts.length - k0); ctx.lineTo(pts[i][0], pts[i][1] + 6 + s * 48); }
      ctx.closePath(); ctx.fillStyle = "rgba(205,187,152,.16)"; ctx.fill();
      ctx.beginPath();
      pts.forEach(([x, y], i) => (i ? ctx.lineTo(x, y) : ctx.moveTo(x, y)));
      ctx.strokeStyle = "#C15C28"; ctx.lineWidth = 2.5; ctx.lineJoin = "round"; ctx.stroke();
      const [px, py] = pts[k0];
      ctx.beginPath(); ctx.arc(px, py, 5.5, 0, Math.PI * 2); ctx.fillStyle = "#C15C28"; ctx.fill();
    };
    const loop = () => { t += 0.006; draw(); raf = requestAnimationFrame(loop); };
    resize(); draw();
    window.addEventListener("resize", () => { resize(); draw(); });
    if (!reduceMotion) {
      loop();
      document.addEventListener("visibilitychange", () => { if (document.hidden) cancelAnimationFrame(raf); else loop(); });
    }
  }

  /* ---------- Decorative SVG lines (covers, page hero) ---------- */
  function linesSVG(seed = 1) {
    const a = 20 + (seed * 17) % 30, b = 10 + (seed * 11) % 25;
    const d = `M0 170 C 70 ${150 - b}, 120 ${165 - a}, 170 ${135 - b} S 270 ${110 - a}, 310 ${95 - b} S 380 ${60 - a / 2}, 400 50`;
    return `<svg class="lines" viewBox="0 0 400 200" preserveAspectRatio="none" aria-hidden="true">
      <path d="${d}" fill="none" stroke="#C15C28" stroke-width="2.5" vector-effect="non-scaling-stroke" stroke-linecap="round"/></svg>`;
  }
  const triSVG = '<svg class="tri" viewBox="0 0 100 62" aria-hidden="true"><path d="M7 6 H93 L50 55 Z" fill="none" stroke="currentColor" stroke-width="8" stroke-linejoin="miter"/></svg>';
  $$("[data-lines]").forEach((el, i) => el.insertAdjacentHTML("afterbegin", linesSVG(i + 3)));

  /* ---------- Helpers ---------- */
  const fetchJSON = url => fetch(url, { cache: "no-cache" }).then(r => { if (!r.ok) throw new Error(r.status); return r.json(); });
  // Datos en vivo: si existe data/origen.json (lo crea la automatización cuando el repositorio de GitHub es público),
  // los datos de mercado se leen directo de GitHub, sin necesidad de redesplegar en Netlify. Si falla, se usa la copia local.
  let origenP = null;
  const origen = () => origenP || (origenP = fetch("data/origen.json", { cache: "no-cache" })
    .then(r => (r.ok ? r.json() : {})).then(o => (o && o.base) || "").catch(() => ""));
  const fetchData = path => origen().then(base => base
    ? fetchJSON(base + path).then(d => ({ d, base })).catch(() => fetchJSON(path).then(d => ({ d, base: "" })))
    : fetchJSON(path).then(d => ({ d, base: "" })));
  const esc = s => String(s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const fmtDate = (iso, opts = { month: "short", year: "numeric" }) => {
    const [y, m, d] = iso.split("-").map(Number);
    return new Date(y, (m || 1) - 1, d || 1).toLocaleDateString("es-DO", opts).replace(/\./g, "");
  };
  const isFuture = iso => new Date(iso + "T00:00:00") > new Date();

  /* ---------- Modal ---------- */
  let lastFocus = null;
  function openModal(id) {
    const m = document.getElementById(id); if (!m) return;
    lastFocus = document.activeElement;
    m.classList.add("is-open"); m.setAttribute("aria-hidden", "false");
    const f = m.querySelector("input:not([type=hidden]):not(.hp input), button"); f && f.focus();
  }
  function closeModal() {
    $$(".modal.is-open").forEach(m => { m.classList.remove("is-open"); m.setAttribute("aria-hidden", "true"); });
    lastFocus && lastFocus.focus && lastFocus.focus();
  }
  $$("[data-close-modal]").forEach(el => el.addEventListener("click", closeModal));

  /* ---------- Netlify Forms via AJAX ---------- */
  const encode = data => new URLSearchParams(data).toString();
  $$("form.js-ajax").forEach(form => {
    form.addEventListener("submit", e => {
      e.preventDefault();
      const status = form.querySelector(".form-status");
      const btn = form.querySelector("[type=submit]");
      const data = new FormData(form);
      btn && (btn.disabled = true);
      fetch("/", { method: "POST", headers: { "Content-Type": "application/x-www-form-urlencoded" }, body: encode(data) })
        .then(r => { if (!r.ok) throw new Error(r.status); })
        .then(() => {
          if (status) { status.className = "form-status is-ok"; status.textContent = form.dataset.success || "¡Gracias! Te responderemos en breve."; }
          const dl = form.dataset.download;
          if (dl) {
            const a = document.createElement("a"); a.href = dl; a.download = ""; document.body.appendChild(a); a.click(); a.remove();
            if (status) status.innerHTML = `Tu descarga comenzó. Si no inicia, <a href="${esc(dl)}" download>haz clic aquí</a>.`;
          }
          form.reset();
        })
        .catch(() => {
          // Si el registro del formulario falla, la descarga gratuita se entrega igual (el visitante nunca se queda sin el archivo)
          const dlFail = form.dataset.download;
          if (dlFail) {
            const a = document.createElement("a"); a.href = dlFail; a.download = ""; document.body.appendChild(a); a.click(); a.remove();
            if (status) { status.className = "form-status is-ok"; status.innerHTML = `Tu descarga comenzó. Si no inicia, <a href="${esc(dlFail)}" download>haz clic aquí</a>.`; }
            return;
          }
          if (status) {
            status.className = "form-status is-err";
            status.textContent = /claude|localhost|127\.0\.0\.1/.test(location.hostname)
              ? "Vista previa: los formularios funcionan una vez publicado el sitio en Netlify."
              : "Algo salió mal. Escríbenos a " + CFG.email + ".";
          }
        })
        .finally(() => { btn && (btn.disabled = false); });
    });
  });

  /* ---------- Research library ---------- */
  const lockIcon = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><rect x="4" y="11" width="16" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/></svg>';
  const dlIcon = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M12 3v12m0 0-5-5m5 5 5-5M4 21h16"/></svg>';
  const variants = ["", "study--ink", "study--paper"];

  function studyCard(s, i) {
    const upcoming = isFuture(s.date);
    let price, action, chip;
    if (s.access === "free") {
      chip = '<span class="chip chip--good chip--dot">Descarga gratis</span>';
      price = '<span class="price price--free">Gratis</span>';
      action = `<button class="btn btn--slate btn--sm" data-get="${esc(s.id)}">${dlIcon} Descargar</button>`;
    } else if (s.checkoutUrl && !upcoming) {
      chip = '<span class="chip">Premium</span>';
      price = `<span class="price">US$${s.price} <small>pago único</small></span>`;
      action = `<a class="btn btn--primary btn--sm" href="${esc(s.checkoutUrl)}" target="_blank" rel="noopener">${lockIcon} Comprar y descargar</a>`;
    } else {
      chip = `<span class="chip">${upcoming ? "Disponible " + fmtDate(s.date) : "Premium"}</span>`;
      price = `<span class="price">US$${s.price} <small>${upcoming ? "preventa" : "pago único"}</small></span>`;
      action = `<button class="btn btn--ghost btn--sm" data-notify="${esc(s.id)}">Avísame</button>`;
    }
    return `
      <article class="study reveal ${variants[i % 3]}" data-cat="${esc(s.category)}">
        <div class="study__cover" data-lines>
          ${triSVG}
          ${chip}
          <span class="study__cover-cat">${esc(s.type || "Estudio")} · ${s.date.slice(0, 4)} · ${esc(s.category)}</span>
        </div>
        <div class="study__body">
          <div class="study__meta"><span>${fmtDate(s.date)}</span><span>${s.pages ? s.pages + " páginas" : s.records ? s.records + " registros" : ""}</span>${s.author ? `<span>Por ${esc(s.author)}</span>` : ""}</div>
          <h3>${esc(s.title)}</h3>
          <p>${esc(s.summary)}</p>
          <div class="study__foot">${price}${action}</div>
        </div>
      </article>`;
  }

  const lists = $$("[data-research-list]");
  if (lists.length) {
    fetchJSON("data/research.json").then(({ studies }) => {
      // destacados primero; luego disponibles (más recientes primero) y al final los próximos (más cercanos primero)
      studies.sort((a, b) => {
        if (!!b.featured !== !!a.featured) return b.featured ? 1 : -1;
        const fa = isFuture(a.date), fb = isFuture(b.date);
        if (fa !== fb) return fa ? 1 : -1;
        return fa ? a.date.localeCompare(b.date) : b.date.localeCompare(a.date);
      });
      const byId = Object.fromEntries(studies.map(s => [s.id, s]));

      lists.forEach(list => {
        const limit = Number(list.dataset.limit) || 0;
        const filtersEl = $("[data-research-filters]");
        const searchEl = $("[data-research-search]");
        let cat = "Todos", q = "";

        if (filtersEl) {
          const cats = ["Todos", ...new Set(studies.map(s => s.category))];
          filtersEl.innerHTML = cats.map(c => `<button class="filter-btn" aria-pressed="${c === "Todos"}" data-cat="${esc(c)}">${esc(c)}</button>`).join("");
          filtersEl.addEventListener("click", e => {
            const b = e.target.closest("[data-cat]"); if (!b) return;
            cat = b.dataset.cat;
            $$(".filter-btn", filtersEl).forEach(x => x.setAttribute("aria-pressed", String(x === b)));
            render();
          });
        }
        searchEl && searchEl.addEventListener("input", () => { q = searchEl.value.trim().toLowerCase(); render(); });

        function render() {
          let items = studies.filter(s => (cat === "Todos" || s.category === cat) &&
            (!q || (s.title + " " + s.summary + " " + s.tags.join(" ")).toLowerCase().includes(q)));
          if (limit) items = items.slice(0, limit);
          list.innerHTML = items.length ? items.map(studyCard).join("") : '<p class="empty">Ningún estudio coincide con tu búsqueda.</p>';
          $$("[data-lines]", list).forEach((el, i) => el.insertAdjacentHTML("afterbegin", linesSVG(i + 2)));
          observeReveals(list);
        }
        render();
      });

      document.addEventListener("click", e => {
        const get = e.target.closest("[data-get]");
        const notify = e.target.closest("[data-notify]");
        if (get) {
          const s = byId[get.dataset.get];
          const form = $("#download-form");
          if (!form) { window.location.href = "investigacion.html"; return; }
          $("#download-title").textContent = s.title;
          form.querySelector("[name=study]").value = s.title;
          form.dataset.download = s.downloadUrl;
          form.querySelector(".form-status").className = "form-status";
          openModal("download-modal");
        }
        if (notify) {
          const s = byId[notify.dataset.notify];
          const form = $("#notify-form");
          if (!form) { window.location.href = "investigacion.html"; return; }
          $("#notify-title").textContent = s.title;
          form.querySelector("[name=study]").value = s.title;
          form.querySelector(".form-status").className = "form-status";
          openModal("notify-modal");
        }
      });
    }).catch(() => lists.forEach(l => (l.innerHTML = '<p class="empty">Cargando la biblioteca… Si persiste, recarga la página.</p>')));
  }

  /* ---------- Line chart (una serie, un eje, huecos, banda opcional, tooltip) ---------- */
  function lineChart(el, series, { fmt = v => v.toFixed(2), step = false, color = "#2C4856", label = "", band = null, dateFmt = null } = {}) {
    const fd = dateFmt || (d => fmtDate(d, { month: "short", year: "2-digit" }));
    const draw = () => {
      const W = el.clientWidth, H = el.clientHeight;
      const m = { t: 16, r: 14, b: 28, l: 50 };
      const iw = W - m.l - m.r, ih = H - m.t - m.b;
      const vals = series.map(d => d.value).filter(v => v != null);
      if (!vals.length) { el.innerHTML = '<p class="empty">Sin datos.</p>'; return; }
      let lo = Math.min(...vals, ...(band || [])), hi = Math.max(...vals, ...(band || []));
      const pad = (hi - lo) * 0.18 || Math.abs(hi) * 0.05 || 1;
      lo -= pad; hi += pad;
      const n = series.length;
      const x = i => m.l + (n === 1 ? iw / 2 : (i / (n - 1)) * iw);
      const y = v => m.t + ih - ((v - lo) / (hi - lo)) * ih;
      const grid = []; for (let k = 0; k <= 4; k++) grid.push(lo + ((hi - lo) * k) / 4);

      // segmentos continuos (los nulos cortan la línea)
      const segs = []; let cur = [];
      series.forEach((p, i) => { if (p.value == null) { if (cur.length) segs.push(cur); cur = []; } else cur.push(i); });
      if (cur.length) segs.push(cur);
      const segPath = idx => idx.map((i, k) => k === 0 ? `M${x(i)},${y(series[i].value)}` : (step ? `H${x(i)}V${y(series[i].value)}` : `L${x(i)},${y(series[i].value)}`)).join("");
      const lines = segs.map(segPath);
      const areas = segs.map((idx, j) => `${lines[j]}V${m.t + ih}H${x(idx[0])}Z`);
      const lastI = segs[segs.length - 1].slice(-1)[0];
      const maxLabels = W < 480 ? 4 : 7, every = Math.max(1, Math.ceil(n / maxLabels));
      const gid = "g" + Math.random().toString(36).slice(2, 7);
      const bandSvg = band ? `<rect x="${m.l}" y="${y(band[1])}" width="${iw}" height="${y(band[0]) - y(band[1])}" fill="#CDBB98" fill-opacity=".28"/>
          <text x="${m.l + 6}" y="${y(band[1]) + 13}" fill="#8A7A57" font-size="10.5" font-family="Manrope, Arial">Rango meta</text>` : "";

      el.innerHTML = `
        <svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(label)}">
          <defs><linearGradient id="${gid}" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stop-color="${color}" stop-opacity=".14"/><stop offset="1" stop-color="${color}" stop-opacity="0"/>
          </linearGradient></defs>
          ${bandSvg}
          <g class="grid">${grid.map(v => `<line x1="${m.l}" x2="${W - m.r}" y1="${y(v)}" y2="${y(v)}"/>`).join("")}</g>
          <g class="axis">
            ${grid.map(v => `<text x="${m.l - 8}" y="${y(v) + 4}" text-anchor="end">${fmt(v)}</text>`).join("")}
            ${series.map((p, i) => (i % every === 0 && n - 1 - i >= every * 0.6) || i === n - 1 ? `<text x="${x(i)}" y="${H - 6}" text-anchor="middle">${fd(p.date)}</text>` : "").join("")}
          </g>
          ${band ? "" : areas.map(a => `<path d="${a}" fill="url(#${gid})"/>`).join("")}
          ${lines.map(d => `<path d="${d}" fill="none" stroke="${color}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>`).join("")}
          ${segs.filter(g => g.length === 1).map(g => `<circle cx="${x(g[0])}" cy="${y(series[g[0]].value)}" r="3" fill="${color}"/>`).join("")}
          <circle cx="${x(lastI)}" cy="${y(series[lastI].value)}" r="5" fill="#B35231" stroke="#FCFAF5" stroke-width="2"/>
          <g class="hover" style="opacity:0">
            <line class="xh" y1="${m.t}" y2="${m.t + ih}" stroke="${color}" stroke-opacity=".35" stroke-dasharray="3 3"/>
            <circle class="dot" r="5" fill="${color}" stroke="#FCFAF5" stroke-width="2"/>
          </g>
          <rect x="${m.l}" y="${m.t}" width="${iw}" height="${ih}" fill="transparent" class="hit"/>
        </svg>
        <div class="tip"></div>`;

      const svg = el.querySelector("svg"), hv = el.querySelector(".hover"), tip = el.querySelector(".tip");
      const xh = el.querySelector(".xh"), dot = el.querySelector(".dot");
      const move = ev => {
        const r = svg.getBoundingClientRect();
        const px = ((ev.touches ? ev.touches[0].clientX : ev.clientX) - r.left) * (W / r.width);
        let i = Math.max(0, Math.min(n - 1, Math.round(((px - m.l) / iw) * (n - 1))));
        if (series[i].value == null) {   // salta al dato más cercano
          let a = i, b = i;
          while (a > 0 && series[a].value == null) a--;
          while (b < n - 1 && series[b].value == null) b++;
          i = series[a].value == null ? b : series[b].value == null ? a : (i - a <= b - i ? a : b);
        }
        const p = series[i], cx = x(i), cy = y(p.value);
        xh.setAttribute("x1", cx); xh.setAttribute("x2", cx);
        dot.setAttribute("cx", cx); dot.setAttribute("cy", cy);
        hv.style.opacity = 1;
        tip.innerHTML = `${fmtDate(p.date, p.date.length > 7 ? { day: "numeric", month: "short", year: "numeric" } : { month: "short", year: "numeric" })} · <strong>${fmt(p.value)}</strong>`;
        tip.style.left = Math.min(Math.max(cx / W * 100, 12), 88) + "%"; tip.style.top = (cy / H) * 100 + "%"; tip.style.opacity = 1;
      };
      const leave = () => { hv.style.opacity = 0; tip.style.opacity = 0; };
      const hit = el.querySelector(".hit");
      hit.addEventListener("mousemove", move); hit.addEventListener("touchmove", move, { passive: true });
      hit.addEventListener("touchstart", move, { passive: true });
      hit.addEventListener("mouseleave", leave); hit.addEventListener("touchend", leave);
    };
    draw();
    let rt; window.addEventListener("resize", () => { clearTimeout(rt); rt = setTimeout(draw, 120); });
    return { redraw: draw };
  }

  /* ---------- Centro de datos ---------- */
  const datosRoot = $("[data-datos]");
  if (datosRoot) {
    fetchData("data/macro/series.json").then(({ d: D, base }) => {
      const B = p => base + p;
      $$("[data-datos-updated]").forEach(el => (el.textContent = fmtDate(D.actualizado, { day: "numeric", month: "long", year: "numeric" })));
      $$("[data-dl-all-xlsx]").forEach(a => (a.href = B(D.descargas.xlsx)));
      $$("[data-dl-all-csv]").forEach(a => (a.href = B(D.descargas.csv)));
      $$("[data-dl-daily]").forEach(a => (a.href = B(D.descargas.diario_csv)));
      if (D.series.some(s => s.frecuencia === "Semanal")) $$("[data-weekly-note]").forEach(el => el.remove());
      const ranges = [["1A", 1], ["3A", 3], ["5A", 5], ["Todo", 0]];
      datosRoot.innerHTML = D.series.map((s, k) => `
        <article class="panel dataset reveal" id="${esc(s.id)}">
          <div class="dataset__head">
            <div>
              <span class="eyebrow" style="margin-bottom:6px">${esc(s.frecuencia)} · ${esc(s.unidad)}</span>
              <h3>${esc(s.nombre)}</h3>
              <p>${esc(s.descripcion)}</p>
            </div>
            <div class="dataset__dl">
              <a class="btn btn--ghost btn--sm" href="${esc(B(s.descargas.csv))}" download>CSV</a>
              <a class="btn btn--slate btn--sm" href="${esc(B(s.descargas.xlsx))}" download>Excel</a>
            </div>
          </div>
          <div class="dataset__kpis" data-kpis></div>
          <div class="dataset__bar">
            <div class="seg" role="group" aria-label="Período">${ranges.map(([l, y]) => `<button data-yrs="${y}" aria-pressed="${y === (s.datos.length > 60 ? 5 : 0)}">${l}</button>`).join("")}</div>
            <button class="linkish" data-table-toggle aria-expanded="false">Ver tabla</button>
          </div>
          <div class="chart chart--tall" data-chart></div>
          <div class="dataset__table" data-table hidden></div>
          <p class="source">Fuente: ${esc(s.fuente)} · Elaboración TBRL · <a href="${esc(s.fuente_url)}" target="_blank" rel="noopener">fuente oficial ↗</a></p>
        </article>`).join("");

      D.series.forEach(s => {
        const card = document.getElementById(s.id);
        const all = s.datos.map(([date, value]) => ({ date, value }));
        const dec = s.decimales ?? 2;
        const f = v => v.toFixed(dec) + (s.unidad.startsWith("%") ? "%" : "");
        const nn = all.filter(p => p.value != null);
        const last = nn[nn.length - 1], prev = nn[nn.length - 2];
        const perYear = s.frecuencia === "Semanal" ? 52 : s.frecuencia === "Diaria" ? 250 : 12;
        const byDate = new Map(nn.map(p => [p.date, p]));
        let yearAgo = null;
        if (last.date.length === 7) {
          const [yy, mm] = last.date.split("-");
          yearAgo = byDate.get(`${Number(yy) - 1}-${mm}`) || null;
        } else {
          const target = new Date(last.date + "T00:00:00"); target.setDate(target.getDate() - 364);
          yearAgo = nn.reduce((best, p) => {
            const dd = Math.abs(new Date(p.date + "T00:00:00") - target);
            return dd < 5 * 864e5 && (!best || dd < best.d) ? { p, d: dd } : best;
          }, null);
          yearAgo = yearAgo && yearAgo.p;
        }
        const diff = (a, b) => {
          if (!a || !b) return "—";
          const d = a.value - b.value;
          return s.unidad.startsWith("%") ? `${d >= 0 ? "+" : ""}${(d * 100).toFixed(0)} pb` : `${d >= 0 ? "+" : ""}${(d / b.value * 100).toFixed(2)}%`;
        };
        const per = s.frecuencia === "Semanal" ? "semana" : "mes";
        card.querySelector("[data-kpis]").innerHTML = `
          <div><span>Último dato · ${fmtDate(last.date, last.date.length > 7 ? { day: "numeric", month: "short", year: "numeric" } : { month: "long", year: "numeric" })}</span><strong>${f(last.value)}</strong></div>
          <div><span>Vs. ${per} anterior</span><strong>${diff(last, prev)}</strong></div>
          <div><span>Vs. hace un año</span><strong>${diff(last, yearAgo)}</strong></div>
          <div><span>Observaciones</span><strong>${nn.length}</strong></div>`;
        const chartEl = card.querySelector("[data-chart]");
        const opts = { fmt: v => v.toFixed(s.unidad.startsWith("%") ? 2 : 1), step: !!s.escalonada, band: s.banda || null, label: s.nombre + " " + s.frecuencia,
          color: s.id.startsWith("tasa_politica") ? "#B35231" : "#2C4856" };
        const render = yrs => {
          const pts = yrs ? all.slice(-yrs * perYear) : all;
          lineChart(chartEl, pts, opts);
        };
        const def = card.querySelector('[data-yrs][aria-pressed="true"]');
        render(Number(def.dataset.yrs));
        card.querySelectorAll("[data-yrs]").forEach(b => b.addEventListener("click", () => {
          card.querySelectorAll("[data-yrs]").forEach(x => x.setAttribute("aria-pressed", String(x === b)));
          render(Number(b.dataset.yrs));
        }));
        const tbtn = card.querySelector("[data-table-toggle]"), tbox = card.querySelector("[data-table]");
        tbtn.addEventListener("click", () => {
          const open = tbox.hidden;
          if (open && !tbox.innerHTML) tbox.innerHTML = `<table class="data"><thead><tr><th>Fecha</th><th class="num">${esc(s.unidad)}</th></tr></thead><tbody>${
            [...all].reverse().map(p => `<tr><td>${esc(p.date)}</td><td class="num">${p.value == null ? "—" : p.value.toFixed(dec + (s.unidad.startsWith("RD") ? 2 : 0))}</td></tr>`).join("")}</tbody></table>`;
          tbox.hidden = !open; tbtn.setAttribute("aria-expanded", String(open)); tbtn.textContent = open ? "Ocultar tabla" : "Ver tabla";
        });
      });
      observeReveals(datosRoot);
    }).catch(() => (datosRoot.innerHTML = '<p class="empty">No se pudieron cargar los datos. Recarga la página.</p>'));
  }

  /* ---------- Barras horizontales (una serie, rango P25–P75 opcional) ---------- */
  function hbars(el, items, { fmt = v => v, label = "" } = {}) {
    const draw = () => {
      const W = el.clientWidth, rowH = 34, m = { t: 6, r: 70, b: 6, l: Math.min(190, W * 0.42) };
      const H = m.t + m.b + rowH * items.length;
      const iw = W - m.l - m.r;
      const max = Math.max(...items.map(d => Math.max(d.value, d.hi || 0))) * 1.05;
      const x = v => m.l + (v / max) * iw;
      el.style.height = H + "px";
      el.innerHTML = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(label)}">
        ${items.map((d, i) => {
          const y = m.t + i * rowH, cy = y + rowH / 2;
          return `<g class="hbar">
            <title>${esc(d.label)}: ${fmt(d.value)}${d.lo != null ? ` (P25–P75: ${fmt(d.lo)}–${fmt(d.hi)})` : ""} · ${d.n} anuncios</title>
            <rect x="0" y="${y}" width="${W}" height="${rowH}" fill="transparent"/>
            <text x="${m.l - 10}" y="${cy + 4}" text-anchor="end" class="hbar__lbl">${esc(d.label)} <tspan class="hbar__n">(${d.n})</tspan></text>
            <rect x="${m.l}" y="${cy - 8}" width="${Math.max(2, x(d.value) - m.l)}" height="16" rx="4" fill="${d.color || "#2C4856"}"/>
            ${d.lo != null ? `<line x1="${x(d.lo)}" x2="${x(d.hi)}" y1="${cy}" y2="${cy}" stroke="#7FA0B0" stroke-width="2"/>
              <line x1="${x(d.lo)}" x2="${x(d.lo)}" y1="${cy - 5}" y2="${cy + 5}" stroke="#7FA0B0" stroke-width="2"/>
              <line x1="${x(d.hi)}" x2="${x(d.hi)}" y1="${cy - 5}" y2="${cy + 5}" stroke="#7FA0B0" stroke-width="2"/>` : ""}
            <text x="${x(Math.max(d.value, d.hi || 0)) + 8}" y="${cy + 4}" class="hbar__val">${fmt(d.value)}</text>
          </g>`;
        }).join("")}
      </svg>`;
    };
    draw();
    let rt; window.addEventListener("resize", () => { clearTimeout(rt); rt = setTimeout(draw, 120); });
  }

  /* ---------- Centro de datos: mercado inmobiliario ---------- */
  const inmo = $("[data-inmo]");
  if (inmo) {
    fetchJSON("data/inmobiliario/resumen.json").then(R => {
      const usd = v => "US$" + Math.round(v).toLocaleString("en-US");
      inmo.querySelector("[data-inmo-kpis]").innerHTML = `
        <div><span>Anuncios</span><strong>${R.n_total}</strong></div>
        <div><span>Venta / alquiler</span><strong>${R.n_venta} / ${R.n_alquiler}</strong></div>
        <div><span>US$/m² mediana (venta)</span><strong>${usd(R.usd_m2_mediana_total)}</strong></div>
        <div><span>Renta mediana mensual</span><strong>${usd(R.renta_mediana_total)}</strong></div>`;
      $$("[data-inmo-csv]").forEach(a => (a.href = R.descargas.csv));
      $$("[data-inmo-xlsx]").forEach(a => (a.href = R.descargas.xlsx));
      hbars(inmo.querySelector("[data-inmo-m2]"),
        R.venta.filter(v => v.usd_m2_mediana).map(v => ({ label: v.sector, value: v.usd_m2_mediana, lo: v.usd_m2_p25, hi: v.usd_m2_p75, n: v.n })),
        { fmt: usd, label: "Precio mediano por metro cuadrado de venta por sector" });
      hbars(inmo.querySelector("[data-inmo-rent]"),
        R.alquiler.map(a => ({ label: a.sector, value: a.precio_mediano, n: a.n, color: "#B35231" })),
        { fmt: usd, label: "Renta mensual mediana por sector" });
    }).catch(() => { inmo.querySelector("[data-inmo-kpis]").innerHTML = '<p class="empty">No se pudieron cargar los datos.</p>'; });
  }

  /* ---------- Market intelligence ---------- */
  const needsMarkets = $("[data-markets]");
  if (needsMarkets) {
    fetchData("data/markets.json").then(({ d: M }) => {
      const set = (sel, v) => $$(sel).forEach(el => (el.textContent = v));
      const mid = (M.fx.buy + M.fx.sell) / 2;
      set("[data-fx-buy]", M.fx.buy.toFixed(2));
      set("[data-fx-sell]", M.fx.sell.toFixed(2));
      set("[data-fx-mid]", mid.toFixed(2));
      set("[data-fx-date]", fmtDate(M.fx.date, { month: "short", day: "numeric", year: "numeric" }));
      set("[data-tpm]", M.policy.tpm.toFixed(2) + "%");
      set("[data-tpm-action]", M.policy.lastAction + " · " + fmtDate(M.policy.lastDecision, { month: "short", day: "numeric" }));
      set("[data-infl]", M.policy.inflationYoY.toFixed(2) + "%");
      set("[data-infl-sub]", M.policy.inflationDate + " · meta " + M.policy.inflationTarget);
      set("[data-next-meeting]", M.policy.nextMeetingLabel || fmtDate(M.policy.nextMeeting, { month: "short", day: "numeric", year: "numeric" }));
      if (M.policy.nextMeetingNote) set("[data-next-meeting-note]", M.policy.nextMeetingNote);
      set("[data-updated]", fmtDate(M.updated, { month: "short", day: "numeric", year: "numeric" }));
      if (!M.sample) $$("[data-sample-flag]").forEach(el => el.remove());

      // 12-month FX change
      const h = M.fxHistory;
      if (h.length > 1) {
        const ch = ((h[h.length - 1].value - h[0].value) / h[0].value) * 100;
        set("[data-fx-change]", (ch >= 0 ? "+" : "") + ch.toFixed(2) + "% en 12 meses (prom. mensual)");
      }

      const fxEl = $("#fx-chart");
      if (fxEl) {
        let chart = lineChart(fxEl, h, { fmt: v => v.toFixed(2), label: "Tasa de referencia USD/DOP, promedio mensual" });
        $$("[data-range]").forEach(b => b.addEventListener("click", () => {
          $$("[data-range]").forEach(x => x.setAttribute("aria-pressed", String(x === b)));
          const n = Number(b.dataset.range);
          chart = lineChart(fxEl, h.slice(-n), { fmt: v => v.toFixed(2), label: "Tasa de referencia USD/DOP, promedio mensual" });
        }));
      }
      const tpmEl = $("#tpm-chart");
      if (tpmEl) lineChart(tpmEl, M.tpmHistory, { fmt: v => v.toFixed(2) + "%", step: true, color: "#B35231", label: "Tasa de política monetaria del BCRD" });

      const tb = $("#decisions-body");
      if (tb) tb.innerHTML = M.decisions.map(d => `
        <tr><td>${fmtDate(d.date, { month: "short", day: "numeric", year: "numeric" })}</td>
        <td>${esc(d.action)}</td><td class="num">${d.rate.toFixed(2)}%</td><td>${esc(d.note)}</td></tr>`).join("");

      const links = $("#bcrd-links");
      if (links) links.innerHTML = M.links.map(l => `<li><a href="${esc(l.url)}" target="_blank" rel="noopener">${esc(l.label)} ↗</a></li>`).join("");

      // Converter
      const amt = $("#conv-amount"), dir = $("#conv-dir"), out = $("#conv-out");
      if (amt && dir && out) {
        const calc = () => {
          const a = parseFloat(amt.value) || 0;
          const r = dir.value === "usd-dop" ? a * M.fx.buy : a / M.fx.sell;
          const cur = dir.value === "usd-dop" ? "RD$" : "US$";
          out.textContent = cur + " " + r.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        };
        amt.addEventListener("input", calc); dir.addEventListener("change", calc); calc();
      }
    }).catch(() => $$("[data-fx-mid],[data-tpm]").forEach(el => (el.textContent = "—")));
  }
})();
