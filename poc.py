import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as pgo
import geopandas
from geopandas.tools import sjoin
import html
import json
from datetime import datetime, timedelta
from sodapy import Socrata
from shapely import Point
from shapely.geometry import shape

# Socrata Info
# Socrata Dataset IDs
COMMUNITY_NAMES_ID = 'surr-xmvs'
LAND_USE_ID = '33vi-ew4s'
DEVELOPMENT_PERMIT_ID = '6933-unw5'
BUILDING_PERMIT_ID = 'c2es-76ed'
TENANCY_CHANGE_ID = 'wrtt-2nqs'

# -365 days in '2020-12-31T00:00:00'
DATE = (datetime.today() - timedelta(days=365)).strftime('%Y-%m-%dT00:00:00')
# Set a default in case things go very wrong.
community_name = 'SUNALTA'

st.set_page_config(page_title="Calgary Communities Development Map", layout="wide")
st.title("Community Development Map")
# Remove margin at top of page
st.markdown("""<style>.appview-container { margin-top: -65px; padding: 0; }</style>""", unsafe_allow_html=True)

# st.cache_data - will cache the output of the function
# Keep cache for 24 hours - it's updated daily
@st.cache_data(ttl=60*60*24)
def load_data(dataID, community_name):
    results = socrata_client.get(dataID,
                                 limit=100,
                                 communityname=community_name,
                                 where="applieddate > '" + DATE + "'",
                                 order="applieddate DESC",
                                 exclude_system_fields=True)
    data = pd.DataFrame.from_dict(results)
    return data

# Separate loading for Land Use Data because it does not share many of the same fields as other datasets
@st.cache_data(ttl=60*60*24)
def load_land_use_data(dataID):
    results = socrata_client.get(dataID,
                                 limit=1000,
                                 where="applieddate > '" + DATE + "'",
                                 order="applieddate DESC",
                                 exclude_system_fields=True)
    data = pd.DataFrame.from_dict(results)
    return data

@st.cache_data(ttl=60*60*24)
def load_community_data(dataID):
    results = socrata_client.get(dataID,
                                 order="name ASC",
                                 exclude_system_fields=True)
    data = pd.DataFrame.from_dict(results)
    return data

socrata_client = Socrata("data.calgary.ca", st.secrets["socrata_token"])

community_data = load_community_data(COMMUNITY_NAMES_ID)

st.sidebar.title("Community")

# If ?community_name is set, grab it
params = st.query_params.to_dict()
# init value just in case
index=0

if 'community_name' in params:
    #Turn to uppercase and remove HTML encoding just in case.
    community_name=html.unescape(params['community_name'][0].upper())

    try:
        newIndex = community_data.loc[community_data['name'] == community_name].index[0]
        index = int(newIndex)
    except:
        st.warning("Community Name not found. Reverting to defaults")
        newIndex = community_data.loc[community_data['name'] == "SUNALTA"].index[0]
        index = int(newIndex)
else:
    newIndex = community_data.loc[community_data['name'] == community_name].index[0]
    index = int(newIndex)

community_name = st.sidebar.selectbox('Choose community:', community_data['name'], index)

# Grab the current community's polygon
selected_community = community_data.loc[community_data['name'] == community_name]
selected_community_geometry = selected_community['multipolygon'].apply(lambda x: shape(x))
selected_community_gdf = geopandas.GeoDataFrame(selected_community, geometry=selected_community_geometry)

st.sidebar.markdown('Note: typing the name is easier')

# Load Land Use Data
with st.spinner('Loading Land Use...'):
    land_use_data = load_land_use_data(LAND_USE_ID)

# Clean data for joint data frame display
land_use_data = land_use_data.drop(['permittype',
                                    'fromlud',
                                    'proposedlud',
                                    'locationcount',
                                    'multipoint',
                                    'completeddate'],
                                    axis=1)
land_use_data = land_use_data.astype({"longitude": np.float64, "latitude": np.float64})

# Remove land use data from the table if it's not within the community
land_use_geometry = [Point(xy) for xy in zip(land_use_data['longitude'], land_use_data['latitude'])]
land_use_gdf = geopandas.GeoDataFrame(land_use_data, geometry=land_use_geometry)

filtered_land_use_data = sjoin(land_use_gdf, selected_community_gdf, how='inner')

