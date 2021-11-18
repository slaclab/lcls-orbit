from typing import List, Dict
import logging
import numpy as np

from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, ColorMapper, Button, Span


from lume_model.variables import Variable, ScalarVariable
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
        variables: List[Variable],
        controller: Controller,
        positions: dict,
        longitudinal_labels: Dict[float, str] = None,
        height: int = 400,
        width: int = 600,
        bar_width = None,
    ):

        # cagetmany
        self.z = []
        self._monitor = PVTable(list(variables.values()), controller)


        self._pv_monitors = {}

        for variable in variables:
            position = positions.get(variable)
            if position is not None:
                self.z.append(position)
            else:
                logger.error(
                    "Unable to use %s in LongitudinalPlot. z value is missing.",
                    variable.name,
                )

        if not bar_width:
            self._bar_width = (max(self.z) - min(self.z)) / len(positions)
        else:
            self._bar_width = bar_width


        self.source = ColumnDataSource(dict(x=[], y=[]))

        self.plot = figure(
            y_range=(-1, 1),
            x_range=(min(self.z) - self._bar_width / 2.0, max(self.z) + self._bar_width / 2.0),
            width=width,
            height=height,
            toolbar_location="right",
            title="X",
        )
        self.plot.vbar(x="x", bottom=0, top="y", width=self._bar_width, source=self.source)

        self.plot.xgrid.grid_line_color = None
        self.plot.ygrid.grid_line_color = None

        if longitudinal_labels:
            self.plot.xaxis.ticker = list(longitudinal_labels.keys())
            self.plot.xaxis.major_label_overrides = longitudinal_labels

        self.plot.ygrid.grid_line_color = None
        self.plot.xaxis.axis_label = "z"
        self.plot.outline_line_color = None

    def update(self) -> None:
        """
        Callback which updates the plot to reflect updated process variable values or
        new process variable.

        Args:
            live_variable (str): Variable to display
        """
        vals = list(self._monitor.poll().values())
        y = np.array(vals, dtype=np.float64)

        # add hline if 0 inside
        if min(y) < 0 < max(y):
            hline = Span(
                location=0, dimension="width", line_color="black", line_width=2
            )
            self.plot.add_layout(hline)

        self.source.data.update({"x": self.z, "y": y})
