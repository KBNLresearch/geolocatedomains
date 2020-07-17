#! /usr/bin/env python3


import time
import multiprocessing as mp

def doSomething(textIn, q):
    """Do some silly text processing"""

    time.sleep(1)
    textOut = textIn + " is rubbish"
    q.put(textOut)
    return textOut

def listener(q):
    """Listens for messages on the q, print to screen"""

    while 1:
        message = q.get()
        if message == "kill":
            break
        print(message)
 
def main():
    """Main function"""

    manager = mp.Manager()
    q = manager.Queue()
    pool = mp.Pool(processes=2)

    # Put listener to work first
    pool.apply_async(listener, (q,))
  
    # Create list with 5 million text elements
    inRows = ["This script"]*5000000

    # Jobs list
    jobs = []
    
    # Iterate over list and add jobs to the pool
    for inRow in inRows:
        job = pool.apply_async(doSomething, (inRow, q))
        jobs.append(job)
                
    # Collect results from workers through pool result queue
    for job in jobs:
        job.get()

    # Kill listener
    q.put("kill")
    pool.close()
    pool.join()

if __name__ == "__main__":
    main()
