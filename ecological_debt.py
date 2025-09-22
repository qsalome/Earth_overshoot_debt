import os
import pathlib
import argparse
import shapely
import pandas as pd
import geopandas
import numpy as np
from datetime import datetime,timedelta
from calendar import isleap
from tqdm import tqdm
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator


#--------------------------------------------------------------------
def polygon_world(gdf_countries):
   """
   Use the polygons and multipolygons of all countries to derive a
   multipolygon for all the countries together. To ensure there is
   no overlap with the other geometry shapes, this new multipolygon
   corresponds to the oceans and seas.
   
   Parameters
   ----------
   gdf_countries: geopandas.geodataframe.GeoDataFrame
         administrative boarders of countries with associated geometry

   Returns
   -------
   shapely.geometry.multipolygon.MultiPolygon or
   shapely.geometry.polygon.Polygon
        polygon for all the countries together ("World")
   """

   poly   = shapely.coverage_union_all([gdf_countries['geometry']])
   square = shapely.geometry.Polygon([(-180,-90),(-180,90),(180,90),(180,-90)])

   return square-poly

#--------------------------------------------------------------------
def read_data_csv(csv_file,polygon,crs):
   """
   Read the World records between 1961 and 2024 and return the annual
   Biocapacity and Ecological Footprint.
   
   Parameters
   ----------
   csv_file: str
         path and name of the csv file to read
   polygon: shapely.geometry.multipolygon.MultiPolygon or
            shapely.geometry.polygon.Polygon
         geometry shape of the country
   crs: pyproj.crs.crs.CRS
         CRS system of the countries polygons and multipolygons

   Returns
   -------
   geopandas.geodataframe.GeoDataFrame
        annual records of the Biocapacity and the Ecological Footprint
        between 1961 and 2024
   """

   df     = pd.read_csv(csv_file)

   for year in np.unique(df['year']):
      d = {'year': [year],
           'EcoFootprint': [df[(df['year'] == year) &
                               (df['Record'] == 'EFConsPerCap')]['Total'].iloc[0]
                           ],
           'Biocapacity':  [df[(df['year'] == year) &
                               (df['Record'] == 'BiocapPerCap')]['Total'].iloc[0]
                           ],
           'geometry': [polygon]}
      gdf = geopandas.GeoDataFrame(d,crs=crs)

      try:
         final_gdf = pd.concat([final_gdf, gdf])
      except:
         final_gdf = gdf.copy()

   final_gdf = final_gdf.reset_index()

   return final_gdf[['year','EcoFootprint','Biocapacity','geometry']]

#--------------------------------------------------------------------
def determine_overshoot_day(annual_records):
   """
   Determine the annual overshoot day, based on the Biocapacity and
   Ecological Footprint.
   
   Parameters
   ----------
   geopandas.geodataframe.GeoDataFrame
        annual records of the Biocapacity and the Ecological Footprint

   Returns
   -------
   geopandas.geodataframe.GeoDataFrame
        annual records, with an additional column containing the Overshoot Day
   """
   biocap = annual_records['Biocapacity'].to_numpy()
   ecofoot = annual_records['EcoFootprint'].to_numpy()

   nbdays = np.array([366 if isleap(year) else 365
                  for year in annual_records['year']])
   overshoot_day = nbdays*biocap/ecofoot
   annual_records['OvershootDay'] = overshoot_day

   formatted_overshoot = np.array([])
   for i in range(len(annual_records)):
      year = annual_records["year"][i]
      overshoot_day = annual_records['OvershootDay'][i]

      if(overshoot_day>nbdays[i]):
         date = 'None'
      else:
         date = datetime.strptime(f"{year}-{int(overshoot_day)}","%Y-%j")
         date = date.isoformat()[:10]

      formatted_overshoot = np.append(formatted_overshoot,date)

   annual_records['OvershootDayFormatted'] = formatted_overshoot

   return annual_records

