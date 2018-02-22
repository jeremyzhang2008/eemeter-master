import tempfile

import pandas as pd
import pytest
import pytz
import json

from eemeter.ee.meter import EnergyEfficiencyMeter
from eemeter.testing.mocks import MockWeatherClient
from eemeter.weather import TMY3WeatherSource
from eemeter.weather import ISDWeatherSource
from eemeter.modeling.formatters import ModelDataBillingFormatter
from eemeter.modeling.models import CaltrackMonthlyModel, CaltrackDailyModel


@pytest.fixture
def project_meter_input():
    return {
        "type": "PROJECT_WITH_SINGLE_MODELING_PERIOD_GROUP",
        "zipcode": "91104",
        "project_id": "PROJECT_1",
        "modeling_period_group": {
            "baseline_period": {
                "start": None,
                "end": "2014-01-01T00:00:00+00:00"
            },
            "reporting_period": {
                "start": "2014-02-01T00:00:00+00:00",
                "end": None
            }
        }
    }


@pytest.fixture
def project_meter_input_bad_zipcode():
    return {
        "type": "PROJECT_WITH_SINGLE_MODELING_PERIOD_GROUP",
        "zipcode": "11111",  # not valid
        "modeling_period_group": {
            "baseline_period": {
                "start": None,
                "end": "2014-01-01T00:00:00+00:00"
            },
            "reporting_period": {
                "start": "2014-02-01T00:00:00+00:00",
                "end": None
            }
        }
    }


@pytest.fixture
def project_meter_input_with_period_start_end():
    return {
        "type": "PROJECT_WITH_SINGLE_MODELING_PERIOD_GROUP",
        "zipcode": "91104",
        "project_id": "PROJECT_1",
        "modeling_period_group": {
            "baseline_period": {
                "start": "2013-01-01T00:00:00+00:00",
                "end": "2014-01-01T00:00:00+00:00"
            },
            "reporting_period": {
                "start": "2014-02-01T00:00:00+00:00",
                "end": "2015-02-01T00:00:00+00:00",
            }
        }
    }


def _electricity_input(records):
    return {
        "type": "ARBITRARY_START",
        "interpretation": "ELECTRICITY_CONSUMPTION_SUPPLIED",
        "unit": "KWH",
        "records": records
    }


def _natural_gas_input(records):
    return {
        "type": "ARBITRARY_START",
        "interpretation": "NATURAL_GAS_CONSUMPTION_SUPPLIED",
        "unit": "THERM",
        "trace_id": "TRACE_1",
        "records": records
    }


@pytest.fixture
def meter_input_daily(project_meter_input):

    record_starts = pd.date_range(
        '2012-01-01', periods=365 * 4, freq='D', tz=pytz.UTC)

    records = [
        {
            "start": dt.isoformat(),
            "value": 1.0,
            "estimated": False
        } for dt in record_starts
    ]

    trace = _natural_gas_input(records)
    trace.update({'interval': 'daily'})

    meter_input = {
        "type": "SINGLE_TRACE_SIMPLE_PROJECT",
        "trace": trace,
        "project": project_meter_input,
    }
    return meter_input


@pytest.fixture
def meter_input_hourly(project_meter_input):

    record_starts = pd.date_range(
        '2012-01-01', periods=365 * 4 * 24, freq='H', tz=pytz.UTC)

    records = [
        {
            "start": dt.isoformat(),
            "value": 1.0 + dt.hour,
            "estimated": False
        } for dt in record_starts
    ]

    trace = _natural_gas_input(records)
    trace.update({'interval': 'hourly'})

    meter_input = {
        "type": "SINGLE_TRACE_SIMPLE_PROJECT",
        "trace": trace,
        "project": project_meter_input,
    }
    return meter_input


@pytest.fixture
def meter_input_daily_elec(project_meter_input):

    record_starts = pd.date_range(
        '2012-01-01', periods=365 * 4, freq='D', tz=pytz.UTC)

    records = [
        {
            "start": dt.isoformat(),
            "value": 1.0,
            "estimated": False
        } for dt in record_starts
    ]

    trace = _electricity_input(records)
    trace.update({'interval': 'daily'})

    meter_input = {
        "type": "SINGLE_TRACE_SIMPLE_PROJECT",
        "trace": trace,
        "project": project_meter_input,
    }
    return meter_input


@pytest.fixture
def meter_input_empty(project_meter_input):

    records = []

    meter_input = {
        "type": "SINGLE_TRACE_SIMPLE_PROJECT",
        "trace": _natural_gas_input(records),
        "project": project_meter_input,
    }
    return meter_input


