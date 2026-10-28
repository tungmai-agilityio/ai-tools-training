  // Apply a saved theme before first paint, so a forced theme never flashes the other one.
  try { const t = localStorage.getItem("cb-theme"); if (t === "light" || t === "dark") document.documentElement.dataset.theme = t; } catch {}
