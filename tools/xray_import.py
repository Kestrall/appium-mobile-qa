#!/usr/bin/env python3
"""Pousse le rapport JUnit vers Xray Cloud => une Test Execution dans Jira.

Les tests portant @pytest.mark.tc("MQA-xx") sont rattaches au Test Jira existant
(propriete JUnit test_key) ; les autres sont crees automatiquement par Xray.

Usage : python tools/xray_import.py reports/junit.xml --plan MQA-100 --version 2.3.0
"""
from __future__ import annotations

import argparse
import os
import sys

import requests
from dotenv import load_dotenv

XRAY = "https://xray.cloud.getxray.app/api/v2"


def authenticate() -> str:
    resp = requests.post(f"{XRAY}/authenticate", json={
        "client_id": os.environ["XRAY_CLIENT_ID"],
        "client_secret": os.environ["XRAY_CLIENT_SECRET"],
    }, timeout=30)
    resp.raise_for_status()
    return resp.json()


def main() -> int:
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument("junit")
    parser.add_argument("--plan", help="Cle du Test Plan Jira")
    parser.add_argument("--version", help="Fix version / build teste")
    parser.add_argument("--environment", help="ex. android-pixel7, iphone13")
    args = parser.parse_args()

    params = {"projectKey": os.getenv("XRAY_PROJECT_KEY", "MQA")}
    if args.plan:
        params["testPlanKey"] = args.plan
    if args.version:
        params["fixVersion"] = args.version
    if args.environment:
        params["testEnvironments"] = args.environment

    token = authenticate()
    with open(args.junit, "rb") as fh:
        resp = requests.post(
            f"{XRAY}/import/execution/junit",
            params=params,
            data=fh.read(),
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/xml"},
            timeout=60,
        )
    if not resp.ok:
        print(f"Echec import Xray ({resp.status_code}) : {resp.text}", file=sys.stderr)
        return 1
    print(f"Test Execution creee : {resp.json().get('key')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