@pytest.fixture
def meter_input_daily_baseline_only(project_meter_input):

    record_starts = pd.date_range(
        '2012-01-01', periods=365 * 1, freq='D', tz=pytz.UTC)

    records = [
        {
            "start": dt.isoformat(),
            "value": 1.0,
            "estimated": False
        } for dt in record_starts
    ]

    meter_input = {
        "type": "SINGLE_TRACE_SIMPLE_PROJECT",
        "trace": _natural_gas_input(records),
        "project": project_meter_input,
    }
    return meter_input


@pytest.fixture
def meter_input_daily_reporting_only(project_meter_input):

    record_starts = pd.date_range(
        '2014-02-01', periods=365 * 1, freq='D', tz=pytz.UTC)

    records = [
        {
            "start": dt.isoformat(),
            "value": 1.0,
            "estimated": False
        } for dt in record_starts
    ]

    meter_input = {
        "type": "SINGLE_TRACE_SIMPLE_PROJECT",
        "trace": _natural_gas_input(records),
        "project": project_meter_input,
    }
    return meter_input


@pytest.fixture
def meter_input_daily_with_period_start_end(
        project_meter_input_with_period_start_end):

    record_starts = pd.date_range(
        '2012-01-01', periods=365 * 4, freq='D', tz=pytz.UTC)

    records = [
        {
            "start": dt.isoformat(),
            "value": 1.0,
            "estimated": False
        } for dt in record_starts
    ]

    trace = _natural_gas_input(records)
    trace.update({'interval': 'daily'})

    meter_input = {
        "type": "SINGLE_TRACE_SIMPLE_PROJECT",
        "trace": trace,
        "project": project_meter_input_with_period_start_end,
    }
    return meter_input


@pytest.fixture
def meter_input_monthly(project_meter_input, ):

    record_starts = pd.date_range(
        '2012-01-01', periods=60, freq='MS', tz=pytz.UTC)

    monthly_heating_cooling_pattern = {
        1:  31,
        2:  31,
        3:  25,
        4:  13,
        5:  0,
        6:  12,
        7:  19,
        8:  19,
        9:  13,
        10: 1,
        11: 12,
        12: 24,
    }

    records = [
        {
            "start": dt.isoformat(),
            "value": monthly_heating_cooling_pattern[dt.month],
            "estimated": False
        } for dt in record_starts
    ]

    meter_input = {
        "type": "SINGLE_TRACE_SIMPLE_PROJECT",
        "trace": _electricity_input(records),
        "project": project_meter_input,
    }
    return meter_input


@pytest.fixture
def meter_input_strange_interpretation(project_meter_input):

    record_starts = pd.date_range(
        '2012-01-01', periods=365 * 4, freq='D', tz=pytz.UTC)

    records = [
        {
            "start": dt.isoformat(),
            "value": 1.0,
            "estimated": False
        } for dt in record_starts
    ]

    meter_input = {
        "type": "SINGLE_TRACE_SIMPLE_PROJECT",
        "trace": {
            "type": "ARBITRARY_START",
            "interpretation": "ELECTRICITY_CONSUMPTION_NET",
            "unit": "therm",
            "records": records
        },
        "project": project_meter_input
    }
    return meter_input


@pytest.fixture
def meter_input_bad_zipcode(project_meter_input_bad_zipcode):

    record_starts = pd.date_range(
        '2012-01-01', periods=50, freq='MS', tz=pytz.UTC)

    records = [
        {
            "start": dt.isoformat(),
            "value": 1.0,
            "estimated": False
        } for dt in record_starts
    ]

    meter_input = {
        "type": "SINGLE_TRACE_SIMPLE_PROJECT",
        "trace": _electricity_input(records),
        "project": project_meter_input_bad_zipcode,
    }
    return meter_input


@pytest.fixture
def mock_isd_weather_source():
    tmp_url = "sqlite:///{}/weather_cache.db".format(tempfile.mkdtemp())
    ws = ISDWeatherSource('722880', tmp_url)
    ws.client = MockWeatherClient()
    return ws


@pytest.fixture
def mock_tmy3_weather_source():
    tmp_url = "sqlite:///{}/weather_cache.db".format(tempfile.mkdtemp())
    ws = TMY3WeatherSource('724838', tmp_url, preload=False)
    ws.client = MockWeatherClient()
    ws._load_data()
    return ws


