# coding: utf-8
#!/usr/bin/python

import paramiko
import pexpect
import re
import sys
import subprocess
import sh
import os
import socket

class CParam(object):
    def __init__(self, ip, login, hostname, sshpass):
        self.ip = ip
        self.login = login
        self.hostname = hostname
        self.sshpass = sshpass
        try:
            self.sshobj = paramiko.SSHClient()
            self.sshobj.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.sshobj.connect(self.ip, username=self.login, password=self.sshpass, allow_agent=False,
                                look_for_keys=False)

        except socket.error:
            print "Make sure the device ", self.ip, " is reachable"

    def sendcmd(self, command):
        self.stdin, self.stdout, self.stderr = self.sshobj.exec_command(command)
        out = ''.join(self.stdout)
        #print out
        f = open('fout.tmp', 'w')
        for line in out:
            f.write(line)
        f.close()

    def sendcmds(self, commandlist):
        channel = self.sshobj.invoke_shell()
        stdin = channel.makefile('wb')
        stdout = channel.makefile('rb')
        stdin.write(commandlist)
        print stdout.read()
        stdout.close()
        stdin.close()

    def __del__(self):
        self.sshobj.close()

def GetInfo(stdout,reString):
    for line in stdout.readlines():
        if re.search(reString, line):
            #line.strip('\r\n')+'\r\n'
            return line
        else:
            return ""

def parsrouteflag(stdout, string):
    ribentry = GetInfo(stdout, string)
    if ribentry:
        prefixflag, prefixnh, prefixmetric, prefixlocalpref, prefixweight, prefixpath = parsribroute(ribentry)
        if re.search('s', prefixflag):
            return 'Suppressed'
        elif re.search('d', prefixflag):
            return 'Damped'
        elif re.search('h', prefixflag):
            return 'History'
        elif re.search('>', prefixflag):
            return 'Best'
        else:
            return 'The route doesn\'t exist'

    else:
        return 'The route doesn\'t exist'

def parsdampinfo(string):
    """ Parsing BGP dampening information """
    if string:
        damp = string.split()
        PENALTY = int(damp[2].replace(",", ""))
        FLAPS = int(damp[4])
        duration = damp[7]
        return PENALTY, FLAPS, duration
    else:
        return 0, 0, 0

### Device information
ip = "192.168.5.202"
login = "admin"
hostname = "SLB"
sshpass = "cisco"
tout = 30
command = 'sh ip slb reals'
#command = 'sh run'

while 1:

    # Get inf. from the router
    session = CParam(ip, login, hostname, sshpass)
    session.sendcmd(command)

    # Keep only useful columns
    COMMAND = "cat fout.tmp | awk {'print $1, $3, $5'} > resfile.tmp"
    subprocess.call(COMMAND, shell=True)

    # Remove useless lines
    lines = open('resfile.tmp').readlines()
    open('resfile.csv', 'w').writelines(lines[4:-1])

    #result = subprocess.check_output("cat fout.tmp | awk {'print $1'}")
    #print result
    realsrv = []
    weight = []
    conn = []
    f = open("resfile.csv", "r")
    for line in f:
        sline = line.split()
        realsrv.append(sline[0])
        weight.append(sline[1])
        conn.append(sline[2])

    os.system('clear')
    sign = '#'
    for i in range(len(realsrv)):
        print realsrv[i],' weight: ',weight[i],' conn: ',conn[i],': ','#' * int(conn[i])

