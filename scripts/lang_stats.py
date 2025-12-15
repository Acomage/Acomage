import os
import requests
from collections import defaultdict

import matplotlib.pyplot as plt

TOKEN = os.environ["GITHUB_TOKEN"]
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
}

API = "https://api.github.com"
USERNAME = "Acomage"   # ← 换成你的 GitHub 用户名
# =======================
# Repository filters
# =======================

EXCLUDE_REPOS = {
    "dotfiles",
    "Acomage",        # profile README repo
    "dotfiles-hyprland",
}

def should_skip_repo(name: str) -> bool:
    if name in EXCLUDE_REPOS:
        return True
   return False



def get_all_public_repos():
    repos = []
    page = 1
    while True:
        resp = requests.get(
            f"{API}/users/{USERNAME}/repos",
            headers=HEADERS,
            params={
                "per_page": 100,
                "page": page,
            },
        )

        resp.raise_for_status()
        batch = resp.json()
        if not batch:
            break
        repos.extend(batch)
        page += 1
    return repos


def get_repo_languages(owner, repo):
    resp = requests.get(
        f"{API}/repos/{owner}/{repo}/languages",
        headers=HEADERS,
    )
    resp.raise_for_status()
    return resp.json()
    
def render_svg(stats, output="language_stats.svg"):
    width = 500
    height = 40 + len(stats) * 32

    bar_x = 140
    bar_width = 280
    bar_height = 12

    svg = []
    svg.append(f"""
<svg width="{width}" height="{height}"
     viewBox="0 0 {width} {height}"
     xmlns="http://www.w3.org/2000/svg">

<style>
  .title {{
    font: bold 20px sans-serif;
    fill: #1f6feb;
  }}
  .label {{
    font: 14px sans-serif;
    fill: #24292f;
  }}
  .percent {{
    font: 13px monospace;
    fill: #57606a;
  }}
</style>

<rect x="0" y="0" width="{width}" height="{height}"
      rx="12" fill="#ffffff" stroke="#d0d7de"/>

<text x="20" y="30" class="title">My Programming Languages</text>
""")
    y = 55
    for lang, percent in stats.items():
        filled = bar_width * percent / 100

        svg.append(f"""
<text x="20" y="{y+10}" class="label">{lang}</text>

<rect x="{bar_x}" y="{y}" width="{bar_width}" height="{bar_height}"
      rx="6" fill="#eaeef2"/>

<rect x="{bar_x}" y="{y}" width="{filled}" height="{bar_height}"
      rx="6" fill="#2da44e"/>

<text x="{bar_x + bar_width + 10}" y="{y+10}"
      class="percent">{percent:.2f}%</text>
""")
        y += 32

    svg.append("</svg>")

    with open(output, "w", encoding="utf-8") as f:
        f.write("".join(svg))

def main():
    repos = get_all_public_repos()
    total = defaultdict(int)

    for repo in repos:
        name = repo["name"]
        if repo["fork"]:
            continue  # 忽略 fork
        if should_skip_repo(name):
            continue

        owner = repo["owner"]["login"]
        name = repo["name"]

        langs = get_repo_languages(owner, name)
        for lang, bytes_ in langs.items():
            total[lang] += bytes_

    if not total:
        print("No language data found.")
        return

    # 计算占比
    sum_bytes = sum(total.values())
    ratios = {
        lang: bytes_ / sum_bytes * 100
        for lang, bytes_ in total.items()
    }

    # 过滤过小的语言
    MIN_PERCENT = 1.0
    major = {k: v for k, v in ratios.items() if v >= MIN_PERCENT}
    other = sum(v for v in ratios.values() if v < MIN_PERCENT)

    if other > 0:
        major["Other"] = other

    labels = list(major.keys())
    values = list(major.values())

    # 绘图
    # 排序 + 取前 N
    stats = dict(
        sorted(ratios.items(), key=lambda x: -x[1])[:5]
    )

    render_svg(stats)

    print("language_stats.svg generated.")


if __name__ == "__main__":
    main()
