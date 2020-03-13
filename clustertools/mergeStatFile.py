#!/usr/bin/env python
# coding: utf-8

import sys
import re
import datetime
import click

linere = re.compile(r'''^#\s+([a-zA-Z]+)\s+=\s(.*)$''')
mergedlines = ['NumberOfRun', 'NumberOfEvents', 'NumberOfTracks', 'NumberOfSteps', 'NumberOfGeometricalSteps',
               'NumberOfPhysicalSteps', 'ElapsedTimeWoInit', 'ElapsedTime', 'StartDate', 'EndDate',
               'NumberOfMergedJobs', 'MeanPPS', 'MeanElapsedTime', 'MinElapsedTime', 'MaxElapsedTime']


def total_seconds(deltat):
    try:
        return float(deltat.total_seconds())
    except AttributeError: # total_seconds defined in 2.7
        total = 0.
        total += deltat.seconds
        total += deltat.microseconds*1e-6
        total += deltat.days*3600.*24.
        return total

def parse_stat_file(filename):
    keys = {}
    for line in open(filename,"r").readlines():
        match = linere.match(line)
        #assert(match is not None)
        if match is None:
            continue
        groups = match.groups()
        if groups[0] not in mergedlines:
            continue
        keys[groups[0]]=groups[1]
    return keys

def merge_keys(ikeys,jkeys):
    mindate = None
    maxdate = None
    keys = {}
    for line in mergedlines:
        value = None

        if line == 'NumberOfMergedJobs':
            try:
                ivalue = int(ikeys['NumberOfMergedJobs'])
                ivalue += 1
                value = str(ivalue)
            except KeyError:
                value = str(2)

        if line == 'MeanPPS':
            try:
                NumberOfEvents = int(keys['NumberOfEvents'])
                ElapsedTime = float(keys['ElapsedTime'])
                pps = NumberOfEvents/ElapsedTime
                value = str(pps)
            except ValueError:
                pass

        if line == 'MeanElapsedTime':
            try:
                ElapsedTime = float(keys['ElapsedTime'])
                NumberOfMergedJobs = int(keys['NumberOfMergedJobs'])
                MeanElapsedTime = ElapsedTime/NumberOfMergedJobs
                value = str(MeanElapsedTime)
            except ValueError:
                pass

        if line == 'MinElapsedTime':
            try:
                jElapsedTime = float(jkeys['ElapsedTime'])
                iElapsedTime = float(ikeys['MinElapsedTime'])
                MinElapsedTime = min(iElapsedTime, jElapsedTime)
                value = str(MinElapsedTime)
            except KeyError:
                try:
                  jElapsedTime = float(jkeys['ElapsedTime'])
                  iElapsedTime = float(ikeys['ElapsedTime'])
                  MinElapsedTime = min(iElapsedTime, jElapsedTime)
                  value = str(MinElapsedTime)
                except ValueError:
                    pass

        if line == 'MaxElapsedTime':
            try:
                jElapsedTime = float(jkeys['ElapsedTime'])
                iElapsedTime = float(ikeys['MaxElapsedTime'])
                MaxElapsedTime = max(iElapsedTime, jElapsedTime)
                value = str(MaxElapsedTime)
            except KeyError:
                try:
                  jElapsedTime = float(jkeys['ElapsedTime'])
                  iElapsedTime = float(ikeys['ElapsedTime'])
                  MaxElapsedTime = max(iElapsedTime, jElapsedTime)
                  value = str(MaxElapsedTime)
                except ValueError:
                    pass

        if line == 'StartDate' or line == 'EndDate':
                ivalue = datetime.datetime.strptime(ikeys[line],"%a %b %d %H:%M:%S %Y")
                jvalue = datetime.datetime.strptime(jkeys[line],"%a %b %d %H:%M:%S %Y")
                if line=="StartDate":
                    value = min(ivalue,jvalue)
                    mindate = value
                if line=="EndDate":
                    value = max(ivalue,jvalue)
                    maxdate = value
                value = value.strftime("%a %b %d %H:%M:%S %Y")

        if value is None:
            try:
                ivalue = int(ikeys[line])
                jvalue = int(jkeys[line])
                value = ivalue + jvalue
                value = str(value)
            except ValueError:
                pass

        if value is None:
            try:
                ivalue = float(ikeys[line])
                jvalue = float(jkeys[line])
                value = ivalue + jvalue
                value = str(value)
            except ValueError:
                pass

        assert(value is not None)
        keys[line] = value
    if mindate is not None and maxdate is not None:
        speedup = float(keys["ElapsedTime"])/total_seconds(maxdate-mindate)
        keys["Speedup"] = str(speedup)
    return keys

def format_keys(keys):
    output = "\n".join("# %s = %s" % (line,keys[line]) for line in mergedlines)
    if "Speedup" in keys:
        output += "\n# Speedup = %s" % keys["Speedup"]
    return output

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.command(context_settings=CONTEXT_SETTINGS)
@click.option('-i', '--input1', default='', help='First input file to merge')
@click.option('-j', '--input2', default='', help='Second input file to merge')
@click.option('-o', '--output', default='', help='Output merged file')
def mergeStatFile(input1, input2, output):
    """
    \b
    Merge Stats file from Gate

    """
    mergeStatFileMain(input1, input2, output)


def mergeStatFileMain(input1, input2, output):
    ikeys = parse_stat_file(input1)
    jkeys = parse_stat_file(input2)
    keys  = merge_keys(ikeys,jkeys)
    outputFile = format_keys(keys)
    open(output,"w").write(outputFile)

if __name__ == "__main__":
    colorama.init()
    mergeStatFile()
