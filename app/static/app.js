// The documented clinic time zone (docs/business-rules.md). Deliberately NOT read from the server,
// so a misconfigured server shows up as wrong times here.
const CLINIC_TZ = "America/New_York";
// Opening hours and lunch, in minutes after clinic midnight (docs/business-rules.md; T-011 Q3: hard-coded).
const OPEN = 8 * 60, CLOSE = 17 * 60, LUNCH = 12 * 60;
document.querySelectorAll(".tzname").forEach((el) => (el.textContent = CLINIC_TZ));

const $ = (id) => document.getElementById(id);
const state = {
  doctors: [], patients: [], doctorId: null, patientId: null, date: null, len: 30, slot: null, resched: null,
  page: 1, status: "", rows: [], today: [], todayView: matchMedia("(max-width: 768px)").matches ? "list" : "timeline",
};
const STATUS = { scheduled: "Scheduled", checked_in: "Checked in", completed: "Completed", cancelled: "Cancelled", no_show: "No-show", left_unseen: "Left unseen" };
const ICON = {
  ok: '<circle cx="12" cy="12" r="9"/><path d="m8 12 3 3 5-6"/>',
  err: '<circle cx="12" cy="12" r="9"/><path d="M12 8v5M12 16.5v.01"/>',
  empty: '<rect x="3" y="4" width="18" height="17" rx="2"/><path d="M8 2v4M16 2v4M3 10h18M9 14l6 5M15 14l-6 5"/>',
  chevron: '<path d="m9 6 6 6-6 6"/>',
};
const svg = (name) => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${ICON[name]}</svg>`;

// ---------- helpers ----------
function esc(v) {
  const d = document.createElement("div");
  d.textContent = String(v ?? "");
  return d.innerHTML.replace(/"/g, "&quot;").replace(/'/g, "&#39;"); // safe inside attributes too
}
const money = (cents) => "$" + (cents / 100).toFixed(2);
const fmtDay = (iso) => new Date(iso).toLocaleDateString("en-GB", { timeZone: CLINIC_TZ, weekday: "short", day: "numeric", month: "short" });
const fmtTime = (iso) => new Date(iso).toLocaleTimeString("en-US", { timeZone: CLINIC_TZ, hour: "numeric", minute: "2-digit" });
const fmtWhen = (iso) => `${fmtDay(iso)}, ${fmtTime(iso)}`;
const shortTime = (iso) => fmtTime(iso).replace(/ [AP]M$/, "");
const clinicDay = (iso) => new Date(iso).toLocaleDateString("en-CA", { timeZone: CLINIC_TZ });
// Minutes after clinic midnight.
function clinicMinutes(iso) {
  const [h, m] = new Date(iso).toLocaleTimeString("en-GB", { timeZone: CLINIC_TZ, hour: "2-digit", minute: "2-digit", hourCycle: "h23" }).split(":");
  return +h * 60 + +m;
}
// Calendar arithmetic on "YYYY-MM-DD" keys (noon UTC, so no time zone can shift the day).
const keyDate = (key) => new Date(key + "T12:00:00Z");
const addDays = (key, n) => new Date(keyDate(key).getTime() + n * 864e5).toISOString().slice(0, 10);
const isWeekend = (key) => [0, 6].includes(keyDate(key).getUTCDay());
const nextClinicDay = (key) => { do key = addDays(key, 1); while (isWeekend(key)); return key; };
const fmtKey = (key, opts) => keyDate(key).toLocaleDateString("en-GB", { timeZone: "UTC", ...opts });
const todayKey = () => clinicDay(Date.now());
const nameOf = (list, id) => (list.find((x) => x.id === id) || {}).name || `#${id}`;
const badge = (s) => `<span class="cb-badge" data-status="${esc(s)}">${esc(STATUS[s] || s)}</span>`;
// title, hint and action are inserted as raw HTML: callers must esc() anything that comes from the API.
const empty = (title, hint = "", action = "") =>
  `<div class="cb-empty">${svg("empty")}<p class="cb-empty__title">${title}</p>${hint ? `<p>${hint}</p>` : ""}${action}</div>`;
const skeleton = (n = 5) =>
  `<div aria-busy="true" style="display:grid;gap:14px;padding:var(--space-3) 0">${Array.from({ length: n }, (_, i) => `<span class="cb-skel" style="width:${[40, 100, 85, 70, 90][i % 5]}%"></span>`).join("")}</div>`;

// Success toasts hide themselves; errors stay until dismissed (FR-4).
function toast(title, sub = "", kind = "ok") {
  const t = document.createElement("div");
  t.className = `cb-toast cb-toast--${kind}`;
  t.setAttribute("role", kind === "ok" ? "status" : "alert");
  t.innerHTML = `<span class="cb-toast__icon">${svg(kind)}</span><div class="cb-toast__body"><strong>${esc(title)}</strong>${sub ? `<span class="cb-sub">${esc(sub)}</span>` : ""}</div>` +
    (kind === "ok" ? "" : `<button class="cb-toast__close" aria-label="Dismiss">×</button>`);
  t.querySelector(".cb-toast__close")?.addEventListener("click", () => t.remove());
  $("toasts").append(t);
  if (kind === "ok") setTimeout(() => t.remove(), 5000);
}
const fail = (title, e) => toast(title, e.message, "err");

