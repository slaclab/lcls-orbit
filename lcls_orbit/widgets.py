from typing import List, Dict
import logging
import numpy as np

from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, ColorMapper, Button, Span


from lume_model.variables import Variable, ScalarVariable, TableVariable
from lume_epics.client.controller import (
    Controller,
    DEFAULT_IMAGE_DATA,
    DEFAULT_SCALAR_VALUE,
)
from lume_epics.client.monitors import PVTable

logger = logging.getLogger(__name__)


class OrbitDisplay:

    """
    Todo:
    labels for z axis +
    toolkits for zooming etc.
    document
    dynamic width for markers
    scaling?

    """

    def __init__(
        self,
        table: TableVariable,
        controller: Controller,
        longitudinal_labels: Dict[float, str] = None,
        height: int = 400,
        width: int = 600,
        bar_width = None,
    ):

        self.z = []
        # cagetmany
        for row, value in table.table_data["Z"].items():
            self.z.append(value)

        self._monitor = PVTable(table, controller)

        if not bar_width:
            self._bar_width = (max(self.z) - min(self.z)) / len(self.z)
        else:
            self._bar_width = bar_width


        self.x_source = ColumnDataSource(dict(x=[], y=[]))
        self.y_source = ColumnDataSource(dict(x=[], y=[]))

        # setup x plot
        self.x_plot = figure(
            y_range=(-1, 1),
            x_range=(min(self.z) - self._bar_width / 2.0, max(self.z) + self._bar_width / 2.0),
            width=width,
            height=height,
            toolbar_location="right",
            title="X",
        )
        self.x_plot.vbar(x="x", bottom=0, top="y", width=self._bar_width, source=self.x_source)

        self.x_plot.xgrid.grid_line_color = None
        self.x_plot.ygrid.grid_line_color = None

        

        if longitudinal_labels:
            self.x_plot.xaxis.ticker = list(longitudinal_labels.keys())
            self.x_plot.xaxis.major_label_overrides = longitudinal_labels

        self.x_plot.ygrid.grid_line_color = None
        self.x_plot.xaxis.axis_label = "z"
        self.x_plot.outline_line_color = None


        # setup y plot
        self.y_plot = figure(
            y_range=(-1, 1),
            x_range=(min(self.z) - self._bar_width / 2.0, max(self.z) + self._bar_width / 2.0),
            width=width,
            height=height,
            toolbar_location="right",
            title="Y",
        )
        self.y_plot.vbar(x="x", bottom=0, top="y", width=self._bar_width, source=self.x_source)

        self.y_plot.xgrid.grid_line_color = None
        self.y_plot.ygrid.grid_line_color = None

        if longitudinal_labels:
            self.y_plot.xaxis.ticker = list(longitudinal_labels.keys())
            self.y_plot.xaxis.major_label_overrides = longitudinal_labels

        self.y_plot.ygrid.grid_line_color = None
        self.y_plot.xaxis.axis_label = "z"
        self.y_plot.outline_line_color = None


    def update(self) -> None:
        """
        Callback which updates the plot to reflect updated process variable values or
        new process variable.

        Args:
            live_variable (str): Variable to display
        """
        vals = self._monitor.poll()


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

        self.x_source.data.update({"x": self.z, "y": x})
        self.y_source.data.update({"x": self.z, "y": y})
