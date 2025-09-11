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

    def run_dashboard(self):
        st.set_page_config(
            page_title="Dashboard Statistiche Film",
            page_icon="🎬",
            layout="wide"
        )

        # Header
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

        # Grafici
        stats = self.aggregated_stats['aggregated_statistics']

        # Row 1: INT/EXT e Ambienti
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Distribuzione Interni vs Esterni")
            int_ext_data = stats['locations']['int_ext_totals']
            fig1 = px.pie(
                values=list(int_ext_data.values()),
                names=list(int_ext_data.keys()),
                title="INT vs EXT",
                color_discrete_sequence=['#667eea', '#764ba2']
            )
            st.plotly_chart(fig1, use_container_width=True)

        with col2:
            st.subheader("Distribuzione per Ambiente")
            env_data = stats['locations']['environment_totals']
            fig2 = px.bar(
                x=list(env_data.keys()),
                y=list(env_data.values()),
                title="Ambienti",
                color_discrete_sequence=['#FF6B6B']
            )
            fig2.update_layout(xaxis_title="Ambiente", yaxis_title="Numero Scene")
            st.plotly_chart(fig2, use_container_width=True)

        # Row 2: Periodi del giorno e Stagioni
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Periodi del Giorno")
            period_data = stats['temporal']['period_totals']
            fig3 = px.pie(
                values=list(period_data.values()),
                names=list(period_data.keys()),
                title="Periodi del Giorno",
                color_discrete_sequence=['#FFD93D', '#6BCF7F', '#4834DF', '#686DE0']
            )
            st.plotly_chart(fig3, use_container_width=True)

        with col2:
            st.subheader("Distribuzione Stagionale")
            season_data = stats['temporal']['season_totals']
            # Traduci i nomi delle stagioni
            season_labels = {
                'spring': 'Primavera',
                'summer': 'Estate',
                'winter': 'Inverno',
                'autumn': 'Autunno'
            }
            translated_names = [season_labels.get(k, k) for k in season_data.keys()]

            fig4 = px.pie(
                values=list(season_data.values()),
                names=translated_names,
                title="Stagioni",
                color_discrete_sequence=['#FF6B6B', '#4ECDC4', '#FECA57', '#FF9FF3']
            )
            st.plotly_chart(fig4, use_container_width=True)

        # ================================
        # SEZIONE: ANALISI SINGOLI FILM
        # ================================
        st.markdown("---")
        st.header("📊 Analisi Dettagliata Singoli Film")

        # Selezione film
        film_names = [film['film'] for film in self.individual_stats]
        selected_film = st.selectbox("Seleziona un film per l'analisi dettagliata:", film_names)

        # Trova i dati del film selezionato
        film_data = None
        for film in self.individual_stats:
            if film['film'] == selected_film:
                film_data = film
                break

        if film_data:
            self.display_individual_film_analysis(film_data)

    def display_individual_film_analysis(self, film_data):
        """Visualizza l'analisi dettagliata di un singolo film"""

        # Info generale del film
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🎬 Film", film_data['film'])
        with col2:
            st.metric("🎭 Scene Totali", film_data['total_scenes'])
        with col3:
            timestamp = film_data['analysis_timestamp'].split('T')[0]
            st.metric("📅 Analisi", timestamp)

        stats = film_data['statistics']

        # Row 1: Locations del singolo film
        st.subheader(f"🏞️ Analisi Locations - {film_data['film']}")
        col1, col2 = st.columns(2)

        with col1:
            # INT vs EXT per il film
            st.markdown("**Interni vs Esterni**")
            int_ext_data = stats['locations']['int_ext_distribution']
            fig_int_ext = px.pie(
                values=list(int_ext_data.values()),
                names=list(int_ext_data.keys()),
                title=f"INT vs EXT - {film_data['film']}",
                color_discrete_sequence=['#667eea', '#764ba2']
            )
            st.plotly_chart(fig_int_ext, use_container_width=True)

        with col2:
            # Ambienti per il film
            st.markdown("**Distribuzione Ambienti**")
            env_data = stats['locations']['environment_distribution']
            if env_data:  # Controlla se ci sono dati
                fig_env = px.bar(
                    x=list(env_data.keys()),
                    y=list(env_data.values()),
                    title=f"Ambienti - {film_data['film']}",
                    color_discrete_sequence=['#FF6B6B']
                )
                fig_env.update_layout(xaxis_title="Ambiente", yaxis_title="Scene")
                st.plotly_chart(fig_env, use_container_width=True)
            else:
                st.info("Nessun dato ambientale disponibile per questo film")

        # Row 2: Temporal del singolo film
        st.subheader(f"⏰ Analisi Temporale - {film_data['film']}")
        col1, col2 = st.columns(2)

        with col1:
            # Periodi del giorno
            st.markdown("**Periodi del Giorno**")
            day_data = stats['temporal']['day_night_distribution']
            if day_data:
                fig_day = px.pie(
                    values=list(day_data.values()),
                    names=list(day_data.keys()),
                    title=f"Periodi Giorno - {film_data['film']}",
                    color_discrete_sequence=['#FFD93D', '#6BCF7F', '#4834DF', '#686DE0']
                )
                st.plotly_chart(fig_day, use_container_width=True)
            else:
                st.info("Nessun dato sui periodi del giorno per questo film")

        with col2:
            # Stagioni
            st.markdown("**Distribuzione Stagionale**")
            season_data = stats['temporal']['season_distribution']
            if season_data:
                # Traduci i nomi delle stagioni
                season_labels = {
                    'spring': 'Primavera',
                    'summer': 'Estate',
                    'winter': 'Inverno',
                    'autumn': 'Autunno'
                }
                translated_names = [season_labels.get(k, k) for k in season_data.keys()]

                fig_season = px.pie(
                    values=list(season_data.values()),
                    names=translated_names,
                    title=f"Stagioni - {film_data['film']}",
                    color_discrete_sequence=['#FF6B6B', '#4ECDC4', '#FECA57', '#FF9FF3']
                )
                st.plotly_chart(fig_season, use_container_width=True)
            else:
                st.info("Nessun dato stagionale per questo film")

        # Summary insights del film
        st.subheader(f"🎯 Insights - {film_data['film']}")
        col1, col2, col3 = st.columns(3)

        with col1:
            most_common_env = stats['locations'].get('most_common_environment', 'N/A')
            st.info(f"**Ambiente Dominante:** {most_common_env}")

        with col2:
            most_common_period = stats['temporal'].get('most_common_period', 'N/A')
            st.info(f"**Periodo Dominante:** {most_common_period}")

        with col3:
            # Calcola percentuale INT vs EXT
            int_scenes = int_ext_data.get('INT', 0)
            total_int_ext = sum(int_ext_data.values())
            int_percentage = (int_scenes / total_int_ext * 100) if total_int_ext > 0 else 0
            st.info(f"**% Scene Interne:** {int_percentage:.1f}%")

        # Comparazione con la media generale
        st.subheader("📈 Confronto con la Media Generale")

        # Calcola alcune metriche comparative
        general_stats = self.aggregated_stats['aggregated_statistics']
        general_int_perc = general_stats['locations']['int_ext_percentages']['INT']

        col1, col2 = st.columns(2)
        with col1:
            difference = int_percentage - general_int_perc
            if difference > 0:
                st.success(
                    f"Questo film ha **{difference:.1f}%** in più di scene interne rispetto alla media generale ({general_int_perc}%)")
            else:
                st.warning(
                    f"Questo film ha **{abs(difference):.1f}%** in meno di scene interne rispetto alla media generale ({general_int_perc}%)")

        with col2:
            avg_scenes_per_film = self.aggregated_stats['analysis_summary']['average_scenes_per_film']
            scene_difference = film_data['total_scenes'] - avg_scenes_per_film
            if scene_difference > 0:
                st.info(f"**{scene_difference:.0f} scene** in più rispetto alla media ({avg_scenes_per_film:.1f})")
            else:
                st.info(
                    f"**{abs(scene_difference):.0f} scene** in meno rispetto alla media ({avg_scenes_per_film:.1f})")

if __name__ == "__main__":
    dashboard = StreamlitDashboard('screenplay_analysis.json', 'screenplay_analysis_macro_stats.json')
    dashboard.run_dashboard()