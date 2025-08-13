import os
import re
import string
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
    """Rileva se una riga è un numero di scena (cifre pure o alfanumerici come 11A, 11B, etc.)"""
    riga_clean = riga.strip()

    # Pattern originale: solo cifre
    if re.match(r"^\d+$", riga_clean):
        return True

    # Pattern numeri seguiti da lettere: 11A, 11B, 123C, etc.
    if re.match(r"^\d+[A-Za-z]{1,3}$", riga_clean):
        return True

    # Pattern lettere seguite da numeri: A1, B2, AA1, ABC123
    if re.match(r"^[A-Za-z]{1,3}\d+$", riga_clean):
        return True

    # Pattern con trattino: A-1, B-2, 11-A, etc.
    if re.match(r"^([A-Za-z]{1,3}-\d+|\d+-[A-Za-z]{1,3})$", riga_clean):
        return True

    return False


def parse_html_scene_line(riga):
    """
    Parsa una riga che contiene numero di scena + location in formato HTML
    Esempio: "1   EXT. CASTLE GROUNDS - NIGHT                                1"
    Ritorna: (numero_scena, location) o (None, None)
    """
    riga_clean = riga.strip()

    # Pattern per righe con numero scena + location + numero scena ripetuto
    # Esempio: "1   EXT. CASTLE GROUNDS - NIGHT                                1"
    match = re.match(r'^(\d+[A-Za-z]*)\s+(.*?)\s+\1\s*$', riga_clean)
    if match:
        numero_scena = match.group(1)
        location = match.group(2).strip()
        if is_location_line(location):
            return numero_scena, location

    # Pattern per righe con solo numero scena + location (senza ripetizione)
    # Esempio: "1   EXT. CASTLE GROUNDS - NIGHT"
    match = re.match(r'^(\d+[A-Za-z]*)\s+(.*?)$', riga_clean)
    if match:
        numero_scena = match.group(1)
        location = match.group(2).strip()
        if is_location_line(location):
            return numero_scena, location

    return None, None


def is_html_scene_line(riga):
    """Rileva se una riga è nel formato HTML con scena+location"""
    numero, location = parse_html_scene_line(riga)
    return numero is not None and location is not None


def is_page_number(riga):
    """Rileva numeri di pagina in vari formati, inclusi quelli alfanumerici"""
    riga_clean = riga.strip()

    # Formato originale: \f seguito da numero
    if re.match(r"^\f\d+$", riga_clean):
        return True

    # Formato alfanumerico con \f: \f11A, \f11B, \fA1, \fB2, etc.
    if re.match(r"^\f(\d+[A-Za-z]{1,3}|[A-Za-z]{1,3}\d+)$", riga_clean):
        return True

    # Presenza del carattere di escape \f
    if '\f' in riga:
        return True

    # Numero puro seguito da punto (es. "2.")
    if re.match(r"^\d+\.$", riga_clean):
        return True

    # Numeri alfanumerici seguiti da punto (es. "11A.", "B2.")
    if re.match(r"^(\d+[A-Za-z]{1,3}|[A-Za-z]{1,3}\d+)\.$", riga_clean):
        return True

    # Intestazione pagina: testo seguito da spazi e numero con punto finale
    # Es: "ACU FINAL SHOOTING SCRIPT                          2."
    if re.match(r"^.+\s{10,}\d+\.$", riga_clean):
        return True

    # Intestazione pagina con numero alfanumerico
    # Es: "ACU FINAL SHOOTING SCRIPT                          11A."
    if re.match(r"^.+\s{10,}(\d+[A-Za-z]{1,3}|[A-Za-z]{1,3}\d+)\.$", riga_clean):
        return True

    # Intestazione pagina: testo seguito da spazi e numero senza punto
    # Es: "SCRIPT TITLE                                        15"
    if re.match(r"^.+\s{10,}\d+$", riga_clean):
        return True

    # Intestazione pagina con numero alfanumerico senza punto
    # Es: "SCRIPT TITLE                                        11A"
    if re.match(r"^.+\s{10,}(\d+[A-Za-z]{1,3}|[A-Za-z]{1,3}\d+)$", riga_clean):
        return True

    # Righe molto lunghe con molto spazio bianco (probabile header/footer)
    # Solo se terminano con numero o numero+punto
    if len(riga_clean) > 50 and re.search(r"\s{10,}\d+\.?$", riga_clean):
        return True

    # Righe lunghe che terminano con numeri alfanumerici
    if len(riga_clean) > 50 and re.search(r"\s{10,}(\d+[A-Za-z]{1,3}|[A-Za-z]{1,3}\d+)\.?$", riga_clean):
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


