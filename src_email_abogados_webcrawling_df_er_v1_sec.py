import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
from time import time
import logging


def normalize_url(url):
    if isinstance(url, str):
        url = url.strip()
        if not url.startswith(("http://", "https://")):
            return "https://" + url
        return url
    return None

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

def limpiar_email(email):
    try:
        email = email.strip().lower()
        usuario, dominio = email.split('@', 1)

        # Eliminar guiones, puntos o números al inicio del usuario
        usuario = re.sub(r'^[-.\d_]+', '', usuario)

        # Recorta el dominio hasta .com si es necesario
        if ".com" in dominio:
            dominio = dominio[:dominio.index(".com") + 4]

        return f"{usuario}@{dominio}"
    except Exception:
        return email


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

    return list(set(emails_limpios))

def extract_emails_from_html(html):
    soup = BeautifulSoup(html, 'html.parser')
    text = soup.get_text()
    clean_text = clean_text_before_regex(text)

    text_emails = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", clean_text)

    mailto_emails = []
    for a in soup.find_all('a', href=True):
        href = a['href']
        if href.startswith("mailto:"):
            mail = href[7:].split('?')[0].strip()
            if "@" in mail:
                mailto_emails.append(mail)

    todos = list(set(text_emails + mailto_emails))
    return filtrar_emails_validos(todos)

def try_extract_emails(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=7)
        if response.status_code == 200:
            return extract_emails_from_html(response.text)
    except requests.exceptions.RequestException:
        return []
    return []

def extract_emails_from_all_routes(base_url):
    base_url = normalize_url(base_url)
    if not base_url:
        return []

    rutas = ["", "contact", "contacto", "contact-us", "contactenos"]
    for ruta in rutas:
        url_full = urljoin(base_url + "/", ruta)
        correos = try_extract_emails(url_full)
        if correos:
            return correos
    return []

# Operación en paralelo

def procesar_fila(row, columna_url):
    nombre = row.get('name_naics', 'empresa')
    website = row.get(columna_url, '')
    logging.info(f"Procesando {nombre} - {website}")
    correos = extract_emails_from_all_routes(website)
    return (row.name, correos)

def extraer_emails_desde_web(df, columna_url, max_threads=10):
    df = df.copy()
    resultados = [None] * len(df)

    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = [executor.submit(procesar_fila, row, columna_url) for _, row in df.iterrows()]
        for future in as_completed(futures):
            idx, emails = future.result()
            resultados[idx] = emails

    df['emails'] = resultados
    df['emails_todos'] = df['emails'].apply(lambda lst: '; '.join(lst) if lst else "")
    df['email_principal'] = df['emails'].apply(lambda lst: lst[0] if lst else None)
    return df.drop(columns=['emails'])

# V4