async function api(path, opts = {}) {
  let res;
  try {
    const { headers, ...rest } = opts; // caller headers add to the JSON Content-Type default instead of replacing it
    res = await fetch(path, { ...rest, headers: { ...(opts.body ? { "Content-Type": "application/json" } : {}), ...headers } });
  } catch { throw new Error("Could not reach the server"); }
  if (res.status === 204) return null;
  const data = await res.json().catch(() => ({}));
  if (res.status === 401 && typeof onUnauthorized === "function") onUnauthorized(); // session ended: back to the login form
  if (!res.ok) {
    let msg = data.detail ?? res.statusText;
    if (Array.isArray(msg)) msg = msg.map((e) => `${(e.loc || []).slice(1).join(".")}: ${e.msg}`).join("; ");
    throw Object.assign(new Error(`${res.status} · ${msg}`), { status: res.status });
  }
  return data;
}

// ---------- theme: System follows the OS; Light and Dark are remembered in this browser ----------
document.querySelectorAll('input[name="theme"]').forEach((r) => {
  r.checked = r.value === (document.documentElement.dataset.theme || "system");
  r.addEventListener("change", () => {
    if (r.value === "system") delete document.documentElement.dataset.theme;
    else document.documentElement.dataset.theme = r.value;
    try { r.value === "system" ? localStorage.removeItem("cb-theme") : localStorage.setItem("cb-theme", r.value); } catch {}
  });
});

// ---------- routing (FR-2) ----------
const SCREENS = ["book", "appointments", "today", "revenue", "users", "account"];
const ADMIN_SCREENS = ["revenue", "users"];
function route() {
  if (!state.user) return;
  let screen = SCREENS.includes(location.hash.slice(1)) ? location.hash.slice(1) : "book"; // T-011 Q2: Book by default
  if (state.user.must_change_password) screen = "account";
  else if (ADMIN_SCREENS.includes(screen) && state.user.role !== "admin") screen = "book";
  $("screen-login").hidden = true;
  for (const s of SCREENS) $("screen-" + s).hidden = s !== screen;
  document.querySelectorAll(".cb-nav a").forEach((a) =>
    a.getAttribute("href") === "#" + screen ? a.setAttribute("aria-current", "page") : a.removeAttribute("aria-current"));
  if (screen === "appointments") loadList();
  if (screen === "today") loadToday();
  if (screen === "users") loadUsers();
  if (screen === "account") $("account-who").textContent = `Signed in as ${state.user.username} (${state.user.role})`;
}
window.addEventListener("hashchange", route);

// ---------- book ----------
// Searchable pickers (FR-5): the typed name must match one exactly, and the combobox below fills it in.
function pick(kind) {
  const list = kind === "doctor" ? state.doctors : state.patients;
  const name = $(kind).value.trim().toLowerCase();
  const found = list.find((x) => x.name.toLowerCase() === name);
  state[kind + "Id"] = found ? found.id : null;
  $(kind + "-hint").textContent = !found ? (name ? "Pick a name from the list" : "")
    : kind === "doctor" ? found.specialty : found.insured ? "Insured" : "Not insured";
}
// Combobox: a filtered listbox under the input. Arrow keys move, Enter picks, Esc closes.
function combo(kind, items, extra, changed) {
  const input = $(kind), box = $(kind + "-list");
  let matches = [], active = -1;
  const show = (open) => { box.hidden = !open; input.setAttribute("aria-expanded", open); if (!open) input.removeAttribute("aria-activedescendant"); };
  const mark = (name, q) => {
    const i = q ? name.toLowerCase().indexOf(q) : -1;
    return i < 0 ? esc(name) : esc(name.slice(0, i)) + `<mark>${esc(name.slice(i, i + q.length))}</mark>` + esc(name.slice(i + q.length));
  };
  function render() {
    // A name that is already picked shows the whole list again, so it is easy to switch.
    const q = state[kind + "Id"] ? "" : input.value.trim().toLowerCase();
    matches = items().filter((x) => x.name.toLowerCase().includes(q));
    active = Math.min(Math.max(active, q ? 0 : -1), matches.length - 1);
    box.innerHTML = matches.length
      ? matches.map((x, i) => `<li class="cb-option" role="option" id="${kind}-opt-${esc(x.id)}" data-i="${i}" aria-selected="${i === active}"><span>${mark(x.name, q)}</span>${extra(x)}</li>`).join("")
      : `<li class="cb-option" aria-disabled="true">No ${kind} matches “${esc(input.value)}”</li>`;
    if (active >= 0) { input.setAttribute("aria-activedescendant", `${kind}-opt-${matches[active].id}`); box.children[active].scrollIntoView({ block: "nearest" }); }
    else input.removeAttribute("aria-activedescendant");
    show(true);
  }
  const choose = (x) => { input.value = x.name; changed(); show(false); };
  input.addEventListener("input", () => { active = 0; changed(); render(); });
  input.addEventListener("focus", render);
  input.addEventListener("click", () => box.hidden && render());
  input.addEventListener("blur", () => show(false));
  box.addEventListener("mousedown", (e) => { // mousedown + preventDefault keeps focus in the input
    const li = e.target.closest("[data-i]");
    e.preventDefault();
    if (li) choose(matches[+li.dataset.i]);
  });
  input.addEventListener("keydown", (e) => {
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      e.preventDefault();
      if (box.hidden) return render();
      active = (active + (e.key === "ArrowDown" ? 1 : -1) + matches.length) % matches.length;
      render();
    } else if (e.key === "Enter" && !box.hidden && matches[active]) { e.preventDefault(); choose(matches[active]); }
    else if (e.key === "Escape" && !box.hidden) { e.stopPropagation(); show(false); }
  });
}
combo("doctor", () => state.doctors, (d) => `<span class="cb-sub">${esc(d.specialty)}</span>`,
  () => { const before = state.doctorId; pick("doctor"); if (state.doctorId !== before) loadSlots(); });
combo("patient", () => state.patients, (p) => p.insured ? '<span class="cb-tag cb-tag--brand">Insured</span>' : "",
  () => { pick("patient"); renderSummary(); });

