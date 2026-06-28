#!/bin/env python3

"""
    BashZero v0.2.0:
         - Add bash command as default new target.
         - Half-ass argparse for input. Otherwise I can't remember what the inputs are.

    BashZero v0.1.0:
         - Lots of bugfixes.
         - Default command-line folder target addition.

     BashZero v0.0.0:
         - Read sizes of folders in config file
         - Save sizes of folders in config file
         - Plot graphs showing progress over time
         - Highlight folders where progress isn't being made or are growning
         - Calculate amount of money I owe charity, less amount given
     v1 goals:
         - read and unread inbox from gmail
         - count firfox tabs

     Assumes python >= 3.10
"""
from pathlib import Path
import subprocess
from datetime import datetime as dt
from datetime import timedelta
import pytz
import json
import matplotlib
matplotlib.use("QtAgg")
import matplotlib.pyplot as plt
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False
import sys
import argparse


# Simple dict of directories for now
# Dict(Name => Type, Path, (Valuehist))

# Example first target: Can be created and saved in ipython.
#  targets = {}
#  targets["home"] = {"type": "folder_size", "function": "linear", "goal": 8, "starttime": , "dailyrate": -1, "path":"/home/user/", "valuehist": [("2026-06-22T05:59:49.286862+09:00", 8)], "goalhist": [(2026-06-22T05:59:49.28682+09:00", 8)]}

#  Example second generation target: Just run bash for everything. CMD must return a numerical string that can be converted to float().
#  targets["home"] = {"type": "bash_command", "function": "linear", "goal": 8, "starttime": , "dailyrate": -1, "cmd":"ls /home/user/ | wc -l", "valuehist": [("2026-06-22T05:59:49.286862+09:00", 8)], "goalhist": [(2026-06-22T05:59:49.28682+09:00", 8)]}

# Use local time for goal calculations and graphs
config = {}
config["tz"] = 'Asia/Seoul'
config["targets"] = 'targets.json'

Key = str # for type annotations

def load_config(p:Path):
    """
    load_config: Will load config from path evenutally,
    but we don't need that complexity now.
    """
    pass

    
def folder_size(p: Path) -> int:
    """ Counts hidden files and folders, but not . and .."""
    return sum(1 for _ in p.iterdir())

def bash_command(c: str) -> float:
    """ Assuming a bash command returns a single number on a single line, get the result of the command."""
    result = subprocess.run(c, shell=True, capture_output=True, text=True)
    print(result.stdout)
    try:
        return float(str(result.stdout).strip())
    except:
        print("Warning: unable to get a float out of command. Edit in config later and rerun.")
        return 0

def get_value(t: Key) -> int:
    """
        Get current value for target, for all types of targets.
        This allows running different retrieval functions for different
        target types.
    """

    typ = targets[t]["type"]
    match typ:
        case "folder_size":
            return folder_size(Path(targets[t]["path"]))
        case "bash_command":
            return bash_command(targets[t]["cmd"])
    
def save_value(t: Key, i: int, valuetype="valuehist"):
    """
        Save the current value to the target goal.
        Modifies the global value of targets.
    """

    # Use UTC internally.
    tz = pytz.timezone("UTC")
    tm = dt.now(tz).isoformat()
    
    if t in targets:
        if valuetype in targets[t]:
            targets[t][valuetype].append((tm, i))
        else:
            targets[t][valuetype]=[(tm, i)]
    else:
        raise ValueError


def save_targets(p:Path = config["targets"]):
    with open(p, "w", encoding="utf-8") as f:
        json.dump(targets, f, indent=2)

def load_targets(p:Path = Path(config["targets"])):
    global targets
    if p.exists() and not p.is_dir():
        with open(p, "r", encoding="utf-8") as f:
            targets = json.load(f)
    elif not p.exists():
        print("Warning: targets.json not found. Initializing empty targets.")
        targets = {}
        

def sgn(x):
    return (x > 0) - (x < 0)

def expsgn(x):
    return (x > 1) - (x < 1)
        
