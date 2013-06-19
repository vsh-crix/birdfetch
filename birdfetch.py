#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''                                                                                                                                                                                       
Created on 14.06.2013                                                                                                                                                                     
                                                                                                                                                                                          
@author: vsh                                                                                                                                                                              
'''         


import os, sys
import difflib
import time
import email, mailer
import telnetlib, subprocess

try:
    from birdfetchconfig import *
except Exception as e:
    import warnings
    warnings.warn("Unable import local settings [%s]: %s" % (type(e),  e))
    os.sys.exit(1)


class ASGet:
    
    def __init__(self):

        self.spooldir = None
        self.asFile = None
        self.oldDir = None
        self.curDir = None

        self.currentAS = None
        self.currentASDescr = None

        self.downstreamList = []
        
        self.diffOutStream = None
        
        self.diffDir = None
        self.diffFile = None
        
        self.errCode = 0
        self.errDesc = None
    
        self.emailSender = None
        self.emailRecepient = None
        self.emailSubject = None
        self.emailEncoding = None
        self.emailRelay = None

        self.flagEmailSend = None
        
        self.asListPrefix = []
        self.asList = []

        self.s = ""
        self.m = ""

        self.tn = None

        fd = open(LIST, "rb")    
        fcontent = fd.readlines()
        fd.close()

        for i in fcontent:        
            try:
                self.asList.append(i)
            except Exception as ex:
                print >>sys.stderr, "Unable to save AS-SET  to list '%s'. Error: %s" % (self.asList, ex)
                sys.exit(-1)

        
    def init(self):
        self.__init__()
        

    def BirdPrefixGet(self, currentAS=None, currentHostDescr=None):
        
        sys.stderr.write("processing ...  => %s\n" % currentAS)
        self.asListPrefix.append(self.bgpGenList(currentAS))


        fd=open(bird_template, 'r')                                                                                                                      
        fcontent=fd.readlines()                                                                                                                              
        fd.close() 
        
        for i in self.asListPrefix:
            for l in i:
                _fcontent = "" 
                for line in fcontent:  
                    _fcontent += line 
                    _fcontent = _fcontent.replace('@@AS@@', l.replace("-","_"))
                    _fcontent = _fcontent.replace('@@NET@@', i[l])
        
                fd=open("%s/%s" % (BIRD_OUTGOING_TMP, l.lower() + ".conf"), 'wb') 
                fd.write(_fcontent)
                fd.close()
                self.downstreamList.append("%s\t%s" % (l, i[l]))

    def makedirs(self, dirPath=None):
        if dirPath is None:        return
        try:
            if os.path.exists(dirPath) is False:
                os.makedirs(dirPath)
                os.chmod(dirPath, 0o755)
        except Exception as ex:
            print >>sys.stderr,"Unable to create a directory '%s'. Error: %s" % (dirPath, ex)
            sys.exit(-1)

    def saveDownstreamList(self, filePath=None):
        if filePath is None:
            print >>sys.stderr, "File to save downstream list is not specified. Aborting."
            sys.exit(-1)
        try:
            fp = open(filePath, "wb")
            for _as in self.downstreamList:
                fp.write("%s\n" % _as)
            fp.close()
            os.chmod(filePath, 0o644)
        except Exception as ex:
            print >>sys.stderr, "Unable to save downstream list to file '%s'. Error: %s" % (filePath, ex)
            sys.exit(-1)
    
    def diffCurrentVSOldAS(self, currentASPath=None, oldASPath=None, diffPath=None):
        self.diffFile = diffPath
    
        f1 = None
        f2 = None
        diffList = []
        _diffList = []
        diffString = None
        
        try:
            if os.path.exists(oldASPath) is False:
                open(oldASPath, "wb").close()
            
            fp = open(oldASPath, "rb")
            f1 = fp.readlines()
            fp.close()
            
            fp = open(currentASPath, "rb")
            f2 = fp.readlines()
            fp.close()
        except Exception as ex:
            print >>sys.stderr, "Unable to read files '%s' and '%s' while making a diff. Error: %s" % (oldASPath, currentASPath, ex)
            sys.exit(-1)

        if f1 is None or f2 is None:
            print >>sys.stderr, "Unable to make a diff between '%s' and '%s'" % (oldASPath, currentASPath)
            sys.exit(-1)

        # Save diff of two full (true) filenames to diff file
        
        if self.diffFile is None:
            self.diffFile = "%s.diff" % time.strftime("%Y-%m-%d", time.localtime())
        
        self.diffFile = "%s/%s/%s/%s" % (self.spooldir, self.currentAS, self.diffDir, self.diffFile)
        
        try:
            fp = open(self.diffFile, "wb")
            for line in difflib.unified_diff(f1, f2, fromfile=oldASPath, tofile=currentASPath):
                f1 = fp.write(line)
            fp.close()
        except Exception as ex:
            print >>sys.stderr, "Unable to make a diff between '%s' and '%s' and save to %s. Error: %s" % (oldASPath, currentASPath, self.diffFile, ex)
            sys.exit(-1)

        # Format a diff list to end user
        try:
            fp = open(self.diffFile, "rb")
            _diffList = fp.readlines()
            fp.close()
        except Exception as ex:
            print >>sys.stderr, "Unable to load a diff from '%s'. Error: %s" % (self.diffFile, ex)
            sys.exit(-1)
            
        lc = 0
        diffList.append("--- Old List")
        diffList.append("+++ Current List")
        for line in _diffList:
            if lc >= 2:
                diffList.append(line)
            lc += 1
            
        diffString = ""
        for diffLine in diffList:
            diffString += diffLine
        
        self.diffOutStream = ""
        
        self.diffOutStream += "-------------------------------\r\n"
        self.diffOutStream += "%s - %s\r\n" % (self.currentAS, self.currentASDescr)
        self.diffOutStream += "-------------------------------\r\n"
        self.diffOutStream += "Current AS List:"
        if f2 is None or len(f2) == 0:
            self.diffOutStream += " Empty\r\n"
        else:
            self.diffOutStream += "\r\n"
            for i in f2:
                self.diffOutStream += "%s\r\n" % i.strip().replace("\n", "")
        self.diffOutStream += "\r\n"
        self.diffOutStream += "Old AS List:"
        if f1 is None or len(f1) == 0:
            self.diffOutStream += " Empty\r\n"
        else:
            self.diffOutStream += "\r\n"
            for i in f1:
                self.diffOutStream += "%s\r\n" % i.strip().replace("\n", "")
        self.diffOutStream += "\r\n"
        self.diffOutStream += "\r\n"
        self.diffOutStream += "Diff List:"
        if diffList is None or len(diffList) == 2:
            self.diffOutStream += " No differences\r\n"
	    return
        else:
            self.diffOutStream += "\r\n"
            for i in diffList:
                self.diffOutStream += "%s\r\n" % i.strip().replace("\n", "")
        
        self.diffOutStream += "\r\n\r\n\r\n"
        
        self.emailSubject = "%s for %s" % (self.emailSubject, self.currentAS)
        
        self.sendMail(self.emailRecepient, self.emailSubject, self.diffOutStream)
        
    def moveCurrentASToOld(self, AS=None):
        if AS is None:        pass
        else:                self.currentAS = AS
        
        fcontList = None
        fcontString = None

        oldASPath        = "%s/%s/%s/%s" % (self.spooldir, self.currentAS, self.oldDir, self.asFile)
        currentASPath        = "%s/%s/%s/%s" % (self.spooldir, self.currentAS, self.curDir, self.asFile)
                        
        try:
            if os.path.exists(currentASPath) is False:        return
            
            fp = open(currentASPath, "rb")
            fcontList = fp.readlines()
            fp.close()
            
            fcontString = ""
            for _as in fcontList:
                fcontString += _as
            
            fp = open(oldASPath, "wb")
            fp.write(fcontString)
            fp.close()
            os.chmod(oldASPath, 0o644)
        except Exception as ex:
            print >>sys.stderr, "Unable to copy current as list to old'. Error: %s" % ex
            sys.exit(-1)

    def bgpGenList(self, currentAS=None):

        if BGPQ3:
            _asPrefixlist = subprocess.Popen(["/usr/local/bin/bgpq3", "-3", "-P", "-R 24", "-m 24", "-l%s" % currentAS,  currentAS], stdout = subprocess.PIPE)
        else:
            _asPrefixlist = subprocess.Popen(["/usr/bin/bgpq", "-H", "-P", "-c", "-q", "-A", "-R 24", "-l%s" % currentAS,  currentAS], stdout = subprocess.PIPE)
        asPrefixlist = _asPrefixlist.stdout.read().splitlines()
        out = []
        _out = ""
        birdPrefix = ""
        dataBlock = {} 
    
        for i in asPrefixlist:
            if i.startswith("!"):       continue
            if i.startswith("no"):      continue
            else:
                i = i.split()[4]
                l = i.split("/")[1]
                if l == "24":
                    l = ""
                    i = i + l
                    out.append(i)
                    continue
                l = "{%s,24}" % l
                i = i + l
                out.append(i)
    
        birdPrefix = '[%s];' % ', '.join(out)            
        dataBlock[currentAS] = birdPrefix

        return dataBlock


    def sendMail(self, fieldRecipient=None, fieldSubject=None, fieldBody=None, attachSet=[], fieldSender=None):
        if self.flagEmailSend is False:        return
        if fieldSender is None:
            fieldSender = self.emailSender
        if fieldRecipient is None:
                print >>sys.stderr, "Unable to mail report: Error: destination email recepient is not specified."
                sys.exit(-1)
        message = mailer.Message(From=fieldSender, To=fieldRecipient, charset=self.emailEncoding)
        message.Subject = fieldSubject
        message.Body = fieldBody

        if (len(attachSet) > 0):
            for i in attachSet:
                message.attach(i)

        sender = mailer.Mailer(self.emailRelay)
        try:
            sender.send(message)
        except Exception as ex:
            print >>sys.stderr, "Unable to send email to %s. Error: %s" % (fieldRecipient, ex)
            sys.exit(-1)
            

    def printPage(self):
        if self.httpPage is None:        pass
        else:
            for i in self.httpLines:
                print(i)


    def printDownstreamList(self):
        if len(self.downstreamList) == 0:
            print ("No links")
            return
        
        for _as in self.downstreamList:
            print (_as)

def main():


    asObject = ASGet()
    
    for _as in asObject.asList:

        if len(_as) == 1:        continue
        _as = _as.split(".")
        asSet = _as[0]
        
        asObject.init()
        asObject.spooldir = SPOOLDIR
        asObject.asFile = ASFILE
        asObject.oldDir = OLD_DIR
        asObject.curDir = CUR_DIR
        
        asObject.diffDir = DIFF_DIR
        asObject.diffFile = DIFFFILE
        
        asObject.currentAS = asSet
        asObject.currentASDescr = asSet

        asObject.emailSender = emailSender
        asObject.emailRecepient = emailRecepient
        asObject.emailSubject = emailSubject
        asObject.emailEncoding = emailEncoding
        asObject.emailRelay = emailRelay
        
        asObject.flagEmailSend = flagEmailSend

        oldPathDir = "%s/%s/%s" % (asObject.spooldir, asObject.currentAS, asObject.oldDir)
        curPathDir = "%s/%s/%s"        % (asObject.spooldir, asObject.currentAS, asObject.curDir)
        diffPathDir = "%s/%s/%s" % (asObject.spooldir, asObject.currentAS, asObject.diffDir)

        asObject.makedirs(oldPathDir)
        asObject.makedirs(curPathDir)
        asObject.makedirs(diffPathDir)
        asObject.BirdPrefixGet(asObject.currentAS, asObject.currentASDescr)
        asObject.saveDownstreamList("%s/%s" % (curPathDir, asObject.asFile))
        asObject.diffCurrentVSOldAS("%s/%s" % (curPathDir, asObject.asFile), "%s/%s" % (oldPathDir, asObject.asFile))
        asObject.moveCurrentASToOld()


main()
