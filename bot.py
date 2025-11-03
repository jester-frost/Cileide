import os
import time
from datetime import datetime
import pytz
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# -------------------
# CONFIGURAÇÕES GERAIS 'Europe/Lisbon'
# -------------------
TIMEZONE = 'America/Sao_Paulo'  # Fuso horário principal
single_search = 'mensagem não lida'
plural_search = 'mensagens não lidas'

def read_profiles():
    profiles = []
    try:
        with open('exceptions/profiles.txt', 'r', encoding='utf-8') as file:
            for line in file:
                name = line.strip()
                if name:
                    profiles.append(name.lower())
    except Exception as e:
        print(f"❌ Erro ao ler o arquivo de perfis: {e}")
    return profiles

def get_message_by_time(timezone_str=TIMEZONE):
    try:
        tz = pytz.timezone(timezone_str)
    except pytz.UnknownTimeZoneError:
        print(f"⚠️ Fuso horário '{timezone_str}' inválido. Usando '{TIMEZONE}' como padrão.")
        tz = pytz.timezone(TIMEZONE)

    current_time = datetime.now(tz)
    current_hour = current_time.strftime("%H:%M")

    try:
        with open('messages/messages.txt', 'r', encoding='utf-8') as file:
            messages = file.readlines()
    except Exception as e:
        print(f"❌ Erro ao ler o arquivo de mensagens: {e}")
        return "Mensagem padrão, algo deu errado!", current_hour

    for line in messages:
        line = line.strip()
        if not line:
            continue

        try:
            if '"' in line:
                time_range, message = line.split('"', 1)
            elif '“' in line or '”' in line:
                time_range, message = line.split('”', 1) if '”' in line else line.split('“', 1)
            else:
                continue

            start, end = time_range.split('-')
            start_time = datetime.strptime(start.strip(), "%H:%M").time()
            end_time = datetime.strptime(end.strip(), "%H:%M").time()
            now_time = current_time.time()

            if start_time <= now_time <= end_time:
                return message.strip('" ').strip(), current_hour

        except ValueError:
            continue

    return "Mensagem padrão, horário não definido!", current_hour

driver_path = './chromedriver/chromedriver'
service = Service(driver_path)
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
options.add_argument("--user-data-dir=./chrome_data")
driver = webdriver.Chrome(service=service, options=options)

driver.get('https://web.whatsapp.com')
print("🟡 Escaneie o QR Code para continuar...")

WebDriverWait(driver, 180).until(
    EC.presence_of_element_located((By.XPATH, '//div[@data-tab="3"]'))
)
print("✅ WhatsApp carregado com sucesso!")

def send_auto_reply(contact_name):
    try:
        profiles = read_profiles()
        normalized_contact = contact_name.lower().strip()

        if any(profile in normalized_contact for profile in profiles):
            print(f"🚫 Contato ou grupo '{contact_name}' está na lista de exceções. Ignorando.")
            return

        contact = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, f'//span[@title="{contact_name}"]'))
        )
        contact.click()
        time.sleep(1)

        message_box = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located(
                (By.XPATH, '//div[@contenteditable="true" and @data-tab="10"]')
            )
        )

        auto_message, current_hour = get_message_by_time(TIMEZONE)

        auto_message = auto_message.replace("%s%", current_hour)

        auto_message = auto_message.replace("%d%", TIMEZONE)

        message_box.send_keys(auto_message)
        time.sleep(0.5)
        message_box.send_keys(Keys.RETURN)

        print(f"💬 Mensagem automática enviada para {contact_name}.")

    except Exception as e:
        print(f"❌ Erro ao enviar mensagem para {contact_name}: {str(e)}")



def monitor_new_messages():
    print("🟢 Monitorando novas mensagens... (Ctrl + C para parar)")
    profiles = read_profiles()

    while True:
        try:
            unread_rows_single = driver.find_elements(
                By.XPATH,
                f'//div[@id="pane-side"]//span[contains(@aria-label, "{single_search}")]/ancestor::div[@role="row"]'
            )

            unread_rows_plural = driver.find_elements(
                By.XPATH,
                f'//div[@id="pane-side"]//span[contains(@aria-label, "{plural_search}")]/ancestor::div[@role="row"]'
            )

            unread_rows = unread_rows_single + unread_rows_plural

            if not unread_rows:
                time.sleep(5)
                continue

            unread_conversations = []

            for row in unread_rows:
                try:
                    contact_name_elem = row.find_element(By.XPATH, './/span[@title]')
                    contact_name = contact_name_elem.get_attribute("title")

                    if any(profile in contact_name.lower() for profile in profiles):
                        print(f"🚫 Contato ou grupo '{contact_name}' está na lista de exceções. Ignorando.")
                        continue

                    unread_conversations.append(contact_name)

                    print(f"📩 Nova mensagem de: {contact_name}")
                    row.click()

                    time.sleep(1)

                    send_auto_reply(contact_name)

                    time.sleep(3)

                except Exception as inner_e:
                    print(f"⚠️ Erro ao processar chat: {inner_e}")

            print(f"🔍 Conversas com mensagens não lidas: {unread_conversations}")

            time.sleep(5)

        except Exception as e:
            print(f"❌ Erro no monitoramento: {e}")
            time.sleep(5)


monitor_new_messages()
