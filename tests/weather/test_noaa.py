import tempfile

from numpy.testing import assert_allclose
import pandas as pd
import pytest

from eemeter.weather import GSODWeatherSource, ISDWeatherSource
from eemeter.testing import MockWeatherClient


@pytest.fixture
def mock_gsod_weather_source():
    tmp_url = "sqlite:///{}/weather_cache.db".format(tempfile.mkdtemp())
    ws = GSODWeatherSource("722880", tmp_url)
    ws.client = MockWeatherClient()
    return ws


def test_gsod_index_hourly(mock_gsod_weather_source):
    index = pd.date_range('2011-01-01 00:00:00Z', periods=2, freq='H')
    with pytest.raises(ValueError):
        mock_gsod_weather_source.indexed_temperatures(index, 'degF')


def test_gsod_index_daily(mock_gsod_weather_source):
    index = pd.date_range('2011-01-01 00:00:00Z', periods=2, freq='D')
    temps = mock_gsod_weather_source.indexed_temperatures(index, 'degF')
    assert all(temps.index == index)
    assert all(temps.index == index)
    assert temps.shape == (2,)
    assert_allclose(temps.values, [35.617314, 35.388398])

    temps = mock_gsod_weather_source.indexed_temperatures(index, 'degC')
    assert_allclose(temps.values, [2.009619, 1.882443], rtol=10e-3, atol=10e-3)

    with pytest.raises(ValueError):
        mock_gsod_weather_source.indexed_temperatures(index, 'BAD')


def test_gsod_index_arbitrary(mock_gsod_weather_source):
    index = pd.DatetimeIndex(['2011-01-30', '2011-01-31', '2011-03-31'],
                             dtype='datetime64[ns, UTC]', freq=None)

    with pytest.raises(ValueError):
        mock_gsod_weather_source.indexed_temperatures(
            index, 'degF')

    temps = mock_gsod_weather_source.indexed_temperatures(
        index, 'degF', allow_mixed_frequency=True)

    assert temps.index.names == ["period", "daily"]
    assert temps.shape == (60, 1)


def test_bad_gsod_station():
    with pytest.raises(ValueError):
        GSODWeatherSource("INVALID")


def test_gsod_repr(mock_gsod_weather_source):
    assert str(mock_gsod_weather_source) == 'GSODWeatherSource("722880")'


@pytest.fixture
def mock_isd_weather_source():
    tmp_url = "sqlite:///{}/weather_cache.db".format(tempfile.mkdtemp())
    ws = ISDWeatherSource("722880", tmp_url)
    ws.client = MockWeatherClient()
    return ws


def test_isd_index_hourly(mock_isd_weather_source):
    index = pd.date_range('2011-01-01 00:00:00Z', periods=2, freq='H')
    temps = mock_isd_weather_source.indexed_temperatures(index, 'degF')
    assert all(temps.index == index)
    assert all(temps.index == index)
    assert temps.shape == (2,)
    assert_allclose(temps.values, [35.617314, 35.607637])


def test_isd_index_daily(mock_isd_weather_source):
    index = pd.date_range('2011-01-01 00:00:00Z', periods=2, freq='D')
    temps = mock_isd_weather_source.indexed_temperatures(index, 'degF')
    assert all(temps.index == index)
    assert all(temps.index == index)
    assert temps.shape == (2,)
    assert_allclose(temps.values, [35.507046, 35.281477])


def test_isd_index_arbitrary(mock_isd_weather_source):
    index = pd.DatetimeIndex(['2011-01-30', '2011-01-31', '2011-03-31'],
                             dtype='datetime64[ns, UTC]', freq=None)

    with pytest.raises(ValueError):
        temps = mock_isd_weather_source.indexed_temperatures(
            index, 'degF')

    temps = mock_isd_weather_source.indexed_temperatures(
        index, 'degF', allow_mixed_frequency=True)

    assert temps.index.names == ["period", "hourly"]
    assert temps.shape == (1440, 1)


def test_isd_index_arbitrary_single(mock_isd_weather_source):
    index = pd.DatetimeIndex(['2011-01-30'],
                             dtype='datetime64[ns, UTC]', freq=None)

    with pytest.raises(ValueError):
        mock_isd_weather_source.indexed_temperatures(index, 'degF')

    with pytest.raises(ValueError):
        mock_isd_weather_source.indexed_temperatures(
            index, 'degF', allow_mixed_frequency=True)


def test_bad_isd_station():
    with pytest.raises(ValueError):
        ISDWeatherSource("INVALID")


def test_isd_repr(mock_isd_weather_source):
    assert str(mock_isd_weather_source) == 'ISDWeatherSource("722880")'


def test_not_mocked():
    ws = ISDWeatherSource('722880')
    ws.add_year_range(2011, 2011)


def test_load_cached(monkeypatch):
    f = tempfile.NamedTemporaryFile()
    monkeypatch.setenv('EEMETER_WEATHER_CACHE_URL', 'sqlite:///{}'.format(f.name))

    ws = ISDWeatherSource('722880')
    ws.client = MockWeatherClient()
    assert ws.tempC.empty
    ws.add_year(2015)
    assert not ws.tempC.empty

    ws = ISDWeatherSource('722880')
    assert ws.tempC.empty
    ws.load_cached(2013, 2017)
    assert not ws.tempC.empty

    f.close()
