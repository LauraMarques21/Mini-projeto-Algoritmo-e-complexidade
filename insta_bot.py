# insta_bot.py (corrigido para sempre extrair full_name e bio)
import json
import os
import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

PROFILE_TO_SCRAPE = "computacaounifavip_"
OUT_FILE = "bio.json"

def load_secrets():
    if os.path.exists("secrets.json"):
        with open("secrets.json", "r", encoding="utf-8") as f:
            d = json.load(f)
            return d.get("INSTAGRAM_USER"), d.get("INSTAGRAM_PASS")
    return os.environ.get("INSTAGRAM_USER"), os.environ.get("INSTAGRAM_PASS")

def make_driver(headless=False):
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1200,900")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def login_instagram(driver, username, password):
    driver.get("https://www.instagram.com/accounts/login/")
    w = WebDriverWait(driver, 15)
    user_inp = w.until(EC.presence_of_element_located((By.NAME, "username")))
    pass_inp = driver.find_element(By.NAME, "password")
    user_inp.send_keys(username)
    pass_inp.send_keys(password)
    driver.find_element(By.XPATH, "//button[@type='submit']").click()
    time.sleep(4)

def handle_save_info_and_notifications(driver):
    try:
        btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Agora não') or contains(text(),'Not Now')]"))
        )
        btn.click()
    except Exception:
        pass

def scrape_profile_bio(driver, profile):
    driver.get(f"https://www.instagram.com/{profile}/")
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    time.sleep(2)

    data = {"username": profile, "full_name": "", "bio": "", "external_url": ""}

    # ----- Método 1: tentar pegar pelo DOM -----
    try:
        data["full_name"] = driver.find_element(By.XPATH, "//header//h1").text.strip()
    except NoSuchElementException:
        pass
    try:
        data["bio"] = driver.find_element(By.XPATH, "//header//div[contains(@class,'-vDIg')]/span").text.strip()
    except NoSuchElementException:
        pass
    try:
        data["external_url"] = driver.find_element(By.XPATH, "//header//a[contains(@href,'http')]").get_attribute("href")
    except NoSuchElementException:
        pass

    # ----- Método 2: fallback - pegar do JSON embutido -----
    html = driver.page_source
    match = re.search(r'"biography":"(.*?)","blocked_by_viewer"', html)
    if match and not data["bio"]:
        data["bio"] = match.group(1).encode("utf-8").decode("unicode_escape")

    match = re.search(r'"full_name":"(.*?)","', html)
    if match and not data["full_name"]:
        data["full_name"] = match.group(1).encode("utf-8").decode("unicode_escape")

    return data

def save_json(data, filename=OUT_FILE):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def run():
    username, password = load_secrets()
    if not username or not password:
        raise RuntimeError("Credenciais não encontradas em variáveis de ambiente ou secrets.json")
    driver = make_driver(headless=False)  # mude para True se quiser headless
    try:
        login_instagram(driver, username, password)
        handle_save_info_and_notifications(driver)
        data = scrape_profile_bio(driver, PROFILE_TO_SCRAPE)
        save_json(data, OUT_FILE)
        print(f"[+] Bio salva em {OUT_FILE}")
        print(json.dumps(data, ensure_ascii=False, indent=2))
    finally:
        driver.quit()

if __name__ == "__main__":
    run()