# Create DMAP links on land use permits
filtered_land_use_data['permitnum'] = 'https://developmentmap.calgary.ca/?find=' + filtered_land_use_data['permitnum']

# Load DP data
with st.spinner('Loading DPs...'):
    dev_data = load_data(DEVELOPMENT_PERMIT_ID, community_name)

# Clean data for joint data frame display
dev_data = dev_data.drop(['proposedusecode',
                          'communitycode',
                          'communityname',
                          'ward',
                          'quadrant',
                          'locationtypes',
                          'locationsgeojson',
                          'locationswkt',
                          'locationcount',
                          'locationaddresses'],
                         axis=1)

# Dev lat/long is rounded. Use point data (dev_data.point[X]['coordinates'])
# Extract lat and lon from the points
lats = []
lons = []
for i in dev_data.point:
    lats.append(i['coordinates'][1])
    lons.append(i['coordinates'][0])

dev_data['latitude'] = pd.Series(lats, copy=False, dtype=np.float64)
dev_data['longitude'] = pd.Series(lons, copy=False, dtype=np.float64)

# Create DMAP links on dev permits
dev_data['permitnum'] = 'https://developmentmap.calgary.ca/?find=' + dev_data['permitnum']

# Load BP data
with st.spinner('Loading BPs...'):
    bp_data = load_data(BUILDING_PERMIT_ID, community_name)

# Clean data for joint data frame display
bp_data = bp_data.drop(['permittypemapped',
                        'permitclassgroup',
                        'permitclassmapped',
                        'workclassgroup',
                        'communitycode',
                        'communityname',
                        'locationcount',
                        'locationtypes',
                        'locationaddresses',
                        'locationswkt',
                        'locationsgeojson',
                        'workclassmapped'],
                       axis=1)
bp_data = bp_data.astype({"longitude": np.float64, "latitude": np.float64})

# Load tenancy data
with st.spinner('Loading Tenancy info...'):
    tc_data = load_data(TENANCY_CHANGE_ID, community_name)

# Clean data for joint data frame display
tc_data = tc_data.drop(['permittype',
                        'communitycode',
                        'communityname',
                        'quadrant',
                        'ward'],
                      axis=1)
# TC lat/long is rounded. Use point data (tc_data.point[X]['coordinates'])
# Extract lat and lon from the points
lats = []
lons = []
for i in tc_data.point:
    lats.append(i['coordinates'][1])
    lons.append(i['coordinates'][0])

tc_data['latitude'] = pd.Series(lats, copy=False, dtype=np.float64)
tc_data['longitude'] = pd.Series(lons, copy=False, dtype=np.float64)

# Roughly calculate centre of community - based on the building permit data
# Could not figure out how to use the GeoJSON object in community_data when this was written
gdf = geopandas.GeoDataFrame(
    bp_data, geometry=geopandas.points_from_xy(bp_data.longitude, bp_data.latitude))


map_centre_x = selected_community_gdf.geometry.centroid.x.mean()
map_centre_y = selected_community_gdf.geometry.centroid.y.mean()

# Rename some columns for normalization
bp_data = bp_data.rename(columns={"originaladdress": "address"})
tc_data = tc_data.rename(columns={"applicantname": "applicant", "originaladdress": "address", "proposeduse": "description"})


all_data = pd.concat([dev_data, bp_data, tc_data, filtered_land_use_data])
# Filter data - could use pandas filters instead
all_data = all_data[['permitnum',
                     'address',
                     'applicant',
                     'description',
                     'applieddate',
                     'statuscurrent',
                     'permittype',
                     'estprojectcost',
                     'contractorname',
                     'issueddate']]

#Convert datetimes to dates
all_data['applieddate'] = pd.to_datetime(all_data['applieddate']).dt.date
all_data['issueddate'] = pd.to_datetime(all_data['issueddate']).dt.date

all_data.sort_values(by=['applieddate'], ascending=False, inplace=True)


fig = pgo.Figure()

