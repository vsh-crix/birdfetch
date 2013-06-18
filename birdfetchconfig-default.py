#/usr/bin/env python

import os

BGPQ3=True
SPOOLDIR="/var/tmp/birdfetch"

ASFILE="downstream.list"

LIST =  os.path.join('/usr/local/etc', 'rs1.list')

bird_template = os.path.join('/usr/local/etc', 'bird_template')
BIRD_OUTGOING_TMP = os.path.join('/etc/bird/prefixes')

OLD_DIR="old"
CUR_DIR="current"
DIFF_DIR="diff"
DIFFFILE = None                # None for autoformat file (date), or some name

flagEmailSend = False          # True for send email

emailSender = ""
emailRecepient = ""
emailSubject = "ripe exchange"
emailEncoding = "UTF-8"
emailRelay = ""

