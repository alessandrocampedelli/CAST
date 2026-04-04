import os
import re
import io
import requests
from bs4 import BeautifulSoup
from pdfminer.high_level import extract_text_to_fp
from pdfminer.layout import LAParams
from huggingface_hub import hf_hub_download, list_repo_files

HF_REPO_ID = "campe03/CAST-screenplays"
HF_REPO_TYPE = "dataset"
INPUT_DIR = "input/pdf_scripts"
OUTPUT_DIR = "txt_scripts"


def download_from_huggingface():
    """Scarica PDF e sites.txt da Hugging Face se non già presenti in locale"""
    print("[INFO] Controllo file su Hugging Face...")

    os.makedirs(INPUT_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Scarica sites.txt
    sites_local = "input/sites.txt"
    if not os.path.exists(sites_local):
        print("[INFO] Scaricamento sites.txt da Hugging Face...")
        path = hf_hub_download(
            repo_id=HF_REPO_ID,
            repo_type=HF_REPO_TYPE,
            filename="sites.txt"
        )
        with open(path, "r") as src, open(sites_local, "w") as dst:
            dst.write(src.read())
        print("[OK] sites.txt scaricato")
    else:
        print("[SKIP] sites.txt già presente in locale")

    # Scarica tutti i PDF
    all_files = list_repo_files(HF_REPO_ID, repo_type=HF_REPO_TYPE)
    pdf_files = [f for f in all_files if f.startswith("pdf_scripts/") and f.endswith(".pdf")]

    for hf_path in pdf_files:
        filename = os.path.basename(hf_path)
        local_path = os.path.join(INPUT_DIR, filename)

        if not os.path.exists(local_path):
            print(f"[INFO] Scaricamento {filename} da Hugging Face...")
            downloaded = hf_hub_download(
                repo_id=HF_REPO_ID,
                repo_type=HF_REPO_TYPE,
                filename=hf_path
            )
            with open(downloaded, "rb") as src, open(local_path, "wb") as dst:
                dst.write(src.read())
            print(f"[OK] {filename} scaricato")
        else:
            print(f"[SKIP] {filename} già presente in locale")


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


def estrai_pdf(percorso_pdf, output_path):
    print(f"[INFO] Estrazione testo da PDF: {percorso_pdf}")

    laparams = LAParams(
        line_margin=0.1,
        char_margin=2.0,
        word_margin=0.1,
        boxes_flow=None
    )

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

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(testo)


def ricava_nome_film_da_url(url):
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
    # Fase 0: scarica da Hugging Face se necessario
    download_from_huggingface()

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Estrazione da sites.txt
    path_siti = "input/sites.txt"
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

    # Estrazione da PDF
    for nome_file in os.listdir(INPUT_DIR):
        if nome_file.lower().endswith(".pdf"):
            nome_base = os.path.splitext(nome_file)[0]
            percorso_pdf = os.path.join(INPUT_DIR, nome_file)
            percorso_txt = os.path.join(OUTPUT_DIR, f"{nome_base}.txt")
            estrai_pdf(percorso_pdf, percorso_txt)


if __name__ == "__main__":
    main()