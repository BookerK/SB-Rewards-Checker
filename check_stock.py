from playwright.sync_api import sync_playwright
import json
import urllib.request
import os

URL = "https://www.starbucks.co.jp/mystarbucks/reward/exchange/original_goods/"
DISCORD_WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]

PRODUCTS = {
    "ブラウンマグ": "#item9",
    "グリーンマグ": "#item4",
}

def send_discord(message: str):
    data = {"content": message}
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0"
    }
    req = urllib.request.Request(
        DISCORD_WEBHOOK_URL,
        data=json.dumps(data).encode("utf-8"),
        headers=headers,
        method="POST"
    )
    with urllib.request.urlopen(req):
        pass

def check_stock(page, selector: str) -> bool:
    page.wait_for_function(
        """
        (selector) => {
            const el = document.querySelector(selector);
            if (!el) return false;

            return (
                el.querySelector('.js-cartform-instock:not(.hide)') ||
                el.querySelector('.js-cartform-outofstock:not(.hide)')
            );
        }
        """,
        arg=selector,
        timeout=15000
    )

    container = page.locator(selector)
    return container.locator(".js-cartform-instock:not(.hide)").count() > 0

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(URL, timeout=60000)

    results = {}

    for name, selector in PRODUCTS.items():
        results[name] = check_stock(page, selector)

    browser.close()

send_discord("🧪 GitHub Actions 動作確認テスト")

# Discordに送信
lines = []

for name, is_stock in results.items():
    if is_stock:
        lines.append(f"🎉 在庫復活！\n{name}\n{URL}")

if lines:
    send_discord("\n\n".join(lines))
