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
    """Rileva se una riga è un numero di scena (ora viene ignorato)"""
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
    """Rileva righe di intestazione e piè di pagina (titoli con date di revisione, copyright, ecc.)"""
    riga_clean = riga.strip()

    # Rimuove eventuali caratteri di escape e caratteri Unicode problematici
    riga_senza_escape = re.sub(r'^[\f\x0c]+', '', riga_clean)
    riga_senza_escape = re.sub(r'[^\x00-\x7F]+', ' ', riga_senza_escape)  # Rimuove caratteri non-ASCII

    # ---- PIEDI DI PAGINA (NUOVI PATTERN) ----

    # Pattern copyright generale: © o (C) o simboli Unicode copyright + anno + testo
    if re.search(r'(©|\(C\)|COPYRIGHT|�)\s*\d{4}', riga_senza_escape, re.IGNORECASE):
        return True

    # Pattern specifico Disney/Pixar/Studios: "DISNEY", "PIXAR", "CONFIDENTIAL", etc.
    footer_keywords = [
        'DISNEY', 'PIXAR', 'MARVEL', 'LUCASFILM', 'DREAMWORKS', 'WARNER', 'PARAMOUNT',
        'UNIVERSAL', 'SONY', 'FOX', 'MGM', 'LIONSGATE', 'A24', 'NETFLIX', 'AMAZON',
        'CONFIDENTIAL', 'PRIVILEGED', 'PROPRIETARY', 'RESTRICTED', 'INTERNAL USE',
        'DO NOT DISTRIBUTE', 'FOR YOUR CONSIDERATION', 'SCREENPLAY BY', 'WRITTEN BY',
        'ALL RIGHTS RESERVED', 'PROPERTY OF'
    ]

    riga_upper = riga_senza_escape.upper()
    for keyword in footer_keywords:
        if keyword in riga_upper and re.search(r'\d{4}', riga_senza_escape):  # Con anno
            return True

    # Pattern "CONFIDENTIAL" anche senza anno
    confidential_patterns = [
        'CONFIDENTIAL', 'PRIVILEGED', 'PROPRIETARY', 'RESTRICTED',
        'INTERNAL USE ONLY', 'DO NOT DISTRIBUTE', 'PRIVATE AND CONFIDENTIAL'
    ]
    for pattern in confidential_patterns:
        if pattern in riga_upper:
            return True

    # Pattern con simboli speciali tipici di footer (es: "• 2023 STUDIO •")
    if re.search(r'[•·▪▫■□●○◆◇★☆]+.*\d{4}.*[•·▪▫■□●○◆◇★☆]+', riga_senza_escape):
        return True

    # Pattern "Studio Name - Year" o "Year - Studio Name"
    if re.search(r'(^|\s)\d{4}\s*[-–—]\s*[A-Z]', riga_senza_escape) or \
            re.search(r'[A-Z]\s*[-–—]\s*\d{4}(\s|$)', riga_senza_escape):
        return True

    # Pattern con parentesi e anno: "(C) 2023" o "© 2023"
    if re.search(r'\([Cc©]\)\s*\d{4}', riga_senza_escape):
        return True

    # ---- INTESTAZIONI ORIGINALI ----

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

    # Date tra parentesi
    if re.search(
            r"\(\s*(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}\s*\)",
            riga_senza_escape, re.IGNORECASE):
        return True

    # Righe tutte maiuscole che sembrano titoli (escluse location)
    if (len(riga_senza_escape) > 20 and
            riga_senza_escape.isupper() and
            not riga_senza_escape.startswith("(") and
            not re.match(r"^(INT\.|EXT\.).+", riga_senza_escape)):
        # Evita di confondere con nomi di personaggi (max 4 parole)
        if len(riga_senza_escape.split()) > 4:
            return True

    # Titolo in maiuscolo + data sulla riga successiva
    if (riga_senza_escape.isupper() and len(riga_senza_escape.split()) > 1 and next_line):
        next_clean = next_line.strip()
        if re.search(
                r"\(\s*(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}\s*\)",
                next_clean, re.IGNORECASE):
            return True

    return False


