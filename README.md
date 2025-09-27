# Equinox

***Balancing minds, one insight at a time.***

---

## **Project Overview**

Mental health issues like anxiety and depression often go undetected. While individuals frequently share their struggles on platforms like Reddit, there is no structured way to convert these posts into actionable insights.

**Equinox** addresses this gap by analyzing Reddit posts to generate a **Personalized Wellbeing Score** based on sentiment and language patterns, providing early indicators of emotional health for monitoring and intervention.

---

## **Problem Statement**

Mental health challenges are often silent. People may express their emotional highs and lows on social media, particularly Reddit, but these insights remain unquantified. Equinox aims to transform these textual cues into meaningful, actionable indicators for well-being, enabling early recognition of mental decline and fostering proactive care.

---

## **Aim**

* Represent the **balance between emotional highs and lows**, inspired by the equinox.
* Transform Reddit conversations into a **Personalized Wellbeing Score**.
* Provide **early insights** into emotional decline.
* Enable **continuous monitoring** of mental health over time.
* Offer a **clear picture of emotional health** for better awareness.
* Promote **stability, self-awareness, and proactive care**.

---

## **Feasibility**

Equinox is highly feasible because it leverages:

* **Readily available technologies** (Flask, PRAW, Chart.js)
* **Lightweight NLP models** (VADER Sentiment Analysis)
* **Existing public data sources** (Reddit submissions)

Designed for **scalability and user accessibility**, Equinox can be rapidly deployed as a hackathon MVP while retaining flexibility to evolve into a robust HealthTech platform.

---

## **Tech Stack**

* **Backend:** Python, Flask
* **Data:** Reddit posts via PRAW
* **Sentiment Analysis:** VADER
* **Frontend:** HTML, CSS, JavaScript, Chart.js
* **Styling & Theme:** Dark theme (black + turquoise)
* **Hosting:** Local machine or any Flask-compatible server

---

## **Features**

* Enter a Reddit username to fetch the latest posts.
* Calculate a **Wellbeing Score** using sentiment analysis.
* Visualize **daily mood trends** and **monthly averages** in an interactive graph.
* Display **alerts** when sentiment drops significantly.
* Dark-themed dashboard for clear, modern visualization.

---

## **Installation & Setup**

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/Equinox.git
cd Equinox
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv
```

Activate the environment:

* **Windows:**

```bash
venv\Scripts\activate
```

* **Mac/Linux:**

```bash
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Reddit API Credentials

Replace the placeholders in `app.py` with your own Reddit API credentials:

```python
REDDIT_CLIENT_ID = "YOUR_CLIENT_ID"
REDDIT_CLIENT_SECRET = "YOUR_CLIENT_SECRET"
REDDIT_USER_AGENT = "wellness-tracker-demo by u/YOUR_REDDIT_USERNAME"
```

> You can get credentials by creating a Reddit app here: [https://www.reddit.com/prefs/apps](https://www.reddit.com/prefs/apps)

### 5. Run the App

```bash
python app.py
```

Open your browser and go to:

```
http://127.0.0.1:5000/
```

---

## **Usage**

1. Enter a Reddit username in the homepage input.
2. Click **View Dashboard**.
3. Dashboard shows:

   * Number of posts fetched
   * Daily mood trend (line graph)
   * Alerts for significant emotional drops

---

## **Folder Structure**

```
From-Posts-To-Patterns/
│
├─ app.py
├─ templates/
│   ├─ home.html
│   └─ dashboard.html
├─ static/
│   └─ logo.png
└─ requirements.txt
```

---

## **License**

This project is for educational and hackathon purposes. Do not use without user consent, as it processes public Reddit posts.

---

