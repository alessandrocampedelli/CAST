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


def is_scene_number(riga):
    """Rileva se una riga è un numero di scena (solo cifre)"""
    return re.match(r"^\d+$", riga.strip())


def is_page_number(riga):
    """Rileva numeri di pagina in vari formati"""
    riga_clean = riga.strip()

    # Formato originale: \f seguito da numero
    if re.match(r"^\f\d+$", riga_clean):
        return True

    # Presenza del carattere di escape \f
    if '\f' in riga:
        return True

    # Numero seguito da punto (es. "2.")
    if re.match(r"^\d+\.$", riga_clean):
        return True

    # Intestazione pagina: testo seguito da spazi e numero con punto finale
    # Es: "ACU FINAL SHOOTING SCRIPT                          2."
    if re.match(r"^.+\s{10,}\d+\.$", riga_clean):
        return True

    # Intestazione pagina: testo seguito da spazi e numero senza punto
    # Es: "SCRIPT TITLE                                        15"
    if re.match(r"^.+\s{10,}\d+$", riga_clean):
        return True

    # Righe molto lunghe con molto spazio bianco (probabile header/footer)
    # Solo se terminano con numero o numero+punto
    if len(riga_clean) > 50 and re.search(r"\s{10,}\d+\.?$", riga_clean):
        return True

    return False


def is_transition_line(riga):
    """Rileva righe di transizione cinematografica da ignorare"""
    riga_upper = riga.strip().upper()

    # Lista delle transizioni comuni
    transizioni = [
        "CUT TO:",
        "CUT TO BLACK:",
        "FREEZE FRAME:",
        "RESUMING:",
        "THE END",
        "FADE TO BLACK",
        "FADE OUT",
        "MATCH FADE TO",
        "FADE IN:",
        "DISSOLVE TO:",
        "SMASH CUT TO:",
        "JUMP CUT TO:",
        "QUICK CUT TO:",
        "SLOW FADE TO:",
        "IRIS OUT",
        "IRIS IN",
        "WIPE TO:",
        "CROSSFADE TO:",
        "END FLASHBACK"
    ]

    # Verifica se la riga corrisponde esattamente a una transizione
    if riga_upper in transizioni:
        return True

    # Verifica pattern più generici
    # CUT TO qualcosa:
    if re.match(r"^CUT TO\b", riga_upper):
        return True

    # FADE TO qualcosa:
    if re.match(r"^FADE TO\b", riga_upper):
        return True

    # MATCH qualcosa TO:
    if re.match(r"^MATCH .+ TO:?$", riga_upper):
        return True

    return False


def is_header_line(riga):
    """Rileva righe di intestazione (titoli con date di revisione, etc.)"""
    riga_clean = riga.strip()

    # Intestazioni con date di revisione (es: "THE CHAMBER OF SECRETS - Rev. 1/28/02")
    if re.search(r"- Rev\. \d+/\d+/\d+", riga_clean):
        return True

    # Intestazioni con "Draft" (es: "SCRIPT TITLE - First Draft")
    if re.search(r"- (First|Second|Third|Final|Shooting) Draft", riga_clean, re.IGNORECASE):
        return True

    # Intestazioni con date generiche (es: "TITLE - January 2023")
    if re.search(r"- (January|February|March|April|May|June|July|August|September|October|November|December) \d{4}",
                 riga_clean, re.IGNORECASE):
        return True

    # Intestazioni molto lunghe (probabilmente titoli di film)
    # che non sono dialoghi o descrizioni scene
    if (len(riga_clean) > 20 and
            riga_clean.isupper() and
            not riga_clean.startswith("(") and
            not re.match(r"^(INT\.|EXT\.).+", riga_clean)):
        # Verifica che non sia uno speaker (max 4 parole per gli speaker)
        if len(riga_clean.split()) > 4:
            return True

    return False

def is_location_line(riga):
    """Rileva righe di location (INT./EXT.)"""
    return re.match(r"^(INT\.|EXT\.).+", riga.strip())


