/**
 * 金样业务预览 · 通用逻辑
 * 页面需提供 window.GOLD_CASE 配置，并包含对应 DOM 节点。
 *
 * 固定四段：
 *  1. #tabs     章节跳转
 *  2. #video    视频播放
 *  3. #strip    关键画面
 *  4. #pptGrid  PPT 页截图
 */
(function () {
  const cfg = window.GOLD_CASE;
  if (!cfg) {
    console.error("GOLD_CASE missing");
    return;
  }

  // 视频编辑器入口（有则显示按钮）
  const editorUrl = cfg.editorUrl || cfg.editor || "";
  const editorMount =
    document.getElementById("editorActions") ||
    document.querySelector(".actions");
  if (editorUrl && editorMount) {
    let btn = document.getElementById("btnOpenEditor");
    if (!btn) {
      btn = document.createElement("a");
      btn.id = "btnOpenEditor";
      btn.className = "btn editor";
      btn.target = "_blank";
      btn.rel = "noopener noreferrer";
      editorMount.insertBefore(btn, editorMount.firstChild);
    }
    btn.href = editorUrl;
    btn.textContent = cfg.editorLabel || "打开视频编辑器";
    btn.title = cfg.editorHint || "在新标签打开业务图层编辑（Revideo）";
  }

  const video = document.getElementById("video");
  const clock = document.getElementById("clock");
  const seek = document.getElementById("seek");
  const tabs = document.getElementById("tabs");
  const strip = document.getElementById("strip");
  const pptGrid = document.getElementById("pptGrid");
  const captionEl = document.getElementById("caption");
  const sceneLabel = document.getElementById("sceneLabel");
  const btnPlay = document.getElementById("btnPlay");
  const lightbox = document.getElementById("lightbox");
  const lightboxImg = document.getElementById("lightboxImg");

  const SCENES = cfg.scenes || [];
  const THUMBS = cfg.thumbs || [];
  const SLIDES = cfg.slides || [];
  const CAPTIONS = cfg.captions || [];
  const DURATION_FALLBACK = cfg.duration || 90;
  let currentId = null;

  function sceneAt(t) {
    for (const sc of SCENES) if (t >= sc.start && t < sc.end) return sc;
    return SCENES[SCENES.length - 1] || { id: "end", label: "—", start: 0, end: DURATION_FALLBACK };
  }

  function captionAt(t) {
    for (const c of CAPTIONS) {
      if (t >= c.start && t < c.end) return c.text;
    }
    return "";
  }

  function showAt(t) {
    const sc = sceneAt(t);
    if (sc.id !== currentId) {
      currentId = sc.id;
      tabs.querySelectorAll("button").forEach((el) => {
        el.classList.toggle("active", el.dataset.id === sc.id);
      });
    }
    const dur =
      video.duration && isFinite(video.duration) ? video.duration : DURATION_FALLBACK;
    clock.textContent = `${t.toFixed(2)} / ${dur.toFixed(2)}s`;
    sceneLabel.textContent = `当前章节：${sc.label}`;
    if (Math.abs(parseFloat(seek.value) - t) > 0.12) seek.value = String(t);

    const cap = captionAt(t);
    if (cap) {
      captionEl.textContent = cap;
      captionEl.classList.add("show");
    } else {
      captionEl.classList.remove("show");
    }

    let best = null;
    let bestD = 1e9;
    strip.querySelectorAll("button").forEach((el) => {
      const tt = parseFloat(el.dataset.t);
      const d = Math.abs(tt - t);
      if (d < bestD) {
        bestD = d;
        best = el;
      }
      el.classList.remove("active");
    });
    if (best && bestD < 10) best.classList.add("active");
  }

  function jumpTo(t, play) {
    video.currentTime = t;
    showAt(t);
    if (play !== false) {
      video.play().catch(() => {});
      if (btnPlay) btnPlay.textContent = "暂停";
    }
  }

  // 1) chapters
  SCENES.forEach((sc) => {
    const b = document.createElement("button");
    b.type = "button";
    b.dataset.id = sc.id;
    b.innerHTML = `<span>${sc.label}</span><span class="t">${Number(sc.start).toFixed(0)}s</span>`;
    b.addEventListener("click", () => jumpTo(sc.start + 0.05, true));
    tabs.appendChild(b);
  });

  // 3) key frames
  THUMBS.forEach((th) => {
    const b = document.createElement("button");
    b.type = "button";
    b.dataset.t = String(th.t);
    b.innerHTML = `<img src="${th.src}" alt="${th.title}" loading="lazy" /><div class="cap"><strong>${th.title}</strong>${th.note || ""} · ${th.t}s</div>`;
    b.addEventListener("click", () => jumpTo(th.t, true));
    strip.appendChild(b);
  });

  // 4) PPT slides
  SLIDES.forEach((sl, i) => {
    const a = document.createElement("a");
    a.className = "tile";
    a.href = sl.src;
    a.dataset.index = String(i);
    a.innerHTML = `<img src="${sl.src}" alt="${sl.title}" loading="lazy" /><div class="cap"><strong>${sl.title}</strong>${sl.note || `第 ${i + 1} 页`}</div>`;
    a.addEventListener("click", (e) => {
      e.preventDefault();
      if (!lightbox || !lightboxImg) {
        window.open(sl.src, "_blank");
        return;
      }
      lightboxImg.src = sl.src;
      lightboxImg.alt = sl.title;
      lightbox.classList.add("open");
    });
    pptGrid.appendChild(a);
  });

  if (lightbox) {
    lightbox.addEventListener("click", (e) => {
      if (e.target === lightbox || e.target.classList.contains("close")) {
        lightbox.classList.remove("open");
      }
    });
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") lightbox.classList.remove("open");
    });
  }

  if (btnPlay) {
    btnPlay.addEventListener("click", () => {
      if (video.paused) {
        video.play().catch(() => {});
        btnPlay.textContent = "暂停";
      } else {
        video.pause();
        btnPlay.textContent = "播放";
      }
    });
  }
  const btnRestart = document.getElementById("btnRestart");
  if (btnRestart) {
    btnRestart.addEventListener("click", () => jumpTo(0, true));
  }
  seek.addEventListener("input", () => {
    const t = parseFloat(seek.value);
    video.currentTime = t;
    showAt(t);
  });
  video.addEventListener("timeupdate", () => showAt(video.currentTime));
  video.addEventListener("play", () => {
    if (btnPlay) btnPlay.textContent = "暂停";
  });
  video.addEventListener("pause", () => {
    if (btnPlay) btnPlay.textContent = "播放";
  });
  video.addEventListener("loadedmetadata", () => {
    const d = video.duration || DURATION_FALLBACK;
    seek.max = String(d);
    showAt(video.currentTime || 0);
  });
  if (cfg.videoFallback) {
    video.addEventListener("error", () => {
      if (!video.dataset.fallback) {
        video.dataset.fallback = "1";
        video.src = cfg.videoFallback;
        video.load();
      }
    });
  }

  showAt(0);
})();