function renderDays() {
  let key = todayKey();
  if (isWeekend(key)) key = nextClinicDay(key);
  const days = [];
  for (let i = 0; i < 10; i++, key = nextClinicDay(key)) days.push(key);
  $("days").innerHTML = days.map((k) =>
    `<button class="cb-day" data-day="${k}" aria-pressed="${k === state.date}" aria-label="${fmtKey(k, { weekday: "long", day: "numeric", month: "long" })}">` +
    `<span class="cb-day__dow">${fmtKey(k, { weekday: "short" })}</span><span class="cb-day__num">${fmtKey(k, { day: "numeric" })}</span><span class="cb-day__mon">${fmtKey(k, { month: "short" })}</span></button>`).join("");
  $("date").value = state.date;
  $("date").min = todayKey();
  $("date").max = addDays(todayKey(), 60);
}
function setDate(key) { state.date = key; renderDays(); loadSlots(); }
$("days").addEventListener("click", (e) => { const b = e.target.closest(".cb-day"); if (b) setDate(b.dataset.day); });
$("date").addEventListener("change", () => { if ($("date").value) setDate($("date").value); });
document.querySelectorAll('input[name="len"]').forEach((r) => r.addEventListener("change", () => { state.len = +r.value; loadSlots(); }));

let slotSeq = 0;
async function loadSlots() {
  state.slot = null; renderSummary();
  const seq = ++slotSeq, date = state.date;
  if (!state.doctorId) { $("slots").innerHTML = empty("Pick a doctor", "Free slots for the chosen day show here."); return; }
  if (date < $("date").min || date > $("date").max) {
    $("slots").innerHTML = empty("Pick a date in the next 60 days", `Bookings are open from ${fmtKey($("date").min, { weekday: "short", day: "numeric", month: "short" })} to ${fmtKey($("date").max, { weekday: "short", day: "numeric", month: "short" })}.`);
    return;
  }
  $("slots").innerHTML = skeleton(3);
  try {
    const res = await api(`/doctors/${state.doctorId}/slots?date=${date}`);
    let slots = withOwnSlots(res.slots, state.resched, date);
    if (seq !== slotSeq) return;
    // A 60-min visit needs the next half hour free too (this also keeps it clear of lunch and closing).
    const free = new Set(slots.map(Date.parse));
    if (state.len === 60) slots = slots.filter((s) => free.has(Date.parse(s) + 18e5));
    renderSlots(slots, date, res.closed);
  } catch (e) {
    if (seq !== slotSeq) return;
    $("slots").innerHTML = empty("Could not load free slots", esc(e.message));
    fail("Could not load free slots", e);
  }
}

function renderSlots(slots, date, closed) {
  if (!slots.length) {
    const next = nextClinicDay(date);
    const label = fmtKey(next, { weekday: "short", day: "numeric", month: "short" });
    $("slots").innerHTML = empty(`No free slots on ${esc(fmtKey(date, { weekday: "short", day: "numeric", month: "short" }))}`,
      closed ? `${esc(closed)}.` : `${esc(nameOf(state.doctors, state.doctorId))} has no ${state.len}-minute opening this day.`,
      next <= $("date").max ? `<button class="cb-btn" id="next-day" data-day="${next}">Next open day: ${esc(label)} ${svg("chevron")}</button>` : "");
    $("next-day")?.addEventListener("click", (e) => setDate(e.currentTarget.dataset.day));
    return;
  }
  const own = state.resched && Date.parse(state.resched.start);
  const group = (title, list) => list.length ? `<div class="cb-slots__group"><h3 class="cb-caption">${title} · ${list.length} free</h3><div class="cb-slots__grid">${list.map((s) =>
    `<button class="cb-slot${Date.parse(s) === own ? " cb-slot--current" : ""}" aria-pressed="false" data-start="${esc(s)}" aria-label="${esc(fmtWhen(s))}">${esc(shortTime(s))}</button>`).join("")}</div></div>` : "";
  $("slots").innerHTML = group("Morning", slots.filter((s) => clinicMinutes(s) < LUNCH)) + group("Afternoon", slots.filter((s) => clinicMinutes(s) >= LUNCH));
}

$("slots").addEventListener("click", (e) => {
  const b = e.target.closest(".cb-slot");
  if (!b) return;
  document.querySelectorAll(".cb-slot").forEach((x) => x.setAttribute("aria-pressed", x === b));
  state.slot = b.dataset.start;
  renderSummary();
});

function renderSummary() {
  const d = state.doctors.find((x) => x.id === state.doctorId), p = state.patients.find((x) => x.id === state.patientId);
  const r = state.resched, dash = '<span class="cb-muted">—</span>';
  const row = (k, v) => `<div><dt>${k}</dt><dd>${v}</dd></div>`;
  $("summary").innerHTML =
    row("Patient", p ? `${esc(p.name)}${p.insured ? ' <span class="cb-tag cb-tag--brand">Insured</span>' : ""}` : dash) +
    row("Doctor", d ? `${esc(d.name)}<span class="cb-sub">${esc(d.specialty)}</span>` : dash) +
    row("When", (r ? `<span class="cb-summary__old cb-num">${esc(fmtWhen(r.start))}</span><br>` : "") +
      (state.slot ? `<span class="cb-num">${esc(fmtWhen(state.slot))}</span><span class="cb-sub">Clinic time, ${CLINIC_TZ}</span>` : dash)) +
    row("Length", `${state.len} min`);
  $("confirm").disabled = !(state.doctorId && state.patientId && state.slot);
  $("confirm").textContent = r ? (state.slot ? `Move to ${fmtTime(state.slot)}` : `Reschedule #${r.id}`) : "Confirm booking";
}

