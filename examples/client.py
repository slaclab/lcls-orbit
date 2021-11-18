import pandas as pd
from bokeh.io import curdoc
from bokeh import palettes
from bokeh.layouts import column, row
from bokeh.models import LinearColorMapper, Div

from lume_epics.client.controller import Controller
from lume_epics.client.monitors import PVTable
from lume_model.variables import ScalarOutputVariable

from lcls_orbit.widgets import OrbitDisplay

df= pd.read_csv("examples/cu_hxr_basic.csv")
BPMS_df = df[df["device_name"].apply(lambda x: isinstance(x, str) and "BPMS" in x)]


positions = {}

x_variables = {}
y_variables = {}
for index, row in BPMS_df.iterrows():
    positions[f"{row['device_name']}:X"] = row["z_position"]
    positions[f"{row['device_name']}:Y"] = row["z_position"]
    x_variables[f"{row['device_name']}:X"] = ScalarOutputVariable(name=f"{row['device_name']}:X")
    y_variables[f"{row['device_name']}:Y"] = ScalarOutputVariable(name=f"{row['device_name']}:Y")

all_variables = {**x_variables, **y_variables}

# set up controller
controller = Controller("ca", all_variables, {}, prefix=None, auto_monitor=True)



long_plot_x = OrbitDisplay(
    x_variables, controller, positions
)

long_plot_y = OrbitDisplay(
    y_variables, controller, positions
)


# render
curdoc().title = "Demo App"
curdoc().add_root(
    column(
        long_plot_x.plot,
        long_plot_y.plot,
    )
)

curdoc().add_periodic_callback(long_plot_x.update, 500)
curdoc().add_periodic_callback(long_plot_y.update, 500)
