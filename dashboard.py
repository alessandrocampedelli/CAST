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

        # Row 3: Periodi storici (full width)
        st.subheader("Periodi Storici")
        historical_data = stats['temporal']['historical_totals']
        fig5 = px.bar(
            x=list(historical_data.keys()),
            y=list(historical_data.values()),
            title="Distribuzione per Periodo Storico",
            color_discrete_sequence=['#4ECDC4']
        )
        fig5.update_layout(xaxis_title="Periodo Storico", yaxis_title="Numero Scene")
        st.plotly_chart(fig5, use_container_width=True)

        # Row 4: Reale vs Immaginario
        st.subheader("Classificazione Realtà")
        reality_data = stats['locations']['real_imaginary_totals']
        # Traduci le etichette
        reality_labels = {
            'unknown': 'Sconosciuto',
            'real': 'Reale',
            'imaginary': 'Immaginario'
        }
        translated_reality_names = [reality_labels.get(k, k) for k in reality_data.keys()]

        fig6 = px.pie(
            values=list(reality_data.values()),
            names=translated_reality_names,
            title="Distribuzione Reale vs Immaginario",
            color_discrete_sequence=['#95A5A6', '#27AE60', '#E74C3C']
        )
        st.plotly_chart(fig6, use_container_width=True)

if __name__ == "__main__":
    dashboard = StreamlitDashboard('screenplay_analysis.json', 'screenplay_analysis_macro_stats.json')
    dashboard.run_dashboard()