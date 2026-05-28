# Chicago Mural Registry Dashboard

## Live Demo
View the deployed dashboard: https://chicago-mural-registry-dashboard.onrender.com/

## Overview
An interactive dashboard built with Dash for exploring Chicago's registry of outdoor murals, 
featuring summary statistics, a searchable/sortable table, an interactive map, an animated word cloud of mural themes, and switchable animated charts.

## screenshot
screenshots of the dashboard 

## Data
Mural Registry(Chicago Public Data)
https://data.cityofchicago.org/Historic-Preservation/Mural-Registry/we8h-apcf/about_data
Link to csv file:https://data.cityofchicago.org/resource/we8h-apcf.csv
Includes artwork_title, artist_credit, year_installed, zip code, latitude, longitude, and media

## Setup & How to Run Locally
```bash
pip install -r requirements.txt
```

## Run

```bash
python dash_final.py
```

Then open the local Dash URL shown in the terminal, usually:

```text
http://127.0.0.1:8050/
```
## Files
- README.md
- requirement.txt
-`dash_final.py`: main Dash app
- assets folder
    bg3.jpg: page background image
    flag.png: flag image shown on each side of the title
    cards.css: styling for the summary circles and their hover "pop" animation
    
## Visualization Design Features
# Three circles for the summary statistics
The total number of murals registered, the number of unique artists, and the number of unique zip codes
hover animation

# Table with filtering options
Includes artwork_title, artist_credit, year_installed, zip
Referred to w8_interactive dash_example.py
Two filtering options: latest and oldest; filter murals based on year_installed
Search bar: search by title or artist name
    Results can also be filtered by the latest and oldest
    If no result found, return "No murals found for ... Go back" 

# Interactive map with hover information
Referred to Plotly interactive map examples: https://plotly.com/python/tile-scatter-maps
Data cleaning
   Only keep murals with valid latitude and longitude
Hover information: hover on each mural will show its title, artist, and year installed
Add base map layer and adjust layout

# Word cloud for mural themes
Find frequent word in the artwork_title and description_of_artwork columns
openning animation
frequent words have larger bubbles and darker color
hover information: hover on each word bubble to see the actual frequency count
Data cleaning
    words such as murals, wall, image, painted.. don't count toward the word cloud.

# Switchable Interactive Charts
Switch button to switch between bar chart and line chart

# Interactive bar chart with year slider
Visualize the popularity of the mural media type over time
Referred to w8_interactive plotly_interactive.py
Group murals by media type and installed year 
Data cleaning
   Only keep murals with valid media and year_installed
   Simplify all medias into four major categories: mixed media, mosaic/tile, paint, spray paint
   Count how many murals exist each year for each media category
Visualization optimization
   Fill in missing year/media combos with 0 so the animation is smooth
   Map each media category to a different shade of blue
   Update layout by adjusting margins and bar gap

# Interactive line chart
Visualize the trend of murals installed each year (from 1971 to 2024)
animation: plot the line chart in real time.
Include play and pause button

