import streamlit as st
import plotly.express as px
import json
import os


class StreamlitDashboard:
    def __init__(self, analysis_dir, stats_file1, stats_file2):
        self.individual_stats_path = os.path.join(analysis_dir, stats_file1)
        self.aggregated_stats_path = os.path.join(analysis_dir, stats_file2)

        self.individual_stats = self.load_json(self.individual_stats_path)
        self.aggregated_stats = self.load_json(self.aggregated_stats_path)

        # ============================
        # PALETTE COLORI UNIFICATE
        # ============================
        self.COLOR_PALETTES = {
            "int_ext": {
                "Interno": "#764ba2",
                "Esterno": "#667eea",
                "Sconosciuto": "#95a5a6"
            },
            "periodi": {
                "Mattina": "#6BCF7F",
                "Giorno": "#FFD93D",
                "Sera": "#686DE0",
                "Notte": "#4834DF",
                "Sconosciuto": "#95a5a6"
            },
            "stagioni": {
                "Primavera": "#FF6B6B",
                "Estate": "#4ECDC4",
                "Autunno": "#FF9FF3",
                "Inverno": "#FECA57",
                "Sconosciuto": "#95a5a6"
            },
            "default": {
                "Sconosciuto": "#95a5a6"
            }
        }

    def load_json(self, filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    def translate_labels(self, data, translation_dict):
        """Traduce le etichette dei dati usando il dizionario fornito"""
        translated_data = {}
        for key, value in data.items():
            translated_key = translation_dict.get(key, key)
            translated_data[translated_key] = value
        return translated_data

    def get_color_map(self, labels, palette_key="default"):
        """Restituisce la mappa colori coerente in base alla palette scelta"""
        palette = self.COLOR_PALETTES.get(palette_key, self.COLOR_PALETTES["default"])
        return {label: palette.get(label, "#ff6b6b") for label in labels}

    # ============================
    # METODI GENERICI PER GRAFICI
    # ============================
    def plot_pie(self, data, title, translation_dict=None, palette_key="default"):
        if not data:
            st.info("Nessun dato disponibile")
            return

        plot_data = data.copy()

        if translation_dict:
            plot_data = self.translate_labels(plot_data, translation_dict)

        labels = list(plot_data.keys())
        color_map = self.get_color_map(labels, palette_key)

        fig = px.pie(
            values=list(plot_data.values()),
            names=labels,
            title=title,
            color=labels,
            color_discrete_map=color_map
        )
        st.plotly_chart(fig, use_container_width=True)

    def plot_bar(self, data, title, x_title="Categoria", y_title="Valore",
                 translation_dict=None, palette_key="default", exclude_unknown=True):
        if not data:
            st.info("Nessun dato disponibile")
            return

        plot_data = data.copy()
        if exclude_unknown:
            plot_data = {k: v for k, v in plot_data.items()
                         if k not in ['unknown', 'UNKNOWN', 'Sconosciuto']}

        if translation_dict:
            plot_data = self.translate_labels(plot_data, translation_dict)

        if not plot_data:
            st.info("Nessun dato disponibile (escluso sconosciuto)")
            return

        labels = list(plot_data.keys())
        color_map = self.get_color_map(labels, palette_key)

        fig = px.bar(
            x=labels,
            y=list(plot_data.values()),
            title=title,
            color=labels,
            color_discrete_map=color_map
        )
        fig.update_layout(xaxis_title=x_title, yaxis_title=y_title)
        st.plotly_chart(fig, use_container_width=True)

    # ============================
    # DASHBOARD PRINCIPALE
    # ============================
    def run_dashboard(self):
        st.set_page_config(
            page_title="Dashboard Statistiche Film",
            page_icon="🎬",
            layout="wide"
        )

        # Dizionari di traduzione
        int_ext_translations = {'INT': 'Interno', 'EXT': 'Esterno', 'UNKNOWN': 'Sconosciuto'}
        period_translations = {
            'MORNING': 'Mattina', 'DAY': 'Giorno', 'EVENING': 'Sera',
            'NIGHT': 'Notte', 'UNKNOWN': 'Sconosciuto'
        }
        season_translations = {
            'spring': 'Primavera', 'summer': 'Estate', 'winter': 'Inverno',
            'autumn': 'Autunno', 'unknown': 'Sconosciuto'
        }

        # Metriche principali
        col1, col2, col3, col4 = st.columns(4)
        summary = self.aggregated_stats['analysis_summary']

        st.title("🎬 Dashboard Statistiche Film")
        st.markdown(
            f"Analisi di {summary['total_films_analyzed']} film e {summary['total_scenes_analyzed']:,} scene cinematografiche")

        with col1:
            st.metric("Film Analizzati", summary['total_films_analyzed'])
        with col2:
            st.metric("Scene Totali", f"{summary['total_scenes_analyzed']:,}")
        with col3:
            st.metric("Scene per Film", f"{summary['average_scenes_per_film']:.1f}")
        with col4:
            int_ext_percentages = self.aggregated_stats['aggregated_statistics']['locations']['int_ext_percentages']
            known_total = sum(v for k, v in int_ext_percentages.items() if k != 'UNKNOWN')
            if known_total > 0:
                int_percentage = int_ext_percentages.get('INT', 0) * 100 / known_total
                st.metric("Scene Interne", f"{int_percentage:.1f}%")
            else:
                st.metric("Scene Interne", "N/A")

        stats = self.aggregated_stats['aggregated_statistics']

        # Row 1: INT/EXT e Ambienti
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Distribuzione Interni vs Esterni")
            self.plot_pie(stats['locations']['int_ext_totals'], "Interno vs Esterno",
                          int_ext_translations, palette_key="int_ext")
        with col2:
            st.subheader("Distribuzione per Ambiente")
            self.plot_bar(stats['locations']['environment_totals'], "Ambienti",
                          x_title="Ambiente", y_title="Numero Scene", palette_key="default")

        # Row 2: Periodi del giorno e Stagioni
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Periodi del Giorno")
            self.plot_pie(stats['temporal']['period_totals'], "Periodi del Giorno",
                          period_translations, palette_key="periodi")
        with col2:
            st.subheader("Distribuzione Stagionale")
            self.plot_pie(stats['temporal']['season_totals'], "Stagioni",
                          season_translations, palette_key="stagioni")

        # ============================
        # NUOVI ISTOGRAMMI PER FILM
        # ============================
        st.markdown("---")
        st.header("📊 Confronto tra Film")

        # --- 1. INT/EXT per film ---
        int_ext_data = []
        for film in self.individual_stats:
            film_name = film.get('film', 'N/A')
            stats = film.get('statistics', {})
            locations = stats.get('locations', {})
            dist = locations.get('int_ext_distribution', {})
            for k, v in dist.items():
                if k != 'UNKNOWN':
                    translated_key = int_ext_translations.get(k, k)
                    int_ext_data.append({"Film": film_name, "Categoria": translated_key, "Scene": v})

        if int_ext_data:
            color_map = self.COLOR_PALETTES["int_ext"]
            fig1 = px.bar(int_ext_data, x="Film", y="Scene", color="Categoria",
                          barmode="stack", title="Distribuzione Interno/Esterno per film (escluso Sconosciuto)",
                          color_discrete_map=color_map)
            fig1.update_layout(xaxis=dict(showticklabels=False))
            st.plotly_chart(fig1, use_container_width=True)

        # --- 2. Fasi del giorno per film ---
        daytime_data = []
        for film in self.individual_stats:
            film_name = film.get('film', 'N/A')
            stats = film.get('statistics', {})
            temporal = stats.get('temporal', {})
            dist = temporal.get('day_night_distribution', {})
            for k, v in dist.items():
                if k != 'UNKNOWN':
                    translated_key = period_translations.get(k, k)
                    daytime_data.append({"Film": film_name, "Categoria": translated_key, "Scene": v})

        if daytime_data:
            color_map = self.COLOR_PALETTES["periodi"]
            fig2 = px.bar(daytime_data, x="Film", y="Scene", color="Categoria",
                          barmode="stack", title="Distribuzione fasi del giorno per film (escluso Sconosciuto)",
                          color_discrete_map=color_map)
            fig2.update_layout(xaxis=dict(showticklabels=False))
            st.plotly_chart(fig2, use_container_width=True)

        # --- 3. Stagioni per film ---
        season_data = []
        for film in self.individual_stats:
            film_name = film.get('film', 'N/A')
            stats = film.get('statistics', {})
            temporal = stats.get('temporal', {})
            dist = temporal.get('season_distribution', {})
            for k, v in dist.items():
                if k != 'unknown':
                    translated_key = season_translations.get(k, k)
                    season_data.append({"Film": film_name, "Categoria": translated_key, "Scene": v})

        if season_data:
            color_map = self.COLOR_PALETTES["stagioni"]
            fig3 = px.bar(season_data, x="Film", y="Scene", color="Categoria",
                          barmode="stack", title="Distribuzione stagioni per film (escluso Sconosciuto)",
                          color_discrete_map=color_map)
            fig3.update_layout(xaxis=dict(showticklabels=False))
            st.plotly_chart(fig3, use_container_width=True)

        # ============================
        # SEZIONE: ANALISI SINGOLI FILM
        # ============================
        st.markdown("---")
        st.header("📊 Analisi Dettagliata Singoli Film")

        film_names = [film['film'] for film in self.individual_stats]
        selected_film = st.selectbox("Seleziona un film per l'analisi dettagliata:", film_names)

        film_data = next((film for film in self.individual_stats if film['film'] == selected_film), None)
        if film_data:
            self.display_individual_film_analysis(film_data)

    # ============================
    # ANALISI SINGOLO FILM
    # ============================
    def display_individual_film_analysis(self, film_data):
        int_ext_translations = {'INT': 'Interno', 'EXT': 'Esterno', 'UNKNOWN': 'Sconosciuto'}
        period_translations = {
            'MORNING': 'Mattina', 'DAY': 'Giorno', 'EVENING': 'Sera',
            'NIGHT': 'Notte', 'UNKNOWN': 'Sconosciuto'
        }
        season_translations = {
            'spring': 'Primavera', 'summer': 'Estate', 'winter': 'Inverno',
            'autumn': 'Autunno', 'unknown': 'Sconosciuto'
        }

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🎬 Film", film_data['film'])
        with col2:
            st.metric("🎭 Scene Totali", film_data['total_scenes'])
        with col3:
            timestamp = film_data['analysis_timestamp'].split('T')[0]
            st.metric("📅 Analisi", timestamp)

        stats = film_data.get('statistics', {})

        # Row 1: Locations del film
        st.subheader(f"🏞️ Analisi Locations - {film_data['film']}")
        col1, col2 = st.columns(2)
        with col1:
            self.plot_pie(stats.get('locations', {}).get('int_ext_distribution', {}),
                          f"Interno vs Esterno - {film_data['film']}", int_ext_translations, palette_key="int_ext")
        with col2:
            self.plot_bar(stats.get('locations', {}).get('environment_distribution', {}),
                          f"Ambienti - {film_data['film']}",
                          x_title="Ambiente", y_title="Scene", palette_key="default")

        # Row 2: Temporal del film
        st.subheader(f"⏰ Analisi Temporale - {film_data['film']}")
        col1, col2 = st.columns(2)
        with col1:
            self.plot_pie(stats.get('temporal', {}).get('day_night_distribution', {}),
                          f"Periodi Giorno - {film_data['film']}", period_translations, palette_key="periodi")
        with col2:
            self.plot_pie(stats.get('temporal', {}).get('season_distribution', {}),
                          f"Stagioni - {film_data['film']}", season_translations, palette_key="stagioni")

        # Insights
        st.subheader(f"🎯 Insights - {film_data['film']}")
        col1, col2, col3 = st.columns(3)

        locations = stats.get('locations', {})
        temporal = stats.get('temporal', {})

        with col1:
            most_common_env = locations.get('most_common_environment', 'N/A')
            if most_common_env == 'unknown':
                st.info(f"**Ambiente Dominante:** Sconosciuto")
            else:
                st.info(f"**Ambiente Dominante:** {most_common_env}")
        with col2:
            most_common_period = temporal.get('most_common_period', 'N/A')
            translated_period = period_translations.get(most_common_period, most_common_period)
            st.info(f"**Periodo Dominante:** {translated_period}")
        with col3:
            int_ext_data = locations.get('int_ext_distribution', {})
            int_scenes = int_ext_data.get('INT', 0)
            known_scenes = sum(v for k, v in int_ext_data.items() if k != 'UNKNOWN')
            if known_scenes > 0:
                int_percentage = (int_scenes / known_scenes * 100)
                st.info(f"**% Scene Interne:** {int_percentage:.1f}%")
            else:
                st.info(f"**% Scene Interne:** N/A")

        # Statistiche su unknown
        st.subheader("📈 Statistiche Sconosciute")
        col1, col2, col3 = st.columns(3)

        with col1:
            unknown_int_ext = int_ext_data.get('UNKNOWN', 0)
            total_scenes = sum(int_ext_data.values())
            if total_scenes > 0:
                unknown_perc = (unknown_int_ext / total_scenes * 100)
                st.metric("Scene INT/EXT Sconosciute", f"{unknown_int_ext} ({unknown_perc:.1f}%)")
            else:
                st.metric("Scene INT/EXT Sconosciute", "0")

        with col2:
            period_data = temporal.get('day_night_distribution', {})
            unknown_periods = period_data.get('UNKNOWN', 0)
            total_periods = sum(period_data.values())
            if total_periods > 0:
                unknown_perc = (unknown_periods / total_periods * 100)
                st.metric("Periodi Sconosciuti", f"{unknown_periods} ({unknown_perc:.1f}%)")
            else:
                st.metric("Periodi Sconosciuti", "0")

        with col3:
            season_data = temporal.get('season_distribution', {})
            unknown_seasons = season_data.get('unknown', 0)
            total_seasons = sum(season_data.values())
            if total_seasons > 0:
                unknown_perc = (unknown_seasons / total_seasons * 100)
                st.metric("Stagioni Sconosciute", f"{unknown_seasons} ({unknown_perc:.1f}%)")
            else:
                st.metric("Stagioni Sconosciute", "0")

        # Confronto con la media
        st.subheader("📈 Confronto con la Media Generale")
        general_stats = self.aggregated_stats['aggregated_statistics']
        general_int_ext = general_stats['locations']['int_ext_percentages']

        known_general_total = sum(v for k, v in general_int_ext.items() if k != 'UNKNOWN')
        if known_general_total > 0:
            general_int_perc = general_int_ext.get('INT', 0) * 100 / known_general_total
        else:
            general_int_perc = 0

        col1, col2 = st.columns(2)
        with col1:
            if known_scenes > 0:
                difference = int_percentage - general_int_perc
                if difference > 0:
                    st.success(
                        f"Questo film ha **{difference:.1f}%** in più di scene interne rispetto alla media ({general_int_perc:.1f}%)")
                else:
                    st.warning(
                        f"Questo film ha **{abs(difference):.1f}%** in meno di scene interne rispetto alla media ({general_int_perc:.1f}%)")
            else:
                st.info("Impossibile calcolare il confronto: tutte le scene sono sconosciute")

        with col2:
            avg_scenes_per_film = self.aggregated_stats['analysis_summary']['average_scenes_per_film']
            scene_difference = film_data['total_scenes'] - avg_scenes_per_film
            if scene_difference > 0:
                st.info(f"**{scene_difference:.0f} scene** in più rispetto alla media ({avg_scenes_per_film:.1f})")
            else:
                st.info(
                    f"**{abs(scene_difference):.0f} scene** in meno rispetto alla media ({avg_scenes_per_film:.1f})")


if __name__ == "__main__":
    analysis_directory = "analysis"
    individual_stats_file = "screenplay_analysis.json"
    aggregated_stats_file = "screenplay_analysis_macro_stats.json"

    dashboard = StreamlitDashboard(analysis_directory, individual_stats_file, aggregated_stats_file)
    dashboard.run_dashboard()
