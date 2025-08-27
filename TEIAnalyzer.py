import re
import json
import os
import xml.etree.ElementTree as ET
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
            tree = ET.parse(file_path)
            root = tree.getroot()

            # Estrai titolo
            title_elem = root.find('.//{http://www.tei-c.org/ns/1.0}title')
            title = title_elem.text if title_elem is not None else os.path.basename(file_path)

            # Analizza tutte le scene
            scenes = []
            scene_divs = root.findall('.//{http://www.tei-c.org/ns/1.0}div[@type="scene"]')

            for scene_div in scene_divs:
                scene_analysis = self._analyze_scene(scene_div)
                if scene_analysis:
                    scenes.append(asdict(scene_analysis))

            # Calcola statistiche aggregate
            statistics = self._calculate_statistics(scenes)

            return {
                'film': title,
                'total_scenes': len(scenes),
                'statistics': statistics,
                'analysis_timestamp': '2025-08-27T12:00:00'  # In produzione usare datetime.now()
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

        # Estrai location principale
        location_stage = scene_div.find('.//{http://www.tei-c.org/ns/1.0}stage[@type="location"]')
        raw_location_text = location_stage.text if location_stage is not None else ""

        # Estrai tutti i testi delle stage directions
        stage_elements = scene_div.findall('.//{http://www.tei-c.org/ns/1.0}stage')
        stage_texts = [elem.text for elem in stage_elements if elem.text]

        # Analizza location
        location_info = self._analyze_location(raw_location_text, stage_texts)

        # Analizza temporalità
        temporal_info = self._analyze_temporal(raw_location_text, stage_texts)

        return SceneAnalysis(
            scene_n=scene_n,
            location=location_info,
            temporal=temporal_info,
            raw_location_text=raw_location_text,
            stage_texts=stage_texts
        )

    def _analyze_location(self, location_text: str, stage_texts: List[str]) -> LocationInfo:
        """Analisi combinata dei luoghi (Opzioni A+B+C)"""
        location_info = LocationInfo()

        # STEP 1: Pattern cinematografici standard (Opzione A)
        location_upper = location_text.upper()

        # Estrai INT/EXT
        if location_upper.startswith('INT'):
            location_info.type = 'INT'
        elif location_upper.startswith('EXT'):
            location_info.type = 'EXT'
        elif 'INT.' in location_upper:
            location_info.type = 'INT'
        elif 'EXT.' in location_upper:
            location_info.type = 'EXT'

        # STEP 2: Analisi semantica (Opzione B)
        all_text = (location_text + ' ' + ' '.join(stage_texts)).lower()

        # Determina environment
        environment_scores = {}
        for env_type, keywords in self.environment_keywords.items():
            score = sum(1 for keyword in keywords if keyword in all_text)
            if score > 0:
                environment_scores[env_type] = score

        if environment_scores:
            location_info.environment = max(environment_scores, key=environment_scores.get)

        # Determina setting generale
        if location_info.environment in ['space', 'fantasy']:
            location_info.setting = 'fantasy/sci-fi'
        elif location_info.environment in ['urban', 'suburban']:
            location_info.setting = 'contemporary'
        elif location_info.environment in ['sea', 'mountain', 'desert']:
            location_info.setting = 'natural'
        else:
            location_info.setting = 'unspecified'

        # STEP 3: Verifica geografica (Opzione C)
        location_words = set(location_text.lower().split())

        # Controlla luoghi reali
        if any(place in location_words for place in self.real_places):
            location_info.real_imaginary = 'real'
        elif any(place in location_words for place in self.imaginary_places):
            location_info.real_imaginary = 'imaginary'
        else:
            # Inferenza basata su setting
            if location_info.setting == 'fantasy/sci-fi':
                location_info.real_imaginary = 'imaginary'
            else:
                location_info.real_imaginary = 'unknown'

        return location_info

    def _analyze_temporal(self, location_text: str, stage_texts: List[str]) -> TemporalInfo:
        """Analisi contestuale degli intervalli temporali (Opzione B)"""
        temporal_info = TemporalInfo()

        all_text = (location_text + ' ' + ' '.join(stage_texts)).lower()

        # Analizza periodo giornaliero
        time_scores = {}
        for time_type, keywords in self.time_keywords.items():
            if time_type in ['morning', 'day', 'evening', 'night']:
                score = sum(1 for keyword in keywords if keyword in all_text)
                if score > 0:
                    time_scores[time_type] = score

        if time_scores:
            temporal_info.period = max(time_scores, key=time_scores.get).upper()

        # Analizza stagione
        season_scores = {}
        for season, keywords in self.time_keywords.items():
            if season in ['winter', 'spring', 'summer', 'autumn']:
                score = sum(1 for keyword in keywords if keyword in all_text)
                if score > 0:
                    season_scores[season] = score

        if season_scores:
            temporal_info.season = max(season_scores, key=season_scores.get)

        # Analizza periodo storico
        historical_scores = {}
        for period, keywords in self.historical_keywords.items():
            score = sum(1 for keyword in keywords if keyword in all_text)
            if score > 0:
                historical_scores[period] = score

        if historical_scores:
            temporal_info.historical = max(historical_scores, key=historical_scores.get)
        else:
            temporal_info.historical = 'contemporary'  # Default

        return temporal_info

    def _calculate_statistics(self, scenes: List[Dict]) -> Dict[str, Any]:
        """Calcola statistiche aggregate del film"""
        if not scenes:
            return {}

        # Statistiche sui luoghi
        location_types = [s['location']['type'] for s in scenes if s['location']['type']]
        environments = [s['location']['environment'] for s in scenes if s['location']['environment']]
        real_imaginary = [s['location']['real_imaginary'] for s in scenes if s['location']['real_imaginary']]

        # Statistiche temporali
        periods = [s['temporal']['period'] for s in scenes if s['temporal']['period']]
        seasons = [s['temporal']['season'] for s in scenes if s['temporal']['season']]
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

        # Salva risultati
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"Analisi completata. Risultati salvati in: {output_file}")
        return results


def main():
    """Funzione principale per test"""
    analyzer = TEIAnalyzer()

    # Analizza directory di file TEI
    results = analyzer.analyze_directory('output', 'screenplay_analysis.json')

    # Stampa sommario
    if results:
        for result in results:
            if 'error' not in result:
                print(f"\n{result['film']}:")
                print(f"  Scene totali: {result['total_scenes']}")
                if result['statistics']:
                    stats = result['statistics']
                    if 'locations' in stats:
                        print(f"  INT/EXT: {stats['locations']['int_ext_distribution']}")
                    if 'temporal' in stats:
                        print(f"  Giorno/Notte: {stats['temporal']['day_night_distribution']}")


if __name__ == "__main__":
    main()