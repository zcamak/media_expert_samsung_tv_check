#!/usr/bin/env python3
import argparse
import datetime as dt
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional, Tuple

DEFAULT_URL = (
    "https://www.mediaexpert.pl/telewizory-i-rtv/telewizory/"
    "telewizor-samsung-qe65qn92f-65-qd-mini-led-4k-120hz-tizen-tv-dolby-atmos-hdmi-2-1"
)
DEFAULT_HISTORY_PATH = ".tmp/price_history.json"
DEFAULT_TIMEOUT = 20
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def fetch_html(url: str, timeout: int, user_agent: str) -> str:
    headers = {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Referer": url,
    }
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        charset = resp.headers.get_content_charset() or "utf-8"
        return resp.read().decode(charset, errors="replace")


def _extract_json_ld_blocks(html: str) -> List[str]:
    pattern = re.compile(
        r"<script[^>]+type=\"application/ld\+json\"[^>]*>(.*?)</script>",
        re.IGNORECASE | re.DOTALL,
    )
    return [m.group(1).strip() for m in pattern.finditer(html)]


def _walk_json(obj: Any) -> List[Dict[str, Any]]:
    items = []
    if isinstance(obj, dict):
        items.append(obj)
        for v in obj.values():
            items.extend(_walk_json(v))
    elif isinstance(obj, list):
        for v in obj:
            items.extend(_walk_json(v))
    return items


def _extract_price_from_json_ld(html: str) -> Tuple[Optional[str], Optional[str]]:
    for block in _extract_json_ld_blocks(html):
        try:
            data = json.loads(block)
        except json.JSONDecodeError:
            continue

        for item in _walk_json(data):
            offers = item.get("offers")
            if not offers:
                continue
            if isinstance(offers, list):
                offers_list = offers
            else:
                offers_list = [offers]

            for offer in offers_list:
                if not isinstance(offer, dict):
                    continue
                price = offer.get("price") or offer.get("priceSpecification", {}).get("price")
                currency = offer.get("priceCurrency")
                if price:
                    return str(price), currency
    return None, None


def _extract_price_from_meta(html: str) -> Tuple[Optional[str], Optional[str]]:
    patterns = [
        r"itemprop=\"price\"\s+content=\"([^\"]+)\"",
        r"property=\"product:price:amount\"\s+content=\"([^\"]+)\"",
        r"name=\"twitter:data1\"\s+content=\"([^\"]+)\"",
    ]
    for pat in patterns:
        match = re.search(pat, html, re.IGNORECASE)
        if match:
            return match.group(1), None

    currency_match = re.search(
        r"itemprop=\"priceCurrency\"\s+content=\"([^\"]+)\"",
        html,
        re.IGNORECASE,
    )
    currency = currency_match.group(1) if currency_match else None
    return None, currency


def normalize_price(raw: str) -> str:
    cleaned = raw.replace("\xa0", " ").strip()
    cleaned = re.sub(r"[^0-9,\.]", "", cleaned)
    if "," in cleaned and "." not in cleaned:
        cleaned = cleaned.replace(" ", "").replace(",", ".")
    else:
        cleaned = cleaned.replace(" ", "")
    try:
        value = Decimal(cleaned)
    except InvalidOperation as exc:
        raise ValueError(f"Invalid price format: {raw}") from exc
    return f"{value:.2f}"


def detect_currency(raw: Optional[str], html: str) -> str:
    if raw:
        return raw
    if re.search(r"\bPLN\b|zl|z\u0142", html, re.IGNORECASE):
        return "PLN"
    return "PLN"


def load_history(path: str) -> List[Dict[str, str]]:
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_history(path: str, history: List[Dict[str, str]]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def send_telegram_message(token: str, chat_id: str, text: str, timeout: int) -> None:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = urllib.parse.urlencode({"chat_id": chat_id, "text": text}).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read().decode("utf-8", errors="replace")
        if resp.status >= 400:
            raise RuntimeError(f"Telegram API error {resp.status}: {body}")


def format_history(history: List[Dict[str, str]]) -> str:
    lines = []
    for entry in history:
        lines.append(f"{entry['date']}: {entry['price']} {entry['currency']}")
    return "\n".join(lines)


def load_env_file(path: str) -> None:
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip("\"").strip("'")
            os.environ.setdefault(key, value)


def main() -> int:
    parser = argparse.ArgumentParser(description="Daily price watcher")
    parser.add_argument("--url", default=DEFAULT_URL, help="Product URL")
    parser.add_argument(
        "--history",
        default=DEFAULT_HISTORY_PATH,
        help="History JSON path (default: .tmp/price_history.json)",
    )
    parser.add_argument("--force-notify", action="store_true", help="Send message even if unchanged")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help="HTTP timeout seconds")
    parser.add_argument("--user-agent", default=DEFAULT_USER_AGENT, help="HTTP User-Agent")
    args = parser.parse_args()

    load_env_file(".env")

    html = fetch_html(args.url, args.timeout, args.user_agent)
    price_raw, currency = _extract_price_from_json_ld(html)
    if not price_raw:
        price_raw, currency_meta = _extract_price_from_meta(html)
        currency = currency or currency_meta

    if not price_raw:
        raise RuntimeError("Could not find price in page HTML")

    price = normalize_price(price_raw)
    currency = detect_currency(currency, html)

    today = dt.date.today().isoformat()
    history = load_history(args.history)
    last = history[-1] if history else None

    changed = last is None or last["price"] != price
    if changed:
        history.append({"date": today, "price": price, "currency": currency})
        save_history(args.history, history)

    if not changed and not args.force_notify:
        print("Price unchanged; no notification sent.")
        return 0

    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        raise RuntimeError("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID")

    old_price = last["price"] if last else "N/A"
    message = (
        f"Price update\n"
        f"URL: {args.url}\n"
        f"Old price: {old_price} {currency}\n"
        f"New price: {price} {currency}\n\n"
        f"History:\n{format_history(history)}"
    )
    send_telegram_message(token, chat_id, message, args.timeout)
    print("Notification sent.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001 - handle for systemd retries
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
