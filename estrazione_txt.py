import os
import re
import io
import requests
from bs4 import BeautifulSoup
from pdfminer.high_level import extract_text_to_fp
from pdfminer.layout import LAParams

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



def estrai_pdf(pdf_url, output_path):
    print(f"[INFO] Scaricamento PDF da: {pdf_url}")
    nome_pdf = "tmp_script.pdf"

    #scarico il pdf a blocchi e lo salvo localmente in un file temporaneo per garantire compatibilità con pdfminer.
    #dal momento che la funzione extract_text_to_fp di pdfminer richiede un file-like object in modalità binaria (rb).
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

    #estrae il testo dal pdf tmp con libreria pdfminer e lo scrivo in una stringa di output
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

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(testo)

    print(f"[OK] Script PDF estratto e pulito salvato in: {output_path}")


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

    # Estrazione Rush (PDF)
    url_rush = "https://assets.scriptslug.com/live/pdf/scripts/rush-2013.pdf"
    nome_rush = ricava_nome_film_da_url(url_rush)
    estrai_pdf(url_rush, os.path.join("copioni_txt", f"{nome_rush}.txt"))

    # Estrazione Cars 2 (HTML - IMSDB)
    url_cars2 = "https://imsdb.com/scripts/Cars-2.html"
    nome_cars2 = ricava_nome_film_da_url(url_cars2)
    estrai_da_imsdb(url_cars2, os.path.join("copioni_txt", f"{nome_cars2}.txt"))

