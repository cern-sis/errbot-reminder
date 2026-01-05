from datetime import date, datetime, timedelta

import pytz
from errbot import BotPlugin, botcmd
import re
from openai import OpenAI
import httpx
import os
import random
# Daily / Retrospective --> If it's an ordinary day or a retrospective, meeting at 9:30
# Sprint Planning --> If it's a Sprint planning, meeting at 15:30
# Sprint review --> If it's a Sprint Review, meeting at 14:45

#  -----------------

utc = pytz.timezone("UTC")
now = utc.localize(datetime.utcnow())
tz_cern = pytz.timezone("Europe/Zurich")
now.astimezone(tz_cern)


EVENTS = {
    "sprint planning": (
        tz_cern.localize(datetime(2026, 1, 5, 15, 00)),
        timedelta(weeks=2),
    ),
    "review": (
        tz_cern.localize(datetime(2026, 1, 15, 15, 00)),
        timedelta(weeks=2),
    ),
    "Retrospective": (
        tz_cern.localize(datetime(2026, 1, 16, 9, 30)),
        timedelta(weeks=2),
    ),
    "daily": (
        tz_cern.localize(datetime(2026, 1, 5, 9, 30)),
        timedelta(days=1),
    ),
}

CONFIG = {
    "ts_stream_id":  311658,
    "zoom_url_regex":  re.compile('https://cern.zoom.us/j/\d+\?pwd=\w+'),
}


class Reminder(BotPlugin):
    @staticmethod
    def get_monday(today):
        today_weekday = today.weekday()
        monday = today.date() - timedelta(days=today_weekday)
        monday = datetime.combine(monday, datetime.min.time())
        return monday.date()

    @staticmethod
    def is_sprint_planning(today):
        first_iteration_startdate = date(2026, 1, 5)
        nb_days = (first_iteration_startdate - Reminder.get_monday(today)).days
        nb_weeks = nb_days // 7

        return nb_weeks % 2 == 0

    @staticmethod
    def next_occurance(meeting, today):
        today = tz_cern.localize(today)
        next_occurance = EVENTS.get(meeting)[0].astimezone(tz_cern)
        delta_occurance = EVENTS.get(meeting)[1]

        while next_occurance <= today:
            next_occurance += delta_occurance

        if next_occurance > today:
            return next_occurance.strftime("**%Y-%m-%d** at **%H:%M**")

    @staticmethod
    def next_daily(today):
        today = tz_cern.localize(today)
        next_daily = EVENTS.get("daily")[0].astimezone(tz_cern)
        delta_daily = EVENTS.get("daily")[1]

        while next_daily <= today:
            next_daily += delta_daily

            if Reminder.is_sprint_planning(today):
                if next_daily.weekday() == 0:
                    next_daily += delta_daily

                if next_daily.weekday() >= 5:
                    next_daily += timedelta(days=(7 - next_daily.weekday()))

            else:
                if next_daily.weekday() >= 3:
                    next_daily += timedelta(days=(7 - next_daily.weekday() + 1))

        return next_daily.strftime("**%Y-%m-%d** at **%H:%M**")

    @staticmethod
    def get_openai_message(meeting_type, zoom_link, time_until_meeting):
        character = ["Marvin from Hitchhiker's Guide To The Galaxy."]
        client = OpenAI(timeout=httpx.Timeout(15.0, read=5.0, write=10.0, connect=3.0), api_key=os.environ.get("OPENAI_API_KEY"),)
        prompt = (
            f"You are a chatbot that announces the next meeting."
            f"Your character is {random.choice(character)}."
            f"The meeting is happening in {time_until_meeting} minutes and it is a {meeting_type} meeting. "
            "Create a short text message for this announcement."
        )
        response = client.chat.completions.create(
            model="gpt-5.1",
            messages=[
                {"role": "system", "content": prompt}
            ],
            max_tokens=50
        )
        message_content = response.choices[0].message.content.strip()
        final_message = f"@**all** {message_content} \n\n [meeting]({zoom_link})."
        return final_message

    def zoom_meeting_url(self):
        client = self._bot.client
        # Get stream by id is currently not available on the python client.
        response = client.get_streams(
            include_public = False,
        )

        stream = next(filter(
            lambda s: s["stream_id"] == CONFIG["ts_stream_id"],
            response["streams"],
        ))
        match = CONFIG["zoom_url_regex"].search(stream["description"])

        return match.group()

    @botcmd
    def test_ai_message(self, msg, args):
        return Reminder.get_openai_message("daily", "abc", 5)
    
    @botcmd
    def reminder_link(self, msg, args):
        return f"[Link]({self.zoom_meeting_url()}) to our Zoom meeting"

    @botcmd
    def reminder_next(self, msg, args):
        today = datetime.now()
        next_planning = Reminder.next_occurance("sprint planning", today)
        next_daily = Reminder.next_daily(today)
        next_review = Reminder.next_occurance("review", today)
        next_retrospective = Reminder.next_occurance("Retrospective", today)
        return "\n".join(
            [
                f"Next planning: {next_planning}",
                f"Next daily: {next_daily}",
                f"Next review: {next_review}",
                f"Next retrospective: {next_retrospective}",
            ]
        )

    def send_notification(self, meeting, today):
        client = self._bot.client
        next_occurance = EVENTS.get(meeting)[0]
        delta_occurance = EVENTS.get(meeting)[1]

        while next_occurance <= today:
            next_occurance += delta_occurance

        if next_occurance > today:
            if next_occurance.date() == today.date():
                now_minus_15 = (next_occurance - timedelta(minutes=15)).time()
                now_minus_5 = (next_occurance - timedelta(minutes=5)).time()

                zoom_link = self.zoom_meeting_url()

                if now_minus_15 == today.time():
                    client.send_message(
                        {
                            "type": "stream",
                            "to": "tools & services",
                            "topic": meeting,
                            "content": f"@**all** [meeting]({zoom_link}) in 15 minutes.",
                        }
                    )

                if now_minus_5 == today.time():
                    try:
                        content = Reminder.get_openai_message(meeting, zoom_link, 5)
                    except Exception:
                        content = f"@**all** [meeting]({zoom_link}) in 5 minutes."
                    
                    client.send_message(
                        {
                            "type": "stream",
                            "to": "tools & services",
                            "topic": meeting,
                            "content": content,
                        }
                    )

    def notify_for_meetings(self):
        today = (datetime.now().astimezone(tz_cern)).replace(second=0, microsecond=0)
        weekday = today.weekday()

        if weekday < 5:
            if weekday == 0 and self.is_sprint_planning(today):
                self.send_notification("sprint planning", today)

            elif weekday == 4 and not self.is_sprint_planning(today):
                self.send_notification("Retrospective", today)

            elif weekday == 3 and not self.is_sprint_planning(today):
                self.send_notification("daily", today)
                self.send_notification("review", today)

            else:
                self.send_notification("daily", today)

    def activate(self):
        super().activate()
        self.start_poller(60, self.notify_for_meetings)
