import sys
import numpy as np
import bezier
from datetime import timedelta

def get_values_curved_line(point1,point2):

    x_diff = abs(point1[0] - point2[0])
    y_diff = abs(point1[1] - point2[1])
    xm = (point1[0] + point2[0])/2
    ym = (point1[1] + point2[1])/2
    hy = x_diff/3
    hx = y_diff/3
    if point1[0]>point2[0] and point1[1]<point2[1]:
        nx = xm+hx
        ny = ym+hy
    elif point1[0]<point2[0] and point1[1]<point2[1]:
        nx = xm-hx
        ny = ym+hy
    elif point1[0]<point2[0] and point1[1]>point2[1]:
        nx = xm-hx
        ny = ym-hy
    else:
        nx = xm+hx
        ny = ym-hy

    points=[point1]
    points.append([nx,ny])
    points.append(point2)

    points=np.array(points).transpose()
    points=np.asfortranarray(points)
    curve = bezier.Curve(points,degree=2)
    s_val=np.linspace(0,1,30)
    f=curve.evaluate_multi(s_val)

    return list(f)[0], list(f)[1]

def split(x,n):
    nums = []
    nums_end = []
    if (x % n == 0):
        for i in range(n):
            pp = x//n
            nums.append(pp)
    else:
        zp = n - (x % n)
        pp = x//n
        for i in range(n):
            if i >= zp:
                nums.append(pp+1)
            else:
                nums.append(pp)
    for i in range(len(nums)):
        if i == 0:
            nums_end.append(nums[i])
        else:
            nums_end.append(nums[i]+nums_end[i-1])
    return nums_end

def remove_frames(L,Title,limit,frames_per_day):
    i = 0
    frames_to_remove = []
    while i < limit:
        diff_plots = 0
        for k in range(frames_per_day):
            for frame in L[i+k]:
                if frame[0] != "m" and frame[0] != "t" and diff_plots == 0: #if frames are not only text or municipality
                    diff_plots = 1
        if diff_plots == 0:
            for k in range(frames_per_day-1):
                frames_to_remove.insert(0,i+k)
        i+=frames_per_day

    for f in frames_to_remove:
        del L[f]
        del Title[f]
    return L,Title

# graph title
def title(title_format,start_date,delta_days,frames_per_day):
    Title=[]
    for i in range(delta_days):
        day = start_date + timedelta(days=i)
        for f in range(frames_per_day):
            Title.append(day.strftime(title_format))
    return Title

# Progress bar woohoo!
def progress(iteration, steps, max_value, no_limit=False):
    if int(iteration) == max_value:
        if no_limit == True:
            sys.stdout.write('\r')
            print ("[x] \t%d%%" % (100), end='\r')
        else:
            sys.stdout.write('\r')
            print ("[x] \t%d%%" % (100))
    elif int(iteration) % steps == 0:
        sys.stdout.write('\r')
        print ("[x] \t%d%%" % (float(int(iteration) / int(max_value)) * 100), end='\r')
        sys.stdout.flush()
    else:
        pass
