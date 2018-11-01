# coding: utf8
#! /usr/env/python

import numpy as np

from numpy.testing import assert_array_almost_equal  # assert_array_equal,
import pytest

from terrainbento import BasicThVs
from terrainbento.utilities import precip_defaults, precip_testing_factor


def test_Aeff():
    U = 0.0001
    K = 0.001
    m = 0.5
    n = 1.0
    dt = 1000
    threshold = 0.01
    hydraulic_conductivity = 0.1
    soil__initial_thickness = 0.1
    node_spacing = 100.0
    recharge_rate = 0.5
    # construct dictionary. note that D is turned off here
    params = {
        "model_grid": "RasterModelGrid",
        "clock": {"dt": 1, "output_interval": 2., "run_duration": 200.},
        "number_of_node_rows": 3,
        "number_of_node_columns": 20,
        "node_spacing": 100.0,
        "north_boundary_closed": True,
        "south_boundary_closed": True,
        "regolith_transport_parameter": 0.,
        "water_erodability": K,
        "hydraulic_conductivity": 0.1,
        "soil__initial_thickness": 0.1,
        "recharge_rate": 0.5,
        "m_sp": m,
        "n_sp": n,
        "water_erosion_rule__threshold": threshold,
        "random_seed": 3141,
        "BoundaryHandlers": "NotCoreNodeBaselevelHandler",
        "NotCoreNodeBaselevelHandler": {"modify_core_nodes": True, "lowering_rate": -U},
    }

    model = BasicThVs(params=params)
    for _ in range(200):
        model.run_one_step(dt)

    # construct actual and predicted slopes
    actual_slopes = model.grid.at_node["topographic__steepest_slope"]
    actual_areas = model.grid.at_node["drainage_area"]

    alpha = (
        hydraulic_conductivity * soil__initial_thickness * node_spacing / recharge_rate
    )
    A_eff_predicted = actual_areas * np.exp(-(-alpha * actual_slopes) / actual_areas)

    # assert aeff internally calculated correclty
    assert_array_almost_equal(
        model.eff_area[model.grid.core_nodes],
        A_eff_predicted[model.grid.core_nodes],
        decimal=1,
    )

    # somewhat circular test to make sure slopes are below predicted upper bound
    predicted_slopes_eff_upper = ((U + threshold) / (K * (model.eff_area ** m))) ** (
        1. / n
    )
    predicted_slopes_eff_lower = ((U + 0.0) / (K * (model.eff_area ** m))) ** (1. / n)

    # somewhat circular test to make sure VSA slopes are higher than expected "normal" slopes
    predicted_slopes_normal_upper = ((U + threshold) / (K * (actual_areas ** m))) ** (
        1. / n
    )
    predicted_slopes_normal_lower = ((U + 0.0) / (K * (actual_areas ** m))) ** (1. / n)

    assert (
        np.all(
            actual_slopes[model.grid.core_nodes[1:-1]]
            < predicted_slopes_eff_upper[model.grid.core_nodes[1:-1]]
        )
        == True
    )
    assert (
        np.all(
            predicted_slopes_eff_upper[model.grid.core_nodes[1:-1]]
            > predicted_slopes_normal_upper[model.grid.core_nodes[1:-1]]
        )
        == True
    )
    assert (
        np.all(
            actual_slopes[model.grid.core_nodes[1:-1]]
            > predicted_slopes_eff_lower[model.grid.core_nodes[1:-1]]
        )
        == True
    )
    assert (
        np.all(
            predicted_slopes_eff_lower[model.grid.core_nodes[1:-1]]
            > predicted_slopes_normal_lower[model.grid.core_nodes[1:-1]]
        )
        == True
    )


def test_bad_n_sp():
    params = {
        "model_grid": "RasterModelGrid",
        "clock": {"dt": 1, "output_interval": 2., "run_duration": 200.},
        "water_erosion_rule__threshold": 0.001,
        "water_erodability": 0.001,
        "n_sp": 1.01,
        "regolith_transport_parameter": 0.001,
    }

    with pytest.raises(ValueError):
        BasicThVs(params=params)


def test_diffusion_only():
    U = 0.001
    K = 0.0
    m = 1. / 3.
    n = 1.0
    dt = 1000
    total_time = 5.0e6
    D = 1.0
    params = {
        "model_grid": "RasterModelGrid",
        "clock": {"dt": 1, "output_interval": 2., "run_duration": 200.},
        "number_of_node_rows": 3,
        "number_of_node_columns": 21,
        "node_spacing": 100.0,
        "north_boundary_closed": True,
        "west_boundary_closed": False,
        "south_boundary_closed": True,
        "regolith_transport_parameter": D,
        "water_erodability": K,
        "water_erosion_rule__threshold": 0.5,
        "m_sp": m,
        "n_sp": n,
        "hydraulic_conductivity": 0.5,
        "soil__initial_thickness": 0.1,
        "recharge_rate": 0.5,
        "random_seed": 3141,
        "depression_finder": "DepressionFinderAndRouter",
        "BoundaryHandlers": "NotCoreNodeBaselevelHandler",
        "NotCoreNodeBaselevelHandler": {"modify_core_nodes": True, "lowering_rate": -U},
    }

    nts = int(total_time / dt)

    reference_node = 9
    # construct and run model
    model = BasicThVs(params=params)
    for _ in range(nts):
        model.run_one_step(dt)

    predicted_z = model.z[model.grid.core_nodes[reference_node]] - (U / (2. * D)) * (
        (
            model.grid.x_of_node
            - model.grid.x_of_node[model.grid.core_nodes[reference_node]]
        )
        ** 2
    )

    # assert actual and predicted elevations are the same.
    assert_array_almost_equal(
        predicted_z[model.grid.core_nodes], model.z[model.grid.core_nodes], decimal=2
    )


