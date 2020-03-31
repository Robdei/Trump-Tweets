import pandas as pd
import json
from subprocess import Popen
import os

def download_sched():
    p = Popen('curl https://media-cdn.factba.se/rss/json/calendar-full.json > PresidentialSchedule.txt', shell=True)
    p.wait()
    with open('PresidentialSchedule.txt') as json_file:
        sched = json.load(json_file)
        arraydata = pd.DataFrame(
            columns=['date', 'time', 'time_formatted', 'year', 'month', 'day', 'day_of_week', 'type', 'details',
                     'location',
                     'coverage', 'daily_text', 'url', 'trump_property', "political_rally", "golf", "fundraiser",
                     "international", 'newmonth', 'daycount', 'lastdaily'], index=range(len(sched)))
        for n, sched_item in enumerate(sched):
            for sched_parameter in sched_item.keys():
                if sched_parameter in ['day_summary', 'tags']:
                    for day_sum in sched_item[sched_parameter]:
                        arraydata[day_sum] = sched_item[sched_parameter][day_sum]
                else:
                    arraydata[sched_parameter].iloc[n] = sched_item[sched_parameter]

    arraydata.to_csv('Presidential_schedule.csv', index=False)
    os.remove('PresidentialSchedule.txt')