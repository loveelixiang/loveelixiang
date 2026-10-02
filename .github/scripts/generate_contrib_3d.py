import os
import json
import urllib.request
from datetime import datetime

USERNAME = os.environ.get("USERNAME", "loveelixiang")
TOKEN = os.environ["GITHUB_TOKEN"]

query = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            contributionCount
            date
            color
          }
        }
      }
    }
  }
}
"""

payload = json.dumps({
    "query": query,
    "variables": {"login": USERNAME}
}).encode("utf-8")

req = urllib.request.Request(
    "https://api.github.com/graphql",
    data=payload,
    headers={
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
        "User-Agent": "github-contrib-3d"
    }
)

with urllib.request.urlopen(req) as response:
    data = json.loads(response.read().decode("utf-8"))

calendar = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
weeks = calendar["weeks"]
total = calendar["totalContributions"]

# ---------------------------
# SVG layout
# ---------------------------

CELL = 14
GAP = 4
COLS = len(weeks)
ROWS = 7

LEFT = 40
TOP = 40

WIDTH = LEFT * 2 + COLS * (CELL + GAP)
HEIGHT = TOP * 2 + ROWS * (CELL + GAP) + 120

MAX_BAR_HEIGHT = 42

svg = []

svg.append(
    f'<svg xmlns="http://www.w3.org/2000/svg" '
    f'width="{WIDTH}" height="{HEIGHT}" '
    f'viewBox="0 0 {WIDTH} {HEIGHT}">'
)

svg.append("""
<style>
  .label {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    fill: #57606a;
    font-size: 14px;
  }

  .title {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    fill: #24292f;
    font-size: 20px;
    font-weight: 600;
  }
</style>
""")

# transparent background
svg.append('<rect width="100%" height="100%" fill="transparent"/>')

svg.append(
    f'<text x="{LEFT}" y="25" class="title">'
    f'{total} contributions in the last year'
    f'</text>'
)

# flatten values for scale
counts = []

for week in weeks:
    for day in week["contributionDays"]:
        counts.append(day["contributionCount"])

max_count = max(counts) if counts else 1
if max_count == 0:
    max_count = 1


def shade(count):
    if count == 0:
        return "#ebedf0"
    ratio = count / max_count

    if ratio <= 0.25:
        return "#9be9a8"
    elif ratio <= 0.5:
        return "#40c463"
    elif ratio <= 0.75:
        return "#30a14e"
    else:
        return "#216e39"


for col, week in enumerate(weeks):
    for row, day in enumerate(week["contributionDays"]):
        count = day["contributionCount"]

        x = LEFT + col * (CELL + GAP)
        y_base = TOP + row * (CELL + GAP)

        if count == 0:
            height = 2
        else:
            height = max(
                6,
                int((count / max_count) * MAX_BAR_HEIGHT)
            )

        color = shade(count)

        # shadow/base
        svg.append(
            f'<rect '
            f'x="{x}" '
            f'y="{y_base + MAX_BAR_HEIGHT}" '
            f'width="{CELL}" '
            f'height="{CELL}" '
            f'rx="2" '
            f'fill="#ebedf0"/>'
        )

        if count > 0:
            # vertical bar
            svg.append(
                f'<rect '
                f'x="{x}" '
                f'y="{y_base + MAX_BAR_HEIGHT - height}" '
                f'width="{CELL}" '
                f'height="{height + CELL}" '
                f'rx="2" '
                f'fill="{color}">'
                f'<title>{day["date"]}: {count} contributions</title>'
                f'</rect>'
            )

# weekday labels
labels = {
    1: "Mon",
    3: "Wed",
    5: "Fri"
}

for row, label in labels.items():
    y = TOP + row * (CELL + GAP) + MAX_BAR_HEIGHT + 12
    svg.append(
        f'<text x="0" y="{y}" class="label">{label}</text>'
    )

svg.append("</svg>")

os.makedirs("generated", exist_ok=True)

with open("generated/contribution-3d.svg", "w", encoding="utf-8") as f:
    f.write("\n".join(svg))

print("Generated generated/contribution-3d.svg")
