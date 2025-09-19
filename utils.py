import os
import re
import string
import xml.etree.ElementTree as ET


def indent(elem, level=0):
    """Formatta l'XML con indentazione corretta"""
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
    """Crea un elemento XML con il testo specificato"""
    elem = ET.Element(tag)
    elem.text = testo.strip()
    return elem


def is_scene_number(riga):
    """Rileva se una riga è un numero di scena"""
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

    # 1. DATE SEMPLICI (mm/dd/yy, mm/dd/yyyy, dd/mm/yy, dd/mm/yyyy)
    if re.match(r'^\d{1,2}/\d{1,2}/\d{2,4}$', riga_senza_escape.strip()):
        return True

    # 2. PATTERN "TITOLO by AUTORE" (con eventuali dettagli dopo trattino)
    # Es: "CONCLAVE by Peter Straughan - Pink Revisions."
    if re.search(r'\b[A-Z][A-Z\s]+\s+by\s+[A-Z][A-Za-z\s]+', riga_senza_escape, re.IGNORECASE):
        return True

    # 3. REVISIONI E DRAFT - Pattern generali
    revision_patterns = [
        # Colori di revisione standard Hollywood
        r'\b(PINK|BLUE|YELLOW|GREEN|GOLDENROD|BUFF|SALMON|CHERRY|TAN|GREY|WHITE)\s+(REVISION|REVISIONS|DRAFT|PAGES?)\b',
        # Pattern "TITOLO REVISED/REVISION - DATA"
        r'\b[A-Z][A-Z\s]*\s+(REVISED?|REVISION)\s*[-–—]\s*\d{1,2}/\d{1,2}/\d{2,4}',
        # Pattern generico "qualcosa REVISED/REVISION"
        r'\b\w+\s+(REVISED?|REVISION)\b',
        # Draft con numeri ordinali
        r'\b(FIRST|SECOND|THIRD|FOURTH|FIFTH|FINAL|SHOOTING|PRODUCTION)\s+(DRAFT|REVISION)\b',
        # Pattern "Rev. X" o "Revision X"
        r'\b(Rev\.?|Revision)\s*[#]?\d+',
    ]

    riga_upper = riga_senza_escape.upper()
    for pattern in revision_patterns:
        if re.search(pattern, riga_upper):
            return True

    # 4. PATTERN TITOLO-DATA (trattino seguito da data)
    # Es: "SOMETHING - 01/10/23", "TITLE - January 2024"
    if re.search(r'.+\s*[-–—]\s*(\d{1,2}/\d{1,2}/\d{2,4}|[A-Z][a-z]+\s+\d{4})', riga_senza_escape):
        return True

    # 5. PATTERN CON PARENTESI E DATE
    # Es: "(January 15, 2024)", "(Rev. 3/15/23)"
    if re.search(r'\([^)]*(\d{1,2}/\d{1,2}/\d{2,4}|[A-Z][a-z]+\s+\d{1,2},?\s+\d{4}|Rev\.?\s*\d+)[^)]*\)',
                 riga_senza_escape, re.IGNORECASE):
        return True

    # PIEDI DI PAGINA (PATTERN ORIGINALI)

    # Pattern copyright generale: © o (C) o simboli Unicode copyright + anno + testo
    if re.search(r'(©|\(C\)|COPYRIGHT| )\s*\d{4}', riga_senza_escape, re.IGNORECASE):
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

    # 6. RIGHE CON SOLO LETTERE MAIUSCOLE E PUNTEGGIATURA (probabilmente titoli)
    # Ma esclude location e speaker
    if (len(riga_senza_escape) > 15 and
            re.match(r'^[A-Z\s\-\.,:;!?]+$', riga_senza_escape) and
            not re.match(r'^(INT\.|EXT\.|I/E\.).*', riga_senza_escape) and
            len(riga_senza_escape.split()) > 3 and
            '.' in riga_senza_escape):  # Contiene punto (tipico di titoli)
        return True

    # 7. PATTERN CON NUMERI DI VERSIONE
    # Es: "v1.2", "Version 3", "Draft 2.1"
    if re.search(r'\b(v|version|draft)\s*\d+(\.\d+)?\b', riga_senza_escape, re.IGNORECASE):
        return True

    return False


