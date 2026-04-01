// ── State ──────────────────────────────────────────────
const state = { activeTab: "sales", loaded: {} };

const PAGE_META = {
  sales:    { title: "Sales Analysis",    sub: "Live data from sales.csv" },
  students: { title: "Student Analysis",  sub: "Live data from students.csv" },
  expenses: { title: "Expense Tracker",   sub: "Live data from expenses.csv" },
  add:      { title: "Add Data",          sub: "Insert new records into CSV files" },
};

// ── Init ───────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  // set today's date on all date inputs
  const today = new Date().toISOString().split("T")[0];
  ["sale-date","exp-date"].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.value = today;
  });

  // score preview
  const scoreInput = document.getElementById("stu-score");
  if (scoreInput) {
    scoreInput.addEventListener("input", () => {
      const v = parseFloat(scoreInput.value);
      const el = document.getElementById("score-preview");
      if (isNaN(v)) { el.textContent = "Grade will appear here"; el.style.color = "var(--muted)"; return; }
      let grade, color;
      if (v >= 90)      { grade = "A — Excellent!"; color = "var(--green)"; }
      else if (v >= 80) { grade = "B — Good";       color = "var(--accent)"; }
      else if (v >= 70) { grade = "C — Average";    color = "var(--amber)"; }
      else if (v >= 50) { grade = "D — Pass";       color = "var(--muted)"; }
      else              { grade = "F — Fail";        color = "var(--coral)"; }
      el.textContent = `Grade: ${grade}`;
      el.style.color = color;
    });
  }

  // sidebar nav
  document.querySelectorAll(".nav-item").forEach(btn => {
    btn.addEventListener("click", () => switchTab(btn.dataset.tab));
  });

  loadTab("sales");
});

// ── Tab Switch ─────────────────────────────────────────
function switchTab(tab) {
  document.querySelectorAll(".nav-item").forEach(b => b.classList.toggle("active", b.dataset.tab === tab));
  document.querySelectorAll(".tab-section").forEach(s => s.classList.remove("active"));
  document.getElementById(`tab-${tab}`).classList.add("active");
  document.getElementById("page-title").textContent = PAGE_META[tab].title;
  document.getElementById("page-sub").textContent   = PAGE_META[tab].sub;
  state.activeTab = tab;
  loadTab(tab);
}

function loadTab(tab) {
  if (tab === "sales")    loadSales();
  if (tab === "students") loadStudents();
  if (tab === "expenses") loadExpenses();
}

function refreshPage() {
  state.loaded = {};
  loadTab(state.activeTab);
}

// ── Fetch helpers ──────────────────────────────────────
async function apiFetch(url) {
  const res = await fetch(url);
  return res.json();
}

function setChart(cardId, base64) {
  const card = document.getElementById(cardId);
  if (!card) return;
  const body = card.querySelector(".chart-body");
  body.innerHTML = `<img src="data:image/png;base64,${base64}" alt="chart" loading="lazy"/>`;
}

function fmt(n) {
  if (n >= 100000) return "₹" + (n/100000).toFixed(1) + "L";
  if (n >= 1000)   return "₹" + (n/1000).toFixed(1) + "K";
  return "₹" + n.toLocaleString("en-IN");
}

function badge(text, type) {
  return `<span class="badge badge-${type}">${text}</span>`;
}

