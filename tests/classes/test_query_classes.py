# pylint: disable=missing-function-docstring, missing-module-docstring

from pytest import CaptureFixture

from classes.query_classes import QueryBuilder
from tests.config.consts import FAKE


def test_passes_help_string(capsys: CaptureFixture):
    bucket = FAKE.pystr()
    start_range = FAKE.date_between(start_date=-30)

    query_builder = QueryBuilder(bucket=bucket, start_range=start_range)
    query_builder.help()
    captured = capsys.readouterr()

    assert captured.out != ""


def test_passes_basic_query_created():
    bucket = FAKE.pystr()
    start_range = FAKE.date_between(start_date=-30)

    query_builder = QueryBuilder(bucket=bucket, start_range=start_range)

    assert (
        str(query_builder)
        == f'from(bucket: "{bucket}")\n\t|> range(start: {start_range})'
    )


def test_passes_query_with_end_date():
    bucket = FAKE.pystr()
    start_range = FAKE.date_between(start_date=-30, end_date=-15)
    end_range = FAKE.date_between(start_date=-16)

    query_builder = QueryBuilder(
        bucket=bucket, start_range=start_range, end_range=end_range
    )

    assert (
        str(query_builder) == f'from(bucket: "{bucket}")'
        f"\n\t|> range(start: {start_range}, stop: {end_range})"
    )


def test_passes_query_with_filter():
    bucket = FAKE.pystr()
    start_range = FAKE.date_between(start_date=-30)
    field = FAKE.pystr()
    value = FAKE.pystr()

    query_builder = QueryBuilder(bucket=bucket, start_range=start_range)
    query_builder.append_filter(field=field, value=value)

    assert (
        str(query_builder) == f'from(bucket: "{bucket}")'
        f"\n\t|> range(start: {start_range})"
        f'\n\t|> filter(fn: (r) => r["{field}"] == "{value}")'
    )


def test_passes_query_filter_with_join():
    bucket = FAKE.pystr()
    start_range = FAKE.date_between(start_date=-30)
    field = FAKE.pystr()
    value = FAKE.pystr()
    joiner = FAKE.random_element(elements=["And", "Or"])

    query_builder = QueryBuilder(bucket=bucket, start_range=start_range)
    query_builder.append_filter(field=field, value=value, joiner=joiner)

    assert (
        str(query_builder) == f'from(bucket: "{bucket}")'
        f"\n\t|> range(start: {start_range})"
        f'\n\t|> filter(fn: (r) => r["{field}"] == "{value}" {joiner} '
    )


def test_passes_query_filter_with_band():
    bucket = FAKE.pystr()
    start_range = FAKE.date_between(start_date=-30)
    field_1 = FAKE.pystr()
    value_1 = FAKE.pystr()
    field_2 = FAKE.pystr()
    value_2 = FAKE.pystr()

    query_builder = QueryBuilder(bucket=bucket, start_range=start_range)
    query_builder.append_filter(
        field=field_1,
        value=value_1,
    )
    query_builder.append_filter(field=field_2, value=value_2, new_band=True)

    assert (
        str(query_builder) == f'from(bucket: "{bucket}")'
        f"\n\t|> range(start: {start_range})"
        f'\n\t|> filter(fn: (r) => r["{field_1}"] == "{value_1}")'
        f'\n\t|> filter(fn: (r) => r["{field_2}"] == "{value_2}")'
    )


def test_passes_query_with_aggregate():
    bucket = FAKE.pystr()
    start_range = FAKE.date_between(start_date=-30)
    collection_window = FAKE.pystr()
    aggregate_function = FAKE.pystr()

    query_builder = QueryBuilder(bucket=bucket, start_range=start_range)
    query_builder.append_aggregate(
        collection_window=collection_window, aggregate_function=aggregate_function
    )

    assert (
        str(query_builder) == f'from(bucket: "{bucket}")'
        f"\n\t|> range(start: {start_range})"
        f"\n\t|> aggregateWindow(every:"
        f" {collection_window}, fn: {aggregate_function}"
    )


def test_passes_query_with_sort():
    bucket = FAKE.pystr()
    start_range = FAKE.date_between(start_date=-30)
    field = FAKE.pystr()
    desc = FAKE.pybool()

    query_builder = QueryBuilder(bucket=bucket, start_range=start_range)
    query_builder.append_sort(field=field, desc=desc)

    assert (
        str(query_builder) == f'from(bucket: "{bucket}")'
        f"\n\t|> range(start: {start_range})"
        f'\n\t|> sort(columns: ["{field}"], desc: {desc}'
    )
