import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime

INPUT_DIR = "copioni_txt"
OUTPUT_DIR = "copioni_tei"

def crea_header_tei(titolo):
    teiHeader = ET.Element("teiHeader")

    fileDesc = ET.SubElement(teiHeader, "fileDesc")
    titleStmt = ET.SubElement(fileDesc, "titleStmt")
    ET.SubElement(titleStmt, "title").text = titolo
    ET.SubElement(titleStmt, "author").text = "Unknown"

    publicationStmt = ET.SubElement(fileDesc, "publicationStmt")
    ET.SubElement(publicationStmt, "publisher").text = "Converted Script Archive"
    ET.SubElement(publicationStmt, "pubPlace").text = "Italy"
    ET.SubElement(publicationStmt, "date").text = datetime.today().strftime("%Y-%m-%d")

    sourceDesc = ET.SubElement(fileDesc, "sourceDesc")
    ET.SubElement(sourceDesc, "p").text = f"Derived from plain text file: {titolo}.txt"

    return teiHeader

def testo_to_tei_body(righe):
    body = ET.Element("text")
    div_scene = ET.SubElement(body, "body")
    scena = ET.SubElement(div_scene, "div", {"type": "scene"})

    current_sp = None

    for riga in righe:
        riga = riga.strip()
        if not riga:
            current_sp = None
            continue

        # Didascalia tra parentesi o frasi descrittive
        if re.match(r"^\[.*\]$", riga) or (riga.lower().startswith("int.") or riga.lower().startswith("ext.")):
            stage = ET.SubElement(scena, "stage")
            stage.text = riga
            continue

        # Nome personaggio in MAIUSCOLO, max 4 parole
        if riga.isupper() and len(riga.split()) <= 4:
            current_sp = ET.SubElement(scena, "sp")
            speaker = ET.SubElement(current_sp, "speaker")
            speaker.text = riga.title()
            continue

        # Se è battuta (dopo uno speaker attivo)
        if current_sp is not None:
            p = ET.SubElement(current_sp, "p")
            p.text = riga
        else:
            # Se non c'è speaker, ma è comunque testo, lo mettiamo come generico <p>
            p = ET.SubElement(scena, "p")
            p.text = riga

    return body

def converti_file_txt_in_tei(nome_file):
    path_input = os.path.join(INPUT_DIR, nome_file)
    nome_base = os.path.splitext(nome_file)[0]
    path_output = os.path.join(OUTPUT_DIR, f"{nome_base}.xml")

    with open(path_input, encoding="utf-8") as f:
        righe = f.readlines()

    tei = ET.Element("TEI", xmlns="http://www.tei-c.org/ns/1.0")
    tei.append(crea_header_tei(nome_base.title()))
    tei.append(testo_to_tei_body(righe))

    # Salvataggio XML
    ET.indent(tei)  # Python 3.9+
    tree = ET.ElementTree(tei)
    tree.write(path_output, encoding="utf-8", xml_declaration=True)

    print(f"[OK] Creato TEI XML: {path_output}")

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    for nome_file in os.listdir(INPUT_DIR):
        if nome_file.endswith(".txt"):
            converti_file_txt_in_tei(nome_file)

if __name__ == "__main__":
    main()
