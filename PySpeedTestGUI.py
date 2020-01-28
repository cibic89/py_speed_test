#!/usr/bin/env python
# coding: utf-8

import gc
import os
import sys

import PySimpleGUI as sg
from pandas import DataFrame, to_datetime, concat  # , read_csv
import speedtest

bit_to_mb_factor = 10 ** 6

main_dir = str(os.path.normpath(os.getcwd()))  # +os.sep+os.pardir
images_dir = main_dir+os.sep+"images"+os.sep+"exports"+os.sep
output_dir = main_dir+os.sep+"data"+os.sep+"processed"+os.sep
if not os.path.isdir(output_dir):
    os.mkdir(output_dir)

app_logo_fname = "app_logo.ico"

results = dict()
results_df = DataFrame()
timestamp_fmt = "%d %B, %Y %H:%M:%S"
cities_rgx = "United Kingdom|Italy|Russian Federation|Estonia|Albania|Tunisia"
cities_rgx += "Morocco|Turkey|United States"
cities_rgx += "United Arab Emirates|China|India|Uganda|Brazil|Mexico"

test_speed = sg.PopupYesNo("Test your worldwide internet speed?", title="WST",
                           icon=images_dir+os.sep+app_logo_fname)


def close_all():
    """Closes debug outputs and exits program"""
    sg.EasyPrintClose()
    sys.exit()


if test_speed == "Yes":
    s = speedtest.Speedtest()
    servers_df = DataFrame.from_dict(s.get_servers(), orient="index")
    servers_df = servers_df[0].reset_index(drop=True)
    servers_df = DataFrame(servers_df.to_list()).sort_values("d").set_index("id")  # sort by ping
    # servers_df.to_csv(output_dir+"servers.csv", index=False)
    # servers_df.head(2)

    server_inds = servers_df["country"].drop_duplicates()
    server_inds = server_inds[server_inds.str.contains(cities_rgx, case=False)]
    server_inds = server_inds.drop_duplicates().index

    start_time = to_datetime('now')
    Print = sg.EasyPrint  # (do_not_reroute_stdout=False)
    Print("Welcome to Worldwide Speed Test. \n\nFor this to work, please close" +
          " all internet related applications from all devices using the test" +
          " network. Optionally restart the broadband device and set your" +
          " power profile to high performance." +
          "\n\nINFO: start time - "+start_time.strftime(timestamp_fmt)+" - currently speed testing:")

    for i, server in enumerate(server_inds):
        s = speedtest.Speedtest()

        servers = [server]  # has to be one only
        # If you want to test against a specific server
        # servers = [1234]

        s.get_servers(servers)  # run this to update the internal config of speedtest

        threads = None
        # If you want to use a single threaded test
        # threads = 1

        s.download(threads=threads)  # tests download
        s.upload(threads=threads, pre_allocate=False)  # tests upload
        s.results.share()  # shares results with speedtest

        results[server] = s.results.dict()

        #         clear_output(wait=True)
        Print(servers_df["name"].loc[server]+", "+servers_df["country"].loc[server])

    results_df = DataFrame(results).T

    server_df, client_df = DataFrame(), DataFrame()

    for idx, server, client in results_df[["server", "client"]].itertuples():
        server_df = server_df.append(server, ignore_index=True)
        client_df = client_df.append(client, ignore_index=True)

    server_df.index, client_df.index = results_df.index, results_df.index
    results_df = results_df.drop(columns=["server", "client"])
    results_df = concat([results_df, server_df, client_df], axis=1, sort=False)
    # results_df.to_csv(output_dir+"results_df.csv", index=False)

    del server_df, client_df, results
    gc.collect()

    finish_time = to_datetime('now')
    Print("INFO: end time - ", str(finish_time.strftime(timestamp_fmt))+". This took",
          round((finish_time - start_time).total_seconds() / 60, 2), "minutes")

    # results_df = read_csv(output_dir+isp_name_package+".csv")
    Print("\n\nMedian download speed is",
          round(results_df["download"].median() / bit_to_mb_factor, 2), "mb",
          "\nMedian upload speed is", round(results_df["upload"].median() / bit_to_mb_factor, 2), "mb",
          "\nPing is", round(results_df["ping"].median(), 2), "ms")
else:
    close_all()

# display(results_df.head())

save_results = sg.PopupYesNo("Save results as a csv file?", title="WST", icon=images_dir+os.sep+app_logo_fname)

if (test_speed == "Yes") & (save_results == "Yes"):
    text_in = sg.PopupGetText('Please enter filename (without extension)',
                              title="WST",
                              icon=images_dir+os.sep+app_logo_fname)
    if text_in is not None:
        results_df.to_csv(output_dir+text_in+".csv", index=False)
    close_all()
else:
    close_all()
