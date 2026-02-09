import json
import os
import requests
from playwright.sync_api import sync_playwright

PRODUCT_URL = "https://www.starbucks.co.jp/mystarbucks/reward/exchange/original_goods/"
STATUS_FILE = "last_status.json"
DISCORD_WEBHOOK = os.environ["DISCORD_WEBHOOK_URL"]

# 👇 あなたが特定したクラスに置き換える
PRODUCTS = {
    "スターマグ ブラウン": ".class-for-brown-mug",
    "スターマグ グリーン": ".class-for-green-mug",
}


def get_current_status():
    results = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(PRODUCT_URL, timeout=60000)
        page.wait_for_timeout(3000)

        for name, selector in PRODUCTS.items():
            product = page.locator(selector)
            button_text = product.locator("button").inner_text().strip()

            if "交換に進む" in button_text:
                results[name] = "in_stock"
            elif "在庫切れ" in button_text:
                results[name] = "out_of_stock"
            else:
                results[name] = "unknown"

        browser.close()

    return results


def load_last_status():
    if not os.path.exists(STATUS_FILE):
        return {}
    with open(STATUS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_status(status):
    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump(status, f, ensure_ascii=False, indent=2)


def notify_discord(changes):
    lines = ["☕ スタバ在庫変化あり"]

    for name, (old, new) in changes.items():
        lines.append(f"- {name}: {old} → {new}")

    lines.append(PRODUCT_URL)

    requests.post(
        DISCORD_WEBHOOK,
        json={"content": "\n".join(lines)}
    )


def main():
    current = get_current_status()
    last = load_last_status()

    changes = {}
    for name, status in current.items():
        if last.get(name) != status:
            changes[name] = (last.get(name, "なし"), status)

    if changes:
        notify_discord(changes)

    save_status(current)


if __name__ == "__main__":
    main()
