from playwright.sync_api import sync_playwright
import json

with open("cookies.json", "r") as f:
    cookies = json.load(f)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()

    context.add_cookies(cookies)  # ⚠️ ça doit se faire AVANT l'ouverture de la page
    page = context.new_page()
    page.goto("https://sora.com")

    input("➡️ Vérifie que tu es connecté. Appuie sur Entrée pour sauvegarder la session...")
    context.storage_state(path="session.json")
    browser.close()
