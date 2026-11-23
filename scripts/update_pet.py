import json
import os
import urllib.request
from datetime import datetime, timedelta, timezone

USER = os.environ["PET_USER"]
TOKEN = os.environ.get("GITHUB_TOKEN", "")
OUTPUT = "pet/pet.svg"

TEMPLATE = """<svg xmlns="http://www.w3.org/2000/svg" width="420" height="260" viewBox="0 0 420 260">
  <style>
    .pet { animation: bounce 1.2s ease-in-out infinite; }
    .eye { animation: blink 4s infinite; transform-box: fill-box; transform-origin: center; }
    @keyframes bounce { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-10px); } }
    @keyframes blink { 0%, 92%, 100% { transform: scaleY(1); } 95% { transform: scaleY(0.1); } }
    .label { font: bold 14px sans-serif; fill: #555; }
    .msg { font: 15px sans-serif; fill: #222; }
  </style>
  <rect width="420" height="260" rx="16" fill="#f6f8fa" stroke="#d0d7de"/>
  <g class="pet">
    <circle cx="100" cy="115" r="18" fill="#7cc7ff"/>
    <circle cx="200" cy="115" r="18" fill="#7cc7ff"/>
    <ellipse cx="150" cy="175" rx="80" ry="65" fill="#7cc7ff"/>
    <g class="eye"><ellipse cx="122" cy="160" rx="11" ry="13" fill="#fff"/><circle cx="125" cy="162" r="6" fill="#222"/></g>
    <g class="eye"><ellipse cx="178" cy="160" rx="11" ry="13" fill="#fff"/><circle cx="181" cy="162" r="6" fill="#222"/></g>
    __MOUTH__
    <ellipse cx="120" cy="238" rx="18" ry="8" fill="#5aa9e6"/>
    <ellipse cx="180" cy="238" rx="18" ry="8" fill="#5aa9e6"/>
  </g>
  <text x="260" y="90" class="label">Food: __FOOD__%</text>
  <rect x="260" y="100" width="120" height="14" rx="7" fill="#d0d7de"/>
  <rect x="260" y="100" width="__BAR__" height="14" rx="7" fill="#2da44e"/>
  <text x="260" y="150" class="msg">Mood: __MOOD__</text>
  <text x="260" y="175" class="msg">__MSG__</text>
  <text x="20" y="245" class="label">Eats commits, grows happy. Updated automatically.</text>
</svg>"""

HAPPY = '<path d="M128 190 Q150 212 172 190" stroke="#222" stroke-width="3" fill="none"/>'
OKAY = '<line x1="130" y1="195" x2="170" y2="195" stroke="#222" stroke-width="3"/>'
HUNGRY = '<path d="M128 200 Q150 185 172 200" stroke="#222" stroke-width="3" fill="none"/>'


def fetch_events():
    url = f"https://api.github.com/users/{USER}/events/public?per_page=100"
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "pet-bot",
    })
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req) as response:
        return json.load(response)


def count_recent_commits(events, days=7):
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    total = 0
    for event in events:
        if event.get("type") != "PushEvent":
            continue
        created = datetime.strptime(event["created_at"], "%Y-%m-%dT%H:%M:%SZ")
        created = created.replace(tzinfo=timezone.utc)
        if created >= cutoff:
            total += event["payload"].get("size", 0)
    return total


def main():
    commits = count_recent_commits(fetch_events())
    food = min(100, commits * 10)

    if food >= 60:
        mood, msg, mouth = "happy", "Well fed! Keep coding!", HAPPY
    elif food >= 20:
        mood, msg, mouth = "okay", "A snack would be nice.", OKAY
    else:
        mood, msg, mouth = "hungry", "Feed me some commits!", HUNGRY

    svg = (TEMPLATE.replace("__MOUTH__", mouth)
                   .replace("__FOOD__", str(food))
                   .replace("__BAR__", str(int(food * 1.2)))
                   .replace("__MOOD__", mood)
                   .replace("__MSG__", msg))

    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(svg)

    print(f"Pet updated: {commits} commits this week, mood={mood}")


if __name__ == "__main__":
    main()
