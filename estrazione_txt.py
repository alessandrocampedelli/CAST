import os
import re
import io
import requests
from bs4 import BeautifulSoup
from pdfminer.high_level import extract_text_to_fp
from pdfminer.layout import LAParams

#scarica e salva lo script dal sito www.springfieldspringfield.co.uk
def estrai_da_springfield(url, output_path):
    print(f"[INFO] Scaricamento HTML da: {url}")
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    #scarica la pagina e la analizza tramite la libreria BeatifulSoup identificando il div in cui è contenuto
    #il copione
    script_div = soup.find("div", class_="scrolling-script-container")
    if not script_div:
        raise ValueError("Tag <div class='scrolling-script-container'> non trovato nella pagina HTML.")

    #estraggo il testo
    testo = script_div.get_text(separator="\n", strip=True)

    #salvo il testo in un file txt
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(testo)

    print(f"[OK] Script HTML salvato in: {output_path}")


def estrai_da_imsdb(url, output_path):
    print(f"[INFO] Scaricamento da IMSDB: {url}")
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    pre_tag = soup.find('pre')
    if not pre_tag:
        raise ValueError("Tag <pre> non trovato nella pagina.")

    testo = pre_tag.get_text(separator="\n", strip=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(testo)

    print(f"[OK] Script IMSDB salvato in: {output_path}")



def estrai_e_pulisci_pdf(pdf_url, output_path):
    print(f"[INFO] Scaricamento PDF da: {pdf_url}")
    nome_pdf = "tmp_script.pdf"

    #scarisco il pdf a blocchi e lo salvo localmente in un file temporaneo
    with requests.get(pdf_url, stream=True) as r:
        r.raise_for_status()
        with open(nome_pdf, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

    #parametri di parsing per ottenere un testo più strutturato
    laparams = LAParams(
        line_margin=0.1,
        char_margin=2.0,
        word_margin=0.1,
        boxes_flow=None
    )

    #estrae il testo dal pdf con libreria pdfminer e lo scrivo in una stringa di output
    output_string = io.StringIO()
    with open(nome_pdf, 'rb') as f:
        extract_text_to_fp(
            f,
            output_string,
            laparams=laparams,
            output_type='text',
            codec='utf-8'
        )

    testo = output_string.getvalue()

    #elimino il pdf temporaneo
    os.remove(nome_pdf)

    # Pulizia direttamente sul testo estratto
    testo_pulito = pulisci_testo(testo)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(testo_pulito)

    print(f"[OK] Script PDF estratto e pulito salvato in: {output_path}")


def pulisci_testo(testo_raw):
    #divido il testo in righe
    righe = testo_raw.splitlines()

    #conterrà il testo finale formattato
    righe_pulite = []

    #tiene temporaneamente le battute associate a un personaggio
    buffer_dialogo = []
    personaggio_corrente = None

    for riga in righe:
        #rimuovo gli spazi a fine riga
        riga = riga.rstrip()

        #Se la riga è vuota e l’ultima riga pulita è già vuota, la ignora, salto così righe vuote doppie
        if riga.strip() == '' and (len(righe_pulite) == 0 or righe_pulite[-1] == ''):
            continue

        #salta righe composte solo da numeri
        if re.fullmatch(r'\d+', riga.strip()):
            continue

        #verifico se la riga è in maiuscolo e ha al massimo 3 parole: corrisponde al personaggio che parla
        if re.fullmatch(r"[A-Z\s]+", riga.strip()) and len(riga.strip().split()) <= 3:
            #se c'erano battute da personaggi precedenti le salvo
            if buffer_dialogo:
                righe_pulite.extend(buffer_dialogo)
                buffer_dialogo = []

            personaggio_corrente = riga.strip()
            centrato = personaggio_corrente.center(60)
            righe_pulite.append(centrato)
            continue

        #se c'è un personaggio attivo salvo le sue battute
        if personaggio_corrente:
            #Se trova una riga vuota → fine del blocco dialogo → salva tutto
            if riga.strip() == "":
                righe_pulite.extend(buffer_dialogo)
                buffer_dialogo = []
                personaggio_corrente = None
            #Se la riga ha testo → indenta e aggiunge alla lista di battute
            else:
                buffer_dialogo.append("    " + riga.strip())
            continue

        #Se la riga non è né un nome né un dialogo, la salva com'è (indicazione di scena)
        righe_pulite.append(riga.strip())

    if buffer_dialogo:
        righe_pulite.extend(buffer_dialogo)

    #ritorno testo pulito
    return '\n'.join(righe_pulite)

def ricava_nome_film_da_url(url):
    # Per scriptslug e springfield: prendi il valore dopo "movie=" o l'ultima parte del path
    if "springfieldspringfield" in url:
        match = re.search(r'movie=([^&]+)', url)
        return match.group(1).replace('-', '_') if match else "film"
    elif "scriptslug" in url:
        match = re.search(r'/([^/]+)\.pdf', url)
        return match.group(1).replace('-', '_') if match else "film"
    elif "imsdb" in url:
        match = re.search(r'/scripts/([^\.]+)\.html', url)
        return match.group(1).replace('-', '_') if match else "film"
    else:
        return "film"


if __name__ == "__main__":
    os.makedirs("copioni_txt", exist_ok=True)

    # Estrazione Cars (HTML - springfield)
    url_cars = "https://www.springfieldspringfield.co.uk/movie_script.php?movie=cars"
    nome_cars = ricava_nome_film_da_url(url_cars)
    estrai_da_springfield(url_cars, os.path.join("copioni_txt", f"{nome_cars}.txt"))

    # Estrazione + pulizia Rush (PDF)
    url_rush_pdf = "https://assets.scriptslug.com/live/pdf/scripts/rush-2013.pdf"
    nome_rush = ricava_nome_film_da_url(url_rush_pdf)
    estrai_e_pulisci_pdf(url_rush_pdf, os.path.join("copioni_txt", f"{nome_rush}.txt"))

    # Estrazione Cars 2 (HTML - IMSDB)
    url_cars2 = "https://imsdb.com/scripts/Cars-2.html"
    nome_cars2 = ricava_nome_film_da_url(url_cars2)
    estrai_da_imsdb(url_cars2, os.path.join("copioni_txt", f"{nome_cars2}.txt"))