#--------------------------------------------------------------------
def determine_country_overshoot_day(country_records,world_records):
   """
   Determine the annual overshoot day of a country, based on the Biocapacity
   and Ecological Footprint.
   
   Parameters
   ----------
   geopandas.geodataframe.GeoDataFrame
        annual records of the Biocapacity and the Ecological Footprint

   Returns
   -------
   geopandas.geodataframe.GeoDataFrame
        annual records, with an additional column containing the Overshoot Day
   """
   biocap = annual_records['Biocapacity'].to_numpy()
   ecofoot = annual_records['EcoFootprint'].to_numpy()

   nbdays = np.array([366 if isleap(year) else 365
                  for year in annual_records['year']])
   overshoot_day = nbdays*biocap/ecofoot
   annual_records['OvershootDay'] = overshoot_day

   formatted_overshoot = np.array([])
   for i in range(len(annual_records)):
      year = annual_records["year"][i]
      overshoot_day = annual_records['OvershootDay'][i]

      if(overshoot_day>nbdays[i]):
         date = 'None'
      else:
         date = datetime.strptime(f"{year}-{int(overshoot_day)}","%Y-%j")
         date = date.isoformat()[:10]

      formatted_overshoot = np.append(formatted_overshoot,date)

   annual_records['OvershootDayFormatted'] = formatted_overshoot

   return annual_records

#--------------------------------------------------------------------
def calculate_ecological_debt(annual_records):
   """
   Calculate the annual and cumulated ecological debt (in days), based
   on the overshoot days.

   Parameters
   ----------
   geopandas.geodataframe.GeoDataFrame
        annual records of the Biocapacity, the Ecological Footprint
        and the Overshoot Day

   Returns
   -------
   geopandas.geodataframe.GeoDataFrame
        annual records, with additional columns containing the annual and
        accumulated ecological debt
   """
   nbdays = np.array([366 if isleap(year) else 365
                  for year in annual_records['year']])
   over   = annual_records['OvershootDay']-nbdays


   first_over = np.where(over<0)[0][0]
   debt = np.zeros(len(annual_records))*float('nan')
   for i in range(first_over,len(annual_records),1):
      if(over[i]<0): debt[i] = over[i]
      elif(over[i]<abs(np.sum(debt))): debt[i] = over[i]
      else: debt[i] = abs(np.sum(debt))

   annual_records['AnnualDebt'] = -debt

   cumul_debt = np.zeros(len(annual_records))
   for i in range(len(annual_records)):
      cumul_debt[i] = np.nansum(-debt[:i])

   annual_records['CumulativeDebt'] = cumul_debt

   return annual_records

#--------------------------------------------------------------------
def plot_cumulative_debt(annual_records):
   """
   Plot the evolution of the cumulative ecological debt.
   
   Parameters
   ----------
   geopandas.geodataframe.GeoDataFrame
        annual records of the Biocapacity, the Ecological Footprint,
        the Overshoot Day, the annual and accumulated ecological debt

   Returns
   -------
   matplotlib.figure.Figure
         Evolution of the cumulative ecological debt.
   """
   year = annual_records['year'].to_numpy()
   cumul_debt = annual_records['CumulativeDebt'].to_numpy()/365.25

   fig,ax = plt.subplots(figsize=(10,7))
   ax.bar(year,cumul_debt, width=1,facecolor="black",alpha=0.25,
               linewidth=1,edgecolor="black",
               label='Cumulated debt before 2025: %.2f years'%(cumul_debt[-1]))
   ax.legend(loc='upper left')

   plt.title(f"Evolution of the humanity ecological debt")
   plt.xlabel("Year")
   plt.ylabel("Cumulated ecological debt (years)")
   plt.xlim([1961,2025])

   ax.tick_params(labelright=True,right=True,which='both')
   ax.xaxis.set_major_locator(MultipleLocator(10))
   ax.xaxis.set_minor_locator(MultipleLocator(5))
   ax.yaxis.set_major_locator(MultipleLocator(5))
   ax.yaxis.set_minor_locator(MultipleLocator(1))

   fig.tight_layout()

   return fig

#--------------------------------------------------------------------



#parser = argparse.ArgumentParser()
#parser.add_argument("--month", type=int, default=1,
#                    help="Month (number) of interest.")

#args  = parser.parse_args()
#month = args.month


# Paths definition
NOTEBOOK_PATH  = pathlib.Path().resolve()
DATA_DIRECTORY = NOTEBOOK_PATH / "data"
FIG_DIRECTORY  = NOTEBOOK_PATH / "figures"


countries = geopandas.read_file(DATA_DIRECTORY /
         "ne_10m_admin_0_countries")


country = 'World'

polygon = polygon_world(countries)

annual_records = read_data_csv(DATA_DIRECTORY / file,
      polygon,countries.crs)

records_with_overshot = determine_overshoot_day(annual_records)

records_with_debt = calculate_ecological_debt(records_with_overshot)

fig = plot_cumulative_debt(records_with_debt)
fig.savefig(FIG_DIRECTORY / f"Evolution_ecological_debt.png")