def is_location_line(riga):
    """Rileva righe che rappresentano location di scena (INT., EXT., I/E., EXT./INT., ecc.)"""

    # Rimuove spazi non-breaking e normalizza gli spazi
    riga_clean = riga.strip().replace("\xa0", " ").replace("\u00A0", " ")

    # Mantieni versione originale per alcuni controlli
    riga_original = riga_clean

    #Converte in maiuscolo per pattern matching case-insensitive
    riga_clean = re.sub(r'\s+', ' ', riga_clean).upper()

    # MATCH ALTA PRIORITÀ
    # 1. Standard cinematografici
    location_patterns = [
        r"^(INT\.?|EXT\.?|I/E\.?)\s+.+",  # Pattern originali
        r"^(EXT\.?/INT\.?|INT\.?/EXT\.?)\s+.+",  # EXT./INT. o INT./EXT.
        r"^(EXT\./INT\.|INT\./EXT\.)\s+.+",  # Con punti obbligatori
        r"^(EXT/INT|INT/EXT)\s+.+",  # Senza punti
        r"^(EXTERIOR/INTERIOR|INTERIOR/EXTERIOR)\s+.+",  # Forme complete
        r"^(EXT-INT|INT-EXT)\s+.+",  # Con trattino
        r"^(EXT\.?\s*-\s*INT\.?|INT\.?\s*-\s*EXT\.?)\s+.+",  # Con trattino e spazi
    ]

    for pattern in location_patterns:
        if re.match(pattern, riga_clean):
            return True

    # 2. Pattern numerati delle scene: numero - descrizione - numero
    if re.match(r"^(\d+[A-Za-z]*|[A-Za-z]*\d+)\s+.+\s+(\d+[A-Za-z]*|[A-Za-z]*\d+)\s*$", riga_clean):
        return True

    # 3. Pattern numero + spazio + location patterns
    number_location_patterns = [
        r"^\d+[A-Za-z]*\s+(INT\.?|EXT\.?|I/E\.?)\s+.+",
        r"^\d+[A-Za-z]*\s+(EXT\.?/INT\.?|INT\.?/EXT\.?)\s+.+",
        r"^\d+[A-Za-z]*\s+(EXT\./INT\.|INT\./EXT\.)\s+.+",
        r"^\d+[A-Za-z]*\s+(EXT/INT|INT/EXT)\s+.+",
        r"^\d+[A-Za-z]*\s+(EXT\.?\s*-\s*INT\.?|INT\.?\s*-\s*EXT\.?)\s+.+",
    ]

    for pattern in number_location_patterns:
        if re.match(pattern, riga_clean):
            return True

    # ESCLUSIONI IMMEDIATE - MEDIA PRIORITÀ
    # Esclude righe che sono chiaramente stage directions narrative
    narrative_indicators = [
        # Connettori narrativi
        r".*\.\s+(NO\s+RESPONSE|THIS\s+IS|HE\s+|SHE\s+|THEY\s+|IT\s+)",
        # Azioni in corso
        r".*(STARES?\s+UP|LOOKS?\s+DOWN|TURNS?\s+TO|WALKS?\s+TO)",
        # Descrizioni di oggetti specifici
        r".*LABEL.*:",  # "POV: the label - ..."
        r".*:\s+THE\s+LABEL",  # "POV: the label"
        # Pattern narrativi con punteggiatura specifica
        r".*\.\s+[A-Z][a-z]",  # Maiuscola seguita da minuscola dopo punto (prosa)
        # Frasi che continuano oltre la riga
        r".*[,;]\s*$",  # Termina con virgola o punto e virgola (continua)
        r".*\s+OF\s+",  # "a sea of dripping" (tipico di descrizioni)
    ]

    for pattern in narrative_indicators:
        if re.match(pattern, riga_clean):
            return False

    # Esclude POV che sono chiaramente descrizioni narrative
    if riga_clean.startswith("POV"):
        # Se contiene punteggiatura complessa o parole narrative, è stage direction
        if (re.search(r"[.,:;]\s+[A-Z]", riga_original) or  # Frasi multiple
                re.search(r"\b(no\s+response|this\s+is|going|stares?|looks?)\b", riga_clean) or
                len(riga_clean.split()) > 10 or  # Troppo lungo per essere header
                riga_clean.count("-") > 2):  # Troppi trattini (tipico di descrizioni)
            return False

    # CONTROLLI STRUTTURALI - MEDIA PRIORITÀ

    # Esclude righe che iniziano con articoli/possessivi (tipico di stage directions)
    if re.match(r"^(THE\s+|A\s+|AN\s+|\w+'S\s+|TWO\s+|THREE\s+|FOUR\s+|SEVERAL\s+)", riga_clean):
        return False

    # Esclude descrizioni di azioni specifiche
    action_patterns = [
        r".*\b(LEAN\s+ON|PLAYS?\s+ON|DRIPPING|UMBRELLAS)\b",
        r".*\b(WALKING|RUNNING|SITTING|STANDING|LOOKING)\b",
        r".*\b(HOLDS?|GRABS?|TAKES?|PUTS?|PLACES?)\b"
    ]

    for pattern in action_patterns:
        if re.match(pattern, riga_clean):
            return False

    # MATCH CONDIZIONALI - BASSA PRIORITÀ

    # Shot keywords SOLO se soddisfano criteri strutturali rigorosi
    shot_keywords = [
        "FULL SHOT", "CLOSE UP", "MEDIUM SHOT", "WIDE SHOT", "EXTREME CLOSE UP",
        "ESTABLISHING SHOT", "MASTER SHOT", "TWO SHOT", "OVER THE SHOULDER",
        "POINT OF VIEW", "POV", "CUTAWAY", "INSERT"
    ]

    for keyword in shot_keywords:
        if riga_clean.startswith(keyword):
            # Criteri aggiuntivi per shot keywords:
            # - Deve essere relativamente corto (< 80 caratteri)
            # - Non deve contenere punteggiatura complessa
            # - Non deve avere indicatori narrativi
            if (len(riga_clean) < 80 and
                    not re.search(r"[.,:;]\s+[A-Z]", riga_original) and  # No frasi multiple
                    not re.search(r"\b(no\s+response|this\s+is|going|stares?|looks?)\b", riga_clean) and
                    riga_clean.count(".") <= 1):  # Max un punto
                return True

    # Location keywords specifiche
    location_keywords = [
        "ESTABLISHING SHOT", "LOCATION:", "SETTING:", "SCENE LOCATION:",
        "ESTABLISHING:", "SOMEPLACE", "SOMEWHERE", "VARIOUS LOCATIONS"
    ]

    for keyword in location_keywords:
        if riga_clean.startswith(keyword):
            return True

    # Pattern temporale SOLO se strutturalmente appropriato
    temporal_match = re.match(r"^(.+)\s*[-–—]\s*(DAY|NIGHT|CONTINUOUS|MOMENTS LATER|SAME TIME|LATER|SAME)$", riga_clean)
    if (temporal_match and
            not re.match(r"^(THE\s+|A\s+|AN\s+|\w+'S\s+)", riga_clean) and
            len(temporal_match.group(1).split()) <= 6 and  # La parte prima del tempo non è troppo lunga
            not re.search(r"\b(LEAN|PLAY|DRIP|WALK|RUN|LOOK|STARE)\b", riga_clean)):  # No verbi di azione
        return True

    return False


