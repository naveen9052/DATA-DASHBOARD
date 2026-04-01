from flask import Flask, jsonify, render_template, request
import csv
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import io
import base64
from datetime import datetime
from collections import defaultdict

app = Flask(__name__)
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

# ── helpers ────────────────────────────────────────────────

def load_csv(filename):
    path = os.path.join(DATA_DIR, filename)
    with open(path, newline="") as f:
        return list(csv.DictReader(f))

def chart_to_base64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=130, bbox_inches="tight", facecolor=fig.get_facecolor())
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode()
    plt.close(fig)
    return b64

DARK_BG = "#0f1117"
CARD_BG = "#1a1d27"
ACCENT  = "#4f8ef7"
GREEN   = "#3ecf8e"
AMBER   = "#f5a623"
CORAL   = "#f76f6f"
PURPLE  = "#a78bfa"
TEXT    = "#e2e8f0"
MUTED   = "#64748b"
PALETTE = [ACCENT, GREEN, AMBER, CORAL, PURPLE, "#38bdf8", "#fb923c"]

def apply_style():
    plt.rcParams.update({
        "figure.facecolor": DARK_BG, "axes.facecolor": CARD_BG,
        "axes.edgecolor": "#2d3148", "axes.labelcolor": MUTED,
        "axes.titlecolor": TEXT, "axes.titlesize": 12, "axes.titlepad": 12,
        "axes.titleweight": "bold",
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.spines.left": False, "axes.spines.bottom": False,
        "xtick.color": MUTED, "ytick.color": MUTED,
        "xtick.labelsize": 9, "ytick.labelsize": 9,
        "grid.color": "#2d3148", "grid.linewidth": 0.6,
        "text.color": TEXT, "font.family": "DejaVu Sans",
        "legend.frameon": False, "legend.labelcolor": TEXT, "legend.fontsize": 9,
    })

# ══════════════════════════════════════════════════════════
#  SALES API
# ══════════════════════════════════════════════════════════

@app.route("/api/sales/summary")
def sales_summary():
    rows = load_csv("sales.csv")
    for r in rows:
        r["units"]   = int(r["Units"])
        r["price"]   = float(r["Price"])
        r["revenue"] = r["units"] * r["price"]
        r["date"]    = datetime.strptime(r["Date"], "%Y-%m-%d")

    total = sum(r["revenue"] for r in rows)

    monthly = defaultdict(float)
    for r in rows:
        monthly[r["date"].strftime("%b")] += r["revenue"]
    month_order = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    monthly_list = [{"month": m, "revenue": round(monthly.get(m, 0))} for m in month_order]

    cat = defaultdict(float)
    for r in rows:
        cat[r["Category"]] += r["revenue"]
    cat_list = [{"category": k, "revenue": round(v)} for k, v in sorted(cat.items(), key=lambda x: -x[1])]

    products = defaultdict(lambda: {"units": 0, "revenue": 0})
    for r in rows:
        products[r["Product"]]["units"] += r["units"]
        products[r["Product"]]["revenue"] += r["revenue"]
    top5 = sorted(products.items(), key=lambda x: -x[1]["revenue"])[:5]
    top5_list = [{"product": k, "units": v["units"], "revenue": round(v["revenue"])} for k, v in top5]

    best_month = max(monthly_list, key=lambda x: x["revenue"])["month"]

    return jsonify({
        "total_revenue": round(total),
        "total_records": len(rows),
        "best_month": best_month,
        "monthly_avg": round(total / 12),
        "monthly": monthly_list,
        "by_category": cat_list,
        "top_products": top5_list,
    })

