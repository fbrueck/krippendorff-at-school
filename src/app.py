from typing import Callable

from irrCAC.raw import CAC
from pandera.typing import DataFrame
import pandas as pd
import streamlit as st
import krippendorff


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



def analyze_by_two_dimensions(data: DataFrame, dimension_1: str, dimension_2: str) -> list:
    result = []
    for analyze_by_value in data[[dimension_1, dimension_2]].drop_duplicates().itertuples(index=False):
        filtered_data = data[
            (data[dimension_1] == analyze_by_value[0])
            & (data[dimension_2] == analyze_by_value[1])
        ]
        try:
            inter_rater_reliability = calculate_ac2(filtered_data)
            result.append(
                {
                    dimension_1: analyze_by_value[0],
                    dimension_2: analyze_by_value[1],
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

analyze_by = st.multiselect("Analysiere per", options=DIMENSION, max_selections=2)

if not analyze_by:
    st.warning("Please select at least one dimension to analyze")
elif len(analyze_by) == 2:
    result = analyze_by_two_dimensions(data, *analyze_by)
    st.dataframe(result)
else:
    result = analyze_by_one_dimension(data, analyze_by[0])
    st.dataframe(result)
