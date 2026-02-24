#!/usr/bin/env python3
"""
add_prices.py — Equalization API で Monthly + Annual の175カ国価格を一括設定

使い方:
  python3 add_prices.py \
    --annual-sub  "6759388949" \
    --annual-pp   "eyJzIjoiNjc1OTM4ODk0OSIsInQiOiJVU0EiLCJwIjoiMTAxNzcifQ" \
    --monthly-sub "6759389150" \
    --monthly-pp  "eyJzIjoiNjc1OTM4OTE1MCIsInQiOiJVU0EiLCJwIjoiMTAwNjIifQ"

価格ポイント ID の取得方法:
  asc subscriptions price-points list \
    --subscription-id "<SUB_ID>" \
    --paginate 2>&1 | python3 -c "
import sys, json
d = json.load(sys.stdin)
for pp in d['data']:
    attrs = pp['attributes']
    if attrs.get('territory') == 'USA':
        print(pp['id'], attrs.get('customerPrice'), attrs.get('territory'))
"
"""

import subprocess
import json
import argparse
import sys


def run(cmd: list[str]) -> dict:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{result.stderr}")
    return json.loads(result.stdout)


def get_equalizations(price_point_id: str) -> list[str]:
    """US 価格ポイントから全175カ国の等価価格ポイント ID を取得"""
    data = run([
        "asc", "subscriptions", "price-points", "equalizations",
        "--id", price_point_id,
        "--paginate"
    ])
    return [item["id"] for item in data.get("data", [])]


def add_price(subscription_id: str, price_point_id: str) -> str:
    """1テリトリーに価格を追加。成功=ok, 既存=skip, エラー=fail"""
    result = subprocess.run(
        ["asc", "subscriptions", "prices", "add",
         "--subscription-id", subscription_id,
         "--price-point", price_point_id],
        capture_output=True, text=True
    )
    stdout = result.stdout.lower()
    stderr = result.stderr.lower()

    if result.returncode == 0:
        return "ok"
    if "already exists" in stdout or "already exists" in stderr:
        return "skip"
    if "duplicate" in stdout or "duplicate" in stderr:
        return "skip"
    print(f"  WARN: {result.stderr.strip()}", file=sys.stderr)
    return "fail"


def process_subscription(label: str, sub_id: str, us_pp_id: str):
    print(f"\n=== {label} ===")
    print(f"Subscription ID : {sub_id}")
    print(f"US Price Point  : {us_pp_id}")

    print("Fetching equalized price points...")
    eq_ids = get_equalizations(us_pp_id)
    print(f"Total equalized territories: {len(eq_ids)}")

    ok = skip = fail = 0
    for pp_id in eq_ids:
        status = add_price(sub_id, pp_id)
        if status == "ok":
            ok += 1
        elif status == "skip":
            skip += 1
        else:
            fail += 1

    print(f"DONE: ok:{ok}, skip:{skip}, fail:{fail}")
    if fail > 0:
        print(f"ERROR: {fail} territories failed. Check stderr above.", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Equalization API で Monthly + Annual の175カ国価格を一括設定"
    )
    parser.add_argument("--annual-sub",  required=True, help="Annual subscription ID")
    parser.add_argument("--annual-pp",   required=True, help="Annual US price point ID")
    parser.add_argument("--monthly-sub", required=True, help="Monthly subscription ID")
    parser.add_argument("--monthly-pp",  required=True, help="Monthly US price point ID")
    args = parser.parse_args()

    process_subscription("Annual",  args.annual_sub,  args.annual_pp)
    process_subscription("Monthly", args.monthly_sub, args.monthly_pp)

    print("\n✅ 全テリトリーへの価格設定が完了しました。")


if __name__ == "__main__":
    main()
