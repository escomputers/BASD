#!/usr/bin/env python3.9

from unicorn_binance_websocket_api.manager import BinanceWebSocketApiManager
import unicorn_fy
from unicorn_binance_rest_api.manager import BinanceRestApiManager

import time as tempo
from decimal import Decimal
import logging
import pytz
import threading
import os
import smtplib
import ssl
from datetime import datetime, time, timedelta

from binance.spot import Spot as Client
from binance.error import ClientError

from getpass import getpass
from tabulate import tabulate

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from jinja2 import Environment, FileSystemLoader

# LOG FILE
logging.getLogger('unicorn_binance_websocket_api')
logging.basicConfig(
    level=logging.INFO,
    filename=os.path.basename(__file__) + '.log',
    format='{asctime} [{levelname:8}] {process} {thread} {module}: {message}',
    style='{'
)


# reset all inputs
def reset_inputs():
    for element in dir():
        if element[0:2] != "__":
            del globals()[element]
    del element


# get LAST PRICE via rest api
def get_last_pr(stream_dt):
    ubra = BinanceRestApiManager(api_key, api_secret, exchange="binance.com")
    last_symbol_data = ubra.get_ticker(
        symbol=stream_dt['symbol']
    )
    last_pr = float(last_symbol_data['lastPrice'])
    return last_pr


# PLACE ORDER
def place_new_order(stream_dt):

    # order_pr = float(stream_dt['order_price'])
    order_pr = 19556.02

    # OCO order
    if 'y' in is_oco.lower():

        # TAKE PROFIT price
        profit_pr = round(
            (order_pr + round(((order_pr / 100) * profit_pct), 8)), 2
        )

        # STOP LOSS price
        sl_pr_oco = round(
            (
                order_pr - round(
                    ((order_pr / 100) * sl_oco_pct), 8
                )
            ), 2
        )

        # LIMIT PRICE
        sl_lmt_pr_oco = round(
            (
                order_pr - round(
                    ((order_pr / 100) * sl_lmt_oco_pct), 8
                )
            ), 2
        )

        # new order
        params = {
            'symbol': stream_dt['symbol'],
            'side': 'SELL',
            'stopLimitTimeInForce': 'GTC',
            # 'quantity': stream_dt['order_quantity'],
            'quantity': 0.00119,
            'price': str(profit_pr),
            'stopPrice': str(sl_pr_oco),
            'stopLimitPrice': str(sl_lmt_pr_oco)

        }

        client = Client(
            api_key, api_secret, base_url='https://api.binance.com'
        )

        '''
        OCO SELL rule = Limit Price > Last Price > Stop Price
        OCO BUY rule  = Limit Price < Last Price < Stop Price
        '''

        # get LAST SYMBOL PRICE
        last_pr = get_last_pr(stream_dt)

        # if stop and limit prices respect OCO rules, place orders
        if last_pr > sl_pr_oco and last_pr < sl_lmt_pr_oco:

            try:
                response = client.new_oco_order(**params)
                mail_notification(response)

            except ClientError as error:
                logging.info(response)
                logging.error(
                    error.status_code,
                    error.error_code,
                    error.error_message
                )
                mail_notification(response)
        else:
            print(
                ' [ERROR] Prices relationship for the orders not correct.' +
                '\n' +
                ' OCO SELL rule = Limit Price > Last Price > Stop Price'
            )

    # non OCO orders
    else:
        # TAKE PROFIT order
        if 'n' in is_sl_order:

            # LIMIT PROFIT price
            lmt_profit_pr = round(
                (order_pr + round(((order_pr / 100) * lmt_profit_pct), 8)), 2
            )

            # STOP PROFIT price
            stop_pr = round(
                (order_pr + round(((order_pr / 100) * stop_profit_pct), 8)), 2
            )

            # new order
            params = {
                'symbol': stream_dt['symbol'],
                'side': 'SELL',
                'type': 'TAKE_PROFIT_LIMIT',
                'timeInForce': 'GTC',
                # 'quantity': stream_dt['order_quantity'],
                'quantity': 0.00119,
                'price': str(lmt_profit_pr),
                'stopPrice': str(stop_pr),

            }

            client = Client(
                api_key, api_secret, base_url='https://api.binance.com'
            )

            try:
                response = client.new_order(**params)
                mail_notification(response)

            except ClientError as error:
                response = logging.error(
                    error.status_code,
                    error.error_code,
                    error.error_message
                )
                mail_notification(response)

        # STOP LOSS order
        else:

            # STOP LOSS LIMIT price
            lmt_loss_pr = round(
                (order_pr - round(((order_pr / 100) * lmt_loss_pct), 8)), 2
            )

            # STOP LOSS price
            sl_pr = round(
                (order_pr - round(((order_pr / 100) * sl_pct), 8)), 2
            )

            # new order
            params = {
                'symbol': stream_dt['symbol'],
                'side': 'SELL',
                'type': 'STOP_LOSS_LIMIT',
                'timeInForce': 'GTC',
                # 'quantity': stream_dt['order_quantity'],
                'quantity': 0.00119,
                'price': str(lmt_loss_pr),
                'stopPrice': str(sl_pr),

            }

            client = Client(
                api_key, api_secret, base_url='https://api.binance.com'
            )

            try:
                response = client.new_order(**params)
                mail_notification(response)

            except ClientError as error:
                logging.info(response)
                logging.error(
                    error.status_code,
                    error.error_code,
                    error.error_message
                )
                mail_notification(response)


