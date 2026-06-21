#!/bin/env python3

"""
     BashZero v0:
         - Read sizes of folders in config file
         - Save sizes of folders in config file
         - Plot graphs showing progress over time
         - Highlight folders where progress isn't being made or are growning
         - Calculate amount of money I owe charity, less amount given
     v1 goals:
         - read and unread inbox from gmail
         - count firfox tabs

     Assumes python > 3.4
"""
from pathlib import Path
import subprocess
import datetime.datetime as dt
from datetime import timedelta
import pytz
import json
import matplotlib.pyplot as plt

# Simple dict of directories for now
# Dict(Name => Type, Path, (Valuehist))

# Example first target: Can be created and saved in ipython.
#  targets = {}
#  targets["home"] = {"type": "folder_size", "direction": "down", "goal": 8, "start": , "dailyrate": -1, "path":"/home/user/", "valuehist": [("2026-06-22T05:59:49.286862+09:00", 8)], "goalhist": []}


# Use local time for goal calculations and graphs
config["tz"] = 'Asia/Seoul'
config["targets"] = 'targets.json'

def load_config(p:Path):
    """
    load_config: Will load config from path evenutally,
    but we don't need that complexity now.
    """
    pass

    
def folder_size(p:Path): -> int
    value = subprocess.run([f"ls '{str(p)}'| wc -l"], shell=True, capture_output=True, text=True) 
    return int(value.stdout.strip())

def get_value(t:target): -> int
    """
        Get current value for target, for all types of targets.
        This allows running different retrieval functions for different
        target types.
    """

    type = targets[t]["type"]
    match type:
        case "folder_size":
            return folder_size(targets[t]["path"])
    
def save_value(t:target, i:Int, valuetype="valuehist"):
    """
        Save the current value to the target goal.
        Modifies the global value of targets.
    """

    # Use UTC internally.
    tz = pytz.timezone("UTC")
    tm = dt.now(tz).isoformat()
    
    if t in targets:
        if vh in targets[t]:
            targets[t][valuetype].append((tm, i))
        else:
            targets[t][valuetype]=[(tm, i)]
    else:
        raise(ValueError)


def save_targets(p:Path = config["targets"]):
    with open(p, "w", encoding="utf-8") as f:
        json.dump(targets, f, indent=2)

def load_targets(p:Path = config["targets"]):
    global targets
    with open(p, "r", encoding="utf-8") as f:
        targets = json.load(f)

def update_goalhists():
    """
        Update value of goalhist in each target since last goalhist.
    """
    failed_goals = []
    complete_goals = []
    for (t, d) in targets.items():
        start = d["start"]
        rate = d["dailyrate"]
        goal = d["goal"]
        gh = d["goalhist"]
        last_date = d["valuehist"][-1][0]
        last_value = d["valuehist"][-1][1]

        # Find latest goal time and value in goalhist:
        lt = None # last goal time
        lv = None # last goal value
        for (t, v) in gh:
            t =  dt.fromisotime(t)
            if lt == None or t > lt:
                lt = t
                lv = v

        # Step through, updating goal time and value daily       
        ct = dt.now(config["tz"])
        d1 = timedelta(hours=24)
        # Todo: have us also step through valuehist since start,
        # to catch days we went over/under...?
        while lt < (ct - d1):
            lt = lt + d1
            lv = lv + rate
            if lv * sgn(rate) > goal * sgn(rate):
                complete_goals.append(t)
                if last_value * sgn(rate) > goal * sgn(rate):
                    print(f"WARNING: Not maintaining goal!: {t}, goal: {goal}, value: {last_value}")
                    failed_goals.append(t)
            else:
                gh.append((lt, lv))

            if last_value * sgn(rate) > lv * sgn(rate):
                failed_goals.append(t)
                print(f"Goal {t} failed on {lt}: goal {lv}, value {last_value}")
                continue
            
            if (last_value+3*rate) * sgn(rate) > lv * sgn(rate):
                print(f"WARNING: Goal {t} will fail in 2 days from {lt}:",
                      f"{lt}: goal {lv}, value {last_value}")

        targets[t]["goalhist"] = gh

def update_values():
    for t, d in targets.items():
        v = get_value(t)
        save_value(t, v)
        
def plot_target(t:target, valuetype="valuehist"):
    """
    Simple graph for a single target.
    Will modify it later to show values at 4 am local.
    """

    dates = []
    values = []
    goaldates = []
    goalvalues = []

    # Values themselves
    for date, value in targets[t][valuetype]:
        dates.append(dt.fromisoformat(date))
        values.append(value)

    # Goal
    # load target
    start = targets[t]["start"]
    rate = targets[t]["dailyrate"]
    goal = targets[t]["goal"]
    for d, v in targets[t]["goalhist"]:
        goaldates.append(dt.fromisoformat(d))
        goalvalues.append(v)
    
    plt.title(t)
    plt.plot(dates,values, color="b")
    plt.plot(goaldates, goalvalues, color="r")
    plt.show()

def plot_targets():
    for t, d in targets.items():
        plot_target()
    
def make_report(t:target):
    update_goalhists() # Good enough for MVP
 
def calculate_charges(:Path):
    pass

def count_tabs():
    pass # I have a shell script which does this but don't want it here yet.


def count_emails():
    pass # Mail not yet integrated


def manual_update(t:target):
    pass

def main():
    targets = load_targets()
    update_targets()
    update_goals()
    save_targets()
    plot_targets()
