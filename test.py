#! /usr/bin/env python3


import sys
import time
import multiprocessing as mp

def doSomething(textIn, q):
    """Do some silly text processing"""

    #time.sleep(0.01)
    textOut = textIn + " is rubbish"
    q.put(textOut)
    return textOut

def listener(q):
    """Listens for messages on the q, print to screen"""

    while 1:
        message = q.get()
        if message == "kill":
            break
        #print(message)
        pass
 
def main():
    """Main function"""

    manager = mp.Manager()
    q = manager.Queue()
    pool = mp.Pool(processes=8)

    # Put listener to work first
    pool.apply_async(listener, (q,))
  
    # Create list with 5 million text elements
    inRows = ["This script"]*6000000

    # Jobs list
    jobs = []

    count = 0
    
    # Iterate over list and add jobs to the pool
    for inRow in inRows:
        count += 1
        job = pool.apply_async(doSomething, (inRow, q))
        jobs.append(job)
        #print(len(jobs))

        if count%1000 == 0:
            print("Count: " + str(count))
            print("Cache size (before): " + str(len(pool._cache)))
            if len(pool._cache) > 10000:
                print("Waiting for cache to clear...")
                job.wait() # Where last is assigned the latest ApplyResult
                print("Cache size (after): " + str(len(pool._cache)))
                
    # Collect results from workers through pool result queue
    for job in jobs:
        job.get()

    # Kill listener
    q.put("kill")
    pool.close()
    pool.join()

if __name__ == "__main__":
    main()
