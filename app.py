# app.py
import re
from datetime import datetime, timedelta
from collections import defaultdict
from flask import Flask, render_template, jsonify, request, redirect, url_for
import praw
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# ---------- CONFIG ----------
# Replace these with your own Reddit app credentials
REDDIT_CLIENT_ID = "R1MF9MFjRJs92nukAzRSoA"
REDDIT_CLIENT_SECRET = "5V1JAMa7_TeofhYRH-KkEX6b7rNcNw"
REDDIT_USER_AGENT = "wellness-tracker-demo"

# Alert detection parameters
ALERT_DROP_THRESHOLD = 0.40   # prev_day - curr_day >= this triggers a drop alert
ALERT_LOOKBACK_DAYS = 60      # how much history to show
ALERT_MIN_POINTS = 2          # need at least 2 days to compare

# ---------- APP INIT ----------
app = Flask(__name__)
analyzer = SentimentIntensityAnalyzer()

# In-memory store: username -> list of posts
# Each post: {"id","title","created":datetime,"text"}
user_posts = {}

# ---------- REDDIT + PREPROCESS ----------
def init_reddit():
    return praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        user_agent=REDDIT_USER_AGENT
    )

def preprocess_text(text: str) -> str:
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"http\S+", "", text)             # remove urls
    text = re.sub(r"[^a-z0-9\s.,!?']", " ", text)   # keep basic punctuation
    text = re.sub(r"\s+", " ", text).strip()        # collapse whitespace
    return text

def fetch_user_submissions(username: str, limit: int = 100):
    """
    Fetch latest submissions (title + selftext) for username and store in user_posts.
    Returns list of posts.
    """
    reddit = init_reddit()
    ruser = reddit.redditor(username)
    posts = []
    for s in ruser.submissions.new(limit=limit):
        text = (s.title or "") + " " + (s.selftext or "")
        clean = preprocess_text(text)
        posts.append({
            "id": s.id,
            "title": s.title or "",
            "created": datetime.utcfromtimestamp(s.created_utc),
            "text": clean
        })
    user_posts[username] = posts
    return posts

# ---------- SENTIMENT & AGGREGATION ----------
def analyze_posts(posts):
    """
    Return list of sentiment dicts for posts
    each: {"id","title","created","compound","pos","neg","neu"}
    """
    results = []
    for p in posts:
        scores = analyzer.polarity_scores(p["text"])
        results.append({
            "id": p["id"],
            "title": p["title"],
            "created": p["created"],
            "compound": scores["compound"],
            "pos": scores["pos"],
            "neg": scores["neg"],
            "neu": scores["neu"],
        })
    return results

def get_daily_mood(username: str, days: int = 30):
    """
    Return list of {"date","avg_compound","count"} (sorted ascending by date)
    """
    posts = user_posts.get(username, [])
    if not posts:
        return []
    analyzed = analyze_posts(posts)
    cutoff = datetime.utcnow() - timedelta(days=days)
    buckets = defaultdict(list)
    for a in analyzed:
        if a["created"] < cutoff:
            continue
        d = a["created"].date().isoformat()
        buckets[d].append(a["compound"])
    trend = []
    for d in sorted(buckets.keys()):
        vals = buckets[d]
        trend.append({"date": d, "avg_compound": sum(vals) / len(vals), "count": len(vals)})
    return trend

def get_monthly_mood(username: str, months: int = 6):
    """
    Return recent months aggregated: list of {"month","avg_compound","post_count"} sorted recent -> older
    """
    posts = user_posts.get(username, [])
    if not posts:
        return []
    analyzed = analyze_posts(posts)
    buckets = defaultdict(list)
    for a in analyzed:
        m = a["created"].strftime("%Y-%m")
        buckets[m].append(a["compound"])
    months_sorted = sorted(buckets.keys(), reverse=True)[:months]
    result = []
    for m in months_sorted:
        vals = buckets[m]
        result.append({"month": m, "avg_compound": sum(vals) / len(vals), "post_count": len(vals)})
    return result

# ---------- ALERT DETECTION (IN-APP) ----------
def detect_alerts_from_trend(trend, drop_threshold=ALERT_DROP_THRESHOLD):
    """
    trend: list of {"date","avg_compound",...} sorted ascending.
    Return alerts list with {"index","date","prev","curr","message"}.
    """
    alerts = []
    for i in range(1, len(trend)):
        prev = trend[i-1]["avg_compound"]
        curr = trend[i]["avg_compound"]
        if prev - curr >= drop_threshold:
            alerts.append({
                "index": i,
                "date": trend[i]["date"],
                "prev": prev,
                "curr": curr,
                "message": f"Sudden drop: {prev:.2f} → {curr:.2f}"
            })
    return alerts

# ---------- ROUTES / API ----------
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        if username:
            # fetch right away and redirect
            try:
                fetch_user_submissions(username, limit=100)
            except Exception as e:
                # store empty in-memory so dashboard can show a friendly message
                user_posts[username] = []
                return render_template("home.html", error=str(e))
            return redirect(url_for("dashboard", username=username))
    return render_template("home.html")

@app.route("/dashboard/<username>")
def dashboard(username):
    # Render page; the front-end will call fetch + mood endpoints to populate charts.
    return render_template("dashboard.html", username=username)

@app.route("/api/fetch/<username>")
def api_fetch(username):
    try:
        posts = fetch_user_submissions(username, limit=100)
        return jsonify({"fetched": len(posts)})
    except Exception as e:
        return jsonify({"error": str(e), "fetched": 0}), 500

@app.route("/api/mood_trend/<username>")
def api_mood_trend(username):
    days = int(request.args.get("days", ALERT_LOOKBACK_DAYS))
    trend = get_daily_mood(username, days=days)
    alerts = detect_alerts_from_trend(trend)
    return jsonify({"trend": trend, "alerts": alerts})

@app.route("/api/monthly/<username>")
def api_monthly(username):
    months = int(request.args.get("months", 6))
    m = get_monthly_mood(username, months=months)
    return jsonify(m)

# ---------- RUN ----------
if __name__ == "__main__":
    app.run(debug=True, port=5000)