def test_basic_usage_daily(
        meter_input_daily, mock_isd_weather_source, mock_tmy3_weather_source):

    meter = EnergyEfficiencyMeter()

    results = meter.evaluate(meter_input_daily,
                             weather_source=mock_isd_weather_source,
                             weather_normal_source=mock_tmy3_weather_source)

    assert results['status'] == 'SUCCESS'
    assert results['failure_message'] is None
    assert len(results['logs']) == 2

    assert results['eemeter_version'] is not None

    assert results['project_id'] == 'PROJECT_1'
    assert results['trace_id'] == 'TRACE_1'
    assert results['interval'] == 'daily'

    assert results['meter_kwargs'] == {}
    assert results['model_class'] == 'CaltrackDailyModel'
    assert results['model_kwargs'] is not None
    assert results['formatter_class'] == 'ModelDataFormatter'
    assert results['formatter_kwargs'] is not None

    assert results['modeled_energy_trace'] is not None

    derivatives = results['derivatives']

    baseline_observed = {d['series']:d for d in derivatives}['Observed, baseline period']
    reporting_observed = {d['series']:d for d in derivatives}['Observed, reporting period']

    assert (baseline_observed['orderable'][0], baseline_observed['orderable'][-1]) == ('2012-01-01T00:00:00+00:00', '2014-01-01T00:00:00+00:00')
    assert (reporting_observed['orderable'][0], reporting_observed['orderable'][-1]) == ('2014-02-01T00:00:00+00:00', '2015-12-30T00:00:00+00:00')

    assert len(derivatives) == 32
    assert derivatives[0]['modeling_period_group'] == \
        ('baseline', 'reporting')
    assert derivatives[0]['orderable'] == [None]

    source_series = set([d['series'] for d in derivatives])
    assert source_series == set([
        'Cumulative baseline model minus reporting model, normal year',
        'Cumulative baseline model, normal year',
        'Baseline model, normal year',
        'Cumulative reporting model, normal year',
        'Baseline model minus reporting model, normal year',
        'Baseline model, normal year',
        'Reporting model, normal year',
        'Baseline model, baseline period',

        'Cumulative baseline model minus observed, reporting period',
        'Cumulative baseline model, reporting period',
        'Cumulative observed, reporting period',
        'Baseline model minus observed, reporting period',
        'Baseline model, reporting period',
        'Observed, reporting period',
        'Masked baseline model minus observed, reporting period',
        'Masked baseline model, reporting period',
        'Masked observed, reporting period',

        'Baseline model, baseline period',
        'Reporting model, reporting period',

        'Cumulative observed, baseline period',
        'Observed, baseline period',

        'Observed, project period',

        'Inclusion mask, baseline period',
        'Inclusion mask, reporting period',

        'Temperature, baseline period',
        'Temperature, reporting period',
        'Temperature, normal year',
        'Masked temperature, reporting period',

        'Heating degree day balance point, baseline period',
        'Cooling degree day balance point, baseline period',
        'Heating degree day balance point, reporting period',
        'Cooling degree day balance point, reporting period',
        'Best-fit intercept, baseline period',
        'Best-fit intercept, reporting period',
    ])

    for d in derivatives:
        assert isinstance(d['orderable'], list)
        assert isinstance(d['value'], list)
        assert isinstance(d['variance'], list)
        assert len(d['orderable']) == len(d['value']) == len(d['variance'])

    json.dumps(results)


def test_basic_usage_monthly(
        meter_input_monthly,
        mock_isd_weather_source,
        mock_tmy3_weather_source):

    meter = EnergyEfficiencyMeter()

    results = meter.evaluate(meter_input_monthly,
                             weather_source=mock_isd_weather_source,
                             weather_normal_source=mock_tmy3_weather_source)

    assert results['status'] == 'SUCCESS'
    assert results['failure_message'] is None
    assert len(results['logs']) == 2

    assert results['eemeter_version'] is not None
    assert results['meter_kwargs'] == {}
    assert results['model_class'] == 'CaltrackMonthlyModel'
    assert results['model_kwargs'] is not None
    assert results['formatter_class'] == 'ModelDataBillingFormatter'
    assert results['formatter_kwargs'] is not None

    assert results['modeled_energy_trace'] is not None

    derivatives = results['derivatives']

    assert len(derivatives) == 36
    assert derivatives[0]['modeling_period_group'] == \
        ('baseline', 'reporting')
    assert derivatives[0]['orderable'] == [None]

    source_series = set([d['series'] for d in derivatives])
    assert source_series == set([
        'Cumulative baseline model minus reporting model, normal year',
        'Cumulative baseline model, normal year',
        'Baseline model, normal year',
        'Cumulative reporting model, normal year',
        'Baseline model minus reporting model, normal year',
        'Reporting model, normal year',

        'Cumulative baseline model minus observed, reporting period',
        'Cumulative baseline model, reporting period',
        'Cumulative observed, reporting period',
        'Baseline model minus observed, reporting period',
        'Baseline model, reporting period',
        'Observed, reporting period',
        'Masked baseline model minus observed, reporting period',
        'Masked baseline model, reporting period',
        'Masked observed, reporting period',

        'Baseline model, baseline period',
        'Reporting model, reporting period',

        'Cumulative observed, baseline period',
        'Observed, baseline period',

        'Observed, project period',

        'Inclusion mask, baseline period',
        'Inclusion mask, reporting period',

        'Temperature, baseline period',
        'Temperature, reporting period',
        'Temperature, normal year',
        'Masked temperature, reporting period',

        'Heating degree day balance point, baseline period',
        'Cooling degree day balance point, baseline period',
        'Heating degree day balance point, reporting period',
        'Cooling degree day balance point, reporting period',
        'Best-fit intercept, baseline period',
        'Best-fit intercept, reporting period',
        'Best-fit heating coefficient, baseline period',
        'Best-fit heating coefficient, reporting period',
        'Best-fit cooling coefficient, baseline period',
        'Best-fit cooling coefficient, reporting period',
    ])

    for d in derivatives:
        assert isinstance(d['orderable'], list)
        assert isinstance(d['value'], list)
        assert isinstance(d['variance'], list)
        assert len(d['orderable']) == len(d['value']) == len(d['variance'])

    json.dumps(results)