# Plotly's version of Layer is Trace
# Zesty Colour Palette from https://venngage.com/blog/color-blind-friendly-palette/
fig.add_trace(pgo.Scattermap(
    lat=filtered_land_use_data['latitude'],
    lon=filtered_land_use_data['longitude'],
    mode='markers',
    marker=pgo.scattermap.Marker(
        size=13,
        color='rgb(245,121,58)',
        opacity=0.7,
    ),
    text=filtered_land_use_data['permitnum'],
    meta=filtered_land_use_data['statuscurrent'],
    customdata=filtered_land_use_data['description'],
    hovertemplate = "%{text}:<br>Status: %{meta}<br><br>Description: %{customdata}",
    name='Land Use'
))

fig.add_trace(pgo.Scattermap(
    lat=dev_data['latitude'],
    lon=dev_data['longitude'],
    mode='markers',
    marker=pgo.scattermap.Marker(
        size=13,
        color='rgb(169, 90, 161)',
        opacity=0.7,
    ),
    text=dev_data['permitnum'],
    meta=dev_data['statuscurrent'],
    customdata=dev_data['description'],
    hovertemplate = "%{text}:<br>Status: %{meta}<br><br>Description: %{customdata}",
    name='Development Permits'
))

fig.add_trace(pgo.Scattermap(
    lat=bp_data['latitude'],
    lon=bp_data['longitude'],
    mode='markers',
    marker=pgo.scattermap.Marker(
        size=13,
        color='rgb(133, 192, 249)',
        opacity=0.7,
    ),
    text=bp_data['permitnum'],
    meta=bp_data['statuscurrent'],
    customdata=bp_data['description'],
    hovertemplate = "%{text}:<br>Status: %{meta}<br><br>Description: %{customdata}",
    name='Building Permits'
))

fig.add_trace(pgo.Scattermap(
    lat=tc_data['latitude'],
    lon=tc_data['longitude'],
    mode='markers',
    marker=pgo.scattermap.Marker(
        size=13,
        color='rgb(15, 32, 128)',
        opacity=0.7
    ),
    text=tc_data['permitnum'],
    meta=tc_data['statuscurrent'],
    customdata=tc_data['applicant'],
    hovertemplate = "%{text}:<br>Status: %{meta}<br><br>Description: %{customdata}",
    name='Tenancy Changes'
))

fig.update_layout(
    margin = {
        "r": 0,
        "t": 33,
        "l": 0,
        "b": 0,
        },
    height=600,
    hovermode='closest',
    clickmode='select',
    showlegend=True,
    legend_orientation='h',
    legend_y=1.05,
    map=dict(
        bearing=0,
        center=dict(
            lat=map_centre_y,
            lon=map_centre_x
        ),
        pitch=0,
        zoom=14,
        style='light'
    ),
)

st.plotly_chart(fig, use_container_width=True)

st.dataframe(all_data, hide_index=True, use_container_width=True, height=(len(all_data.index) + 1) * 35 + 3,
    column_config={
        "permitnum": st.column_config.LinkColumn(
            "Permit Number",
            display_text="=(.*)"
        ),
        "address": st.column_config.TextColumn("Address"),
        "applicant": st.column_config.TextColumn("Applicant", width="medium"),
        "description": st.column_config.TextColumn("Description"),
        "applieddate": st.column_config.DateColumn("Application Date"),
        "statuscurrent": st.column_config.TextColumn("Status"),
        "permittype": st.column_config.TextColumn("Permit Type"),
        "estprojectcost": st.column_config.TextColumn("Estimated Project Cost"),
        "contractorname": st.column_config.TextColumn("Contractor Name"),
        "issueddate": st.column_config.DateColumn("Issued Date"),
    })

st.sidebar.markdown("""
----
Collating a bunch of data one place to make things easier. Data is cached for 24 hours.  
Land use changes do *not* appear in the table.

All data is from [data.calgary.ca](https://data.calgary.ca):

- [Community Boundaries](https://data.calgary.ca/Base-Maps/Community-District-Boundaries/surr-xmvs)
- [Land Use](https://data.calgary.ca/dataset/Land-Use-Redesignation-Applications/33vi-ew4s)
- [Development Permits](https://data.calgary.ca/dataset/Development-Permits/6933-unw5)
- [Building Permits](https://data.calgary.ca/Business-and-Economic-Activity/Building-Permits/c2es-76ed)
- [Tenancy Changes](https://data.calgary.ca/dataset/Tenancy-Change-Applications/wrtt-2nqs)

[Forks and PRs greatly appreciated at GitHub](https://github.com/chealion/yycdevmap)
""")
