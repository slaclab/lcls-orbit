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

variables = {}
for index, row in BPMS_df.iterrows():
    pvname = f"{row['device_name']}:X"
    positions[pvname] = row["z_position"]
    variables[pvname] = ScalarOutputVariable(name=pvname)




# set up controller
controller = Controller("ca", variables, {}, prefix=None, auto_monitor=True)



long_plot = OrbitDisplay(
    variables, controller, positions
)


# render
curdoc().title = "Demo App"
curdoc().add_root(
    column(
        long_plot.plot
    )
)

curdoc().add_periodic_callback(long_plot.update, 500)
#curdoc().add_periodic_callback(table_monitor.poll, 250)