def test_basic_usage_baseline_only(
        meter_input_daily_baseline_only,
        mock_isd_weather_source,
        mock_tmy3_weather_source):

    meter = EnergyEfficiencyMeter()

    results = meter.evaluate(meter_input_daily_baseline_only,
                             weather_source=mock_isd_weather_source,
                             weather_normal_source=mock_tmy3_weather_source)

    assert results['status'] == 'SUCCESS'
    assert results['failure_message'] is None
    assert len(results['logs']) == 2

    assert results['eemeter_version'] is not None
    assert results['meter_kwargs'] == {}
    assert results['model_class'] == 'CaltrackDailyModel'
    assert results['model_kwargs'] is not None
    assert results['formatter_class'] == 'ModelDataFormatter'
    assert results['formatter_kwargs'] is not None

    assert results['modeled_energy_trace'] is not None

    derivatives = results['derivatives']
    assert len(derivatives) == 18
    assert derivatives[0]['modeling_period_group'] == \
        ('baseline', 'reporting')
    assert derivatives[0]['orderable'] == [None]

    source_series = set([d['series'] for d in derivatives])
    assert source_series == set([
        # 'Cumulative baseline model minus reporting model, normal year',
        'Cumulative baseline model, normal year',
        # 'Cumulative reporting model, normal year',
        # 'Baseline model minus reporting model, normal year',
        'Baseline model, normal year',
        # 'Reporting model, normal year',

        # 'Cumulative baseline model minus observed, reporting period',
        # 'Cumulative baseline model, reporting period',
        'Cumulative observed, reporting period',
        # 'Baseline model minus observed, reporting period',
        # 'Baseline model, reporting period',
        'Observed, reporting period',
        # 'Masked baseline model minus observed, reporting period',
        # 'Masked baseline model, reporting period',
        'Masked observed, reporting period',

        'Baseline model, baseline period',
        #'Reporting model, reporting period',

        'Cumulative observed, baseline period',
        'Observed, baseline period',

        'Observed, project period',

        'Inclusion mask, baseline period',
        'Inclusion mask, reporting period',

        'Temperature, baseline period',
        'Temperature, reporting period',
        'Temperature, normal year',
        'Masked temperature, reporting period',

        'Heating degree day balance point, baseline period',
        'Cooling degree day balance point, baseline period',
        #'Heating degree day balance point, reporting period',
        #'Cooling degree day balance point, reporting period',
        'Best-fit intercept, baseline period',
        #'Best-fit intercept, reporting period',
    ])

    for d in derivatives:
        assert isinstance(d['orderable'], list)
        assert isinstance(d['value'], list)
        assert isinstance(d['variance'], list)
        assert len(d['orderable']) == len(d['value']) == len(d['variance'])

    json.dumps(results)


