import pandas as pd
import json
import numpy as np
import plotly.graph_objs as go

pd.options.mode.chained_assignment = None

class ASV:
    def __init__(self) -> None:
        self.county_to_domain_data = pd.DataFrame()
        self.all_domain_data = pd.DataFrame()

    def plot_county(self, graph_data):

        f = open('data/geojson-counties-fips.json')
        counties = json.load(f)    
        f.close()

        # Standardize 'county_fips' to a 5-digit string format, ensuring consistency for mapping.
        # Convert 'port_tier' to string for display purposes.
        graph_data["county_fips"] = graph_data["county_fips"].astype(int).astype(str).apply(lambda x: x.zfill(5))
        graph_data["port_tier"] = graph_data["port_tier"].astype(int).astype(str)

        traces = []
        buttons = []

        # Extract unique state names, sort them, and add an "All" option for a complete view.
        states = graph_data["state_name"].unique()
        states = states.tolist()
        states = sorted(states)
        states[:0] = ["All"]

        # Prepare a visibility array for interactive state selection in the plot.
        visible = np.array(states)   
        color_scale = [[0.0, '#21d952'], 
                        [0.25, '#FFC469'], 
                        [0.8, '#FF0000'],
                        [1.0, '#7a0000']]

        # Loop through each state to create a choropleth layer and a corresponding button for interactivity
        for state in states:
        
            # Filter data for the current state. If the state is "All", use all data.
            state_wise_data = graph_data[graph_data["state_name"] == state] if state != "All" else graph_data

            # Create a choropleth map layer for the current state's data
            traces.append(go.Choroplethmapbox(
                geojson = counties,
                locations= state_wise_data["county_fips"], 
                z=state_wise_data["port_tier"],
                zmin=0,
                zmax=4,
                colorbar_title=state,
                colorscale=color_scale,
                customdata = np.stack( (state_wise_data['County'], state_wise_data['port_tier'],state_wise_data['state_name'], state_wise_data["number of ips"]), axis=-1),
                visible= True if state==states[0] else False))

            # Create an interactive button for the current state
            buttons.append(dict(label=state,
                            method="update",
                            args=[{"visible":list(visible==state)},
                                {"title":f"Attack surface Distribution for <b>{state} {'states' if state == 'All' else ''} </b>"}]))

        # Set up the interactive menu with the buttons created
        updatemenus = [{"active":0,
                    "buttons":buttons,
                    }]
        
        # Create the figure with the traces and layout settings including the interactive menus
        fig = go.Figure(data=traces,
                    layout=dict(updatemenus=updatemenus))

        # Fit the map to display all the locations properly.
        fig.update_geos(fitbounds="locations")

         # Set initial layout settings for the map, including center coordinates and zoom level.
        first_title = states[0]
        fig.update_layout(
            margin=dict(l=20, r=20, t=70, b=20),
            mapbox_style = "carto-positron",
            mapbox_zoom = 4,
            mapbox_center = {"lat": 37.0902, "lon": -95.7129},
            title=f"Attack surface Distribution for <b>{first_title} {'states' if state == 'All' else ''}</b>",title_x=0.5,)

         # Customize the hover information on the choropleth map to display state, county, and severity.
        fig.update_traces(hovertemplate="<br>".join([
            "State: %{customdata[2]}",
            "County: %{customdata[0]}",
            "Severity: %{customdata[1]}",
        ]) + "<extra></extra>")

        return fig
    
    def create_domain_dataframe(self):
        
        new_data = pd.read_csv('data/County Data to Visualize.csv')

        # Format county names (captialize first letter)
        new_data['County'] = new_data['County'].str.title()

        # Assigning columsn to dataframe (was asked to keep columns like this)
        df = pd.DataFrame(columns=['domain', 'ips', 'ip_count', 'ports', 'ports_count', 'services',
       'services_count', 'port_tier_data', 'port_tier', 'Domain Name',
       'Domain Type', 'County', 'State', 'city', 'county_fips', 'county_name',
       'state_id', 'state_name', 'number of domains','number of ips','number open ports', 'DNS MDNS','POSTGRES MSSQL MYSQL','TELNET FTP TFTP RDP SSH','NETBIOS SMB', 'Score'])
    
        df['state_id'] = new_data['State']
        df['state_name'] = new_data['state_name']
        df['port_tier'] = new_data['Score']
        df['County'] = new_data['County']
        df['State'] = new_data['state_id'] 
        df['Number of Domains'] = new_data['number of domains']
        df['Number of Ips'] = new_data['number of ips']
        df['Number of Open Ports'] = new_data['number open ports']
        df['DNS MDNS'] = new_data['DNS MDNS']
        df['POSTGRES MSSQL MYSQL'] = new_data['POSTGRES MSSQL MYSQL']
        df['TELNET FTP TFTP RDP SSH'] = new_data['TELNET FTP TFTP RDP SSH']
        df['NETBIOS SMB'] = new_data['NETBIOS SMB']
        df['Severity'] = new_data['Score']

        f = open('data/geojson-counties-fips.json')
        json_data = json.load(f)
        f.close()
        
        counties = json_data['features']
        county_info = []

        for county in counties:
            county_name = county['properties']['NAME'].lower()
            state_id = county['properties']['STATE']
            county_id = county['id']
            lsad = county['properties']['LSAD']
            county_info.append((county_name, state_id, county_id, lsad))

        for i, name in df['County'].items():
            if str(name).lower().__contains__(' city'):
                df['Domain Name'].loc[i] = 'city'
            
            for county in county_info:
                if str(name).replace(' City', '').lower() == county[0] and df['State'].loc[i] == int(county[1]) and (df['Domain Name'].loc[i] == 'city' and county[3] == 'city'):
                    df['county_fips'].loc[i] = county[2]
                elif str(name).lower() == county[0] and df['State'].loc[i] == int(county[1]) and (df['Domain Name'].loc[i] == 'city'):
                    df['county_fips'].loc[i] = county[2]
                elif str(name).lower() == county[0] and df['State'].loc[i] == int(county[1]) and (df['Domain Name'].loc[i] != 'city' and county[3] != 'city'):
                    df['county_fips'].loc[i] = county[2]


        df['county_fips'] = df['county_fips'].fillna(0)

        # Create a mask for rows where 'County' contains "'S"
        mask = df['County'].str.contains("'S")

        # Use str.replace with regex to efficiently modify the string
        # This regex looks for the pattern "'S" and replaces it with "'s"
        df.loc[mask, 'County'] = df.loc[mask, 'County'].str.replace(
            r"('S)", 
            lambda x: x.group(0).lower(), 
            regex=True
        )

        self.all_domain_data = df.fillna('Null')
        return self.all_domain_data
    

obj = ASV()
obj.create_domain_dataframe()