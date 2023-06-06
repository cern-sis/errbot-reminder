from datetime import date, datetime

from freezegun import freeze_time

from reminder import Reminder


@freeze_time("2023-06-15")
def test_get_monday():
    test_date = date(2023, 6, 15)
    assert Reminder().get_monday(test_date) == date(2023, 6, 12)


@freeze_time("2023-06-12")
def test_is_spring_planning():
    assert not Reminder().is_sprint_planning()


@freeze_time("2023-06-12")
def test_next_planning():
    assert Reminder().next_occurance("Sprint planning") == datetime(2023, 6, 19, 15, 30)


@freeze_time("2023-06-12")
def test_next_review():
    assert Reminder().next_occurance("Sprint review") == datetime(2023, 6, 15, 14, 45)


@freeze_time("2023-06-12")
def test_next_retrospective():
    assert Reminder().next_occurance("Sprint restrospective") == datetime(
        2023, 6, 16, 9, 30
    )


@freeze_time("2023-06-12")
def test_next_daily():
    test_date = datetime(2023, 6, 12, 15, 32)
    assert Reminder().next_daily(test_date) == datetime(2023, 6, 13, 9, 30)


@freeze_time("2023-06-12")
def test_reminder_next():
    assert Reminder().reminder_next() == "\n".join(
        f"Next planning: {datetime(2023, 6, 19, 15, 30)}",
        f"Next daily: {datetime(2023, 6, 13, 9, 30)}",
        f"Next review: {datetime(2023, 6, 15, 14, 45)}"
        f"Next retrospective: {datetime(2023, 6, 16, 9, 30)}",
    )
