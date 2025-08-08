import os
import re
import io
import requests
from bs4 import BeautifulSoup
from pdfminer.high_level import extract_text_to_fp
from pdfminer.layout import LAParams

INPUT_DIR = "copioni_pdf"
OUTPUT_DIR = "copioni_txt"

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



def estrai_pdf(percorso_pdf, output_path):
    print(f"[INFO] Estrazione testo da PDF: {percorso_pdf}")

    # Parametri di parsing pdfminer per mantenere una buona struttura
    laparams = LAParams(
        line_margin=0.1,
        char_margin=2.0,
        word_margin=0.1,
        boxes_flow=None
    )

    # Legge PDF ed estrae testo
    output_string = io.StringIO()
    with open(percorso_pdf, 'rb') as f:
        extract_text_to_fp(
            f,
            output_string,
            laparams=laparams,
            output_type='text',
            codec='utf-8'
        )

    testo = output_string.getvalue()

    # Salva il testo estratto in .txt
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(testo)

    print(f"[OK] Script PDF salvato in: {output_path}")

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

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # --- Estrazione da file siti.txt ---
    path_siti = "siti.txt"
    if os.path.exists(path_siti):
        with open(path_siti, 'r', encoding='utf-8') as f:
            urls = [riga.strip() for riga in f if riga.strip()]

        for url in urls:
            if "imsdb.com" in url:
                try:
                    nome_film = ricava_nome_film_da_url(url)
                    output_path = os.path.join(OUTPUT_DIR, f"{nome_film}.txt")
                    estrai_da_imsdb(url, output_path)
                except Exception as e:
                    print(f"[ERRORE] Impossibile estrarre da {url}: {e}")
            else:
                print(f"[AVVISO] URL non supportato: {url}")
    else:
        print(f"[ERRORE] File '{path_siti}' non trovato.")

    # --- Estrazione da PDF nella cartella ---
    for nome_file in os.listdir(INPUT_DIR):
        if nome_file.lower().endswith(".pdf"):
            nome_base = os.path.splitext(nome_file)[0]
            percorso_pdf = os.path.join(INPUT_DIR, nome_file)
            percorso_txt = os.path.join(OUTPUT_DIR, f"{nome_base}.txt")
            estrai_pdf(percorso_pdf, percorso_txt)


if __name__ == "__main__":
    main()