def is_header_line(riga, next_line=None):
    """Rileva righe di intestazione (titoli con date di revisione, ecc.)"""
    riga_clean = riga.strip()

    # Rimuove eventuali caratteri di escape
    riga_senza_escape = re.sub(r'^[\f\x0c]+', '', riga_clean)

    # ---- 1) Pattern classici già presenti ----
    # Date di revisione tipo Rev. mm/dd/yyyy
    if re.search(r"- Rev\. \d{1,2}/\d{1,2}/\d{2,4}", riga_senza_escape):
        return True

    # Draft
    if re.search(r"- (First|Second|Third|Final|Shooting) Draft", riga_senza_escape, re.IGNORECASE):
        return True

    # Mese + anno
    if re.search(r"- (January|February|March|April|May|June|July|August|September|October|November|December) \d{4}",
                 riga_senza_escape, re.IGNORECASE):
        return True

    # ---- 2) Nuovo: date tra parentesi ----
    if re.search(
            r"\(\s*(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}\s*\)",
            riga_senza_escape, re.IGNORECASE):
        return True

    # ---- 3) Righe tutte maiuscole che sembrano titoli ----
    if (len(riga_senza_escape) > 20 and
            riga_senza_escape.isupper() and
            not riga_senza_escape.startswith("(") and
            not re.match(r"^(INT\.|EXT\.).+", riga_senza_escape)):
        # Evita di confondere con nomi di personaggi (max 4 parole)
        if len(riga_senza_escape.split()) > 4:
            return True

    # ---- 4) Nuovo: titolo in maiuscolo + data sulla riga successiva ----
    if (riga_senza_escape.isupper() and len(riga_senza_escape.split()) > 1 and next_line):
        next_clean = next_line.strip()
        if re.search(
                r"\(\s*(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}\s*\)",
                next_clean, re.IGNORECASE):
            return True

    return False


def is_location_line(riga):
    """Rileva righe che rappresentano location di scena (INT., EXT., I/E., ecc.)"""
    riga_clean = riga.strip().replace("\xa0", " ").upper()

    # Match iniziale con INT., EXT., I/E. o senza punto (INT, EXT, I/E)
    if re.match(r"^(INT\.?|EXT\.?|I/E\.?)\s+.+", riga_clean):
        return True

    # Contiene keyword tipiche di location
    location_keywords = [
        "ESTABLISHING SHOT",
        "LOCATION:",
        "SETTING:",
        "SCENE LOCATION:",
        "ESTABLISHING:",
        "SOMEPLACE",
        "SOMEWHERE",
        "VARIOUS LOCATIONS"
    ]
    for keyword in location_keywords:
        if keyword in riga_clean:
            return True

    # Pattern: qualcosa seguito da "-" e un'indicazione temporale (es: DAY, NIGHT, CONTINUOUS, MOMENTS LATER)
    if re.match(r"^.+\s*[-–—]\s*(DAY|NIGHT|CONTINUOUS|MOMENTS LATER|SAME TIME|LATER)$", riga_clean):
        return True

    return False


def is_speaker(riga):
    """Rileva righe che rappresentano uno speaker (personaggio che parla)"""
    if not riga.strip():
        return False

    riga_clean = riga.strip()
    base_name = riga_clean.split("(")[0].strip()

    # Ammessi: apostrofo, #, numeri e trattino
    allowed_chars = set("'#-0123456789")
    punctuation_check = "".join(ch for ch in string.punctuation if ch not in allowed_chars)

    # Esclude se contiene punteggiatura non ammessa
    if any(char in punctuation_check for char in base_name):
        return False

    # Esclude se è un numero di scena
    if is_scene_number(riga_clean):
        return False

    # Esclude CONTINUED scritto da solo
    if base_name in ["CONTINUED", "CONTINUED:"]:
        return False

    # Conta parole "non maiuscole" per permettere eccezioni tipo McGONAGALL, O'Neil, De Gaulle
    words = base_name.split()
    lowercase_tolerated = all(
        w.isupper() or re.match(r"^(Mc|O'|D[ae])", w) or w[0].isupper()
        for w in words
    )

    # Speaker tipico: tutto maiuscolo o quasi, poche parole
    if lowercase_tolerated and len(words) <= 4 and not riga_clean.startswith("("):
        return True

    # Speaker con CONT'D o CONTINUED in varie forme
    if re.match(r"^[A-Z0-9#\-\s]+(\s*\(CONT'?D\))\s*$", riga_clean):
        return True
    if re.match(r"^[A-Z0-9#\-\s]+(\s*\(CONTINUED\))\s*$", riga_clean):
        return True
    if re.match(r"^[A-Z0-9#\-\s]+\s*\([^)]*cont[^)]*\)\s*$", riga_clean, re.IGNORECASE):
        return True

    return False


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


