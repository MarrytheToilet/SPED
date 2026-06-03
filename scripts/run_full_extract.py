#!/usr/bin/env python3
"""Run a full extraction job with a process lock.

This script is intended for long-running background jobs. It uses the webapp
service entry point so extraction behavior stays identical to the UI.
"""
from __future__ import annotations

import argparse
import fcntl
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import settings
from webapp import services


class ConsoleHandle:
    cancelled = False

    def log(self, message: str) -> None:
        print(message, flush=True)

    def set_progress(self, done: int, total: int) -> None:
        print(f"PROGRESS {done}/{total}", flush=True)

    def set_meta(self, **kwargs) -> None:
        print("META " + json.dumps(kwargs, ensure_ascii=False), flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run full schema extraction")
    parser.add_argument("--collection", required=True)
    parser.add_argument("--slug", required=True)
    args = parser.parse_args()

    collection = args.collection.strip()
    slug = args.slug.strip()
    if not collection or not slug:
        raise SystemExit("--collection and --slug are required")

    lock_dir = settings.STATE_DIR / "jobs"
    lock_dir.mkdir(parents=True, exist_ok=True)
    lock_path = lock_dir / f"extract.{collection}.{slug}.lock"
    with lock_path.open("w", encoding="utf-8") as lock_file:
        try:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print(f"另一个全量提取任务正在运行: {lock_path}", flush=True)
            return 2
        lock_file.write(str(Path.cwd()))
        lock_file.flush()

        papers = [p["paper_id"] for p in services.parsed_papers(collection)]
        print(
            f"START collection={collection} slug={slug} papers={len(papers)}",
            flush=True,
        )
        result = services.run_extract_job(ConsoleHandle(), slug, papers, collection)
        print("FINAL " + json.dumps(result, ensure_ascii=False), flush=True)
        return 0 if result.get("failed", 0) == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
