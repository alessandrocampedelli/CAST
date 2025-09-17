# Convertitore e Analizzatore Copioni HTML/PDF → TEI-XML

Questo progetto converte copioni cinematografici da HTML e PDF nel formato standard TEI-XML e genera analisi statistiche

## Struttura del Progetto

```
progetto/
├── main.py             # Script principale (esegue tutto)
├── extract_txt.py      # Fase 1: Estrae TXT da HTML/PDF
├── txt2tei.py          # Fase 2: Converte TXT → TEI-XML  
├── TEIAnalyzer.py      # Fase 3: Analizza i copioni TEI
├── dashboard.py        # Fase 4: Dashboard interattiva Streamlit
├── utils.py            # Funzioni di utilità per txt2tei
├── README.md           # Documentazione
├── input/              # Sorgenti originali
│   ├── pdf_scripts/    # File PDF dei copioni
│   └── sites.txt       # URL HTML da scaricare (IMSDB)
├── txt_scripts/        # File TXT intermedi (generati automaticamente)
├── tei_scripts/        # File XML TEI (generati automaticamente)
└── analysis/           # Risultati analisi (generati automaticamente)
    ├── screenplay_analysis.json
    └── screenplay_analysis_macro_stats.json
```

## Workflow Completo

### Esecuzione Automatica (Consigliata)
```bash
python main.py
```
Esegue automaticamente tutte e quattro le fasi in sequenza:
1. Estrazione testo da PDF/HTML
2. Conversione in formato TEI-XML
3. Analisi statistica dei copioni
4. Avvio dashboard interattiva

### Esecuzione Manuale (Avanzata)

#### Fase 1: Estrazione TXT
```bash
python extract_txt.py
```
- **Input**: File PDF in `input/pdf_scripts/` + URL in `input/sites.txt`
- **Output**: File TXT in `txt_scripts/`

#### Fase 2: Conversione TEI-XML  
```bash
python txt2tei.py
```
- **Input**: File TXT in `txt_scripts/`
- **Output**: File XML in `tei_scripts/`

#### Fase 3: Analisi Statistiche
```bash
python TEIAnalyzer.py
```
- **Input**: File XML in `tei_scripts/`
- **Output**: File JSON di analisi in `analysis/`

#### Fase 4: Dashboard Interattiva
```bash
streamlit run dashboard.py
```
- **Input**: File JSON da `analysis/`
- **Output**: Dashboard web interattiva

## Installazione

### Dipendenze Complete
```bash
pip install requests beautifulsoup4 pdfminer.six streamlit plotly
```

### Dipendenze per Fase
- **Fase 1**: `requests (download righe dalla pagina web),
               beautifulsoup4 (estrazione testo da html),
               pdfminer.six (estrazione testo da pdf)`
- **Fase 2**: Solo librerie standard Python
- **Fase 3**: Solo librerie standard Python
- **Fase 4**: `streamlit (creazione pagina web con interfaccia utente), 
               plotly (creazione di grafici interattivi)`

## Utilizzo

### Preparazione Iniziale
1. Crea la struttura delle cartelle:
   ```bash
   mkdir -p input/pdf_scripts txt_scripts tei_scripts analysis
   ```

2. **Per file PDF**: Inserisci i file PDF in `input/pdf_scripts/`

3. **Per siti web**: Crea `input/sites.txt` con gli URL IMSDB:
   ```
   https://imsdb.com/scripts/Film1.html
   https://imsdb.com/scripts/Film2.html
   ```

### Esecuzione Completa
```bash
# Metodo rapido (consigliato)
python main.py

# Metodo manuale (se necessario)
python extract_txt.py
python txt2tei.py
python TEIAnalyzer.py
streamlit run dashboard.py
```

### Risultati
- **File XML**: Copioni convertiti in `tei_scripts/`
- **Analisi JSON**: Statistiche dettagliate in `analysis/`
- **Dashboard Web**: Visualizzazioni interattive accessibili via browser

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

### File TEI-XML
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

### File di Analisi JSON
Le statistiche vengono salvate in due file:

- `screenplay_analysis.json`: Analisi dettagliate per ogni singolo film
- `screenplay_analysis_macro_stats.json`: Statistiche aggregate di tutti i film

## Funzionalità

### Conversione TEI-XML
#### Riconoscimento Automatico
- **Scene**: Identificate tramite location lines (INT./EXT.)
- **Personaggi**: Nomi in maiuscolo con gestione delle continuazioni
- **Dialoghi**: Testo associato ai personaggi
- **Descrizioni**: Stage directions e indicazioni sceniche

#### Filtri Intelligenti
- Rimuove numeri di pagina
- Ignora intestazioni e piè di pagina
- Salta transizioni cinematografiche (`CUT TO:`, `FADE OUT`, etc.)
- Gestisce righe `CONTINUED` e `(MORE)`

### Analisi Statistiche
#### Analisi per Location
- **Tipo**: Classificazione INT/EXT
- **Ambiente**: urban, suburban, rural, sea, mountain, desert, space, fantasy
- **Setting**: contemporary, natural, fantasy/sci-fi

#### Analisi Temporale
- **Periodi giornalieri**: MORNING, DAY, EVENING, NIGHT
- **Stagioni**: spring, summer, autumn, winter

#### Statistiche Aggregate
- Distribuzione percentuale per tutti i parametri
- Confronti tra film
- Identificazione di pattern e tendenze

### Dashboard Interattiva
- **Grafici a torta**: Distribuzione INT/EXT, periodi giornalieri, stagioni
- **Grafici a barre**: Ambienti, confronti tra film
- **Analisi individuali**: Dettagli per ogni singolo film
- **Metriche comparative**: Confronto con le medie generali
- **Visualizzazioni responsive**: Grafici interattivi con Plotly

## File del Progetto

### `main.py`
Script orchestratore che esegue l'intero pipeline con gestione degli errori.

### `extract_txt.py`
Estrazione testo da PDF (pdfminer) e HTML (IMSDB via requests e BeautifulSoup).

### `txt2tei.py`
Conversione da formato screenplay a TEI-XML con parsing intelligente.

### `utils.py`
Libreria completa di funzioni per il riconoscimento degli elementi screenplay:
- `is_location_line()`: Identifica nuove scene con pattern multipli
- `is_speaker()`: Riconosce personaggi e continuazioni
- `is_page_number()`, `is_header_line()`: Filtri per contenuto non rilevante
- `extract_title_from_filename()`: Estrazione titoli
- E oltre 10 funzioni specializzate

### `TEIAnalyzer.py`
Analizzatore avanzato che:
- Classifica semanticamente location e temporalità
- Calcola statistiche per film singoli e aggregate
- Genera report JSON strutturati
- Utilizza dizionari di keyword per classificazione automatica

### `dashboard.py`
Dashboard Streamlit con:
- Visualizzazioni aggregate multi-film
- Analisi dettagliate per singoli film
- Grafici interattivi (Plotly)
- Metriche comparative
- Interface responsive

## Licenza

Progetto open source per uso educativo e di ricerca.