@app.route("/api/sales/chart/<chart_type>")
def sales_chart(chart_type):
    rows = load_csv("sales.csv")
    for r in rows:
        r["units"]   = int(r["Units"])
        r["price"]   = float(r["Price"])
        r["revenue"] = r["units"] * r["price"]
        r["date"]    = datetime.strptime(r["Date"], "%Y-%m-%d")

    apply_style()

    if chart_type == "monthly":
        monthly = defaultdict(float)
        for r in rows:
            monthly[r["date"].strftime("%b")] += r["revenue"]
        mo = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
        vals = [monthly.get(m, 0) / 1000 for m in mo]
        fig, ax = plt.subplots(figsize=(10, 4))
        bars = ax.bar(mo, vals, color=ACCENT, width=0.6, zorder=3)
        best = vals.index(max(vals))
        bars[best].set_color(GREEN)
        for b, v in zip(bars, vals):
            ax.text(b.get_x()+b.get_width()/2, b.get_height()+1, f"₹{v:.0f}K",
                    ha="center", va="bottom", fontsize=7.5, color=TEXT)
        ax.yaxis.grid(True, zorder=0)
        ax.set_ylim(0, max(vals)*1.22)
        ax.set_title("Monthly Revenue 2024")
        patch = mpatches.Patch(color=GREEN, label="Best month")
        ax.legend(handles=[patch])

    elif chart_type == "category":
        cat = defaultdict(float)
        for r in rows:
            cat[r["Category"]] += r["revenue"]
        labels = list(cat.keys())
        sizes  = list(cat.values())
        fig, ax = plt.subplots(figsize=(6, 6))
        fig.patch.set_facecolor(DARK_BG)
        ax.set_facecolor(DARK_BG)
        wedges, _, ats = ax.pie(sizes, colors=PALETTE[:len(labels)], autopct="%1.1f%%",
                                 startangle=140, pctdistance=0.72,
                                 wedgeprops={"linewidth": 2, "edgecolor": DARK_BG})
        for at in ats:
            at.set_color(DARK_BG); at.set_fontsize(9); at.set_fontweight("bold")
        ax.legend(wedges, labels, loc="lower center", bbox_to_anchor=(0.5, -0.08), ncol=2)
        ax.set_title("Revenue by Category")

    elif chart_type == "products":
        products = defaultdict(lambda: {"units": 0, "revenue": 0})
        for r in rows:
            products[r["Product"]]["units"]   += r["units"]
            products[r["Product"]]["revenue"] += r["revenue"]
        top5 = sorted(products.items(), key=lambda x: -x[1]["revenue"])[:5]
        names = [p[0] for p in top5]
        revs  = [p[1]["revenue"] / 1000 for p in top5]
        fig, ax = plt.subplots(figsize=(9, 4.5))
        bars = ax.barh(names, revs, color=PALETTE[:5], height=0.55, zorder=3)
        for b, v in zip(bars, revs):
            ax.text(b.get_width()+5, b.get_y()+b.get_height()/2, f"₹{v:.0f}K",
                    va="center", fontsize=9, color=TEXT)
        ax.set_xlim(0, max(revs)*1.25)
        ax.xaxis.grid(True, zorder=0)
        ax.invert_yaxis()
        ax.set_title("Top 5 Products by Revenue")

    else:
        return jsonify({"error": "Unknown chart type"}), 400

    return jsonify({"image": chart_to_base64(fig)})


# ══════════════════════════════════════════════════════════
#  STUDENTS API
# ══════════════════════════════════════════════════════════

@app.route("/api/students/summary")
def students_summary():
    rows = load_csv("students.csv")
    for r in rows:
        r["Score"] = float(r["Score"])

    scores   = [r["Score"] for r in rows]
    avg      = sum(scores) / len(scores)
    passed   = sum(1 for s in scores if s >= 50)
    topper   = max(rows, key=lambda r: r["Score"])

    subjects = defaultdict(list)
    for r in rows:
        subjects[r["Subject"]].append(r["Score"])
    sub_avgs = {s: round(sum(v)/len(v), 1) for s, v in subjects.items()}

    bins   = [0, 50, 60, 70, 80, 90, 100]
    labels = ["<50","50-60","61-70","71-80","81-90","91-100"]
    counts = [0]*6
    for s in scores:
        for i in range(len(bins)-1):
            if bins[i] <= s < bins[i+1] or (i == 5 and s == 100):
                counts[i] += 1
                break

    return jsonify({
        "total": len(rows),
        "average": round(avg, 1),
        "pass_rate": round(passed / len(rows) * 100, 1),
        "topper_name": topper["Name"],
        "topper_score": topper["Score"],
        "topper_subject": topper["Subject"],
        "subject_averages": sub_avgs,
        "distribution": {"labels": labels, "counts": counts},
    })

