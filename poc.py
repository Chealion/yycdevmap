import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as pgo
from datetime import datetime, timedelta
import geopandas 

from sodapy import Socrata

# Socrata Info
# Socrata Dataset IDs
COMMUNITY_NAMES_ID = 'surr-xmvs'
LAND_USE_ID = '33vi-ew4s'
DEVELOPMENT_PERMIT_ID = '6933-unw5'
BUILDING_PERMIT_ID = 'c2es-76ed'
TENANCY_CHANGE_ID = 'wrtt-2nqs'

# -365 days in '2020-12-31T00:00:00'
DATE = (datetime.today() - timedelta(days=365)).strftime('%Y-%m-%dT00:00:00')
# Set a default
community_name = 'SUNALTA'

# Start presenting
st.set_page_config(page_title="Calgary Communities Development Map", layout="wide")
st.title("Community Development Map")

# st.cache - will cache the output of the function
# Keep cache for 24 hours - it's updated daily
@st.cache(suppress_st_warning=True, ttl=60*60*24)
def load_data(dataID):
    results = socrata_client.get(dataID,
                                 limit=100,
                                 communityname=community_name,
                                 where="applieddate > '" + DATE + "'",
                                 order="applieddate DESC",
                                 exclude_system_fields=True)
    data = pd.DataFrame.from_dict(results)
    return data

# Separate loading for Land Use Data because it's not consistent with every other dataset
@st.cache(suppress_st_warning=True, ttl=60*60*24)
def load_land_use_data(dataID):
    results = socrata_client.get(dataID,
                                 limit=1000,
                                 where="applieddate > '" + DATE + "'",
                                 order="applieddate DESC",
                                 exclude_system_fields=True)
    data = pd.DataFrame.from_dict(results)
    return data

@st.cache(suppress_st_warning=True)
def load_community_data(dataID):
    results = socrata_client.get(dataID,
                                 order="name ASC",
                                 exclude_system_fields=True)
    data = pd.DataFrame.from_dict(results)
    return data

socrata_client = Socrata("data.calgary.ca", st.secrets["socrata_token"])

community_data = load_community_data(COMMUNITY_NAMES_ID)

st.sidebar.title("Community")
community_name = st.sidebar.selectbox('Choose community:', community_data['name'], index=276)

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

# Load DP data
with st.spinner('Loading DPs...'):
    dev_data = load_data(DEVELOPMENT_PERMIT_ID)

