import cmasher
import datashader as ds
from datashader import transfer_functions as tf
import pandas as pd

# local settings
DATA_PATH = "data/gitcoin_datashader.csv"
IMG_PATH = "img/gitcoin_datashader.png"

# image parameters
START_DATE = pd.to_datetime('2018-01-01').tz_localize('UTC')
CMAP = cmasher.ocean

# load and arrange the data
df = pd.read_csv(DATA_PATH, parse_dates=['time'])
df = df[df['time'] >= START_DATE]
df['day'] = df['time'].apply(lambda x: (x.date() - START_DATE.date()).days)
df['hour'] = df['time'].dt.hour + df['time'].dt.minute/60
df['amount'] = 1

# make the image
aspect = (1 + 5**0.5) / 2
width = int(df['day'].nunique() / 2)
height = int(width / aspect)
canvas = ds.Canvas(plot_width=width, plot_height=height)
points = canvas.points(df, "day", "hour", agg=ds.sum("amount")).fillna(0)
heatmap = tf.shade(points, cmap=CMAP)

# save the image
heatmap.to_pil().save(IMG_PATH)