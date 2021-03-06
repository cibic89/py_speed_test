#!/usr/bin/env python
# coding: utf-8
"""Worldwide speedtest source code"""

import gc
import os
import re
import sys
import time

import speedtest
from pandas import DataFrame, to_datetime, concat

bit_to_mb_factor = 10 ** 6  # convert bits to megabits

main_dir = str(os.path.normpath(os.getcwd()))  # +os.sep+os.pardir+os.sep+os.pardir
output_dir = main_dir+os.sep+"processed"  # +os.sep
# print(main_dir+"\n"+output_dir)

results = dict()
results_df = DataFrame()
timestamp_fmt = "%d %B, %Y %H:%M:%S"
cities_rgx = "United Kingdom|Italy|Russian Federation|Estonia|Albania|Tunisia"
cities_rgx += "Morocco|Turkey|United States"
cities_rgx += "United Arab Emirates|China|India|Uganda|Brazil|Mexico"

yes = {'yes', 'y', 'ye', ''}
no = {'no', 'n'}
test_speed = None
save_results = None
usable_input = None


def filename_check(strg: str, search=re.compile(r'[\"\'\\/]').search):
    """Checks filename for erroneous characters

    Args:
        strg (str): filename
        search (re.search): regex character search

    Returns:
        bool: (obvious)
    """
    return bool(search(strg))


def yn_input(question: str):
    """Handles intelligently input questions with yes/no answers

    Args:
        question (str): obvious

    Returns:
        bool/None: (obvious)
    """
    choice = input(question + " (y/n) [y]: ").lower().strip()
    if choice in yes:
        return True
    elif choice in no:
        return False
    else:
        print("Please respond with 'y' for yes or 'n' for n ")
        return None


def close_all():
    """Quits WST"""
    print("\nThank you for using Worldwide Speedtest® by George Joseph 2020")
    time.sleep(5)
    sys.exit()


print("\nWelcome to Worldwide Speedtest® v1\n\nFor this to work, please close" +
      " all internet related applications from all devices using the test" +
      " network. Optionally, restart the broadband device, set your test" +
      " machine's power profile to high performance, and get as close as possible" +
      " to the wireless access point or use the wired network.\n")

while test_speed is None:
    test_speed = yn_input("Test your worldwide internet speed?")

if test_speed:
    s = speedtest.Speedtest()
    servers_df = DataFrame.from_dict(s.get_servers(), orient="index")  # get speedtest.net servers
    servers_df = servers_df[0].reset_index(drop=True)
    servers_df = DataFrame(servers_df.to_list()).sort_values("d").set_index("id")  # sort by ping

    # Select the best performing (ping-wise) servers from select countries (akamai top download locations)
    server_inds = servers_df["country"].drop_duplicates()
    server_inds = server_inds[server_inds.str.contains(cities_rgx, case=False)]
    server_inds = server_inds.drop_duplicates().index

    start_time = to_datetime('now')  # execute timer
    print("\n\nINFO: start time - "+start_time.strftime(timestamp_fmt)+" - currently speed testing:")

    # actual speedtesting
    for i, server in enumerate(server_inds):
        s = speedtest.Speedtest()

        servers = [server]  # has to be one only - if you want to test against a specific server servers = [1234]

        s.get_servers(servers)  # run this to update the internal config of speedtest

        threads = None  # if you want to use a single threaded test threads = 1

        s.download(threads=threads)  # tests download
        s.upload(threads=threads, pre_allocate=False)  # tests upload
        s.results.share()  # shares results with speedtest

        results[server] = s.results.dict()

        print(servers_df["name"].loc[server]+", "+servers_df["country"].loc[server]+": download",
              round(results[server]["download"] / bit_to_mb_factor, 2), "mb - upload",
              round(results[server]["upload"] / bit_to_mb_factor, 2), "mb - ping",
              round(results[server]["ping"], 2), "ms.")

    # assembling results
    results_df = DataFrame(results).T
    server_df, client_df = DataFrame(), DataFrame()

    for idx, server, client in results_df[["server", "client"]].itertuples():
        server_df = server_df.append(server, ignore_index=True)
        client_df = client_df.append(client, ignore_index=True)

    server_df.index, client_df.index = results_df.index, results_df.index
    results_df = results_df.drop(columns=["server", "client"])
    results_df = concat([results_df, server_df, client_df], axis=1, sort=False)

    del server_df, client_df, results
    gc.collect()

    finish_time = to_datetime('now')
    print("INFO: end time - ", str(finish_time.strftime(timestamp_fmt))+". This took",
          round((finish_time - start_time).total_seconds() / 60, 2), "minutes")

    print("\n\nMedian download speed is", round(results_df["download"].median() / bit_to_mb_factor, 2), "mb",
          "\nMedian upload speed is", round(results_df["upload"].median() / bit_to_mb_factor, 2), "mb",
          "\nPing is", round(results_df["ping"].median(), 2), "ms\n")
else:
    close_all()

while save_results is None:
    save_results = yn_input("Save results as a csv file?")

# save results from here-on
if test_speed & save_results:
    text_in = input('Please enter filename (without extension) [wst]: ') or "wst"

    while not usable_input:
        if (text_in is None) | (text_in == "") | (filename_check(text_in)):
            usable_input = False
            print("Please input a usable filename...")
        else:
            if not os.path.exists(output_dir):
                os.mkdir(output_dir)
            full_output_fname = output_dir + text_in + ".csv"
            results_df.to_csv(full_output_fname, index=False)
            print("Results exported as:\n"+full_output_fname)
            usable_input = True
            close_all()
else:
    close_all()
