import numpy as np
#from numpy.testing import assert_array_equal, assert_array_almost_equal
from nose.tools import assert_raises#, assert_almost_equal, assert_equal

from landlab import HexModelGrid
from landlab.components import (FlowDirectorSteepest,
                                DepressionFinderAndRouter,
                                FlowDirectorMFD)

from terrainbento import ErosionModel


def test_FlowAccumulator_with_depression_steepest():
    params = {'model_grid': 'RasterModelGrid',
              'dt': 1,
              'output_interval': 2.,
              'run_duration': 200.,
              'flow_director': 'FlowDirectorSteepest',
              'depression_finder': 'DepressionFinderAndRouter'}

    em = ErosionModel(params=params)
    assert isinstance(em.flow_accumulator.flow_director, FlowDirectorSteepest)
    assert isinstance(em.flow_accumulator.depression_finder, DepressionFinderAndRouter)


def test_no_depression_finder():
    params = {'model_grid': 'RasterModelGrid',
              'dt': 1,
              'output_interval': 2.,
              'run_duration': 200.}

    em = ErosionModel(params=params)
    assert em.flow_accumulator.depression_finder is None


def test_FlowAccumulator_with_D8_Hex():
    params = {'model_grid': 'HexModelGrid',
              'dt': 1,
              'output_interval': 2.,
              'run_duration': 200.,
              'flow_director' : 'D8'}
    assert_raises(NotImplementedError, ErosionModel, params=params)


def test_FlowAccumulator_with_depression_MFD():
    params = {'model_grid': 'HexModelGrid',
              'dt': 1,
              'output_interval': 2.,
              'run_duration': 200.,
              'flow_director' : 'MFD'}
    em = ErosionModel(params=params)
    assert isinstance(em.flow_accumulator.flow_director, FlowDirectorMFD)

def test_alt_names_steepest():
    params = {'model_grid': 'RasterModelGrid',
              'dt': 1,
              'output_interval': 2.,
              'run_duration': 200.,
              'flow_director': 'D4'}

    em = ErosionModel(params=params)
    assert isinstance(em.flow_accumulator.flow_director, FlowDirectorSteepest)

    params = {'model_grid': 'RasterModelGrid',
              'dt': 1,
              'output_interval': 2.,
              'run_duration': 200.,
              'flow_director': 'Steepest'}

    em = ErosionModel(params=params)
    assert isinstance(em.flow_accumulator.flow_director, FlowDirectorSteepest)