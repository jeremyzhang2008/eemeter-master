from datetime import datetime
import pytz

from eemeter.processors.interventions import get_modeling_period_set
from eemeter.structures import Intervention


def test_empty():
    mps = get_modeling_period_set([])
    assert mps is None


def test_basic_usage():
    start_date = datetime(2000, 1, 1, tzinfo=pytz.UTC)
    end_date = datetime(2001, 1, 1, tzinfo=pytz.UTC)
    interventions = [Intervention(start_date, end_date)]

    mps = get_modeling_period_set(interventions)

    groups = list(mps.iter_modeling_period_groups())
    assert len(groups) == 1
    labels, periods = groups[0]
    assert labels == ('baseline', 'reporting')
    assert periods[0].start_date is None
    assert periods[0].end_date is start_date
    assert periods[1].start_date is end_date
    assert periods[1].end_date is None

    modeling_periods = list(mps.iter_modeling_periods())
    assert len(modeling_periods) == 2
