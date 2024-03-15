from typing import Callable

from irrCAC.raw import CAC
from pandera.typing import DataFrame
import pandas as pd
import streamlit as st
import krippendorff

TEACHING_PRINCIPLE_TO_OBSERVATION_CATEGORY = {
    "Action orientation": "HANDLUNG",
    "Experience based": "ERFAHRUNG",
    "Holistic Approach": "GANZHEITLICH",

    "Competence orientation 1": "KOMPETENZ_1",
    "Competence orientation 2": "KOMPETENZ_2",

    "Motivation": "MOTIVIERUNG",
    "Target orientation": "ZIEL",
    "Process orientation": "PROZESS",
    "Independence": "SELBSTSTÄNDIGKEIT",
    "Learner orientation": "LERNERO.",
    "Participation": "PARTIZIPATION",
    "Experiencing self - efficiency": "SELBSTWIRKSAMKEIT",
    "Cooperative learning": "KOOPERATIV",
    "Variety of methods": "METHODEN",
    "Visualization": "VERANSCHAULICHUNG",
    "Transparent performance expectations": "LEISTUNG",
    "Intelligent practice": "ÜBEN",
    "Fuse of content": "SICHERUNG",
    "Differentiation 1": "DIFFERENZIERUNG_1",
    "Differentiation 2": "DIFFERENZIERUNG_2",

    "Activate prior knowledge": "VORWISSEN",
    "Interdisciplinary": "VERBINDEND",
    "Authentic & problem based learning experiences": "WIRKLICHKEIT",

    "Structure & clarity 1": "STRUKTUR_1",
    "Structure & clarity 2": "STRUKTUR_2",

    "Time utilization 1": "LERNZEIT_1",
    "Time utilization 2": "LERNZEIT_2",

    "Communication 1": "KOMMUNIKATION_1",
    "Communication 2": "KOMMUNIKATION_2",
    "Communication 3": "KOMMUNIKATION_3",

    "Learning - friendly classroom climate 1": "KLIMA_1",
    "Learning - friendly classroom climate 2": "KLIMA_2",
    "Learning - friendly classroom climate 3": "KLIMA_3",
    "Learning - friendly classroom climate 4": "KLIMA_4",
    "Learning - friendly classroom climate 5": "KLIMA_5",

    "learning environment 1": "LERNORT_1",
    "learning environment 2": "LERNORT_2",
    "learning environment 3": "LERNORT_3",

    "Use of the learning environment": "DRAUßEN",
}

OBSERVATION_CATEGORY_TO_TEACHING_PRINCIPLE = {
    v: k for k, v in TEACHING_PRINCIPLE_TO_OBSERVATION_CATEGORY.items()
}


def map_principles(mapping: dict) -> Callable:
    def _map_principles(x):
        return mapping.get(x, x)
    return _map_principles


def read_input_excel(file_name: str) -> DataFrame:
    return pd.read_excel(file_name, sheet_name="data_transformed")


RATER_1 = "Rater_1"
RATER_2 = "Rater_2"
MEASURES = [RATER_1, RATER_2]

SITUATION = "Situation"
SOZIALFORM = "Sozialform"
SKALA = "Skala"

KATEGORIE = "Kategorie"
BEOBACHTUNG_ID = "Beobachtung ID"

CATEGORICAL_PRE_FILTER = [SITUATION, SOZIALFORM, SKALA]
DIMENSION = [KATEGORIE, *CATEGORICAL_PRE_FILTER]

RATING_CATEGORIES = [1, 2, 3, 4, 5, 6]


def calculate_ac2(data: DataFrame):
    cac = CAC(data[[RATER_1, RATER_2]], weights="ordinal", categories=RATING_CATEGORIES)
    return cac.gwet()


def calculate_krippendorff(data: DataFrame) -> float:
    rater_1 = data[RATER_1].values
    rater_2 = data[RATER_2].values
    result = krippendorff.alpha(
        reliability_data=[rater_1, rater_2], level_of_measurement="ordinal"
    )
    return result


def is_observation_id_gte(version: int) -> Callable:
    return lambda x: int(str(x).split(".")[1]) >= version


def analyze_by_one_dimension(data: DataFrame, dimension: str) -> list:
    result = []
    for analyze_by_value in data[dimension].unique():
        filtered_data = data[data[dimension] == analyze_by_value]
        try:
            inter_rater_reliability = calculate_ac2(filtered_data)
            result.append(
                {
                    dimension: analyze_by_value,
                    "inter_rater_reliability": inter_rater_reliability["est"][
                        "coefficient_value"
                    ],
                    "n": len(filtered_data)
                }
            )
        except Exception as e:
            st.error(f"Error for {analyze_by_value}: {e}")
    return result


st.title("OPTIS inter rater reliability")

DATASETS = INTER_RATER, INTER_RATER_TEST, INTRA_RATER = [
    "Inter-Rater Pilotierung",
    "Inter-Rater Pilotierung Testphase",
    "Intra-Rater Pilotierung",
]

LABEL_TO_FILE = {
    INTER_RATER: "OPTIS_Interrater_Pilotierung.xlsx",
    INTER_RATER_TEST: "OPTIS_Interrater_Pilotierung_Testphase.xlsx",
    INTRA_RATER: "OPTIS_Intrarater_Pilotierung.xlsx",
}

FILE_UPLOAD = "Excel datei hochladen"

DATASET_OPTIONS = [*DATASETS, FILE_UPLOAD]

data_set = st.selectbox("Daten Set auswählen", options=DATASET_OPTIONS)

if data_set == FILE_UPLOAD:
    uploaded_file = st.file_uploader("Input Excel")
    if uploaded_file is not None:
        try:
            data = read_input_excel(uploaded_file)
        except Exception as e:
            st.error(f"Error reading file: {e}")
            st.stop()
    else:
        st.stop()
else:
    data = read_input_excel(f"data/{LABEL_TO_FILE[data_set]}")

data[KATEGORIE] = data[KATEGORIE].map(map_principles(OBSERVATION_CATEGORY_TO_TEACHING_PRINCIPLE))

st.subheader("Rohdaten")
st.write(data)

st.header("Analyse")

min_observation_id = st.number_input("Minimale Beobachtungs ID", value=1)
data = data[data[BEOBACHTUNG_ID].apply(is_observation_id_gte(min_observation_id))]
for dimension in CATEGORICAL_PRE_FILTER:
    analyze_by_value = st.multiselect(
        f"{dimension} Filter",
        options=data[dimension].unique(),
        default=data[dimension].unique(),
    )
    data = data[data[dimension].isin(analyze_by_value)]

analyze_by = st.selectbox("Analysiere per", options=DIMENSION)

result = []
for analyze_by_value in data[analyze_by].unique():
    filtered_data = data[data[analyze_by] == analyze_by_value]
    try:
        inter_rater_reliability = calculate_ac2(filtered_data)
        result.append(
            {
                analyze_by: analyze_by_value,
                "inter_rater_reliability": inter_rater_reliability["est"][
                    "coefficient_value"
                ],
            }
        )
    except Exception as e:
        st.error(f"Error for {analyze_by_value}: {e}")

st.dataframe(result)