from typing import Callable

from pandera.typing import DataFrame
import pandas as pd
import streamlit as st
import krippendorff


def read_input(file_name: str) -> DataFrame:
    return pd.read_excel(file_name, sheet_name="data_transformed")


TM = "TM"
X = "X"
MEASURES = [TM, X]

SITUATION = "Situation"
SOZIALFORM = "Sozialform"
SKALA = "Skala"
CATEGORICAL_PRE_FILTER = [SITUATION, SOZIALFORM, SKALA]

KATEGORIE = "Kategorie"
BEOBACHTUNG_ID = "Beobachtung ID"
DIMENSION = [*CATEGORICAL_PRE_FILTER, KATEGORIE, BEOBACHTUNG_ID]


def calculate_krippendorff(data: DataFrame) -> float:
    tm = data[TM].values
    x = data[X].values
    result = krippendorff.alpha(
        reliability_data=[tm, x], level_of_measurement="ordinal"
    )
    return result


def is_observation_id_gte(version: int) -> Callable:
    return lambda x: int(x.split(".")[1]) >= version


st.title("Krippendorff's Alpha in der Schule")

uploaded_file = st.file_uploader("Input Excel")
if uploaded_file is not None:
    data = read_input(uploaded_file)
else:
    st.stop()

st.subheader("Input data")
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
        inter_rater_reliability = calculate_krippendorff(filtered_data)
        result.append(
            {
                analyze_by: analyze_by_value,
                "inter_rater_reliability": inter_rater_reliability,
            }
        )
    except Exception as e:
        st.error(f"Error for {analyze_by_value}: {e}")


st.dataframe(result)
