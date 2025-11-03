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


def get_message_by_time(timezone_str='Europe/Lisbon'):
    try:
        tz = pytz.timezone(timezone_str)
    except pytz.UnknownTimeZoneError:
        print(f"⚠️ Fuso horário '{timezone_str}' inválido. Usando 'America/Sao_Paulo' como padrão.")
        tz = pytz.timezone('America/Sao_Paulo')

    current_time = datetime.now(tz)
    current_hour = current_time.strftime("%H:%M")
    print(f"🕓 Horário atual ({timezone_str}): {current_hour}")

    try:
        with open('messages/messages.txt', 'r', encoding='utf-8') as file:
            messages = file.readlines()
    except Exception as e:
        print(f"❌ Erro ao ler o arquivo de mensagens: {e}")
        return "Mensagem padrão, algo deu errado!"

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
                return message.strip('" ').strip()

        except ValueError:
            continue

    return "Mensagem padrão, horário não definido!"

driver_path = './chromedriver/chromedriver'
service = Service(driver_path)
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
options.add_argument("--user-data-dir=./chrome_data")  # mantém login
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

        auto_message = get_message_by_time()

        message_box.send_keys(auto_message)
        time.sleep(0.5)
        message_box.send_keys(Keys.RETURN)
        time.sleep(0.6)
        message_box.send_keys(f"🕓 Horário atual ({timezone_str}): {current_hour}")
        time.sleep(0.5)
        message_box.send_keys(Keys.RETURN)

        print(f"💬 Mensagem automática enviada para {contact_name}.")
    
    except Exception as e:
        print(f"❌ Erro ao enviar mensagem para {contact_name}: {str(e)}")

def monitor_new_messages():
    print("🟢 Monitorando novas mensagens... (Ctrl + C para parar)")
    last_replied = set()

    while True:
        try:
            unread_rows = driver.find_elements(
                By.XPATH,
                '//div[@id="pane-side"]//span[contains(@aria-label, "mensagem não lida")]/ancestor::div[@role="row"]'
            )

            if not unread_rows:
                time.sleep(5)
                continue

            for row in unread_rows:
                try:
                    contact_name_elem = row.find_element(By.XPATH, './/span[@title]')
                    contact_name = contact_name_elem.get_attribute("title")

                    if contact_name in last_replied:
                        continue

                    print(f"📩 Nova mensagem de: {contact_name}")
                    row.click()
                    time.sleep(1)
                    send_auto_reply(contact_name)
                    last_replied.add(contact_name)
                    time.sleep(3)

                except Exception as inner_e:
                    print(f"⚠️ Erro ao processar chat: {inner_e}")

            time.sleep(5)

        except Exception as e:
            print(f"❌ Erro no monitoramento: {e}")
            time.sleep(5)

monitor_new_messages()