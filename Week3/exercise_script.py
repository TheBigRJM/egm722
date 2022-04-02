import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
from cartopy.feature import ShapelyFeature
import cartopy.crs as ccrs
import matplotlib.patches as mpatches


# generate matplotlib handles to create a legend of the features we put in our map.
def generate_handles(labels, colors, edge='k', alpha=1):
    lc = len(colors)  # get the length of the color list
    handles = []
    for i in range(len(labels)):
        handles.append(mpatches.Rectangle((0, 0), 1, 1, facecolor=colors[i % lc], edgecolor=edge, alpha=alpha))
    return handles


plt.ion()

# ---------------------------------------------------------------------------------------------------------------------
# in this section, write the script to load the data and complete the main part of the analysis.
# try to print the results to the screen using the format method demonstrated in the workbook

# load the necessary data here and transform to a UTM projection (Additional Ex. 1-1)

data_folder = 'D://UlsterProgramming//egm722//Week3//data_files//'

wards = gpd.read_file(data_folder + 'NI_Wards.shp')
counties = gpd.read_file(data_folder + 'Counties.shp')

wards = wards.to_crs(epsg=32629)
counties = counties.to_crs(epsg=32629)

join = gpd.sjoin(counties, wards, how='inner', lsuffix='left', rsuffix='right')

# your analysis goes here...
# (Additional ex. 1-2-1) Prints the sum of population per county (including potential ward overlaps)
countyPop = join.groupby(['CountyName'])['Population'].sum()

# (Additional x. 1-2-2 - print max/min county pop'n values)
print('County with maximum population is:', countyPop.idxmax(), countyPop.max())
print('County with minimum population is:', countyPop.idxmin(), countyPop.min())

# (Additional Ex. 2-2) Prints the wards with minimum and maximum populations from list
print('Max population Ward', wards.max())
print('Min population Ward', wards.min())

# (Additional Ex. 2-1) Work out the number, names and populations of wards in multiple counties
dfObj = pd.DataFrame(join)
duplicateDFRow = dfObj[dfObj.duplicated(['Ward'])]
uniqueObj = duplicateDFRow.Ward.unique()

sumUnique = dfObj.loc[dfObj['Ward'].isin(uniqueObj), 'Population'].sum()

print(list(uniqueObj))
print('Sum of populations from Wards in more than one county', sumUnique)


# Create population density columns in the Wards shapefile
for i, row in wards.iterrows(): # iterate over each row in the GeoDataFrame
    wards.loc[i, 'Area_KMsq'] = row['geometry'].area / 1000 # assign the row's geometry area to a new column, Area_KMsq

for i, row in wards.iterrows():# iterate over each row in the GeoDataFrame
    wards.loc[i, 'PopDen'] = row['Population'] / row['Area_KMsq'] # create new column PopDen, assign value by Area/Pop

# print(wards.head()) # print the updated GeoDataFrame to see the changes

# ---------------------------------------------------------------------------------------------------------------------
# below here, you may need to modify the script somewhat to create your map.
# create a crs using ccrs.UTM() that corresponds to our CRS
# Additional Ex 3.
myCRS = ccrs.UTM(29)
# create a figure of size 10x10 (representing the page size in inches
fig, ax = plt.subplots(1, 1, figsize=(10, 10), subplot_kw=dict(projection=myCRS))

# add gridlines below
gridlines = ax.gridlines(draw_labels=True,
                         xlocs=[-8, -7.5, -7, -6.5, -6, -5.5],
                         ylocs=[54, 54.5, 55, 55.5])
gridlines.right_labels = False
gridlines.bottom_labels = False

# to make a nice colorbar that stays in line with our map, use these lines:
divider = make_axes_locatable(ax)
cax = divider.append_axes("right", size="5%", pad=0.1, axes_class=plt.Axes)

# plot the ward data into our axis, using
#ward_plot = wards.plot(column='Population', ax=ax, vmin=1000, vmax=8000, cmap='viridis',
#                       legend=True, cax=cax, legend_kwds={'label': 'Resident Population'})

ward_plot = wards.plot(column='PopDen', ax=ax, vmin=0, vmax=12, cmap='viridis',
                       legend=True, cax=cax, legend_kwds={'label': 'Population Density (residents per sqkm)'})

county_outlines = ShapelyFeature(counties['geometry'], myCRS, edgecolor='r', facecolor='none')

ax.add_feature(county_outlines)
county_handles = generate_handles([''], ['none'], edge='r')

ax.legend(county_handles, ['County Boundaries'], fontsize=12, loc='upper left', framealpha=1)

# save the figure
fig.savefig('sample_map.png', dpi=300, bbox_inches='tight')
