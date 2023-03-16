#!/usr/bin/python3

import json
import subprocess
import time

logging_enabled = True

# *** create log file if it doesn't exist ***
subprocess.run(["touch", "/var/log/btrfs-scrub.log"])

# *** open file and log the script has started ***
try:
    with open("/var/log/btrfs-scrub.log", "w+") as file:
        file.write("BTRFS Scrub started" + time.asctime(time.localtime(time.time())))
except OSError: 
    # if for some reason we still can't write to the log file, disable logging
    print ("Unable to open log file.  Logging is disabled")
    logging_enabled = False

# *** Get a list of partitions and their filetype and mountpoint ***
devices = json.loads(subprocess.check_output(["lsblk", "-n", "-i", "--json",
                                                           "-o", "NAME,FSTYPE,MOUNTPOINT"]).decode())

devices = devices["blockdevices"] # cut out everything except for "blockdevices"

# *** log discovered partitions ***
if logging_enabled:
    try:
        with open("/var/log/btrfs-scrub.log", "w") as file:
            file.write("Discovered devices:\n")
            file.write(json.dumps(devices))
    except OSError:
        print ("Logging error")

# *** add desired partitions to the scrub list ***
dev_list = tuple(devices) # change the devices list into a tuple
scrub_list = [] # this is the list of devices we want to run btrfs_scrub on

for device in dev_list: 
    if device['mountpoint'] == '/mnt' or device['mountpoint'] == '/media': 
        # if the device is in these locations, it is probably removable and we don't want to include it
        continue
    elif device == []:  # if the device is empty, we skip
        continue
    elif 'children' in device: # the case where the device has children partitions
        for child in device['children']:
            if "fstype" not in child.keys():  # if it doesn't have a label, skip
                continue
            elif child['fstype'] == 'btrfs' and child['mountpoint'] != None:
                # if the child is btrfs and the mountpoint isn't null, add it
                scrub_list.append("/dev/" + child['name'])
    else: # this is the case where the device does not have children
        if device['fstype'] == 'btrfs' and device['mountpoint'] != None:
            # if the device is btrfs and the mountpoint isn't null, add it
            scrub_list.append("/dev/" + device['name'])

# *** log the devices we decided to run butter_scrub on ***
if logging_enabled:
    try:
        with open("/var/log/btrfs-scrub.log", "a") as file:
            file.write("\nSelected scrub devices: ")
            for item in scrub_list:
                file.write(item)
            file.write("\nBeggining scrub process.  Check /var/lib/btrfs/ folder for results")
    except OSError:
        print ("Logging error")

# *** run the btrfs scrub command on each partition, pausing until each is finished
for partition_name in scrub_list:
    results = subprocess.run(["btrfs", "scrub", "start", "-B", partition_name])

    #command option -B: do not background and print scrub statistics when finished



