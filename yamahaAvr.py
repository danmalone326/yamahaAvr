import urllib2
import urllib
import json
import sys

debug=False


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
    def __init__(self,host,debug=False,showProgress=True):
        self.debug = debug
        self.showProgress = showProgress
        self.host = host
        self.urlPrefix="http://%s/YamahaExtendedControl/v1" % (self.host)
        self.getFeatures()
        self.current={}
        self.setZone(self.getZoneList()[0])
        
    def __printJSON(self,data):
        print(json.dumps(data, indent=4, sort_keys=True)) 

    def __request(self,url,data=None,headers=None):
        if debug:
            print url

        if self.showProgress:
            print '\bO',
            sys.stdout.flush()
        
        try:
            if (data):
                response=urllib2.urlopen(urllib2.Request(url,data,headers))
            else:
                response=urllib2.urlopen(url)

            responseData = json.loads(response.read().decode("utf-8"))
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
        
        if self.showProgress:
            print '\b\b.',
            sys.stdout.flush()
        
        return responseData
    
    def __getURL(self,url):
        return self.__request(url)

    def __postJSON(self,url,jsonData):
        # parameters are a dictionary
        data = json.dumps(jsonData)
    
        # headers
        headers = {'Content-Type': 'application/json'}

        return self.__request(url,data,headers)

    def getFeatures(self):
            result=self.__getURL(self.urlPrefix+"/system/getFeatures")
            self.features=result
        
    def getZoneList(self):
        result = []
        for zone in self.features['zone']:
            result.append(zone['id'])
        return result
    
    def getZone(self):
        return self.current.zone
        
    def setZone(self,zone):
        if (zone in self.getZoneList()):
            self.current['zone'] = zone
            self.getStatus(zone)
        else:
            print('bad zone: %s' % zone)

    def getStatus(self,zone='main'):
        result=self.__getURL(self.urlPrefix+"/%s/getStatus" % (zone))
        self.status=result
        self.current['input'] = result['input']
        self.current['power'] = result['power']

    def setPower(self,zone='main',power='standby'):
        result=self.__getURL(self.urlPrefix+"/%s/setPower?power=%s" % (zone,power))

    def powerOn(self,zone='main'):
        self.setPower(zone,'on')

    def powerStandby(self,zone='main'):
        self.setPower(zone,'standby')

    def powerToggle(self,zone='main'):
        self.setPower(zone,'toggle')
    
    def setInput(self,zone='main',input='',mode='autoplay_disabled'):
        result=self.__getURL(self.urlPrefix+"/%s/setInput?input=%s&mode=%s" % (zone,input,mode))

    def mute(self,zone='main'):
        self.setMute(True)
    
    def unmute(self,zone='main'):
        self.setMute(False)

    def setMute(self,zone='main',enable=True):
        if enable:
            enableString='True'
        else:
            enableString='False'
        result=self.__getURL(self.urlPrefix+"/%s/setMute?enable=" % (zone,enableString))

    def getListInfo(self,input='net_radio',index=0):
        return self.__getURL(self.urlPrefix+"/netusb/getListInfo?input=%s&index=%d&size=8&lang=en" % (input,index))
    
    def getFullListInfo(self,input='net_radio'):
        currentIndex=0
        fullListInfo = self.getListInfo(input,currentIndex)
        
        while (True):
            currentIndex += 8
            if (currentIndex > fullListInfo['max_line']):
                break
            fullListInfo['list_info'].extend(self.getListInfo(input,currentIndex)['list_info'])
        
        return fullListInfo

    def resetMenu(self,input='net_radio'):
        while True:
            menu=self.__getURL(self.urlPrefix+"/netusb/getListInfo?input=%s&index=0&size=8&lang=en" % input)
            if (menu["menu_layer"] == 0):
                break
            else:
                self.__getURL(self.urlPrefix+"/netusb/setListControl?list_id=main&type=return&index=0")

    def findMenuItemIndex(self,list_info,text,thumbnail=None):
        result = -1
        for i in range(len(list_info)):
            if ((list_info[i]['text'] == text) and 
                (thumbnail is None or (list_info[i]['thumbnail'] == thumbnail))):
                result = i
                break
        if debug:
            print result
        
        return result
    
    def findMenuItem(self,text,thumbnail=None):
        menu = self.getFullListInfo(input='net_radio')
        foundIndex = self.findMenuItemIndex(menu["list_info"],text,thumbnail)
   
        return foundIndex
        
    def selectMenuItem(self,index):
        self.__getURL(self.urlPrefix+"/netusb/setListControl?type=select&index=%s" % (index))

    # {"index":9,"list_id":"main","string":"kkjg"}
    def setSearchString(self,index,text):
        parameters = {'index':index,'list_id':'main','string':text}
        self.__postJSON(self.urlPrefix+"/netusb/setSearchString",parameters)

    def manageList(self,type='add_bookmark',index=0,timeout=5000):
        return self.__getURL(self.urlPrefix+"/netusb/manageList?type=%s&index=%d&timeout=%d" % (type,index,timeout))

    def addBookmark(self,index):
        return self.manageList(type='add_bookmark',index=index)
        
    def removeBookmark(self,index):
        return self.manageList(type='remove_bookmark',index=index)

    def cdRadio(self):
        self.resetMenu()
        index = self.findMenuItem(text='Radio')
        self.selectMenuItem(index=index)
        
    def cdFavorites(self):
        self.cdRadio()
        index = self.findMenuItem(text='Favorites')
        self.selectMenuItem(index=index)
        
    def startSearch(self,text,thumbnail=None):
        self.cdRadio()
        index = self.findMenuItem(text='Search')
        self.setSearchString(index=index,text=text)

    def doSearch(self,text,thumbnail=None):
        self.startSearch(text=text,thumbnail=thumbnail)
        index = self.findMenuItem(text=text,thumbnail=thumbnail)
        return index
        
    def getMenu(self):
        menu = self.getFullListInfo(input='net_radio')
        return menu
