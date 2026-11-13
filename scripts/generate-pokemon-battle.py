#!/usr/bin/env python3
import json
import os
import sys
import urllib.request
from datetime import datetime, timedelta, timezone


USERNAME = os.environ.get("GITHUB_USER_NAME", "harshita-8605")
TOKEN = os.environ.get("GITHUB_TOKEN")
OUTPUT = sys.argv[1] if len(sys.argv) > 1 else "pokemon-battle.svg"


def fetch_contributions():
    if not TOKEN:
        raise RuntimeError("GITHUB_TOKEN is required")
    today = datetime.now(timezone.utc).date()
    start = today - timedelta(days=364)
    query = """
    query($login: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $login) {
        contributionsCollection(from: $from, to: $to) {
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays { contributionCount contributionLevel }
            }
          }
        }
      }
    }
    """
    payload = json.dumps({
        "query": query,
        "variables": {
            "login": USERNAME,
            "from": f"{start.isoformat()}T00:00:00Z",
            "to": f"{today.isoformat()}T23:59:59Z",
        },
    }).encode()
    request = urllib.request.Request(
        "https://api.github.com/graphql",
        data=payload,
        headers={
            "Authorization": f"bearer {TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "github-profile-contribution-battle",
        },
    )
    with urllib.request.urlopen(request) as response:
        data = json.load(response)
    if data.get("errors"):
        raise RuntimeError(data["errors"][0].get("message", "GitHub API error"))
    calendar = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    return calendar["totalContributions"], [
        day for week in calendar["weeks"] for day in week["contributionDays"]
    ]


def esc(value):
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render(total, days, dark=False):
    bg = "#111827" if dark else "#f8fafc"
    panel = "#172033" if dark else "#ffffff"
    text = "#f8fafc" if dark else "#172033"
    muted = "#94a3b8" if dark else "#64748b"
    border = "#334155" if dark else "#e2e8f0"
    colors = ["#253047", "#c4b5fd", "#a78bfa", "#8b5cf6", "#6d28d9"] if dark else [
        "#ede9fe", "#ddd6fe", "#c4b5fd", "#8b5cf6", "#6d28d9"
    ]
    cells = []
    for index, day in enumerate(days[-371:]):
        column, row = divmod(index, 7)
        level = ["NONE", "FIRST_QUARTILE", "SECOND_QUARTILE", "THIRD_QUARTILE", "FOURTH_QUARTILE"].index(day["contributionLevel"])
        x, y = 44 + column * 13, 88 + row * 13
        cells.append(
            f'<rect x="{x}" y="{y}" width="9" height="9" rx="2" fill="{colors[level]}">'
            f'<title>{day["contributionCount"]} contributions</title></rect>'
        )
    grid_width = max(440, 44 + ((len(days[-371:]) + 6) // 7) * 13)
    beam_x = 44 + ((len(days[-371:]) - 1) // 7) * 13
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{grid_width}" height="210" viewBox="0 0 {grid_width} 210" role="img">
  <title>Pokémon-inspired contribution battle for {esc(USERNAME)}</title>
  <rect width="100%" height="100%" rx="18" fill="{bg}"/>
  <rect x="14" y="14" width="{grid_width - 28}" height="182" rx="14" fill="{panel}" stroke="{border}"/>
  <text x="34" y="43" fill="{text}" font-family="ui-sans-serif,system-ui,sans-serif" font-size="16" font-weight="700">⚡ CONTRIBUTION BATTLE</text>
  <text x="34" y="63" fill="{muted}" font-family="ui-sans-serif,system-ui,sans-serif" font-size="11">{esc(total)} contributions • trainer level {max(1, total // 25 + 1)}</text>
  <g>{''.join(cells)}</g>
  <g>
    <circle cx="{beam_x + 5}" cy="58" r="13" fill="#fbbf24">
      <animate attributeName="cy" values="58;64;58" dur="1.8s" repeatCount="indefinite"/>
    </circle>
    <circle cx="{beam_x + 5}" cy="58" r="6" fill="#fff7ed">
      <animate attributeName="cy" values="58;64;58" dur="1.8s" repeatCount="indefinite"/>
    </circle>
    <path d="M {beam_x - 8} 58 L {beam_x - 28} 51 L {beam_x - 28} 65 Z" fill="#f97316">
      <animate attributeName="opacity" values="1;.35;1" dur="1.8s" repeatCount="indefinite"/>
    </path>
  </g>
  <g transform="translate({max(75, beam_x - 48)} 151)">
    <circle cx="0" cy="0" r="18" fill="#7c3aed"/>
    <path d="M -10 -4 Q 0 -18 10 -4 Q 4 1 0 7 Q -4 1 -10 -4" fill="#fef3c7"/>
    <circle cx="-5" cy="-4" r="2.5" fill="#172033"/><circle cx="5" cy="-4" r="2.5" fill="#172033"/>
    <animateTransform attributeName="transform" type="translate" values="{max(75, beam_x - 48)} 151;{max(75, beam_x - 48)} 146;{max(75, beam_x - 48)} 151" dur="1.8s" repeatCount="indefinite"/>
  </g>
  <text x="34" y="181" fill="{muted}" font-family="ui-sans-serif,system-ui,sans-serif" font-size="10">Keep training • keep shipping • evolve every day</text>
</svg>"""


def main():
    total, days = fetch_contributions()
    with open(OUTPUT, "w", encoding="utf-8") as file:
        file.write(render(total, days, OUTPUT.endswith("-dark.svg")))


if __name__ == "__main__":
    main()
