#!/usr/bin/env python3
"""Launch the RevOps system for local use or stakeholder demos."""

from __future__ import annotations

import argparse
import os
import signal
import socket
import subprocess
import time
import webbrowser
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = REPO_ROOT / "logs" / "launcher"
DEFAULT_STREAMLIT_PORT = 8501
DEFAULT_AIRFLOW_PORT = 8080

_CHILDREN: list[tuple[str, subprocess.Popen[str], Any]] = []


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        choices=("demo", "full", "bootstrap-only"),
        default="demo",
        help=(
            "demo boots the system and opens the dashboard; full also starts Airflow; "
            "bootstrap-only runs checks and exits"
        ),
    )
    parser.add_argument(
        "--with-airflow",
        action="store_true",
        help="Start Airflow alongside the dashboard after bootstrap.",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Do not automatically open the browser after the dashboard is ready.",
    )
    parser.add_argument(
        "--streamlit-port",
        type=int,
        default=int(os.getenv("STREAMLIT_SERVER_PORT", str(DEFAULT_STREAMLIT_PORT))),
        help="Port for the Streamlit dashboard.",
    )
    parser.add_argument(
        "--airflow-port",
        type=int,
        default=int(os.getenv("AIRFLOW_WEB_PORT", str(DEFAULT_AIRFLOW_PORT))),
        help="Expected Airflow web port for readiness polling.",
    )
    return parser.parse_args()


def run_step(label: str, command: list[str]) -> None:
    print(f"[{label}] running: {' '.join(command)}")
    completed = subprocess.run(command, cwd=REPO_ROOT, check=False, text=True)
    if completed.returncode != 0:
        raise SystemExit(f"{label} failed with exit code {completed.returncode}")


def start_background(label: str, command: list[str], env: dict[str, str]) -> subprocess.Popen[str]:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / f"{label}.log"
    log_handle = log_path.open("a", encoding="utf-8")
    process = subprocess.Popen(
        command,
        cwd=REPO_ROOT,
        env=env,
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        text=True,
    )
    _CHILDREN.append((label, process, log_handle))
    print(f"[{label}] started (pid={process.pid}); log: {log_path}")
    return process


def wait_for_port(host: str, port: int, timeout_seconds: int = 90) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1.0)
            if sock.connect_ex((host, port)) == 0:
                return True
        time.sleep(1)
    return False


def stop_children() -> None:
    for label, process, log_handle in reversed(_CHILDREN):
        if process.poll() is None:
            print(f"[{label}] stopping")
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
        log_handle.close()


def signal_handler(_signum: int, _frame: object) -> None:
    stop_children()
    raise SystemExit(130)


def bootstrap() -> None:
    steps = [
        ["make", "preflight"],
        ["make", "init-warehouse"],
        ["make", "dbt-deps"],
        ["make", "quality-gate"],
        ["make", "refresh-caches"],
    ]
    for command in steps:
        run_step(command[1], command)


def main() -> int:
    args = parse_args()
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    bootstrap()
    if args.mode == "bootstrap-only":
        print("Bootstrap completed successfully.")
        return 0

    env = os.environ.copy()
    env.setdefault("STREAMLIT_SERVER_PORT", str(args.streamlit_port))

    streamlit_command = [
        "make",
        "streamlit-dev",
    ]
    start_background("streamlit", streamlit_command, env)

    if wait_for_port("127.0.0.1", args.streamlit_port, timeout_seconds=120):
        print(f"Streamlit is ready at http://127.0.0.1:{args.streamlit_port}")
        if not args.no_browser:
            webbrowser.open(f"http://127.0.0.1:{args.streamlit_port}")
    else:
        print(
            "Streamlit did not become ready on port "
            f"{args.streamlit_port}; check logs/launcher/streamlit.log"
        )

    include_airflow = args.mode == "full" or args.with_airflow
    if include_airflow:
        airflow_env = os.environ.copy()
        airflow_env.setdefault("AIRFLOW_HOME", str(REPO_ROOT / ".airflow"))
        airflow_command = ["make", "airflow-start"]
        start_background("airflow", airflow_command, airflow_env)
        if wait_for_port("127.0.0.1", args.airflow_port, timeout_seconds=120):
            print(f"Airflow is ready at http://127.0.0.1:{args.airflow_port}")
        else:
            print(
                "Airflow did not become ready on port "
                f"{args.airflow_port}; check logs/launcher/airflow.log"
            )

    print("RevOps system launched. Leave this process running to keep the services up.")

    try:
        while True:
            exited = [label for label, process, _ in _CHILDREN if process.poll() is not None]
            if exited:
                print(f"Child process exited: {', '.join(exited)}")
                break
            time.sleep(2)
    finally:
        stop_children()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
