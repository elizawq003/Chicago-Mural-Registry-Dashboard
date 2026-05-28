# Import packages
from dash import Dash, html, dash_table, dcc, callback, Output, Input
import pandas as pd
import plotly.express as px
from wordcloud import WordCloud, STOPWORDS
import io, base64, random
import plotly.graph_objects as go
import re
from collections import Counter
import math


# Incorporate data
# Chicago Mural Registry
df = pd.read_csv('https://data.cityofchicago.org/resource/we8h-apcf.csv')

# debugging for interactive map hover function: find murals with invaid/bad latitude or longitude
bad_lat = df[(df['latitude'] < -90) | (df['latitude'] > 90)]
bad_lon = df[(df['longitude'] < -180) | (df['longitude'] > 180)]
"""
print("Rows with invalid latitude:")
print(bad_lat[['artwork_title', 'latitude', 'longitude']])
print()
print("Rows with invalid longitude:")
print(bad_lon[['artwork_title', 'latitude', 'longitude']])
"""


# Initialize the app - incorporate css
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css',
                       'https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap']
app = Dash(external_stylesheets=external_stylesheets, suppress_callback_exceptions=True)

#columns to be displayed in table: artwork_title, artist_credit, year_installed, zip)
df_table = df[['artwork_title', 'artist_credit', 'year_installed', 'zip']]

# Summary statistics for the header cards
total_murals   = len(df)
unique_artists = df['artist_credit'].nunique()
unique_zips    = df['zip'].nunique()

#helper function to build 3 blue circles for the summary statistics under the title
def stat_circle(value, label, ring_color):
    return html.Div(
        className='stat-circle',
        style={'borderColor': ring_color,
               'width': '105px', 'height': '105px', 'borderWidth': '5px',
               'padding': '6px', 'boxSizing': 'border-box', 'overflow': 'hidden'},
        children=[
            html.Div(label, className='stat-label',
                     style={'fontSize': '10px', 'marginBottom': '2px',
                            'textAlign': 'center', 'lineHeight': '1.1',
                            'whiteSpace': 'normal'}),
            html.Div(f'{value:,}', className='stat-number',
                     style={'color': ring_color, 'fontSize': '18px',
                            'lineHeight': '1.1'}),
        ]
    )

#if the mural is missing latitude or longtitude, do not show it on the interactive map
# Data for the map - drop rows missing coordinates
# refer to :https://plotly.com/python/tile-scatter-maps/
df_map = df.dropna(subset=['latitude', 'longitude'])

#update df_map to only keep murals with valid latitude and longitude
df_map = df_map[
    (df_map['latitude'].between(-90, 90)) &
    (df_map['longitude'].between(-180, 180))
]

#hover on each mural will show its title, artist, and year installed
fig = px.scatter_map(
    df_map,
    lat = 'latitude',
    lon = 'longitude',
    hover_name = 'artwork_title',
    hover_data = ['artist_credit','year_installed'],
    color_discrete_sequence = ['#3182bd'],   # all markers blue
    zoom = 10,
    height = 700
)

#manually draw the base map layer
# trim margins
fig.update_layout(
    map_style='open-street-map',
    map_center={'lat': 41.88, 'lon': -87.63},
    map_zoom=10,
    margin=dict(l=0, r=0, t=10, b=0),
    hoverlabel=dict(
        bgcolor='#08519c',
        font=dict(color='white'),
        bordercolor='#08519c'
    )
    
    ) 

# only keep murals with valid meida and year_installed 
df_media = df.dropna(subset=['media','year_installed']).copy()

# did not generate enough data
"""
# find the top 10 most popular media type
#keep only the top 10 media type to make drawing figure easier
top_media = df_media['media'].value_counts().head(10).index.tolist()
print("Top 10 media types:")
print(df_media['media'].value_counts().head(10))


# only keep murals fall into the 10 types
df_media = df_media[df_media['media'].isin(top_media)]
"""
# keep all entries but group similar media types into broader categories
def categorize_media(m):
    m = str(m).lower().strip()
    if 'spray' in m:
        return 'Spray Paint'
    if 'mosaic' in m or 'tile' in m:
        return 'Mosaic/Tile'
    if 'mixed' in m:
        return 'Mixed Media'
    if 'paint' in m or 'brush' in m:
        return 'Paint'
    return 'Other'

df_media['media'] = df_media['media'].apply(categorize_media)
"""
print("\nMedia categories after grouping:")
print(df_media['media'].value_counts())
"""


# all categories in the data
media_type = sorted(df_media['media'].unique().tolist())

