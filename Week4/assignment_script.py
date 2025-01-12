import numpy as np
import rasterio as rio
import geopandas as gpd
import cartopy.crs as ccrs
import matplotlib.pyplot as plt
from shapely.ops import cascaded_union
from shapely.geometry.polygon import Polygon
from cartopy.feature import ShapelyFeature
import matplotlib.patches as mpatches


def generate_handles(labels, colors, edge='r', alpha=1):
    lc = len(colors)  # get the length of the color list
    handles = []
    for i in range(len(labels)):
        handles.append(mpatches.Rectangle((0, 0), 1, 1, facecolor=colors[i % lc], edgecolor=edge, alpha=alpha))
    return handles


def percentile_stretch(img, pmin=0., pmax=100.):
    '''
    This is where you should write a docstring.
    '''
    # here, we make sure that pmin < pmax, and that they are between 0, 100
    if not 0 <= pmin < pmax <= 100:
        raise ValueError('0 <= pmin < pmax <= 100')
    # here, we make sure that the image is only 2-dimensional
    if not img.ndim == 2:
        raise ValueError('Image can only have two dimensions (row, column)')

    minval = np.percentile(img, pmin)
    maxval = np.percentile(img, pmax)

    stretched = (img - minval) / (maxval - minval)  # stretch the image to 0, 1
    stretched[img < minval] = 0  # set anything less than minval to the new minimum, 0.
    stretched[img > maxval] = 1  # set anything greater than maxval to the new maximum, 1.

    return stretched


def img_display(img, ax, bands, stretch_args=None, **imshow_args):
    '''
    This is where you should write a docstring.
    '''
    dispimg = img.copy().astype(np.float32)  # make a copy of the original image,
    # but be sure to cast it as a floating-point image, rather than an integer

    for b in range(img.shape[0]):  # loop over each band, stretching using percentile_stretch()
        if stretch_args is None:  # if stretch_args is None, use the default values for percentile_stretch
            dispimg[b] = percentile_stretch(img[b])
        else:
            dispimg[b] = percentile_stretch(img[b], **stretch_args)

    # next, we transpose the image to re-order the indices
    dispimg = dispimg.transpose([1, 2, 0])

    # finally, we display the image
    handle = ax.imshow(dispimg[:, :, bands], **imshow_args)

    return handle, ax


# ------------------------------------------------------------------------
# note - rasterio's open() function works in much the same way as python's - once we open a file,
# we have to make sure to close it. One easy way to do this in a script is by using the with statement shown
# below - once we get to the end of this statement, the file is closed.
data_folder = 'D://UlsterProgramming//egm722//Week4//data_files//'
with rio.open(data_folder + '/NI_Mosaic.tif') as dataset:
    img = dataset.read()
    xmin, ymin, xmax, ymax = dataset.bounds

# your code goes here!

w2data_folder = 'D://UlsterProgramming//egm722//Week2//data_files//'

outline = gpd.read_file(w2data_folder + 'NI_outline.shp')
towns = gpd.read_file(w2data_folder + 'Towns.shp')
water = gpd.read_file(w2data_folder + 'Water.shp')
rivers = gpd.read_file(w2data_folder + 'Rivers.shp')
counties = gpd.read_file(w2data_folder + 'counties.shp')

myCRS = ccrs.UTM(29) # note that this matches with the CRS of our image
fig, ax = plt.subplots(1, 1, figsize=(10, 10), subplot_kw=dict(projection=myCRS))

# Add NI image to axis
my_kwargs = {'extent': [xmin, xmax, ymin, ymax], 'transform': myCRS}

my_stretch = {'pmin': 0.1, 'pmax': 99.9}

h, ax = img_display(img, ax, [2, 1, 0], stretch_args=my_stretch, **my_kwargs)

# ShapelyFeature creates a polygon, so for point data we can just use ax.plot()
town = towns[towns['town_city'] == 0]
city = towns[towns['town_city'] == 1]

town_handle = ax.plot(town.geometry.x, town.geometry.y, 's', color='b', ms=6, transform=myCRS)
city_handle = ax.plot(city.geometry.x, city.geometry.y, 'D', color='m', ms=6, transform=myCRS)

# update county_names to take it out of uppercase text
#nice_names = [name.title() for name in county_names]

# create a polygon using co-ordinates for NI raster xy min/max values to fill the axis to use as a background
border = Polygon([((xmin), (ymin)), ((xmin), (ymax)), ((xmax), (ymax)), ((xmax), (ymin))])

union = cascaded_union(counties['geometry'].values) # Create a cascaded union of the counties of NI

# remove areas of counties from border using union and transform to shapely feature.
overlay = ShapelyFeature(border.symmetric_difference(union), myCRS,
                        edgecolor='r',
                        facecolor='white', # colour solid white
                        alpha=0.5)  # make the background semi-transparent

# add the county outlines
county_outlines = ShapelyFeature(counties['geometry'], myCRS, edgecolor='r', facecolor='none')

# add overlay to axis
ax.add_feature(overlay)
ax.add_feature(county_outlines)

# generate a list of handles for the county datasets
county_handles = generate_handles([''], ['none'], edge='r')

# ax.legend() takes a list of handles and a list of labels corresponding to the objects you want to add to the legend
handles = county_handles + town_handle + city_handle
labels = ['County boundaries', 'Town', 'City']

leg = ax.legend(handles, labels, title='Legend', title_fontsize=14,
                 fontsize=12, loc='upper left', frameon=True, framealpha=1)

gridlines = ax.gridlines(draw_labels=True,
                         xlocs=[-8, -7.5, -7, -6.5, -6, -5.5],
                         ylocs=[54, 54.5, 55, 55.5])

gridlines.left_labels = False
gridlines.bottom_labels = False
ax.set_extent([xmin, xmax, ymin, ymax], crs=myCRS)


fig.savefig('map.png', bbox_inches='tight', dpi=300)
