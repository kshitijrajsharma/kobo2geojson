import json
import re

import folium
import geopandas as gpd
import pandas as pd
import streamlit as st
from streamlit_folium import folium_static


def clean_column_name(name):
    return re.sub(r"[^\w\s]", "", name).replace(" ", "_").lower()


def convert_to_geojson(df, lat_col, lon_col):
    gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df[lon_col], df[lat_col]))
    gdf = gdf.drop(columns=[lat_col, lon_col])
    gdf = gdf.rename(columns={col: clean_column_name(col) for col in gdf.columns})
    return json.loads(gdf.to_json())


def plot_geojson(geojson_data):

    center_lat = geojson_data["features"][0]["geometry"]["coordinates"][1]
    center_lon = geojson_data["features"][0]["geometry"]["coordinates"][0]

    m = folium.Map(location=[center_lat, center_lon], zoom_start=10)

    geoj = folium.GeoJson(geojson_data, name="geojson")

    label_attributes = []
    for feature in geojson_data["features"]:

        for key, value in feature["properties"].items():
            if key not in label_attributes:
                label_attributes.append(key)
        break

    folium.features.GeoJsonPopup(
        fields=label_attributes,
        aliases=label_attributes,
        localize=True,
        labels=True,
        style="""
        background-color: #F0EFEF;
        border: 2px solid black;
        border-radius: 3px;
        box-shadow: 3px;
    """,
        max_width=300,
        max_height=200,
    ).add_to(geoj)
    geoj.add_to(m)

    return m


def main():
    st.title("Kobo Excel/CSV to GeoJSON Converter")

    uploaded_file = st.file_uploader(
        "Choose an XLSX or CSV file output from KoboToolbox", type=["xlsx", "csv"]
    )

    if uploaded_file is not None:
        with st.spinner("Reading file..."):
            if uploaded_file.name.endswith(".csv"):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)

        st.write("Preview of the uploaded data:")
        st.write(df.head())

        columns = df.columns.tolist()
        lat_col = st.selectbox("Select the latitude column", columns)
        lon_col = st.selectbox("Select the longitude column", columns)

        output_format = st.selectbox("Select output format", ["GeoJSON"])

        if st.button("Convert"):
            with st.spinner("Converting..."):
                if output_format == "GeoJSON":
                    result = convert_to_geojson(df, lat_col, lon_col)
                    output = json.dumps(result, indent=2)
                    file_extension = "geojson"
                    mime_type = "application/json"
                    # elif output_format == "Shapefile":
                    #     output = df.to_csv(index=False)
                    #     file_extension = "csv"
                    #     mime_type = "text/csv"
                    # else:  # Excel
                    #     output = df.to_excel(index=False)
                    #     file_extension = "xlsx"
                    #     mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

                    st.success("Conversion complete!")
                    st.subheader("Map")
                    m = plot_geojson(result)
                    folium_static(m)
            st.download_button(
                label=f"Download {output_format}",
                data=output,
                file_name=f"converted_data.{file_extension}",
                mime=mime_type,
            )


if __name__ == "__main__":
    main()
