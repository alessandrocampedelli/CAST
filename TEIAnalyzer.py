import re
import json
import os
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from collections import Counter

@dataclass
class LocationInfo:
    """Informazioni estratte sui luoghi"""
    type: Optional[str] = None  # INT/EXT
    setting: Optional[str] = None  # suburban, fantasy, etc.
    environment: Optional[str] = None  # sea, mountain, urban, etc.
    real_imaginary: Optional[str] = None  # real/imaginary

@dataclass
class TemporalInfo:
    """Informazioni estratte sui tempi"""
    period: Optional[str] = None  # DAY/NIGHT/MORNING/EVENING
    season: Optional[str] = None  # winter/spring/summer/autumn
    historical: Optional[str] = None  # contemporary/medieval/future/1920s

@dataclass
class SceneAnalysis:
    """Analisi completa di una scena"""
    scene_n: str
    location: LocationInfo
    temporal: TemporalInfo
    #info non inserite nel file json. TODO: capire cosa farci -> se tenerle o meno
    raw_location_text: str
    stage_texts: List[str]


class TEIAnalyzer:
    """Analizzatore principale per file TEI"""

    def __init__(self):
        # Dizionari di parole chiave per classificazione
        self.environment_keywords = {
            'sea': ['ocean', 'sea', 'beach', 'coast', 'waves', 'harbor', 'port', 'ship', 'boat'],
            'mountain': ['mountain', 'hill', 'peak', 'cliff', 'valley', 'cave', 'rock'],
            'urban': ['city', 'street', 'building', 'apartment', 'office', 'shop', 'mall', 'downtown'],
            'suburban': ['house', 'home', 'neighborhood', 'garden', 'yard', 'driveway', 'suburb'],
            'rural': ['farm', 'field', 'countryside', 'barn', 'village', 'meadow', 'forest', 'woods'],
            'desert': ['desert', 'sand', 'dune', 'oasis', 'wasteland'],
            'space': ['space', 'spaceship', 'planet', 'moon', 'galaxy', 'asteroid', 'orbit'],
            'fantasy': ['castle', 'dungeon', 'tower', 'magical', 'enchanted', 'wizard', 'dragon']
        }

        self.time_keywords = {
            'morning': ['morning', 'dawn', 'sunrise', 'early'],
            'day': ['day', 'noon', 'afternoon', 'midday', 'daylight'],
            'evening': ['evening', 'sunset', 'dusk', 'twilight'],
            'night': ['night', 'midnight', 'darkness', 'moonlight', 'stars'],
            'winter': ['snow', 'ice', 'cold', 'winter', 'frost', 'christmas', 'freezing'],
            'spring': ['spring', 'flowers', 'bloom', 'rain', 'easter'],
            'summer': ['summer', 'hot', 'sun', 'heat', 'vacation', 'beach'],
            'autumn': ['autumn', 'fall', 'leaves', 'harvest', 'october', 'november']
        }

        self.historical_keywords = {
            'medieval': ['medieval', 'castle', 'knight', 'sword', 'armor', 'kingdom', 'throne'],
            'victorian': ['victorian', '1800s', 'carriage', 'corset', 'gentleman', 'lady'],
            'modern': ['car', 'phone', 'computer', 'internet', 'smartphone', 'laptop'],
            'future': ['future', 'robot', 'laser', 'spacecraft', 'cyberpunk', 'ai', '2050'],
            '1920s': ['1920', 'jazz', 'prohibition', 'flapper', 'speakeasy'],
            '1960s': ['1960', 'hippie', 'vietnam', 'beatles', 'woodstock'],
            '1980s': ['1980', 'neon', 'arcade', 'walkman', 'disco']
        }

        # Luoghi reali vs immaginari (campione)
        self.real_places = {
            'london', 'paris', 'new york', 'rome', 'tokyo', 'moscow', 'berlin',
            'madrid', 'sydney', 'cairo', 'mumbai', 'beijing', 'chicago',
            'los angeles', 'san francisco', 'miami', 'boston', 'seattle'
        }

        self.imaginary_places = {
            'hogwarts', 'gotham', 'metropolis', 'rivendell', 'mordor',
            'narnia', 'atlantis', 'asgard', 'wakanda', 'neverland'
        }

    def analyze_tei_file(self, file_path: str) -> Dict[str, Any]:
        """Analizza un file TEI completo"""
        try:
            #contenuto xml
            tree = ET.parse(file_path)
            root = tree.getroot()

            # Estrai titolo
            title_elem = root.find('.//{http://www.tei-c.org/ns/1.0}title')
            title = title_elem.text if title_elem is not None else os.path.basename(file_path)

            #salvo tutte le scene in una lista
            scenes = []
            scene_divs = root.findall('.//{http://www.tei-c.org/ns/1.0}div[@type="scene"]')

            #analizzo ogni scena una a una
            for scene_div in scene_divs:
                scene_analysis = self._analyze_scene(scene_div)
                if scene_analysis:
                    scenes.append(asdict(scene_analysis))

            #Calcola statistiche aggregate a livello di film
            statistics = self._calculate_statistics(scenes)

            return {
                'film': title,
                'total_scenes': len(scenes),
                'statistics': statistics,
                'analysis_timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'error': f'Errore nell\'analisi del file {file_path}: {str(e)}',
                'film': os.path.basename(file_path),
                'scenes': [],
                'statistics': {}
            }

    def _analyze_scene(self, scene_div) -> Optional[SceneAnalysis]:
        """Analizza una singola scena"""

        #numero della scena
        scene_n = scene_div.get('n', 'unknown')

        #estrazione location principale
        location_stage = scene_div.find('.//{http://www.tei-c.org/ns/1.0}stage[@type="location"]')
        raw_location_text = location_stage.text if location_stage is not None else ""

        #estrazione di tutti i testi etichettati come stage
        stage_elements = scene_div.findall('.//{http://www.tei-c.org/ns/1.0}stage')
        stage_texts = [elem.text for elem in stage_elements if elem.text]

        #analizzo location
        location_info = self._analyze_location(raw_location_text, stage_texts)

        #analizzo temporalità
        temporal_info = self._analyze_temporal(raw_location_text, stage_texts)

        return SceneAnalysis(
            scene_n=scene_n,
            location=location_info,
            temporal=temporal_info,
            raw_location_text=raw_location_text,
            stage_texts=stage_texts
        )

    def _analyze_location(self, location_text: str, stage_texts: List[str]) -> LocationInfo:
        """Analisi dei luoghi"""

        #creo l'oggetto vuoto
        location_info = LocationInfo()

        #STEP 1: Pattern cinematografici standard
        location_upper = location_text.upper()

        #Estrai INT/EXT
        if location_upper.startswith('INT'):
            location_info.type = 'INT'
        elif location_upper.startswith('EXT'):
            location_info.type = 'EXT'
        elif 'INT.' in location_upper:
            location_info.type = 'INT'
        elif 'EXT.' in location_upper:
            location_info.type = 'EXT'

        #STEP 2: Analisi semantica
        all_text = (location_text + ' ' + ' '.join(stage_texts)).lower()

        #dizionario vuoto che conterrà per ogni ambiente prestabilito, quante parole chiave sono state trovate
        #nella scena
        environment_scores = {}

        #scorro su tutti i tipi di ambienti definiti nel dizionario
        #env_type: stringa che rappresenta il tipo di ambiente
        #keywords: lista di parole associate a quell'ambiente
        for env_type, keywords in self.environment_keywords.items():

            #controllo se la parola chiave è contenuta nel testo. Se si aggiungo 1 al conteggio
            score = sum(1 for keyword in keywords if keyword in all_text)

            #se è stata trovata almeno una parola chiave con almeno una occorrenza, memorizzo il risultato
            #chiave: tipo ambiente; valore: punteggio
            if score > 0:
                environment_scores[env_type] = score

        if environment_scores:
            #imposto come environment quello che ha il punteggio più alto nel dizionario
            location_info.environment = max(environment_scores, key=environment_scores.get)

        #Determina setting generale
        if location_info.environment in ['space', 'fantasy']:
            location_info.setting = 'fantasy/sci-fi'
        elif location_info.environment in ['urban', 'suburban']:
            location_info.setting = 'contemporary'
        elif location_info.environment in ['sea', 'mountain', 'desert']:
            location_info.setting = 'natural'
        else:
            location_info.setting = 'unspecified'

        #STEP 3: Verifica geografica

        #salvo le parole in un insieme (per evitare duplicati)
        location_words = set(location_text.lower().split())

        #se c'è almeno un luogo reale contenuto in location_words marchio la scena come real
        if any(place in location_words for place in self.real_places):
            location_info.real_imaginary = 'real'
        #se non era reale, controllo se c'è almeno una parola immaginaria
        elif any(place in location_words for place in self.imaginary_places):
            location_info.real_imaginary = 'imaginary'
        else:
            #se la scena non è ne reale e ne immaginaria, si usa una logica di fallback
            #se il setting trovato nella fase 2 è fantasy/sci-fi, si assume che il luogo sia immaginario altrimenti sconosciuto
            if location_info.setting == 'fantasy/sci-fi':
                location_info.real_imaginary = 'imaginary'
            else:
                location_info.real_imaginary = 'unknown'

        return location_info

    def _analyze_temporal(self, location_text: str, stage_texts: List[str]) -> TemporalInfo:
        """Analisi contestuale degli intervalli temporali"""

        #oggetto vuoto di output
        temporal_info = TemporalInfo()

        all_text = (location_text + ' ' + ' '.join(stage_texts)).lower()

        #Analizza periodo giornaliero

        #dizionario vuoto
        time_scores = {}

        #scorro tutti i tipi di tempo (fasi giornata)
        for time_type, keywords in self.time_keywords.items():
            if time_type in ['morning', 'day', 'evening', 'night']:

                #controllo se ogni parola chiave è contenuta nel testo, se si aggiungo uno al conteggio
                score = sum(1 for keyword in keywords if keyword in all_text)

                if score > 0:
                    #per ogni fase della giornata assegno quante parole chiave sono state trovate nella scena
                    time_scores[time_type] = score

        #per decretare il vero momento della giornata, viene selezionato il momento che ha più occorrenze di parole
        #chiave associate nel testo della scena
        if time_scores:
            temporal_info.period = max(time_scores, key=time_scores.get).upper()

        season_scores = {}

        #scorro tutti i tipi di tempo (stagioni)
        for season, keywords in self.time_keywords.items():
            if season in ['winter', 'spring', 'summer', 'autumn']:

                #controllo se ogni parola chiave è contenuta nel testo. Se si aggiungo un al punteggio.
                #ottengo cosi per ogni stagione, il numero di parole chiave associate trovate nel testo
                score = sum(1 for keyword in keywords if keyword in all_text)

                if score > 0:
                    #assegno ad ogni stagione il numero di keywords relative trovate nel testo
                    season_scores[season] = score

        #per stabilire la stagione corretta, scelgo la stagione con il numero di occorrenze di parole chiave maggiore
        if season_scores:
            temporal_info.season = max(season_scores, key=season_scores.get)

        historical_scores = {}

        #scorro tutti tipi di periodi storici
        for period, keywords in self.historical_keywords.items():

            #conto per ogni periodo storico, quante occorrenze di parole chiave associate ci sono nel testo
            score = sum(1 for keyword in keywords if keyword in all_text)
            if score > 0:
                historical_scores[period] = score

        #scelgo il periodo storico che ha più occorrenze di parole chiave trovate
        if historical_scores:
            temporal_info.historical = max(historical_scores, key=historical_scores.get)
        else:
            #se non trovo parole chiave, di default imposto "contemporaneo"
            temporal_info.historical = 'contemporary'

        return temporal_info

    def _calculate_statistics(self, scenes: List[Dict]) -> Dict[str, Any]:
        """Calcola statistiche aggregate del film"""
        #prende in input una lista di dizionari, ognuno dei quali contiene le info di una scena
        if not scenes:
            return {}

        #Statistiche sui luoghi. Liste di n elementi (n scene del film)

        #lista nella quale, per ogni cella, è salvata l'informazione di INT o EXT
        location_types = [s['location']['type'] for s in scenes if s['location']['type']]

        #lista nella quale, per ogni cella, è salvata l'informazione del tipo di enviroment
        environments = [s['location']['environment'] for s in scenes if s['location']['environment']]

        #lista nella quale, per ogni cella, è salvata l'informazione del tipo reale o immaginario
        real_imaginary = [s['location']['real_imaginary'] for s in scenes if s['location']['real_imaginary']]

        #Statistiche temporali. Liste di n elementi (n scene: somma di tutte le scene dei film analizzati)

        #lista nella quale, per ogni cella, è salvata l'informazione relativo al periodo della giornata
        periods = [s['temporal']['period'] for s in scenes if s['temporal']['period']]

        #lista nella quale, per ogni cella, è salvata l'informazione relativo alla stagione della scena
        seasons = [s['temporal']['season'] for s in scenes if s['temporal']['season']]

        #lista nella quale, per ogni cella, è salvata l'informazione relativo al periodo storico
        historical = [s['temporal']['historical'] for s in scenes if s['temporal']['historical']]

        return {
            'locations': {
                'int_ext_distribution': dict(Counter(location_types)),
                'environment_distribution': dict(Counter(environments)),
                'real_imaginary_distribution': dict(Counter(real_imaginary)),
                'most_common_environment': Counter(environments).most_common(1)[0][0] if environments else None
            },
            'temporal': {
                'day_night_distribution': dict(Counter(periods)),
                'season_distribution': dict(Counter(seasons)),
                'historical_distribution': dict(Counter(historical)),
                'most_common_period': Counter(periods).most_common(1)[0][0] if periods else None
            }
        }

    def _calculate_macro_statistics(self, all_results: List[Dict]) -> Dict[str, Any]:
        """Calcola statistiche aggregate per tutti i film analizzati"""

        # Filtra solo i risultati senza errori
        valid_results = [r for r in all_results if 'error' not in r]

        if not valid_results:
            return {'error': 'Nessun file valido analizzato'}

        # Statistiche generali
        total_films = len(valid_results)
        total_scenes = sum(r['total_scenes'] for r in valid_results)

        # Aggregazione dati di tutti i film
        all_location_types = []
        all_environments = []
        all_real_imaginary = []
        all_periods = []
        all_seasons = []
        all_historical = []

        film_summaries = []

        for result in valid_results:
            stats = result.get('statistics', {})

            # Estrai dati location
            locations = stats.get('locations', {})
            int_ext = locations.get('int_ext_distribution', {})
            environments = locations.get('environment_distribution', {})
            real_img = locations.get('real_imaginary_distribution', {})

            # Estrai dati temporali
            temporal = stats.get('temporal', {})
            periods = temporal.get('day_night_distribution', {})
            seasons = temporal.get('season_distribution', {})
            historical = temporal.get('historical_distribution', {})

            # Aggiungi ai totali
            for location_type, count in int_ext.items():
                all_location_types.extend([location_type] * count)

            for env, count in environments.items():
                all_environments.extend([env] * count)

            for ri, count in real_img.items():
                all_real_imaginary.extend([ri] * count)

            for period, count in periods.items():
                all_periods.extend([period] * count)

            for season, count in seasons.items():
                all_seasons.extend([season] * count)

            for hist, count in historical.items():
                all_historical.extend([hist] * count)

            # Sommario per film
            film_summaries.append({
                'film': result['film'],
                'scenes': result['total_scenes'],
                'dominant_environment': locations.get('most_common_environment'),
                'dominant_period': temporal.get('most_common_period')
            })

        # Calcola percentuali
        def calculate_percentages(counter_dict, total):
            return {k: round((v / total) * 100, 1) for k, v in counter_dict.items()}

        location_counter = dict(Counter(all_location_types))
        environment_counter = dict(Counter(all_environments))
        real_img_counter = dict(Counter(all_real_imaginary))
        period_counter = dict(Counter(all_periods))
        season_counter = dict(Counter(all_seasons))
        historical_counter = dict(Counter(all_historical))

        return {
            'analysis_summary': {
                'total_films_analyzed': total_films,
                'total_scenes_analyzed': total_scenes,
                'average_scenes_per_film': round(total_scenes / total_films, 1),
                'analysis_timestamp': datetime.now().isoformat()
            },
            'aggregated_statistics': {
                'locations': {
                    'int_ext_totals': location_counter,
                    'int_ext_percentages': calculate_percentages(location_counter,
                                                                 sum(location_counter.values())) if location_counter else {},
                    'environment_totals': environment_counter,
                    'environment_percentages': calculate_percentages(environment_counter,
                                                                     sum(environment_counter.values())) if environment_counter else {},
                    'real_imaginary_totals': real_img_counter,
                    'real_imaginary_percentages': calculate_percentages(real_img_counter,
                                                                        sum(real_img_counter.values())) if real_img_counter else {},
                    'most_common_overall': {
                        'location_type': Counter(all_location_types).most_common(1)[0][
                            0] if all_location_types else None,
                        'environment': Counter(all_environments).most_common(1)[0][0] if all_environments else None,
                        'reality_type': Counter(all_real_imaginary).most_common(1)[0][0] if all_real_imaginary else None
                    }
                },
                'temporal': {
                    'period_totals': period_counter,
                    'period_percentages': calculate_percentages(period_counter,
                                                                sum(period_counter.values())) if period_counter else {},
                    'season_totals': season_counter,
                    'season_percentages': calculate_percentages(season_counter,
                                                                sum(season_counter.values())) if season_counter else {},
                    'historical_totals': historical_counter,
                    'historical_percentages': calculate_percentages(historical_counter,
                                                                    sum(historical_counter.values())) if historical_counter else {},
                    'most_common_overall': {
                        'period': Counter(all_periods).most_common(1)[0][0] if all_periods else None,
                        'season': Counter(all_seasons).most_common(1)[0][0] if all_seasons else None,
                        'historical_period': Counter(all_historical).most_common(1)[0][0] if all_historical else None
                    }
                }
            },
            'films_summary': film_summaries,
            'top_insights': {
                'most_common_combinations': self._find_common_combinations(valid_results),
                'genre_patterns': self._identify_genre_patterns(valid_results)
            }
        }

    def _find_common_combinations(self, results: List[Dict]) -> Dict[str, Any]:
        """Trova combinazioni comuni di caratteristiche"""
        combinations = []

        for result in results:
            stats = result.get('statistics', {})
            locations = stats.get('locations', {})
            temporal = stats.get('temporal', {})

            # Estrai caratteristiche dominanti
            dom_env = locations.get('most_common_environment')
            dom_period = temporal.get('most_common_period')
            dom_historical = list(temporal.get('historical_distribution', {}).keys())
            dom_historical = dom_historical[0] if dom_historical else 'contemporary'

            if dom_env and dom_period:
                combo = f"{dom_env}_{dom_period}_{dom_historical}"
                combinations.append(combo)

        combo_counter = Counter(combinations)
        return {
            'most_frequent': combo_counter.most_common(5),
            'total_unique_combinations': len(combo_counter)
        }

    def _identify_genre_patterns(self, results: List[Dict]) -> Dict[str, Any]:
        """Identifica pattern tipici di generi cinematografici"""
        patterns = {
            'sci_fi_indicators': 0,
            'fantasy_indicators': 0,
            'contemporary_drama': 0,
            'historical_pieces': 0
        }

        for result in results:
            stats = result.get('statistics', {})
            locations = stats.get('locations', {})
            temporal = stats.get('temporal', {})

            env_dist = locations.get('environment_distribution', {})
            hist_dist = temporal.get('historical_distribution', {})

            # Indicatori sci-fi
            if env_dist.get('space', 0) > 0 or hist_dist.get('future', 0) > 0:
                patterns['sci_fi_indicators'] += 1

            # Indicatori fantasy
            if env_dist.get('fantasy', 0) > 0 or hist_dist.get('medieval', 0) > 0:
                patterns['fantasy_indicators'] += 1

            # Drama contemporaneo
            if (env_dist.get('urban', 0) > 0 or env_dist.get('suburban', 0) > 0) and \
                    hist_dist.get('contemporary', 0) > 0:
                patterns['contemporary_drama'] += 1

            # Pezzi storici
            historical_periods = ['medieval', 'victorian', '1920s', '1960s', '1980s']
            if any(hist_dist.get(period, 0) > 0 for period in historical_periods):
                patterns['historical_pieces'] += 1

        total_films = len(results)
        return {
            'absolute_counts': patterns,
            'percentages': {k: round((v / total_films) * 100, 1) for k, v in patterns.items()},
            'dominant_genre_pattern': max(patterns, key=patterns.get) if patterns else None
        }

    def analyze_directory(self, tei_dir: str, output_file: str = 'analysis_results.json'):
        """Analizza tutti i file TEI in una directory"""
        results = []

        if not os.path.exists(tei_dir):
            print(f"Directory {tei_dir} non trovata")
            return

        tei_files = [f for f in os.listdir(tei_dir) if f.endswith('.xml')]

        for tei_file in tei_files:
            file_path = os.path.join(tei_dir, tei_file)
            print(f"Analizzando: {tei_file}")

            analysis = self.analyze_tei_file(file_path)
            results.append(analysis)

        # Salva risultati per singoli film
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        # Genera e salva statistiche macro
        macro_stats = self._calculate_macro_statistics(results)
        macro_output_file = output_file.replace('.json', '_macro_stats.json')

        with open(macro_output_file, 'w', encoding='utf-8') as f:
            json.dump(macro_stats, f, indent=2, ensure_ascii=False)

        print(f"Analisi completata. Risultati salvati in: {output_file}")
        print(f"Statistiche macro salvate in: {macro_output_file}")
        return results


def main():
    analyzer = TEIAnalyzer()

    # Analizza directory di file TEI
    results = analyzer.analyze_directory('output', 'screenplay_analysis.json')


if __name__ == "__main__":
    main()