// ══════════════════════════════════════════════════════
//  SALES
// ══════════════════════════════════════════════════════
async function loadSales() {
  const data = await apiFetch("/api/sales/summary");

  // metrics
  document.getElementById("sales-metrics").innerHTML = `
    <div class="metric-card">
      <div class="m-label">Total Revenue</div>
      <div class="m-value">${fmt(data.total_revenue)}</div>
      <div class="m-sub">${data.total_records} transactions</div>
    </div>
    <div class="metric-card">
      <div class="m-label">Best Month</div>
      <div class="m-value up">${data.best_month}</div>
      <div class="m-sub">Peak sales month</div>
    </div>
    <div class="metric-card">
      <div class="m-label">Monthly Average</div>
      <div class="m-value">${fmt(data.monthly_avg)}</div>
      <div class="m-sub">per month</div>
    </div>
    <div class="metric-card">
      <div class="m-label">Top Product</div>
      <div class="m-value" style="font-size:1.1rem;margin-top:6px">${data.top_products[0]?.product || "—"}</div>
      <div class="m-sub">${fmt(data.top_products[0]?.revenue || 0)}</div>
    </div>
  `;

  // table
  const total = data.top_products.reduce((s, p) => s + p.revenue, 0);
  const tbody = document.querySelector("#sales-table tbody");
  tbody.innerHTML = data.top_products.map((p, i) => {
    const share = ((p.revenue / data.total_revenue) * 100).toFixed(1);
    const badgeType = i === 0 ? "green" : i < 3 ? "amber" : "red";
    return `<tr>
      <td style="color:var(--muted);font-family:'DM Mono',monospace">${i+1}</td>
      <td style="color:var(--text);font-weight:500">${p.product}</td>
      <td>${p.units.toLocaleString()}</td>
      <td style="color:var(--accent);font-family:'DM Mono',monospace">${fmt(p.revenue)}</td>
      <td>${badge(share + "%", badgeType)}</td>
    </tr>`;
  }).join("");

  // charts
  const [monthly, category, products] = await Promise.all([
    apiFetch("/api/sales/chart/monthly"),
    apiFetch("/api/sales/chart/category"),
    apiFetch("/api/sales/chart/products"),
  ]);
  setChart("chart-sales-monthly",  monthly.image);
  setChart("chart-sales-category", category.image);
  setChart("chart-sales-products", products.image);
}

// ══════════════════════════════════════════════════════
//  STUDENTS
// ══════════════════════════════════════════════════════
async function loadStudents() {
  const data = await apiFetch("/api/students/summary");

  document.getElementById("students-metrics").innerHTML = `
    <div class="metric-card">
      <div class="m-label">Total Students</div>
      <div class="m-value">${data.total}</div>
      <div class="m-sub">3 subjects</div>
    </div>
    <div class="metric-card">
      <div class="m-label">Class Average</div>
      <div class="m-value">${data.average}</div>
      <div class="m-sub">out of 100</div>
    </div>
    <div class="metric-card">
      <div class="m-label">Pass Rate</div>
      <div class="m-value up">${data.pass_rate}%</div>
      <div class="m-sub">≥ 50 marks</div>
    </div>
    <div class="metric-card">
      <div class="m-label">Topper</div>
      <div class="m-value" style="font-size:1.1rem;margin-top:6px">${data.topper_name}</div>
      <div class="m-sub">${data.topper_score} — ${data.topper_subject}</div>
    </div>
  `;

  // subject table
  const tbody = document.querySelector("#students-table tbody");
  tbody.innerHTML = Object.entries(data.subject_averages).map(([sub, avg]) => {
    let band, type;
    if (avg >= 80)      { band = "A — Excellent"; type = "green"; }
    else if (avg >= 70) { band = "B — Good";      type = "green"; }
    else if (avg >= 60) { band = "C — Average";   type = "amber"; }
    else                { band = "D — Below Avg"; type = "red"; }
    return `<tr>
      <td style="color:var(--text);font-weight:500">${sub}</td>
      <td style="font-family:'DM Mono',monospace;color:var(--accent)">${avg}</td>
      <td>${band}</td>
      <td>${badge(avg >= 70 ? "On Track" : "Needs Attention", type)}</td>
    </tr>`;
  }).join("");

  const [dist, radar, passfail] = await Promise.all([
    apiFetch("/api/students/chart/distribution"),
    apiFetch("/api/students/chart/radar"),
    apiFetch("/api/students/chart/passfail"),
  ]);
  setChart("chart-stu-dist",  dist.image);
  setChart("chart-stu-radar", radar.image);
  setChart("chart-stu-pass",  passfail.image);
}