def update_goalhists():
    """
        Update value of goalhist in each target since last goalhist.
    """
    failed_goals = []
    complete_goals = []
    for (t, d) in targets.items():
        starttime = d["starttime"]
        rate = d["dailyrate"]
        goal = d["goal"]
        gh = d["goalhist"]
        gf = d["function"]
        
        first_value = d["valuehist"][0][1]
        if not gh:
            gh = safe_firstgoal(first_value, rate, goal, starttime, gf)
        last_date = dt.fromisoformat(d["valuehist"][-1][0])
        last_value = d["valuehist"][-1][1]

        # Find latest goal time and value in goalhist:
        (lt, lv) = (dt.fromisoformat(gh[-1][0]), gh[-1][1])

        # Step through, updating goal time and value daily       
        ct = dt.now(pytz.timezone("UTC"))
        d1 = timedelta(hours=24)
        # Todo: have us also step through valuehist since start,
        # to catch days we went over/under...?
        while lt < (ct - d1):
            if gf == "linear":
                lt = lt + d1
                if rate > 0:
                    lv = min(lv + rate, goal)
                elif rate <= 0:
                    lv = max(lv + rate, goal)
                    
                if lv * sgn(rate) >= goal * sgn(rate):
                    complete_goals.append(t)
                    if last_value * sgn(rate) > goal * sgn(rate):
                        print(f"WARNING: Not maintaining goal!: {t}, goal: {goal}, value: {last_value}")
                        failed_goals.append(t)
                else:
                    gh.append((lt.isoformat(), lv))

                if last_value * sgn(rate) < lv * sgn(rate):
                    failed_goals.append(t)
                    print(f"Goal {t} failed on {lt}: goal {lv}, value {last_value}")
                    continue
            
                if (last_value+3*rate) * sgn(rate) < lv * sgn(rate):
                    print(f"WARNING: Goal {t} will fail in 2 days from {lt}:",
                          f"{lt}: goal {lv}, value {last_value}")

            elif gf == "exponential":
                lt = lt + d1
                if rate > 1:
                    lv = min(lv * rate, goal)
                elif rate <= 1:
                    lv = max(lv * rate, goal)
                    
                if lv * expsgn(rate) >= goal * expsgn(rate):
                    complete_goals.append(t)
                    if last_value * expsgn(rate) > goal * expsgn(rate):
                        print(f"WARNING: Not maintaining goal!: {t}, goal: {goal}, value: {last_value}")
                        failed_goals.append(t)
                else:
                    gh.append((lt.isoformat(), lv))

                if last_value * expsgn(rate) < lv * expsgn(rate):
                    failed_goals.append(t)
                    print(f"Goal {t} failed on {lt}: goal {lv}, value {last_value}")
                    continue
            
                if (last_value * rate**3) * expsgn(rate) < lv * expsgn(rate):
                    print(f"WARNING: Goal {t} will fail in 2 days from {lt}:",
                          f"{lt}: goal {lv}, value {last_value}")

        targets[t]["goalhist"] = gh

def update_values():
    for t, d in targets.items():
        v = get_value(t)
        save_value(t, v)
        
def plot_target(t: Key, valuetype="valuehist"):
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
    starttime = targets[t]["starttime"]
    rate = targets[t]["dailyrate"]
    goal = targets[t]["goal"]
    for d, v in targets[t]["goalhist"]:
        goaldates.append(dt.fromisoformat(d))
        goalvalues.append(v)
    
    plt.title(t)
    plt.plot(dates,values, color="b")
    plt.plot(goaldates, goalvalues, color="r")
    plt.show()

def safe_firstgoal(first_value, rate, goal, starttime, gf):
    if gf == "linear":
        if first_value * sgn(rate) >= goal * sgn(rate):
            # Goal already achieved at start.
            return (starttime, goal)
        else:
            if rate > 0:
                return ((dt.fromisoformat(starttime) +
                      timedelta(hours=24)).isoformat(),
                        min(first_value + rate, goal))
            else: #rate <= 0:
                return ((dt.fromisoformat(starttime) +
                         timedelta(hours=24)).isoformat(),
                        max(first_value + rate, goal))

    elif gf == "exponential":
        if first_value * expsgn(rate) >= goal * expsgn(rate):
            # Goal achieved.
            return (starttime, goal)
        else:
            if rate > 1:
                return ((dt.fromisoformat(starttime) +
                         timedelta(hours=24)).isoformat(),
                        min(first_value * rate, goal))
            else: #if rate <= 1:
                return ((dt.fromisoformat(starttime) +
                         timedelta(hours=24)).isoformat(),
                        max(first_value * rate, goal))
    else:
        raise ValueError
    
