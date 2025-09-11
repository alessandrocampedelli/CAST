import re
import json
import os
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
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

        self.historical_keywords = {
            'ancient': ['ancient', 'rome', 'greece', 'egypt', 'babylon', 'gladiator', 'colosseum', 'pharaoh', 'pyramid',
                        'temple', 'toga', 'chariot', 'caesar', 'emperor'],
            'medieval': ['medieval', 'castle', 'knight', 'sword', 'armor', 'kingdom', 'throne', 'king', 'queen',
                         'noble', 'peasant', 'feudal', 'crusade', 'monastery', 'cathedral', 'plague', 'blacksmith',
                         'minstrel'],
            'renaissance': ['renaissance', 'florence', 'venice', 'michelangelo', 'leonardo', 'art', 'painter',
                            'sculpture', 'patron', 'merchant', 'guild'],
            'victorian': ['victorian', '1800s', 'carriage', 'corset', 'gentleman', 'lady', 'gaslight', 'telegraph',
                          'steam', 'industrial', 'factory', 'chimney', 'top hat', 'parasol'],
            '1920s': ['1920', 'jazz', 'prohibition', 'flapper', 'speakeasy', 'charleston', 'gangster', 'bootlegger',
                      'radio', 'automobile', 'model t'],
            '1930s': ['1930', 'depression', 'dust bowl', 'new deal', 'hollywood', 'swing', 'art deco'],
            '1940s': ['1940', 'world war', 'wwii', 'nazi', 'hitler', 'churchill', 'roosevelt', 'rationing', 'victory',
                      'liberation', 'blitz'],
            '1950s': ['1950', 'suburban', 'television', 'rock roll', 'elvis', 'drive-in', 'diner', 'housewife',
                      'nuclear', 'cold war'],
            '1960s': ['1960', 'hippie', 'vietnam', 'beatles', 'woodstock', 'protest', 'civil rights', 'moon landing',
                      'kennedy', 'psychedelic'],
            '1970s': ['1970', 'disco', 'watergate', 'oil crisis', 'punk', 'afro', 'polyester', 'skateboard'],
            '1980s': ['1980', 'neon', 'arcade', 'walkman', 'disco', 'yuppie', 'mtv', 'personal computer', 'reagan',
                      'berlin wall'],
            '1990s': ['1990', 'internet', 'grunge', 'clinton', 'cell phone', 'cd', 'hip hop', 'dot com'],
            '2000s': ['2000', 'millennium', 'smartphone', 'social media', 'youtube', 'ipod', 'wifi', 'facebook'],
            'contemporary': ['smartphone', 'instagram', 'tesla', 'uber', 'airbnb', 'netflix', 'zoom', 'covid',
                             'pandemic', 'tiktok', 'iphone', 'android', 'laptop', 'tablet', 'wifi', 'bluetooth',
                             'streaming'],
            'future': ['future', 'robot', 'laser', 'spacecraft', 'cyberpunk', 'ai', '2050', 'hologram',
                       'virtual reality', 'android', 'cyborg', 'teleportation', 'time travel', 'dystopia', 'utopia']
        }

        # Liste di luoghi reali e immaginari
        self.real_places = {
            # Città principali del mondo
            'london', 'paris', 'new york', 'rome', 'tokyo', 'moscow', 'berlin',
            'madrid', 'sydney', 'cairo', 'mumbai', 'beijing', 'chicago',
            'los angeles', 'san francisco', 'miami', 'boston', 'seattle',
            'amsterdam', 'barcelona', 'vienna', 'prague', 'budapest',
            'istanbul', 'athens', 'lisbon', 'dublin', 'edinburgh',
            'stockholm', 'copenhagen', 'oslo', 'helsinki',
            # Stati e regioni
            'california', 'texas', 'florida', 'new york state', 'italy', 'france',
            'germany', 'spain', 'england', 'scotland', 'ireland', 'wales',
            'australia', 'canada', 'japan', 'china', 'india', 'brazil',
            # Luoghi geografici famosi
            'alps', 'himalayas', 'sahara', 'amazon', 'mississippi', 'nile',
            'mediterranean', 'atlantic', 'pacific', 'indian ocean',
            'mount everest', 'grand canyon', 'niagara falls'
        }

        self.imaginary_places = {
            # Fantasy
            'hogwarts', 'rivendell', 'mordor', 'narnia', 'middle earth',
            'atlantis', 'asgard', 'valhalla', 'olympus', 'camelot',
            'neverland', 'wonderland', 'oz', 'shangri-la',
            # Sci-fi
            'gotham', 'metropolis', 'wakanda', 'pandora', 'tatooine',
            'vulcan', 'krypton', 'coruscant', 'endor',
            # Altri universi finzionali
            'westeros', 'essos', 'middle-earth', 'discworld'
        }

        # Indicatori geografici reali
        self.real_place_indicators = {
            'airport', 'international', 'highway', 'interstate', 'state',
            'university', 'college', 'hospital', 'museum', 'embassy',
            'consulate', 'border', 'customs', 'passport', 'visa'
        }

        # Indicatori fantastici
        self.fantasy_indicators = {
            'magical', 'enchanted', 'mystical', 'supernatural', 'otherworldly',
            'dimension', 'realm', 'parallel universe', 'alternate reality'
        }

    def _analyze_location(self, location_text: str, stage_texts: List[str]) -> LocationInfo:
        """Analisi dei luoghi"""
        location_info = LocationInfo()

        # STEP 1: Pattern cinematografici standard
        location_upper = location_text.upper()

        #Estrai INT/EXT
        if location_upper.startswith('INT') or 'INT.' in location_upper:
            location_info.type = 'INT'
        elif location_upper.startswith('EXT') or 'EXT.' in location_upper:
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

        #Determina setting generale
        if location_info.environment in ['space', 'fantasy']:
            location_info.setting = 'fantasy/sci-fi'
        elif location_info.environment in ['urban', 'suburban']:
            location_info.setting = 'contemporary'
        elif location_info.environment in ['sea', 'mountain', 'desert', 'rural']:
            location_info.setting = 'natural'
        else:
            location_info.setting = 'unspecified'

        # STEP 3: Verifica geografica
        location_info.real_imaginary = self._determine_reality_type(location_text, stage_texts, location_info)

        return location_info

    def _determine_reality_type(self, location_text: str, stage_texts: List[str], location_info: LocationInfo) -> str:
        """Determina se un luogo è reale o immaginario"""
        all_text = (location_text + ' ' + ' '.join(stage_texts)).lower()

        # Punteggi per reale vs immaginario
        real_score = 0
        imaginary_score = 0

        # Verifica luoghi esplicitamente reali
        for place in self.real_places:
            if place in all_text:
                # Punteggio maggiore per match esatti
                real_score += 5

        # Verifica luoghi esplicitamente immaginari
        for place in self.imaginary_places:
            if place in all_text:
                imaginary_score += 5

        # Indicatori di luoghi reali
        for indicator in self.real_place_indicators:
            if indicator in all_text:
                real_score += 2

        # Indicatori fantastici
        for indicator in self.fantasy_indicators:
            if indicator in all_text:
                imaginary_score += 3

        # Logica basata sull'ambiente
        if location_info.environment == 'fantasy':
            imaginary_score += 3
        elif location_info.environment == 'space':
            # Space può essere reale (ISS, NASA) o immaginario
            if any(word in all_text for word in ['nasa', 'iss', 'houston', 'kennedy', 'cape canaveral']):
                real_score += 2
            else:
                imaginary_score += 1
        elif location_info.environment in ['urban', 'suburban']:
            real_score += 1

        # Pattern linguistici che indicano luoghi reali
        real_patterns = [
            r'\b\d+\s+(street|avenue|road|boulevard|drive|lane)\b',
            r'\b(north|south|east|west|downtown|uptown)\b',
            r'\b(state|county|district|province)\b',
        ]

        for pattern in real_patterns:
            if re.search(pattern, all_text, re.IGNORECASE):
                real_score += 2

        # Decisione finale
        if real_score > imaginary_score:
            return 'real'
        elif imaginary_score > real_score:
            return 'imaginary'
        else:
            # Se i punteggi sono uguali, usa euristica basata sull'ambiente
            if location_info.environment in ['fantasy', 'space']:
                return 'imaginary'
            elif location_info.environment in ['urban', 'suburban']:
                return 'real'
            else:
                return 'unknown'

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

                score = 0
                # controllo se ogni parola chiave è contenuta nel testo. Se si aggiungo un al punteggio.
                # ottengo cosi per ogni stagione, il numero di parole chiave associate trovate nel testo
                for keyword in keywords:
                    occurrences = all_text.count(keyword)
                    if occurrences > 0:
                        weight = 2 if len(keyword) > 5 else 1
                        score += occurrences * weight

                if score > 0:
                    #assegno ad ogni stagione il numero di keywords relative trovate nel testo
                    season_scores[season] = score

        #per stabilire la stagione corretta, scelgo la stagione con il numero di occorrenze di parole chiave maggiore
        if season_scores:
            temporal_info.season = max(season_scores, key=season_scores.get)

        # Analisi storica con logica gerarchica
        temporal_info.historical = self._determine_historical_period(all_text)

        return temporal_info

    def _determine_historical_period(self, text: str) -> str:
        """Determina il periodo storico con logica migliorata"""
        period_scores = {}

        # Prima verifica: indicatori espliciti di periodo
        for period, keywords in self.historical_keywords.items():
            score = 0
            for keyword in keywords:
                occurrences = text.count(keyword)
                if occurrences > 0:
                    # Pesi diversi per diversi tipi di indicatori
                    if any(year in keyword for year in
                           ['1920', '1930', '1940', '1950', '1960', '1970', '1980', '1990', '2000']):
                        weight = 5  # Anni specifici hanno peso massimo
                    elif keyword in ['medieval', 'victorian', 'renaissance', 'ancient']:
                        weight = 4  # Periodi storici ben definiti
                    elif keyword in ['contemporary', 'modern', 'future']:
                        weight = 3  # Periodi generali
                    else:
                        weight = 1  # Altri indicatori

                    score += occurrences * weight

            if score > 0:
                period_scores[period] = score

        #scelgo il periodo storico che ha più occorrenze di parole chiave trovate
        if not period_scores:
            # Verifica tecnologie moderne
            modern_tech = ['smartphone', 'computer', 'internet', 'car', 'phone', 'tv', 'radio']
            if any(tech in text for tech in modern_tech):
                return 'contemporary'

            # Verifica indicatori storici generici
            historical_terms = ['old', 'ancient', 'historical', 'traditional', 'classic']
            if any(term in text for term in historical_terms):
                return 'medieval'  # Fallback generico per "storico"

            # Default
            return 'contemporary'

        # Ritorna il periodo con punteggio più alto
        best_period = max(period_scores, key=period_scores.get)

        # Post-processing: risolvi conflitti comuni
        if best_period == 'modern' and period_scores.get('contemporary', 0) > 0:
            # Se sia "modern" che "contemporary" sono presenti, preferisci il più recente
            if period_scores['contemporary'] >= period_scores['modern'] * 0.8:
                return 'contemporary'

        return best_period

    # [Il resto dei metodi rimane uguale: analyze_tei_file, _analyze_scene, _calculate_statistics, etc.]
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
            temporal=temporal_info,
            raw_location_text=raw_location_text,
            stage_texts=stage_texts
        )

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
            historical_periods = ['medieval', 'victorian', '1920s', '1960s', '1980s', 'ancient', 'renaissance']
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
    results = analyzer.analyze_directory('output', 'screenplay_analysis.json')


if __name__ == "__main__":
    main()