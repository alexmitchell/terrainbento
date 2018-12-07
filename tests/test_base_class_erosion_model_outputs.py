# coding: utf8
# !/usr/env/python

import glob
import os

import xarray as xr

from terrainbento import Basic

# from numpy.testing import assert_array_equal, assert_array_almost_equal


_TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def test_write_output_raster():
    fp = os.path.join(_TEST_DATA_DIR, "basic_raster_inputs.yaml")
    model = Basic(input_file=fp)
    model._out_file_name = "tb_raster_output"
    model.run()
    fs = glob.glob(model._out_file_name + "*.nc")

    assert len(fs) == 5

    ds = xr.open_dataset(fs[0])
    ds.close()

    # todo assess raster output.

    model.remove_output_netcdfs()


def test_write_output_hex():
    fp = os.path.join(_TEST_DATA_DIR, "basic_inputs.yaml")
    model = Basic(input_file=fp)
    model._out_file_name = "tb_hex_output"
    model.run()
    fs = glob.glob(model._out_file_name + "*.nc")

    assert len(fs) == 5
    # ds = xr.open_dataset(fs[0])

    # todo assess hex output

    model.remove_output_netcdfs()


def test_write_synthesis_netcdf():
    fp = os.path.join(_TEST_DATA_DIR, "basic_raster_inputs_for_nc.yaml")
    truth = os.path.join(_TEST_DATA_DIR, "truth.nc")
    model = Basic(input_file=fp)
    model._out_file_name = "tb_synth_output"
    model.run()

    ds = model.to_xarray_dataset(time_unit="years", space_unit="meter")

    out_fn = "tb_output.nc"
    model.save_to_xarray_dataset(
        filename=out_fn, time_unit="years", space_unit="meter"
    )

    output = xr.open_dataset(out_fn, decode_times=False)
    truth = xr.open_dataset(truth, decode_times=False)

    assert truth.dims == output.dims
    assert truth.dims == ds.dims

    assert truth.equals(output) is True
    assert truth.equals(ds) is True

    output.close()
    truth.close()
    ds.close()

    model.remove_output_netcdfs()
    os.remove(out_fn)


def test_write_synthesis_netcdf_one_field():
    fp = os.path.join(_TEST_DATA_DIR, "basic_raster_inputs.yaml")
    truth = os.path.join(_TEST_DATA_DIR, "truth_one_field.nc")
    model = Basic(input_file=fp)
    model._out_file_name = "tb_synth_output_one_field"
    model.run(output_fields="topographic__elevation")

    ds = model.to_xarray_dataset(time_unit="years", space_unit="meter")

    out_fn = "tb_output_one_field.nc"
    model.save_to_xarray_dataset(
        filename=out_fn, time_unit="years", space_unit="meter"
    )

    output = xr.open_dataset(out_fn, decode_times=False)
    truth = xr.open_dataset(truth, decode_times=False)

    assert truth.dims == output.dims
    assert truth.dims == ds.dims

    assert truth.equals(output) is True
    assert truth.equals(ds) is True

    output.close()
    truth.close()
    ds.close()

    model.remove_output_netcdfs()
    os.remove(out_fn)


def test_write_synthesis_netcdf_one_field_first_timestep_false():
    fp = os.path.join(_TEST_DATA_DIR, "basic_raster_inputs.yaml")
    truth = os.path.join(_TEST_DATA_DIR, "truth_one_field_first_ts.nc")
    model = Basic(input_file=fp)
    model.save_first_timestep = False
    model._out_file_name = "tb_synth_output_one_field_first_ts"
    model.run(output_fields="topographic__elevation")

    ds = model.to_xarray_dataset(time_unit="years", space_unit="meter")

    out_fn = "tb_output_one_field_first_ts.nc"
    model.save_to_xarray_dataset(
        filename=out_fn, time_unit="years", space_unit="meter"
    )

    output = xr.open_dataset(out_fn, decode_times=False)
    truth = xr.open_dataset(truth, decode_times=False)

    assert truth.dims == output.dims
    assert truth.dims == ds.dims

    assert truth.equals(output) is True
    assert truth.equals(ds) is True

    output.close()
    truth.close()
    ds.close()

    model.remove_output_netcdfs()
    os.remove(out_fn)
