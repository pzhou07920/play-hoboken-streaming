import random
from datetime import date, datetime

def generate_access_code(length=4):
    # get todays date
    today = date.today()
    print("Today's date:", today)
    # add a time to today where time is 00:00:00
    today_midnight = datetime.combine(today, datetime.min.time())
    epoch_time = today_midnight.timestamp()
    print("Epoch time for today's date:", epoch_time)
    # seed the random number generator with today's date

    random.seed(epoch_time)
    return ''.join(random.choices('0123456789', k=length))