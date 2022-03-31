import plotly.graph_objects as go
import numpy as np

import pandas as pd

# Read data from a csv
z_data = pd.read_csv('https://raw.githubusercontent.com/plotly/datasets/master/api_docs/mt_bruno_elevation.csv')
z_data.to_numpy()

z_data = np.random.randint(1,9,[5,5])

#fig = go.Figure(data=[go.Surface(z=z_data.values)])
fig = go.Figure(data=[go.Surface(z=z_data)])

fig.update_layout(title='Mt Bruno Elevation', autosize=False,
                  width=500, height=500,
                  margin=dict(l=65, r=50, b=65, t=90))

fig.show()