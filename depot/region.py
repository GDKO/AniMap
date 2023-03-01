#!/usr/bin/env python
"""
    Usage:
      animap region -c <FILE> -o <DIR>

    Options:
      -h, --help                    show this
      -c, --config_file <FILE>      config_file
      -o, --output <DIR>            creates a directory for all output files
"""

import matplotlib as mpl
import matplotlib.pyplot as plt
import geopandas as gpd
import csv
import sys
import time
import math
import yaml

from docopt import docopt
from datetime import date, timedelta
from unidecode import unidecode
from multiprocessing import Pool
from matplotlib.gridspec import GridSpec
from matplotlib.lines import Line2D

from depot.AniMapLib import get_values_curved_line, split, progress, title, remove_frames, get_outdir


def fplot(j_list):

    L, Title, i, out_dir, data, data2, dpi = j_list

    municipalities_colors = ["lightskyblue", "#009fff" ,"#0060ff", "#0020ff", "#0000b3"]
    fig = plt.figure(figsize=(9,6))
    gs = GridSpec(ncols=3,nrows=2,width_ratios=[3.4,1.12,0.1],height_ratios=[2.8,4.4],wspace=0.05)
    ax1 = fig.add_subplot(gs[:,0])
    ax2 = fig.add_subplot(gs[0,1])
    ax3 = fig.add_subplot(gs[1:,1:])
    ax4 = fig.add_subplot(gs[0,2:])

    #Ax1 --points
    data.plot(ax=ax1,edgecolor='darkgrey',facecolor='white',linewidth=.4)
    ##legend
    legend_elements=[Line2D([],[],marker="o", markersize=5, color="red", label="Apiary",linewidth=0),
                     Line2D([],[],marker="o", markersize=5, color="purple", label="Sentinel",linewidth=0),
                     Line2D([],[],marker="o", markersize=5, color="orange", label="Natural",linewidth=0)]
    ax1.legend(handles=legend_elements,loc="lower right", title="Colony")
    #Ax2 --municipalities
    data2.plot(ax=ax2,edgecolor='darkgrey',facecolor='white',linewidth=.2)
    ##colorbar
    cmap = mpl.colors.ListedColormap(municipalities_colors)
    bounds = [1,5,10,15,20,30]
    norm = mpl.colors.BoundaryNorm(bounds, cmap.N)
    cbar = fig.colorbar(mpl.cm.ScalarMappable(cmap=cmap,norm=norm),cax=ax4,ticks=bounds,orientation="vertical", label="Number of cases")
    cbar.ax.tick_params(labelsize=7)
    #Ax3 Add text
    ax3.text(0.1,0.9,"Milestones",fontsize=15)
    text_list= []
    ax3.set_axis_off()

    # Title
    fig.suptitle(Title)

    for frame in L:
        if frame[0] == "p":
            ax1.plot(frame[1], frame[2], marker="o", markersize=frame[3], alpha=frame[4], markerfacecolor=frame[5], markeredgecolor=frame[5])
        elif frame[0] == "l":
            ax1.plot(frame[1], frame[2], color="black")
        elif frame[0] == "m":
            color_index = math.floor(frame[2]/5)
            if color_index>4:
                color_index=4
            data2[data2.name==frame[1]].plot(ax=ax2,color=municipalities_colors[color_index])
        elif frame[0] == "t":
            text_list.append(frame[1])
    h = 0.8
    for text in text_list:
        ax3.text(0.1,h,text,fontsize=8)
        h-=0.05

    ax1.set_xlim([14.9,16.6])
    ax1.set_ylim([37.1,39.3])
    ax2.set_xlim(ax1.get_xlim())
    ax2.set_ylim(ax1.get_ylim())
    ax2.tick_params(axis="x", which="both", labelbottom=False, bottom=False, top=False)
    ax2.tick_params(axis="y", which="both", labelleft=False, left=False, right=False)
    ax1.set_aspect("auto")
    ax2.set_aspect("auto")
    plt.text(0.075,0.5,"Sicily",transform=ax1.transAxes)
    plt.text(0.6,0.77,"Calambria",transform=ax1.transAxes)
    plt.savefig(out_dir + "/frame_%05d.png"%(i),format="png",dpi=dpi) #dpi=300
    plt.close()