def test_basic_usage_reporting_only(
        meter_input_daily_reporting_only,
        mock_isd_weather_source,
        mock_tmy3_weather_source):

    meter = EnergyEfficiencyMeter()

    results = meter.evaluate(meter_input_daily_reporting_only,
                             weather_source=mock_isd_weather_source,
                             weather_normal_source=mock_tmy3_weather_source)

    assert results['status'] == 'SUCCESS'
    assert results['failure_message'] is None
    assert len(results['logs']) == 2

    assert results['eemeter_version'] is not None
    assert results['meter_kwargs'] == {}
    assert results['model_class'] == 'CaltrackDailyModel'
    assert results['model_kwargs'] is not None
    assert results['formatter_class'] == 'ModelDataFormatter'
    assert results['formatter_kwargs'] is not None

    assert results['modeled_energy_trace'] is not None

    derivatives = results['derivatives']
    assert len(derivatives) == 18
    assert derivatives[0]['modeling_period_group'] == \
        ('baseline', 'reporting')
    assert derivatives[0]['orderable'] == [None]
    assert derivatives[0]['value'] is not None
    assert derivatives[0]['variance'] is not None

    source_series = set([d['series'] for d in derivatives])
    assert source_series == set([
        # 'Cumulative baseline model minus reporting model, normal year',
        # 'Cumulative baseline model, normal year',
        'Cumulative reporting model, normal year',
        # 'Baseline model minus reporting model, normal year',
        # 'Baseline model, normal year',
        'Reporting model, normal year',

        # 'Cumulative baseline model minus observed, reporting period',
        # 'Cumulative baseline model, reporting period',
        'Cumulative observed, reporting period',
        # 'Baseline model minus observed, reporting period',
        # 'Baseline model, reporting period',
        'Observed, reporting period',
        # 'Masked baseline model minus observed, reporting period',
        # 'Masked baseline model, reporting period',
        'Masked observed, reporting period',

        #'Baseline model, baseline period',
        'Reporting model, reporting period',

        'Cumulative observed, baseline period',
        'Observed, baseline period',

        'Observed, project period',

        'Inclusion mask, baseline period',
        'Inclusion mask, reporting period',

        'Temperature, baseline period',
        'Temperature, reporting period',
        'Temperature, normal year',
        'Masked temperature, reporting period',

        #'Heating degree day balance point, baseline period',
        #'Cooling degree day balance point, baseline period',
        'Heating degree day balance point, reporting period',
        'Cooling degree day balance point, reporting period',
        #'Best-fit intercept, baseline period',
        'Best-fit intercept, reporting period',
    ])

    for d in derivatives:
        assert isinstance(d['orderable'], list)
        assert isinstance(d['value'], list)
        assert isinstance(d['variance'], list)
        assert len(d['orderable']) == len(d['value']) == len(d['variance'])

    json.dumps(results)


def test_basic_usage_empty(
        meter_input_empty,
        mock_isd_weather_source,
        mock_tmy3_weather_source):

    meter = EnergyEfficiencyMeter()

    results = meter.evaluate(meter_input_empty,
                             weather_source=mock_isd_weather_source,
                             weather_normal_source=mock_tmy3_weather_source)

    assert results['status'] == 'SUCCESS'
    assert results['failure_message'] is None
    assert results['modeled_energy_trace'] is not None
    assert len(results['derivatives']) == 0


def test_bad_meter_input(mock_isd_weather_source, mock_tmy3_weather_source):

    meter = EnergyEfficiencyMeter()

    results = meter.evaluate({},
                             weather_source=mock_isd_weather_source,
                             weather_normal_source=mock_tmy3_weather_source)

    assert results['status'] == 'FAILURE'
    assert results['failure_message'].startswith("Meter input")


def test_strange_interpretation(meter_input_strange_interpretation,
                                mock_isd_weather_source,
                                mock_tmy3_weather_source):

    meter = EnergyEfficiencyMeter()

    results = meter.evaluate(meter_input_strange_interpretation,
                             weather_source=mock_isd_weather_source,
                             weather_normal_source=mock_tmy3_weather_source)

    assert results['status'] == 'FAILURE'
    assert results['failure_message'].startswith("Default formatter")


def test_bad_zipcode(meter_input_bad_zipcode):

    meter = EnergyEfficiencyMeter()

    results = meter.evaluate(meter_input_bad_zipcode)

    assert results['project_id'] is None
    assert results['trace_id'] is None
    assert results['interval'] is None

    derivatives = results['derivatives']
    assert len(derivatives) == 8

    source_series = set([d['series'] for d in derivatives])
    assert source_series == set([
        # 'Cumulative baseline model minus reporting model, normal year',
        # 'Cumulative baseline model, normal year',
        # 'Cumulative reporting model, normal year',
        # 'Baseline model minus reporting model, normal year',
        # 'Baseline model, normal year',
        # 'Reporting model, normal year',

        # 'Cumulative baseline model minus observed, reporting period',
        # 'Cumulative baseline model, reporting period',
        'Cumulative observed, reporting period',
        # 'Baseline model minus observed, reporting period',
        # 'Baseline model, reporting period',
        'Observed, reporting period',
        # 'Masked baseline model minus observed, reporting period',
        # 'Masked baseline model, reporting period',
        'Masked observed, reporting period',

        #'Baseline model, baseline period',
        #'Reporting model, reporting period',

        'Cumulative observed, baseline period',
        'Observed, baseline period',

        'Observed, project period',

        'Inclusion mask, baseline period',
        'Inclusion mask, reporting period',

        # 'Temperature, baseline period',
        # 'Temperature, reporting period',
        # 'Temperature, normal year',

        # 'Masked temperature, reporting period',
    ])

    for d in derivatives:
        assert isinstance(d['orderable'], list)
        assert isinstance(d['value'], list)
        assert isinstance(d['variance'], list)
        assert len(d['orderable']) == len(d['value']) == len(d['variance'])

    json.dumps(results)


