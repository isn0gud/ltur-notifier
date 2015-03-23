# -*- encoding: utf-8 *-*

#import datetime

# customize traveling specs
# mind that ltur offers bahn tickets only for the next 7 days starting from tomorrow
from_city = 'Berlin Hbf'
to_city = 'Augsburg Hbf'

# default to tomorrow
#on_date = ( datetime.date.today() + datetime.timedelta( days=1 )).strftime( '%d.%m.%Y' )
on_date = '25.03.2015'

at_time = '20:12'
max_price = 40.0

# set the mode of notification: pushover or email
# MODE = 'pushover'
MODE = 'email'

# Pushover config
APP_TOKEN   = 'EpMD3BrlmxioeKvGujVccccPqHeUxd'
USER_TOKEN  = ''
PUSHOVER_URL = "api.pushover.net"
PUSHOVER_PATH = "/1/messages.json"

# E-mail config
EMAIL = 'x@gmail.com'
FROM_EMAIL = 'x@gmail.com'
#gmail:
SMTP_SERVER = 'smtp.gmail.com'
# SMTP_SERVER = 'smtp.example.org'
SMTP_USER = 'x@gmail.com'  # optional
SMTP_PASS = 'x'  # optional



