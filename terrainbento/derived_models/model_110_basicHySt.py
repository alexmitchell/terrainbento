# -*- coding: utf-8 -*-
"""
model_110_basicHySt.py: erosion model with stochastic
rainfall and hybrid alluvial incision.

Model 110 BasicHySt

The hydrology aspect models discharge and erosion across a topographic
surface assuming (1) stochastic Poisson storm arrivals, (2) single-direction
flow routing, and (3) Hortonian infiltration model. Includes stream-power
erosion plus linear diffusion.

The hydrology uses calculation of drainage area using the standard "D8"
approach (assuming the input grid is a raster; "DN" if not), then modifies it
by running a lake-filling component. It then iterates through a sequence of
storm and interstorm periods. Storm depth is drawn at random from a gamma
distribution, and storm duration from an exponential distribution; storm
intensity is then depth divided by duration. Given a storm precipitation
intensity $P$, the runoff production rate $R$ [L/T] is calculated using:

$R = P - I (1 - \exp ( -P / I ))$

where $I$ is the soil infiltration capacity. At the sub-grid scale, soil
infiltration capacity is assumed to have an exponential distribution of which
$I$ is the mean. Hence, there are always some spots within any given grid cell
that will generate runoff. This approach yields a smooth transition from
near-zero runoff (when $I>>P$) to $R \approx P$ (when $P>>I$), without a
"hard threshold."

Landlab components used: FlowRouter, DepressionFinderAndRouter,
PrecipitationDistribution, LinearDiffuser, HybridAlluvium

"""

import sys
import numpy as np

from landlab.components import LinearDiffuser, ErosionDeposition
from terrainbento.base_class import StochasticErosionModel


class BasicHySt(StochasticErosionModel):
    """
    A BasicHySt computes erosion using (1) hybrid alluvium river erosion,
    (2) linear nhillslope diffusion, and
    (3) generation of a random sequence of runoff events across a topographic
    surface.

    Examples
    --------
    >>> from terrainbento import BasicHySt
    >>> my_pars = {}
    >>> my_pars['dt'] = 1.0
    >>> my_pars['run_duration'] = 1.0
    >>> my_pars['output_interval'] = 2.0
    >>> my_pars['infiltration_capacity'] = 1.0
    >>> my_pars['K_stochastic_sp'] = 1.0
    >>> my_pars['m_sp'] = 0.5
    >>> my_pars['n_sp'] = 1.0
    >>> my_pars['erosion__threshold'] = 1.0
    >>> my_pars['linear_diffusivity'] = 0.01
    >>> my_pars['mean_storm__intensity'] = 0.002
    >>> my_pars['intermittency_factor'] = 0.008
    >>> my_pars['mean_storm_depth'] = 0.025
    >>> my_pars['random_seed'] = 907
    >>> my_pars['precip_shape_factor'] = 0.65
    >>> my_pars['number_of_sub_time_steps'] = 10
    >>> my_pars['v_s'] = 0.01
    >>> my_pars['F_f'] = 0.1
    >>> my_pars['phi'] = 0.3
    >>> my_pars['solver'] = 'adaptive'
    >>> srt = BasicHySt(params=my_pars)
    """

    def __init__(self, input_file=None, params=None, BoundaryHandlers=None, OutputWriters=None):
        """Initialize the BasicHySt."""

        # Call ErosionModel's init
        super(BasicHySt, self).__init__(input_file=input_file,
                                        params=params,
                                        BoundaryHandlers=BoundaryHandlers,
                                        OutputWriters=OutputWriters)

        # Get Parameters:
        K = ((self._length_factor ** 0.5)  # K_stochastic [=] L^(1/2)  T^-(1/2)
             * self.get_parameter_from_exponent('K_stochastic_sp'))

        linear_diffusivity = ((self._length_factor ** 2)
                              * self.get_parameter_from_exponent(
                                      'linear_diffusivity')) # L^2/T

        v_s = (self._length_factor)*self.get_parameter_from_exponent('v_s') # has units length per time

        #set methods and fields.
        method = 'simple_stream_power'
        discharge_method = 'discharge_field'
        area_field = None
        discharge_field = 'surface_water__discharge'

        # instantiate rain generator
        self.instantiate_rain_generator()

        # Add a field for discharge
        if 'surface_water__discharge' not in self.grid.at_node:
            self.grid.add_zeros('node', 'surface_water__discharge')
        self.discharge = self.grid.at_node['surface_water__discharge']

        # Get the infiltration-capacity parameter
        infiltration_capacity = (self._length_factor
                                 * self.params['infiltration_capacity']) # L/T
        self.infilt = infiltration_capacity

        # Run flow routing and lake filler
        self.flow_router.run_one_step()

        # Keep a reference to drainage area
        self.area = self.grid.at_node['drainage_area']

        # Handle solver option
        try:
            solver = self.params['solver']
        except:
            solver = 'original'

        # Instantiate an ErosionDeposition component
        self.eroder = ErosionDeposition(self.grid,
                            K=K,
                            F_f=self.params['F_f'],
                            phi=self.params['phi'],
                            v_s=v_s,
                            m_sp=self.params['m_sp'],
                            n_sp=self.params['n_sp'],
                            method=method,
                            discharge_method=discharge_method,
                            area_field=area_field,
                            discharge_field=discharge_field,
                            solver=solver)

        # Instantiate a LinearDiffuser component
        self.diffuser = LinearDiffuser(self.grid,
                                       linear_diffusivity = linear_diffusivity)

    def calc_runoff_and_discharge(self):
        """Calculate runoff rate and discharge; return runoff."""
        if self.rain_rate > 0.0 and self.infilt > 0.0:
            runoff = self.rain_rate - (self.infilt *
                                       (1.0 -
                                        np.exp(-self.rain_rate / self.infilt)))
            if runoff < 0:
                runoff = 0
        else:
            runoff = self.rain_rate
        self.discharge[:] = runoff * self.area
        return runoff

    def run_one_step(self, dt):
        """
        Advance model for one time-step of duration dt.
        """
        # Route flow
        self.flow_router.run_one_step()

        # Get IDs of flooded nodes, if any
        flooded = np.where(self.flow_router.depression_finder.flood_status==3)[0]

        # Handle water erosion
        self.handle_water_erosion(dt, flooded)

        # Do some soil creep
        self.diffuser.run_one_step(dt)

        # Finalize the run_one_step_method
        self.finalize__run_one_step(dt)


def main():
    """Executes model."""
    import sys

    try:
        infile = sys.argv[1]
    except IndexError:
        print('Must include input file name on command line')
        sys.exit(1)

    em = BasicHySt(input_file=infile)
    em.run()


if __name__ == '__main__':
    main()