def is_more_line(riga):
    """Rileva righe (MORE) che indicano continuazione su pagina successiva"""
    riga_upper = riga.strip().upper()
    return (
            riga_upper == "(MORE)" or
            riga_upper == "MORE" or
            re.match(r'^\s*\(?\s*MORE\s*\)?\s*$', riga_upper)
    )


def extract_speaker_name(speaker_line):
    """Estrae il nome pulito dello speaker"""
    # Rimuove (CONT'D), (contíd), e altre parentesi
    name = re.sub(r'\s*\([^)]*\)\s*$', '', speaker_line.strip())
    return name.strip()


def is_continuation_speaker(speaker_line):
    """Verifica se lo speaker indica continuazione"""
    return bool(re.search(r'\((CONT\'D|cont[íi]d)\)', speaker_line, re.IGNORECASE))


def extract_title_from_filename(filename):
    """Estrae il titolo del film dal nome del file, rimuovendo l'anno finale.
    Gestisce nomi con trattini, es. 'nome-del-film-2020.txt'"""

    # Rimuove l'estensione .txt
    name_without_ext = os.path.splitext(filename)[0]

    # Cerca l'anno alla fine del nome con trattini (es. 'nome-del-film-2020')
    match = re.search(r'^(.+)-(\d{4})$', name_without_ext)

    if match:
        title_slug = match.group(1)
        year = match.group(2)
        # Sostituisce i trattini con spazi per una forma leggibile
        title = title_slug.replace('-', ' ').strip()
        print(f"[DEBUG] Titolo estratto: '{title}', Anno: {year}")
        return title
    else:
        # Se non trova l'anno, restituisce comunque il nome "normalizzato"
        normalized_title = name_without_ext.replace('-', ' ').strip()
        print(f"[DEBUG] Anno non trovato, uso tutto il nome: '{normalized_title}'")
        return normalized_title


def detect_source_type(righe):
    """
    Rileva se il copione proviene da fonte HTML o PDF analizzando la struttura.
    Ritorna: 'html' o 'pdf'
    """
    html_indicators = 0
    pdf_indicators = 0

    for i, riga in enumerate(righe):
        # Indicatori formato HTML
        if is_html_scene_line(riga):
            html_indicators += 2

        # Indicatori formato PDF
        if is_scene_number(riga) and i + 1 < len(righe):
            next_riga = righe[i + 1].strip()
            if is_location_line(next_riga):
                pdf_indicators += 2

    print(f"[DEBUG] HTML indicators: {html_indicators}, PDF indicators: {pdf_indicators}")

    if html_indicators > pdf_indicators:
        return 'html'
    else:
        return 'pdf'