def test_custom_evaluate_args_monthly(
        meter_input_monthly,
        mock_isd_weather_source,
        mock_tmy3_weather_source):

    meter = EnergyEfficiencyMeter()

    results = meter.evaluate(meter_input_monthly,
                             model=None,
                             formatter=None,
                             weather_source=mock_isd_weather_source,
                             weather_normal_source=mock_tmy3_weather_source)

    assert results['meter_kwargs'] == {}
    assert results['model_class'] == 'CaltrackMonthlyModel'
    assert results['model_kwargs'] == {'fit_cdd': True, 'grid_search': True}
    assert results['formatter_class'] == 'ModelDataBillingFormatter'
    assert results['formatter_kwargs'] == {}

    results = meter.evaluate(meter_input_monthly,
                             model=(None, None),
                             formatter=(None, None),
                             weather_source=mock_isd_weather_source,
                             weather_normal_source=mock_tmy3_weather_source)

    assert results['meter_kwargs'] == {}
    assert results['model_class'] == 'CaltrackMonthlyModel'
    assert results['model_kwargs'] == {'fit_cdd': True, 'grid_search': True}
    assert results['formatter_class'] == 'ModelDataBillingFormatter'
    assert results['formatter_kwargs'] == {}

    results = meter.evaluate(meter_input_monthly,
                             model=('CaltrackMonthlyModel', None),
                             formatter=('ModelDataBillingFormatter', None),
                             weather_source=mock_isd_weather_source,
                             weather_normal_source=mock_tmy3_weather_source)

    assert results['meter_kwargs'] == {}
    assert results['model_class'] == 'CaltrackMonthlyModel'
    assert results['model_kwargs'] == {}
    assert results['formatter_class'] == 'ModelDataBillingFormatter'
    assert results['formatter_kwargs'] == {}

    results = meter.evaluate(meter_input_monthly,
                             model=(None, {"fit_cdd": False}),
                             weather_source=mock_isd_weather_source,
                             weather_normal_source=mock_tmy3_weather_source)

    assert results['meter_kwargs'] == {}
    assert results['model_class'] == 'CaltrackMonthlyModel'
    assert results['model_kwargs'] == {'fit_cdd': False, 'grid_search': True}
    assert results['formatter_class'] == 'ModelDataBillingFormatter'
    assert results['formatter_kwargs'] == {}

    results = meter.evaluate(meter_input_monthly,
                             model=(None, {"fit_cdd": False}),
                             formatter=(None, {}),
                             weather_source=mock_isd_weather_source,
                             weather_normal_source=mock_tmy3_weather_source)

    assert results['meter_kwargs'] == {}
    assert results['model_class'] == 'CaltrackMonthlyModel'
    assert results['model_kwargs'] == {'fit_cdd': False, 'grid_search': True}
    assert results['formatter_class'] == 'ModelDataBillingFormatter'
    assert results['formatter_kwargs'] == {}

    results = meter.evaluate(meter_input_monthly,
                             model=(CaltrackMonthlyModel, {"fit_cdd": False}),
                             formatter=(ModelDataBillingFormatter, {}),
                             weather_source=mock_isd_weather_source,
                             weather_normal_source=mock_tmy3_weather_source)

    assert results['meter_kwargs'] == {}
    assert results['model_class'] == 'CaltrackMonthlyModel'
    assert results['model_kwargs'] == {'fit_cdd': False}
    assert results['formatter_class'] == 'ModelDataBillingFormatter'
    assert results['formatter_kwargs'] == {}


def test_custom_evaluate_args_daily(
        meter_input_daily_elec,
        mock_isd_weather_source,
        mock_tmy3_weather_source):

    meter = EnergyEfficiencyMeter()

    results = meter.evaluate(meter_input_daily_elec,
                             model=None,
                             formatter=None,
                             weather_source=mock_isd_weather_source,
                             weather_normal_source=mock_tmy3_weather_source)

    assert results['meter_kwargs'] == {}
    assert results['model_class'] == 'CaltrackDailyModel'
    assert results['model_kwargs'] == {'fit_cdd': True, 'grid_search': True}
    assert results['formatter_class'] == 'ModelDataFormatter'
    assert results['formatter_kwargs'] == {'freq_str': 'D'}

    results = meter.evaluate(meter_input_daily_elec,
                             model=(CaltrackDailyModel, {'fit_cdd': False}),
                             formatter=None,
                             weather_source=mock_isd_weather_source,
                             weather_normal_source=mock_tmy3_weather_source)

    assert results['meter_kwargs'] == {}
    assert results['model_class'] == 'CaltrackDailyModel'
    assert results['model_kwargs'] == {'fit_cdd': False}
    assert results['formatter_class'] == 'ModelDataFormatter'
    assert results['formatter_kwargs'] == {'freq_str': 'D'}


