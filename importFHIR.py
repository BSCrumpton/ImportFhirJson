import json, requests, sqlite3, os, argparse, itertools

defaultServer="https://apps.hdap.gatech.edu/omoponfhir2/fhir/"
defaultFolder="/home/bcrumpton3-gtri/Documents/AllOfUs/ImportFhirJson/test"
authTypes=["basic","SSO"]
defaultDB="OmopMapping.db"

def getFileList(path):
    jsonFiles=[]
    for root, dirs, files in os.walk(path):
        for name in files:
            if name.endswith((".json")):
                print(name)
                full_path = os.path.join(root, name)
                jsonFiles.append(full_path)
    return jsonFiles

def DBSetup(conn):
    c=conn.cursor()
    c.execute('CREATE TABLE IDMap (oldID text, resourceType text, newID text);')
    conn.commit()

def mappingExists(conn,entity):
    c=conn.cursor()
    # c.execute("SELECT * from IDMap WHERE oldID=?;",(oldID,))
    oldID=entity.get('id')
    resourceType=entity.get('resourceType')
    c.execute("SELECT * from IDMap WHERE oldID='{}' AND resourceType='{}';".format(oldID,resourceType))
    if(c.fetchone()):
        return True
    else:
        return False

def fixEntity(conn,entity):
    c=conn.cursor()
    resourceType=entity.get('resourceType')
    if(resourceType=="Observation"):
        refrence=entity.get('subject').get('reference').split('/')
        referenceType=reference[0]
        referenceID=reference[1]
        c.execute("SELECT * from IDMap WHERE oldID='{}' AND resourceType='{}';".format(referenceID,referenceType))
        result=c.fetchone()
        if(result):
            referenceID=result[2]
            return entity,True
        else:
            return entity,False
        

def postEntity(entity)

def processFile(conn,entity):
    c=conn.cursor()
    oldID=entity.get('id')
    resourceType=entity.get('resourceType')
    if(resourceType!="Patient"):
        entity,successful=fixEntity(conn,entity)
        if(not successful):
            return False
    # postEntity()
    c.execute("INSERT INTO IDMap VALUES('{}','{}','{}');".format(oldID,resourceType,oldID))
    conn.commit()
    return True

def cleanUp(conn,args):
    c=conn.cursor()
    c.execute("SELECT * from IDMap;")
    rows=c.fetchall()
    for row in rows:
        deleteFromServer(row,args)

def deleteFromServer(row,args):
    response = requests.delete("{}{}/{}".format(args.server,row.get('resourceType'),row.get('newID')),auth=requests.auth.HTTPBasicAuth('***REMOVED***','***REMOVED***'))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="""
        This will go through all files in the specified folder ({} by default), and import them to the omoponfhir server provided ({} by default)
        """.format(defaultServer,defaultFolder))
    parser.add_argument("-s","--server",type=str,default=defaultServer,help="Omop Server URL to import data")
    parser.add_argument("-f","--folder",type=str,default=defaultFolder,help="folder location with all JSON files. This can have sub folders")
    parser.add_argument("--auth-type",type=str,choices=authTypes,help="what type of authentication the server utilizes. ")
    parser.add_argument("-d","--database-name",type=str,default=defaultDB,help="sqlite file name that will hold the ID mapping results")
    parser.add_argument('--clean',help='will go over all mapping objects in the provided database, and remove them from the provided server',action='store_true')
    args=parser.parse_args()

    fileList=getFileList(args.folder)
    conn=sqlite3.connect(args.database_name)
    if(args.clean)
    DBSetup(conn)
    print(len(fileList))
    print(fileList)
    iteration=0
    addedFiles=[]
    skippedFiles=[]
    maxIterations=len(fileList)*len(fileList)
    while fileList:
        if(iteration>=maxIterations):
            print("we have a problem file. ")
            print("exiting")
            break
        file=fileList[0]
        print(file)
        with open(file,'r') as f:
            try:
                tempString=json.load(f)
            except json.JSONDecodeError:
                print("file {} is invalid json".format(file))
                print("popping file, ",file)
                fileList.pop(0)
                continue
        # do I need to handle bundles? 
        if(tempString.get('resource',None)):
            # print("format one")
            entity=tempString.get('resource')
        else:
            # print("format two")
            entity=tempString
        if(mappingExists(conn,entity)):
            # This entity already exists
            skippedFiles.append(file)
            fileList.pop(0)
            print("popping file, ",file)
            continue
        else:
            if(processFile(conn,entity)):
                # we successfully processed the file
                addedFiles.append(file)
                fileList.pop(0)
            else:
                # we failed importing
                fileList.append(file)
                fileList.pop(0)
                iteration=iteration+1
                continue
        
        iteration=iteration+1
    print("files not imported: ",fileList)
    print(addedFiles)
    print("files skipped as they're already imported: ",skippedFiles)