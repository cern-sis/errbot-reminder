import os
import sys
from datetime import date, datetime

from freezegun import freeze_time

from reminder import Reminder

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(parent_dir)


@freeze_time("2026-2-14")
def test_get_monday():
    assert Reminder.get_monday(datetime.now()) == date(2026, 2, 9)


@freeze_time("2026-2-14")
def test_is_spring_planning():
    assert not Reminder.is_sprint_planning(datetime.now())


@freeze_time("2026-02-16")
def test_next_planning():
    test_date = datetime(2026, 2, 16, 15, 32)
    expected_result = datetime(2026, 3, 2, 15, 00).strftime(
        "**%Y-%m-%d** at **%H:%M**"
    )

    assert Reminder.next_occurance("sprint planning", test_date) == expected_result



@freeze_time("2026-02-16")
def test_next_retrospective_review():
    test_date = datetime(2026, 2, 16, 15, 32)
    expected_result = datetime(2026, 2, 27, 9, 30).strftime("**%Y-%m-%d** at **%H:%M**")

    assert Reminder.next_occurance("Retrospective and review", test_date) == expected_result


@freeze_time("2026-06-12 15:32", tz_offset=2)
def test_next_daily():
    test_date = datetime(2026, 6, 19, 15, 32)

    expected_result = datetime(2026, 6, 23, 9, 30).strftime("**%Y-%m-%d** at **%H:%M**")

    assert Reminder.next_daily(test_date) == expected_result


@freeze_time("2026-02-16")
def test_reminder_next():
    planning_content = datetime(2026, 2, 16, 15, 00)
    daily_content = datetime(2026, 2, 16, 9, 30)
    restrospective_review_content = datetime(2026, 2, 27, 9, 30).strftime(
        "**%Y-%m-%d** at **%H:%M**"
    )
    expected_response = "\n".join(
        [
            f"Next planning: {planning_content.strftime('**%Y-%m-%d** at **%H:%M**')}",
            f"Next daily: {daily_content.strftime('**%Y-%m-%d** at **%H:%M**')}",
            f"Next retrospective and review: {restrospective_review_content}",
        ]
    )
    assert Reminder.reminder_next(None, None, None) == expected_response
