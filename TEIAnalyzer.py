import json
import os
import xml.etree.ElementTree as ET
from collections import Counter
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, List, Optional, Any


@dataclass
class LocationInfo:
    """Informazioni estratte sui luoghi"""
    type: Optional[str] = None  # INT/EXT
    setting: Optional[str] = None  # suburban, fantasy, etc.
    environment: Optional[str] = None  # sea, mountain, urban, etc


@dataclass
class TemporalInfo:
    """Informazioni estratte sui tempi"""
    period: Optional[str] = None  # DAY/NIGHT/MORNING/EVENING
    season: Optional[str] = None  # winter/spring/summer/autumn


@dataclass
class SceneAnalysis:
    """Analisi completa di una scena"""
    scene_n: str
    location: LocationInfo
    temporal: TemporalInfo


class TEIAnalyzer:
    """Analizzatore principale per file TEI"""

    def __init__(self):
        # Dizionari migliorati per classificazione
        self.environment_keywords = {
            'sea': ['ocean', 'sea', 'beach', 'coast', 'waves', 'harbor', 'port', 'ship', 'boat', 'pier', 'marina',
                    'wharf', 'dock', 'seaside', 'shoreline', 'naval', 'yacht', 'submarine', 'lighthouse'],
            'mountain': ['mountain', 'hill', 'peak', 'cliff', 'valley', 'cave', 'rock', 'ridge', 'summit', 'alpine',
                         'slope', 'canyon', 'gorge', 'boulder', 'crag'],
            'urban': ['city', 'street', 'building', 'apartment', 'office', 'shop', 'mall', 'downtown', 'skyscraper',
                      'plaza', 'square', 'avenue', 'boulevard', 'metropolis', 'sidewalk', 'crosswalk', 'intersection',
                      'alley', 'penthouse', 'loft'],
            'suburban': ['house', 'home', 'neighborhood', 'garden', 'yard', 'driveway', 'suburb', 'residential', 'lawn',
                         'garage', 'porch', 'backyard', 'frontyard', 'cul-de-sac', 'picket fence'],
            'rural': ['farm', 'field', 'countryside', 'barn', 'village', 'meadow', 'forest', 'woods', 'ranch',
                      'pasture', 'orchard', 'farmhouse', 'stable', 'grain', 'harvest', 'tractor', 'cow', 'sheep'],
            'desert': ['desert', 'sand', 'dune', 'oasis', 'wasteland', 'arid', 'cactus', 'mirage', 'sandstorm',
                       'nomad'],
            'space': ['space', 'spaceship', 'planet', 'moon', 'galaxy', 'asteroid', 'orbit', 'spacecraft', 'satellite',
                      'cosmos', 'alien', 'mars', 'jupiter', 'venus', 'solar system', 'nebula', 'starship'],
            'fantasy': ['castle', 'dungeon', 'tower', 'magical', 'enchanted', 'wizard', 'dragon', 'fairy', 'goblin',
                        'elf', 'dwarf', 'magic', 'spell', 'potion', 'kingdom', 'realm', 'tavern', 'inn', 'quest']
        }

        self.time_keywords = {
            'morning': ['morning', 'dawn', 'sunrise', 'early', 'breakfast', 'am', 'daybreak', 'cockcrow'],
            'day': ['day', 'noon', 'afternoon', 'midday', 'daylight', 'lunch', 'pm', 'sunny', 'bright'],
            'evening': ['evening', 'sunset', 'dusk', 'twilight', 'dinner', 'supper', 'late afternoon'],
            'night': ['night', 'midnight', 'darkness', 'moonlight', 'stars', 'nocturnal', 'late night', 'bedtime',
                      'sleeping'],
            'winter': ['snow', 'ice', 'cold', 'winter', 'frost', 'christmas', 'freezing', 'blizzard', 'snowfall',
                       'icicle', 'december', 'january', 'february'],
            'spring': ['spring', 'flowers', 'bloom', 'rain', 'easter', 'march', 'april', 'may', 'blossom', 'tulip',
                       'daffodil'],
            'summer': ['summer', 'hot', 'sun', 'heat', 'vacation', 'beach', 'june', 'july', 'august', 'swimming',
                       'sunbathing', 'barbecue'],
            'autumn': ['autumn', 'fall', 'leaves', 'harvest', 'october', 'november', 'september', 'pumpkin',
                       'thanksgiving', 'foliage', 'rake']
        }

    def _analyze_location(self, location_text: str, stage_texts: List[str]) -> LocationInfo:
        """Analisi dei luoghi"""
        location_info = LocationInfo()

        # STEP 1: Pattern cinematografici standard
        location_upper = location_text.upper()

        # Estrai INT/EXT
        if location_upper.startswith('INT') or 'INT.' in location_upper:
            location_info.type = 'INT'
        elif location_upper.startswith('EXT') or 'EXT.' in location_upper:
            location_info.type = 'EXT'

        # STEP 2: Analisi semantica
        all_text = (location_text + ' ' + ' '.join(stage_texts)).lower()

        # dizionario vuoto che conterrà per ogni ambiente prestabilito, quante parole chiave sono state trovate
        # nella scena
        environment_scores = {}

        # scorro su tutti i tipi di ambienti definiti nel dizionario
        # env_type: stringa che rappresenta il tipo di ambiente
        # keywords: lista di parole associate a quell'ambiente
        for env_type, keywords in self.environment_keywords.items():
            score = 0
            for keyword in keywords:
                # Conta occorrenze multiple della stessa parola chiave
                occurrences = all_text.count(keyword)
                if occurrences > 0:
                    # Peso maggiore per parole più specifiche
                    weight = len(keyword.split()) * 2 if ' ' in keyword else 1
                    score += occurrences * weight

            # se è stata trovata almeno una parola chiave con almeno una occorrenza, memorizzo il risultato
            # chiave: tipo ambiente; valore: punteggio
            if score > 0:
                environment_scores[env_type] = score

        if environment_scores:
            # imposto come environment quello che ha il punteggio più alto nel dizionario
            location_info.environment = max(environment_scores, key=environment_scores.get)

        # Determina setting generale
        if location_info.environment in ['space', 'fantasy']:
            location_info.setting = 'fantasy/sci-fi'
        elif location_info.environment in ['urban', 'suburban']:
            location_info.setting = 'contemporary'
        elif location_info.environment in ['sea', 'mountain', 'desert', 'rural']:
            location_info.setting = 'natural'
        else:
            location_info.setting = 'unspecified'

        return location_info

    def _analyze_temporal(self, location_text: str, stage_texts: List[str]) -> TemporalInfo:
        """Analisi temporale migliorata con logica più sofisticata"""
        temporal_info = TemporalInfo()
        all_text = (location_text + ' ' + ' '.join(stage_texts)).lower()

        # Analizza periodo giornaliero con pesi
        time_scores = {}
        for time_type, keywords in self.time_keywords.items():
            if time_type in ['morning', 'day', 'evening', 'night']:
                score = 0
                # controllo se ogni parola chiave è contenuta nel testo, se si aggiungo uno al conteggio
                for keyword in keywords:
                    occurrences = all_text.count(keyword)
                    if occurrences > 0:
                        # Peso maggiore per termini più specifici
                        weight = 2 if len(keyword) > 5 else 1
                        score += occurrences * weight

                if score > 0:
                    # per ogni fase della giornata assegno quante parole chiave sono state trovate nella scena
                    time_scores[time_type] = score

        # per decretare il vero momento della giornata, viene selezionato il momento che ha più occorrenze di parole
        # chiave associate nel testo della scena
        if time_scores:
            temporal_info.period = max(time_scores, key=time_scores.get).upper()

        season_scores = {}

        # scorro tutti i tipi di tempo (stagioni)
        for season, keywords in self.time_keywords.items():
            if season in ['winter', 'spring', 'summer', 'autumn']:

                score = 0
                # controllo se ogni parola chiave è contenuta nel testo. Se si aggiungo un al punteggio.
                # ottengo cosi per ogni stagione, il numero di parole chiave associate trovate nel testo
                for keyword in keywords:
                    occurrences = all_text.count(keyword)
                    if occurrences > 0:
                        weight = 2 if len(keyword) > 5 else 1
                        score += occurrences * weight

                if score > 0:
                    # assegno ad ogni stagione il numero di keywords relative trovate nel testo
                    season_scores[season] = score

        # per stabilire la stagione corretta, scelgo la stagione con il numero di occorrenze di parole chiave maggiore
        if season_scores:
            temporal_info.season = max(season_scores, key=season_scores.get)

        return temporal_info

    def analyze_tei_file(self, file_path: str) -> Dict[str, Any]:
        """Analizza un file TEI completo"""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()

            title_elem = root.find('.//{http://www.tei-c.org/ns/1.0}title')
            title = title_elem.text if title_elem is not None else os.path.basename(file_path)

            scenes = []
            scene_divs = root.findall('.//{http://www.tei-c.org/ns/1.0}div[@type="scene"]')

            for scene_div in scene_divs:
                scene_analysis = self._analyze_scene(scene_div)
                if scene_analysis:
                    scenes.append(asdict(scene_analysis))

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
        scene_n = scene_div.get('n', 'unknown')

        location_stage = scene_div.find('.//{http://www.tei-c.org/ns/1.0}stage[@type="location"]')
        raw_location_text = location_stage.text if location_stage is not None else ""

        stage_elements = scene_div.findall('.//{http://www.tei-c.org/ns/1.0}stage')
        stage_texts = [elem.text for elem in stage_elements if elem.text]

        location_info = self._analyze_location(raw_location_text, stage_texts)
        temporal_info = self._analyze_temporal(raw_location_text, stage_texts)

        return SceneAnalysis(
            scene_n=scene_n,
            location=location_info,
            temporal=temporal_info
        )

    def _calculate_statistics(self, scenes: List[Dict]) -> Dict[str, Any]:
        """Calcola statistiche aggregate del film"""
        # prende in input una lista di dizionari, ognuno dei quali contiene le info di una scena
        if not scenes:
            return {}

        # Statistiche sui luoghi. Liste di n elementi (n scene del film)

        # lista nella quale, per ogni cella, è salvata l'informazione di INT o EXT
        location_types = [s['location']['type'] for s in scenes if s['location']['type']]

        # lista nella quale, per ogni cella, è salvata l'informazione del tipo di enviroment
        environments = [s['location']['environment'] for s in scenes if s['location']['environment']]

        # Statistiche temporali. Liste di n elementi (n scene: somma di tutte le scene dei film analizzati)

        # lista nella quale, per ogni cella, è salvata l'informazione relativo al periodo della giornata
        periods = [s['temporal']['period'] for s in scenes if s['temporal']['period']]

        # lista nella quale, per ogni cella, è salvata l'informazione relativo alla stagione della scena
        seasons = [s['temporal']['season'] for s in scenes if s['temporal']['season']]

        return {
            'locations': {
                'int_ext_distribution': dict(Counter(location_types)),
                'environment_distribution': dict(Counter(environments)),
                'most_common_environment': Counter(environments).most_common(1)[0][0] if environments else None
            },
            'temporal': {
                'day_night_distribution': dict(Counter(periods)),
                'season_distribution': dict(Counter(seasons)),
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
        all_periods = []
        all_seasons = []

        film_summaries = []

        for result in valid_results:
            stats = result.get('statistics', {})

            # Estrai dati location
            locations = stats.get('locations', {})
            int_ext = locations.get('int_ext_distribution', {})
            environments = locations.get('environment_distribution', {})

            # Estrai dati temporali
            temporal = stats.get('temporal', {})
            periods = temporal.get('day_night_distribution', {})
            seasons = temporal.get('season_distribution', {})

            # Aggiungi ai totali
            for location_type, count in int_ext.items():
                all_location_types.extend([location_type] * count)

            for env, count in environments.items():
                all_environments.extend([env] * count)

            for period, count in periods.items():
                all_periods.extend([period] * count)

            for season, count in seasons.items():
                all_seasons.extend([season] * count)

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
        period_counter = dict(Counter(all_periods))
        season_counter = dict(Counter(all_seasons))

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
                    'most_common_overall': {
                        'location_type': Counter(all_location_types).most_common(1)[0][
                            0] if all_location_types else None,
                        'environment': Counter(all_environments).most_common(1)[0][0] if all_environments else None,
                    }
                },
                'temporal': {
                    'period_totals': period_counter,
                    'period_percentages': calculate_percentages(period_counter,
                                                                sum(period_counter.values())) if period_counter else {},
                    'season_totals': season_counter,
                    'season_percentages': calculate_percentages(season_counter,
                                                                sum(season_counter.values())) if season_counter else {},
                    'most_common_overall': {
                        'period': Counter(all_periods).most_common(1)[0][0] if all_periods else None,
                        'season': Counter(all_seasons).most_common(1)[0][0] if all_seasons else None
                    }
                }
            },
            'films_summary': film_summaries
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
            'contemporary_drama': 0
        }

        for result in results:
            stats = result.get('statistics', {})
            locations = stats.get('locations', {})

            env_dist = locations.get('environment_distribution', {})

        total_films = len(results)
        return {
            'absolute_counts': patterns,
            'percentages': {k: round((v / total_films) * 100, 1) for k, v in patterns.items()},
            'dominant_genre_pattern': max(patterns, key=patterns.get) if patterns else None
        }

    def analyze_directory(self, tei_dir: str, output_file: str = 'screenplay_analysis.json'):
        """Analizza tutti i file TEI in una directory e salva i risultati nella cartella analysis"""
        results = []

        if not os.path.exists(tei_dir):
            print(f"Directory {tei_dir} non trovata")
            return

        # Crea la cartella analysis se non esiste
        analysis_dir = 'analysis'
        if not os.path.exists(analysis_dir):
            os.makedirs(analysis_dir)
            print(f"Cartella '{analysis_dir}' creata")

        tei_files = [f for f in os.listdir(tei_dir) if f.endswith('.xml')]

        for tei_file in tei_files:
            file_path = os.path.join(tei_dir, tei_file)
            print(f"Analizzando: {tei_file}")

            analysis = self.analyze_tei_file(file_path)
            results.append(analysis)

        # Percorso completo per i file di tei_scripts nella cartella analysis
        output_path = os.path.join(analysis_dir, output_file)
        macro_output_file = output_file.replace('.json', '_macro_stats.json')
        macro_output_path = os.path.join(analysis_dir, macro_output_file)

        # Salva risultati per singoli film
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        # Genera e salva statistiche macro
        macro_stats = self._calculate_macro_statistics(results)

        with open(macro_output_path, 'w', encoding='utf-8') as f:
            json.dump(macro_stats, f, indent=2, ensure_ascii=False)

        print(f"Analisi completata. Risultati salvati in: {output_path}")
        print(f"Statistiche macro salvate in: {macro_output_path}")
        return results


def main():
    analyzer = TEIAnalyzer()
    analyzer.analyze_directory('tei_scripts', 'screenplay_analysis.json')


if __name__ == "__main__":
    main()