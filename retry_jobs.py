#!/usr/bin/python
"""
Retrying jenkins jobs through REST API using autojenkins library (https://github.com/txels/autojenkins/).

The script accepts path to a json config file of the following format:

{"jobs":
 [
     "job1",
     "job2"
 ],
 "pass_file": "/home/johndoe/raw_pass",
 "log_file": "/home/johndoe/.autojenkins_log.txt",
 "jenkins_url": "http://jenkins.somecompany.com",
 "user": "johndoe"
}

@author: Sergey Evstifeev
"""
import json
from autojenkins import Jenkins
import logging
import sys

LOG_LEVEL = logging.DEBUG


def get_pass(pass_file):
    with open(pass_file, "r") as passfile:
        return passfile.read().replace('\n', '')


def init_jenkins(jenkins_url, user, pass_file):
    return Jenkins(jenkins_url, auth=(user, get_pass(pass_file)))


def is_building(jenkins, jobname):
    return jenkins.last_build_info(jobname)['building']


def is_in_queue(jenkins, jobname):
    return jenkins.job_info(jobname)['inQueue']


def is_last_build_successful(jenkins, jobname):
    return jenkins.last_build_info(jobname)['result'] == 'SUCCESS'


def load_config(config_filename):
    with open(config_filename, 'r') as json_file:
        return json.load(json_file)


def needs_a_retry(jenkins, jobname):
    building = is_building(jenkins, jobname)
    in_queue = is_in_queue(jenkins, jobname)
    build_successful = is_last_build_successful(jenkins, jobname)
    logging.debug("JOB: %s, BUILDING: %s, IN_QUEUE: %s, SUCCESSFUL: %s", jobname, building, in_queue, build_successful)
    return (not building) and (not in_queue) and (not build_successful)


def retry(jenkins, jobname):
    jenkins.build(jobname)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print "Usage: ", sys.argv[0], "config_file"
        sys.exit(1)

    config_file = sys.argv[1]
    config = load_config(config_file)

    log_file = config['log_file']
    jenkins_url = config['jenkins_url']
    user = config['user']
    pass_file = config['pass_file']
    log_file = config['log_file']
    jobs = config['jobs']

    logging.basicConfig(filename=log_file, level=LOG_LEVEL, format='%(asctime)s %(message)s')

    jenkins = init_jenkins(jenkins_url, user, pass_file)
    for job in jobs:
        if needs_a_retry(jenkins, job):
            logging.info('RETRYING: %s', job)
            retry(jenkins, job)
