"""
Testing out dash-bootstrap-components for layout and design.
"""
# -*- coding: utf-8 -*-

"""
Trying scattermapbox as subplots for multiple, facetted maps.

"""
import pathlib
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import plotly.express as px
import os
import pandas as pd
import dash_bootstrap_components as dbc
import warnings
import numpy as np

from controls import discrete_colorscale

# Ignore warnings from numpy about comparisons
warnings.simplefilter(action='ignore', category=FutureWarning)

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

# Get relative data folder
PATH = pathlib.Path(__file__).parent

DATA_PATH = PATH.joinpath('data').resolve()

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

server = app.server

# Load mapbox token
mapboxAccessToken = str(os.environ['MAPBOX_ACCESS_TOKEN'])

# # Mapbox token  NOTE: see also using the config var
# in heroku (
# # https://devcenter.heroku.com/articles/config-vars)
# mapboxAccessToken = str(os.environ['MAPBOX_ACCESS_TOKEN'])
# # may need to be "MAPBOX_TOKEN" (i.e., without the "ACCESS")
# if not mapboxAccessToken:
# mbt = open(PATH(".mapbox_token"), 'r')
# mapboxAccessToken = mbt.read().replace('"', '')
# mbt.close()

# Load datasets: Converted in external script from goeJSON to csv with x,y columns
df = pd.read_csv(DATA_PATH.joinpath(
    'az_nm_2000_2020_noGrassMask_points_cat_precip_cats.csv'), index_col='year')

# Colorscale for anomalies
bvals = [-30, -15, -5, 5, 15, 30]
colors = ['rgb(244, 165, 130)', 'rgb(253, 219, 199)',
          'rgb(247, 247, 247)', 'rgb(209, 229, 240)',
          'rgb(146, 197, 222)']

dcolorsc = discrete_colorscale(bvals, colors)

bvals = np.array(bvals)
tickvals = [np.mean(bvals[k:k+2]) for k in range(len(bvals)-1)] #position with respect to bvals where ticktext is displayed
ticktext = [f'<{bvals[1]}'] + [f'{bvals[k]}-{bvals[k+1]}' for k in range(1, len(bvals)-2)]+[f'>{bvals[-2]}']

# Colorscale for precip ratio groups as continuous data
bvals_precip = [0.36, 0.8, 1.2, 2.97]
colors_precip = ['rgb(146, 197, 222)',
                'rgb(247, 247, 247)',
                'rgb(244, 165, 130)']

dcolorsc_precip = discrete_colorscale(bvals_precip, colors_precip)

bvals_precip = np.array(bvals_precip)
tickvals_precip = [np.mean(bvals_precip[k:k+2]) for k in range(len(bvals_precip)-1)]
#position with respect to bvals_precip where ticktext_precip is displayed
ticktext_precip = [f'<{bvals_precip[1]}'] + [f'{bvals_precip[k]}-' \
                                             f'{bvals_precip[k+1]}' for
                                             k in
                                    range(1, len(bvals_precip)-2)]+[f'>'
                                                                    f'{bvals_precip[-2]}']

infoModal = html.H1(
    [
        dbc.Button("Learn More", id="open-info"),
        dbc.Modal(
            [
                dbc.ModalHeader("Project Description"),
                dbc.ModalBody("To include descriptions of dataset, and app "
                              "functionality."),
                dbc.ModalFooter(
                    dbc.Button(
                        "Close", id="close-info", className="ml-auto"
                    )
                ),
            ],
            id="info-modal-centered",
            centered=True,
        ),
    ]
)

app.layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H1('ANPP - NDVI Anomalies', style={'testAlign':'center'}),
                        # html.P('Interactive mapping of GrassCast ANPP and '
                        #        'MODIS NDVI anomalies', style={'testAlign':'center'}),
                    ],
                    md=11,
                ),
                dbc.Col(
                    [
                        infoModal,
                    ],

                )
            ],
            justify='end'
        ),

        dbc.Row(
            [
            dbc.Col(
                [
                dbc.Form(
                    [
                    dbc.Label('Filter by Year'),
                    dcc.Slider(
                        id='year-slider',
                        min=2000,
                        max=2020,
                        step=None,
                        marks={i: '{}'.format(str(i)) for i in range(2000,
                                                                     2021,
                                                                     1)},
                        value=2000,
                        tooltip={'always_visible': False, 'placement':
                            'bottomLeft'},
                        updatemode='drag'
                        ),
                    ],
                    ),
                ],
                md=10,
                ),
            ],
            justify='center',
        ),

        dbc.Row(
            [
                dbc.Col(
                    dcc.Graph(
                        id='map-graph',
                        config={'scrollZoom': True}
                    ),
                    md=12),
            ],
            # autosize=True,
        ),
        dbc.Row(
            [
                dbc.Col(
                    dcc.Graph(
                        id='distribution-plots'
                    ),
                    md=12),
            ],
            # autosize=True,
        ),
    ],
    fluid=True,
)