$("confirm").addEventListener("click", async () => {
  $("confirm").disabled = true;
  if (state.resched) return reschedule();
  try {
    const a = await api("/appointments", {
      method: "POST",
      body: JSON.stringify({ doctor_id: state.doctorId, patient_id: state.patientId, start: state.slot, duration_minutes: state.len }),
    });
    toast(`Booked #${a.id}, ${fmtWhen(a.start)}`, `Fee ${money(a.fee_cents)}`);
    $("patient").value = ""; pick("patient"); // doctor and day stay (AC-1.3); the patient is picked fresh each time
  } catch (e) { fail("Could not book this slot", e); }
  await loadSlots();
});

// ---------- reschedule (reuses the Book screen's slot picker) ----------
// The slots API counts the appointment being moved as busy, but the reschedule endpoint ignores it,
// so add its own 30-min starts back. Nothing else can sit there: the doctor can't be double-booked.
function withOwnSlots(slots, appt, day) {
  if (!appt || new Date(appt.start).toLocaleDateString("en-CA", { timeZone: CLINIC_TZ }) !== day) return slots;
  const own = [];
  for (let m = 0; m < appt.duration_minutes; m += 30) own.push(new Date(Date.parse(appt.start) + m * 6e4).toISOString());
  const taken = new Set(slots.map(Date.parse));
  return [...slots, ...own.filter((s) => !taken.has(Date.parse(s)))].sort((a, b) => Date.parse(a) - Date.parse(b));
}

function setReschedule(a) {
  state.resched = a;
  $("resched-bar").hidden = !a;
  $("doctor").disabled = $("patient").disabled = !!a;
  $("book-title").textContent = a ? "Reschedule" : "Book a visit";
  if (a) {
    $("resched-label").innerHTML = `<strong>Rescheduling #${esc(a.id)}</strong>, now ${esc(fmtWhen(a.start))}. Doctor and patient stay the same.`;
    $("doctor").value = nameOf(state.doctors, a.doctor_id); pick("doctor");
    $("patient").value = nameOf(state.patients, a.patient_id); pick("patient");
    state.len = a.duration_minutes;
    document.querySelector(`input[name="len"][value="${a.duration_minutes}"]`).checked = true;
    state.date = clinicDay(a.start);
    renderDays();
  }
  loadSlots();
}

async function reschedule() {
  try {
    const a = await api(`/appointments/${state.resched.id}/reschedule`, {
      method: "POST",
      body: JSON.stringify({ start: state.slot, duration_minutes: state.len }),
    });
    toast(`Moved #${a.id} to ${fmtWhen(a.start)}`, `Fee ${money(a.fee_cents)}`);
    setReschedule(null);
  } catch (e) { fail("Could not reschedule", e); await loadSlots(); }
}
$("resched-exit").addEventListener("click", () => setReschedule(null));

// ---------- appointments ----------
$("chips").innerHTML = [["", "All"], ...Object.entries(STATUS)].map(([s, label]) =>
  `<button class="cb-chip" ${s ? `data-status="${s}"` : ""} data-filter="${s}" aria-pressed="${s === state.status}">${label}</button>`).join("");
$("chips").addEventListener("click", (e) => {
  const b = e.target.closest(".cb-chip");
  if (!b) return;
  state.status = b.dataset.filter; state.page = 1;
  document.querySelectorAll(".cb-chip").forEach((x) => x.setAttribute("aria-pressed", x === b));
  loadList();
});

function actionsFor(a) {
  const btn = (act, label, cls = "") => `<button class="${cls}" data-act="${act}" data-id="${a.id}">${label}</button>`;
  const more = (items) => `<details class="cb-more"><summary aria-label="More actions for #${a.id}">⋯</summary><div class="cb-menu">${items}</div></details>`;
  if (a.status === "scheduled") return btn("check-in", "Check in", "cb-btn cb-btn--sm") +
    more(btn("reschedule", "Reschedule") + btn("no-show", "Mark no-show") + "<hr>" + btn("cancel", "Cancel appointment", "cb-menu__danger"));
  if (a.status === "checked_in") return btn("complete", "Complete", "cb-btn cb-btn--sm") + more(btn("left-unseen", "Left unseen"));
  return "";
}

function feeCell(a) {
  const extra = a.cancellation_fee_cents ? `<span class="cb-sub">+ ${money(a.cancellation_fee_cents)} ${a.status === "no_show" ? "no-show fee" : "late cancel"}</span>` : "";
  return money(a.fee_cents) + extra;
}

function table(rows) {
  return `<table class="cb-table"><thead><tr><th>#</th><th>When</th><th>Patient · Doctor</th><th>Length</th><th>Status</th><th>Fee</th><th><span class="cb-sr">Actions</span></th></tr></thead><tbody>${rows.map((a) => `
    <tr>
      <td data-col="id" class="cb-num cb-muted">#${esc(a.id)}</td>
      <td data-col="when" class="cb-num"><strong>${esc(fmtTime(a.start))}</strong><span class="cb-sub">${esc(fmtDay(a.start))}</span></td>
      <td data-col="who">${esc(nameOf(state.patients, a.patient_id))}<span class="cb-sub">${esc(nameOf(state.doctors, a.doctor_id))}</span></td>
      <td data-col="length" class="cb-num">${esc(a.duration_minutes)} min</td>
      <td data-col="status">${badge(a.status)}</td>
      <td data-col="fee" class="cb-num">${feeCell(a)}</td>
      <td data-col="actions"><div class="cb-actions">${actionsFor(a)}</div></td>
    </tr>`).join("")}</tbody></table>`;
}