# count how many murals exist each year for each media type
media_counts = (df_media.groupby(['year_installed', 'media']).size().reset_index(name='count'))


# debugging: Fill in missing year/media combos with 0 so the animation is smooth
years = sorted(df_media['year_installed'].unique())
all_combos = pd.MultiIndex.from_product(
    [years, media_type], names=['year_installed', 'media']
)
media_counts = (media_counts.set_index(['year_installed', 'media'])
                            .reindex(all_combos, fill_value=0)
                            .reset_index()
                            .sort_values('year_installed'))

# visual effect:map each media category to a different shade of blue (light -> dark)
blue_shades = {
    'Mixed Media': '#c6dbef',
    'Mosaic/Tile': '#9ecae1',
    'Other':       '#6baed6',
    'Paint':       '#3182bd',
    'Spray Paint': '#08519c',
}


fig_media = px.bar(
    media_counts,
    x='media',
    y='count',
    color='media',
    color_discrete_map=blue_shades,
    animation_frame='year_installed',
    range_y=[0, media_counts['count'].max() * 1.1],
    title='Popularity of Mural Media Types Over Time',
    labels={'media': 'Media Type',
            'count': 'Number of Murals',
            'year_installed': 'Year'},
    height=500
)

fig_media.update_layout(xaxis_tickangle=-45, 
                        showlegend=False,
                        margin=dict(l=40, r=20, t=60, b=80),
                        bargap=0.35)

# total murals installed per year, for the animated line chart
year_counts = (df.dropna(subset=['year_installed'])
                 .groupby('year_installed').size()
                 .reset_index(name='count')
                 .sort_values('year_installed'))
yc_years = year_counts['year_installed'].tolist()
yc_vals  = year_counts['count'].tolist()

# each frame adds one more year -> the line "draws" itself
line_frames = [
    go.Frame(name=str(yc_years[k-1]),
             data=[go.Scatter(x=yc_years[:k], y=yc_vals[:k],
                              mode='lines+markers',
                              line=dict(color='#3182bd', width=3),
                              marker=dict(color='#08519c', size=7))])
    for k in range(1, len(yc_years) + 1)
]
fig_line = go.Figure(
    data=[go.Scatter(x=[yc_years[0]], y=[yc_vals[0]],
                     mode='lines+markers',
                     line=dict(color='#3182bd', width=3),
                     marker=dict(color='#08519c', size=7))],
    frames=line_frames
)
fig_line.update_layout(
    title='Number of Murals Installed per Year',
    xaxis=dict(title='Year', range=[min(yc_years), max(yc_years)]),
    yaxis=dict(title='Number of Murals', range=[0, max(yc_vals) * 1.1]),
    height=500, margin=dict(l=50, r=20, t=60, b=90),
    updatemenus=[dict(
        type='buttons', showactive=False, direction='left',
        x=0.0, y=-0.18, xanchor='left', yanchor='top',
        buttons=[
            dict(label='▶ ', method='animate',
                 args=[None, {'frame': {'duration': 400, 'redraw': True},
                              'transition': {'duration': 300},
                              'fromcurrent': True}]),
            dict(label='⏸ ', method='animate',
                 args=[[None], {'frame': {'duration': 0, 'redraw': False},
                                'mode': 'immediate',
                                'transition': {'duration': 0}}])
        ]
    )]
)

# build an interactive word cloud FIGURE (each word hoverable) from titles + descriptions
def _intersections(c0, c1, r):
    # centers of a circle (radius r) tangent to both c0 and c1
    x0, y0, ra = c0
    x1, y1, rb = c1
    R0, R1 = ra + r, rb + r
    dx, dy = x1 - x0, y1 - y0
    d = math.hypot(dx, dy)
    if d == 0 or d > R0 + R1 or d < abs(R0 - R1):
        return []
    a = (R0*R0 - R1*R1 + d*d) / (2*d)
    h2 = R0*R0 - a*a
    if h2 < 0:
        return []
    h = math.sqrt(h2)
    xm, ym = x0 + a*dx/d, y0 + a*dy/d
    ox, oy = -dy/d * h, dx/d * h
    return [(xm + ox, ym + oy), (xm - ox, ym - oy)]

def _overlaps(x, y, r, placed, eps=1e-3):
    return any(math.hypot(x - px, y - py) < r + pr - eps for px, py, pr in placed)

