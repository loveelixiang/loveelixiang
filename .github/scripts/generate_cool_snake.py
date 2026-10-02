import os
import json
import math
import urllib.request
from datetime import datetime

USERNAME = os.getenv("USERNAME", "loveelixiang")
TOKEN = os.environ["GITHUB_TOKEN"]

QUERY = """
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
            weekday
          }
        }
      }
    }
  }
}
"""

payload = json.dumps({
    "query": QUERY,
    "variables": {"login": USERNAME}
}).encode("utf-8")

req = urllib.request.Request(
    "https://api.github.com/graphql",
    data=payload,
    headers={
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
        "User-Agent": "cool-snake-generator"
    }
)

with urllib.request.urlopen(req) as response:
    data = json.loads(response.read().decode("utf-8"))

calendar = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
weeks = calendar["weeks"]
total_contributions = calendar["totalContributions"]

# ====== layout ======
CELL = 18
GAP = 5
ROWS = 7
COLS = len(weeks)

MARGIN_X = 35
MARGIN_Y = 35

GRID_WIDTH = COLS * (CELL + GAP) - GAP
GRID_HEIGHT = ROWS * (CELL + GAP) - GAP

WIDTH = MARGIN_X * 2 + GRID_WIDTH
HEIGHT = MARGIN_Y * 2 + GRID_HEIGHT + 10

# ====== color helpers ======
def contribution_color(count, max_count):
    if count == 0:
        return "#ebedf0"
    ratio = count / max_count if max_count > 0 else 0
    if ratio <= 0.25:
        return "#9be9a8"
    elif ratio <= 0.5:
        return "#40c463"
    elif ratio <= 0.75:
        return "#30a14e"
    else:
        return "#216e39"

# flatten all cells
cells = []
counts = []

for c, week in enumerate(weeks):
    for r, day in enumerate(week["contributionDays"]):
        x = MARGIN_X + c * (CELL + GAP)
        y = MARGIN_Y + r * (CELL + GAP)
        count = day["contributionCount"]
        counts.append(count)
        cells.append({
            "col": c,
            "row": r,
            "x": x,
            "y": y,
            "cx": x + CELL / 2,
            "cy": y + CELL / 2,
            "count": count,
            "date": day["date"],
            "weekday": day["weekday"]
        })

max_count = max(counts) if counts else 1
active = [c for c in cells if c["count"] > 0]

# If there are too few active cells, use latest cells on right side as fallback
if len(active) < 5:
    fallback = sorted(cells, key=lambda x: x["date"])
    snake_cells = fallback[-8:]
else:
    active_sorted = sorted(active, key=lambda x: x["date"])
    snake_cells = active_sorted[-12:]  # length of the snake

points = [(c["cx"], c["cy"]) for c in snake_cells]

# ====== SVG helpers ======
def path_from_points(pts):
    if not pts:
        return ""
    if len(pts) == 1:
        x, y = pts[0]
        return f"M {x} {y}"

    d = f"M {pts[0][0]} {pts[0][1]} "
    for i in range(1, len(pts) - 1):
        x0, y0 = pts[i]
        x1, y1 = pts[i + 1]
        mx = (x0 + x1) / 2
        my = (y0 + y1) / 2
        d += f"Q {x0} {y0} {mx} {my} "
    d += f"T {pts[-1][0]} {pts[-1][1]}"
    return d

def rotate_point(px, py, cx, cy, angle_deg):
    angle = math.radians(angle_deg)
    dx = px - cx
    dy = py - cy
    rx = cx + dx * math.cos(angle) - dy * math.sin(angle)
    ry = cy + dx * math.sin(angle) + dy * math.cos(angle)
    return rx, ry

snake_path = path_from_points(points)

# head direction
if len(points) >= 2:
    hx, hy = points[-1]
    px, py = points[-2]
    angle = math.degrees(math.atan2(hy - py, hx - px))
else:
    hx, hy = points[-1]
    angle = 0

# head local anchor points before rotation
# head centered at hx, hy
head_points_local = [
    (hx + 16, hy),      # nose
    (hx + 8, hy - 10),
    (hx - 8, hy - 12),
    (hx - 14, hy),
    (hx - 8, hy + 12),
    (hx + 8, hy + 10),
]

head_points_rot = [rotate_point(x, y, hx, hy, angle) for x, y in head_points_local]
head_points_str = " ".join(f"{x:.2f},{y:.2f}" for x, y in head_points_rot)

# eyes
def head_offset(forward, side):
    rad = math.radians(angle)
    ux, uy = math.cos(rad), math.sin(rad)
    nx, ny = -uy, ux
    return hx + forward * ux + side * nx, hy + forward * uy + side * ny

