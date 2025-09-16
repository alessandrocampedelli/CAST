# Convertitore Copioni HTML/PDF → TEI-XML

Questo progetto converte copioni cinematografici da HTML e PDF nel formato standard TEI-XML attraverso un workflow a due fasi.

## Struttura del Progetto

```
progetto/
├── main.py             # Script principale (esegue tutto)
├── estrazione_txt.py   # Fase 1: Estrae TXT da HTML/PDF
├── txt2tei.py          # Fase 2: Converte TXT → TEI-XML  
├── utils.py            # Funzioni di utilità per txt2tei
├── README.md           # Documentazione
├── input/              # Sorgenti originali
│   ├── copioni_pdf/    # File PDF dei copioni
│   └── siti.txt        # URL HTML da scaricare (IMSDB)
├── copioni_txt/        # File TXT intermedi (generati automaticamente)
└── output/             # File XML finali
```

## Workflow Completo

### Esecuzione Automatica (Consigliata)
```bash
python main.py
```
Esegue automaticamente entrambe le fasi in sequenza con gestione degli errori.

### Esecuzione Manuale (Avanzata)

#### Fase 1: Estrazione TXT
```bash
python extract_txt.py
```
- **Input**: File PDF in `input/copioni_pdf/` + URL in `input/siti.txt`
- **Output**: File TXT in `copioni_txt/`

#### Fase 2: Conversione TEI-XML  
```bash
python txt2tei.py
```
- **Input**: File TXT in `copioni_txt/`
- **Output**: File XML in `output/`

## Installazione

### Dipendenze Fase 1 (estrazione_txt.py)
```bash
pip install requests beautifulsoup4 pdfminer.six
```

### Dipendenze Fase 2 (txt2tei.py)
- Solo librerie standard Python (nessuna installazione aggiuntiva)

## Utilizzo

### Preparazione Iniziale
1. Crea la struttura delle cartelle:
   ```bash
   mkdir -p input/pdf_scripts txt_scripts tei_scripts
   ```

2. **Per file PDF**: Inserisci i file PDF in `input/copioni_pdf/`

3. **Per siti web**: Crea `input/siti.txt` con gli URL IMSDB:
   ```
   https://imsdb.com/scripts/Film1.html
   https://imsdb.com/scripts/Film2.html
   ```

### Esecuzione Completa
```bash
# ⚡ Metodo rapido (consigliato)
python main.py

# 🔧 Metodo manuale (se necessario)
python extract_txt.py
python txt2tei.py
```

### Risultato
- File XML pronti nella cartella `output/`

## Formato Input

### Sorgenti Supportate
- **File PDF**: Copioni in formato PDF (estratti automaticamente)
- **Siti IMSDB**: URL del database Internet Movie Script Database

I file TXT intermedi seguono il formato standard dei copioni cinematografici:

- **Location lines**: `INT. CASA - GIORNO` o `EXT. STRADA - NOTTE`
- **Speaker**: Nomi in maiuscolo (es. `MARIO`, `LUIGI (CONT'D)`)
- **Dialoghi**: Testo normale dopo il nome del personaggio
- **Stage directions**: Descrizioni narrative

## Formato Output

I file XML seguono lo standard TEI (Text Encoding Initiative):

```xml
<?xml version="1.0" encoding="utf-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <teiHeader>
    <fileDesc>
      <titleStmt>
        <title>Titolo del Film</title>
      </titleStmt>
    </fileDesc>
  </teiHeader>
  <text>
    <body>
      <div type="scene" n="1">
        <stage type="location">INT. CASA - GIORNO</stage>
        <sp>
          <speaker>MARIO</speaker>
          <p>Ciao Luigi!</p>
        </sp>
        <stage>Mario entra in cucina.</stage>
      </div>
    </body>
  </text>
</TEI>
```

## Funzionalità

### Riconoscimento Automatico
- **Scene**: Identificate tramite location lines (INT./EXT.)
- **Personaggi**: Nomi in maiuscolo con gestione delle continuazioni
- **Dialoghi**: Testo associato ai personaggi
- **Descrizioni**: Stage directions e indicazioni sceniche

### Filtri Intelligenti
- Rimuove numeri di pagina
- Ignora intestazioni e piè di pagina
- Salta transizioni cinematografiche (`CUT TO:`, `FADE OUT`, etc.)
- Gestisce righe `CONTINUED` e `(MORE)`

### Gestione Errori
- Verifica della struttura delle cartelle
- Rapporto dettagliato sui file processati
- Gestione degli errori per singoli file

## File del Progetto

### `main.py` 🎯
Script orchestratore che:
- Esegue automaticamente l'intero workflow
- Verifica la presenza dei file necessari
- Gestisce gli errori e fornisce feedback dettagliato
- Mostra il riepilogo finale

### `estrazione_txt.py`
Script di estrazione che:
- Scarica copioni da URL IMSDB
- Estrae testo da file PDF usando pdfminer
- Genera file TXT nella cartella `copioni_txt/`

### `txt2tei.py`
Script di conversione che:
- Legge i file TXT da `copioni_txt/`
- Converte in formato TEI-XML
- Salva i risultati in `output/`

### `utils.py`
Libreria di funzioni di utilità per `txt2tei.py`:
- `is_location_line()`: Identifica nuove scene
- `is_speaker()`: Riconosce i nomi dei personaggi  
- `is_page_number()`: Filtra numeri di pagina
- `extract_title_from_filename()`: Estrae il titolo dal nome file
- E molte altre funzioni di supporto

## Personalizzazione

### Modifica dei Pattern
Puoi personalizzare il riconoscimento modificando le funzioni in `utils.py`:

- **Personaggi**: Modifica `is_speaker()` per pattern specifici
- **Location**: Aggiorna `is_location_line()` per nuovi formati
- **Filtri**: Estendi `is_header_line()` per rimuovere contenuti specifici

### Struttura TEI
Puoi modificare la struttura XML generata nella funzione `converti_in_tei()` in `txt2tei.py`.

## Risoluzione Problemi

### Cartelle non trovate
Lo script crea automaticamente le cartelle mancanti. Assicurati di avere i permessi di scrittura.

### Nessun file processato
Verifica che:
- Hai eseguito prima `estrazione_txt.py`
- I file TXT siano nella cartella `copioni_txt/`
- I file abbiano estensione `.txt`
- I file non siano vuoti

### Errori di estrazione
Se `estrazione_txt.py` non funziona:
- Verifica la connessione internet per gli URL IMSDB
- Controlla che i file PDF non siano corrotti
- Installa le dipendenze: `pip install requests beautifulsoup4 pdfminer.six`

### Errori di encoding
I file devono essere in encoding UTF-8. Se hai problemi, converti i file prima dell'elaborazione.

## Licenza

Progetto open source per uso educativo e di ricerca.