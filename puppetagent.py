#! /usr/bin/env python

import sys
import os
import datetime
import argparse
import yaml

"""
    NRPE plugin to check if Puppet agent works properly.
    Extracts the age from last_run_summary.yaml and also verifies
    the syntax of the yaml file.
"""

summary = '/var/lib/puppet/state/last_run_summary.yaml'


def ok(message):
    print 'OK: %s' % message
    sys.exit(0)


def warning(message):
    print 'WARN: %s' % message
    sys.exit(1)


def critical(message):
    print 'CRIT: %s' % message
    sys.exit(2)


def unknown(message):
    print 'UNKNOWN: %s' % message
    sys.exit(3)


def time_prettyfy(secs):
    """Returns a human readable time description"""

    days = secs // 86400
    hours = (secs % 86400) // 3600
    minutes = (secs % 3600) // 60
    seconds = secs % 60
    message = '%d seconds ago' % seconds
    if minutes:
        message = '%d minutes and %s' % (minutes, message)
    if hours:
        message = '%d hours, %s' % (hours, message)
    if days:
        message = '%d days, %s' % (days, message)
    return message


def optionsparser():
    parser = argparse.ArgumentParser()
    parser.add_argument("-w", "--warn", dest="warn", type=int, default=1200,
                        help="seconds after last Puppet run which issues a warning")
    parser.add_argument("-c", "--crit", type=int, dest="crit", default=2700,
                        help="seconds after last Puppet run which are critical")
    arguments = parser.parse_args()

    try:
        warn_seconds = arguments.warn
        crit_seconds = arguments.crit

    except Exception, exc:
        unknown('Unable to parse arguments: %s' % exc)

    if not os.path.isfile(summary):
        # Should perhaps be CRIT
        warning('Puppet has never run, no %s found.' % summary)

    return warn_seconds, crit_seconds

def getyamlfile(summary):
    """Get time information from yaml file"""

    summaryfile = open(summary)
    summarymap = yaml.safe_load(summaryfile)
    summaryfile.close()
    # Check if the yaml file has correct entries
    # If "events" is missing, the puppet run failed for some reason.
    # Also, we check the yaml file for failures puppet detected itself.
    try:
        failures = summarymap["events"]["failure"]

    except Exception, exc:
        critical('Yaml file not properly formatted, last puppet run failed.')

    if failures:
        critical('Puppet status file lists failures.')

    return summarymap

def main():
    warn_seconds, crit_seconds = optionsparser()
    yaml_map = getyamlfile(summary)

    # Check last_run time on summary file
    now = datetime.datetime.now()
    lastruntime = datetime.datetime.fromtimestamp(int(yaml_map["time"]["last_run"]))
    diff_time = now - lastruntime
    diff_sec = diff_time.total_seconds()
    lastrun = 'Puppet was last run %s' % time_prettyfy(diff_sec)

    if lastruntime > now:
        warning('Puppet summary file modified in the future!')
    elif diff_sec > crit_seconds:
        critical(lastrun)
    elif diff_sec > warn_seconds:
        warning(lastrun)
    else:
        ok(lastrun)

main()