def main():
    args = docopt(__doc__)
    config_yaml = args['--config_file']
    out_dir = get_outdir(args['--output'])

    # Load config_file
    stream = open(config_yaml, 'r')
    config_opts = yaml.safe_load(stream)
    stream.close()

    threads = config_opts["threads"]
    dpi = config_opts["dpi"]
    title_format = config_opts["title_format_region"]
    frames_per_day = config_opts["frames_per_day"]
    frames_for_line = config_opts["frames_for_line"]
    start_date = config_opts["start_date"]
    end_date = config_opts["end_date"]
    point_decay_days = config_opts["point_decay_days"]
    point_size = config_opts["point_size"]
    transparency_alpha = config_opts["transparency_alpha"]

    region_json = config_opts["region_json"]
    municipalities_json=config_opts["municipalities_json"]
    region_cases = config_opts["region_cases"]
    region_transfers_file = config_opts["world_transfers_file"]
    milestones = config_opts["milestones"]
    ##

    st = time.time() #tm
    data = gpd.read_file(region_json)
    data2 = gpd.read_file(municipalities_json)
    municipalities = []
    municipalities_cases = {}
    for name in data2.name:
        municipalities.append(name)
        municipalities_cases[name] = 0

    et = time.time() - st #tm
    print("Loaded map in " + str(int(et)) + " seconds.") #tm

    # multiprocessing
    p = Pool(threads)


    # point decay
    point_decay_frames = point_decay_days * frames_per_day
    size_decay = point_size / point_decay_frames
    transparency_decay = transparency_alpha / point_decay_frames

    delta = end_date - start_date
    delta_days = delta.days
    limit = delta_days * frames_per_day

    #graph title
    Title=title(title_format,start_date,delta_days,frames_per_day)


    L=[[] for x in range(limit)]
    points = {}

    st = time.time() #tm
    with open(region_cases) as csvfile:
        reader = csv.reader(csvfile,delimiter=",")
        for row in reader:
            i_id = row.index('ID')
            i_longtitude = row.index('Longtitude')
            i_latitude = row.index('Latitude')
            i_colony = row.index('Colony')
            i_day = row.index('Day')
            i_month = row.index('Month')
            i_year = row.index('Year')
            i_municipality = row.index('Municipality')
            break

        for row in reader:
            longtitude = float(row[i_longtitude])
            latitude = float(row[i_latitude])
            id_name = row[i_id]
            municipality = row[i_municipality]
            points[id_name] ={}
            points[id_name]["loc"] = [longtitude,latitude]
            point_date = date(int(row[i_year]),int(row[i_month]),int(row[i_day]))
            delta = point_date - start_date
            start = delta.days * frames_per_day
            points[id_name]["start"] = start
            end = start + point_decay_frames

            if end == "":
                end = limit
            else:
                end = int(end)

            ##### municipalities
            found = 0
            for name in municipalities:
                if unidecode(name.lower()) == unidecode(municipality.lower()):
                    municipalities_cases[name] += 1
                    found = 1
                    for f in range(limit - start):
                        l_index = 0
                        m_found = 0
                        while l_index < len(L[start+f]):
                            if L[start+f][l_index][0] == "m" and L[start+f][l_index][1] == name:
                                L[start+f][l_index][2] += 1
                                m_found = 1
                            l_index += 1

                        if not m_found:
                            loc = ["m",name,1]
                            L[start+f].append(loc)

            #check_errors
            if not found:
                print(municipality)
            #####
            markersize = point_size
            alpha = transparency_alpha

            if row[i_colony] == "Sentinel":
                color = "purple"
            elif row[i_colony] == "Natural":
                color = "orange"
            else:
                color = "red"

            while start < end and start < limit and delta.days>=0:

                for f in range(frames_per_day):
                    loc = ["p",longtitude,latitude,markersize,alpha,color]
                    L[start+f].append(loc)

                start += 1
                markersize -= size_decay
                alpha -= transparency_decay


    et = time.time() - st #tm
    print("Parsed points file in " + str(int(et)) + " seconds.") #tm

    st = time.time() #tm
    with open(region_transfers_file) as csvfile:
        reader = csv.reader(csvfile,delimiter=",")
        for row in reader:
            i_from = row.index('from')
            i_to = row.index('to')
            break

        for row in reader:
            start = points[row[i_to]]["start"]
            if start < limit: #GK still if too early or too late
                x_values, y_values = get_values_curved_line(points[row[i_from]]["loc"],points[row[i_to]]["loc"])
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


    st = time.time() #tm
    with open(milestones) as csvfile:
        reader = csv.reader(csvfile,delimiter=",")
        for row in reader:
            i_day = row.index('Day')
            i_month = row.index('Month')
            i_year = row.index('Year')
            i_text = row.index('Text')
            break

        for row in reader:
            point_date = date(int(row[i_year]),int(row[i_month]),int(row[i_day]))
            delta = point_date - start_date
            start = delta.days * frames_per_day
            while start < limit and delta.days>=0:
                for f in range(frames_per_day):
                    loc = ["t",row[i_text]]
                    L[start+f].append(loc)

                start += frames_per_day

    et = time.time() - st #tm
    print("Parsed milestones file in " + str(int(et)) + " seconds.") #tm


    # Scale to 1 frame empty days of ax1
    L,Title = remove_frames(L,Title,limit,frames_per_day)


    #Plotting the frames
    st = time.time() #tm
    j_list=[]
    for i in range(len(Title)):
        j = [L[i],Title[i],i,out_dir, data, data2, dpi]
        j_list.append(j)

    i=0
    for i, _ in enumerate(p.imap_unordered(fplot,j_list),1):
        progress(i,1,len(j_list))



    et = time.time() - st #tm
    num_frames = len(j_list)
    pfps = round(num_frames/et,1)
    print("Plotted " + str(num_frames) + " frames in " + str(int(et)) + " seconds (" + str(pfps) + "/s)") #tm
