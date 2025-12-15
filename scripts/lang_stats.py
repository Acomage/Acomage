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


def get_all_public_repos():
    repos = []
    page = 1
    while True:
        resp = requests.get(
            f"{API}/user/repos",
            headers=HEADERS,
            params={
                "visibility": "public",
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


def main():
    repos = get_all_public_repos()
    total = defaultdict(int)

    for repo in repos:
        if repo["fork"]:
            continue  # 忽略 fork

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
    plt.figure(figsize=(6, 6))
    plt.pie(
        values,
        labels=labels,
        autopct="%1.1f%%",
        startangle=90,
    )
    plt.title("Programming Language Usage")
    plt.tight_layout()
    plt.savefig("language_stats.svg", format="svg")
    plt.close()

    print("language_stats.svg generated.")


if __name__ == "__main__":
    main()
