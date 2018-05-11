import datetime

def get_today_date_string():
        # Get the current date in yyyy-mm-dd format.
    return datetime.datetime.utcnow().strftime('%Y-%m-%d')