async function loadList() {
  $("list").innerHTML = skeleton();
  try {
    const q = new URLSearchParams({ page: state.page, page_size: $("f-size").value });
    if (state.status) q.set("status", state.status);
    const data = await api("/appointments?" + q);
    state.rows = data.items;
    $("list").innerHTML = data.items.length ? table(data.items)
      : empty(state.status ? `No ${STATUS[state.status].toLowerCase()} appointments` : "No appointments yet", "Bookings show up here.");
    const pages = Math.max(1, Math.ceil(data.total / data.page_size));
    $("pageinfo").textContent = `Page ${data.page} of ${pages} · ${data.total} total`;
    $("prev").disabled = data.page <= 1;
    $("next").disabled = data.page >= pages;
  } catch (e) {
    $("list").innerHTML = empty("Could not load appointments", "Check the server, then press Refresh.");
    $("pageinfo").textContent = "";
    $("prev").disabled = $("next").disabled = true;
    fail("Could not load appointments", e);
  }
}

$("prev").addEventListener("click", () => { state.page--; loadList(); });
$("next").addEventListener("click", () => { state.page++; loadList(); });
$("f-size").addEventListener("change", () => { state.page = 1; loadList(); });
$("refresh").addEventListener("click", loadList);

// Cancel and No-show go through a dialog that names the appointment (AC-3.3).
function confirmDialog(a, act) {
  const cancel = act === "cancel";
  $("dlg-title").textContent = cancel ? `Cancel appointment #${a.id}?` : `Mark #${a.id} as no-show?`;
  $("dlg-rule").textContent = cancel
    ? "This frees the slot. Cancelling less than 24 hours before the start costs 50% of the consultation fee."
    : "A no-show costs 100% of the consultation fee. It can only be marked once the start time has passed.";
  $("dlg-facts").innerHTML = `<strong>${esc(nameOf(state.patients, a.patient_id))} with ${esc(nameOf(state.doctors, a.doctor_id))}</strong>` +
    `<span class="cb-sub cb-num">${esc(fmtWhen(a.start))} · ${esc(a.duration_minutes)} min</span>`;
  $("dlg-ok").textContent = cancel ? "Cancel appointment" : "Mark no-show";
  $("dlg").returnValue = "";
  $("dlg").showModal();
  return new Promise((resolve) => $("dlg").addEventListener("close", () => resolve($("dlg").returnValue === "ok"), { once: true }));
}

$("list").addEventListener("click", async (e) => {
  const b = e.target.closest("button[data-act]");
  if (!b) return;
  b.closest("details")?.removeAttribute("open");
  const { act, id } = b.dataset;
  if (act === "reschedule") {
    try { setReschedule(await api(`/appointments/${id}`)); location.hash = "#book"; } catch (err) { fail("Could not open the appointment", err); }
    return;
  }
  if ((act === "cancel" || act === "no-show") && !(await confirmDialog(state.rows.find((r) => r.id === +id), act))) return;
  try {
    const a = await api(`/appointments/${id}/${act}`, { method: "POST" });
    const fee = a.cancellation_fee_cents ? `Fee charged: ${money(a.cancellation_fee_cents)}` : a.status === "cancelled" ? "No fee charged" : "";
    toast(`#${a.id} is now ${STATUS[a.status].toLowerCase()}`, fee);
  } catch (err) { fail(`Could not update #${id}`, err); }
  loadList();
});

// Row menus: close on Esc or a click elsewhere.
document.addEventListener("click", (e) => document.querySelectorAll(".cb-more[open]").forEach((d) => d.contains(e.target) || d.removeAttribute("open")));
document.addEventListener("keydown", (e) => {
  if (e.key !== "Escape") return;
  document.querySelectorAll(".cb-more[open]").forEach((d) => { d.removeAttribute("open"); d.querySelector("summary").focus(); });
});

// ---------- today (read-only, T-011 Q1) ----------
document.querySelectorAll('input[name="view"]').forEach((r) => {
  r.checked = r.value === state.todayView;
  r.addEventListener("change", () => { state.todayView = r.value; renderToday(); });
});
$("refresh-today").addEventListener("click", loadToday);

async function loadToday() {
  $("todaylabel").textContent = new Date().toLocaleDateString("en-US", { timeZone: CLINIC_TZ, weekday: "long", month: "long", day: "numeric" });
  $("today").innerHTML = `<div class="cb-card">${skeleton()}</div>`;
  try { state.today = await api("/appointments/today"); renderToday(); }
  catch (e) {
    $("stats").innerHTML = "";
    $("today").innerHTML = `<div class="cb-card">${empty("Could not load today's appointments", "Check the server, then press Refresh.")}</div>`;
    fail("Could not load today", e);
  }
}

