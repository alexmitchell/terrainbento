# coding: utf8
# !/usr/env/python
"""terrainbento model **BasicDdVs** program.

Erosion model program using linear diffusion, stream power with a smoothed
threshold that varies with incision depth, and discharge proportional to
effective drainage area.

Landlab components used:
    1. `FlowAccumulator <http://landlab.readthedocs.io/en/release/landlab.components.flow_accum.html>`_
    2. `DepressionFinderAndRouter <http://landlab.readthedocs.io/en/release/landlab.components.flow_routing.html#module-landlab.components.flow_routing.lake_mapper>`_ (optional)
    3. `StreamPowerSmoothThresholdEroder <http://landlab.readthedocs.io/en/release/landlab.components.stream_power.html>`_
    4. `LinearDiffuser <http://landlab.readthedocs.io/en/release/landlab.components.diffusion.html>`_
"""

import numpy as np

from landlab.components import LinearDiffuser, StreamPowerSmoothThresholdEroder
from terrainbento.base_class import ErosionModel

_REQUIRED_FIELDS = ["topographic__elevation"]


class BasicDdVs(ErosionModel):
    """**BasicDdVs** model program.

    **BasicDdVs** is a model program that evolves a topographic surface described
    by :math:`\eta` with the following governing equations:


    .. math::

        \\frac{\partial \eta}{\partial t} = -\left(KA_{eff}^{m}S^{n} - \omega_{ct}\left(1-e^{-KA_{eff}^{m}S^{n}/\omega_{ct}}\\right)\\right) + D\\nabla^2 \eta

        A_{eff} = A \exp \left( -\\frac{-\\alpha S}{A}\\right)

        \\alpha = \\frac{K_{sat}  H_{init}  dx}{R_m}


    where :math:`A` is the local drainage area, :math:`S` is the local slope,
    :math:`m` and :math:`n` are the drainage area and slope exponent parameters,
    :math:`K` is the erodability by water, :math:`D` is the regolith transport
    parameter, and :math:`\omega_{ct}` is the critical stream power needed for
    erosion to occur. :math:`\omega_{ct}` changes through time as it increases
    with cumulative incision depth:

    .. math::

        \omega_{ct}\left(x,y,t\\right) = \mathrm{max}\left(\omega_c +  b D_I\left(x, y, t\\right), \omega_c \\right)

    where :math:`\omega_c` is the threshold when no incision has taken place,
    :math:`b` is the rate at which the threshold increases with incision depth,
    and :math:`D_I` is the cumulative incision depth at location
    :math:`\left(x,y\\right)` and time :math:`t`.

    :math:`\\alpha` is the saturation area scale used for transforming area into
    effective area. It is given as a function of the saturated hydraulic
    conductivity :math:`K_{sat}`, the soil thickness :math:`H_{init}`,
    the grid spacing :math:`dx`, and the recharge rate, :math:`R_m`.

    The **BasicDdVs** program inherits from the terrainbento **ErosionModel** base
    class. In addition to the parameters required by the base class, models
    built with this program require the following parameters.

    +--------------------+-------------------------------------------------+
    | Parameter Symbol   | Input File Name                                 |
    +====================+=================================================+
    |:math:`m`           | ``m_sp``                                        |
    +--------------------+-------------------------------------------------+
    |:math:`n`           | ``n_sp``                                        |
    +--------------------+-------------------------------------------------+
    |:math:`K`           | ``water_erodability``                           |
    +--------------------+-------------------------------------------------+
    |:math:`\omega_{c}`  | ``water_erosion_rule__threshold``               |
    +--------------------+-------------------------------------------------+
    |:math:`b`           | ``water_erosion_rule__thresh_depth_derivative`` |
    +--------------------+-------------------------------------------------+
    |:math:`D`           | ``regolith_transport_parameter``                |
    +--------------------+-------------------------------------------------+
    |:math:`K_{sat}`     | ``hydraulic_conductivity``                      |
    +--------------------+-------------------------------------------------+
    |:math:`H_{init}`    | ``soil__initial_thickness``                     |
    +--------------------+-------------------------------------------------+
    |:math:`R_m`         | ``recharge_rate``                               |
    +--------------------+-------------------------------------------------+

    Refer to the terrainbento manuscript Table 5 (URL to manuscript when
    published) for full list of parameter symbols, names, and dimensions.

    """

    def __init__(
        self,
        clock,
        grid,
        m_sp=0.5,
        n_sp=1.0,
        water_erodability=0.0001,
        regolith_transport_parameter=0.1,
        **kwargs
    ):
        """
        Parameters
        ----------


        Returns
        -------
        BasicRtDdVs : model object

        Examples
        --------
        This is a minimal example to demonstrate how to construct an instance
        of model **BasicVs**. For more detailed examples, including steady-state
        test examples, see the terrainbento tutorials.

        To begin, import the model class.

        >>> from landlab import RasterModelGrid
        >>> from landlab.values import random
        >>> from terrainbento import Clock, Basic
        >>> clock = Clock(start=0, stop=100, step=1)
        >>> grid = RasterModelGrid((5,5))
        >>> _ = random(grid, "topographic__elevation")

        Construct the model.

        >>> model = Basic(clock, grid)

        Running the model with ``model.run()`` would create output, so here we
        will just run it one step.

        >>> model.run_one_step(1.)
        >>> model.model_time
        1.0

        >>> params = {"model_grid": "RasterModelGrid",
        ...           "clock": {"step": 1,
        ...                     "output_interval": 2.,
        ...                     "stop": 200.},
        ...           "number_of_node_rows" : 6,
        ...           "number_of_node_columns" : 9,
        ...           "node_spacing" : 10.0,
        ...           "regolith_transport_parameter": 0.001,
        ...           "water_erodability": 0.001,
        ...           "water_erosion_rule__threshold": 0.5,
        ...           "water_erosion_rule__thresh_depth_derivative": 0.001,
        ...           "m_sp": 0.5,
        ...           "n_sp": 1.0,
        ...           "recharge_rate": 0.5,
        ...           "soil__initial_thickness": 2.0,
        ...           "hydraulic_conductivity": 0.1}

        Construct the model.

        >>> model = BasicDdVs(params=params)

        Running the model with ``model.run()`` would create output, so here we
        will just run it one step.

        >>> model.run_one_step(1.)
        >>> model.model_time
        1.0

        """
        # Call ErosionModel"s init
        super(BasicDdVs, self).__init__(clock, grid, **kwargs)

        if float(self.params["n_sp"]) != 1.0:
            raise ValueError("Model BasicDdVs only supports n = 1.")

        self.m = self.params["m_sp"]
        self.n = self.params["n_sp"]
        self.K = self._get_parameter_from_exponent("water_erodability") * (
            self._length_factor ** (1. - (2. * self.m))
        )

        regolith_transport_parameter = (
            self._length_factor ** 2.
        ) * self._get_parameter_from_exponent(
            "regolith_transport_parameter"
        )  # has units length^2/time

        recharge_rate = (self._length_factor) * self.params[
            "recharge_rate"
        ]  # has units length per time
        soil_thickness = (self._length_factor) * self.params[
            "soil__initial_thickness"
        ]  # has units length
        K_hydraulic_conductivity = (self._length_factor) * self.params[
            "hydraulic_conductivity"
        ]  # has units length per time

        self.threshold_value = (
            self._length_factor
            * self._get_parameter_from_exponent(
                "water_erosion_rule__threshold"
            )
        )  # has units length/time

        # Add a field for effective drainage area
        self.eff_area = self.grid.add_zeros("node", "effective_drainage_area")

        # Get the effective-area parameter
        self.sat_param = (
            K_hydraulic_conductivity * soil_thickness * self.grid.dx
        ) / (recharge_rate)

        # Create a field for the (initial) erosion threshold
        self.threshold = self.grid.add_zeros(
            "node", "water_erosion_rule__threshold"
        )
        self.threshold[:] = self.threshold_value

        # Instantiate a FastscapeEroder component
        self.eroder = StreamPowerSmoothThresholdEroder(
            self.grid,
            use_Q="surface_water__discharge",
            K_sp=self.K,
            m_sp=self.m,
            n_sp=self.n,
            threshold_sp=self.threshold,
        )

        # Get the parameter for rate of threshold increase with erosion depth
        self.thresh_change_per_depth = self.params[
            "water_erosion_rule__thresh_depth_derivative"
        ]

        # Instantiate a LinearDiffuser component
        self.diffuser = LinearDiffuser(
            self.grid, linear_diffusivity=regolith_transport_parameter
        )

    def _calc_effective_drainage_area(self):
        """Calculate and store effective drainage area."""

        area = self.grid.at_node["drainage_area"]
        slope = self.grid.at_node["topographic__steepest_slope"]
        cores = self.grid.core_nodes
        self.eff_area[cores] = area[cores] * (
            np.exp(-self.sat_param * slope[cores] / area[cores])
        )

    def run_one_step(self, step):
        """Advance model **BasicVs** for one time-step of duration step.

        The **run_one_step** method does the following:

        1. Directs flow, accumulates drainage area, and calculates effective
           drainage area.

        2. Assesses the location, if any, of flooded nodes where erosion should
           not occur.

        3. Assesses if a **PrecipChanger** is an active BoundaryHandler and if
           so, uses it to modify the two erodability by water values.

        4. Calculates detachment-limited erosion by water.

        5. Calculates topographic change by linear diffusion.

        6. Finalizes the step using the **ErosionModel** base class function
           **finalize__run_one_step**. This function updates all BoundaryHandlers
           by ``step`` and increments model time by ``step``.

        Parameters
        ----------
        step : float
            Increment of time for which the model is run.
        """
        # create and move water
        self.create_and_move_water(step)

        # Update effective runoff ratio
        self._calc_effective_drainage_area()

        # Get IDs of flooded nodes, if any
        if self.flow_accumulator.depression_finder is None:
            flooded = []
        else:
            flooded = np.where(
                self.flow_accumulator.depression_finder.flood_status == 3
            )[0]

        # Zero out effective area in flooded nodes
        self.eff_area[flooded] = 0.0

        # Set the erosion threshold.
        #
        # Note that a minus sign is used because cum ero depth is negative for
        # erosion, positive for deposition.
        # The second line handles the case where there is growth, in which case
        # we want the threshold to stay at its initial value rather than
        # getting smaller.
        cum_ero = self.grid.at_node["cumulative_elevation_change"]
        cum_ero[:] = (
            self.z - self.grid.at_node["initial_topographic__elevation"]
        )
        self.threshold[:] = self.threshold_value - (
            self.thresh_change_per_depth * cum_ero
        )
        self.threshold[
            self.threshold < self.threshold_value
        ] = self.threshold_value

        # Do some erosion (but not on the flooded nodes)
        # (if we're varying K through time, update that first)
        if "PrecipChanger" in self.boundary_handlers:
            self.eroder.K = (
                self.K
                * self.boundary_handlers[
                    "PrecipChanger"
                ].get_erodability_adjustment_factor()
            )
        self.eroder.run_one_step(step)

        # Do some soil creep
        self.diffuser.run_one_step(step)

        # Finalize the run_one_step_method
        self.finalize__run_one_step(step)


def main():  # pragma: no cover
    """Executes model."""
    import sys

    try:
        infile = sys.argv[1]
    except IndexError:
        print("Must include input file name on command line")
        sys.exit(1)

    my_model = BasicDdVs(input_file=infile)
    my_model.run()


if __name__ == "__main__":
    main()
