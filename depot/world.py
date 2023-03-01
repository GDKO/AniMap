#!/usr/bin/env python
"""
    Usage:
      animap world -c <FILE>

    Options:
      -h, --help                    show this
      -c, --config_file <FILE>      config_file
"""

import matplotlib.pyplot as plt
import geopandas as gpd
import csv
import sys
import time
import math
import yaml
import shutil

from docopt import docopt
from datetime import date, timedelta
from unidecode import unidecode
from multiprocessing import Pool

from depot.AniMapLib import get_values_curved_line, split, progress, title

def fplot(j_list):


    fig = plt.figure(figsize=(12,6))
    ax1 = fig.add_subplot()

    #j_list contents
    L, Title, i, k, out_dir, data, dpi = j_list
    #Ax1 --points
    data.plot(ax=ax1,edgecolor='darkgrey',facecolor='white',linewidth=.4)

    #For these countries paint the borders black since the json contains individual states/regions
    data.loc[data['name'] == "United States of America"].plot(ax=ax1,facecolor='none',edgecolor='black',linewidth=0.4)
    data.loc[data['name'] == "Canada"].plot(ax=ax1,facecolor='none',edgecolor='black',linewidth=0.4)
    data.loc[data['name'] == "Brazil"].plot(ax=ax1,facecolor='none',edgecolor='black',linewidth=0.4)
    data.loc[data['name'] == "China"].plot(ax=ax1,facecolor='none',edgecolor='black',linewidth=0.4)
    data.loc[data['name'] == "Australia"].plot(ax=ax1,facecolor='none',edgecolor='black',linewidth=0.4)

    # Title
    fig.suptitle(Title)

    for frame in L:
        if frame[0] == "c":
            if frame[2] != "":
                data[data.r_name==frame[2]].plot(ax=ax1,color=frame[3],alpha=0.5)
            else:
                data[data.name==frame[1]].plot(ax=ax1,color=frame[3],alpha=0.5)
        elif frame[0] == "l":
            ax1.plot(frame[1], frame[2], color="black",linewidth=0.8)

    ax1.set_aspect("auto")

    frame_name = out_dir + "/frame_%05d.png"%(i)
    plt.savefig(frame_name,format="png", dpi=dpi)
    plt.close()

    #Copy same frames
    f=1
    while f < k:
        same_frame_name = out_dir + "/frame_%05d.png"%(i+f)
        shutil.copyfile(frame_name,same_frame_name)
        f += 1


