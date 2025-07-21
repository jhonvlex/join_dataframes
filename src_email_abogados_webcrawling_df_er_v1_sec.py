import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
from time import sleep
import random

def extraer_emails_desde_web(df, columna_url):
    # --- Normaliza la URL ---
    def normalize_url(url):
        if isinstance(url, str) and not url.startswith(("http://", "https://")):
            return "https://" + url.strip()
        return url.strip() if isinstance(url, str) else None

    # --- Limpia texto antes de aplicar regex ---
    def clean_text_before_regex(text):
        if not isinstance(text, str):
            return ""
        text = re.sub(r"http\S+|www\.\S+", " ", text)
        text = re.sub(r"\b\d{7,}\b", " ", text)
        keywords = ["Instagram", "LinkedIn", "Twitter", "Inicio", "Servicios", "Legal",
                    "Mensajes", "Account", "Bookings", "My", "Phone", "Email", "MAIL",
                    "Contacto", "Horario", "Mon-Fri", "Facebook", "X", "WhatsApp"]
        pattern = r'\b(?:' + '|'.join(keywords) + r')\b'
        text = re.sub(pattern, " ", text, flags=re.IGNORECASE)
        text = re.sub(r'\b[A-Z]{3,}\b', " ", text)
        return re.sub(r'\s+', ' ', text).strip()

    # --- Corrección de emails encontrados ---
    def limpiar_email(email):
        # Eliminar números iniciales antes del @
        email = re.sub(r'^[0-9]+(?=[a-zA-Z_])', '', email)

        # Cortar cualquier cosa después de .com
        if ".com" in email:
            email = email[:email.index(".com") + 4]

        return email

    # --- Filtro para emails válidos ---
    def filtrar_emails_validos(lista):
        dominios_invalidos = ['godaddy.com', 'example.com']
        emails_limpios = []

        for mail in lista:
            if not mail or '@' not in mail:
                continue
            mail = limpiar_email(mail)
            dominio = mail.split('@')[-1].lower()
            if dominio in dominios_invalidos or len(mail) > 60:
                continue
            emails_limpios.append(mail)

        return list(set(emails_limpios))  # sin duplicados

    # --- Extraer correos desde HTML (texto y mailto) ---
    def extract_emails_from_html(html):
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text()
        clean_text = clean_text_before_regex(text)

        # Correos en texto plano
        text_emails = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", clean_text)

        # Correos en mailto:
        mailto_emails = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.startswith("mailto:"):
                mail = href[7:].split('?')[0].strip()
                if "@" in mail:
                    mailto_emails.append(mail)

        todos = list(set(text_emails + mailto_emails))
        return filtrar_emails_validos(todos)

    # --- Probar una URL concreta ---
    def try_extract_emails(url):
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=10)
            sleep(random.uniform(1, 3))
            if response.status_code != 200:
                return []
            return extract_emails_from_html(response.text)
        except requests.exceptions.RequestException:
            return []

    # --- Buscar en /contact y rutas comunes ---
    def extract_emails_from_all_routes(base_url):
        base_url = normalize_url(base_url)
        if not base_url:
            return []
        rutas = ["", "contact", "contacto", "contact-us", "contactenos"]
        for ruta in rutas:
            url_full = urljoin(base_url + "/", ruta)
            emails = try_extract_emails(url_full)
            if emails:
                return emails
        return []

    # --- Procesar cada fila del DataFrame ---
    emails_extraidos = []
    for i, row in df.iterrows():
        nombre = row.get('name_naics', f"fila {i}")
        website = row.get(columna_url, '')
        print(f"Procesando {nombre} - {website}")
        correos = extract_emails_from_all_routes(website)
        emails_extraidos.append(correos)

    # --- Agregar columnas al DataFrame ---
    df = df.copy()
    df['emails'] = emails_extraidos
    df['emails_todos'] = df['emails'].apply(lambda lst: '; '.join(lst) if lst else "")
    df['email_principal'] = df['emails'].apply(lambda lst: lst[0] if lst else None)

    # Opcional: puedes eliminar la columna 'emails' si solo quieres la versión string
    return df
