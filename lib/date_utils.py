from datetime import datetime, timedelta, timezone


def get_today_date_string():
    # Get the current date in yyyy-mm-dd format.
    return datetime.now(timezone.utc).strftime('%Y-%m-%d')


def get_current_hour():
    return datetime.now(timezone.utc).hour


def get_unix_time_range_for_hour():
    current_time = datetime.now(timezone.utc)

    start_of_hour = datetime(current_time.year,
                             current_time.month,
                             current_time.day,
                             current_time.hour,
                             minute=0,
                             second=0,
                             microsecond=0,
                             tzinfo=timezone.utc)

    end_of_hour = start_of_hour + timedelta(hours=1)

    return int(start_of_hour.timestamp()), int(end_of_hour.timestamp())


def get_current_unix_time():
    return int(datetime.utcnow().timestamp())


def add_days_to_current_time(days_to_add: int):
    current_time = datetime.now(timezone.utc)
    result = current_time + timedelta(days=days_to_add)

    return int(result.timestamp())
