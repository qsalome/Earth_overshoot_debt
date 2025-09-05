import pathlib
import argparse
import shapely
import pandas as pd
import geopandas
import numpy as np
from datetime import datetime,timedelta
from calendar import isleap,month_name
from tqdm import tqdm
from itertools import product
import lmfit
#import fit_functions
#from geoanalysis_functions import read_data_csv
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator


#--------------------------------------------------------------------
def read_data_csv(csv_file,gdf_countries):
   """
   Read the World records between 1961 and 2024 and return the annual
   Biocapacity and Ecological Footprint.
   
   Parameters
   ----------
   csv_file: str
         path and name of the csv file to read
   gdf_countries: geopandas.geodataframe.GeoDataFrame
         administrative boarders of countries with associated geometry

   Returns
   -------
   geopandas.geodataframe.GeoDataFrame
        annual records of the Biocapacity and the Ecological Footprint
        between 1961 and 2024
   """

   df   = pd.read_csv('data/Country_Trends.csv')
   poly = shapely.coverage_union_all([gdf_countries['geometry']])

   for year in np.unique(df['year']):
      d = {'year': [year],
           'EcoFootprint': [df[(df['year'] == year) &
                               (df['Record'] == 'EFConsTotGHA')]['Total'].iloc[0]
                           ],
           'Biocapacity':  [df[(df['year'] == year) &
                               (df['Record'] == 'BiocapTotGHA')]['Total'].iloc[0]
                           ],
           'geometry': [poly]}
      gdf = geopandas.GeoDataFrame(d,crs=gdf_countries.crs)

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
annual_records = read_data_csv(DATA_DIRECTORY /
         "Country_Trends.csv",countries)


records_with_overshot = determine_overshoot_day(annual_records)

records_with_debt = calculate_ecological_debt(records_with_overshot)

fig = plot_cumulative_debt(records_with_debt)
fig.savefig(FIG_DIRECTORY / f"Evolution_ecological_debt.png")


