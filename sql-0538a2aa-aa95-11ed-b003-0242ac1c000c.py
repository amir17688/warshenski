from datetime import datetime, timedelta
from time import localtime, strftime
import sqlite3


# Get the new date from string time/date
def get_date(time):
    now = datetime.now()
    if ',' in time:
        times = time.split(',')
        for t in times:
            val = t
            if 's' in val:
                val = val.replace('s', '')
                now += timedelta(seconds=int(val))
            elif 'm' in val:
                val = val.replace('m', '')
                now += timedelta(minutes=int(val))
            elif 'h' in val:
                val = val.replace('h', '')
                now += timedelta(hours=int(val))
            elif 'd' in val:
                val = val.replace('d', '')
                now += timedelta(days=int(val))
    else:
        val = time
        if 's' in val:
            val = val.replace('s', '')
            now += timedelta(seconds=int(val))
        elif 'm' in val:
            val = val.replace('m', '')
            now += timedelta(minutes=int(val))
        elif 'h' in val:
            val = val.replace('h', '')
            now += timedelta(hours=int(val))
        elif 'd' in val:
            val = val.replace('d', '')
            now += timedelta(days=int(val))
    return now


# RemindMe command
async def ex_me(dclient, channel, mention, con, con_ex, author_id, a, log_file, cmd_char):
    a = a.split(' ')
    if len(a) >= 2:
        time = a[0].lower()
        msg = ''
        for i in range(1, len(a)):
            msg += a[i] + ' '
        if 'd' in time or 'h' in time or 'm' in time or 's' in time or ',' in time:
            date = get_date(time)
            try:
                con_ex.execute("INSERT INTO reminder (type, channel, message, date) VALUES ('0', {}, '{}', '{}');"
                               .format(author_id, msg, date.strftime('%Y-%m-%d %X')))
                con.commit()
                await dclient.send_message(channel, '{}, will remind you.'.format(mention))
            except sqlite3.Error as e:
                await dclient.send_message(channel, '{}, error when trying to add info to database! Please notifiy '
                                                    'the admins!'.format(mention))
                print('[{}]: {} - {}'.format(strftime("%b %d, %Y %X", localtime()), 'SQLITE',
                                             'Error when trying to insert data: ' + e.args[0]))
                log_file.write('[{}]: {} - {}\n'.format(strftime("%b %d, %Y %X", localtime()), 'SQLITE',
                                                        'Error when trying to insert data: ' + e.args[0]))
        else:
            await dclient.send_message(channel, '{}, The time must be in #time format (ex: 1h or 2h,5m).'
                                       .format(mention, cmd_char))
    else:
        await dclient.send_message(channel, '{}, **USAGE:** {}remindme <time> <message...>'.format(mention, cmd_char))
        print('')


# RemindAll command
async def ex_all(dclient, channel, mention, con, con_ex, channel_id, a, log_file, cmd_char):
    a = a.split(' ')
    if len(a) >= 2:
        time = a[0].lower()
        msg = ''
        for i in range(1, len(a)):
            msg += a[i] + ' '
        if 'd' in time or 'h' in time or 'm' in time or 's' in time or ',' in time:
            date = get_date(time)
            try:
                con_ex.execute("INSERT INTO reminder (type, channel, message, date) VALUES ('1', {}, '{}', '{}');"
                               .format(channel_id, msg, str(date)))
                con.commit()
                await dclient.send_message(channel, '{}, will remind you.'.format(mention))
            except sqlite3.Error as e:
                await dclient.send_message(channel, '{}, error when trying to add info to database! Please notifiy '
                                                    'the admins!'.format(mention))
                print('[{}]: {} - {}'.format(strftime("%b %d, %Y %X", localtime()), 'SQLITE',
                                             'Error when trying to insert data: ' + e.args[0]))
                log_file.write('[{}]: {} - {}\n'.format(strftime("%b %d, %Y %X", localtime()), 'SQLITE',
                                                        'Error when trying to insert data: ' + e.args[0]))
        else:
            await dclient.send_message(channel, '{}, The time must be in #time format (ex: 1h or 2h,5m).'
                                       .format(mention, cmd_char))
    else:
        await dclient.send_message(channel, '{}, **USAGE:** {}remindall <time> <message...>'.format(mention, cmd_char))
        print('')
