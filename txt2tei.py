import os
import re
import xml.etree.ElementTree as ET
import utils

INPUT_TXT_DIR = "txt_scripts"
OUTPUT_DIR = "tei_scripts"


def converti_in_tei(percorso_txt):
    with open(percorso_txt, 'r', encoding='utf-8') as f:
        righe = [r.strip() for r in f if r.strip()]

    # Estrae il titolo dal nome del file invece che dalla prima riga
    filename = os.path.basename(percorso_txt)
    titolo = utils.extract_title_from_filename(filename)

    # Tutto il contenuto del file è il corpo del copione
    corpo_righe = righe

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
            i += 1
            continue

        # PRIORITÀ 2: RILEVA INIZIO NUOVA SCENA BASANDOSI SULLA LOCATION
        if utils.is_location_line(riga):
            #1) pulizia della riga: normalizzo tutti gli spazi multipli in un singolo spazio
            riga_clean = riga.strip().replace("\xa0", " ").replace("\u00A0", " ")
            riga_clean = re.sub(r'\s+', ' ', riga_clean)

            #2)riconoscimento dei pattern
            # Pattern 1: numero/alfanumerico + descrizione + numero/alfanumerico
            numero_desc_numero_match = re.match(r'^([A-Za-z]*\d+[A-Za-z]*)\s+(.+?)\s+([A-Za-z]*\d+[A-Za-z]*)$',
                                                riga_clean)

            # Pattern 2: numero + INT./EXT./I/E. + descrizione
            numero_location_match = re.match(r'^(\d+[A-Za-z]*)\s+((?:INT\.?|EXT\.?|I/E\.?)\s+.+)$',
                                             riga_clean, re.IGNORECASE)

            if numero_desc_numero_match:
                # Estrae SOLO la descrizione, ignora il numero originale
                location_description = numero_desc_numero_match.group(2).strip()

                # Usa numerazione automatica
                numero_scena = str(scene_counter)

                # Crea la scena usando numerazione automatica
                scena_corrente = ET.SubElement(body, "div", type="scene")
                scena_corrente.set("n", numero_scena)

                # Aggiunge la location estratta
                ET.SubElement(scena_corrente, "stage", type="location").text = location_description

            elif numero_location_match:
                #stesso identico approccio per questo pattern
                location_description = numero_location_match.group(2).strip()

                numero_scena = str(scene_counter)

                scena_corrente = ET.SubElement(body, "div", type="scene")
                scena_corrente.set("n", numero_scena)

                ET.SubElement(scena_corrente, "stage", type="location").text = location_description

            else:
                #location standard
                location_line = riga

                numero_scena = str(scene_counter)

                # Crea la scena con numerazione automatica
                scena_corrente = ET.SubElement(body, "div", type="scene")
                scena_corrente.set("n", numero_scena)

                # Aggiunge la location
                ET.SubElement(scena_corrente, "stage", type="location").text = location_line

            # Reset dello speaker quando inizia nuova scena (comune a tutti i pattern)
            speaker_corrente = None
            ultimo_sp_element = None
            speech_in_continuazione = False

            # Incrementa il contatore delle scene
            scene_counter += 1
            i += 1
            continue

        # PRIORITÀ 3: Ignora numeri di pagina (SOLO se non sono location o continued)
        if utils.is_page_number(riga):
            i += 1
            continue

        # PRIORITÀ 4: Ignora numeri di scena (ora non servono più per identificare scene)
        if utils.is_scene_number(riga):
            i += 1
            continue

        # PRIORITÀ 5: Ignora righe MORE (ma imposta flag di continuazione)
        if utils.is_more_line(riga):
            speech_in_continuazione = True
            i += 1
            continue

        # PRIORITÀ 6: Ignora transizioni
        if utils.is_transition_line(riga):
            i += 1
            continue

        # PRIORITÀ 7: Ignora intestazioni (header) - righe duplicate
        if utils.is_header_line(riga, next_line):
            i += 1
            continue

        # PRIORITÀ 8: RILEVA SPEAKER E BATTUTE
        if utils.is_speaker(riga) and scena_corrente is not None:
            speaker_name = utils.extract_speaker_name(riga)
            is_continuation = utils.is_continuation_speaker(riga)

            # Determina se continuare la speech precedente
            '''
             due scenari possibili: 
                JOHN
                    Hello there!
                    (MORE)                  #speech_in_continuazione = True
                
                [pagina successiva]
                
                JOHN                        #speaker_name == speaker_corrente
                    How are you doing?
                -----------------------
                JOHN
                    I was saying...
                
                JOHN (CONT'D)               #is_continuation = True dato che c'è (CONT'D)
                    that we should leave.
            '''
            continua_speech = (
                                      (speech_in_continuazione and speaker_name == speaker_corrente) or
                                      (is_continuation and speaker_name == speaker_corrente)
                              ) and ultimo_sp_element is not None

            #salto la riga dello speaker
            i += 1
            battute = []

            # loop per raccogliere tutte le righe di dialogo del personaggio corrente
            while i < len(corpo_righe):
                next_riga = corpo_righe[i].strip()

                # Stop conditions: il loop si ferma quando incontra:
                '''
                    Nuovo speaker: "MARY"
                    Nuova scena: "INT. KITCHEN - DAY"
                    Numero pagina: "15"
                    Continued: "CONTINUED"
                    More: "(MORE)"
                    Numero scena: "12A"
                '''
                if (utils.is_speaker(next_riga) or utils.is_location_line(next_riga) or
                        utils.is_page_number(next_riga) or utils.is_continued_line(next_riga) or
                        utils.is_more_line(next_riga) or utils.is_scene_number(next_riga)):
                    break

                # durante la raccolta se individuo righe header le ignoro
                if utils.is_header_line(next_riga):
                    i += 1
                    continue

                # durante raccolta se individuo parole di transizioni le ignoro
                if utils.is_transition_line(next_riga):
                    i += 1
                    continue

                #raccolta effettiva: salvo la riga nella lista battute
                if next_riga:
                    battute.append(next_riga)
                i += 1

            # Verifica se c'è (MORE) alla fine delle battute raccolte
            '''
            Se l'ultima battuta è (MORE), la rimuovo e imposto il flag. esso verrà usato
            per la prossima speech dello stesso personaggio, in questo modo (MORE) non appare nell'xml finale 
            '''
            if battute and utils.is_more_line(battute[-1]):
                #rimuove (MORE) dalle battute
                battute.pop()
                speech_in_continuazione = True
            else:
                speech_in_continuazione = False

            # creazione/aggiornamento xml aggiungendo le battute
            if battute:
                if continua_speech:
                    # Continua la speech precedente
                    for battuta in battute:
                        #inserisco tutti gli elementi p in sp
                        ultimo_sp_element.append(utils.crea_elemento_testo("p", battuta))
                else:
                    # Crea nuova speech
                    sp = ET.SubElement(scena_corrente, "sp")
                    ET.SubElement(sp, "speaker").text = speaker_name
                    for battuta in battute:
                        # inserisco tutti gli elementi p in sp
                        sp.append(utils.crea_elemento_testo("p", battuta))
                    #aggiorno il riferimento all'ultimo elemento <sp>
                    ultimo_sp_element = sp
                    speaker_corrente = speaker_name
            continue

        # PRIORITÀ 9: tutto ciò che non è stato catturato lo catturo come DESCRIZIONI SCENE (stage directions)
        if scena_corrente is not None and riga:
            ET.SubElement(scena_corrente, "stage").text = riga

        i += 1

    # Formattazione e salvataggio
    utils.indent(root)
    tree = ET.ElementTree(root)
    nome_file = os.path.basename(percorso_txt).replace(".txt", ".xml")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    percorso_finale = os.path.join(OUTPUT_DIR, nome_file)
    tree.write(percorso_finale, encoding="utf-8", xml_declaration=True)

def main():
    # Conta i file da processare
    file_txt = [f for f in os.listdir(INPUT_TXT_DIR) if f.endswith('.txt')]

    if not file_txt:
        return

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