import pandas as pd
from bokeh.io import curdoc
from bokeh import palettes
from bokeh.layouts import column, row
from bokeh.models import LinearColorMapper, Div

from lume_epics.client.controller import Controller
from lume_epics.client.monitors import PVTable
from lume_model.variables import ScalarOutputVariable, TableVariable

from lcls_orbit.widgets import OrbitDisplay

df= pd.read_csv("examples/cu_hxr_basic.csv")
BPMS_df = df[df["device_name"].apply(lambda x: isinstance(x, str) and "BPMS" in x)]

positions = {}

variables = {}
table = {"X": {}, "Y": {}, "Z": {}}
rows = []


for index, row in BPMS_df.iterrows():
    rows.append(row['device_name'])
    output_x = ScalarOutputVariable(name=f"{row['device_name']}:X")
    output_y = ScalarOutputVariable(name=f"{row['device_name']}:Y")
    table["X"][row['device_name']] = output_x
    table["Y"][row['device_name']] = output_y
    table["Z"][row['device_name']]=row["z_position"]
    variables[f"{row['device_name']}:X"]= output_x
    variables[f"{row['device_name']}:Y"]=output_y

# set up table var
table_var = TableVariable(table_rows=rows, table_data=table)

# set up controller
controller = Controller("ca", variables, {}, prefix=None, auto_monitor=True)

# create longitudinal plot
long_plot = OrbitDisplay(
    table_var, controller
)

# render
curdoc().title = "Demo App"
curdoc().add_root(
    column(
        long_plot.x_plot,
        long_plot.y_plot,
    )
)

curdoc().add_periodic_callback(long_plot.update, 500)