def pack_circles(radii):
    # greedy front-packing: each new bubble sits tangent to two existing ones,
    # as close to the center as possible (gives the clustered look)
    placed = []
    for i, r in enumerate(radii):
        if i == 0:
            placed.append((0.0, 0.0, r)); continue
        if i == 1:
            placed.append((placed[0][2] + r, 0.0, r)); continue
        best = None
        for a in range(len(placed)):
            for b in range(a + 1, len(placed)):
                for x, y in _intersections(placed[a], placed[b], r):
                    if not _overlaps(x, y, r, placed):
                        d2 = x*x + y*y
                        if best is None or d2 < best[0]:
                            best = (d2, x, y)
        if best is None:                       # fallback: spiral outward
            ang, rad = 0.0, r
            while _overlaps(rad*math.cos(ang), rad*math.sin(ang), r, placed):
                ang += 0.5; rad += r*0.08
            best = (0, rad*math.cos(ang), rad*math.sin(ang))
        placed.append((best[1], best[2], r))
    return placed

# --- interactive bubble word cloud -----------------------------------------
def build_wordcloud_fig(n_words=40, seed=8):
    text_cols = ['artwork_title', 'description_of_artwork']
    text = ' '.join(df[text_cols].fillna('').astype(str).values.ravel()).lower()

    stop = set(STOPWORDS)
    stop.update(['mural', 'murals', 'chicago', 'artist', 'artists', 'created',
                 'project', 'street', 'nan', 'public', 'art', 'foundation',
                 'new', 'work', 'works', 'one', 'will', 'wall', 'image', 'painted'])

    tokens = [t for t in re.findall(r"[a-z']+", text) if t not in stop and len(t) > 2]
    top = Counter(tokens).most_common(n_words)
    words  = [w for w, c in top]
    counts = [c for w, c in top]

    hi, lo = max(counts), min(counts)
    def norm(c):
        return 0.0 if hi == lo else (c - lo) / (hi - lo)

    radii  = [1.0 + 3.4 * math.sqrt(norm(c)) for c in counts]   # area ~ frequency

    # text color strategy — UNCHANGED (darker blue = more frequent)
    blues = ['#9ecae1', '#6baed6', '#3182bd', '#08519c']
    def color_for(c):
        return blues[-1] if hi == lo else blues[int(norm(c) * (len(blues) - 1))]
    colors = [color_for(c) for c in counts]

    # pack with a small gap added to each radius so drawn bubbles never touch
    gap = 0.18
    placed = pack_circles([r + gap for r in radii])
    cx = [p[0] for p in placed]
    cy = [p[1] for p in placed]

    minx = min(x - r for (x, _, _), r in zip(placed, radii))
    maxx = max(x + r for (x, _, _), r in zip(placed, radii))
    miny = min(y - r for (_, y, _), r in zip(placed, radii))
    maxy = max(y + r for (_, y, _), r in zip(placed, radii))
    pad = 0.8
    y0, y1 = miny - pad, maxy + pad

    PLOT_H = 460
    px_per_unit = (PLOT_H - 20) / (y1 - y0)

    # font sized to FIT inside each bubble (width- and height-limited)
    def fit_font(r, word, freq_size):
        diam_px = 2 * r * px_per_unit
        by_width  = 1.4 * diam_px / max(1, len(word))   # word must fit across
        by_height = 0.8 * diam_px                        # and within the height
        return max(6, min(freq_size, by_width, by_height))
    freq_sizes = [11 + norm(c) * 20 for c in counts]
    sizes = [fit_font(r, w, fs) for r, w, fs in zip(radii, words, freq_sizes)]

    # exact, non-overlapping bubbles as data-coordinate circle shapes
    shapes = [dict(type='circle', xref='x', yref='y',
                   x0=x - r, y0=y - r, x1=x + r, y1=y + r,
                   fillcolor='rgba(49,130,189,0.12)',
                   line=dict(color=col, width=2))
              for x, y, r, col in zip(cx, cy, radii, colors)]

    hit_px = [max(12, 2 * r * px_per_unit) for r in radii]      # hover hit-area

    # scattered START positions for the fly-in
    rng = random.Random(seed)
    spanx = (maxx - minx) or 1
    spany = (maxy - miny) or 1
    sx = [rng.uniform(minx - 0.6 * spanx, maxx + 0.6 * spanx) for _ in words]
    sy = [rng.uniform(miny - 0.6 * spany, maxy + 0.6 * spany) for _ in words]

    fig_wc = go.Figure(
        data=[go.Scatter(
            x=sx, y=sy, mode='markers+text',
            text=words,
            textfont=dict(size=sizes, color=colors, family='Poppins, sans-serif'),
            marker=dict(size=hit_px, sizemode='diameter', opacity=0),   # invisible
            hovertext=[f'{w}: {c}' for w, c in top],
            hoverinfo='text')],
        frames=[go.Frame(name='settle', data=[go.Scatter(x=cx, y=cy)])]
    )
    fig_wc.update_layout(
        shapes=shapes,
        xaxis=dict(visible=False, range=[minx - pad, maxx + pad]),
        yaxis=dict(visible=False, range=[y0, y1], scaleanchor='x', scaleratio=1),
        plot_bgcolor='white', paper_bgcolor='white',
        margin=dict(l=10, r=10, t=10, b=10),
        height=PLOT_H,
        hoverlabel=dict(bgcolor='#08519c', font=dict(color='white'),
                        bordercolor='#08519c')
    )
    return fig_wc

