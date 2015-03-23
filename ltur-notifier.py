#! /usr/bin/env python
# -*- encoding: utf-8 -*-

import httplib
import urllib
import sys
import re
import datetime

from mechanize import Browser
from bs4 import BeautifulSoup

from config import *




# ltur's Bahn webpagde: journey form (dynamically loaded after page load via AJAX)
user_url = 'http://www.ltur.com/de/bahn.html?omnin=DB-DE'
scraper_url = 'http://bahn.ltur.com/ltb/searchform/external'
#
# keywords for webscraping
# TRIGGER = [
# 'price_Fernweh_H',      # really cheap prices
# 'price_Sparpreis_H'     # medium cheap prices...
# ]

PRICE_TAG_REGEX = u'([0-9]{1,3}(,|.)?([0-9]{1,2}))?\s*€?'

# TODO: error handling
# (1) if on_date - today > 7, inform user

def main():
    def to_date(date_string):
        date_split = date_string.split('.')
        return datetime.date(int(date_split[2]), int(date_split[1]), int(date_split[0]))

    days_between = (to_date(latest_date) - to_date(earliest_date)).days

    entries = []
    for dayCount in range(0, days_between + 1):
        day = to_date(earliest_date) + datetime.timedelta(dayCount)
        for dayUnit in range(0, 3):
            current = datetime.datetime(day.year, day.month, day.day) + datetime.timedelta(0, 0, 0, 0, 0, 8 * dayUnit)
            current_date = current.strftime("%d.%m.%Y")
            current_time = current.strftime("%H:%M")
            # print(current.isoformat() + " [OK]")
            entries.extend(parse_cheap_entries(submit_form(current_date, current_time)))
    cheap_entries = [elem for elem in entries if elem['price'] < max_price] # filter(lambda x: x['price'] > max_price, entries)
    cheapest = max_price
    for entry in cheap_entries:
        if entry['price'] < cheapest:
            cheapest = entry['price']
    if cheapest < max_price:
        if MODE == 'pushover':
            send_pushover(cheapest)
        elif MODE == 'email':
            send_mail(cheap_entries, cheapest)


def submit_form(on_date, at_time):
    br = Browser()  # create browser instance
    response = br.open(scraper_url)  # load page

    # hack
    rp_data = response.get_data()
    rp_data = re.sub(r'<optgroup label=".+">', "", rp_data)  # replace all optgroup elements
    response.set_data(rp_data)
    br.set_response(response)
    # eohack

    br.select_form(name='form_spar_topz')

    # fill in custom values
    br['from'] = from_city
    br['to_spar'] = to_city
    br.form.find_control('fromDate').readonly = False
    br['fromDate'] = on_date
    br['fromTime'] = at_time

    return br.submit()


# Entry Tuple (fromCity,departureTime,toCity,arrivalTime,via[],price)
def parse_cheap_entries(page):
    soup = BeautifulSoup(page)

    entries = soup.find_all('tr', ['even', 'odd'])

    def is_sub_class(tag):
        return 'subinfotop' in tag['class'] or 'subinfobottem' in tag['class']

    def is_cheap_entry(entry):
        is_cheap = False
        for elem in entry.find_all('td'):
            if 'price_Fernweh_H' in elem['class'] or 'price_Sparpreis_H' in elem['class']:
                is_cheap = True
        return is_cheap

    filtered_entries = []
    for entry in entries:
        if not entry.has_attr('style') and not is_sub_class(entry):
            if is_cheap_entry(entry):
                filtered_entries.append(entry)

    beautified_entries = []
    for entry in filtered_entries:
        elements = entry.find_all('td')
        ticket = dict()
        ticket['departure_date'] = elements[1].text.strip()[0:11]
        ticket['arrival_date'] = elements[1].text.strip()[11:22]
        ticket['departure_time'] = elements[2].text[0:5]
        ticket['arrival_time'] = elements[2].text[5:10]
        ticket['travel_time'] = elements[3].text

        price_string = elements[5].text.strip()
        match = re.match(PRICE_TAG_REGEX, unicode(price_string))
        if match:
            price = match.group(1)
            price = re.sub(',', '.', price)
            ticket['price'] = float(price)

        beautified_entries.append(ticket)

    return beautified_entries


# def parse_page(haystack, needles):
# bs = BeautifulSoup(haystack)
# gems = []
# price_tags = []
# for needle in needles:
# price_tags.extend(bs.find_all('td', attrs={'class': needle}))
#
# for price_tag in price_tags:
#         price_string = price_tag.get_text().strip()
#         match = re.match(PRICE_TAG_REGEX, unicode(price_string))
#         if match:
#             price = match.group(1)
#             price = re.sub(',', '.', price)
#             gems.append(float(price))
#     return gems


def send_pushover(cheapest):
    if not USER_TOKEN:
        print( "You have to configure your Pushover user token in config.py for this to work." )
        sys.exit()
    conn = httplib.HTTPSConnection(PUSHOVER_URL)
    conn.request('POST', PUSHOVER_PATH,
                 urllib.urlencode({
                     'title': '( : ltur für ' + str(cheapest) + ' ',
                     'token': APP_TOKEN,
                     'user': USER_TOKEN,
                     'message': ')',
                 }), {'Content-type': 'application/x-www-form-urlencoded'})

    # for debugging
    res = conn.getresponse()
    conn.close()


def send_mail(entries, cheapest):
    preparedMsg = "Train rides form " + from_city + " to " + to_city + ":\n\n"
    preparedMsg += "departure\t\tarrival\t\t\t\ttravel time\tprice\n"
    for entry in entries:
        preparedMsg += entry['departure_date'] + "\t\t" + entry['arrival_date'] + "\n" + \
                       entry['departure_time'] + "\t\t\t" + entry['arrival_time'] + "\t\t\t\t" + entry['travel_time'] + \
                       "\t\t" + str(entry['price']) + " Euro\n\n"
    preparedMsg += "\n" + user_url

    import smtplib
    from email.mime.text import MIMEText

    # Create a text/plain message
    msg = MIMEText(preparedMsg)
    msg['Subject'] = 'Ltur Notifier ' + str(cheapest) + " Euro"
    msg['From'] = FROM_EMAIL
    msg['To'] = EMAIL

    s = smtplib.SMTP(SMTP_SERVER)
    if SMTP_USER and SMTP_PASS:
        s.ehlo()
        s.starttls()
        s.ehlo()
        s.login(SMTP_USER, SMTP_PASS)
    s.sendmail(msg['From'], [msg['To']], msg.as_string())
    s.quit()


if __name__ == '__main__':
    main()