@app.route("/api/students/chart/<chart_type>")
def students_chart(chart_type):
    rows = load_csv("students.csv")
    for r in rows:
        r["Score"] = float(r["Score"])
    apply_style()

    if chart_type == "distribution":
        scores = [r["Score"] for r in rows]
        bins   = [0, 50, 60, 70, 80, 90, 100]
        lbls   = ["<50","50-60","61-70","71-80","81-90","91-100"]
        counts, _ = np.histogram(scores, bins=bins)
        fig, ax = plt.subplots(figsize=(9, 4.5))
        bars = ax.bar(lbls, counts, color=PALETTE[:6], width=0.6, zorder=3)
        for b, c in zip(bars, counts):
            if c > 0:
                ax.text(b.get_x()+b.get_width()/2, b.get_height()+0.2,
                        str(c), ha="center", va="bottom", fontsize=11, fontweight="bold", color=TEXT)
        ax.yaxis.grid(True, zorder=0)
        ax.set_ylim(0, max(counts)*1.3)
        ax.set_title("Score Distribution")

    elif chart_type == "radar":
        subjects = defaultdict(list)
        for r in rows:
            subjects[r["Subject"]].append(r["Score"])
        sub_avgs = {s: sum(v)/len(v) for s, v in subjects.items()}
        subjs  = list(sub_avgs.keys())
        avgs   = list(sub_avgs.values())
        N      = len(subjs)
        angles = np.linspace(0, 2*np.pi, N, endpoint=False).tolist()
        vp = avgs + [avgs[0]]; ap = angles + [angles[0]]
        fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
        fig.patch.set_facecolor(DARK_BG); ax.set_facecolor(CARD_BG)
        ax.plot(ap, vp, color=ACCENT, linewidth=2)
        ax.fill(ap, vp, color=ACCENT, alpha=0.25)
        ax.set_xticks(angles); ax.set_xticklabels(subjs, fontsize=11, color=TEXT)
        ax.set_ylim(60, 100); ax.yaxis.set_tick_params(labelcolor=MUTED, labelsize=7)
        ax.grid(color="#2d3148"); ax.spines["polar"].set_visible(False)
        ax.set_title("Subject Averages Radar", pad=20, fontweight="bold")
        for ang, val in zip(angles, avgs):
            ax.text(ang, val+2.5, f"{val:.1f}", ha="center", fontsize=9, color=GREEN, fontweight="bold")

    elif chart_type == "passfail":
        subjects_list = ["Math","Science","English"]
        fig, axes = plt.subplots(1, 3, figsize=(12, 4))
        fig.patch.set_facecolor(DARK_BG)
        for ax, sub in zip(axes, subjects_list):
            ax.set_facecolor(CARD_BG)
            sd = [r for r in rows if r["Subject"] == sub]
            p  = sum(1 for r in sd if r["Score"] >= 50)
            f  = len(sd) - p
            _, _, ats = ax.pie([p, f], colors=[GREEN, CORAL], autopct="%1.0f%%",
                                startangle=90, pctdistance=0.65,
                                wedgeprops={"linewidth": 2, "edgecolor": DARK_BG})
            for at in ats:
                at.set_color(DARK_BG); at.set_fontsize(10); at.set_fontweight("bold")
            ax.set_title(sub, fontsize=11, pad=10)
        ph = mpatches.Patch(color=GREEN, label="Pass")
        fh = mpatches.Patch(color=CORAL, label="Fail")
        fig.legend(handles=[ph,fh], loc="lower center", ncol=2, bbox_to_anchor=(0.5,-0.06))

    else:
        return jsonify({"error": "Unknown chart"}), 400

    return jsonify({"image": chart_to_base64(fig)})


# ══════════════════════════════════════════════════════════
#  EXPENSES API
# ══════════════════════════════════════════════════════════

@app.route("/api/expenses/summary")
def expenses_summary():
    rows = load_csv("expenses.csv")
    for r in rows:
        r["Amount"] = float(r["Amount"])
        r["date"]   = datetime.strptime(r["Date"], "%Y-%m-%d")

    total = sum(r["Amount"] for r in rows)
    cats  = defaultdict(float)
    for r in rows:
        cats[r["Category"]] += r["Amount"]
    cats_sorted = dict(sorted(cats.items(), key=lambda x: -x[1]))

    weeks = defaultdict(float)
    for r in rows:
        weeks[r["date"].strftime("%Y-W%U")] += r["Amount"]
    weekly_list = [{"week": f"Week {i+1}", "amount": round(v)} for i, v in enumerate(weeks.values())]

    dates    = set(r["date"].date() for r in rows)
    daily    = total / len(dates) if dates else 0
    budgets  = {"Food": 4000, "Shopping": 5000, "Transport": 1000, "Bills": 4000}
    alerts   = [{"category": c, "spent": round(cats.get(c, 0)), "budget": b,
                  "over": round(cats.get(c, 0) - b)}
                for c, b in budgets.items() if cats.get(c, 0) > b]

    return jsonify({
        "total": round(total),
        "daily_avg": round(daily),
        "biggest_category": max(cats_sorted, key=cats_sorted.get),
        "over_budget_count": len(alerts),
        "by_category": [{"category": k, "amount": round(v)} for k, v in cats_sorted.items()],
        "weekly": weekly_list,
        "alerts": alerts,
    })

