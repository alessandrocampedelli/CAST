import json
import os
import xml.etree.ElementTree as ET
from collections import Counter
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, List, Optional, Any
from nltk.corpus import wordnet as wn


@dataclass
class LocationInfo:
    """Informazioni estratte sui luoghi"""
    type: Optional[str] = None
    setting: Optional[str] = None
    environment: Optional[str] = None


@dataclass
class TemporalInfo:
    """Informazioni estratte sui tempi"""
    period: Optional[str] = None
    season: Optional[str] = None


@dataclass
class SceneAnalysis:
    """Analisi completa di una scena"""
    scene_n: str
    location: LocationInfo
    temporal: TemporalInfo


class TEIAnalyzer:
    """Analizzatore principale per file TEI con filtri anti-rumore"""

    def __init__(self, expand_with_wordnet: bool = True, max_synonyms: int = 3):
        """
        Inizializza l'analizzatore
        """
        self.max_synonyms = max_synonyms

        # CORE KEYWORDS - Alta priorità, peso maggiore
        self.core_keywords = {
            'sea': ['ocean', 'sea', 'beach', 'ship', 'boat', 'submarine'],
            'mountain': ['mountain', 'hill', 'peak', 'cliff', 'cave'],
            'urban': ['city', 'street', 'building', 'downtown', 'skyscraper'],
            'suburban': ['house', 'home', 'neighborhood', 'suburb', 'garage'],
            'rural': ['farm', 'field', 'countryside', 'barn', 'village'],
            'desert': ['desert', 'sand', 'dune', 'oasis'],
            'space': ['space', 'spaceship', 'planet', 'galaxy', 'spacecraft'],
            'fantasy': ['castle', 'dungeon', 'wizard', 'dragon', 'magic']
        }

        # EXTENDED KEYWORDS - Bassa priorità, peso minore
        self.environment_keywords = {
            'sea': ['waves', 'harbor', 'port', 'pier', 'marina', 'wharf', 'dock',
                    'seaside', 'shoreline', 'naval', 'yacht', 'lighthouse'],
            'mountain': ['valley', 'rock', 'ridge', 'summit', 'alpine', 'slope',
                         'canyon', 'gorge', 'boulder', 'crag'],
            'urban': ['apartment', 'office', 'shop', 'mall', 'plaza', 'square',
                      'avenue', 'boulevard', 'metropolis', 'sidewalk', 'crosswalk',
                      'intersection', 'alley', 'penthouse', 'loft'],
            'suburban': ['garden', 'yard', 'driveway', 'residential', 'lawn',
                         'porch', 'backyard', 'frontyard', 'cul-de-sac', 'picket fence'],
            'rural': ['meadow', 'forest', 'woods', 'ranch', 'pasture', 'orchard',
                      'farmhouse', 'stable', 'grain', 'harvest', 'tractor', 'cow', 'sheep'],
            'desert': ['wasteland', 'arid', 'cactus', 'mirage', 'sandstorm', 'nomad'],
            'space': ['moon', 'asteroid', 'orbit', 'satellite', 'cosmos', 'alien',
                      'mars', 'jupiter', 'venus', 'solar system', 'nebula', 'starship'],
            'fantasy': ['tower', 'magical', 'enchanted', 'fairy', 'goblin', 'elf',
                        'dwarf', 'spell', 'potion', 'kingdom', 'realm', 'tavern', 'inn', 'quest']
        }

        self.blacklist = {
            'general': ['place', 'area', 'location', 'site', 'spot', 'position',
                        'room', 'space', 'time', 'day', 'way', 'thing', 'part'],
            'urban_noise': ['center', 'point', 'line', 'side', 'end', 'back',
                            'front', 'top', 'bottom', 'inside', 'outside'],
            'false_positives': ['character', 'scene', 'act', 'stage']
        }

        # Unisce tutte le blacklist
        self.all_blacklist = set()
        for category in self.blacklist.values():
            self.all_blacklist.update(category)

        # Keyword temporali
        self.time_keywords = {
            'morning': ['morning', 'dawn', 'sunrise', 'early', 'breakfast', 'am', 'daybreak'],
            'day': ['day', 'noon', 'afternoon', 'midday', 'daylight', 'lunch', 'pm', 'sunny', 'bright'],
            'evening': ['evening', 'sunset', 'dusk', 'twilight', 'dinner', 'supper'],
            'night': ['night', 'midnight', 'darkness', 'moonlight', 'stars', 'nocturnal'],
            'winter': ['snow', 'ice', 'cold', 'winter', 'frost', 'christmas', 'freezing',
                       'blizzard', 'december', 'january', 'february'],
            'spring': ['spring', 'flowers', 'bloom', 'rain', 'easter', 'march', 'april',
                       'may', 'blossom', 'tulip'],
            'summer': ['summer', 'hot', 'sun', 'heat', 'vacation', 'beach', 'june', 'july',
                       'august', 'swimming'],
            'autumn': ['autumn', 'fall', 'leaves', 'harvest', 'october', 'november',
                       'september', 'pumpkin', 'thanksgiving']
        }

        # Espansione con WordNet (controllata)
        if expand_with_wordnet:
            self._expand_keywords_with_wordnet()

    def _is_valid_synonym(self, word: str, original_word: str) -> bool:
        """
        Filtra sinonimi non validi
        """
        word_lower = word.lower()

        # 1. Controlla blacklist
        if word_lower in self.all_blacklist:
            return False

        # 2. Troppo corto (< 3 caratteri)
        if len(word_lower) < 3:
            return False

        # 3. Troppo generico (contiene numeri o caratteri speciali)
        if not word_lower.replace('_', '').replace('-', '').isalpha():
            return False

        # 4. Troppo diverso dalla parola originale (controllo similarità)
        if len(word_lower) > len(original_word) * 2:
            return False

        return True

    def _expand_keywords_with_wordnet(self):
        """Espande i dizionari con sinonimi WordNet filtrati"""

        def expand_list(words: List[str], max_syn: int) -> List[str]:
            expanded = set(words)  # Mantiene le parole originali

            for word in words:
                synonyms = set()

                # Ottiene synset per la parola
                for syn in wn.synsets(word):
                    for lemma in syn.lemmas():
                        synonym = lemma.name().replace("_", " ")

                        # Applica filtri
                        if self._is_valid_synonym(synonym, word):
                            synonyms.add(synonym)

                # Limita numero di sinonimi per parola
                expanded.update(list(synonyms)[:max_syn])

            return list(expanded)

        # Espande solo extended keywords (non core)
        for env, keywords in self.environment_keywords.items():
            self.environment_keywords[env] = expand_list(keywords, self.max_synonyms)

        # Espande temporal keywords
        for time_key, keywords in self.time_keywords.items():
            self.time_keywords[time_key] = expand_list(keywords, self.max_synonyms)

    def _calculate_environment_score(self, text: str, env_type: str) -> float:
        """
        Calcola score pesato per un ambiente
        """
        score = 0.0

        # CORE KEYWORDS - Peso 3x
        for keyword in self.core_keywords.get(env_type, []):
            occurrences = text.count(keyword)
            if occurrences > 0:
                weight = 3.0 * (len(keyword.split()) * 2 if ' ' in keyword else 1)
                score += occurrences * weight

        # EXTENDED KEYWORDS - Peso 1x
        for keyword in self.environment_keywords.get(env_type, []):
            occurrences = text.count(keyword)
            if occurrences > 0:
                weight = len(keyword.split()) * 2 if ' ' in keyword else 1
                score += occurrences * weight

        return score

    def _apply_disambiguation_rules(self, scores: Dict[str, float], text: str) -> Dict[str, float]:
        """
        Applica regole di disambiguazione per risolvere conflitti
        """
        # Regola 1: Se "sea" e "beach" presenti → favorisce sea
        if 'sea' in text or 'beach' in text:
            scores['sea'] = scores.get('sea', 0) * 1.5

        # Regola 2: Se "mountain" e "cave" presenti → favorisce mountain
        if 'mountain' in text or 'cave' in text:
            scores['mountain'] = scores.get('mountain', 0) * 1.5

        # Regola 3: Se "space" e "planet" presenti → favorisce space
        if 'space' in text or 'planet' in text:
            scores['space'] = scores.get('space', 0) * 1.5

        # Regola 4: Penalizza urban se score troppo vicino ad altri
        if 'urban' in scores:
            other_scores = [s for e, s in scores.items() if e != 'urban' and s > 0]
            if other_scores and max(other_scores) > scores['urban'] * 0.7:
                scores['urban'] *= 0.8

        return scores

    def _analyze_location(self, location_text: str, stage_texts: List[str]) -> LocationInfo:
        """Analisi location con filtri anti-rumore"""
        location_info = LocationInfo()

        # STEP 1: Estrai INT/EXT
        location_upper = location_text.upper()
        if location_upper.startswith('INT') or 'INT.' in location_upper:
            location_info.type = 'INT'
        elif location_upper.startswith('EXT') or 'EXT.' in location_upper:
            location_info.type = 'EXT'
        else:
            location_info.type = 'UNKNOWN'

        # STEP 2: Analisi semantica con score pesati
        all_text = (location_text + ' ' + ' '.join(stage_texts)).lower()

        environment_scores = {}

        # Calcola score per ogni ambiente
        for env_type in self.core_keywords.keys():
            score = self._calculate_environment_score(all_text, env_type)
            if score > 0:
                environment_scores[env_type] = score

        # Applica regole di disambiguazione
        if environment_scores:
            environment_scores = self._apply_disambiguation_rules(environment_scores, all_text)

        # STEP 3: Soglia minima per classificazione
        MIN_SCORE_THRESHOLD = 2.0  # Score minimo per essere considerato valido

        if environment_scores:
            max_score = max(environment_scores.values())

            # Se lo score massimo è troppo basso → unknown
            if max_score < MIN_SCORE_THRESHOLD:
                location_info.environment = 'unknown'
            else:
                # Verifica che il vincitore sia significativamente superiore al secondo
                sorted_scores = sorted(environment_scores.items(), key=lambda x: x[1], reverse=True)

                if len(sorted_scores) > 1:
                    first_score = sorted_scores[0][1]
                    second_score = sorted_scores[1][1]

                    # Se la differenza è < 20% → troppo ambiguo → unknown
                    if second_score > first_score * 0.8:
                        location_info.environment = 'unknown'
                    else:
                        location_info.environment = sorted_scores[0][0]
                else:
                    location_info.environment = sorted_scores[0][0]
        else:
            location_info.environment = 'unknown'

        # Determina setting
        if location_info.environment in ['space', 'fantasy']:
            location_info.setting = 'fantasy/sci-fi'
        elif location_info.environment in ['urban', 'suburban']:
            location_info.setting = 'contemporary'
        elif location_info.environment in ['sea', 'mountain', 'desert', 'rural']:
            location_info.setting = 'natural'
        else:
            location_info.setting = 'unknown'

        return location_info

    def _analyze_temporal(self, location_text: str, stage_texts: List[str]) -> TemporalInfo:
        """Analisi temporale"""
        temporal_info = TemporalInfo()
        all_text = (location_text + ' ' + ' '.join(stage_texts)).lower()

        # Periodo del giorno
        time_scores = {}
        for time_type, keywords in self.time_keywords.items():
            if time_type in ['morning', 'day', 'evening', 'night']:
                score = 0
                for keyword in keywords:
                    occurrences = all_text.count(keyword)
                    if occurrences > 0:
                        weight = 2 if len(keyword) > 5 else 1
                        score += occurrences * weight
                if score > 0:
                    time_scores[time_type] = score

        temporal_info.period = max(time_scores, key=time_scores.get).upper() if time_scores else 'UNKNOWN'

        # Stagione
        season_scores = {}
        for season, keywords in self.time_keywords.items():
            if season in ['winter', 'spring', 'summer', 'autumn']:
                score = 0
                for keyword in keywords:
                    occurrences = all_text.count(keyword)
                    if occurrences > 0:
                        weight = 2 if len(keyword) > 5 else 1
                        score += occurrences * weight
                if score > 0:
                    season_scores[season] = score

        temporal_info.season = max(season_scores, key=season_scores.get) if season_scores else 'unknown'

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
        if not scenes:
            return {}

        location_types = [s['location']['type'] for s in scenes if s['location']['type']]
        environments = [s['location']['environment'] for s in scenes if s['location']['environment']]
        periods = [s['temporal']['period'] for s in scenes if s['temporal']['period']]
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
        """Calcola statistiche aggregate per tutti i film"""
        valid_results = [r for r in all_results if 'error' not in r]

        if not valid_results:
            return {'error': 'Nessun file valido analizzato'}

        total_films = len(valid_results)
        total_scenes = sum(r['total_scenes'] for r in valid_results)

        all_location_types = []
        all_environments = []
        all_periods = []
        all_seasons = []
        film_summaries = []

        for result in valid_results:
            stats = result.get('statistics', {})
            locations = stats.get('locations', {})
            temporal = stats.get('temporal', {})

            for location_type, count in locations.get('int_ext_distribution', {}).items():
                all_location_types.extend([location_type] * count)

            for env, count in locations.get('environment_distribution', {}).items():
                all_environments.extend([env] * count)

            for period, count in temporal.get('day_night_distribution', {}).items():
                all_periods.extend([period] * count)

            for season, count in temporal.get('season_distribution', {}).items():
                all_seasons.extend([season] * count)

            film_summaries.append({
                'film': result['film'],
                'scenes': result['total_scenes'],
                'dominant_environment': locations.get('most_common_environment'),
                'dominant_period': temporal.get('most_common_period')
            })

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

    def analyze_directory(self, tei_dir: str, output_file: str = 'screenplay_analysis.json'):
        """Analizza tutti i file TEI in una directory"""
        results = []

        if not os.path.exists(tei_dir):
            print(f"Directory {tei_dir} non trovata")
            return

        analysis_dir = 'analysis'
        if not os.path.exists(analysis_dir):
            os.makedirs(analysis_dir)

        tei_files = [f for f in os.listdir(tei_dir) if f.endswith('.xml')]

        for tei_file in tei_files:
            file_path = os.path.join(tei_dir, tei_file)
            print(f"Analizzando: {tei_file}")

            analysis = self.analyze_tei_file(file_path)
            results.append(analysis)

        output_path = os.path.join(analysis_dir, output_file)
        macro_output_file = output_file.replace('.json', '_macro_stats.json')
        macro_output_path = os.path.join(analysis_dir, macro_output_file)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        macro_stats = self._calculate_macro_statistics(results)

        with open(macro_output_path, 'w', encoding='utf-8') as f:
            json.dump(macro_stats, f, indent=2, ensure_ascii=False)

        print(f"Analisi completata. Risultati salvati in: {output_path}")
        print(f"Statistiche macro salvate in: {macro_output_path}")
        return results


def main():
    # CONFIGURAZIONE PERSONALIZZABILE
    analyzer = TEIAnalyzer(
        expand_with_wordnet=True,
        max_synonyms=50
    )

    analyzer.analyze_directory('tei_scripts', 'screenplay_analysis.json')


if __name__ == "__main__":
    main()