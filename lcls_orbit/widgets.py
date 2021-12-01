from typing import List, Dict
import logging
import numpy as np

from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, Span


from lume_model.variables import TableVariable, ScalarVariable
from lume_epics.client.controller import (
    Controller
)
from lume_epics.client.monitors import PVTable, PVScalar
from bokeh.models import HoverTool


logger = logging.getLogger(__name__)


class OrbitDisplay:
    """Object holding orbit display widgets.

    """

    def __init__(
        self,
        table: TableVariable,
        controller: Controller,
        longitudinal_labels: Dict[float, str] = None,
        height: int = 400,
        width: int = 600,
        bar_width: int = None,
        color_var: ScalarVariable = None,
        color_map: list = None,
        extents: list = None,
    ):

        self.z = []

        # cagetmany
        for row, value in table.table_data["Z"].items():
            self.z.append(value)

        self._monitor = PVTable(table, controller)
        self._controller = controller
        if color_var is not None:
            # TODO check all exist
            self._color_monitor = PVScalar(color_var, controller)
            self._extents = np.array(extents)
            self._color_map = color_map

        if not bar_width:
            self._bar_width = (max(self.z) - min(self.z)) / (len(self.z) + 1)
        else:
            self._bar_width = bar_width

        self.x_source = ColumnDataSource(dict(x=[], y=[], device=[], color=[]))
        self.y_source = ColumnDataSource(dict(x=[], y=[], device=[], color=[]))

        TOOLTIPS_x = [
            ("device", "@device"),
            ("value", "@y"),
            ("location", "@x{0.0}")
        ]
        
        x_hover = HoverTool(tooltips=TOOLTIPS_x)

        # setup x plot
        self.x_plot = figure(
            y_range=(-1, 1),
            x_range=(min(self.z) - self._bar_width / 2.0, max(self.z) + self._bar_width / 2.0),
            width=width,
            height=height,
            toolbar_location="right",
            title="X (mm)",
        )
        self.x_plot.vbar(x="x", bottom=0, top="y", width=self._bar_width, source=self.x_source,  color="color")
        self.x_plot.add_tools(x_hover)
        self.x_plot.xgrid.grid_line_color = None
        self.x_plot.ygrid.grid_line_color = None

        if longitudinal_labels:
            self.x_plot.xaxis.ticker = list(longitudinal_labels.keys())
            self.x_plot.xaxis.major_label_overrides = longitudinal_labels

        self.x_plot.ygrid.grid_line_color = None
        self.x_plot.xaxis.axis_label = "z (m)"
        self.x_plot.outline_line_color = None

        TOOLTIPS_y = [
            ("device", "@device"),
            ("value", "@y"),
            ("location", "@x")
        ]

        y_hover = HoverTool(tooltips=TOOLTIPS_y)

        # setup y plot
        self.y_plot = figure(
            y_range=(-1, 1),
            x_range=self.x_plot.x_range,
            width=width,
            height=height,
            toolbar_location="right",
            title="Y (mm)",
        )
        self.y_plot.vbar(x="x", bottom=0, top="y", width=self._bar_width, source=self.y_source, color="color")
        self.y_plot.add_tools(y_hover)
        self.y_plot.xgrid.grid_line_color = None
        self.y_plot.ygrid.grid_line_color = None

        if longitudinal_labels:
            self.y_plot.xaxis.ticker = list(longitudinal_labels.keys())
            self.y_plot.xaxis.major_label_overrides = longitudinal_labels

        self.y_plot.ygrid.grid_line_color = None
        self.y_plot.xaxis.axis_label = "z (m)"
        self.y_plot.outline_line_color = None

    def update_table(self, table) -> None:
        self._monitor = PVTable(table, self._controller)

        self.z = []

        # cagetmany
        for row, value in table.table_data["Z"].items():
            self.z.append(value)


    def update(self) -> None:
        """
        Callback which updates the plot to reflect updated process variable values or
        new process variable.

        """
        vals = self._monitor.poll()
        if self._color_monitor is not None:
            color_val = self._color_monitor.poll()
            idx = (np.abs(self._extents - color_val)).argmin()
            color = [self._color_map[idx] for device in vals["X"]]

        else:
            color = ["#212494" for device in vals["X"] ]

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

        self.x_source.data.update({"x": self.z, "y": x, "device": devices, "color": color})
        self.y_source.data.update({"x": self.z, "y": y, "device": devices, "color": color})

    def update_colormap(self, color_var, cmap, extents):
        self._color_map = cmap
        self._extents = np.array(range(extents[0], extents[1], len(self._color_map)))
        self._color_monitor = PVScalar(color_var, self._controller)


