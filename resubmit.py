#!/usr/bin/env python

import os
import sys
import urllib
import httplib
import re

from WMCore.WMSpec.WMWorkload import WMWorkloadHelper

reqmgrCouchURL = "https://cmsweb.cern.ch/couchdb/reqmgr_workload_cache"
#reqmgrHostname = "vocms144"
#reqmgrPort = 8687

def approveRequest(url,workflow):
    params = {"requestName": workflow,
              "status": "assignment-approved"}

    encodedParams = urllib.urlencode(params)
    headers  =  {"Content-type": "application/x-www-form-urlencoded",
                 "Accept": "text/plain"}

    conn  =  httplib.HTTPSConnection(url, cert_file = os.getenv('X509_USER_PROXY'), key_file = os.getenv('X509_USER_PROXY'))
    #conn  =  httplib.HTTPConnection(url)
    conn.request("PUT",  "/reqmgr/reqMgr/request", encodedParams, headers)
    response = conn.getresponse()
    if response.status != 200:
        print 'could not approve request with following parameters:'
        for item in params.keys():
            print item + ": " + str(params[item])
        print 'Response from http call:'
        print 'Status:',response.status,'Reason:',response.reason
        print 'Explanation:'
        data = response.read()
        print data
        print "Exiting!"
        sys.exit(1)
    conn.close()
    print 'Cloned workflow:',workflow
    return



def retrieveSchema(workflowName):
    specURL = os.path.join(reqmgrCouchURL, workflowName, "spec")
    helper = WMWorkloadHelper()
    #print "  retrieving original workflow...",
    helper.load(specURL)
    #print "done."
    schema = {}
    for (key, value) in helper.data.request.schema.dictionary_().iteritems():
        #print key
        if key == 'ProdConfigCacheID':
            schema['ProcConfigCacheID'] = value
	elif key=='ProcConfigCacheID':
	    schema['ProcConfigCacheID'] = value
	elif key=='RequestSizeEvents':
	    schema['RequestNumEvents'] = value
	elif value != None:
            schema[key] = value
    return schema

def submitWorkflow(schema):
    for schemaListItem in ["RunWhitelist", "RunBlacklist", "BlockWhitelist",
                           "BlockBlacklist"]:
        if schemaListItem in schema.keys():
            schema[schemaListItem] = str(schema[schemaListItem])
            
    encodedParams = urllib.urlencode(schema, True)
    headers  =  {"Content-type": "application/x-www-form-urlencoded",
                 "Accept": "text/plain"}

    conn  =  httplib.HTTPSConnection("cmsweb.cern.ch", cert_file = os.getenv('X509_USER_PROXY'), key_file = os.getenv('X509_USER_PROXY'))
    #conn  =  httplib.HTTPConnection("vocms13.cern.ch:8687")
    #conn  =  httplib.HTTPConnection("%s:%s" % (reqmgrHostname, reqmgrPort))
    print "  submitting new workflow..."
    conn.request("POST",  "/reqmgr/create/makeSchema", encodedParams, headers)
    response = conn.getresponse()
    print response.status, response.reason
    data = response.read()
    print data
    details=re.search("details\/(.*)\'",data)
    return details.group(1)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print "Usage:"
        print "  ./resubmit WORKFLOW_NAME"
        sys.exit(0)

    #print "Going to attempt to resubmit %s..." % sys.argv[1]
    schema = retrieveSchema(sys.argv[1])
    newWorkflow=submitWorkflow(schema)
    approveRequest('cmsweb.cern.ch',newWorkflow)
    sys.exit(0)