wordcloud_fig = build_wordcloud_fig()

# App layout
# use flexbox to fix layout
# App layout — top row: stats+table | map ;  bottom row: word cloud | bar chart
app.layout = html.Div(
    style={'padding': '20px',
           'backgroundImage': 'url("/assets/bg3.jpg")',
           'backgroundSize': 'cover',
           'backgroundPosition': 'center',
           'backgroundRepeat': 'no-repeat',
           'backgroundAttachment': 'fixed',
           'minHeight': '100vh'},
    children=[
        # for word cloud
        dcc.Interval(id='wc-anim-trigger', interval=350, n_intervals=0, max_intervals=1),
        html.Div(id='wc-anim-dummy', style={'display': 'none'}),
        # title
        html.Div(
            style={'display': 'flex', 'flexDirection': 'row',
                   'alignItems': 'center', 'justifyContent': 'center','gap': '20px'},
                   children=[
                        html.Img(src='/assets/flag.png',
                                 style={'height': '50px'}),
                        html.Div('Chicago Mural Registry',
                                 style={'color': '#003366', 'fontSize': 30,
                                        'fontFamily': 'Monoton, cursive'}),
                        
                        html.Img(src='/assets/flag.png',style={'height': '50px'}),           
                   ]
                 ),
        #intro
        html.Div('Chicago is home to a growing and important collection of outdoor murals. '
                 'Explore the collection and learn how to register your outdoor mural.',
                 style={'textAlign': 'center', 'color': 'black',
                        'fontSize': 15, 'marginBottom': '20px','color':'#003366','fontFamily': 'Monoton, cursive'}),
       
        html.Div(
            style={'display': 'flex', 'flexDirection': 'row',
                   'gap': '20px', 'alignItems': 'flex-start', 'marginBottom': '20px'},
            children=[

                # LEFT: 3 circles (horizontal) on top, search + table below
                html.Div(
                    style={'flex': '1 1 0', 'minWidth': '0',
                           'display': 'flex', 'flexDirection': 'column', 'gap': '15px','minHeight': '700px'},
                    children=[
                        # 3 small circles, horizontal
                        html.Div(
                            className='stat-row',
                            style={'gap': '15px', 'flexWrap': 'nowrap'},
                            children=[
                                stat_circle(total_murals,   'Total Murals',   '#08519c'),
                                stat_circle(unique_artists, 'Unique Artists', '#3182bd'),
                                stat_circle(unique_zips,    'Zip Codes',      '#6baed6'),
                            ]
                        ),
                        # search + sort + message + table
                        html.Div(children=[
                            html.Div(
                                style={'display': 'flex', 'gap': '8px', 'marginBottom': '10px'},
                                children=[
                                    dcc.Input(
                                        id='mural-search',
                                        type='text',
                                        placeholder='Search by title or artist...',
                                        debounce=True,
                                        style={'flex': '1 1 0', 'padding': '8px', 'fontSize': '14px'}
                                    ),
                                ]
                            ),
                            dcc.RadioItems(options=['Latest', 'Oldest'],
                                           value='Latest',
                                           inline=True,
                                           id='sort-year-radio-buttons',
                                           style={'marginBottom': '10px'},labelStyle={'color': 'white','fontFamily':'Poppins, sans-serif'}),
                            html.Div(id='search-message', style={'marginBottom': '10px'}),
                            dash_table.DataTable(
                                data=df_table.to_dict('records'),
                                page_size=11,
                                style_table={'overflowX': 'auto'},
                                style_cell={'textAlign': 'left', 'padding': '6px',
                                            'fontSize': '13px', 'whiteSpace': 'normal',
                                            'height': 'auto'},
                                style_header={'fontWeight': 'bold'},
                                css = [
                                    {'selector': '.previous-next-container button',
                                     'rule': 'color: white !important;'},
                                     {'selector': '.previous-next-container .page-number',
                                       'rule': 'color: white !important;'},
                                    {'selector': '.previous-next-container .page-number input',
                                     'rule': 'color: white !important;'},
                                ],
                                id='mural-table')
                        ])
                    ]
                ),

                # RIGHT: map
                html.Div(
                    style={'flex': '1.4 1 0', 'minWidth': '0'},
                    children=[
                        dcc.Graph(figure=fig, id='mural-map',
                                  style={'width': '100%'},
                                  config={'responsive': True})
                    ]
                )
            ]
        ),

        html.Div(
            style={'display': 'flex', 'flexDirection': 'row', 'gap': '20px'},
            children=[
                # word cloud — left half
                html.Div(style={'flex': '1 1 0', 'minWidth': '0'},
                    children=[
                        html.Div('Mural Themes',
                                 style={'textAlign': 'center', 'fontWeight': '600',
                                        'marginBottom': '8px','color': '#003366','fontFamily': 'Poppins, sans-serif'}),
                        dcc.Graph(figure=wordcloud_fig,id='wordcloud',
                                 style={'width': '100%','height': '460px'},config={'responsive': True, 'displayModeBar': False})
                    ]),
                # bar chart — right half
                # update with switchable line chart (animated)
                html.Div(style={'flex': '1 1 0', 'minWidth': '0'},
                               
                    children=[
                        # switch arrow
                        html.Div(style={'display': 'flex', 'justifyContent': 'flex-end','marginBottom': '4px'},
                                 children=[
                                     html.Button('⇄ Switch chart', id='chart-switch', n_clicks=0,
                                                 style={'padding': '6px 14px', 'fontSize': '13px',
                                                        'backgroundColor': '#3182bd', 'color': 'white',
                                                        'border': 'none', 'borderRadius': '4px',
                                                        'cursor': 'pointer',
                                                          'fontFamily': 'Poppins, sans-serif'})
                                                        
                                 ]),

                        dcc.Graph(figure=fig_media, id='trend-chart',
                                  style={'width': '100%','height': '500px'},
                                  config={'responsive': True})
                    ])
            ]
        )
    ]
)

