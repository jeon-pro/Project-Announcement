"""
모든 사이트 스크래퍼를 실행하고 결과를 합쳐 data/projects.json 으로 저장한다.

실행:
    python scraper/main.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from common import save_merged  # noqa: E402
import wishket  # noqa: E402
import kmong  # noqa: E402
import wanted_gigs  # noqa: E402
import g2b  # noqa: E402

OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "projects.json")


def main():
    all_items = []

    scrapers = [
        ("wishket", wishket.fetch),
        ("kmong", kmong.fetch),
        ("wanted_gigs", wanted_gigs.fetch),
        ("g2b", g2b.fetch),
    ]

    for name, fn in scrapers:
        try:
            result = fn()
            print(f"[main] {name}: {len(result)}건 수집")
            all_items.extend(result)
        except Exception as e:
            print(f"[main] {name} 실행 중 오류: {e}")

    save_merged(all_items, os.path.abspath(OUT_PATH))


if __name__ == "__main__":
    main()
