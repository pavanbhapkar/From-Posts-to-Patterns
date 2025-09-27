# app.py
import re
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request, redirect, url_for
import praw
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# --- CONFIG: Replace with your Reddit credentials ---
REDDIT_CLIENT_ID = "R1MF9MFjRJs92nukAzRSoA"
REDDIT_CLIENT_SECRET = "5V1JAMa7_TeofhYRH-KkEX6b7rNcNw"
REDDIT_USER_AGENT = "wellness-tracker-demo by u/YOUR_REDDIT_USERNAME"

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
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"[^a-z0-9\s.,!?']", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
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
def get_daily_mood(username, days=60):
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
        {"date": d, "avg_compound": sum(vals)/len(vals)}
        for d, vals in sorted(buckets.items())
    ]
    return trend

# --- Generate alerts if compound score < threshold ---
def get_alerts(username, threshold=-0.5):
    trend = get_daily_mood(username, days=60)
    alerts = []
    for t in trend:
        if t["avg_compound"] < threshold:
            alerts.append({"date": t["date"], "message": "Significant drop in mood"})
    return alerts

# --- ROUTES ---
@app.route("/")
def home():
    return render_template("home.html")

@app.route("/dashboard")
def dashboard():
    username = request.args.get("username")
    if not username:
        return redirect(url_for("home"))
    return render_template("dashboard.html", username=username)

@app.route("/api/fetch/<username>")
def api_fetch(username):
    try:
        posts = fetch_user_submissions(username, limit=100)
        return jsonify({"fetched": len(posts)})
    except Exception as e:
        return jsonify({"fetched": 0, "error": str(e)})

@app.route("/api/mood_trend/<username>")
def api_mood(username):
    days = int(request.args.get("days", 60))
    daily = get_daily_mood(username, days)
    alerts = get_alerts(username)
    return jsonify({"trend": daily, "alerts": alerts})

# --- RUN APP ---
if __name__ == "__main__":
    app.run(debug=True)