def test_ignore_extra_args_daily(
        meter_input_daily_elec,
        mock_isd_weather_source,
        mock_tmy3_weather_source):

    meter = EnergyEfficiencyMeter()

    results = meter.evaluate(meter_input_daily_elec,
                             model=(None, {'fit_cdd': True, 'grid_search': True, 'extra_arg': 'value'}),
                             formatter=None,
                             weather_source=mock_isd_weather_source,
                             weather_normal_source=mock_tmy3_weather_source)

    assert results['meter_kwargs'] == {}
    assert results['model_class'] == 'CaltrackDailyModel'
    assert results['model_kwargs'] == {'fit_cdd': True, 'grid_search': True, 'extra_arg': 'value'}


def test_ignore_extra_args_monthly(
        meter_input_monthly,
        mock_isd_weather_source,
        mock_tmy3_weather_source):

    meter = EnergyEfficiencyMeter()

    results = meter.evaluate(meter_input_monthly,
                             model=(None, {'grid_search': True, 'extra_arg': 'value'}),
                             formatter=None,
                             weather_source=mock_isd_weather_source,
                             weather_normal_source=mock_tmy3_weather_source)

    assert results['meter_kwargs'] == {}
    assert results['model_class'] == 'CaltrackMonthlyModel'
    assert results['model_kwargs'] == {'fit_cdd': True, 'grid_search': True, 'extra_arg': 'value'}


def test_basic_usage_daily_period_start_end(
        meter_input_daily_with_period_start_end,
        mock_isd_weather_source,
        mock_tmy3_weather_source):

    meter = EnergyEfficiencyMeter()

    results = meter.evaluate(meter_input_daily_with_period_start_end,
                             weather_source=mock_isd_weather_source,
                             weather_normal_source=mock_tmy3_weather_source)

    assert results['status'] == 'SUCCESS'
    assert results['failure_message'] is None
    assert len(results['logs']) == 2

    assert results['eemeter_version'] is not None

    assert results['project_id'] == 'PROJECT_1'
    assert results['trace_id'] == 'TRACE_1'
    assert results['interval'] == 'daily'

    assert results['meter_kwargs'] == {}
    assert results['model_class'] == 'CaltrackDailyModel'
    assert results['model_kwargs'] is not None
    assert results['formatter_class'] == 'ModelDataFormatter'
    assert results['formatter_kwargs'] is not None

    assert results['modeled_energy_trace'] is not None

    derivatives = results['derivatives']
    assert len(derivatives) == 32

    baseline_observed = {d['series']:d for d in derivatives}['Observed, baseline period']
    reporting_observed = {d['series']:d for d in derivatives}['Observed, reporting period']

    assert (baseline_observed['orderable'][0], baseline_observed['orderable'][-1]) == ('2013-01-01T00:00:00+00:00', '2014-01-01T00:00:00+00:00')
    assert (reporting_observed['orderable'][0], reporting_observed['orderable'][-1]) == ('2014-02-01T00:00:00+00:00', '2015-02-01T00:00:00+00:00')

    assert derivatives[0]['modeling_period_group'] == ('baseline', 'reporting')
    assert derivatives[0]['orderable'] == [None]

    source_series = set([d['series'] for d in derivatives])
    assert source_series == set([
        'Cumulative baseline model minus reporting model, normal year',
        'Cumulative baseline model, normal year',
        'Baseline model, normal year',
        'Cumulative reporting model, normal year',
        'Baseline model minus reporting model, normal year',
        'Baseline model, normal year',
        'Reporting model, normal year',
        'Baseline model, baseline period',

        'Cumulative baseline model minus observed, reporting period',
        'Cumulative baseline model, reporting period',
        'Cumulative observed, reporting period',
        'Baseline model minus observed, reporting period',
        'Baseline model, reporting period',
        'Observed, reporting period',
        'Masked baseline model minus observed, reporting period',
        'Masked baseline model, reporting period',
        'Masked observed, reporting period',

        'Baseline model, baseline period',
        'Reporting model, reporting period',

        'Cumulative observed, baseline period',
        'Observed, baseline period',

        'Observed, project period',

        'Inclusion mask, baseline period',
        'Inclusion mask, reporting period',

        'Temperature, baseline period',
        'Temperature, reporting period',
        'Temperature, normal year',
        'Masked temperature, reporting period',

        'Heating degree day balance point, baseline period',
        'Cooling degree day balance point, baseline period',
        'Heating degree day balance point, reporting period',
        'Cooling degree day balance point, reporting period',
        'Best-fit intercept, baseline period',
        'Best-fit intercept, reporting period',
    ])

    for d in derivatives:
        assert isinstance(d['orderable'], list)
        assert isinstance(d['value'], list)
        assert isinstance(d['variance'], list)
        assert len(d['orderable']) == len(d['value']) == len(d['variance'])

    json.dumps(results)