# More info button modal
@app.callback(
    Output("info-modal-centered", "is_open"),
    [Input("open-info", "n_clicks"), Input("close-info", "n_clicks")],
    [State("info-modal-centered", "is_open")],
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open

# Distribution plots
@app.callback(
    Output('distribution-plots', 'figure'),
    # [Input('anom-class-dropdown', 'value'),
     [Input('year-slider', 'value')]
)
def dist_plots(year):
    dist_data = df.loc[year, ['spring_delta_anpp', 'summer_delta_anpp',
                           'spring_delta_ndvi', 'summer_delta_ndvi',
                           'pr_cat']]

    fig = px.histogram(dist_data, x=['spring_delta_anpp',
                                     'summer_delta_anpp',
                                     'spring_delta_ndvi',
                                     'summer_delta_ndvi'],
                       color='pr_cat',
                       marginal='box',
                       facet_col='variable',
                       barmode='overlay')
    return fig

# Map graph
# TODO: see https://community.plotly.com/t/preserving-ui-state-like-zoom-in-dcc-graph-with-uirevision/15793
#   about preventing auto resetting map with input (e.g., slider) change.
@app.callback(
    Output('map-graph', 'figure'),
    # [Input('anom-class-dropdown', 'value'),
     [Input('year-slider', 'value')]
)
def map_selection(year):
    map_data = df.loc[year]
    lat = map_data['lat']
    lon = map_data['lon']

    fig = make_subplots(
            rows=2, cols=2,
            shared_xaxes='all', # shared_yaxes=True,
            subplot_titles=('GrassCast ANPP Spring (April-May)',
                            'GrassCast ANPP Summer (August-September)',
                            'MODIS NDVI Spring (April-May)',
                            'MODIS NDVI Summer (August-September)'),
            # column_titles=('Spring', 'Summer'),
            horizontal_spacing=0.05,
            vertical_spacing=0.05,
            specs=[[{'type': 'mapbox'}, {'type': 'mapbox'}],
                    [{'type': 'mapbox'}, {'type': 'mapbox'}]]
        )

    # Spring anpp
    fig.add_trace(go.Scattermapbox(
            lat = lat,
            lon = lon,
            text = list(map_data['gridID']),
            customdata = map_data['spring_delta_anpp'],

            # lat=list(map_data[['gridID', 'spr_anpp_delta', 'lat', 'lon']]['lat']),
            # lon=list(map_data[['gridID', 'spr_anpp_delta', 'lat', 'lon']]['lon']),
            # text=list(
            #     map_data[['gridID', 'spr_anpp_delta', 'lat', 'lon']]['gridID']),
            # customdata=list(map_data[['gridID', 'spr_anpp_delta',
            #                           'lat', 'lon']]['spr_anpp_delta']),
            # subplot = 'mapbox',
            # hover_data = ['gridID', 'year', 'spr_anpp_delta'],
            hovertemplate =
                "Point ID: <b>%{text}</b><br><br>" +
                "Anomaly: <b>%{customdata}</b><br>" +
                    "<extra></extra>",
            mode = 'markers',
            marker = dict(
                size = 7,
                opacity = 0.9,
                showscale=True,
                color = map_data['spr_delta_anpp_nm'],
                coloraxis = 'coloraxis',
                # colorscale = 'RdBu',
                cmid=0,
                cmin = -30,
                cmax = 30
            ),), 1, 1)

    # Summer anpp
    fig.add_trace(go.Scattermapbox(
            lat = lat,
            lon = lon,
            text = list(map_data['gridID']),
            customdata = map_data['summer_delta_anpp'],
            # subplot='mapbox',
            # hover_data = ['gridID', 'year', 'sum_anpp_delta'],
            hovertemplate =
                "Point ID: <b>%{text}</b><br><br>" +
                "Anomaly: <b>%{customdata}</b><br>" +
                    "<extra></extra>",
            mode = 'markers',
            marker = dict(
                size = 7,
                opacity = 0.9,
                showscale=True,
                color = map_data['summ_delta_anpp_nm'],
                coloraxis='coloraxis',
                # colorscale = 'RdBu',
                cmid=0,
                cmin = -30,
                cmax = 30
            ),), 1, 2)

    # SPring ndvi
    fig.add_trace(go.Scattermapbox(
            lat = lat,
            lon = lon,
            text = map_data['gridID'],
            customdata = map_data['spring_delta_ndvi'],
            # subplot='mapbox',
            hovertemplate =
                "Point ID: <b>%{text}</b><br><br>" +
                "Anomaly: <b>%{customdata}</b><br>" +
                    "<extra></extra>",
            mode = 'markers',
            marker = dict(
                size = 7,
                opacity = 0.9,
                showscale=True,
                    color = map_data['spr_delta_ndvi_nm'],
                    coloraxis = 'coloraxis',
                    # colorscale = 'RdBu',
                    cmid=0,
                    cmin = -30,
                    cmax = 30
            ),), 2, 1)

    # Summer ndvi
    fig.add_trace(go.Scattermapbox(
            lat = lat,
            lon = lon,
            text = map_data['gridID'],
            customdata = map_data['summer_delta_ndvi'],
            # subplot='mapbox',
            hovertemplate =
                "Point ID: <b>%{text}</b><br><br>" +
                "Anomaly: <b>%{customdata}</b><br>" +
                    "<extra></extra>",
            mode = 'markers',
            marker = dict(
                size = 7,
                opacity = 0.9,
                showscale=True,
                color = map_data['summ_delta_ndvi_nm'],
                coloraxis = 'coloraxis',
                # colorscale = 'RdBu',
                cmid=0,
                cmin = -30,
                cmax = 30
            ),), 2, 2)

    fig.update_layout(
        autosize=True,
        height=900,
        coloraxis= dict(
            colorscale = dcolorsc),
        showlegend=False,
        hovermode="closest",
        uirevision='never',
        # config=dict(modBarButtonsToAdd = ['scrollZoom'])
        )

    fig.update_mapboxes(
        accesstoken=mapboxAccessToken,
        style="light",
        center=dict(
            lon=-109.0064119,  # manually copied from the csv lon
            lat=  34.50971515  # manually copied from the csv lat
        ),
        # pitch=30,
        zoom=5)
    # configmodBarButtonsToAdd = ['scrollZoom'])
    return fig
    # return gen_map(dff)


if __name__ == '__main__':
    app.run_server(debug=False)