function renderToday() {
  const rows = state.today, now = Date.now(), nowMin = clinicMinutes(now);
  $("stats").innerHTML = Object.keys(STATUS).map((s) =>
    `<div class="cb-stat"><span class="cb-stat__n">${rows.filter((a) => a.status === s).length}</span>${badge(s)}</div>`).join("");
  if (!rows.length) { $("today").innerHTML = `<div class="cb-card">${empty("No appointments today", "Booked visits for today show up here.")}</div>`; return; }
  const late = (a) => a.status === "scheduled" && Date.parse(a.start) < now ? Math.floor((now - Date.parse(a.start)) / 6e4) : 0;
  const byDoctor = state.doctors.map((d) => ({ d, visits: rows.filter((a) => a.doctor_id === d.id) }));

  if (state.todayView === "list") {
    $("today").innerHTML = `<div class="cb-daylist">${byDoctor.filter((g) => g.visits.length).map(({ d, visits }) => {
      const next = visits.find((a) => a.status === "scheduled");
      return `<section><h3>${esc(d.name)} <small>${esc(d.specialty)}</small></h3><ol>${visits.map((a) => `
        <li${a === next ? " data-next" : ""}><time>${esc(fmtTime(a.start))}</time>
          <span class="cb-who">${esc(nameOf(state.patients, a.patient_id))}${a === next ? ' <span class="cb-tag cb-tag--brand">Next</span>' : ""}${late(a) ? ` <span class="cb-tag cb-tag--warn">Late ${late(a)} min</span>` : ""}<span class="cb-sub">${esc(a.duration_minutes)} min</span></span>
          ${badge(a.status)}</li>`).join("")}</ol></section>`;
    }).join("")}</div>`;
    return;
  }

  const open = clinicDay(now) === todayKey() && nowMin >= OPEN && nowMin < CLOSE && !isWeekend(todayKey());
  const hours = Array.from({ length: (CLOSE - OPEN) / 60 }, (_, h) => `<span class="cb-tl__hour" style="--h:${h}">${((OPEN / 60 + h - 1) % 12) + 1} ${OPEN / 60 + h < 12 ? "AM" : "PM"}</span>`).join("");
  const block = (a) => {
    const status = STATUS[a.status] + (late(a) ? ` · Late ${late(a)} min` : ""), who = nameOf(state.patients, a.patient_id);
    return `<div class="cb-tl__block" data-status="${esc(a.status)}" style="--start:${clinicMinutes(a.start) - OPEN};--len:${+a.duration_minutes}" tabindex="0"
      aria-label="${esc(`${fmtTime(a.start)}, ${who}, ${a.duration_minutes} minutes, ${status}`)}"><b>${esc(shortTime(a.start))} ${esc(who)}</b><i>${esc(status)}</i></div>`;
  };
  $("today").innerHTML = `<div class="cb-tl" role="region" aria-label="Today's timeline" tabindex="0"><div class="cb-tl__grid" style="--cols:${byDoctor.length}">
    <div class="cb-tl__corner"></div>${byDoctor.map(({ d, visits }) => `<div class="cb-tl__doc"><strong>${esc(d.name)}</strong><span class="cb-sub">${esc(d.specialty)} · ${visits.length} visit${visits.length === 1 ? "" : "s"}</span></div>`).join("")}
    <div class="cb-tl__body"><div class="cb-tl__axis">${hours}${open ? `<span class="cb-tl__nowlabel" style="--now:${nowMin - OPEN}">${esc(shortTime(now))}</span>` : ""}</div>
    ${byDoctor.map(({ visits }) => `<div class="cb-tl__col">${visits.map(block).join("")}</div>`).join("")}
    <div class="cb-tl__lunch" aria-hidden="true"><span>Lunch</span></div>
    ${open ? `<div class="cb-tl__now" style="--now:${nowMin - OPEN}" aria-hidden="true"></div>` : ""}</div></div></div>`;
}

// ---------- revenue (T-016, admin-only; the session cookie is the only credential) ----------
let revSeq = 0;
// Same rule as the server: both ends inclusive, at most 366 days.
function revenueRangeError(from, to) {
  const iso = /^\d{4}-\d{2}-\d{2}$/; // an empty or 5-digit-year value must not reach the date maths
  if (!iso.test(from) || !iso.test(to)) return "Pick both a From and a To date.";
  if (from > to) return "From must be on or before To.";
  if ((keyDate(to) - keyDate(from)) / 864e5 >= 366) return "The range can be at most 366 days.";
  return "";
}

// Axis step in cents: the smallest 1, 2 or 5 x 10^k dollars (at least $10) that keeps the axis to 5 steps or fewer.
function chartStep(maxCents) {
  for (let k = 1000; ; k *= 10) for (const m of [1, 2, 5]) if (Math.ceil(maxCents / (m * k)) <= 5) return m * k;
}

// Inline SVG, one stacked bar per day (consultation below, penalty above); "" when there is nothing to draw.
// Cents become pixels only for geometry; every shown amount comes from the stored cents.
function revenueChart(days) {
  if (!days.length) return "";
  const BAR = 30, PITCH = 48, LEFT = 48, TOP = 28, H = 180, base = TOP + H, labels = days.length <= 14;
  const max = Math.max(...days.map((d) => d.total_cents)), step = chartStep(max), top = Math.max(step, Math.ceil(max / step) * step);
  const w = LEFT + days.length * PITCH, h = base + 30, px = (c) => (c * H) / top, r = (n) => Math.round(n * 10) / 10;
  const whole = (c) => "$" + (c / 100).toLocaleString("en-US");
  let grid = "";
  for (let v = 0; v <= top; v += step) {
    const y = r(base - px(v));
    grid += `<line class="c-grid" x1="${LEFT}" x2="${w}" y1="${y}" y2="${y}"/><text x="${LEFT - 8}" y="${y + 4}" text-anchor="end">${whole(v)}</text>`;
  }
  const bars = days.map((d, i) => {
    const x = LEFT + (PITCH - BAR) / 2 + i * PITCH, hc = px(d.consultation_cents), hp = px(d.penalty_cents), gap = hc ? 2 : 0;
    const name = fmtKey(d.date, { weekday: "short", day: "numeric", month: "short" });
    return `<g><title>${esc(name)}: Consultation ${esc(money(d.consultation_cents))}, Penalty ${esc(money(d.penalty_cents))}, Total ${esc(money(d.total_cents))}</title>` +
      (d.consultation_cents ? `<rect class="c-cons" x="${x}" y="${r(base - hc)}" width="${BAR}" height="${r(hc)}" rx="3"/>` : "") +
      (d.penalty_cents ? `<rect class="c-pen" x="${x}" y="${r(base - hc - hp)}" width="${BAR}" height="${r(Math.max(hp - gap, 1))}" rx="3"/>` : "") +
      (labels ? `<text class="c-tot" x="${x + BAR / 2}" y="${r(base - hc - hp - 6)}" text-anchor="middle">${esc(d.total_cents % 100 ? money(d.total_cents) : whole(d.total_cents))}</text>` : "") +
      `<text x="${x + BAR / 2}" y="${base + 20}" text-anchor="middle">${esc(fmtKey(d.date, { weekday: "short", day: "numeric" }))}</text></g>`;
  }).join("");
  const span = `${fmtKey(days[0].date, { weekday: "long", day: "numeric", month: "long" })} to ${fmtKey(days[days.length - 1].date, { weekday: "long", day: "numeric", month: "long" })}`;
  const totals = labels ? `Totals: ${days.map((d) => money(d.total_cents)).join(", ")}.` : "The totals are in the table below.";
  return `<svg class="cb-chart" role="img" aria-label="${esc(`Stacked bars of revenue per day, ${span}. ${totals}`)}" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}">${grid}${bars}</svg>`;
}

