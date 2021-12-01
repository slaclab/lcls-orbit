import pandas as pd
import numpy as np
from matplotlib import cm
from matplotlib.colors import ListedColormap
from bokeh.io import curdoc
from bokeh.layouts import column, row

from bokeh.models import CustomJS, Dropdown, Div
from bokeh.palettes import Blues9, Reds9
from bokeh.themes import built_in_themes
from lume_epics.client.controller import Controller
from lume_model.variables import ScalarOutputVariable, TableVariable

from lcls_orbit.widgets import OrbitDisplay

hxr_df= pd.read_csv("examples/cu_hxr_basic.csv")
hxr_BPMS_df = hxr_df[hxr_df["device_name"].apply(lambda x: isinstance(x, str) and "BPMS" in x)]

sxr_df= pd.read_csv("examples/cu_hxr_basic.csv")
sxr_BPMS_df = sxr_df[sxr_df["device_name"].apply(lambda x: isinstance(x, str) and "BPMS" in x)]



sxr_cmp = [(18, 9, 28), (38, 28, 39), (78, 18, 40), (98, 70, 82), (84, 23, 98)]
bokeh_colors = ["#%02x%02x%02x" % (r, g, b) for r, g, b in sxr_cmp]


positions = {}

variables = {}
hxr_table = {"X": {}, "Y": {}, "Z": {}}
hxr_rows = []


for index, table_row in hxr_BPMS_df.iterrows():
    hxr_rows.append(table_row['device_name'])
    output_x = ScalarOutputVariable(name=f"{table_row['device_name']}:X")
    output_y = ScalarOutputVariable(name=f"{table_row['device_name']}:Y")
    hxr_table["X"][table_row['device_name']] = output_x
    hxr_table["Y"][table_row['device_name']] = output_y
    hxr_table["Z"][table_row['device_name']]=table_row["z_position"]
    variables[f"{table_row['device_name']}:X"]= output_x
    variables[f"{table_row['device_name']}:Y"]=output_y

sxr_table = {"X": {}, "Y": {}, "Z": {}}
sxr_rows = []

for index, table_row in sxr_BPMS_df.iterrows():
    sxr_rows.append(table_row['device_name'])
    output_x = ScalarOutputVariable(name=f"{table_row['device_name']}:X")
    output_y = ScalarOutputVariable(name=f"{table_row['device_name']}:Y")
    sxr_table["X"][table_row['device_name']] = output_x
    sxr_table["Y"][table_row['device_name']] = output_y
    sxr_table["Z"][table_row['device_name']] = table_row["z_position"]
    variables[f"{table_row['device_name']}:X"] = output_x
    variables[f"{table_row['device_name']}:Y"] = output_y

# set up table var
hxr_table_var = TableVariable(table_rows=hxr_rows, table_data=hxr_table)
sxr_table_var = TableVariable(table_rows=sxr_rows, table_data=sxr_table)

hxr_shading_var = ScalarOutputVariable(name='GDET:FEE1:241:ENRC')
sxr_shading_var = ScalarOutputVariable(name='EM1K0:GMD:HPS:milliJoulesPerPulse')

variables['GDET:FEE1:241:ENRC'] = hxr_shading_var
variables['EM1K0:GMD:HPS:milliJoulesPerPulse'] = sxr_shading_var

# set up controller
controller = Controller("ca", variables, {}, prefix=None, auto_monitor=True)



# create longitudinal plot
long_plot = OrbitDisplay(
    hxr_table_var, controller, width=1024, color_var= hxr_shading_var, color_map=sxr_cmp, extents=[0,5]
)

label = Div(
    text=f"<b>HXR</b>",
    style={
        "font-size": "150%",
        "color": "#3881e8",
        "text-align": "center",
        "width": "100%",
    },
)

def toggle_callback(event):

    label.text=event.item

    if event.item == "sxr":
        long_plot.update_table(sxr_table_var)
        long_plot.update_colormap(sxr_shading_var, Reds9, extents = [0,5])

    elif event.item == "hxr":
        long_plot.update_table(hxr_table_var)
        long_plot.update_colormap(hxr_shading_var, Blues9, extents = [0,5])



menu = [("SXR", "sxr"), ("HXR", "hxr")]

dropdown = Dropdown(label="line", button_type="default", menu=menu)
dropdown.on_click(toggle_callback)

# render
curdoc().theme = 'dark_minimal'
curdoc().title = "Demo App"
curdoc().add_root(
    column(
        row(column(label), column(dropdown)),
        long_plot.x_plot,
        long_plot.y_plot,
    )
)

curdoc().add_periodic_callback(long_plot.update, 500)