def converti_in_tei(percorso_txt):
    with open(percorso_txt, 'r', encoding='utf-8') as f:
        righe = [r.strip() for r in f if r.strip()]

    print(f"[DEBUG] Totale righe lette: {len(righe)}")

    # Rileva il tipo di sorgente
    source_type = detect_source_type(righe)
    print(f"[DEBUG] Tipo sorgente rilevato: {source_type}")

    # Estrae il titolo dal nome del file invece che dalla prima riga
    filename = os.path.basename(percorso_txt)
    titolo = extract_title_from_filename(filename)

    # Tutto il contenuto del file è il corpo del copione
    corpo_righe = righe
    print(f"[DEBUG] Corpo del copione: {len(corpo_righe)} righe")

    root = ET.Element("TEI", xmlns="http://www.tei-c.org/ns/1.0")

    # HEADER SEMPLIFICATO - solo il titolo
    teiHeader = ET.SubElement(root, "teiHeader")
    fileDesc = ET.SubElement(teiHeader, "fileDesc")
    titleStmt = ET.SubElement(fileDesc, "titleStmt")
    ET.SubElement(titleStmt, "title").text = titolo

    # CORPO TESTO
    text = ET.SubElement(root, "text")
    body = ET.SubElement(text, "body")

    scena_corrente = None
    numeri_scene_gia_creati = set()
    speaker_corrente = None
    ultimo_sp_element = None
    speech_in_continuazione = False
    scene_counter = 1  # Contatore per scene senza numero esplicito
    i = 0

    while i < len(corpo_righe):
        riga = corpo_righe[i].strip()
        next_line = corpo_righe[i + 1].strip() if i + 1 < len(corpo_righe) else None

        # Ignora numeri di pagina
        if is_page_number(riga):
            print(f"[DEBUG] Saltata pagina: {riga}")
            i += 1
            continue

        # Ignora righe CONTINUED
        if is_continued_line(riga):
            print(f"[DEBUG] Saltata riga CONTINUED: {riga}")
            i += 1
            continue

        # Ignora righe MORE (ma imposta flag di continuazione)
        if is_more_line(riga):
            print(f"[DEBUG] Saltata riga MORE: {riga}")
            speech_in_continuazione = True
            i += 1
            continue

        # Ignora transizioni
        if is_transition_line(riga):
            print(f"[DEBUG] Saltata transizione: {riga}")
            i += 1
            continue

        # Ignora intestazioni (header) - righe duplicate
        if is_header_line(riga, next_line):
            print(f"[DEBUG] Saltata intestazione duplicata: {riga}")
            i += 1
            continue

        # GESTIONE FORMATO HTML: scene+location sulla stessa riga
        if source_type == 'html' and is_html_scene_line(riga):
            numero_scena, location_line = parse_html_scene_line(riga)

            if numero_scena in numeri_scene_gia_creati:
                print(f"[DEBUG] Scena {numero_scena} già creata, salto")
                i += 1
                continue

            print(f"[DEBUG] === NUOVA SCENA HTML {numero_scena} ===")

            scena_corrente = ET.SubElement(body, "div", type="scene")
            scena_corrente.set("n", numero_scena)
            numeri_scene_gia_creati.add(numero_scena)

            if location_line:
                ET.SubElement(scena_corrente, "stage", type="location").text = location_line

            print(f"[DEBUG] Scena HTML {numero_scena} creata con location: {location_line}")
            i += 1
            continue

        # GESTIONE FORMATO PDF: RILEVA INIZIO NUOVA SCENA (numero separato)
        if source_type == 'pdf' and is_scene_number(riga):
            numero_scena = riga

            # Verifica se la scena è già stata creata
            if numero_scena in numeri_scene_gia_creati:
                print(f"[DEBUG] Scena {numero_scena} già creata, salto")
                i += 1
                continue

            print(f"[DEBUG] === NUOVA SCENA PDF {numero_scena} ===")

            # Prossima riga: location
            i += 1
            location_line = None

            # Salta eventuali numeri di pagina o ripetizioni
            while i < len(corpo_righe):
                possibile_location = corpo_righe[i].strip()

                if is_page_number(possibile_location):
                    print(f"[DEBUG] Saltata pagina durante ricerca location: {possibile_location}")
                    i += 1
                    continue
                elif possibile_location == numero_scena:
                    print(f"[DEBUG] Saltato numero scena ripetuto: {possibile_location}")
                    i += 1
                    continue
                elif is_continued_line(possibile_location):
                    print(f"[DEBUG] Saltata riga CONTINUED durante ricerca location: {possibile_location}")
                    i += 1
                    continue
                else:
                    break

            # Verifica se è una location
            if i < len(corpo_righe):
                possibile_location = corpo_righe[i].strip()
                if is_location_line(possibile_location):
                    location_line = possibile_location
                    print(f"[DEBUG] Location trovata: {location_line}")
                    i += 1
                else:
                    print(f"[DEBUG] Nessuna location trovata, riga: '{possibile_location}'")

            # Crea la scena
            scena_corrente = ET.SubElement(body, "div", type="scene")
            scena_corrente.set("n", numero_scena)
            numeri_scene_gia_creati.add(numero_scena)

            if location_line:
                ET.SubElement(scena_corrente, "stage", type="location").text = location_line

            print(f"[DEBUG] Scena PDF {numero_scena} creata con location: {location_line}")
            continue

        # GESTIONE LOCATION: ogni location inizia una nuova scena automatica
        if is_location_line(riga):
            numero_scena_auto = f"auto_{scene_counter}"
            print(f"[DEBUG] === NUOVA SCENA AUTOMATICA PER LOCATION {numero_scena_auto} ===")

            # Crea sempre una nuova scena quando si incontra una location
            scena_corrente = ET.SubElement(body, "div", type="scene")
            scena_corrente.set("n", numero_scena_auto)
            numeri_scene_gia_creati.add(numero_scena_auto)
            scene_counter += 1

            # Reset dei riferimenti al speaker precedente per la nuova scena
            speaker_corrente = None
            ultimo_sp_element = None
            speech_in_continuazione = False

            ET.SubElement(scena_corrente, "stage", type="location").text = riga
            print(f"[DEBUG] Scena automatica {numero_scena_auto} creata con location: {riga}")
            i += 1
            continue

        # RILEVA SPEAKER E BATTUTE
        if is_speaker(riga):
            # Se non c'è una scena corrente, creane una automatica
            if scena_corrente is None:
                numero_scena_auto = f"auto_{scene_counter}"
                print(f"[DEBUG] === CREAZIONE SCENA AUTOMATICA PER SPEAKER {numero_scena_auto} ===")

                scena_corrente = ET.SubElement(body, "div", type="scene")
                scena_corrente.set("n", numero_scena_auto)
                numeri_scene_gia_creati.add(numero_scena_auto)
                scene_counter += 1

            speaker_name = extract_speaker_name(riga)
            is_continuation = is_continuation_speaker(riga)

            # Determina se continuare la speech precedente
            continua_speech = (
                                      (speech_in_continuazione and speaker_name == speaker_corrente) or
                                      (is_continuation and speaker_name == speaker_corrente)
                              ) and ultimo_sp_element is not None

            if continua_speech:
                print(f"[DEBUG] Continua speech per {speaker_name} (continuation: {is_continuation})")
            else:
                print(f"[DEBUG] Nuovo speaker trovato: {speaker_name} (continuation: {is_continuation})")

            i += 1
            battute = []

            # Raccoglie le battute del personaggio
            while i < len(corpo_righe):
                next_riga = corpo_righe[i].strip()

                # Stop conditions
                if (is_speaker(next_riga) or is_scene_number(next_riga) or
                        is_location_line(next_riga) or is_page_number(next_riga) or
                        is_continued_line(next_riga) or is_more_line(next_riga) or
                        is_html_scene_line(next_riga)):
                    break

                if next_riga:
                    battute.append(next_riga)
                i += 1

            # Verifica se c'è (MORE) alla fine delle battute raccolte
            if battute and is_more_line(battute[-1]):
                battute.pop()
                speech_in_continuazione = True
                print(f"[DEBUG] Trovato (MORE) nelle battute, speech in continuazione per {speaker_name}")
            else:
                speech_in_continuazione = False

            # Aggiunge le battute
            if battute:
                if continua_speech:
                    # Continua la speech precedente
                    for battuta in battute:
                        ultimo_sp_element.append(crea_elemento_testo("p", battuta))
                    print(f"[DEBUG] Aggiunte {len(battute)} battute alla speech esistente")
                else:
                    # Crea nuova speech
                    sp = ET.SubElement(scena_corrente, "sp")
                    ET.SubElement(sp, "speaker").text = speaker_name
                    for battuta in battute:
                        sp.append(crea_elemento_testo("p", battuta))
                    ultimo_sp_element = sp
                    speaker_corrente = speaker_name
                    print(f"[DEBUG] Creata nuova speech con {len(battute)} battute")
            continue

        # DESCRIZIONI SCENE
        if riga:
            # Se non c'è una scena corrente, creane una automatica
            if scena_corrente is None:
                numero_scena_auto = f"auto_{scene_counter}"
                print(f"[DEBUG] === CREAZIONE SCENA AUTOMATICA PER DESCRIZIONE {numero_scena_auto} ===")

                scena_corrente = ET.SubElement(body, "div", type="scene")
                scena_corrente.set("n", numero_scena_auto)
                numeri_scene_gia_creati.add(numero_scena_auto)
                scene_counter += 1

            ET.SubElement(scena_corrente, "stage").text = riga
            print(f"[DEBUG] Aggiunta descrizione: {riga[:50]}...")

        i += 1

    print(f"[DEBUG] Processamento completato. Scene create: {len(body.findall('.//div[@type=\"scene\"]'))}")

    # Formattazione e salvataggio
    indent(root)
    tree = ET.ElementTree(root)
    nome_file = os.path.basename(percorso_txt).replace(".txt", ".xml")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    percorso_finale = os.path.join(OUTPUT_DIR, nome_file)
    tree.write(percorso_finale, encoding="utf-8", xml_declaration=True)
    print(f"File TEI salvato in: {percorso_finale}")


def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    for nome_file in os.listdir(INPUT_DIR):
        if nome_file.endswith(".txt"):
            print(f"\n Processando: {nome_file}")
            converti_in_tei(os.path.join(INPUT_DIR, nome_file))


if __name__ == "__main__":
    main()