def is_speaker(riga):
    """Rileva speaker (tutto maiuscolo, max 4 parole, non inizia con parentesi)"""
    riga_clean = riga.strip().split("(")[0].strip()
    return (riga_clean.isupper() and
            len(riga_clean.split()) <= 4 and
            not riga.startswith("(") and
            riga_clean != "" and
            riga_clean not in ["CONTINUED", "CONTINUED:"])

def is_continued_line(riga):
    """Rileva righe CONTINUED in tutte le varianti comuni"""
    riga_upper = riga.strip().upper()
    return (
        riga_upper == "(CONTINUED)" or
        riga_upper == "CONTINUED" or
        riga_upper == "CONTINUED:" or
        re.match(r"CONTINUED[:\s]*\(?\d+\)?", riga_upper) or
        re.match(r"\(CONTINUED[:\s]*\d+\)", riga_upper)
    )

def converti_in_tei(percorso_txt):
    with open(percorso_txt, 'r', encoding='utf-8') as f:
        righe = [r.strip() for r in f if r.strip()]

    print(f"[DEBUG] Totale righe lette: {len(righe)}")

    # Parsing intestazione (prime 4 righe: titolo, "By", autore, data)
    titolo = righe[0] if len(righe) > 0 else "Unknown Title"
    autore = righe[2] if len(righe) >= 3 else "Unknown"
    data_raw = righe[3] if len(righe) >= 4 else None
    try:
        data = datetime.strptime(data_raw, "%B %dth, %Y").strftime("%Y-%m-%d")
    except:
        data = datetime.today().strftime("%Y-%m-%d")

    # Corpo del copione inizia dalla riga 4
    corpo_righe = righe[4:]
    print(f"[DEBUG] Corpo del copione: {len(corpo_righe)} righe")

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
    numeri_scene_gia_creati = set()  # Traccia i numeri di scena già processati
    speaker_corrente = None
    ultimo_sp_element = None
    speech_in_continuazione = False
    i = 0

    while i < len(corpo_righe):
        riga = corpo_righe[i].strip()

        # Ignora numeri di pagina (\f numero o simili)
        if is_page_number(riga):
            print(f"[DEBUG] Saltata pagina: {riga}")
            i += 1
            continue

        # Ignora righe CONTINUED (tutte le varianti)
        if is_continued_line(riga):
            print(f"[DEBUG] Saltata riga CONTINUED: {riga}")
            i += 1
            continue

        if is_transition_line(riga):
            print(f"[DEBUG] Saltata transizione: {riga}")
            i += 1
            continue

        # Ignora righe di transizione cinematografica
        if is_header_line(riga):
            print(f"[DEBUG] Saltata transizione: {riga}")
            i += 1
            continue

        # RILEVA INIZIO NUOVA SCENA
        if is_scene_number(riga):
            numero_scena = riga

            # Se abbiamo già creato una scena con questo numero, saltala
            if numero_scena in numeri_scene_gia_creati:
                print(f"[DEBUG] Scena {numero_scena} già creata, salto questo numero")
                i += 1
                continue

            print(f"[DEBUG] === NUOVA SCENA {numero_scena} ===")

            # Prossima riga dovrebbe essere la location (INT./EXT.)
            i += 1
            location_line = None

            if i < len(corpo_righe):
                possibile_location = corpo_righe[i].strip()

                # Salta eventuali numeri di pagina
                while i < len(corpo_righe) and is_page_number(possibile_location):
                    print(f"[DEBUG] Saltata pagina durante ricerca location: {possibile_location}")
                    i += 1
                    if i < len(corpo_righe):
                        possibile_location = corpo_righe[i].strip()

                if i < len(corpo_righe) and is_location_line(possibile_location):
                    location_line = possibile_location
                    print(f"[DEBUG] Location trovata: {location_line}")
                    i += 1  # Avanza dopo la location
                else:
                    print(f"[DEBUG] Nessuna location trovata, riga: '{possibile_location}'")

            # Salta il numero scena ripetuto dopo la location (se presente)
            while i < len(corpo_righe):
                next_riga = corpo_righe[i].strip()
                if is_page_number(next_riga):
                    print(f"[DEBUG] Saltata pagina: {next_riga}")
                    i += 1
                elif next_riga == numero_scena:
                    print(f"[DEBUG] Saltato numero scena ripetuto: {next_riga}")
                    i += 1
                    break  # Esci dal loop dopo aver trovato e saltato il numero ripetuto
                else:
                    break  # Non è un numero ripetuto, esci dal loop

            # Crea nuova scena
            scena_corrente = ET.SubElement(body, "div", type="scene")
            scena_corrente.set("n", numero_scena)
            numeri_scene_gia_creati.add(numero_scena)  # Segna come creata

            # Aggiungi location se trovata
            if location_line:
                ET.SubElement(scena_corrente, "stage", type="location").text = location_line

            print(f"[DEBUG] Scena {numero_scena} creata con location: {location_line}")
            continue

        # RILEVA SPEAKER E BATTUTE
        if is_speaker(riga) and scena_corrente is not None:
            speaker_name = riga.split("(")[0].strip()

            # Se stiamo continuando lo speech e lo speaker è lo stesso
            continua_speech = speech_in_continuazione and speaker_name == speaker_corrente and ultimo_sp_element is not None
            if continua_speech:
                print(f"[DEBUG] Continua speech per {speaker_name}")
            else:
                print(f"[DEBUG] Nuovo speaker trovato: {speaker_name}")

            print(f"[DEBUG] Speaker trovato: {speaker_name}")
            i += 1
            battute = []

            while i < len(corpo_righe):
                next_riga = corpo_righe[i].strip()

                if (is_speaker(next_riga) or
                        is_scene_number(next_riga) or
                        is_location_line(next_riga) or
                        is_page_number(next_riga) or
                        is_continued_line(next_riga.upper())):
                    break

                if next_riga:
                    battute.append(next_riga)

                i += 1

            # Verifica se l'ultima riga è (MORE) per tenere attivo il flag
            if battute and re.match(r"[(\[{]?\s*MORE\s*[)\]}]?$", battute[-1].strip().upper()):
                battute.pop()
                speech_in_continuazione = True
                print(f"[DEBUG] Trovato (MORE), speech in continuazione per {speaker_name}")
            else:
                speech_in_continuazione = False

            if battute:
                if continua_speech:
                    for battuta in battute:
                        ultimo_sp_element.append(crea_elemento_testo("p", battuta))
                    print(f"[DEBUG] Appese {len(battute)} battute a speech esistente di {speaker_name}")
                else:
                    sp = ET.SubElement(scena_corrente, "sp")
                    ET.SubElement(sp, "speaker").text = speaker_name
                    for battuta in battute:
                        sp.append(crea_elemento_testo("p", battuta))
                    ultimo_sp_element = sp
                    speaker_corrente = speaker_name
                    print(f"[DEBUG] Nuovo speech per {speaker_name} con {len(battute)} battute")

            #salto il resto del loop principale e ricomincia dall'inizio (senza incrementare i)
            continue

        # DESCRIZIONI SCENE (tutto il resto)
        if scena_corrente is not None and riga:
            ET.SubElement(scena_corrente, "stage").text = riga
            print(f"[DEBUG] Aggiunta descrizione: {riga[:50]}...")

        i += 1

    print(f"[DEBUG] Processamento completato. Scene create: {len(body.findall('.//div[@type=\"scene\"]'))}")

    # Indenta l'albero XML
    indent(root)

    # Scrittura XML
    tree = ET.ElementTree(root)
    nome_file = os.path.basename(percorso_txt).replace(".txt", ".xml")
    percorso_finale = os.path.join(OUTPUT_DIR, nome_file)
    tree.write(percorso_finale, encoding="utf-8", xml_declaration=True)
    print(f" File TEI salvato in: {percorso_finale}")


def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    for nome_file in os.listdir(INPUT_DIR):
        if nome_file.endswith(".txt"):
            print(f"\n Processando: {nome_file}")
            converti_in_tei(os.path.join(INPUT_DIR, nome_file))


if __name__ == "__main__":
    main()