def is_location_line(riga):
    """Rileva righe che rappresentano location di scena (INT., EXT., I/E., ecc.)
    QUESTA È ORA LA FUNZIONE CHIAVE PER IDENTIFICARE NUOVE SCENE"""

    # Pulizia più aggressiva della riga per rimuovere caratteri problematici
    riga_clean = riga.strip().replace("\xa0", " ").replace("\u00A0", " ")
    # Rimuove spazi multipli e normalizza
    riga_clean = re.sub(r'\s+', ' ', riga_clean).upper()

    # Debug: stampa la riga per vedere cosa stiamo analizzando
    print(f"[DEBUG] Analizzando location: '{riga_clean}' (lunghezza: {len(riga_clean)})")

    # Match iniziale con INT., EXT., I/E. o senza punto (INT, EXT, I/E)
    # Pattern più permissivo per gestire variazioni di spaziatura
    if re.match(r"^(INT\.?|EXT\.?|I/E\.?)\s+.+", riga_clean):
        print(f"[DEBUG] ✅ MATCH INT/EXT: '{riga_clean}'")
        return True

    # Verifica alternativa: inizia con INT o EXT seguito da spazio e altro testo
    if re.match(r"^(INT|EXT|I/E)\s+[A-Z]", riga_clean):
        print(f"[DEBUG] ✅ MATCH INT/EXT alternativo: '{riga_clean}'")
        return True

    # NUOVO: Pattern numero - descrizione - numero (es: "4   FULL SHOT - ENTERPRISE BRIDGE                                4")
    # Questo pattern inizia con numero, ha del testo nel mezzo e finisce con numero
    if re.match(r"^\d+\s+.+\s+\d+\s*$", riga_clean):
        print(f"[DEBUG] ✅ MATCH numero-desc-numero: '{riga_clean}'")
        return True

    # NUOVO: Pattern simile ma con numeri alfanumerici (es: "4A  CLOSE UP - SPOCK'S FACE  4A")
    if re.match(r"^(\d+[A-Za-z]*|[A-Za-z]*\d+)\s+.+\s+(\d+[A-Za-z]*|[A-Za-z]*\d+)\s*$", riga_clean):
        print(f"[DEBUG] ✅ MATCH alfanumerico: '{riga_clean}'")
        return True

    # NUOVO: Pattern con trattino centrale che indica shot/location (es: "FULL SHOT - ENTERPRISE BRIDGE")
    # Questo cattura righe che contengono pattern descrittivi cinematografici
    shot_keywords = [
        "FULL SHOT", "CLOSE UP", "MEDIUM SHOT", "WIDE SHOT", "EXTREME CLOSE UP",
        "ESTABLISHING SHOT", "MASTER SHOT", "TWO SHOT", "OVER THE SHOULDER",
        "POINT OF VIEW", "POV", "CUTAWAY", "INSERT"
    ]
    for keyword in shot_keywords:
        if keyword in riga_clean and "-" in riga_clean:
            print(f"[DEBUG] ✅ MATCH shot keyword '{keyword}': '{riga_clean}'")
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
            print(f"[DEBUG] ✅ MATCH location keyword '{keyword}': '{riga_clean}'")
            return True

    # Pattern: qualcosa seguito da "-" e un'indicazione temporale (es: DAY, NIGHT, CONTINUOUS, MOMENTS LATER)
    if re.match(r"^.+\s*[-–—]\s*(DAY|NIGHT|CONTINUOUS|MOMENTS LATER|SAME TIME|LATER|SAME)$", riga_clean):
        print(f"[DEBUG] ✅ MATCH temporale: '{riga_clean}'")
        return True

    print(f"[DEBUG] ❌ NO MATCH: '{riga_clean}'")
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

    # Pattern originali
    if (riga_upper == "(CONTINUED)" or
            riga_upper == "CONTINUED" or
            riga_upper == "CONTINUED:" or
            re.match(r"CONTINUED[:\s]*\(?\d+\)?", riga_upper) or
            re.match(r"\(CONTINUED[:\s]*\d+\)", riga_upper)):
        return True

    # NUOVO: Pattern numero-CONTINUED-numero (es: "2        CONTINUED:                                                            2")
    # Questo deve essere controllato PRIMA del pattern numero-descrizione-numero in is_location_line
    riga_clean = riga.strip().replace("\xa0", " ").replace("\u00A0", " ")
    riga_clean = re.sub(r'\s+', ' ', riga_clean).upper()

    # Pattern: numero + CONTINUED (con o senza :) + numero
    if re.match(r'^\d+[A-Za-z]*\s+CONTINUED:?\s+\d+[A-Za-z]*\s*$', riga_clean):
        print(f"[DEBUG] ✅ MATCH CONTINUED numero-desc-numero: '{riga_clean}'")
        return True

    # Pattern: solo CONTINUED con spazi e numeri intorno
    if re.match(r'^\d+[A-Za-z]*\s+CONTINUED:?\s*$', riga_clean) or \
            re.match(r'^\s*CONTINUED:?\s+\d+[A-Za-z]*\s*$', riga_clean):
        print(f"[DEBUG] ✅ MATCH CONTINUED con numeri: '{riga_clean}'")
        return True

    return False


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


