import pathlib
import geopandas
import numpy as np

import folium
import base64
import branca.colormap
from geocube.vector import vectorize
from folium.plugins import GroupedLayerControl

from calendar import month_name
from geoanalysis_functions import extract_temperatures


from branca.element import MacroElement
from jinja2 import Template


#--------------------------------------------------------------------
def new_image_layer(gdf,name="",entry="",image=None):
   """
   Produce a polygon layer based on a GeoDataFrame
   
   Parameters
   ----------
   gdf: geopandas.geodataframe.GeoDataFrame
         Municipalities of interest with temperatures information
   name: str
         Name of the layer
   image: str
         Path of the image to be included in a popup
   year: int
         year to be added in name
   month: int
         month to be added in name
   day: int
         day to be added in name

   Returns
   -------
   folium.features.GeoJson
         layer to be added to the interactive map
   """

   layer = folium.Choropleth(
      geo_data=gdf,
      data=gdf,
      columns=("Country", entry),
      key_on="feature.id",
      name=name,

#      bins=[0, 5, 10, 15, 20, 25, 30],
      fill_color="YlOrRd",
      line_weight=0.5,
      legend_name=f"{name} (years)",
      opacity=0.7,

      highlight=True
      )

   return layer

#--------------------------------------------------------------------
def new_polygon_layer(gdf,name="",opacity=0.8,image=None):
   """
   Produce a polygon layer based on a GeoDataFrame
   
   Parameters
   ----------
   gdf: geopandas.geodataframe.GeoDataFrame
         Municipalities of interest with temperatures information
   name: str
         Name of the layer
   image: str
         Path of the image to be included in a popup
   year: int
         year to be added in name
   month: int
         month to be added in name
   day: int
         day to be added in name

   Returns
   -------
   folium.features.GeoJson
         layer to be added to the interactive map
   """

   if image is not None:
      popup_html = np.array([])
      for idx in range(len(gdf)):
         city = gdf["NAMEFIN"][idx]
         imname  = image.name.format(f"{month_name[month]}",city)
         encoded = base64.b64encode(
                     open(image.with_name(imname), 'rb').read()).decode()
         string = f'<img src="data:image/png;base64,{encoded}" width="300">'
         popup_html = np.append(popup_html,string)
      gdf['popup_html'] = popup_html

      popup = folium.GeoJsonPopup(
         fields=["popup_html"],
         aliases=[""],
         labels=True,
         sticky=False,
         localize=True,
      )
   else:
      popup=None

   # Define custom tooltip with HTML
   tooltip = folium.features.GeoJsonTooltip(
      fields=("Country","Period","LastOvershootDay",
              "LocalCumulatedDebt","GlobalCumulatedDebt"),
      aliases=("Country:","Period:",
               "Last Overshoot Day:",
               "Cumulated debt (locally)",
               "Cumulated debt (globally)"),
      labels=True,
      sticky=True,
      localize=True,
      )

   layer = folium.GeoJson(
      gdf,
      style_function=lambda feature: {
            "fillColor": "transparent",
            "color": "black",
            "weight": 2
            },
      opacity=opacity,
      name=name,
      show=True,
      tooltip=tooltip,
      popup=popup
   )

   return layer

#--------------------------------------------------------------------



# Paths definition
NOTEBOOK_PATH  = pathlib.Path().resolve()
DATA_DIRECTORY = NOTEBOOK_PATH / "data"
FIG_DIRECTORY  = NOTEBOOK_PATH / "figures"
HTML_DIRECTORY = NOTEBOOK_PATH / "html"


copyright  = ''
#copyright += 'Temperature data (c) <a href="https://en.ilmatieteenlaitos.fi/">'
#copyright += 'Finnish Meteorological Institute</a> & '
#copyright += '<a href="https://paituli.csc.fi/download.html">Paituli</a>, '
copyright += 'Map data (c) <a href="http://www.openstreetmap.org/copyright">'
copyright += 'OpenStreetMap</a> contributors.'

# Initial map
interactive_map = folium.Map(
    max_bounds=True,
    location=[54.9, 12.7],
    zoom_start=4,
#    min_lat=59.7,
#    max_lat=70.1,
#    min_lon=21.2,
#    max_lon=31.6,
    interactive=True,
    attr = copyright
)


# Read the Finland municipalities (as defined in 2021)
debts = geopandas.read_file(DATA_DIRECTORY /
         "Local_and_global_ecological_debt_countries.gpkg")
#         ).to_crs("EPSG:3067")

debts["LocalCumulatedDebt"] = debts["LocalCumulatedDebt"]/365.25
debts["GlobalCumulatedDebt"] = debts["GlobalCumulatedDebt"]/365.25
debts["Period"]=[f"{init}-{final}" for init,final in
                     zip(debts["FirstYear"],debts["LastYear"])]


layers = {}

folium_layer = new_image_layer(debts.iloc[1:],name="Ecological debt",
            entry="GlobalCumulatedDebt")
layers.update({"0": folium_layer})
layers["0"].add_to(interactive_map)


folium_layer = new_image_layer(debts.iloc[1:],name="Local ecological debt",
            entry="LocalCumulatedDebt")
layers.update({"1": folium_layer})
layers["1"].add_to(interactive_map)


gdf = debts[debts["Country"]=="World"]
folium_layer = new_polygon_layer(gdf,name="World",opacity=0)
folium_layer.add_to(interactive_map)

folium_layer = new_polygon_layer(debts.iloc[1:],name="Countries")
folium_layer.add_to(interactive_map)



folium.LayerControl(collapsed=False).add_to(interactive_map)


list_layers = [layers[key] for key in layers.keys()]
GroupedLayerControl(
   groups={'Layers': list_layers},
   collapsed=False,
   exclusive_groups=True
).add_to(interactive_map)


interactive_map.save(HTML_DIRECTORY /
            "ecological_debts_countries.html")


