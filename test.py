#! /usr/bin/env python3


import os
import sys
import csv
import time
from shutil import which
import multiprocessing as mp

def getIP(domain, q):
    """Returns IP address from domain"""

    # Python in-built methods don't seem to work, so use external
    # host tool
    args = ['host']
    args.append(domain)

    time.sleep(2)

    outRow = [domain, "1234"]
    q.put(outRow)
    return outRow

def listener(fileIp, q):
    """Listens for messages on the q, writes to file"""

    # Open IP file in append mode
    try:
        fIp = open(fileIp, "a", encoding="utf-8")
    except IOError:
        msg = 'could not open file ' + fileIp

    # Create CSV writer object
    ipCSV = csv.writer(fIp, delimiter=",", lineterminator='\n')

    with open(fileIp, "a", encoding="utf-8") as fIp:
        while 1:
            outRow = q.get()
            if outRow[0] == "kill":
                fIp.close()
                break
            try:
                ipCSV.writerow(outRow)
            except IOError:
                msg = 'could not write file ' + fileIp
            fIp.flush()

def main():
    """Main function"""

    manager = mp.Manager()
    q = manager.Queue()
    #pool = mp.Pool(processes=processes, maxtasksperchild=maxtasksperchild)
    pool = mp.Pool(processes=2)

    # Put listener to work first
    pool.apply_async(listener, ("bullsh.csv", q,))

    jobs = []

    inRows = [["bitsgalore.org"]]*100
    
    for inRow in inRows:
        domain = inRow[0]
        job = pool.apply_async(getIP, (domain, q))
        jobs.append(job)
                
    # Collect results from workers through pool result queue
    for job in jobs:
        job.get()

    # Kill listener
    q.put(["kill", "kill"])
    pool.close()
    pool.join()

if __name__ == "__main__":
    main()