# Clean data for joint data frame display
dev_data = dev_data.drop(['point',
                          'proposedusecode',
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
dev_data = dev_data.astype({"longitude": np.float64, "latitude": np.float64})

# Load BP data
with st.spinner('Loading BPs...'):
    bp_data = load_data(BUILDING_PERMIT_ID)

# Clean data for joint data frame display
bp_data = bp_data.drop(['permittypemapped',
                        'permitclassgroup',
                        'permitclassmapped',
                        'workclassgroup',
                        'housingunits',
                        'communitycode',
                        'communityname',
                        'location',
                        'locationcount',
                        'locationtypes',
                        'locationaddresses',
                        'locationswkt',
                        'locationsgeojson',
                        'workclassmapped'],
                       axis=1)
bp_data = bp_data.astype({"longitude": np.float64, "latitude": np.float64})

# Load tenancy data
tc_data = load_data(TENANCY_CHANGE_ID)

# Clean data for joint data frame display
tc_data = tc_data.drop(['permittype', 'communitycode', 'communityname', 'quadrant', 'ward', 'point'],  axis=1)
tc_data = tc_data.astype({"longitude": np.float64, "latitude": np.float64})


fig = pgo.Figure()

# Plotly's version of Layer is Trace
# Zesty Colour Palette from https://venngage.com/blog/color-blind-friendly-palette/ 
fig.add_trace(pgo.Scattermapbox(
    lat=land_use_data['latitude'],
    lon=land_use_data['longitude'],
    mode='markers',
    marker=pgo.scattermapbox.Marker(
        size=13,
        color='rgb(245,121,58)',
        opacity=0.7
    ),
    text=land_use_data['permitnum'],
    meta=land_use_data['statuscurrent'],
    customdata=land_use_data['description'],
    hovertemplate = "%{text}:<br>Status: %{meta}<br><br>Description: %{customdata}",
    name='Land Use'
))

fig.add_trace(pgo.Scattermapbox(
    lat=dev_data['latitude'],
    lon=dev_data['longitude'],
    mode='markers',
    marker=pgo.scattermapbox.Marker(
        size=13,
        color='rgb(169, 90, 161)',
        opacity=0.7
    ),
    text=dev_data['permitnum'],
    meta=dev_data['statuscurrent'],
    customdata=dev_data['description'],
    hovertemplate = "%{text}:<br>Status: %{meta}<br><br>Description: %{customdata}",
    name='Development Permits'
))

fig.add_trace(pgo.Scattermapbox(
    lat=bp_data['latitude'],
    lon=bp_data['longitude'],
    mode='markers',
    marker=pgo.scattermapbox.Marker(
        size=13,
        color='rgb(133, 192, 249)',
        opacity=0.7
    ),
    text=bp_data['permitnum'],
    meta=bp_data['statuscurrent'],
    customdata=bp_data['description'],
    hovertemplate = "%{text}:<br>Status: %{meta}<br><br>Description: %{customdata}",
    name='Building Permits'
))

fig.add_trace(pgo.Scattermapbox(
    lat=tc_data['latitude'],
    lon=tc_data['longitude'],
    mode='markers',
    marker=pgo.scattermapbox.Marker(
        size=13,
        color='rgb(15, 32, 128)',
        opacity=0.7
    ),
    text=tc_data['permitnum'],
    meta=tc_data['statuscurrent'],
    customdata=tc_data['applicantname'],
    hovertemplate = "%{text}:<br>Status: %{meta}<br><br>Description: %{customdata}",
    name='Tenancy Changes'
))

fig.update_layout(
    margin_pad=0,
    height=650,
    hovermode='closest',
    clickmode='select',
    showlegend=True,
    mapbox=dict(
        accesstoken=st.secrets['mapbox']['token'],
        bearing=0,
        center=dict(
            lat=51.0425,
            lon=-114.1
        ),
        pitch=0,
        zoom=14,
        style='light'
    ),
)

st.plotly_chart(fig, use_container_width=True)

# Rename some columns for nomalization
bp_data = bp_data.rename(columns={"originaladdress": "address"})
tc_data = tc_data.rename(columns={"applicantname": "applicant", "originaladdress": "address", "proposeduse": "description"})

#all_data = pd.concat([dev_data, bp_data, tc_data, land_use_data])
all_data = pd.concat([dev_data, bp_data, tc_data])
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

# This is needed for st.write, but if we use plotly we won't.
#all_data.set_index('permitnum', inplace=True)
all_data.sort_values(by=['applieddate'], ascending=False, inplace=True)

fig = pgo.Figure(data=[pgo.Table(
    header=dict(values=list(all_data.columns),
                align='left'),
    cells=dict(values=[all_data.permitnum,all_data.address,all_data.applicant,all_data.description,all_data.applieddate,all_data.statuscurrent,all_data.permittype,all_data.estprojectcost,all_data.contractorname,all_data.issueddate],
               align='center'))
])

fig.update_layout(
    margin_pad=0,
    height=650,
    hovermode='closest',
    clickmode='select',
)

st.plotly_chart(fig, use_container_width=True)

st.sidebar.markdown("""
----

GitHub: https://github.com/chealion/streamlit-sunalta

Data Sources:

Land Use: https://data.calgary.ca/dataset/Land-Use-Redesignation-Applications/33vi-ew4s

Development: https://data.calgary.ca/dataset/Development-Permits/6933-unw5

Building Permits: https://data.calgary.ca/Business-and-Economic-Activity/Building-Permits/c2es-76ed

Tenancy Change: https://data.calgary.ca/dataset/Tenancy-Change-Applications/wrtt-2nqs
""")