def add_target(key: Key, typ: str, fn: str, goal: float, starttime: str, rate: float, pth_or_cmd: str, startval: float):
    if startval == None and typ == "folder_size":
        startval = folder_size(Path(pth_or_cmd))
    if startval == None and typ == "bash_command":
        startval = bash_command(pth_or_cmd)
        
    if fn == "linear" or fn == "exponential":
        firstgoaltime, firstgoalval = safe_firstgoal(startval, rate, goal, starttime.isoformat(), fn)
    else:
        raise ValueError

    if typ == "folder_size":
        targets[key] = {
            "type": typ,
            "function": fn,
            "goal": goal,
            "starttime": starttime.isoformat(),
            "dailyrate": rate,
            "path": str(Path(pth_or_cmd)),
            "valuehist": [(starttime.isoformat(), startval)],
            "goalhist": [(firstgoaltime, firstgoalval)]
        }
    elif typ == "bash_command":
        targets[key] = {
            "type": typ,
            "function": fn,
            "goal": goal,
            "starttime": starttime.isoformat(),
            "dailyrate": rate,
            "cmd": pth_or_cmd,
            "valuehist": [(starttime.isoformat(), startval)],
            "goalhist": [(firstgoaltime, firstgoalval)]
        }

def add_target_interactive():
   """ Quick hack to allow me to add a folder without parsing command line arguments."""
   pass

def add_target_command(name, cmd, fn, rate, goal):
    add_target(name, "bash_command", fn, float(goal), dt.now(pytz.timezone("UTC")), float(rate), cmd, bash_command(cmd))

def add_target_folder(name, pth, fn, rate, goal):
    add_target(name, "folder_size", fn, float(goal), dt.now(pytz.timezone("UTC")), float(rate), pth, folder_size(Path(pth)))
               
def plot_targets():
    for t, d in targets.items():
        plot_target(t)
    
def make_report(t: Key):
    update_goalhists() # Good enough for MVP
 
def calculate_charges(t: Key):
    pass

def count_tabs():
    pass # I have a shell script which does this but don't want it here yet.


def count_emails():
    pass # Mail not yet integrated


def manual_update(t: Key):
    pass

def main():
    load_targets()

    parser = argparse.ArgumentParser(description = "Track progress towards goals in bash.")
    parser.add_argument("--add", dest="target_name", help="shortcut name (lookup key) for the new target")
    parser.add_argument("--path", dest="pth", help="folder path for folder_size goals")
    parser.add_argument("--cmd", dest="cmd", help="bash command for bash_command goals")
    parser.add_argument("--fn", "--function", dest="fn", default="linear", choices=["linear", "exponential"])
    parser.add_argument("--rate", "-r", type=float, default=0, dest="rate", help="growth rate. rate < 0 for decreasing linear, rate < 1 for decreasing exponential")
    parser.add_argument("--goal", "-g", type=float, default=0, dest="goal", help="final goal")

    args = parser.parse_args()

    if args.target_name:
        if args.pth and args.cmd:
            raise ValueError(f"You may only specify one of pth and cmd. Received pth={args.pth} and cmd={args.cmd}.")
        elif args.pth:
            add_target_folder(args.target_name, args.pth, args.fn, args.rate, args.goal)
        elif args.cmd:
            print(f"Adding command {args.cmd}. I hope that escapes properly. Test value: {bash_command(args.cmd)}")
            add_target_command(args.target_name, args.cmd, args.fn, args.rate, args.goal)
        else:
            raise ValueError(f"You must specify one of pth and cmd. Received pth={args.pth} and cmd={args.cmd}.")

    update_values()
    update_goalhists()
    save_targets()
    plot_targets()

if __name__ == "__main__":
    main()
