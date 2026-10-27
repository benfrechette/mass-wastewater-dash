import streamlit as st
import pandas as pd

# Load current data
WastewaterData = pd.read_csv("National/data/Wastewater-20261026.csv")

# Establish page configuration
st.set_page_config(
    page_title="United States Wastewater Dashboard",
    layout="wide"
)
st.title("United States Wastewater Dashboard")
st.write("SARS-CoV-2 pathogen surveillance")

# Dataframe Filters
st.subheader("Filters")

col1, col2, col3 = st.columns(3)

with col1:
    state = sorted(
        WastewaterData["state_territory"].dropna().unique()
    )
    state = st.selectbox(
        "State or Territory",
        ["All states"] + list(state)
    )

with col2:
    county = sorted(WastewaterData["counties_served"].dropna().unique())
    county = st.selectbox(
        "County",
        ["All counties"] + list(county)
    )

with col3:
    search = st.text_input("Search records")


# Apply filters
filtered = WastewaterData.copy()

if state != "All states":
    filtered = filtered[
        filtered["state_territory"] == state
    ]

if county != "All counties":
    filtered = filtered[
        filtered["counties_served"] == county
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
metric1.metric(
    "Total Records", 
    f"{len(filtered):,}"
)
metric2.metric(
    "Monitoring Sites",
    f"{filtered['site'].nunique():,}"
)
metric3.metric(
    "Detected Records",
    f"{filtered['pcr_target_detect'].str.lower().eq('yes').sum():,}"
)

# Print Dataframe
st.dataframe(filtered)


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
