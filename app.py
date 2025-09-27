# app.py
import re
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request
import praw
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# --- CONFIG: Replace with your Reddit credentials ---
REDDIT_CLIENT_ID = "R1MF9MFjRJs92nukAzRSoA"
REDDIT_CLIENT_SECRET = "5V1JAMa7_TeofhYRH-KkEX6b7rNcNw"
REDDIT_USER_AGENT = "wellness-tracker-demo"

# --- APP INIT ---
app = Flask(__name__)
analyzer = SentimentIntensityAnalyzer()
user_posts = {}  # in-memory store: username -> list of posts

# --- Reddit Init ---
def init_reddit():
    return praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        user_agent=REDDIT_USER_AGENT,
    )

# --- Preprocess Text for VADER ---
def preprocess_text(text: str) -> str:
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"http\S+", "", text)             # remove URLs
    text = re.sub(r"[^a-z0-9\s.,!?']", " ", text)   # keep basic punctuation
    text = re.sub(r"\s+", " ", text).strip()        # collapse multiple spaces
    return text

# --- Fetch only submissions ---
def fetch_user_submissions(username, limit=100):
    reddit = init_reddit()
    ruser = reddit.redditor(username)
    posts = []
    for s in ruser.submissions.new(limit=limit):
        text = (s.title or "") + " " + (s.selftext or "")
        clean_text = preprocess_text(text)
        posts.append({
            "id": s.id,
            "title": s.title,
            "created": datetime.utcfromtimestamp(s.created_utc),
            "text": clean_text,
        })
    user_posts[username] = posts
    return posts

# --- Sentiment Analysis ---
def analyze_posts(posts):
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

# --- Aggregate daily mood ---
def get_daily_mood(username, days=30):
    posts = user_posts.get(username, [])
    if not posts:
        return []
    analyzed = analyze_posts(posts)
    cutoff = datetime.utcnow() - timedelta(days=days)
    buckets = {}
    for a in analyzed:
        if a["created"] < cutoff:
            continue
        d = a["created"].date().isoformat()
        buckets.setdefault(d, []).append(a["compound"])
    trend = [
        {"date": d, "avg_compound": sum(vals) / len(vals)}
        for d, vals in sorted(buckets.items())
    ]
    return trend

# --- Detect sudden drops ---
def detect_alerts(trend, drop_threshold=0.4):
    alerts = []
    for i in range(1, len(trend)):
        prev = trend[i - 1]["avg_compound"]
        curr = trend[i]["avg_compound"]
        if prev - curr >= drop_threshold:
            alerts.append({
                "date": trend[i]["date"],
                "message": f"⚠️ Sudden mood drop detected: {prev:.2f} → {curr:.2f}"
            })
    return alerts

# --- ROUTES ---
@app.route("/api/fetch/<username>")
def api_fetch(username):
    posts = fetch_user_submissions(username, limit=100)
    return jsonify({"fetched": len(posts)})

@app.route("/api/mood_trend/<username>")
def api_mood(username):
    days = int(request.args.get("days", 30))
    trend = get_daily_mood(username, days)
    alerts = detect_alerts(trend)
    return jsonify({"trend": trend, "alerts": alerts})

@app.route("/dashboard/<username>")
def dashboard(username):
    return render_template("dashboard.html", username=username)

# --- RUN APP ---
if __name__ == "__main__":
    app.run(debug=True)