def test_steady_Ksp_no_precip_changer():
    U = 0.0001
    K = 0.001
    m = 0.5
    n = 1.0
    dt = 1000
    threshold = 0.01
    # construct dictionary. note that D is turned off here
    params = {
        "model_grid": "RasterModelGrid",
        "clock": {"dt": 1, "output_interval": 2., "run_duration": 200.},
        "number_of_node_rows": 3,
        "number_of_node_columns": 20,
        "node_spacing": 100.0,
        "north_boundary_closed": True,
        "south_boundary_closed": True,
        "regolith_transport_parameter": 0.,
        "water_erodability": K,
        "hydraulic_conductivity": 0.0,
        "soil__initial_thickness": 0.1,
        "recharge_rate": 0.5,
        "m_sp": m,
        "n_sp": n,
        "water_erosion_rule__threshold": threshold,
        "random_seed": 3141,
        "BoundaryHandlers": "NotCoreNodeBaselevelHandler",
        "NotCoreNodeBaselevelHandler": {"modify_core_nodes": True, "lowering_rate": -U},
    }

    # construct and run model
    model = BasicThVs(params=params)
    for _ in range(100):
        model.run_one_step(dt)

    # construct actual and predicted slopes
    # note that since we have a smooth threshold, we do not have a true
    # analytical solution, but a bracket within wich we expect the actual slopes
    # to fall.
    actual_slopes = model.grid.at_node["topographic__steepest_slope"]
    actual_areas = model.grid.at_node["drainage_area"]
    predicted_slopes_upper = ((U + threshold) / (K * (actual_areas ** m))) ** (1. / n)
    predicted_slopes_lower = ((U + 0.0) / (K * (actual_areas ** m))) ** (1. / n)

    # assert actual and predicted slopes are in the correct range for the slopes.
    assert (
        np.all(
            actual_slopes[model.grid.core_nodes[1:-1]]
            > predicted_slopes_lower[model.grid.core_nodes[1:-1]]
        )
        == True
    )
    assert (
        np.all(
            actual_slopes[model.grid.core_nodes[1:-1]]
            < predicted_slopes_upper[model.grid.core_nodes[1:-1]]
        )
        == True
    )


def test_steady_Ksp_no_precip_changer_with_depression_finding():
    U = 0.0001
    K = 0.001
    m = 0.5
    n = 1.0
    dt = 1000
    threshold = 0.000001
    # construct dictionary. note that D is turned off here
    params = {
        "model_grid": "RasterModelGrid",
        "clock": {"dt": 1, "output_interval": 2., "run_duration": 200.},
        "number_of_node_rows": 3,
        "number_of_node_columns": 20,
        "node_spacing": 100.0,
        "north_boundary_closed": True,
        "south_boundary_closed": True,
        "regolith_transport_parameter": 0.,
        "water_erodability": K,
        "hydraulic_conductivity": 0.0,
        "soil__initial_thickness": 0.1,
        "recharge_rate": 0.5,
        "m_sp": m,
        "n_sp": n,
        "water_erosion_rule__threshold": threshold,
        "random_seed": 3141,
        "depression_finder": "DepressionFinderAndRouter",
        "BoundaryHandlers": "NotCoreNodeBaselevelHandler",
        "NotCoreNodeBaselevelHandler": {"modify_core_nodes": True, "lowering_rate": -U},
    }

    # construct and run model
    model = BasicThVs(params=params)
    for _ in range(100):
        model.run_one_step(dt)

    # construct actual and predicted slopes
    actual_slopes = model.grid.at_node["topographic__steepest_slope"]
    actual_areas = model.grid.at_node["drainage_area"]
    predicted_slopes = ((U / K + threshold) / ((actual_areas ** m))) ** (1. / n)

    # assert actual and predicted slopes are the same.
    assert_array_almost_equal(
        actual_slopes[model.grid.core_nodes[1:-1]],
        predicted_slopes[model.grid.core_nodes[1:-1]],
        decimal=4,
    )


def test_with_precip_changer():
    K = 0.01
    threshold = 0.000001
    params = {
        "model_grid": "RasterModelGrid",
        "clock": {"dt": 1, "output_interval": 2., "run_duration": 200.},
        "number_of_node_rows": 3,
        "number_of_node_columns": 20,
        "node_spacing": 100.0,
        "north_boundary_closed": True,
        "south_boundary_closed": True,
        "regolith_transport_parameter": 0.,
        "water_erodability": K,
        "hydraulic_conductivity": 0.0,
        "soil__initial_thickness": 0.1,
        "recharge_rate": 0.5,
        "m_sp": 0.5,
        "n_sp": 1.0,
        "water_erosion_rule__threshold": threshold,
        "random_seed": 3141,
        "BoundaryHandlers": "PrecipChanger",
        "PrecipChanger": precip_defaults,
    }

    model = BasicThVs(params=params)
    assert model.eroder.K == K
    assert "PrecipChanger" in model.boundary_handler
    model.run_one_step(1.0)
    model.run_one_step(1.0)
    assert round(model.eroder.K, 5) == round(K * precip_testing_factor, 5)
