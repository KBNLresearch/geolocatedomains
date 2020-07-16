#! /usr/bin/env python3

"""
Geolocate web domains. Input file is a text file where each line contains
1 web domain.

Author: Johan van der Knijff
Requirements:

1. Unix/Linux environment with 'host' tool installed,
   see https://www.unix.com/man-page/mojave/1/host
2. Python 3.5+ with MaxMind GeoIP2: https://pypi.org/project/geoip2/
3. Up-to date maxMind GeoIP2 City Database; free version (GeoLite2)
   available from https://dev.maxmind.com/geoip/geoip2/geolite2/
"""

import os
import sys
import csv
import argparse
import subprocess as sub
from shutil import which
import multiprocessing as mp
import time
import geoip2.database
import maxminddb

def parseCommandLine(parser):
    """Command line parser"""

    parser.add_argument('fileIn',
                        action='store',
                        type=str,
                        help='input file')
    parser.add_argument('fileOut',
                        action='store',
                        type=str,
                        help='output file')
    parser.add_argument('database',
                        action='store',
                        type=str,
                        help='GeoLite2 database')

    # Parse arguments
    arguments = parser.parse_args()
    return arguments


def errorExit(msg):
    """Print error to stderr and exit"""
    msgString = ('ERROR: ' + msg + '\n')
    sys.stderr.write(msgString)
    sys.exit(1)


def launchSubProcess(args):
    """Launch subprocess and return exit code, stdout and stderr"""
    try:
        p = sub.Popen(args, stdout=sub.PIPE, stderr=sub.PIPE, shell=False)
        output, errors = p.communicate()

        # Decode to UTF8
        outputAsString = output.decode('utf-8')
        errorsAsString = errors.decode('utf-8')

        exitStatus = p.returncode

    except Exception:
        # I don't even want to to start thinking how one might end up here ...

        exitStatus = -99
        outputAsString = ""
        errorsAsString = ""

    return exitStatus, outputAsString, errorsAsString


def getIP(domain):
    """Returns IP address from domain"""

    # Python in-built methods don't seem to work, so use external
    # host tool
    args = ['host']
    args.append(domain)

    hostStatus, hostOut, _ = launchSubProcess(args)

    # Set default value
    ip = ''

    if hostStatus != 0:
        pass
    else:
        outLines = hostOut.split('\n')
        for line in outLines:
            if "has address " in line:
                ip = line.split("has address ")[1].strip()
                break
    return ip


#def processDomain(domain, reader, q):
def processDomain(domain, q):
    """Process one domain"""

    # Get IP address
    ip = getIP(domain)

    # Init flag for validity of IP address
    hasValidIP = True

    # Defaults for output fields
    countryIsoCode = ''
    cityName = ''
    latitude = ''
    longitude = ''
    accuracyRadius = ''

    """  
    # Query database for IP address
    try:
        response = reader.city(ip)
    except ValueError:
        hasValidIP = False
    except geoip2.errors.AddressNotFoundError:
        hasValidIP = False

    if hasValidIP:
        try:
            countryIsoCode = response.country.iso_code
            cityName = response.city.name
            latitude = response.location.latitude
            longitude = response.location.longitude
            accuracyRadius = response.location.accuracy_radius
        except geoip2.errors.AddressNotFoundError:
            pass
    """

    # Add items to output row
    #outRow = [domain, hasValidIP, countryIsoCode, cityName, latitude, longitude, accuracyRadius]
    # TODO: make this work with CSV Writer
    outRow = domain + "," + str(hasValidIP) + "," + ip
    q.put(outRow)
    return outRow


def listener(fileOut, q):
    """Listens for messages on the q, writes to file"""

    with open(fileOut, "w", encoding="utf-8") as fOut:
        while 1:
            m = q.get()
            if m == "kill":
                break
            fOut.write(str(m) + "\n")
            fOut.flush()

def main():
    """Main function"""

    # Check if host tool is installed
    if which('host') is None:
        msg = "'host' tool is not installed"
        errorExit(msg)

    # Parse arguments from command line
    parser = argparse.ArgumentParser(description='Get geolocation information for list of domains')
    args = parseCommandLine(parser)
    fileIn = args.fileIn
    fileOut = args.fileOut
    database = args.database
    separator = ","

    # Create geolocation database reader object
    try:
        reader = geoip2.database.Reader(database)
    except FileNotFoundError:
        msg = "Cannot find database file"
        errorExit(msg)
    except maxminddb.errors.InvalidDatabaseError:
        msg = "Error reading database"
        errorExit(msg)

    # Read input file
    try:
        fIn = open(fileIn, "r", encoding="utf-8")
    except IOError:
        msg = 'could not read file ' + fileIn
        errorExit(msg)

    # Parse input file as comma-delimited data
    try:
        inCSV = csv.reader(fIn, delimiter=',')
        # No header so commented this out
        #inHeader = next(inCSV)
        inRows = [row for row in inCSV]
        fIn.close()
    except csv.Error:
        fIn.close()
        msg = 'Could not parse ' + fileIn
        errorExit(msg)

    # Delete output file if it already exists
    try:
        os.remove(fileOut)
    except IOError:
        pass


    """
    # Open output file in append mode
    try:
        fOut = open(fileOut, "a", encoding="utf-8")
    except IOError:
        msg = 'could not read file ' + fileOut
        errorExit(msg)

    # Create CSV writer object
    outCSV = csv.writer(fOut, delimiter=separator, lineterminator='\n')

    # Header for output file as list
    outHeader = ['domain', 'hasValidIP', 'countryIsoCode', 'cityName', 'latitude', 'longitude', 'accuracyRadius']

    # Write header to output file
    try:
        outCSV.writerow(outHeader)
    except IOError:
        msg = 'could not write file ' + fileOut
        errorExit(msg)
    """

    manager = mp.Manager()
    q = manager.Queue()    
    pool = mp.Pool(mp.cpu_count() + 2)

    #put listener to work first
    watcher = pool.apply_async(listener, (fileOut, q,))

    jobs = []

    for inRow in inRows:
        if inRow != []:
            domain = inRow[0]
            #outRow = processDomain(domain, reader, q)
            #job = pool.apply_async(processDomain, (domain, reader, q))
            job = pool.apply_async(processDomain, (domain, q))
            jobs.append(job)
            

            """
            # Write row to output file
            try:
                outCSV.writerow(outRow)
            except IOError:
                msg = 'could not write file ' + fileOut
                errorExit(msg)

    fOut.close()
    """

    # Collect results from workers through pool result queue
    for job in jobs:
        job.get()

    # Kill listener
    q.put("kill")
    pool.close()
    pool.join()


if __name__ == "__main__":
    main()