# Add controls to build the interaction
@callback(
    Output(component_id='mural-table', component_property='data'),
    Output(component_id='search-message', component_property='children'),
    Input(component_id='sort-year-radio-buttons', component_property='value'),
    Input(component_id='mural-search', component_property='value')
)
def update_table(sort_option, search_term):
    filtered = df_table

    # filter by keyword across title and artist (case-insensitive)
    if search_term:
        term = search_term.lower()
        mask = (
            filtered['artwork_title'].astype(str).str.lower().str.contains(term, na=False) |
            filtered['artist_credit'].astype(str).str.lower().str.contains(term, na=False)
        )
        filtered = filtered[mask]

    # then sort by year
    ascending = (sort_option == 'Oldest')
    filtered = filtered.sort_values(by='year_installed', ascending=ascending)

    # if there is no matche
    # show empty table and  message with a Go back button
    if search_term and filtered.empty:
        message = html.Div(
            style={'padding': '12px',
                   'borderRadius': '4px'},
            children=[
                html.Span(f'No murals found for "{search_term}". ',
                           style={'fontWeight': '600', 'color':'white'}),
                html.Button('Go back', id='go-back-button', n_clicks=0,
                            style={'marginLeft': '10px', 'padding': '6px 16px',
                                   'fontSize': '13px',
                                   'color': 'white', 'border': 'none',
                                    'borderRadius': '4px', 'cursor': 'pointer'})
            ]
        )
        return [], message

    return filtered.to_dict('records'), ''

@callback(
    Output(component_id='mural-search', component_property='value'),
    Input(component_id='go-back-button', component_property='n_clicks'),
    prevent_initial_call=True
)
def go_back(n_clicks):
    return ''

@callback(
    Output('trend-chart', 'figure'),
    Input('chart-switch', 'n_clicks')
)
def switch_chart(n):
    return fig_line if (n or 0) % 2 == 1 else fig_media

app.clientside_callback(
    """
    function(n) {
        if (!n) { return ''; }
        var box = document.getElementById('wordcloud');
        if (!box) { return ''; }
        var gd = box.getElementsByClassName('js-plotly-plot')[0];
        if (gd && window.Plotly) {
            Plotly.animate(gd, ['settle'], {
                transition: {duration: 1400, easing: 'cubic-out'},
                frame: {duration: 1400, redraw: false}
            });
        }
        return '';
    }
    """,
    Output('wc-anim-dummy', 'children'),
    Input('wc-anim-trigger', 'n_intervals')
)
    
# Run the app
if __name__ == '__main__':
    app.run(debug=True)