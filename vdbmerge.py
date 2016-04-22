#!/usr/bin/env python3

#
# vdbmerge.py - script for merging Vdbench output files generated with VDBTest
#
# Author: Ramon A. Lovato (ramonalovato.com)
# For: DeepStorage, LLC (deepstorage.net)
#

import argparse
import re
import os
import csv
import os.path
from vdbconvert import vdbconvert

def getArgs():
    parser = argparse.ArgumentParser(
        description='convert and merge Vdbench "flatfile.html" output files from VDBTest into a single CSV')

    # Positional
    parser.add_argument("rootDir", type=str,
        help="parent directory containing the VDBTest output directories")
    parser.add_argument("outPath", type=str,
        help="where to save the output file")

    return parser.parse_args()

def parseResults(root):
    flatFiles = getFlatFiles(root)
    tables, averages = makeTables(flatFiles)
    return tables, averages

def makeTables(flatFiles):
    # Initial element is None since test indexing begins at 1.
    tables = [None]
    averages = [None]
    for f in flatFiles:
        partials = os.path.split(f)
        if len(partials) < 2:
            continue
        machineString, runString = getMachineAndRun(partials[-2])
        if machineString == None or runString == None:
            continue
        machine = int(machineString)
        run = int(runString)
        while len(tables) <= machine:
            tables.append([None])
            averages.append([None])
        while len(tables[machine]) <= run:
            tables[machine].append(None)
            averages[machine].append(None)
        lines, aves = getLines(f)
        tables[machine][run] = lines
        averages[machine][run] = aves
    return tables, averages

def makeOutputLines(tables, averages):
    allLines = []
    m = 1
    while m < len(tables):
        r = 1
        allLines.append(["--- Machine {} ---".format(m)])
        allLines.append(tables[m][1][0])
        while r < len(tables[m]):
            for line in tables[m][r][1:]:
                allLines.append(line)
            r += 1
        m += 1
        allLines.append([])
        allLines.append([])
    return allLines


def getLines(f):
    with open(f, "r") as inFile:
        f = filter(lambda x: not x.isspace() and not re.match(r"^[<>\*]", x),
            inFile.readlines())
        lines = [re.split(r"\s+(?=\S)", x.strip()) for x in f]
        isAveLam = lambda x: len(x) > 2 and re.match(r"^avg_\S+", x[2])

        # Extract averages.
        averages = []
        i = 0
        iMax = len(lines)
        while i < iMax:
            if isAveLam(lines[i]):
                averages.append(lines.pop(i))
                iMax -= 1
            else:
                i += 1
        return lines, averages

def getKeys(lines):
    return re.split("\s+", lines[0].strip())

def getMachineAndRun(s):
    mReg = re.compile(r"vdb(\d+)")
    rReg = re.compile(r"__output_(\d+)__")
    tokens = re.split(r"\/|\\", s)
    machine = None
    runID = None
    for t in tokens:
        mMatch = mReg.match(t)
        rMatch = rReg.match(t)
        if mMatch:
            machine = mMatch.group(1)
        elif rMatch:
            runID = rMatch.group(1)

    if machine == None or runID == None:
        return None, None
    else:
        return machine, runID

def getFlatFiles(dir):
    flatFiles = []
    for root, dirs, files in os.walk(dir):
        for f in files:
            if f == 'flatfile.html':
                path = os.path.join(root, f)
                flatFiles.append(path)
                print('Found "{}"'.format(path))
    return flatFiles

def buildOutput(lines, outFile):
    outWriter = csv.writer(outFile)
    outWriter.writerows(lines)

# Main.
def main():
    args = getArgs()

    tables, averages = parseResults(args.rootDir)
    allLines = makeOutputLines(tables, averages)

    with open(args.outPath, "w", newline="") as outFile:
        buildOutput(allLines, outFile)

if __name__ == "__main__":
    main()