// ══════════════════════════════════════════════════════
//  EXPENSES
// ══════════════════════════════════════════════════════
async function loadExpenses() {
  const data = await apiFetch("/api/expenses/summary");

  document.getElementById("expenses-metrics").innerHTML = `
    <div class="metric-card">
      <div class="m-label">Total Spent</div>
      <div class="m-value">${fmt(data.total)}</div>
      <div class="m-sub">April 2024</div>
    </div>
    <div class="metric-card">
      <div class="m-label">Daily Average</div>
      <div class="m-value">${fmt(data.daily_avg)}</div>
      <div class="m-sub">per day</div>
    </div>
    <div class="metric-card">
      <div class="m-label">Top Category</div>
      <div class="m-value down" style="font-size:1.1rem;margin-top:6px">${data.biggest_category}</div>
      <div class="m-sub">highest spending</div>
    </div>
    <div class="metric-card">
      <div class="m-label">Over Budget</div>
      <div class="m-value down">${data.over_budget_count}</div>
      <div class="m-sub">categories exceeded</div>
    </div>
  `;

  // alerts
  const alertsContainer = document.getElementById("alerts-container");
  if (data.alerts.length > 0) {
    alertsContainer.innerHTML = `
      <div class="alert-banner">
        <div class="alert-title">⚠ Budget Alerts — ${data.alerts.length} categories over limit</div>
        <div class="alert-rows">
          ${data.alerts.map(a => `
            <div class="alert-row">
              <div class="cat">${a.category}</div>
              <div class="nums">
                Spent ${fmt(a.spent)} / Budget ${fmt(a.budget)}<br/>
                <span class="over">Over by ${fmt(a.over)}</span>
              </div>
            </div>
          `).join("")}
        </div>
      </div>`;
  } else {
    alertsContainer.innerHTML = "";
  }

  // expense table
  const total = data.total;
  const tbody = document.querySelector("#expenses-table tbody");
  tbody.innerHTML = data.by_category.map(c => {
    const pct = ((c.amount / total) * 100).toFixed(1);
    const type = pct > 30 ? "red" : pct > 20 ? "amber" : "green";
    return `<tr>
      <td style="color:var(--text);font-weight:500">${c.category}</td>
      <td style="font-family:'DM Mono',monospace;color:var(--accent)">${fmt(c.amount)}</td>
      <td>${pct}%</td>
      <td>${badge(pct > 30 ? "High" : pct > 20 ? "Medium" : "Low", type)}</td>
    </tr>`;
  }).join("");

  const [cat, weekly, budget] = await Promise.all([
    apiFetch("/api/expenses/chart/category"),
    apiFetch("/api/expenses/chart/weekly"),
    apiFetch("/api/expenses/chart/budget"),
  ]);
  setChart("chart-exp-cat",    cat.image);
  setChart("chart-exp-weekly", weekly.image);
  setChart("chart-exp-budget", budget.image);
}

// ══════════════════════════════════════════════════════
//  ADD DATA
// ══════════════════════════════════════════════════════
async function addSale() {
  const body = {
    date:     document.getElementById("sale-date").value,
    product:  document.getElementById("sale-product").value.trim(),
    category: document.getElementById("sale-category").value,
    units:    document.getElementById("sale-units").value,
    price:    document.getElementById("sale-price").value,
  };
  const msg = document.getElementById("sale-msg");
  if (!body.product || !body.units || !body.price) {
    msg.textContent = "Please fill all fields."; msg.className = "form-msg err"; return;
  }
  const res = await fetch("/api/add/sale", {
    method: "POST", headers: {"Content-Type":"application/json"}, body: JSON.stringify(body)
  });
  const data = await res.json();
  msg.textContent = "✓ " + data.message; msg.className = "form-msg ok";
  state.loaded = {};
  setTimeout(() => { msg.textContent = ""; }, 3000);
}

async function addExpense() {
  const body = {
    date:        document.getElementById("exp-date").value,
    category:    document.getElementById("exp-category").value,
    amount:      document.getElementById("exp-amount").value,
    description: document.getElementById("exp-desc").value.trim(),
  };
  const msg = document.getElementById("exp-msg");
  if (!body.amount || !body.description) {
    msg.textContent = "Please fill all fields."; msg.className = "form-msg err"; return;
  }
  const res = await fetch("/api/add/expense", {
    method: "POST", headers: {"Content-Type":"application/json"}, body: JSON.stringify(body)
  });
  const data = await res.json();
  msg.textContent = "✓ " + data.message; msg.className = "form-msg ok";
  state.loaded = {};
  setTimeout(() => { msg.textContent = ""; }, 3000);
}

async function addStudent() {
  const body = {
    name:    document.getElementById("stu-name").value.trim(),
    subject: document.getElementById("stu-subject").value,
    score:   document.getElementById("stu-score").value,
  };
  const msg = document.getElementById("stu-msg");
  if (!body.name || !body.score) {
    msg.textContent = "Please fill all fields."; msg.className = "form-msg err"; return;
  }
  const res = await fetch("/api/add/student", {
    method: "POST", headers: {"Content-Type":"application/json"}, body: JSON.stringify(body)
  });
  const data = await res.json();
  msg.textContent = `✓ ${data.message} Grade: ${data.grade}`; msg.className = "form-msg ok";
  state.loaded = {};
  setTimeout(() => { msg.textContent = ""; }, 3000);
}