function renderRevenue(r) {
  const m = (c) => esc(money(c)), day = (k) => esc(fmtKey(k, { weekday: "short", day: "numeric", month: "short", year: "numeric" }));
  const stat = (label, c) => `<div class="cb-stat"><span class="cb-stat__n">${m(c)}</span><span class="cb-muted">${label}</span></div>`;
  const rows = (list, name) => list.map((x) => `<tr><td data-col="who"><strong>${name(x)}</strong></td>` +
    [["consultation_cents", "Consultation"], ["penalty_cents", "Penalty"], ["total_cents", "Total"]].map(([k, label]) =>
      `<td data-col="fee" data-label="${label}" class="cb-num cb-right">${m(x[k])}</td>`).join("") + "</tr>");
  const table = (first, list, name) => `<table class="cb-table"><thead><tr><th>${first}</th>` +
    `<th class="cb-right">Consultation</th><th class="cb-right">Penalty</th><th class="cb-right">Total</th></tr></thead><tbody>${rows(list, name).join("")}</tbody></table>`;
  const tbl = (title, first, list, name) => `<section class="cb-card"><h2 class="cb-h2">${title}</h2>${table(first, list, name)}</section>`;
  const phone = globalThis.matchMedia?.("(max-width: 768px)").matches; // the table is the main view on a phone, a toggle elsewhere
  const byDay = (list) => `<section class="cb-card cb-chartcard"><h2 class="cb-h2">Revenue by day</h2>
    <div class="cb-legend"><span><i class="cb-swatch cb-swatch--cons"></i>Consultation</span><span><i class="cb-swatch cb-swatch--pen"></i>Penalty</span></div>
    <div class="cb-chart-scroll">${revenueChart(list)}</div>
    <details class="cb-astable"${phone ? " open" : ""}><summary>Show as table</summary>${table("Day", list, (d) => day(d.date))}</details></section>`;
  $("rev-results").innerHTML = `<div class="cb-stack">
    <p class="cb-muted">${day(r.from)} to ${day(r.to)} · run ${esc(fmtWhen(r.at))}.
      Amounts are gross, counted on the scheduled day in clinic time; a deleted visit drops out.</p>
    <div class="cb-stats">${stat("Consultation", r.data.totals.consultation_cents)}${stat("Penalty", r.data.totals.penalty_cents)}${stat("Total", r.data.totals.total_cents)}</div>
    ${tbl("By doctor", "Doctor", r.data.by_doctor, (d) => esc(d.doctor_name))}
    ${r.data.by_day.length ? byDay(r.data.by_day)
      : `<section class="cb-card">${empty("No revenue in this range", "No completed visits or fees fall on these days.")}</section>`}</div>`;
}

async function runRevenue() {
  const from = $("rev-from").value, to = $("rev-to").value;
  const err = revenueRangeError(from, to);
  $("rev-msg").textContent = err;
  const seq = ++revSeq; // bumped even when invalid, so an in-flight run cannot render under the new range
  if (err) { $("rev-results").innerHTML = ""; return; }
  $("rev-results").innerHTML = skeleton(4);
  try {
    const data = await api(`/reports/revenue?${new URLSearchParams({ from, to })}`);
    if (seq === revSeq) renderRevenue({ from, to, at: Date.now(), data });
  } catch (e) {
    if (seq !== revSeq) return;
    if (e.status === 403) {
      $("rev-results").innerHTML = empty("Administrators only", "Ask an administrator to run the revenue report.");
      return;
    }
    $("rev-results").innerHTML = empty("Could not load the revenue report", esc(e.message), '<button class="cb-btn" type="button" id="rev-retry">Retry</button>');
  }
}
$("rev-form").addEventListener("submit", (e) => { e.preventDefault(); runRevenue(); });
$("rev-results").addEventListener("click", (e) => { if (e.target.closest("#rev-retry")) runRevenue(); });


// ---------- sign in / out, account, users (T-019 to T-023) ----------
// The session cookie is HttpOnly: the page never sees it and stores no credential anywhere.
function showLogin() {
  state.user = null;
  document.querySelector(".cb-app").classList.add("cb-signed-out");
  document.querySelector(".cb-sidebar").hidden = true;
  for (const s of SCREENS) $("screen-" + s).hidden = true;
  $("screen-login").hidden = false;
}
function onUnauthorized() { if (state.user) { showLogin(); toast("Signed out", "Your session ended. Sign in again.", "err"); } }

