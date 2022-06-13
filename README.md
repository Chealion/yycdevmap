# Community Development Map

Live Version: https://share.streamlit.io/chealion/streamlit-sunalta/main/poc.py

## But... why?

The City of Calgary runs a [development map](https://developmentmap.calgary.ca) but there was a use case I had that the map does not consider. Namely, if I'm checking the map - what's actually new in my community? The development map is awesome for a lot of information, but isn't for a check in or to correlate with other more minor items (building permits, tenancy changes).

Additionally my community is part of the [Centre City Enterprise and Main Streets Exemption Areas](https://www.calgary.ca/business-economy/pda/pd/mybusiness/centre-city-enterprise-area.html) which means a number of activities that would normally trigger a full permit process to notify us of a change do not get distributed to the community association. This solves our problem for finding out what's happening without the burden of the full development permit process.

Hopefully this helps others with the same issue - a lens on what is new, and less on all the information for historical purposes. This is a somewhat limited proof of concept but feel free to use or rewrite as you like!

## Data Sources

Data Sources:

Land Use: https://data.calgary.ca/dataset/Land-Use-Redesignation-Applications/33vi-ew4s

Development: https://data.calgary.ca/dataset/Development-Permits/6933-unw5

Building Permits: https://data.calgary.ca/Business-and-Economic-Activity/Building-Permits/c2es-76ed

Tenancy Change: https://data.calgary.ca/dataset/Tenancy-Change-Applications/wrtt-2nqs

## Development

### Install Requirements

    pip3 install -r requirements.txt

#### macOS Notes

You'll want to install proj and gdal via Homebrew first

### Run directly

    streamlit run ./poc.py