eye1 = head_offset(4, -4)
eye2 = head_offset(4, 4)
pupil1 = head_offset(5, -4)
pupil2 = head_offset(5, 4)

# tongue
tongue_base = head_offset(16, 0)
tongue_tip_center = head_offset(24, 0)
tongue_tip_1 = head_offset(28, -4)
tongue_tip_2 = head_offset(28, 4)

# tail
tail_x, tail_y = points[0]

svg = []
svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">')

svg.append("""
<defs>
  <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
    <feDropShadow dx="0" dy="2" stdDeviation="2" flood-color="#000000" flood-opacity="0.22"/>
  </filter>
  <filter id="softShadow" x="-20%" y="-20%" width="140%" height="140%">
    <feDropShadow dx="0" dy="1.5" stdDeviation="1.5" flood-color="#000000" flood-opacity="0.12"/>
  </filter>
</defs>
""")

svg.append('<rect width="100%" height="100%" fill="transparent"/>')

# contribution grid
for cell in cells:
    fill = contribution_color(cell["count"], max_count)
    svg.append(
        f'<rect x="{cell["x"]}" y="{cell["y"]}" width="{CELL}" height="{CELL}" rx="4" fill="{fill}">'
        f'<title>{cell["date"]}: {cell["count"]} contributions</title>'
        f'</rect>'
    )

# snake body shadow
svg.append(
    f'<path d="{snake_path}" fill="none" stroke="#0e4429" stroke-width="18" '
    f'stroke-linecap="round" stroke-linejoin="round" opacity="0.18" filter="url(#softShadow)"/>'
)

# snake body main
svg.append(
    f'<path d="{snake_path}" fill="none" stroke="#1f883d" stroke-width="15" '
    f'stroke-linecap="round" stroke-linejoin="round" filter="url(#shadow)"/>'
)

# body highlight
svg.append(
    f'<path d="{snake_path}" fill="none" stroke="#3fb950" stroke-width="8" '
    f'stroke-linecap="round" stroke-linejoin="round" opacity="0.95"/>'
)

# some body spots
for i, (x, y) in enumerate(points[1:-1:2], start=1):
    svg.append(
        f'<circle cx="{x}" cy="{y}" r="2.2" fill="#b7e3b1" opacity="0.9"/>'
    )

# tail tip
svg.append(
    f'<circle cx="{tail_x}" cy="{tail_y}" r="4.2" fill="#2ea043" opacity="0.95"/>'
)

# head
svg.append(
    f'<polygon points="{head_points_str}" fill="#2ea043" filter="url(#shadow)"/>'
)

# head highlight
highlight1 = head_offset(2, -1.5)
svg.append(
    f'<ellipse cx="{highlight1[0]}" cy="{highlight1[1]}" rx="6" ry="3.2" '
    f'fill="#7ee787" opacity="0.65" transform="rotate({angle} {highlight1[0]} {highlight1[1]})"/>'
)

# eyes
for ex, ey in [eye1, eye2]:
    svg.append(f'<circle cx="{ex}" cy="{ey}" r="2.6" fill="white"/>')
for px, py in [pupil1, pupil2]:
    svg.append(f'<circle cx="{px}" cy="{py}" r="1.2" fill="#111"/>')

# tongue with simple animation
svg.append(
    f'''
    <g>
      <animate attributeName="opacity" values="1;0.25;1" dur="1.2s" repeatCount="indefinite"/>
      <path d="M {tongue_base[0]:.2f} {tongue_base[1]:.2f} L {tongue_tip_center[0]:.2f} {tongue_tip_center[1]:.2f}" 
            stroke="#e5484d" stroke-width="2.2" stroke-linecap="round"/>
      <path d="M {tongue_tip_center[0]:.2f} {tongue_tip_center[1]:.2f} L {tongue_tip_1[0]:.2f} {tongue_tip_1[1]:.2f}" 
            stroke="#e5484d" stroke-width="2" stroke-linecap="round"/>
      <path d="M {tongue_tip_center[0]:.2f} {tongue_tip_center[1]:.2f} L {tongue_tip_2[0]:.2f} {tongue_tip_2[1]:.2f}" 
            stroke="#e5484d" stroke-width="2" stroke-linecap="round"/>
    </g>
    '''
)

svg.append("</svg>")

os.makedirs("generated", exist_ok=True)
with open("generated/cool-snake.svg", "w", encoding="utf-8") as f:
    f.write("\n".join(svg))

print("Generated generated/cool-snake.svg")