def converti_in_tei(percorso_txt):
    with open(percorso_txt, 'r', encoding='utf-8') as f:
        righe = [r.strip() for r in f if r.strip()]

    print(f"[DEBUG] Totale righe lette: {len(righe)}")

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
    scene_counter = 1  # Contatore progressivo delle scene
    speaker_corrente = None
    ultimo_sp_element = None
    speech_in_continuazione = False
    i = 0

    while i < len(corpo_righe):
        riga = corpo_righe[i].strip()
        next_line = corpo_righe[i + 1].strip() if i + 1 < len(corpo_righe) else None

        # PRIORITÀ 1: Ignora righe CONTINUED (deve essere controllato PRIMA di is_location_line)
        # Questo previene che pattern come "2 CONTINUED: 2" vengano interpretati come nuove scene
        if is_continued_line(riga):
            print(f"[DEBUG] Saltata riga CONTINUED (incluso pattern numero-CONTINUED-numero): {riga}")
            i += 1
            continue

        # PRIORITÀ 2: RILEVA INIZIO NUOVA SCENA BASANDOSI SULLA LOCATION
        # Questo deve essere controllato DOPO CONTINUED ma PRIMA dei numeri di pagina
        if is_location_line(riga):
            # Verifica se è il pattern numero-descrizione-numero sulla stessa riga
            riga_clean = riga.strip().replace("\xa0", " ").replace("\u00A0", " ")
            riga_clean = re.sub(r'\s+', ' ', riga_clean)

            # Pattern: numero + descrizione + numero (es: "4   FULL SHOT - ENTERPRISE BRIDGE                                4")
            numero_desc_numero_match = re.match(r'^(\d+[A-Za-z]*)\s+(.+?)\s+(\d+[A-Za-z]*)$', riga_clean)

            if numero_desc_numero_match:
                # Estrae SOLO la descrizione, ignora il numero originale
                location_description = numero_desc_numero_match.group(2).strip()
                # Usa numerazione automatica
                numero_scena = str(scene_counter)

                print(f"[DEBUG] === NUOVA SCENA {numero_scena} (auto-generata da pattern numero-desc-numero) ===")
                print(f"[DEBUG] Location estratta: {location_description}")
                print(f"[DEBUG] Numero originale ignorato: {numero_desc_numero_match.group(1)}")

                # Crea la scena usando numerazione automatica
                scena_corrente = ET.SubElement(body, "div", type="scene")
                scena_corrente.set("n", numero_scena)

                # Aggiunge la location estratta
                ET.SubElement(scena_corrente, "stage", type="location").text = location_description

                # Reset dello speaker quando inizia nuova scena
                speaker_corrente = None
                ultimo_sp_element = None
                speech_in_continuazione = False

                # Incrementa il contatore delle scene
                scene_counter += 1

                print(f"[DEBUG] Scena {numero_scena} creata con location: {location_description}")
                i += 1
                continue
            else:
                # Location line normale (INT./EXT./etc.) - usa numerazione automatica
                numero_scena = str(scene_counter)
                location_line = riga

                print(f"[DEBUG] === NUOVA SCENA {numero_scena} (auto-generata) ===")
                print(f"[DEBUG] Location: {location_line}")

                # Crea la scena con numerazione automatica
                scena_corrente = ET.SubElement(body, "div", type="scene")
                scena_corrente.set("n", numero_scena)

                # Aggiunge la location
                ET.SubElement(scena_corrente, "stage", type="location").text = location_line

                # Reset dello speaker quando inizia nuova scena
                speaker_corrente = None
                ultimo_sp_element = None
                speech_in_continuazione = False

                # Incrementa il contatore delle scene
                scene_counter += 1

                print(f"[DEBUG] Scena {numero_scena} creata con location: {location_line}")
                i += 1
                continue

        # PRIORITÀ 3: Ignora numeri di pagina (SOLO se non sono location o continued)
        if is_page_number(riga):
            print(f"[DEBUG] Saltata pagina: {riga}")
            i += 1
            continue

        # Ignora numeri di scena (ora non servono più per identificare scene)
        if is_scene_number(riga):
            print(f"[DEBUG] Saltato numero scena (ora ignorato): {riga}")
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

        # RILEVA SPEAKER E BATTUTE
        if is_speaker(riga) and scena_corrente is not None:
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

                # Stop conditions - MODIFICATO: non più is_scene_number ma is_location_line
                if (is_speaker(next_riga) or is_location_line(next_riga) or
                        is_page_number(next_riga) or is_continued_line(next_riga) or
                        is_more_line(next_riga) or is_scene_number(next_riga)):
                    break

                # NUOVO: Controlla anche header/footer durante la raccolta battute
                if is_header_line(next_riga):
                    print(f"[DEBUG] Saltato piè di pagina durante raccolta battute: {next_riga}")
                    i += 1
                    continue

                # NUOVO: Controlla anche transizioni durante la raccolta battute
                if is_transition_line(next_riga):
                    print(f"[DEBUG] Saltata transizione durante raccolta battute: {next_riga}")
                    i += 1
                    continue

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

        # DESCRIZIONI SCENE (stage directions)
        if scena_corrente is not None and riga:
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