# CHECK FOR TRADES
def print_stream_data_from_stream_buffer(binance_websocket_api_manager):

    while True:
        if binance_websocket_api_manager.is_manager_stopping():
            exit(0)
            
        old_stream_dt_buff = binance_websocket_api_manager.pop_stream_data_from_stream_buffer()

        if old_stream_dt_buff is False:
            tempo.sleep(0.01)
        else:

            # get data from stream and convert to dictionary
            unicornfy = unicorn_fy.UnicornFy()
            stream_dt = unicornfy.binance_com_websocket(old_stream_dt_buff)

            # get order status
            try:
                order_status = stream_dt['current_order_status']
                if order_status == 'CANCELED':
                    place_new_order(stream_dt)
            except KeyError:
                continue


# CONNECT TO BINANCE.COM
def check_filled_orders():
    # create instances of BinanceWebSocketApiManager
    ws_cnn = BinanceWebSocketApiManager(exchange='binance.com')

    # create the userData streams
    user_stream_id = ws_cnn.create_stream(
        'arr', '!userData', api_key=api_key, api_secret=api_secret
    )

    # start a worker to move data from the stream_buffer to a print func
    worker_thread = threading.Thread(
        target=print_stream_data_from_stream_buffer, args=(ws_cnn,)
    )

    worker_thread.start()

    # monitor the streams
    while True:
        ws_cnn.print_stream_info(user_stream_id)

        # set here refresh interval
        tempo.sleep(refresh_ival)


# CHECK TIME
def check_time():
    # every 5 secs
    threading.Timer(refresh_ival, check_time).start()

    # get time zone of specified location
    tmzone = pytz.timezone(usr_tz)

    # change current time accordingly
    now = (datetime.now(tmzone))

    # check if it's time to work or not
    if now.time() >= user_start_time and now.time() <= user_end_time:
        # yes
        check_filled_orders()
    else:
        check_filled_orders()


# VALIDATION
def is_working_ival(input):
    try:
        input = int(input)
        if input >= 1 and input <= 24:
            return input
        else:
            print(' [ERROR] Type a valid value between 1 and 24')
    except ValueError:
        print(' [ERROR] Type only numbers')


def is_mins(input):
    if not input:
        return '00'
    else:
        try:
            input = int(input)
            if input >= 1 and input <= 59:
                return input
            else:
                print(' [ERROR] Type a valid value between 1 and 59')
        except ValueError:
            print(' [ERROR] Type only numbers')


def is_hour(input):
    try:
        input = int(input)
        if input >= 1 and input <= 24:
            return input
        else:
            print(' [ERROR] Type a valid value between 1 and 24')
    except ValueError:
        print(' [ERROR] Type only numbers')


