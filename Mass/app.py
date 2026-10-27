import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Massachusetts Wastewater Dashboard",
    layout="wide"
)

DATA_FILE = "data/Wastewater Data-Table 1.csv"


@st.cache_data
def load_data():
    # Find the actual column header, even if metadata comes first.
    with open(DATA_FILE, "r", encoding="utf-8-sig") as file:
        lines = file.readlines()

    header_index = next(
        (
            i for i, line in enumerate(lines)
            if line.strip().startswith("respiratory_season,pathogen,")
        ),
        None
    )

    if header_index is None:
        raise ValueError("Could not find the CSV column headers.")

    # Read the CSV starting at its header row.
    from io import StringIO

    data = pd.read_csv(
        StringIO("".join(lines[header_index:])),
        skipinitialspace=True
    )

    # Remove an empty column if the CSV header ends with a comma.
    data = data.loc[:, ~data.columns.astype(str).str.startswith("Unnamed:")]

    # Clean up column names and text values.
    data.columns = data.columns.str.strip()

    for column in data.select_dtypes(include="object").columns:
        data[column] = data[column].str.strip()

    data["sample_collection_date"] = pd.to_datetime(
        data["sample_collection_date"],
        errors="coerce"
    )

    data["concentration_copies_per_l"] = pd.to_numeric(
        data["concentration_copies_per_l"],
        errors="coerce"
    )

    return data


try:
    data = load_data()
except Exception as error:
    st.error(f"Could not load the wastewater data: {error}")
    st.stop()






st.title("Massachusetts Wastewater Dashboard")
st.write("Respiratory pathogen surveillance")


# Filters
st.subheader("Filters")

col1, col2, col3, col4 = st.columns(4)

with col1:
    seasons = sorted(
        data["respiratory_season"].dropna().unique()
    )
    season = st.selectbox(
        "Respiratory Season",
        ["All seasons"] + list(seasons)
    )

with col2:
    pathogens = sorted(data["pathogen"].dropna().unique())
    pathogen = st.selectbox(
        "Pathogen",
        ["All pathogens"] + list(pathogens)
    )

with col3:
    labs = sorted(data["testing_lab"].dropna().unique())
    lab = st.selectbox(
        "Testing Lab",
        ["All labs"] + list(labs)
    )

with col4:
    search = st.text_input("Search records")


# Apply filters
filtered = data.copy()

if season != "All seasons":
    filtered = filtered[
        filtered["respiratory_season"] == season
    ]

if pathogen != "All pathogens":
    filtered = filtered[
        filtered["pathogen"] == pathogen
    ]

if lab != "All labs":
    filtered = filtered[
        filtered["testing_lab"] == lab
    ]

if search:
    matches = filtered.astype(str).apply(
        lambda column: column.str.contains(
            search,
            case=False,
            regex=False,
            na=False
        )
    ).any(axis=1)

    filtered = filtered[matches]


# Summary metrics
st.subheader("Summary")

metric1, metric2, metric3, metric4 = st.columns(4)

metric1.metric("Total Records", f"{len(filtered):,}")

metric2.metric(
    "Monitoring Sites",
    f"{filtered['sampling_location'].nunique():,}"
)

metric3.metric(
    "Detected Records",
    f"{filtered['detect_status'].str.lower().eq('detected').sum():,}"
)

metric4.metric(
    "Outlier Records",
    f"{filtered['is_outlier'].sum():,}"
)


# Chart
st.subheader("Concentration Over Time")

chart_data = filtered.dropna(
    subset=["sample_collection_date", "concentration_copies_per_l"]
)

if not chart_data.empty:
    daily_average = (
        chart_data.groupby("sample_collection_date")[
            "concentration_copies_per_l"
        ]
        .mean()
        .sort_index()
    )

    st.line_chart(
        daily_average,
        x_label="Collection Date",
        y_label="Mean Concentration (copies/L)"
    )
else:
    st.info("No concentration data available for these filters.")


# Table
st.subheader("Wastewater Records")

columns = [
    "sample_collection_date",
    "pathogen",
    "pathogen_target",
    "organization",
    "testing_lab",
    "detect_status",
    "concentration_copies_per_l"
]

st.dataframe(
    filtered[columns].head(500),
    use_container_width=True,
    hide_index=True
)

st.caption(
    f"Showing {min(len(filtered), 500):,} of "
    f"{len(filtered):,} matching records."
)
