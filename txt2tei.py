import os
import re
import xml.etree.ElementTree as ET
import utils

INPUT_TXT_DIR = "copioni_txt"
OUTPUT_DIR = "output"


def converti_in_tei(percorso_txt):
    with open(percorso_txt, 'r', encoding='utf-8') as f:
        righe = [r.strip() for r in f if r.strip()]

    print(f"[DEBUG] Totale righe lette: {len(righe)}")

    # Estrae il titolo dal nome del file invece che dalla prima riga
    filename = os.path.basename(percorso_txt)
    titolo = utils.extract_title_from_filename(filename)

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
        if utils.is_continued_line(riga):
            print(f"[DEBUG] Saltata riga CONTINUED (incluso pattern numero-CONTINUED-numero): {riga}")
            i += 1
            continue

        # PRIORITÀ 2: RILEVA INIZIO NUOVA SCENA BASANDOSI SULLA LOCATION
        # Questo deve essere controllato DOPO CONTINUED ma PRIMA dei numeri di pagina
        if utils.is_location_line(riga):
            # Verifica se è il pattern numero-descrizione-numero sulla stessa riga
            riga_clean = riga.strip().replace("\xa0", " ").replace("\u00A0", " ")
            riga_clean = re.sub(r'\s+', ' ', riga_clean)

            # Pattern: numero/alfanumerico + descrizione + numero/alfanumerico
            # (es: "4 FULL SHOT - ENTERPRISE BRIDGE 4" o "A1 EXT. ADDAMS MANSION FRONT STEPS - CHRISTMAS EVE A1")
            numero_desc_numero_match = re.match(r'^([A-Za-z]*\d+[A-Za-z]*)\s+(.+?)\s+([A-Za-z]*\d+[A-Za-z]*)$',
                                                riga_clean)

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
        if utils.is_page_number(riga):
            print(f"[DEBUG] Saltata pagina: {riga}")
            i += 1
            continue

        # Ignora numeri di scena (ora non servono più per identificare scene)
        if utils.is_scene_number(riga):
            print(f"[DEBUG] Saltato numero scena (ora ignorato): {riga}")
            i += 1
            continue

        # Ignora righe MORE (ma imposta flag di continuazione)
        if utils.is_more_line(riga):
            print(f"[DEBUG] Saltata riga MORE: {riga}")
            speech_in_continuazione = True
            i += 1
            continue

        # Ignora transizioni
        if utils.is_transition_line(riga):
            print(f"[DEBUG] Saltata transizione: {riga}")
            i += 1
            continue

        # Ignora intestazioni (header) - righe duplicate
        if utils.is_header_line(riga, next_line):
            print(f"[DEBUG] Saltata intestazione duplicata: {riga}")
            i += 1
            continue

        # RILEVA SPEAKER E BATTUTE
        if utils.is_speaker(riga) and scena_corrente is not None:
            speaker_name = utils.extract_speaker_name(riga)
            is_continuation = utils.is_continuation_speaker(riga)

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
                if (utils.is_speaker(next_riga) or utils.is_location_line(next_riga) or
                        utils.is_page_number(next_riga) or utils.is_continued_line(next_riga) or
                        utils.is_more_line(next_riga) or utils.is_scene_number(next_riga)):
                    break

                # NUOVO: Controlla anche header/footer durante la raccolta battute
                if utils.is_header_line(next_riga):
                    print(f"[DEBUG] Saltato piè di pagina durante raccolta battute: {next_riga}")
                    i += 1
                    continue

                # NUOVO: Controlla anche transizioni durante la raccolta battute
                if utils.is_transition_line(next_riga):
                    print(f"[DEBUG] Saltata transizione durante raccolta battute: {next_riga}")
                    i += 1
                    continue

                if next_riga:
                    battute.append(next_riga)
                i += 1

            # Verifica se c'è (MORE) alla fine delle battute raccolte
            if battute and utils.is_more_line(battute[-1]):
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
                        ultimo_sp_element.append(utils.crea_elemento_testo("p", battuta))
                    print(f"[DEBUG] Aggiunte {len(battute)} battute alla speech esistente")
                else:
                    # Crea nuova speech
                    sp = ET.SubElement(scena_corrente, "sp")
                    ET.SubElement(sp, "speaker").text = speaker_name
                    for battuta in battute:
                        sp.append(utils.crea_elemento_testo("p", battuta))
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
    utils.indent(root)
    tree = ET.ElementTree(root)
    nome_file = os.path.basename(percorso_txt).replace(".txt", ".xml")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    percorso_finale = os.path.join(OUTPUT_DIR, nome_file)
    tree.write(percorso_finale, encoding="utf-8", xml_declaration=True)
    print(f"File TEI salvato in: {percorso_finale}")

def main():
    # Conta i file da processare
    file_txt = [f for f in os.listdir(INPUT_TXT_DIR) if f.endswith('.txt')]

    if not file_txt:
        return

    print(f"🔄 Processando {len(file_txt)} file...")

    for nome_file in file_txt:
        try:
            print(f"\n📄 Processando: {nome_file}")
            percorso_completo = os.path.join(INPUT_TXT_DIR, nome_file)
            converti_in_tei(percorso_completo)
            print(f"✅ {nome_file} → convertito con successo")

        except Exception as e:
            print(f"❌ Errore durante il processamento di {nome_file}: {str(e)}")

if __name__ == "__main__":
    main()