def test_meter_settings_cz2010(meter_input_daily):
    meter = EnergyEfficiencyMeter(
        weather_station_mapping='CZ2010',
        weather_normal_station_mapping='CZ2010'
    )
    assert meter.weather_station_mapping == 'CZ2010'
    assert meter.weather_normal_station_mapping == 'CZ2010'

    results = meter.evaluate(meter_input_daily)
    assert results['logs'][0] == 'Using weather_source ISDWeatherSource("722874")'
    assert results['logs'][1] == 'Using weather_normal_source CZ2010WeatherSource("722874")'
    assert results['status'] == 'SUCCESS'
    assert results['meter_kwargs'] == {
        'weather_station_mapping': 'CZ2010',
        'weather_normal_station_mapping': 'CZ2010'
    }


def test_basic_usage_hourly(
        meter_input_hourly, mock_isd_weather_source, mock_tmy3_weather_source):

    meter = EnergyEfficiencyMeter()

    results = meter.evaluate(meter_input_hourly,
                             weather_source=mock_isd_weather_source,
                             weather_normal_source=mock_tmy3_weather_source)

    assert results['status'] == 'SUCCESS'
    assert results['failure_message'] is None
    assert len(results['logs']) == 2

    assert results['eemeter_version'] is not None

    assert results['project_id'] == 'PROJECT_1'
    assert results['trace_id'] == 'TRACE_1'
    assert results['interval'] == 'hourly'

    assert results['meter_kwargs'] == {}
    assert results['model_class'] == 'CaltrackDailyModel'
    assert results['model_kwargs'] is not None
    assert results['formatter_class'] == 'ModelDataFormatter'
    assert results['formatter_kwargs'] is not None

    assert results['modeled_energy_trace'] is not None

    derivatives = results['derivatives']

    baseline_observed = {d['series']:d for d in derivatives}['Observed, baseline period']
    reporting_observed = {d['series']:d for d in derivatives}['Observed, reporting period']

    assert (baseline_observed['orderable'][0], baseline_observed['orderable'][-1]) == ('2012-01-01T00:00:00+00:00', '2014-01-01T00:00:00+00:00')
    assert (reporting_observed['orderable'][0], reporting_observed['orderable'][-1]) == ('2014-02-01T00:00:00+00:00', '2015-12-30T00:00:00+00:00')

    assert len(derivatives) == 35
    assert derivatives[0]['modeling_period_group'] == \
        ('baseline', 'reporting')
    assert derivatives[0]['orderable'] == [None]

    source_series = set([d['series'] for d in derivatives])
    assert source_series == set([
        'Cumulative baseline model minus reporting model, normal year',
        'Cumulative baseline model, normal year',
        'Baseline model, normal year',
        'Cumulative reporting model, normal year',
        'Baseline model minus reporting model, normal year',
        'Baseline model, normal year',
        'Reporting model, normal year',
        'Baseline model, baseline period',

        'Cumulative baseline model minus observed, reporting period',
        'Cumulative baseline model, reporting period',
        'Cumulative observed, reporting period',
        'Baseline model minus observed, reporting period',
        'Baseline model, reporting period',
        'Observed, reporting period',
        'Masked baseline model minus observed, reporting period',
        'Masked baseline model, reporting period',
        'Masked observed, reporting period',

        'Baseline model, baseline period',
        'Reporting model, reporting period',

        'Cumulative observed, baseline period',
        'Observed, baseline period',

        'Observed, project period',

        'Inclusion mask, baseline period',
        'Inclusion mask, reporting period',

        'Temperature, baseline period',
        'Temperature, reporting period',
        'Temperature, normal year',
        'Masked temperature, reporting period',

        'Heating degree day balance point, baseline period',
        'Cooling degree day balance point, baseline period',
        'Heating degree day balance point, reporting period',
        'Cooling degree day balance point, reporting period',
        'Best-fit intercept, baseline period',
        'Best-fit intercept, reporting period',

        'Resource curve, normal year',
        'Resource curve, reporting period',
        'CO2 avoided emissions, normal year',
    ])

    for d in derivatives:
        assert isinstance(d['orderable'], list)
        assert isinstance(d['value'], list)
        assert isinstance(d['variance'], list)
        assert len(d['orderable']) == len(d['value']) == len(d['variance'])

    json.dumps(results)

