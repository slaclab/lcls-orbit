from typing import List, Dict
import logging
import numpy as np
from datetime import datetime

from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, Span, Button, ColorBar, LinearColorMapper, Dropdown, LinearAxis, HoverTool, Div

from lume_model.variables import TableVariable, ScalarVariable
from lume_epics.client.controller import (
    Controller
)
from lume_epics.client.monitors import PVTable, PVScalar

from lcls_orbit import SXR_COLORS, HXR_COLORS, SXR_AREAS, HXR_AREAS

logger = logging.getLogger(__name__)


class OrbitDisplay:
    """Object holding orbit display widgets.

    """

    def __init__(
        self,
        hxr_table: TableVariable,
        sxr_table: TableVariable,
        hxr_shading_var: ScalarVariable,
        sxr_shading_var: ScalarVariable, 
        controller: Controller,
        height: int = 400,
        width: int = 600,
        bar_width: int = None,
        color_var: ScalarVariable = None,
        color_map: list = None,
        extents: list = None,
        reference_n: int = 15,
        active_beamline: str = "hxr",
    ):

        # construct z
        self._z = []
        self._active_beamline = active_beamline

        self._sxr_table = sxr_table
        self._hxr_table = hxr_table
        self._sxr_shading_var = sxr_shading_var
        self._hxr_shading_var = hxr_shading_var

        if self._active_beamline == "sxr":
            table = self._sxr_table

        elif self._active_beamline == "hxr": 
            table = self._hxr_table

        for row, value in table.table_data["Z"].items():
            self._z.append(value)

        self._monitor = PVTable(table, controller)
        self._controller = controller


        # validate color inputs
        if color_var is not None:
            self._color_monitor = PVScalar(color_var, controller)
            if extents is None:
                raise ValueError("Color map requires passing of extents.")
            else:
                self._extents = np.array(extents)

            if color_map is None:
                raise ValueError("Color map not provided.")
            else:
                self._color_map = color_map

        if not bar_width:
            self._bar_width = (max(self._z) - min(self._z)) / (len(self._z) + 1)
        else:
            self._bar_width = bar_width

        self._x_source = ColumnDataSource(dict(x=[], y=[], device=[], color=[]))
        self._y_source = ColumnDataSource(dict(x=[], y=[], device=[], color=[]))

        tooltips_x = [
            ("device", "@device"),
            ("value", "@y"),
            ("location", "@x{0.0}")
        ]
        
        x_hover = HoverTool(tooltips=tooltips_x)

        # set up x plot
        self.x_plot = figure(
            y_range=(-1, 1),
            x_range=(min(self._z) - self._bar_width / 2.0, max(self._z) + self._bar_width / 2.0),
            width=width,
            height=height,
            toolbar_location="right",
            title="X (mm)",
        )
        self.x_plot.vbar(x="x", bottom=0, top="y", width=self._bar_width, source=self._x_source,  color="color")
        self.x_plot.add_tools(x_hover)
        self.x_plot.xgrid.grid_line_color = None
        self.x_plot.ygrid.grid_line_color = None

        self.x_plot.xaxis.ticker.desired_num_ticks = 10
        self.x_plot.xaxis.ticker.num_minor_ticks = 10

        self.x_plot.ygrid.grid_line_color = None
        self.x_plot.xaxis.axis_label = "z (m)"
        self.x_plot.outline_line_color = None

        # set up y plot
        tooltips_y = [
            ("device", "@device"),
            ("value", "@y"),
            ("location", "@x{0.0}")
        ]

        y_hover = HoverTool(tooltips=tooltips_y)

        self.y_plot = figure(
            y_range=(-1, 1),
            x_range=self.x_plot.x_range,
            width=width,
            height=height,
            toolbar_location="right",
            title="Y (mm)",
        )
        self.y_plot.vbar(x="x", bottom=0, top="y", width=self._bar_width, source=self._y_source, color="color")
        self.y_plot.add_tools(y_hover)
        self.y_plot.xgrid.grid_line_color = None
        self.y_plot.ygrid.grid_line_color = None

        self.y_plot.xaxis.ticker.desired_num_ticks = 10
        self.y_plot.xaxis.ticker.num_minor_ticks = 10

        self.y_plot.ygrid.grid_line_color = None
        self.y_plot.xaxis.axis_label = "z (m)"
        self.y_plot.outline_line_color = None

        # track devices 
        self._devices = table.rows

        # indicator whether collecting reference
        self._collecting_reference = False

        # store reference
        self._reference_measurements = {"X": {device: [] for device in self._devices}, "Y": {device: [] for device in self._devices}}
        self._active_reference = {"X": {device: 0 for device in self._devices}, "Y": {device: 0 for device in self._devices}}
        self._active_reference_timestamp = None
        self._reference_registry = {"sxr": {}, "hxr": {}}
        self._active_beamline = active_beamline

        self.label = Div(
            text="<b>HXR</b>",
            style={
                "font-size": "150%",
                "color": "#3881e8",
                "text-align": "center",
                "width": "100%",
            },
        )

        menu = [("SXR", "sxr"), ("HXR", "hxr")]
        self.beamline_selection_dropdown = Dropdown(label="Beamline", button_type="default", menu=menu)
        self.beamline_selection_dropdown.on_click(self._toggle_callback)

        # how many reference steps to collect
        self._reference_n = reference_n
        self._reference_count = reference_n

        # reference button
        self.reference_button = Button(label="Collect Reference")
        self.reference_button.on_click(self._collect_reference)

        # save reference button
        self.save_reference_button = Button(label="Save Reference")
        self.save_reference_button.on_click(self._save_reference)

        # reset button
        self.reset_reference_button = Button(label="Reset")
        self.reset_reference_button.on_click(self._reset_reference)

        # reset button
        self.compare_reference_dropdown = Dropdown(label="Set Reference", menu=[])
        self.compare_reference_dropdown.on_click(self._set_reference)

        # add color bars
        sxr_color_mapper = LinearColorMapper(palette=SXR_COLORS, low=extents[0], high=extents[1])
        hxr_color_mapper = LinearColorMapper(palette=HXR_COLORS, low=extents[0], high=extents[1])

        self.sxr_color_bar = ColorBar(color_mapper=sxr_color_mapper)
        self.hxr_color_bar = ColorBar(color_mapper=hxr_color_mapper)

        self.x_plot.add_layout(self.sxr_color_bar, 'right')
        self.x_plot.add_layout(self.hxr_color_bar, 'right')

        self.sxr_color_bar.visible = False

        self.x_plot.extra_x_ranges = {"locations": self.x_plot.x_range}
        self._location_axis = LinearAxis(x_range_name="locations")
        self._location_axis.major_label_orientation = "vertical"

        if self._active_beamline == "sxr":
            self._location_axis.ticker = list(SXR_AREAS.keys())
            self._location_axis.major_label_overrides = SXR_AREAS

        elif self._active_beamline == "hxr":
            self._location_axis.ticker = list(HXR_AREAS.keys())
            self._location_axis.major_label_overrides = HXR_AREAS

        self.x_plot.add_layout(self._location_axis, 'above')

    
    def _toggle_callback(self, event):
        if event.item == "sxr":
            self.label.text="<b>SXR</b>"
            self.label.style.update({"color":  "#c40000"})
            self.toggle_beamline("sxr")


        elif event.item == "hxr":
            self.label.text="<b>HXR</b>"
            self.label.style.update({"color": "#3881e8"})
            self.toggle_beamline("hxr")



    def update_table(self, table: dict) -> None:
        """Assign new table variable.
        
        """
        self._monitor = PVTable(table, self._controller)

        self._z = []

        # caget_many
        for row, value in table.table_data["Z"].items():
            self._z.append(value)


        self._reference_measurements = {"X": {row: [] for row in table.rows}, "Y": {row: [] for row in table.rows}}
        self._devices =  table.rows
        self._active_reference = {"X": {device: 0 for device in self._devices}, "Y": {device: 0 for device in self._devices}}


    def update(self) -> None:
        """
        Callback which updates the plot to reflect updated process variable values or
        new process variable.

        """
        vals = self._monitor.poll()


        if self._color_monitor is not None:
            color_val = self._color_monitor.poll()
            idx = (np.abs(self._extents - color_val)).argmin()
            color = self._color_map[idx]
            colors = [color for device in vals["X"]]

        else:
            # use default gray color
            colors = ["#695f5e" for device in vals["X"] ]


        # if collecting reference, update values
        if self._collecting_reference:
            self._reference_count -= 1

            for device in vals["X"]:
                self._reference_measurements["X"][device].append(vals["X"][device])
            
            for device in vals["Y"]:
                self._reference_measurements["Y"][device].append(vals["Y"][device])

            # check n remaining
            if self._reference_count == 0:
                self._collecting_reference=False

                for device in self._devices:
                    x_mean = np.mean([x for x in self._reference_measurements["X"][device] if x != None])
                    y_mean = np.mean([y for y in self._reference_measurements["Y"][device] if y != None])

                    if not np.isnan(x_mean):
                        self._active_reference["X"][device] = x_mean

                    if not np.isnan(y_mean):
                        self._active_reference["Y"][device] = y_mean

                # reset
                for device in self._reference_measurements["X"]:
                    self._reference_measurements["X"][device] = []
                
                for device in self._reference_measurements["Y"]:
                    self._reference_measurements["Y"][device] = []


                # reset button
                self.reference_button.label = "Collect reference"
                self.reference_button.disabled = False
                self._reference_count = 0

                # reset
                self._reference_count = self._reference_n


        # modify vals w.r.t. reference
        for device in vals["X"]:
            if vals["X"][device] is not None:
                vals["X"][device] = self._active_reference["X"][device] - vals["X"][device]
        for device in vals["Y"]:
            if vals["Y"][device] is not None:
                vals["Y"][device] = self._active_reference["Y"][device] - vals["Y"][device]


        devices = [device for device in vals['X']]
        x = np.array([vals["X"][device] for device in vals["X"]], dtype=np.float64)
        y = np.array([vals["Y"][device] for device in vals["Y"]], dtype=np.float64)

        # add hline if 0 inside
        if min(x) < 0 < max(x):
            hline = Span(
                location=0, dimension="width", line_color="black", line_width=2
            )
            self.x_plot.add_layout(hline)


        # add hline if 0 inside
        if min(y) < 0 < max(y):
            hline = Span(
                location=0, dimension="width", line_color="black", line_width=2
            )
            self.y_plot.add_layout(hline)

        self._x_source.data.update({"x": self._z, "y": x, "device": devices, "color": colors})
        self._y_source.data.update({"x": self._z, "y": y, "device": devices, "color": colors})

    def update_colormap(self, color_var: ScalarVariable, cmap: list, extents: list):
        """Update colormap and assign new PV to track for color intensity. The plots will use 
        extents passed to evaluate the PV value along a continuum and assign a color.
        
        """
        self._color_map = cmap
        self._extents = np.array(range(extents[0], extents[1], len(self._color_map)))
        self._color_monitor = PVScalar(color_var, self._controller)

    def _collect_reference(self):
        self._collecting_reference = True
        self.reference_button.label = "Collecting"
        self.reference_button.disabled = True
        self._active_reference_timestamp = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")

    def _reset_reference(self):
        self._active_reference = {"X": {device: 0 for device in self._devices}, "Y": {device: 0 for device in self._devices}}
        self._active_reference_timestamp = None

    def _save_reference(self):
        self._reference_registry[self._active_beamline][self._active_reference_timestamp] = self._active_reference
        self.compare_reference_dropdown.menu += [(self._active_reference_timestamp, self._active_reference_timestamp)]
        self._active_reference_timestamp = None

    def _set_reference(self, event):
        self._active_reference = self._reference_registry[self._active_beamline][event.item]

    def toggle_beamline(self, beamline):
        self._active_beamline = beamline

        if beamline == "sxr":
            self.update_table(self._sxr_table)
            self.update_colormap(self._sxr_shading_var, SXR_COLORS, extents = [0,5])
            self.hxr_color_bar.visible=False
            self.sxr_color_bar.visible=True

        elif beamline == "hxr":
            self.update_table(self._hxr_table)
            self.update_colormap(self._hxr_shading_var, HXR_COLORS, extents = [0,5])
            self.hxr_color_bar.visible=True
            self.sxr_color_bar.visible=False

        self.compare_reference_dropdown.menu = [registered for registered in self._reference_registry[beamline]]

        # reset
        self._active_reference_timestamp = None

        for device in self._reference_measurements["X"]:
            self._reference_measurements["X"][device] = []
        
        for device in self._reference_measurements["Y"]:
            self._reference_measurements["Y"][device] = []

        self.reference_button.label = "Collect reference"
        self.reference_button.disabled = False
        self._reference_count = 0

        self._reference_count = self._reference_n


