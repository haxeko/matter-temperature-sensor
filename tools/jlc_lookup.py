#!/usr/bin/env python3
"""Query the public JLCPCB parts search endpoint and print the fields a BOM needs.

Usage:
    tools/jlc_lookup.py C2848306 C14663          # exact LCSC/JLC codes
    tools/jlc_lookup.py -k "TPS63900"            # keyword search
    tools/jlc_lookup.py --json C2848306          # raw JSON lines (for reports)

The endpoint is the one used by jlcpcb.com/parts; it is not a documented API and
may change. Results are a snapshot: re-run before ordering.
"""
import argparse
import datetime as dt
import json
import sys
import urllib.request

URL = "https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList"


def query(keyword, page_size=10):
    body = json.dumps({"keyword": keyword, "currentPage": 1, "pageSize": page_size}).encode()
    req = urllib.request.Request(URL, data=body, headers={
        "Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=40) as r:
        data = json.load(r)
    info = (data.get("data") or {}).get("componentPageInfo") or {}
    return info.get("list") or []


def summarize(p):
    lib = p.get("componentLibraryType")
    if p.get("preferredComponentFlag"):
        lib = f"{lib}+preferred"
    prices = p.get("componentPrices") or []
    unit = prices[0]["productPrice"] if prices else None
    return {
        "code": p.get("componentCode"),
        "brand": p.get("componentBrandEn"),
        "mpn": p.get("componentModelEn"),
        "package": p.get("componentSpecificationEn"),
        "category": p.get("componentTypeEn"),
        "library": lib,
        "stock": p.get("stockCount"),
        "unit_price_usd": unit,
        "datasheet": p.get("dataManualUrl"),
        "description": p.get("describe") or p.get("erpComponentName"),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("terms", nargs="*")
    ap.add_argument("-k", "--keyword", action="append", default=[])
    ap.add_argument("-n", type=int, default=8, help="results per keyword search")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    rows = []
    for code in a.terms:
        hits = [h for h in query(code, 5) if h.get("componentCode") == code]
        rows += [summarize(h) for h in hits] or [{"code": code, "error": "not found"}]
    for kw in a.keyword:
        rows += [dict(summarize(h), query=kw) for h in query(kw, a.n)]
    for r in rows:
        r["queried"] = stamp
        if a.json:
            print(json.dumps(r, ensure_ascii=False))
        else:
            print(" | ".join(f"{k}={v}" for k, v in r.items() if k not in ("datasheet", "queried")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