def is_speaker(riga):
    """Rileva righe che rappresentano uno speaker (personaggio che parla)"""
    if not riga.strip():
        return False

    riga_clean = riga.strip()
    base_name = riga_clean.split("(")[0].strip()

    # Ammessi: apostrofo, #, numeri, trattino e punto (per titoli come MR., DR., etc.)
    allowed_chars = set("'#-0123456789.")
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

    # 1. Esclude se contiene virgole (tipico delle descrizioni narrative)
    if "," in riga_clean:
        return False

    # 2. MODIFICATO: Lista più specifica delle parole che escludono uno speaker
    # Rimuoviamo aggettivi comuni che possono essere parte di nomi di personaggi
    description_words = {
        # Manteniamo solo articoli, preposizioni e verbi che chiaramente indicano descrizioni
        "A", "AN", "THE", "IN", "ON", "AT", "OF", "FOR", "WITH", "BY", "FROM", "TO",
        # Verbi di azione che indicano descrizioni narrative
        "CONVALESCING", "SITTING", "STANDING", "WALKING", "RUNNING", "LYING", "MOVING",
        "STARING", "LOOKING", "HOLDING", "CARRYING", "WEARING"
    }
    # RIMOSSI: "LIVING", "DEAD", "OLD", "YOUNG", "SMALL", "BIG", "TALL", "SHORT", "FAT", "THIN"
    # perché possono essere parte legittima di nomi di personaggi

    # 3. Esclude se termina con punto ma non è un titolo (es. "Blake." non è speaker, ma "MR." sì)
    if riga_clean.endswith('.') and not re.match(r'^(MR|MRS|MS|DR|PROF|SIR|LADY)\.$', riga_clean.upper()):
        return False

    words_upper = [w.upper() for w in riga_clean.split()]

    # NUOVO: Controllo più intelligente per description_words
    # Esclude solo se la riga inizia con articoli/preposizioni O contiene verbi di azione
    starts_with_article = any(words_upper[0] == word for word in ["A", "AN", "THE"] if words_upper)
    contains_action_verb = any(word in description_words for word in words_upper)

    if starts_with_article or contains_action_verb:
        return False

    # 4. Esclude se la riga è troppo lunga per essere uno speaker (probabilmente descrizione)
    if len(riga_clean) > 60:  # AUMENTATO da 50 a 60 per permettere nomi più lunghi
        return False

    # 5. MODIFICATO: Gestione migliorata per descrizioni con età
    if re.search(r'\(\d+\)', riga_clean):
        # Verifica se dopo i numeri c'è altro testo (segno di descrizione)
        parentheses_content = re.search(r'\(([^)]+)\)', riga_clean)
        if parentheses_content and not re.match(r'^\d+$', parentheses_content.group(1)):
            return False
        # Se c'è testo dopo le parentesi con età, è una descrizione
        if re.search(r'\(\d+\).+', riga_clean):
            return False

    # 6. NUOVO: Controllo specifico per pattern di speaker descrittivi
    # Permette pattern come "AGGETTIVO NOME" tipici degli screenplay
    words = base_name.split()

    # Pattern comuni per speaker descrittivi negli screenplay
    descriptive_patterns = [
        # Aggettivo + Nome: "BIG JOHN", "OLD MARY", "YOUNG PETER"
        r'^(BIG|SMALL|OLD|YOUNG|TALL|SHORT|FAT|THIN|LITTLE|LARGE)\s+[A-Z]+$',
        # Professione/Ruolo + Nome/Numero: "COP #1", "DOCTOR SMITH", "WAITER"
        r'^(COP|DOCTOR|NURSE|WAITER|GUARD|SOLDIER|OFFICER|DETECTIVE|LAWYER)\s*(#?\d+|[A-Z]+)?$',
        # Titolo + Aggettivo + Nome: "MR. BIG", "DR. YOUNG"
        r'^(MR|MRS|MS|DR|PROF)\.\s+(BIG|SMALL|OLD|YOUNG|TALL|SHORT)\s*[A-Z]*$'
    ]

    # Se corrisponde a un pattern descrittivo, è probabilmente uno speaker
    for pattern in descriptive_patterns:
        if re.match(pattern, base_name.upper()):
            return True

    # Conta parole "non maiuscole" per permettere eccezioni
    lowercase_tolerated = True
    for w in words:
        # Pattern speciali ammessi:
        # - Tutto maiuscolo (normale)
        # - Prefissi come Mc, O', De (per nomi stranieri)
        # - Prima lettera maiuscola (per casi misti)
        # - Solo # seguito da numeri (per speaker numerati)
        # - Solo numeri (per speaker numerati)
        if not (w.isupper() or
                re.match(r"^(Mc|O'|D[ae])", w) or
                w[0].isupper() or
                re.match(r"^#\d+$", w) or  # Pattern #1, #2, etc.
                w.isdigit()):  # Numeri semplici
            lowercase_tolerated = False
            break

    # Speaker tipico: tutto maiuscolo o quasi, poche parole (aumentato a 5 per nomi descrittivi)
    if lowercase_tolerated and len(words) <= 5 and not riga_clean.startswith("("):
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

    #elimino spazi iniziali e finali e imposto maiuscolo
    riga_upper = riga.strip().upper()

    # Pattern originali più comuni
    if (riga_upper == "(CONTINUED)" or
            riga_upper == "CONTINUED" or
            riga_upper == "CONTINUED:" or
            re.match(r"CONTINUED[:\s]*\(?\d+\)?", riga_upper) or
            re.match(r"\(CONTINUED[:\s]*\d+\)", riga_upper)):
        return True

    # Pattern numero-CONTINUED-numero (es: "2        CONTINUED:                                                            2")
    '''
    Rimuove caratteri di spazio non-breaking (\xa0 e \u00A0)
    Normalizza tutti gli spazi multipli in spazi singoli
    Converte in maiuscolo
    '''
    riga_clean = riga.strip().replace("\xa0", " ").replace("\u00A0", " ")
    riga_clean = re.sub(r'\s+', ' ', riga_clean).upper()

    # Pattern numero-CONTINUED-numero (es: "2 CONTINUED: 2")
    if re.match(r'^\d+[A-Za-z]*\s+CONTINUED:?\s+\d+[A-Za-z]*\s*$', riga_clean):
        return True

    # Pattern numero-CONTINUED:(numero)-numero
    # Es: "4   CONTINUED: (2)                                                                   4"
    if re.match(r'^\d+[A-Za-z]*\s+CONTINUED:?\s*\(\d+\)\s+\d+[A-Za-z]*\s*$', riga_clean):
        return True

    # Pattern più generale per CONTINUED con parentesi
    # Es: "CONTINUED: (2)", "5 CONTINUED: (3) 5", etc.
    if re.search(r'CONTINUED:?\s*\(\d+\)', riga_clean):
        return True

    # Pattern solo CONTINUED con spazi e numeri intorno
    if re.match(r'^\d+[A-Za-z]*\s+CONTINUED:?\s*$', riga_clean) or \
            re.match(r'^\s*CONTINUED:?\s+\d+[A-Za-z]*\s*$', riga_clean):
        return True

    # Pattern con numeri di pagina in parentesi e numeri ai lati
    # Es: "4 CONTINUED: (2) 4", "A1 CONTINUED (5) A1"
    if re.match(r'^\d+[A-Za-z]*\s+CONTINUED:?\s*\([^)]+\)\s*\d+[A-Za-z]*\s*$', riga_clean):
        return True

    # Pattern flessibile che cattura varianti con molto spazio bianco
    # Rileva pattern dove CONTINUED è circondato da numeri, anche con spazi estesi
    continued_flexible = re.match(r'^(\d+[A-Za-z]*)\s+(CONTINUED:?)\s*(\([^)]*\))?\s*(\d+[A-Za-z]*)\s*$', riga_clean)
    if continued_flexible:
        # Verifica che i numeri all'inizio e alla fine corrispondano (tipico delle righe continued)
        start_num = continued_flexible.group(1)
        end_num = continued_flexible.group(4)
        if start_num == end_num:
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
        match.group(2)
        # Sostituisce i trattini con spazi per una forma leggibile
        title = title_slug.replace('-', ' ').strip()
        return title
    else:
        # Se non trova l'anno, restituisce comunque il nome "normalizzato"
        normalized_title = name_without_ext.replace('-', ' ').strip()
        return normalized_title