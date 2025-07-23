import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime

INPUT_DIR = "copioni_txt"
OUTPUT_DIR = "copioni_tei"

def indent(elem, level=0):
    i = "\n" + level * "  "  # due spazi per livello
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        for child in elem:
            indent(child, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

def crea_elemento_testo(tag, testo):
    elem = ET.Element(tag)
    elem.text = testo.strip()
    return elem

def converti_in_tei(percorso_txt):
    with open(percorso_txt, 'r', encoding='utf-8') as f:
        righe = [r.strip() for r in f if r.strip()]

    # Parsing intestazione (prime 3–4 righe)
    titolo = righe[0]
    autore = righe[2] if len(righe) >= 3 else "Unknown"
    data_raw = righe[3] if len(righe) >= 4 else None
    try:
        data = datetime.strptime(data_raw, "%B %dth, %Y").strftime("%Y-%m-%d")
    except:
        data = datetime.today().strftime("%Y-%m-%d")

    # Avanzamento righe dopo intestazione
    corpo_righe = righe[4:]

    root = ET.Element("TEI", xmlns="http://www.tei-c.org/ns/1.0")

    # HEADER
    teiHeader = ET.SubElement(root, "teiHeader")
    fileDesc = ET.SubElement(teiHeader, "fileDesc")

    titleStmt = ET.SubElement(fileDesc, "titleStmt")
    ET.SubElement(titleStmt, "title").text = titolo
    ET.SubElement(titleStmt, "author").text = autore

    publicationStmt = ET.SubElement(fileDesc, "publicationStmt")
    ET.SubElement(publicationStmt, "publisher").text = "Converted Script Archive"
    ET.SubElement(publicationStmt, "pubPlace").text = "Italy"
    ET.SubElement(publicationStmt, "date").text = data

    sourceDesc = ET.SubElement(fileDesc, "sourceDesc")
    ET.SubElement(sourceDesc, "p").text = f"Derived from plain text file: {os.path.basename(percorso_txt)}"

    # CORPO TESTO
    text = ET.SubElement(root, "text")
    body = ET.SubElement(text, "body")

    scena_corrente = None
    speaker_attivo = None
    in_continued = False

    i = 0
    while i < len(corpo_righe):
        riga = corpo_righe[i]

        # Ignora numeri di pagina (es: \f 2) o "(CONTINUED)"
        if re.match(r"^\f?\d+$", riga) or riga.upper() == "(CONTINUED)":
            i += 1
            continue

        # Rileva "CONTINUED:" e salta
        if riga.strip().upper() == "CONTINUED:":
            i += 1
            continue

        # Rileva inizio nuova scena tramite numero + INT./EXT.
        if re.match(r"^\d+$", riga):
            riga_succ = corpo_righe[i + 1] if i + 1 < len(corpo_righe) else ""
            if re.match(r"^(INT\.|EXT\.).+", riga_succ):
                scena_corrente = ET.SubElement(body, "div", type="scene")
                ET.SubElement(scena_corrente, "stage").text = riga_succ.strip()
                i += 2
                continue

        # Rileva descrizioni luogo
        if re.match(r"^(INT\.|EXT\.).+", riga):
            if scena_corrente is None:
                scena_corrente = ET.SubElement(body, "div", type="scene")
            ET.SubElement(scena_corrente, "stage").text = riga
            i += 1
            continue

        # Rileva speaker
        if riga.isupper() and len(riga.split()) <= 4 and not riga.startswith("("):
            speaker_attivo = riga.strip().split("(")[0].strip()
            i += 1
            battute = []
            # Raccoglie tutte le righe successive come battuta finché non cambia contesto
            while i < len(corpo_righe) and not corpo_righe[i].isupper() and not re.match(r"^\d+$", corpo_righe[i]):
                battute.append(corpo_righe[i])
                i += 1
            sp = ET.SubElement(scena_corrente, "sp")
            ET.SubElement(sp, "speaker").text = speaker_attivo
            for battuta in battute:
                sp.append(crea_elemento_testo("p", battuta))
            continue

        # Frasi giustificate = descrizione scena
        if scena_corrente is not None:
            ET.SubElement(scena_corrente, "stage").text = riga
        else:
            scena_corrente = ET.SubElement(body, "div", type="scene")
            ET.SubElement(scena_corrente, "stage").text = riga

        i += 1

    # Scrittura XML
    tree = ET.ElementTree(root)
    nome_file = os.path.basename(percorso_txt).replace(".txt", ".xml")
    percorso_finale = os.path.join(OUTPUT_DIR, nome_file)
    indent(root)
    tree.write(percorso_finale, encoding="utf-8", xml_declaration=True)
    print(f"✔️ File TEI salvato in: {percorso_finale}")

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    for nome_file in os.listdir(INPUT_DIR):
        if nome_file.endswith(".txt"):
            converti_in_tei(os.path.join(INPUT_DIR, nome_file))


if __name__ == "__main__":
    main()