def is_int(input):
    try:
        input = int(input)
        if input >= 1 and input <= 86400:
            return input
        else:
            print(' [ERROR] Type a valid value between 1 and 86400')
    except ValueError:
        print(' [ERROR] Type only numbers')


def is_float(input):
    try:
        input = float(input)
        if input >= 0.05 and input <= 2999.99:
            return input
        else:
            print(' [ERROR] Type a valid value between 0.05 and 2999.99')
    except ValueError:
        print(' [ERROR] Type only numbers')


# CONSTRUCT USER TIME
def construct_user_time(start_hour, start_mins, working_ival):
    # construct user start working time
    user_start_time_str = str(start_hour) + ':' + str(start_mins)
    user_start_time = datetime.strptime(user_start_time_str, '%H:%M').time()
    # construct user end working time
    user_end_time = (
        datetime.strptime(user_start_time_str, '%H:%M') +
        timedelta(hours=working_ival)
    ).time()
    return user_start_time, user_end_time


# MAIL
def mail_notification(response):
    sender_email = "emilianos13@gmail.com"
    receiver_email = "emilianos13@gmail.com"
    password = "ipxhsmhiembjrynb"

    message = MIMEMultipart("alternative")
    message["Subject"] = "[BASD] Binance Algorithmic Stop Notification"
    message["From"] = sender_email
    message["To"] = receiver_email

    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('mail.html')

    if 'error' in response.keys() or 'error' in response.values():
        title = 'Caution!: order NOT PLACED'
    else:
        title = 'Success!: order PLACED'

    html = template.render(title=title, msg=response)

    part = MIMEText(html, "html")

    # Add HTML/plain-text parts to MIMEMultipart message
    # The email client will try to render the last part first
    message.attach(part)

    # Create secure connection with server and send email
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(
            sender_email, receiver_email, message.as_string()
        )


