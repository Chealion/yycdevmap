import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk

from sodapy import Socrata

# Socrata Info
# Socrata Dataset IDs
COMMUNITY_NAMES_ID = 'jd78-wxjp'
LAND_USE_ID = '33vi-ew4s'
DEVELOPMENT_PERMIT_ID = '6933-unw5'
BUILDING_PERMIT_ID = 'c2es-76ed'
TENANCY_CHANGE_ID = 'wrtt-2nqs'

# Eventual variables
COMMUNITY_NAME = 'SUNALTA'
DATE = '2020-12-31T00:00:00'

# Set view
st.set_page_config(page_title="Sunalta Development Map", layout="wide")


# st.cache - will cache the output of the function
@st.cache(suppress_st_warning=True)
def load_data(dataID):
    # st.write("Cache miss: Loading data from data.calgary.ca")
    results = socrata_client.get(dataID,
                                 limit=100,
                                 communityname=COMMUNITY_NAME,
                                 where="applieddate > '" + DATE + "'",
                                 order="applieddate DESC",
                                 exclude_system_fields=True)
    data = pd.DataFrame.from_dict(results)
    return data


socrata_client = Socrata("data.calgary.ca", st.secrets["socrata_token"])

# Load DP data
dev_data = load_data(DEVELOPMENT_PERMIT_ID)

# Clean data
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
bp_data = load_data(BUILDING_PERMIT_ID)

# Clean data
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

# Clean data
tc_data = tc_data.drop(['permittype', 'communitycode', 'communityname', 'quadrant', 'ward', 'point'],  axis=1)
tc_data = tc_data.astype({"longitude": np.float64, "latitude": np.float64})

st.title("Sunalta Map")
st.write("""Orange = Development Permits  
Purple = Building Permits  
Blue = Business Tenancy Changes""")

st.pydeck_chart(pdk.Deck(
    map_style='mapbox://styles/mapbox/light-v9',
    tooltip=True,
    initial_view_state=pdk.ViewState(
         latitude=51.0415,
         longitude=-114.1,
         zoom=14,
         pitch=0,
     ),
    layers=[
        pdk.Layer(
            'ScatterplotLayer',
            data=dev_data[['latitude','longitude']],
            auto_highlight=True,
            pickable=True,
            get_position=["longitude", "latitude"],
            get_radius=15,
            radius_scale=1,
            get_fill_color=[245, 121, 58, 255],
        ),
        pdk.Layer(
            'ScatterplotLayer',
            data=bp_data[['latitude','longitude']],
            auto_highlight=True,
            pickable=True,
            get_position=["longitude", "latitude"],
            get_radius=15,
            radius_scale=1,
            get_fill_color=[169, 90, 161, 255]
        ),
        pdk.Layer(
            'ScatterplotLayer',
            data=tc_data[['latitude','longitude']],
            auto_highlight=True,
            pickable=True,
            get_position=["longitude", "latitude"],
            get_radius=15,
            radius_scale=1,
            get_fill_color=[133, 192, 249, 255],
        )
    ],
))

# Rename some columns for nomalization
bp_data = bp_data.rename(columns={"originaladdress": "address"})
tc_data = tc_data.rename(columns={"applicantname": "applicant", "originaladdress": "address", "proposeduse": "description"})

all_data = pd.concat([dev_data, bp_data, tc_data])
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
all_data.set_index('permitnum', inplace=True)
all_data.sort_values(by=['applieddate'], ascending=False, inplace=True)

st.table(all_data)

st.markdown("""
----

GitHub: https://github.com/chealion/streamlit-sunalta

Data Sources:

Land Use: https://data.calgary.ca/dataset/Land-Use-Redesignation-Applications/33vi-ew4s

Development: https://data.calgary.ca/dataset/Development-Permits/6933-unw5
	
Building Permits: https://data.calgary.ca/Business-and-Economic-Activity/Building-Permits/c2es-76ed

Tenancy Change: https://data.calgary.ca/dataset/Tenancy-Change-Applications/wrtt-2nqs

""")