let appLoaded = false;
async function enter(user) {
  state.user = user;
  document.querySelector(".cb-app").classList.remove("cb-signed-out");
  document.querySelector(".cb-sidebar").hidden = false;
  document.querySelectorAll("[data-admin]").forEach((a) => (a.hidden = user.role !== "admin"));
  $("who-name").textContent = user.username;
  $("who-role").textContent = user.role;
  $("who-until").textContent = fmtWhen(user.expires_at);
  if (user.must_change_password) {
    $("pw-forced").hidden = false;
    document.querySelector(".cb-nav").hidden = true;
    return route();
  }
  $("pw-forced").hidden = true;
  document.querySelector(".cb-nav").hidden = false;
  if (!appLoaded) { appLoaded = true; await loadApp(); } else route();
}

$("login-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  $("login-msg").textContent = "";
  try {
    const user = await api("/auth/login", { method: "POST", body: JSON.stringify({ username: $("login-user").value, password: $("login-pass").value }) });
    $("login-pass").value = "";
    await enter(user);
  } catch (err) {
    $("login-pass").value = "";
    $("login-msg").textContent = err.status === 423
      ? "Too many failed attempts. Try again in 15 minutes or ask an administrator to unlock the account."
      : err.status === 401 ? "Wrong username or password." : "Could not sign in. Try again.";
  }
});

for (const id of ["signout", "signout-side"]) $(id).addEventListener("click", async () => {
  try { await api("/auth/logout", { method: "POST" }); } catch {}
  appLoaded = false;
  location.hash = "";
  showLogin();
});

$("pw-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const current = $("pw-current").value, next = $("pw-new").value;
  $("pw-msg").textContent = "";
  if (next !== $("pw-confirm").value) { $("pw-msg").textContent = "The new passwords do not match."; return; }
  try {
    await api("/auth/change-password", { method: "POST", body: JSON.stringify({ current_password: current, new_password: next }) });
    e.target.reset();
    toast("Password changed", "Your other sessions were signed out.");
    await enter({ ...state.user, must_change_password: false });
  } catch (err) {
    $("pw-msg").textContent = err.status === 403 ? "The current password is wrong."
      : err.status === 422 ? "The new password needs at least 12 characters and must differ from the current one." : "Could not change the password.";
  }
});

// Error text without the "409 · " status prefix: these screens show no status codes (DDR-0003).
const plain = (e) => e.message.replace(/^\d{3} · /, "");

async function loadUsers() {
  $("user-list").innerHTML = skeleton(3);
  try {
    const users = await api("/users");
    $("user-list").innerHTML = `<section class="cb-card"><table class="cb-table"><thead><tr><th>User</th><th>Role</th><th>Status</th><th></th></tr></thead><tbody>` +
      users.map((u) => `<tr><td data-col="who"><strong>${esc(u.username)}</strong></td><td data-col="role">${esc(u.role)}</td><td data-col="status"><span class="cb-badge" data-status="${u.active ? "completed" : "cancelled"}">${u.active ? "Active" : "Disabled"}</span></td><td data-col="actions"><div class="cb-actions">` +
        `<button class="cb-btn cb-btn--sm" data-user="${u.id}" data-do="${u.active ? "disable" : "enable"}">${u.active ? "Disable" : "Enable"}</button>` +
        (u.active ? `<button class="cb-btn cb-btn--sm" data-user="${u.id}" data-do="unlock">Unlock</button>` : "") +
        `<button class="cb-btn cb-btn--sm" data-user="${u.id}" data-do="reset" data-name="${esc(u.username)}">Reset password</button></div></td></tr>`).join("") +
      `</tbody></table></section>`;
  } catch (err) { $("user-list").innerHTML = empty("Could not load users", esc(plain(err))); }
}

$("user-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  $("user-msg").textContent = "";
  try {
    await api("/users", { method: "POST", body: JSON.stringify({ username: $("user-name").value, password: $("user-pass").value, role: $("user-role").value }) });
    e.target.reset();
    toast("User added");
    loadUsers();
  } catch (err) {
    $("user-msg").textContent = err.status === 409 ? "That username is taken." : err.status === 422 ? "Enter a username and a password of at least 12 characters." : "Could not add the user.";
  }
});

$("user-list").addEventListener("click", async (e) => {
  const b = e.target.closest("button[data-do]");
  if (!b) return;
  const url = `/users/${b.dataset.user}`;
  try {
    if (b.dataset.do === "reset") {
      const r = await api(`${url}/reset-password`, { method: "POST" });
      $("temp-who").textContent = b.dataset.name;
      $("temp-value").textContent = r.temporary_password;
      $("dlg-temp").showModal();
      return;
    }
    const body = b.dataset.do === "unlock" ? { active: true } : { active: b.dataset.do === "enable" };
    await api(url, { method: "PATCH", body: JSON.stringify(body) });
    loadUsers();
  } catch (err) { toast("Could not update the user", plain(err), "err"); }
});
$("temp-copy").addEventListener("click", () => navigator.clipboard?.writeText($("temp-value").textContent));
$("dlg-temp").addEventListener("close", () => { $("temp-value").textContent = ""; });

(async function start() {
  try { await enter(await api("/auth/me")); } catch { showLogin(); }
})();

// ---------- init ----------
async function loadApp() {
  state.date = nextClinicDay(todayKey());
  $("rev-from").value = todayKey().slice(0, 8) + "01"; // filled once, so route() never overwrites what the user typed
  $("rev-to").value = todayKey();
  renderDays();
  renderSummary();
  try {
    [state.doctors, state.patients] = await Promise.all([api("/doctors"), api("/patients")]);
    route();
    await loadSlots();
  } catch (e) {
    route();
    $("slots").innerHTML = empty("Could not reach the clinic server", "Check that it is running, then reload the page.");
    fail("Could not reach the API", e);
  }
}