# MAIN
while True:
    # COLLECT INPUTS FROM USER
    print()
    tempo.sleep(1)
    print(
        '[INFO] Welcome to BASD - Binance Algorithmic Stop Daemon...' +
        '\n' + '[INFO] DISCLAIMER' +
        '\n' + '[WARN] This software comes with no warranty.' +
        '\n' + '[WARN] You have the whole responsability for profits or losses'
    )
    print()

    # get api key
    api_key = getpass(prompt='Type or paste your Binance.com API KEY: ')
    if len(api_key) < 64:
        print(
            ' [ERROR] Check your API KEY, 64 characters minimum, no spaces'
        )
    else:
        # get api secret key
        api_secret = getpass(
            prompt='Type or paste your Binance.com SECRET KEY: '
        )
        if len(api_secret) < 64:
            print(
                ' [ERROR] Check your API KEY, 64 characters minimum, no spaces'
            )
        else:
            # get timezone continet
            tz_cont = input(
                'Type your CONTINENT (IANA timezone format), e.g. Europe: '
            )
            if tz_cont.isalpha():

                # get timezone city
                tz_city = input(
                    'Type your CITY (IANA timezone format), e.g. Rome: '
                )
                if tz_city.isalpha():
                    usr_tz = tz_cont.capitalize() + '/' + tz_city.capitalize()

                    # validate timezone
                    if usr_tz in pytz.all_timezones:

                        # get start hour
                        inp_start_hour = input(
                            'Type START HOUR (1-24), e.g. 23: '
                        )
                        if is_hour(inp_start_hour):
                            start_hour = is_hour(inp_start_hour)

                            # get start minutes
                            inp_start_mins = input(
                                'Type START MINUTES (0-59).' +
                                'Leave it blank for 0 minutes, e.g. 30: '
                            )
                            if is_mins(inp_start_mins):
                                start_mins = is_mins(inp_start_mins)

                                # get working interval
                                inp_working_ival = input(
                                    'Type how many working HOURS you want.' +
                                    '24 equals to all day, e.g. 8: '
                                )
                                if is_working_ival(inp_working_ival):
                                    working_ival = is_working_ival(inp_working_ival)

                                    # get refresh_ival
                                    inp_refresh_ival = input(
                                        'Type how much time in SECONDS' +
                                        'before controlling again, e.g. 3: '
                                    )
                                    if is_int(inp_refresh_ival):
                                        refresh_ival = is_int(inp_refresh_ival)

                                        # get OCO choice
                                        is_oco = input(
                                            'Do you want OCO orders?' +
                                            'Type yes or no: '
                                        )

                                        # OCO orders
                                        if 'yes' in is_oco.lower():

                                            # get PROFIT percentage
                                            inp_profit_pct = input(
                                                'Type PROFIT percentage,' +
                                                'e.g. 5.20: '
                                            )
                                            if is_float(inp_profit_pct):
                                                profit_pct = is_float(inp_profit_pct)

                                                # get STOP LOSS percentage
                                                inp_sl_oco_pct = input(
                                                    'Type STOP LOSS' +
                                                    'percentage. This' +
                                                    'should be LOWER' +
                                                    'than symbol market' +
                                                    'price WHEN order' +
                                                    'will be placed,' +
                                                    'e.g. 1.20: '
                                                )
                                                if is_float(inp_sl_oco_pct):
                                                    sl_oco_pct = is_float(inp_sl_oco_pct)

                                                    # get SL LIMIT percentage
                                                    inp_sl_lmt_oco_pct = input(
                                                        'Type STOP LOSS' +
                                                        'LIMIT percentage.' +
                                                        'This should be' +
                                                        'HIGHER than' +
                                                        'symbol market' +
                                                        'price WHEN order' +
                                                        'will be placed,' +
                                                        'e.g. 1.00: '
                                                    )
                                                    if is_float(inp_sl_lmt_oco_pct):
                                                        sl_lmt_oco_pct = is_float(inp_sl_lmt_oco_pct)

                                                        # get user time
                                                        user_start_time, user_end_time = construct_user_time(
                                                            start_hour, start_mins, working_ival
                                                        )

                                                        tabledata = [
                                                            ['Timezone', usr_tz],
                                                            ['Start Time', 'everyday at: ' + str(user_start_time)],
                                                            ['End Time', 'everyday at: ' + str(user_end_time)],
                                                            ['Refresh Interval', str(refresh_ival) + 'secs'],
                                                            ['OCO order', 'YES'],
                                                            ['Take Profit Percentage', '+' + str(profit_pct) + '%'],
                                                            ['Stop Loss Percentage', '-' + str(sl_oco_pct) + '%'],
                                                            ['Stop Loss Limit Percentage', '-' + str(sl_lmt_oco_pct) + '%']
                                                        ]
                                                        print(tabulate(tabledata, headers=['Key', 'Value']))

                                                        # get data confirmation
                                                        confirm = input(
                                                            'Type yes to confirm all data above is correct: '
                                                        )
                                                        if 'yes' in confirm.lower():
                                                            # end data collection
                                                            check_time()
                                                        elif 'no' in confirm.lower():
                                                            # restart from the beginning
                                                            continue
                                                            reset_inputs()
                                                        else:
                                                            # restart from the beginning
                                                            print(" [ERROR] Type entire word, e.g. yes")
                                                            continue
                                                            reset_inputs()

                                        # non OCO orders
                                        elif 'no' in is_oco.lower():

                                            # get order choice, SL or TP
                                            is_sl_order = input(
                                                'Do you want a STOP LOSS order?' +
                                                'If not, a take profit order' +
                                                'will be placed. Type yes or no: '
                                            )

                                            # TAKE PROFIT order
                                            if 'no' in is_sl_order.lower():

                                                # get LIMIT PROFIT percentage
                                                inp_lmt_profit_pct = input(
                                                    'Type LIMIT PROFIT percentage, e.g. 5.20: '
                                                )
                                                if is_float(inp_lmt_profit_pct):
                                                    lmt_profit_pct = is_float(inp_lmt_profit_pct)

                                                    # get STOP PROFIT percentage
                                                    inp_stop_profit_pct = input(
                                                        'Type STOP PROFIT percentage, e.g. 5.25: '
                                                    )
                                                    if is_float(inp_stop_profit_pct):
                                                        stop_profit_pct = is_float(inp_stop_profit_pct)

                                                        # get user time
                                                        user_start_time, user_end_time = construct_user_time(
                                                            start_hour, start_mins, working_ival
                                                        )

                                                        print('DATA RESUME')
                                                        print()
                                                        tabledata = [
                                                            ['Timezone', usr_tz],
                                                            ['Start Time', 'everyday at: ' + str(user_start_time)],
                                                            ['End Time', 'everyday at: ' + str(user_end_time)],
                                                            ['Refresh Interval', str(refresh_ival) + 'secs'],
                                                            ['OCO order', 'NO'], ['Take Profit order', 'YES'],
                                                            ['Stop Profit Percentage', '+' + str(stop_profit_pct) + '%'],
                                                            ['Take Profit Limit Percentage', '+' + str(lmt_profit_pct) + '%']
                                                        ]
                                                        print(tabulate(tabledata, headers=['Key', 'Value']))

                                                        # get data confirmation
                                                        confirm = input(
                                                            'Type yes to confirm all data above is correct: '
                                                        )
                                                        if 'yes' in confirm.lower():
                                                            # end data collection
                                                            check_time()
                                                        elif 'no' in confirm.lower():
                                                            # restart from the beginning
                                                            continue
                                                            reset_inputs()
                                                        else:
                                                            # restart from the beginning
                                                            print(" [ERROR] Type entire word, e.g. yes")
                                                            continue
                                                            reset_inputs()

                                            # STOP LOSS order
                                            elif 'yes' in is_sl_order.lower():

                                                # get LIMIT LOSS percentage
                                                inp_lmt_loss_pct = input(
                                                    'Type LIMIT LOSS percentage, e.g. 1.15: '
                                                )
                                                if is_float(inp_lmt_loss_pct):
                                                    lmt_loss_pct = is_float(inp_lmt_loss_pct)

                                                    # get STOP LOSS percentage
                                                    inp_sl_pct = input(
                                                        'Type stop loss percentage, e.g. 1.10: '
                                                    )
                                                    if is_float(inp_sl_pct):
                                                        sl_pct = is_float(inp_sl_pct)

                                                        # get user time preferences form construct_user_time()
                                                        user_start_time, user_end_time = construct_user_time(
                                                            start_hour, start_mins, working_ival
                                                        )

                                                        print('DATA RESUME')
                                                        print()
                                                        tabledata = [
                                                            ['Timezone', usr_tz],
                                                            ['Start Time', 'everyday at: ' + str(user_start_time)],
                                                            ['End Time', 'everyday at: ' + str(user_end_time)],
                                                            ['Refresh Interval', str(refresh_ival) + 'secs'],
                                                            ['OCO order', 'NO'], ['Stop Loss order', 'YES'],
                                                            ['Stop Loss Percentage', '-' + str(sl_pct) + '%'],
                                                            ['Limit Loss Percentage', '-' + str(lmt_loss_pct) + '%']
                                                        ]
                                                        print(tabulate(tabledata, headers=['Key', 'Value']))

                                                        # get data confirmation
                                                        confirm = input(
                                                            'Type yes to confirm all data above is correct: '
                                                        )
                                                        if 'yes' in confirm.lower():
                                                            # end data collection
                                                            check_time()
                                                        elif 'no' in confirm.lower():
                                                            # restart from the beginning
                                                            continue
                                                            reset_inputs()
                                                        else:
                                                            # restart from the beginning
                                                            print(" [ERROR] Type entire word, e.g. yes")
                                                            continue
                                                            reset_inputs()
                                            else:
                                                print(" [ERROR] Type entire word, e.g. yes")
                                        else:
                                            print(" [ERROR] Type entire word, e.g. yes")
                    else:
                        print(
                            ' [ERROR] Timezone: ' + tz_cont.capitalize() + '/' + tz_city.capitalize() +
                            ' you entered is not valid. \n ' +
                            'Check it at: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones#List.'
                        )
                else:
                    print(" [ERROR] Type only letters")
            else:
                print(" [ERROR] Type only letters")