def main():
    args = docopt(__doc__)
    config_yaml = args['--config_file']

    # Load config_file
    stream = open(config_yaml, 'r')
    config_opts = yaml.safe_load(stream)
    stream.close()

    threads = config_opts["threads"]
    dpi = config_opts["dpi"]
    title_format = config_opts["title_format_world"]
    frames_per_day = config_opts["frames_per_day"]
    frames_for_line = config_opts["frames_for_line"]
    start_date = config_opts["start_date"]
    end_date = config_opts["end_date"]
    world_json = config_opts["world_json"]
    world_cases = config_opts["world_cases"]
    centroids_file = config_opts["centroids_file"]
    transfers_file = config_opts["transfers_file"]
    ##

    st = time.time() #tm
    # Parse world json
    data = gpd.read_file(world_json)

    countries = []
    for name in data.name:
        if isinstance(name, str):
            countries.append(name)
    countries = [f for f in countries if f is not None]

    regions = []
    for name in data.r_name:
        if isinstance(name, str):
            regions.append(name)
    regions = [f for f in regions if f is not None]

    et = time.time() - st #tm
    print("Loaded map in " + str(int(et)) + " seconds.") #tm

    # multiprocessing
    p = Pool(threads)


    delta = end_date - start_date
    delta_days = delta.days
    limit = delta_days * frames_per_day

    # output_dir
    out_dir="test_wd"

    # graph title
    Title=title(title_format,start_date,delta_days,frames_per_day)

    L=[[] for x in range(limit)]

    st = time.time() #tm

    #Cases
    with open(world_cases) as csvfile:
        reader = csv.reader(csvfile,delimiter=",")
        for row in reader:
            i_id = row.index('ID')
            i_day = row.index('Day')
            i_month = row.index('Month')
            i_year = row.index('Year')
            i_country = row.index('Country')
            i_region = row.index('Region')
            i_end = row.index('End')
            break

        for row in reader:
            id_name = row[i_id]
            country = row[i_country]
            region = row[i_region]
            end = row[i_end]
            c_found = 0
            r_found = 0
            for name in countries:
                if unidecode(name.lower()) == unidecode(country.lower()):
                    country = name
                    c_found = 1

            for name in regions:
                if region == "":
                    r_found = 1
                if unidecode(name.lower()) == unidecode(region.lower()):
                    region = name
                    r_found = 1

            country_date = date(int(row[i_year]),int(row[i_month]),int(row[i_day]))
            delta = country_date - start_date
            start = delta.days * frames_per_day
            if end == "":
                end = limit
            else:
                end = int(end)
            e = 0
            for f in range(limit - start):
                if e < end:
                    loc = ["c",country,region,"red"]
                    L[start+f].append(loc)
                else:
                    loc = ["c",country,region,"blue"]
                    L[start+f].append(loc)
                e += 1

            if not c_found:
                print(country)
                sys.exit()
            if not r_found:
                print(region)

    #Centroids
    centroids={}
    with open(centroids_file) as csvfile:
        reader = csv.reader(csvfile,delimiter=",")
        for row in reader:
            i_id = row.index('Region')
            i_latitude = row.index('Latitude')
            i_longtitude = row.index('Longitude')
            break

        for row in reader:
            id = row[i_id]
            latitude = float(row[i_latitude])
            longtitude = float(row[i_longtitude])
            centroids[id] = {}
            centroids[id]["loc"] = [longtitude,latitude]

    et = time.time() - st #tm
    print("Parsed centroids file in " + str(int(et)) + " seconds.") #tm

    st = time.time() #tm
    #Transfer file

    with open(transfers_file) as csvfile:
        reader = csv.reader(csvfile,delimiter=",")
        for row in reader:
            i_from = row.index('from')
            i_to = row.index('to')
            i_day = row.index('Day')
            i_month = row.index('Month')
            i_year = row.index('Year')
            break

        for row in reader:
            point_date = date(int(row[i_year]),int(row[i_month]),int(row[i_day]))
            delta = point_date - start_date
            start = delta.days * frames_per_day
            if start < limit: #GK still if too early or too late
                x_values, y_values = get_values_curved_line(centroids[row[i_from]]["loc"],centroids[row[i_to]]["loc"])
                nums_end = split(len(x_values),frames_for_line)
                values = [x_values,y_values]
                L[start].append(["l",x_values,y_values])
                for i in range(frames_for_line-1):
                    diff = i + 1
                    sdiff = frames_for_line - diff
                    loc = ["l", x_values[:nums_end[i]], y_values[:nums_end[i]]]
                    L[start-sdiff].append(loc)
                    loc = ["l", x_values[nums_end[i]:nums_end[-1]],y_values[nums_end[i]:nums_end[-1]]]
                    L[start+diff].append(loc)

    et = time.time() - st #tm
    print("Parsed transfers file in " + str(int(et)) + " seconds.") #tm

    #Plotting the frames
    st = time.time() #tm
    j_list=[]

    for i in range(len(Title)):
        k = 1
        j = [L[i] ,Title[i] ,i , k, out_dir, data, dpi]
        j_list.append(j)

    # Copy same frames
    sj_list = []
    k = 1
    i = 0
    while ((i + k) < len(Title)):
        if j_list[i][0][-1][0] != "l" and j_list[i+k][0][-1][0] != "l" and j_list[i][0] == j_list[i+k][0] and j_list[i][1] == j_list[i+k][1]:
            k += 1
        else:
            j_list[i][3] += k - 1
            sj_list.append(j_list[i])
            i += k
            k = 1

        # For the last frame
        if (i + k) == len(Title):
            j_list[i][3] += k - 1
            sj_list.append(j_list[i])

    i=0
    for i, _ in enumerate(p.imap_unordered(fplot,sj_list),1):
        progress(i,1,len(sj_list))



    et = time.time() - st #tm
    num_frames = len(Title)
    pfps = round(num_frames/et,1)
    print("Plotted " + str(num_frames) + " frames in " + str(int(et)) + " seconds (" + str(pfps) + "/s)") #tm
