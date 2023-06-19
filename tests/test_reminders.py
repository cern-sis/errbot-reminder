import os
import sys
from datetime import date, datetime

from freezegun import freeze_time

from reminder import Reminder

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(parent_dir)


@freeze_time("2023-06-15")
def test_get_monday():
    test_date = date(2023, 6, 15)
    assert Reminder.get_monday(test_date) == date(2023, 6, 12)


@freeze_time("2023-06-12")
def test_is_spring_planning():
    assert not Reminder.is_sprint_planning()


@freeze_time("2023-06-12")
def test_next_planning():
    test_date = datetime(2023, 6, 12, 15, 32)
    expected_result = datetime(2023, 6, 19, 15, 30).strftime(
        "**%Y-%m-%d** at **%H:%M**"
    )

    assert Reminder.next_occurance("Sprint planning", test_date) == expected_result


@freeze_time("2023-06-12")
def test_next_review():
    test_date = datetime(2023, 6, 12, 15, 32)
    expected_result = datetime(2023, 6, 15, 14, 45).strftime(
        "**%Y-%m-%d** at **%H:%M**"
    )

    assert Reminder.next_occurance("Sprint review", test_date) == expected_result


@freeze_time("2023-06-12")
def test_next_retrospective():
    test_date = datetime(2023, 6, 12, 15, 32)
    expected_result = datetime(2023, 6, 16, 9, 30).strftime("**%Y-%m-%d** at **%H:%M**")

    assert Reminder.next_occurance("Sprint retrospective", test_date) == expected_result


@freeze_time("2023-06-12 15:32", tz_offset=2)
def test_next_daily():
    test_date = datetime(2023, 6, 12, 15, 32)

    expected_result = datetime(2023, 6, 13, 9, 30).strftime("**%Y-%m-%d** at **%H:%M**")

    assert Reminder.next_daily(test_date) == expected_result


@freeze_time("2023-06-12")
def test_reminder_next():
    planning_content = datetime(2023, 6, 19, 15, 30)
    daily_content = datetime(2023, 6, 13, 9, 30)
    review_content = datetime(2023, 6, 15, 14, 45)
    restrospective_content = datetime(2023, 6, 16, 9, 30).strftime(
        "**%Y-%m-%d** at **%H:%M**"
    )
    expected_response = "\n".join(
        [
            f"Next planning: {planning_content.strftime('**%Y-%m-%d** at **%H:%M**')}",
            f"Next daily: {daily_content.strftime('**%Y-%m-%d** at **%H:%M**')}",
            f"Next review: {review_content.strftime('**%Y-%m-%d** at **%H:%M**')}",
            f"Next retrospective: {restrospective_content}",
        ]
    )
    assert Reminder.reminder_next(None, None, None) == expected_response
