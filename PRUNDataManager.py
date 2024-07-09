import sys
import requests, json

APPDATAFIELD = "applicationData"

# TODO: Find a way to recommend that calling applications create and supply their own default configs that are customised to the app use.
DEFAULTCONFIG = dict({
                "auth": None,
                "group": None,
                APPDATAFIELD: {},
            })

def customGet(url, headers=None):
    r = requests.Response()
    for i in range(3):
        try:
            r = requests.get(url, headers = headers, timeout=10)
            break;
        except requests.exceptions.Timeout:
            r.status_code = -1
            print("PDM: Request Timeout, Loop "+str(i))
    return r

class DataManager():
    materialData = dict()
    fleetData = dict()
    shipRegistrationIndex = dict()
    userData = dict()
    planetNIdToNameIndex = None
    planetNameToNIdIndex = None
    CXdata = None

    def __init__(self,configDict = {},defaultConfig = DEFAULTCONFIG):
        print("PDM: Initializing")
        self.configPath = configDict["ConfigPath"] if "ConfigPath" in configDict else None # Where to look for the config 
        self.statusBar = configDict["QtStatusBar"] if "QtStatusBar" in configDict else None # A tuple containing (the QtStatusBar object, Start Index), so that the PDM can manage notifications itself
        # NOTE: Right Now, the PDM is hardcoded with Qt modules in mind in this section. In the future, I want to have everything external to this module (Like Qt) be handled by an import of PDM.
        self.badConfig = False
        try:
            print("PDM: Starting Configuration Load")
            with open(self.configPath,"r") as configFile:
                self.config = json.load(configFile)
                for key in defaultConfig:
                    if key not in self.config:
                        self.config = defaultConfig
                        self.badConfig = True # Indicate that the user might not want to overwrite their existing config
                        print("PDM: Bad config, resetting to default")
                        break
        except:
            print("PDM: Load failure, loading default")
            self.config = defaultConfig
        print("PDM: Config load finished")
        self.loadMaterialInformation() # TODO: Move this to a connect() function that can be used to check the online state of the program simultaneously. 
    
    def getFioHeaders(self):
        return {
            "Authorization" : self.config["auth"],
            }

    def loadMaterialInformation(self):
        print("PDM: Fetching Materials")
        r = customGet("https://rest.fnar.net/material/allmaterials")
        if r.status_code == 200:
            print("PDM: Material Fetch Success")
            rContent = json.loads(r.content)
            for material in rContent:
                self.materialData[material["Ticker"]] = material
        else:
            print("PDM: Could not Fetch Materials: "+ str(r.status_code))
            () #TODO: Signal inability to download material information
        return
    
    def getMaterialStorageProperties(self,ticker):
        return self.materialData[ticker]["Weight"], self.materialData[ticker]["Volume"]

    def online(self): # TODO: Rework to be less application specific: Either guarantee that self.materialInformation is loaded when online (by having it be loaded) or find an alternative indicator.
        return len(self.materialData) != 0

    def validMaterialTicker(self, material):
        if len(self.materialData) == 0:
            return True 
            # This is to allow offline use, otherwise even valid materials would be rejected when there isn't a valid connection. 
            # Programs should instead use the online() method to check whether or not the PDM has data if you wish to prevent operations in offline mode.
        return material in self.materialData

    def loadWorkforceData(self):
        print("PDM: Loading Workforce Needs")
        if not self.fetchWorkforceNeeds():
            return False
        if self.config["auth"] != None:
            self.trackedUsers = (self.user)
            if self.config["group"] != None:
                self.fetchGroupData()
                if self.groupData == None:
                    ()
                    # TODO: signal to user that provided Group ID is not working.
                else:
                    self.trackedUsers = list()
                    for user in self.groupData["GroupUsers"]:
                        self.trackedUsers.append(user["GroupUserName"])
                    self.trackedUsers = tuple(self.trackedUsers)
                    if self.user not in self.trackedUsers:
                        ()
                        print("PDM: Authenticated User is not in the tracked group!")
                        # TODO: signal to user that they are not in the tracked group, and this might cause problems!
        return True

    def save(self,configPath = None, forceWrite = False):
        if self.badConfig and not forceWrite:
            print("PDM: Aborted config write due to bad config")
            return False
        if configPath == None:
            configPath = self.configPath
        try:
            with open(configPath,"w") as configFile:
                json.dump(self.config, configFile, indent = 6)
            print("PDM: Config Write Succeeded")
            return True
        except:
            print("PDM: Config Write Failed")
            return False

    def authenticate(self): # TODO: Make this use the QtStatusBar if given
        print("PDM: Authenticating")
        self.user = None
        if self.config["auth"] == None:
            self.authed = -1
            print("PDM: No Authentication Key In Config")
            return self.authed
        r = customGet("https://rest.fnar.net/auth", headers=self.getFioHeaders())
        if r.status_code == 200:
            print("PDM: Success!")
            self.authed = 0
            self.user = r.text
        else:
            print("PDM: Authentication Error: "+str(r.status_code))
            self.authed = 1
        return self.authed
    
    def getCurrentUser(self):
        return self.user
    
    def getAuthState(self):
        return self.authed

    def fetchGroupData(self):
        print("PDM: Fetching Group Data")
        r = customGet("https://rest.fnar.net/auth/group/"+self.config["group"])
        if r.status_code != 200:
            print("PDM: Fetch Failed: "+str(r.status_code))
            self.groupData = None
            return False
        self.groupData = json.loads(r.content)
        print("PDM: Group Data Loaded")
        return True

    def fetchWorkforceNeeds(self):
        print("PDM: Fetching Workforce Needs")
        self.workerData = None
        r = customGet("https://rest.fnar.net/global/workforceneeds")
        if r.status_code != 200:
            print("PDM: Fetch Failed: "+str(r.status_code))
            return False
        rContent = json.loads(r.content)
        self.workerData = dict()
        for entry in rContent:
            self.workerData[entry["WorkforceType"]] = dict()
            for need in entry["Needs"]:
                self.workerData[entry["WorkforceType"]][need["MaterialTicker"]] = need["Amount"]
        print("PDM: Workforce Need Data Loaded")
        return True

    def getUserPlanetBurn(self,user,planet): # TODO: Complete
        r = customGet("https://rest.fnar.net/workforce/"+user+"/"+planet, headers=self.getFioHeaders())

        raise NotImplementedError


    def getTrackedPlanets(self): # TODO: Rework to be less application specific. Move field under config applicationData field
        return self.config["planets"]

    def getTrackedSystems(self): # TODO: Rework to be less application specific. Move field under config applicationData field
        return self.config["systems"]

    def getAppData(self,field):
        if field in self.config[APPDATAFIELD]:
            return self.config[APPDATAFIELD][field]
        return None
    
    def setAppData(self,field,data):
        if field in self.config[APPDATAFIELD]:
            self.config[APPDATAFIELD][field] = data
            return True
        return False
    
    def createAppData(self,field,reset = False):
        print("PDM: Creating New AppData field: "+field)
        if reset or field not in self.config[APPDATAFIELD]:
            self.config[APPDATAFIELD][field] = None
            return True
        return False
    
    def deleteAppData(self,field):
        if field in self.config[APPDATAFIELD]:
            del self.config[APPDATAFIELD][field]
            return True
        return False
    
    def getAllPlanetWorkerMats(self): # TODO: Rework to be less application specific
        print("PDM: Loadng Planet Worker Materials")
        matDict = dict()
        for planet in self.config["planets"]:
            trackedWorkforces = self.config["planets"][planet]
            matDict[planet] = list()
            for workforce in trackedWorkforces:
                matDict[planet].extend(self.workerData[workforce].keys())
            matDict[planet] = set(matDict[planet])
        return matDict

    # Return values: -1: Invalid argument format    0: All good    1: Could not fully fetch data
    def fetchFleetsByUsers(self,usernames): # Fetches fleet data from all the users in the input.
        #TODO: Refactor this function
        print("PDM: Fetching fleet data by Username")
        if type(usernames) != set:
            print("PDM: Invalid Argument Format")
            return -1
        status = 0
        tmpShipData = []
        tmpFlightData = []
        for username in usernames:
            print("PDM: Fetching data for "+username)
            print("PDM: 1/3")
            r = customGet("https://rest.fnar.net/ship/ships/"+username, headers=self.getFioHeaders())
            if r.status_code not in (200,204):
                status = 1
                print("PDM: Aborting data fetch for "+username)
                continue
            else:
                tmpShipData.extend(json.loads(r.content) if r.status_code == 200 else [])
            print("PDM: 2/3")
            self.fetchUserStorageData(username)
            print("PDM: 3/3")
            r = customGet("https://rest.fnar.net/ship/flights/"+username, headers=self.getFioHeaders())
            if r.status_code not in (200,204):
                status = 1
                continue
            else:
                tmpFlightData.extend(json.loads(r.content) if r.status_code == 200 else [])
        
        #Combining the ship information under one key
        print("PDM: Combining Ship Data")
        for ship in tmpShipData:
            self.fleetData[ship["Registration"]] = ship
            self.shipRegistrationIndex[ship["ShipId"]] = ship["Registration"]
        for ship in tmpFlightData:
            self.fleetData[self.shipRegistrationIndex[ship["ShipId"]]].update(ship)
        
        #transplants the ship's storage information into the ship's entry
        print("PDM: Getting Ship Store Data")
        for transponder in self.fleetData:
            hasStoreId = "StoreId" in self.fleetData[transponder]
            hasUsername = "UserNameSubmitted" in self.fleetData[transponder]
            if hasStoreId and hasUsername:
                if self.fleetData[transponder]["UserNameSubmitted"].upper() not in self.userData:
                    print("PDM: No userData available for user "+self.fleetData[transponder]["UserNameSubmitted"]+" of transponder "+transponder)
                    continue
                storageData = self.getUserStoreById(self.fleetData[transponder]["UserNameSubmitted"],self.fleetData[transponder]["StoreId"])
                if storageData:
                    self.fleetData[transponder]["Storage"] = storageData
                    print("PDM: Ship "+transponder+" storage linked")
                else:
                    print("PDM: Ship "+transponder+" storage object not available")
            else:
                if not hasStoreId:
                    print("PDM: Ship "+transponder+" does not possess a StorageId!")
                if not hasUsername:
                    print("PDM: Ship "+transponder+" does not possess a submission Username!") # TODO: fallback onto registered name if it exists in config. 
                    # Possibly create an internal data structure that can be populated through external function calls if the calling program knows this data already (say, through the appData in a config file, which this module cannot otherwise utilise)

        print("PDM: Fleet Fetch Complete")
        return status
    
    def getUserStoreById(self,username,storeId):
        username = username.upper()
        if username not in self.userData:
            return None
        if 'storageData' not in self.userData[username]:
            return None
        for storage in self.userData[username]['storageData']:
            if storage['StorageId'] == storeId:
                return storage
        return None

    def fetchUserStorageData(self,username): #TODO: add a refresh=False argument to deal with intentionally refreshing stale data
        username = username.upper()
        if username not in self.userData:
            if not self.fetchUserInfo(username):
                print("PDM: Aborting Storage Fetch")
                return False
        print("PDM: Fetching User Storage Data: "+username)
        r = customGet("https://rest.fnar.net/storage/"+username,headers=self.getFioHeaders())
        if r.status_code in (200, 204):
            print("PDM: Success!")    
        else: 
            print("PDM: Failed") 
            return False
        match r.status_code:
            case 204:
                print("PDM: No Storage Data for user")
                self.userData[username]["storageData"] = []
            case 200:
                self.userData[username]["storageData"] = json.loads(r.content)
        return True
                
    
    def fetchUserInfo(self,username):
        print("PDM: Fetching User Info for "+username)
        r = customGet("https://rest.fnar.net/user/"+username, headers=self.getFioHeaders())
        if r.status_code == 200:
            print("PDM: Success!")
            self.userData[username.upper()] = json.loads(r.content)
            return True
        print("PDM: Failed")
        return False

    def getUserInfo(self,username):
        if username.upper() in self.userData:
            return self.userData[username.upper()]
        else:
            return self.userData[username.upper()] if self.fetchUserInfo(username) else {}
    
    def getFleetData(self):
        return self.fleetData

    def getShipData(self, transponder):
        return self.fleetData[transponder] if transponder in self.fleetData else {}

    def updateAllData(self):
        print("PDM: Refreshing All Data")
        raise NotImplementedError
        #TODO: Make this function go over all presently **loaded** data and refresh it from the FIO API. Also maybe have it have a lockout (I.e. can only be called once a minute or once every 5 minutes)

    def fetchPlanetNameData(self):
        # NOTE: This function fetches solely the naturalId and Name pairs of planets! This is much faster than fetchPlanetFullData(), but less comprehensive.
        # It is recommended to avoid using fetchPlanetFullData() unless absolutely necessary, instead using fetchPlanetData() or searchForPlanet().
        print("PDM: Fetching Planet Name Data")
        r = customGet("https://rest.fnar.net/planet/allplanets")
        if r.status_code != 200:
            print("PDM: Failed")
            return False
        print("PDM: Success!")
        c = json.loads(r.content)
        self.planetNIdToNameIndex = {}
        self.planetNameToNIdIndex = {}
        for element in c:
            self.planetNIdToNameIndex[element["PlanetNaturalId"].upper()] = element["PlanetName"]
            self.planetNameToNIdIndex[element["PlanetName"].upper()] = element["PlanetNaturalId"]
        print("PDM: Planet Data Loaded")
        return True
    
    def fetchPlanetFullData(self):
        # NOTE: If you absolutely have to use this function, please async it. Otherwise, use any of the other planet functions.
        raise NotImplementedError
        return
    
    def fetchStationData(self):
        print("PMD: Fetching Station Data")
        r = customGet("https://rest.fnar.net/exchange/station")
        if r.status_code != 200:
            print("PDM: Failed")
            return False
        print("PDM: Success!")
        self.CXdata = json.loads(r.content)
        print("PDM: Station Data Loaded")
        return True

    def getPlanetNameIndexes(self):
        if not self.planetNIdToNameIndex:
            self.fetchPlanetNameData()
        return self.planetNIdToNameIndex or {}, self.planetNameToNIdIndex or {}
    
    def isPlanet(self,location):
        location = location.upper()
        if not self.planetNIdToNameIndex:
            return True, True # Defaults to True so that offline function is not impeded.
        return location in self.planetNIdToNameIndex, location in self.planetNameToNIdIndex
    
    def getPlanetNameFormat(self,name):
        pNID, pn = self.isPlanet(name)
        if not (pNID or pn):
            return name
        name = name.upper()
        if pNID:
            return self.planetNameToNIdIndex[self.planetNIdToNameIndex[name].upper()]
        if pn:
            return self.planetNIdToNameIndex[self.planetNameToNIdIndex[name].upper()]
        
    def getStationNameFormat(self,name):
        tmpBool, index = self.isStation(name)
        if not tmpBool:
            return name
        if name.upper() == (formattedName := self.CXdata[index]["NaturalId"]):
            return formattedName
        if name.upper() == (formattedName := self.CXdata[index]["Name"]):
            return formattedName
        return

    def isStation(self, location):
        for i in range(len(self.CXdata)):
            if location.upper() in (self.CXdata[i]["NaturalId"],self.CXdata[i]["Name"].upper()):
                return True, i
        return False, -1


    def isLocation(self, location):
        return self.isStation(location)[0] or (True in self.isPlanet(location))


if __name__ == "__main__":
    pdm = DataManager()
    pdm.fetchStationData()
    pdm.fetchPlanetNameData()
    pdm.fetchUserInfo("MysteriousWalrus")
    print("PDMTEST: "+ str(pdm.isLocation("VH-331a")))
    print(pdm.getPlanetNameFormat("PROMITOR"))