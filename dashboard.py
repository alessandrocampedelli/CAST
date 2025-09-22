import streamlit as st
import plotly.express as px
import json
import os


class StreamlitDashboard:
    """Dashboard interattiva per l'analisi delle statistiche sui film."""

    COLOR_PALETTES = {
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
            "Primavera": "#FECA57",
            "Estate": "#4ECDC4",
            "Autunno": "#FF9FF3",
            "Inverno": "#FF6B6B",
            "Sconosciuto": "#95a5a6"
        },
        "default": {
            "Sconosciuto": "#95a5a6"
        }
    }

    TRANSLATIONS = {
        "int_ext": {'INT': 'Interno', 'EXT': 'Esterno', 'UNKNOWN': 'Sconosciuto'},
        "periodi": {
            'MORNING': 'Mattina', 'DAY': 'Giorno', 'EVENING': 'Sera',
            'NIGHT': 'Notte', 'UNKNOWN': 'Sconosciuto'
        },
        "stagioni": {
            'spring': 'Primavera', 'summer': 'Estate', 'winter': 'Inverno',
            'autumn': 'Autunno', 'unknown': 'Sconosciuto'
        }
    }

    def __init__(self, analysis_dir, stats_file1, stats_file2):
        self.individual_stats = self._load_json(os.path.join(analysis_dir, stats_file1))
        self.aggregated_stats = self._load_json(os.path.join(analysis_dir, stats_file2))

    @staticmethod
    def _load_json(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def _translate(data, mapping):
        """Traduce le chiavi del dict secondo il mapping fornito."""
        return {mapping.get(k, k): v for k, v in data.items()}

    def _get_color_map(self, labels, palette_key="default"):
        """Restituisce un mapping coerente label→colore."""
        palette = self.COLOR_PALETTES.get(palette_key, self.COLOR_PALETTES["default"])
        return {label: palette.get(label, "#ff6b6b") for label in labels}

    def _plot_pie(self, data, title, translation=None, palette_key="default"):
        if not data:
            st.info("Nessun dato disponibile")
            return

        plot_data = self._translate(data, translation) if translation else data
        labels = list(plot_data.keys())
        color_map = self._get_color_map(labels, palette_key)

        fig = px.pie(
            values=list(plot_data.values()),
            names=labels,
            title=title,
            color=labels,
            color_discrete_map=color_map
        )
        st.plotly_chart(fig, use_container_width=True)

    def _plot_bar(self, data, title, x_title="Categoria", y_title="Valore",
                  translation=None, palette_key="default", exclude_unknown=True):
        if not data:
            st.info("Nessun dato disponibile")
            return

        plot_data = {
            k: v for k, v in data.items()
            if not (exclude_unknown and k.lower() in ["unknown", "sconosciuto"])
        }

        if translation:
            plot_data = self._translate(plot_data, translation)

        if not plot_data:
            st.info("Nessun dato disponibile (solo sconosciuti)")
            return

        labels = list(plot_data.keys())
        color_map = self._get_color_map(labels, palette_key)

        fig = px.bar(
            x=labels,
            y=list(plot_data.values()),
            title=title,
            color=labels,
            color_discrete_map=color_map
        )
        fig.update_layout(xaxis_title=x_title, yaxis_title=y_title)
        st.plotly_chart(fig, use_container_width=True)

    # ---------------- Dashboard ---------------- #

    def run_dashboard(self):
        st.set_page_config(page_title="Dashboard Statistiche Film", page_icon="🎬", layout="wide")

        st.title("🎬 Dashboard Statistiche Film")
        summary = self.aggregated_stats["analysis_summary"]
        st.markdown(
            f"Analisi di {summary['total_films_analyzed']} film e "
            f"{summary['total_scenes_analyzed']:,} scene cinematografiche"
        )

        # Metriche principali
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Film Analizzati", summary["total_films_analyzed"])
        with col2:
            st.metric("Scene Totali", f"{summary['total_scenes_analyzed']:,}")
        with col3:
            st.metric("Scene per Film", f"{summary['average_scenes_per_film']:.1f}")
        with col4:
            self._metric_scene_interne()

        stats = self.aggregated_stats["aggregated_statistics"]

        # Distribuzioni generali
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Distribuzione Interni vs Esterni")
            self._plot_pie(stats["locations"]["int_ext_totals"], "Interno vs Esterno",
                           self.TRANSLATIONS["int_ext"], "int_ext")
        with col2:
            st.subheader("Distribuzione per Ambiente")
            self._plot_bar(stats["locations"]["environment_totals"], "Ambienti",
                           x_title="Ambiente", y_title="Scene")

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Periodi del Giorno")
            self._plot_pie(stats["temporal"]["period_totals"], "Periodi del Giorno",
                           self.TRANSLATIONS["periodi"], "periodi")
        with col2:
            st.subheader("Distribuzione Stagionale")
            self._plot_pie(stats["temporal"]["season_totals"], "Stagioni",
                           self.TRANSLATIONS["stagioni"], "stagioni")

        # Confronto tra film
        st.markdown("---")
        st.header("📊 Confronto tra Film")
        self._compare_films()

        # Analisi singoli film
        st.markdown("---")
        st.header("📊 Analisi Dettagliata Singoli Film")
        film_names = [film["film"] for film in self.individual_stats]
        selected_film = st.selectbox("Seleziona un film:", film_names)
        film_data = next((f for f in self.individual_stats if f["film"] == selected_film), None)
        if film_data:
            self._display_film_analysis(film_data)

    # ---------------- Metriche ---------------- #

    def _metric_scene_interne(self):
        perc = self.aggregated_stats["aggregated_statistics"]["locations"]["int_ext_percentages"]
        known = sum(v for k, v in perc.items() if k != "UNKNOWN")
        if known > 0:
            val = perc.get("INT", 0) * 100 / known
            st.metric("Scene Interne", f"{val:.1f}%")
        else:
            st.metric("Scene Interne", "N/A")

    # ---------------- Analisi comparativa ---------------- #

    def _compare_films(self):
        self._stacked_bar("Distribuzione Interno/Esterno per film", "int_ext_distribution",
                          self.TRANSLATIONS["int_ext"], "int_ext")
        self._stacked_bar("Distribuzione fasi del giorno per film", "day_night_distribution",
                          self.TRANSLATIONS["periodi"], "periodi")
        self._stacked_bar("Distribuzione stagioni per film", "season_distribution",
                          self.TRANSLATIONS["stagioni"], "stagioni")

    def _stacked_bar(self, title, key, translation, palette_key):
        data = []
        for film in self.individual_stats:
            name = film.get("film", "N/A")
            dist = film.get("statistics", {}).get("temporal" if "day" in key or "season" in key else "locations", {}).get(key, {})
            for k, v in dist.items():
                if k.lower() not in ["unknown"]:
                    data.append({"Film": name, "Categoria": translation.get(k, k), "Scene": v})

        if data:
            fig = px.bar(data, x="Film", y="Scene", color="Categoria",
                         barmode="stack", title=title, color_discrete_map=self.COLOR_PALETTES[palette_key])
            fig.update_layout(xaxis=dict(showticklabels=False))
            st.plotly_chart(fig, use_container_width=True)

    # ---------------- Analisi singolo film ---------------- #

    def _display_film_analysis(self, film_data):
        st.subheader(f"🏞️ Analisi Locations - {film_data['film']}")
        col1, col2 = st.columns(2)
        with col1:
            self._plot_pie(film_data["statistics"]["locations"].get("int_ext_distribution", {}),
                           "Interno vs Esterno", self.TRANSLATIONS["int_ext"], "int_ext")
        with col2:
            self._plot_bar(film_data["statistics"]["locations"].get("environment_distribution", {}),
                           "Ambienti", x_title="Ambiente", y_title="Scene")

        st.subheader(f"⏰ Analisi Temporale - {film_data['film']}")
        col1, col2 = st.columns(2)
        with col1:
            self._plot_pie(film_data["statistics"]["temporal"].get("day_night_distribution", {}),
                           "Periodi Giorno", self.TRANSLATIONS["periodi"], "periodi")
        with col2:
            self._plot_pie(film_data["statistics"]["temporal"].get("season_distribution", {}),
                           "Stagioni", self.TRANSLATIONS["stagioni"], "stagioni")


if __name__ == "__main__":
    analysis_dir = "analysis"
    dashboard = StreamlitDashboard(
        analysis_dir,
        "screenplay_analysis.json",
        "screenplay_analysis_macro_stats.json"
    )
    dashboard.run_dashboard()