@app.route("/api/expenses/chart/<chart_type>")
def expenses_chart(chart_type):
    rows = load_csv("expenses.csv")
    for r in rows:
        r["Amount"] = float(r["Amount"])
        r["date"]   = datetime.strptime(r["Date"], "%Y-%m-%d")
    apply_style()

    cats = defaultdict(float)
    for r in rows:
        cats[r["Category"]] += r["Amount"]
    cats_sorted = dict(sorted(cats.items(), key=lambda x: -x[1]))

    if chart_type == "category":
        names = list(cats_sorted.keys())
        amts  = [v/1000 for v in cats_sorted.values()]
        fig, ax = plt.subplots(figsize=(9, 4.5))
        bars = ax.bar(names, amts, color=PALETTE[:len(names)], width=0.55, zorder=3)
        for b, v in zip(bars, amts):
            ax.text(b.get_x()+b.get_width()/2, b.get_height()+0.05,
                    f"₹{v:.1f}K", ha="center", va="bottom", fontsize=9, color=TEXT)
        ax.yaxis.grid(True, zorder=0); ax.set_ylim(0, max(amts)*1.25)
        ax.set_title("Spending by Category")

    elif chart_type == "weekly":
        weeks = defaultdict(float)
        for r in rows:
            weeks[r["date"].strftime("%Y-W%U")] += r["Amount"]
        wlabels = [f"Week {i+1}" for i in range(len(weeks))]
        wvals   = [v/1000 for v in weeks.values()]
        fig, ax = plt.subplots(figsize=(9, 4))
        ax.plot(wlabels, wvals, color=ACCENT, linewidth=2.5, marker="o",
                markersize=9, markerfacecolor=GREEN, markeredgecolor=DARK_BG, markeredgewidth=2, zorder=3)
        ax.fill_between(wlabels, wvals, alpha=0.12, color=ACCENT)
        for i,(l,v) in enumerate(zip(wlabels,wvals)):
            ax.text(i, v+0.12, f"₹{v:.1f}K", ha="center", va="bottom", fontsize=9, color=TEXT)
        ax.yaxis.grid(True, zorder=0); ax.set_ylim(0, max(wvals)*1.3)
        ax.set_title("Weekly Spending Trend")

    elif chart_type == "budget":
        budgets = {"Food":4000,"Shopping":5000,"Transport":1000,"Bills":4000}
        bcats   = list(budgets.keys())
        bspent  = [cats.get(c,0)/1000 for c in bcats]
        blimits = [budgets[c]/1000 for c in bcats]
        x = np.arange(len(bcats)); w = 0.35
        fig, ax = plt.subplots(figsize=(9, 4.5))
        ax.bar(x-w/2, bspent,  width=w, color=CORAL,  zorder=3, label="Spent")
        ax.bar(x+w/2, blimits, width=w, color=ACCENT, zorder=3, label="Budget", alpha=0.7)
        for i,(s,l) in enumerate(zip(bspent,blimits)):
            ax.text(i-w/2, s+0.05, f"₹{s:.1f}K", ha="center", va="bottom", fontsize=8, color=TEXT)
            ax.text(i+w/2, l+0.05, f"₹{l:.1f}K", ha="center", va="bottom", fontsize=8, color=MUTED)
        ax.set_xticks(x); ax.set_xticklabels(bcats)
        ax.yaxis.grid(True, zorder=0); ax.legend(); ax.set_title("Actual vs Budget")

    else:
        return jsonify({"error": "Unknown chart"}), 400

    return jsonify({"image": chart_to_base64(fig)})


# ══════════════════════════════════════════════════════════
#  ADD DATA API
# ══════════════════════════════════════════════════════════

@app.route("/api/add/expense", methods=["POST"])
def add_expense():
    data = request.get_json()
    path = os.path.join(DATA_DIR, "expenses.csv")
    with open(path, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([data["date"], data["category"], data["amount"], data["description"]])
    return jsonify({"status": "ok", "message": "Expense added!"})

@app.route("/api/add/sale", methods=["POST"])
def add_sale():
    data = request.get_json()
    path = os.path.join(DATA_DIR, "sales.csv")
    with open(path, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([data["date"], data["product"], data["category"], data["units"], data["price"]])
    return jsonify({"status": "ok", "message": "Sale added!"})

@app.route("/api/add/student", methods=["POST"])
def add_student():
    data = request.get_json()
    score = float(data["score"])
    if score >= 90: grade = "A"
    elif score >= 80: grade = "B"
    elif score >= 70: grade = "C"
    elif score >= 50: grade = "D"
    else: grade = "F"
    path = os.path.join(DATA_DIR, "students.csv")
    with open(path, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([data["name"], data["subject"], score, grade])
    return jsonify({"status": "ok", "message": "Student added!", "grade": grade})


# ══════════════════════════════════════════════════════════
#  PAGES
# ══════════════════════════════════════════════════════════

@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True, port=5000)
