import urllib2
import urllib
import json

debug=True

def printJSON(data):
    print(json.dumps(data, indent=4, sort_keys=True)) 

def request(url,data=None,headers=None):
    if debug:
        print url

    try:
        if (data):
            response=urllib2.urlopen(urllib2.Request(url,data,headers))
        else:
            response=urllib2.urlopen(url)

        responseData = json.loads(response.read().encode("utf-8"))
        if debug:
            print "Got response."
        
    except urllib2.HTTPError as e:
        # This means something went wrong.
        print "Unable to request URL."
        print 'request: {}'.format(e.code)
        responseData=None

    except urllib2.URLError as e:
        # This means something went wrong.
        print "Unable to request URL:"
        print e.reason
        responseData=None

    if debug:
        print "-"
        print responseCode[responseData['response_code']]
        printJSON(responseData)
        print "-"
    
    return responseData
    
def getURL(url):
    return request(url)

def postJSON(url,jsonData):
    # parameters are a dictionary
    data = json.dumps(jsonData)
    
    # headers
    headers = {'Content-Type': 'application/json'}

    return request(url,data,headers)

responseCode = {
    0: "Successful request",
    1: "Initializing",
    2: "Internal Error",
    3: "Invalid Request",
    4: "Invalid Parameter",
    5: "Guarded",
    6: "Time Out",
    99: "Firmware Updating",
# (100s are Streaming Service related errors)
    100: "Access Error",
    101: "Other Errors",
    102: "Wrong User Name",
    103: "Wrong Password",
    104: "Account Expired",
    105: "Account Disconnected/Gone Off/Shut Down",
    106: "Account Number Reached to the Limit",
    107: "Server Maintenance",
    108: "Invalid Account",
    109: "License Error",
    110: "Read Only Mode",
    111: "Max Stations",
    112: "Access Denied"
}

class YamahaAVR:
    def __init__(self,host,debug=False):
        self.debug = debug
        self.host = host
        self.urlPrefix="http://%s/" % (self.host)
        
    def getFeatures(self):
        result=getURL(self.urlPrefix+"YamahaExtendedControl/v1/system/getFeatures")

    def getStatus(self):
        result=getURL(self.urlPrefix+"YamahaExtendedControl/v1/main/getStatus")
        self.power = result['power']
        self.input = result['input']


    def resetMenu(self):
        while True:
            menu=getURL(self.urlPrefix+"YamahaExtendedControl/v1/netusb/getListInfo?input=net_radio&index=0&size=8&lang=en")
            if (menu["menu_layer"] == 0):
                break
            else:
                getURL(self.urlPrefix+"YamahaExtendedControl/v1/netusb/setListControl?list_id=main&type=return&index=0&zone=main")

    def findMenuItemIndex(self,list_info,text):
        result = -1
        for i in range(len(list_info)):
            if (list_info[i]['text'] == text):
                result = i
                break
        if debug:
            print result
        
        return result
    
    def findMenuItem(self,text):
        menuStartIndex=0
        while True:
            menu=getURL(self.urlPrefix+"YamahaExtendedControl/v1/netusb/getListInfo?input=net_radio&index=%d&size=8&lang=en" % menuStartIndex)
            foundIndex = self.findMenuItemIndex(menu["list_info"],text)
            if (foundIndex > -1):
                foundIndex += menuStartIndex
                break
        
            menuStartIndex += 8
            if (menuStartIndex >= menu["max_line"]):
                break
    
        return foundIndex

        
    def selectMenuItem(self,index):
        getURL(self.urlPrefix+"YamahaExtendedControl/v1/netusb/setListControl?list_id=main&type=select&index=%s&zone=main" % (index))

    # {"index":9,"list_id":"main","string":"kkjg"}
    def setSearchString(self,index,text):
        parameters = {'index':index,'list_id':'main','string':text}
        postJSON(self.urlPrefix+"YamahaExtendedControl/v1/netusb/setSearchString",parameters)

    def addBookmark(self,index):
        getURL(self.urlPrefix+"YamahaExtendedControl/v1/netusb/manageList?list_id=main&type=add_bookmark&index=%d&timeout=0" % (index))


    