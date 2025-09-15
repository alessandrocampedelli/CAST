import streamlit as st
import plotly.express as px
import json


class StreamlitDashboard:
    def __init__(self, stats_file1, stats_file2):
        self.individual_stats = self.load_json(stats_file1)
        self.aggregated_stats = self.load_json(stats_file2)

    def load_json(self, filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    # ============================
    # METODI GENERICI PER GRAFICI
    # ============================

    def plot_pie(self, data, title, colors=None, translate_seasons=False):
        if not data:
            st.info("Nessun dato disponibile")
            return

        labels = list(data.keys())
        if translate_seasons:
            season_labels = {
                'spring': 'Primavera',
                'summer': 'Estate',
                'winter': 'Inverno',
                'autumn': 'Autunno'
            }
            labels = [season_labels.get(k, k) for k in labels]

        fig = px.pie(
            values=list(data.values()),
            names=labels,
            title=title,
            color_discrete_sequence=colors
        )
        st.plotly_chart(fig, use_container_width=True)

    def plot_bar(self, data, title, x_title="Categoria", y_title="Valore", colors=None):
        if not data:
            st.info("Nessun dato disponibile")
            return

        fig = px.bar(
            x=list(data.keys()),
            y=list(data.values()),
            title=title,
            color_discrete_sequence=colors
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

        st.title("🎬 Dashboard Statistiche Film")
        st.markdown("Analisi di 100 film e 15.615 scene cinematografiche")

        # Metriche principali
        col1, col2, col3, col4 = st.columns(4)
        summary = self.aggregated_stats['analysis_summary']
        with col1:
            st.metric("Film Analizzati", summary['total_films_analyzed'])
        with col2:
            st.metric("Scene Totali", f"{summary['total_scenes_analyzed']:,}")
        with col3:
            st.metric("Scene per Film", f"{summary['average_scenes_per_film']:.1f}")
        with col4:
            int_percentage = self.aggregated_stats['aggregated_statistics']['locations']['int_ext_percentages']['INT']
            st.metric("Scene Interne", f"{int_percentage}%")

        stats = self.aggregated_stats['aggregated_statistics']

        # Row 1: INT/EXT e Ambienti
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Distribuzione Interni vs Esterni")
            self.plot_pie(stats['locations']['int_ext_totals'], "INT vs EXT", colors=['#667eea', '#764ba2'])
        with col2:
            st.subheader("Distribuzione per Ambiente")
            self.plot_bar(stats['locations']['environment_totals'], "Ambienti",
                          x_title="Ambiente", y_title="Numero Scene", colors=['#FF6B6B'])

        # Row 2: Periodi del giorno e Stagioni
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Periodi del Giorno")
            self.plot_pie(stats['temporal']['period_totals'], "Periodi del Giorno",
                          colors=['#FFD93D', '#6BCF7F', '#4834DF', '#686DE0'])
        with col2:
            st.subheader("Distribuzione Stagionale")
            self.plot_pie(stats['temporal']['season_totals'], "Stagioni",
                          colors=['#FF6B6B', '#4ECDC4', '#FECA57', '#FF9FF3'],
                          translate_seasons=True)

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
                int_ext_data.append({"Film": film_name, "Categoria": k, "Scene": v})

        if int_ext_data:
            fig1 = px.bar(int_ext_data, x="Film", y="Scene", color="Categoria",
                          barmode="group", title="Distribuzione INT/EXT per film")
            st.plotly_chart(fig1, use_container_width=True)
        else:
            st.info("Nessun dato INT/EXT disponibile per i film.")

        # --- 2. Fasi del giorno per film ---
        daytime_data = []
        for film in self.individual_stats:
            film_name = film.get('film', 'N/A')
            stats = film.get('statistics', {})
            temporal = stats.get('temporal', {})
            dist = temporal.get('day_night_distribution', {})
            for k, v in dist.items():
                daytime_data.append({"Film": film_name, "Categoria": k, "Scene": v})

        if daytime_data:
            fig2 = px.bar(daytime_data, x="Film", y="Scene", color="Categoria",
                          barmode="group", title="Distribuzione fasi del giorno per film")
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Nessun dato sulle fasi del giorno disponibile per i film.")

        # --- 3. Stagioni per film ---
        season_data = []
        season_labels = {'spring': 'Primavera','summer': 'Estate','winter': 'Inverno','autumn': 'Autunno'}
        for film in self.individual_stats:
            film_name = film.get('film', 'N/A')
            stats = film.get('statistics', {})
            temporal = stats.get('temporal', {})
            dist = temporal.get('season_distribution', {})
            for k, v in dist.items():
                label = season_labels.get(k, k)
                season_data.append({"Film": film_name, "Categoria": label, "Scene": v})

        if season_data:
            fig3 = px.bar(season_data, x="Film", y="Scene", color="Categoria",
                          barmode="group", title="Distribuzione stagioni per film")
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info("Nessun dato stagionale disponibile per i film.")

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
                          f"INT vs EXT - {film_data['film']}", colors=['#667eea', '#764ba2'])
        with col2:
            self.plot_bar(stats.get('locations', {}).get('environment_distribution', {}),
                          f"Ambienti - {film_data['film']}",
                          x_title="Ambiente", y_title="Scene", colors=['#FF6B6B'])

        # Row 2: Temporal del film
        st.subheader(f"⏰ Analisi Temporale - {film_data['film']}")
        col1, col2 = st.columns(2)
        with col1:
            self.plot_pie(stats.get('temporal', {}).get('day_night_distribution', {}),
                          f"Periodi Giorno - {film_data['film']}",
                          colors=['#FFD93D', '#6BCF7F', '#4834DF', '#686DE0'])
        with col2:
            self.plot_pie(stats.get('temporal', {}).get('season_distribution', {}),
                          f"Stagioni - {film_data['film']}",
                          colors=['#FF6B6B', '#4ECDC4', '#FECA57', '#FF9FF3'],
                          translate_seasons=True)

        # Insights
        st.subheader(f"🎯 Insights - {film_data['film']}")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info(f"**Ambiente Dominante:** {stats['locations'].get('most_common_environment', 'N/A')}")
        with col2:
            st.info(f"**Periodo Dominante:** {stats['temporal'].get('most_common_period', 'N/A')}")
        with col3:
            int_ext_data = stats['locations']['int_ext_distribution']
            int_scenes = int_ext_data.get('INT', 0)
            total_int_ext = sum(int_ext_data.values())
            int_percentage = (int_scenes / total_int_ext * 100) if total_int_ext > 0 else 0
            st.info(f"**% Scene Interne:** {int_percentage:.1f}%")

        # Confronto con la media
        st.subheader("📈 Confronto con la Media Generale")
        general_stats = self.aggregated_stats['aggregated_statistics']
        general_int_perc = general_stats['locations']['int_ext_percentages']['INT']

        col1, col2 = st.columns(2)
        with col1:
            difference = int_percentage - general_int_perc
            if difference > 0:
                st.success(f"Questo film ha **{difference:.1f}%** in più di scene interne rispetto alla media ({general_int_perc}%)")
            else:
                st.warning(f"Questo film ha **{abs(difference):.1f}%** in meno di scene interne rispetto alla media ({general_int_perc}%)")

        with col2:
            avg_scenes_per_film = self.aggregated_stats['analysis_summary']['average_scenes_per_film']
            scene_difference = film_data['total_scenes'] - avg_scenes_per_film
            if scene_difference > 0:
                st.info(f"**{scene_difference:.0f} scene** in più rispetto alla media ({avg_scenes_per_film:.1f})")
            else:
                st.info(f"**{abs(scene_difference):.0f} scene** in meno rispetto alla media ({avg_scenes_per_film:.1f})")


if __name__ == "__main__":
    dashboard = StreamlitDashboard('screenplay_analysis.json', 'screenplay_analysis_macro_stats.json')
    dashboard.run_dashboard()
