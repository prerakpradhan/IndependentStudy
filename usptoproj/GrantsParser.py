import xml.etree.ElementTree as ET
from xml.etree.ElementTree import iterparse
from StringIO import StringIO
import time
import MySQLProcessor
import re
import SourceParser
import os
import multiprocessing
import LogProcessor
import urllib


class GrantsParser:
    """
    UPET(USPTO Patent Exploring Tool)
        provides Python code for downloading, parsing, and loading USPTO patent bulk data into a local MySQL database.
    Website:
        http://abel.lis.illinois.edu/upet/
    Authors:
        Qiyuan Liu (http://liuqiyuan.com, qliu14@illinois.edu),
        Vetle I. Torvik (http://people.lis.illinois.edu/~vtorvik/, vtorvik@illinois.edu)
    Updated:
        12/09/2012

    Modified for Full Text Patent Download  
    Author: Prerak Pradhan
    Updated : 10/25/2014
    """
    """
    Used to parse Patent Grants data and populate them into the database.
    1. Download
    2. Parse
    3. Load
    """
    def __init__(self):
        self.pubCountry=''
        self.pubNo=''
        self.patNum='' # used to fix patent numbers
        self.kind=''
        self.pubDate=''
        self.appCountry=''
        self.appNo=''
        self.appNoOrig='' #in the APS file, the usseries code corresponds to a different format
        self.appDate=''
        self.appType=''
        self.seriesCode=''

        # priority claims
        self.pcSequence=''
        self.pcKind=''
        self.pcCountry=''
        self.pcDocNum=''
        self.pcDate=''
        self.priClaim=[]
        self.priClaimsList=[]

        # international classification
        self.iClassVersionDate=''
        self.iClassLevel=''
        self.iClassSec='' #section
        self.iClassCls='' #mainclass
        self.iClassSub='' #subclass
        self.iClassMgr='' #main group
        self.iClassSgr='' #subgroup 
        self.iClassSps='' #symbol position
        self.iClassVal='' # classification value
        self.iClassActionDate=''
        self.iClassGnr=''  # generating office
        self.iClassStatus='' #status
        self.iClassDS=''  #data source
        self.iClassList=[]

        #national classification
        self.nClassCountry=''
        self.nClassMain=''
        self.nSubclass=''
        self.nClassInfo=''   #mainClass=nClassInfo[0:3] subClass=nClassInfo[3:len(nClassInfo)]
        self.nClassList=[]

        self.title=''

        # citations
        self.ctNum=''
        self.pctCountry=''  # pct : patent citation
        self.pctDocNo=''
        self.pctKind=''
        self.pctName=''
        self.pctDate=''
        self.pctCategory=''
        self.pctClassNation=''
        self.pctClassMain=''
        self.pctClassList=[]
        self.pcitation=[]
        self.pcitationsList=[]  # list of ALL pcitation
        self.pcitationsList_US=[]
        self.pcitationsList_FC=[]

        self.npctDoc=''
        self.npctCategory=''
        self.npcitation=[]
        self.npcitationsList=[] # list of npcitation

        self.claimsNum=''
        self.figuresNum=''
        self.drawingsNum=''

        # ommit us-related-documents

        # inventors info. 
        self.itSequence=''
        self.itFirstName=''  #it inventor
        self.itLastName=''
        self.itCity=''
        self.itState=''
        self.itCountry=''
        self.itNationality=''
        self.itResidence=''
        self.inventor=[]
        self.inventorsList=[]

        # attorney
        # attorney maybe organizations or, one or more than one person
        self.atnSequence=''
        self.atnLastName=''
        self.atnFirstName=''
        self.atnOrgName=''   
        self.atnCountry=''
        self.attorney=[]
        self.attorneyList=[]
    
        #assignee
        self.asnSequence=''
        self.asnOrgName=''
        self.asnRole=''
        self.asnCity=''
        self.asnState=''
        self.asnCountry=''
        self.assignee=[]
        self.assigneeList=[]

        #examiners
        #primary-examiner & assistant-examiner
        self.exmLastName=''
        self.exmFirstName=''
        self.exmDepartment=''
        self.examiner=[]
        self.examinerList=[]

        self.abstract=''
        self.claims=''
        self.test=''  #used for testing

        self.position=1
        self.count=1

        self.csvPath_grant=os.getcwd()+'/CSV_G/grants.csv'
        
        self.csvPath_agent=os.getcwd()+'/CSV_G/agent.csv'
        self.csvPath_assignee=os.getcwd()+'/CSV_G/assignee.csv'
        self.csvPath_examiner=os.getcwd()+'/CSV_G/examiner.csv'
        self.csvPath_intclass=os.getcwd()+'/CSV_G/intclass.csv'
        self.csvPath_inventor=os.getcwd()+'/CSV_G/inventor.csv'
        self.csvPath_pubcit=os.getcwd()+'/CSV_G/pubcit.csv'
        self.csvPath_gracit=os.getcwd()+'/CSV_G/gracit.csv'
        self.csvPath_forpatcit=os.getcwd()+'/CSV_G/forpatcit.csv'
        self.csvPath_nonpatcit=os.getcwd()+'/CSV_G/nonpatcit.csv'
        self.csvPath_usclass=os.getcwd()+'/CSV_G/usclass.csv'

    def __ResetSQLVariables(self):
        # ***************** SQL ***************************
        self.sql_publication=[] #publications
        self.sql_grant=[] #grants

        self.sql_examiner=[]
        self.sql_assignee=[]
        self.sql_agent=[]
        self.sql_inventor=[]
        self.sql_usclass=[]
        self.sql_intclass=[]
        self.sql_pubcit=[]  #publication citations
        self.sql_gracit=[] #grant citations
        self.sql_forpatcit=[] #foreign patent citations
        self.sql_nonpatcit=[] #none-patent citations

    def __checkTag(self,x,tagName=''):
        if(x.tag==tagName):
            return True
        else:
            return False

    def __returnClass(self,s='D 2860'):
        """
        Main Class (3):'D02','PLT','000'
        SubClass (3.3): 
        """
        mc=s[0:3].replace(' ','')
        sc=s[3:len(s)]
        sc1=sc[0:3].replace(' ','0')
        sc2=sc[3:len(sc)].replace(' ','')
        if(len(mc)<=3):
            if(mc.find('D')>-1 and len(mc)==2):mc=mc[0]+'0'+mc[1]
            elif(len(mc)==2):mc='0'+mc
            elif(len(mc)==1):mc='00'+mc
        if(len(sc2)<=3):
            if(len(sc2)==2):sc2='0'+sc2
            elif(len(sc2)==1):sc2='00'+sc2
            elif(len(sc2)==0):sc2='000'
        clist=[mc,sc1+sc2]
        return clist

    def __returnDate(self,timeStr):
        if(len(timeStr)>7):
            return timeStr[0:4]+'-'+timeStr[4:6]+'-'+timeStr[6:8]
        else:
            return None

    def __returnInt(self,s):
        try:
            if(s=='' or s==None):return 'NULL';
            else:return int(s)
        except:return 'NULL'

    def __returnStr(self,s):
        try:
            if(s=='' or s==None):return '';
            else:return s.encode('utf-8').replace('"','\'').strip()
        except:return ''

    # ***** used to fix patent numbers *****
    def returnMatch(self,patternStr,inputStr):
        c=re.compile(patternStr)
        r=c.match(inputStr)
        return r

    def returnNewNum(self,oldPatNum):
        if(len(oldPatNum.strip())==9):
            self.patNum=oldPatNum[0:8]
        elif(len(oldPatNum.strip())==8):
            self.patNum=oldPatNum
        else:
            #raw_input('there is patent number whoes legth is nor 8 or 9! It is: {0}'.format(self.patNum))
            pass

        if(self.returnMatch('^[0-9]{8}$',self.patNum)):
            self.patNum=self.patNum[1:8]
            return self.patNum
        else:
            if(self.returnMatch('^[A-Za-z]{1,2}[0-9]{6,7}$',self.patNum)):
                c=re.compile('[0-9]')
                index_0=c.search(self.patNum).start()
                self.patNum=self.patNum[0:index_0]+self.patNum[index_0+1:len(self.patNum)]
                return self.patNum
            else:
                #raw_input('there is patent number out of expection! It is:{0}'.format(self.patNum))
                print 'exception...',oldPatNum
                return ''

    def returnAppNum(self,seriesCode,oldAppNum):
        if(str.upper(seriesCode.strip())=='D'):
            seriesCode='29'
        if(len(seriesCode.strip())==1):
            seriesCode='0'+seriesCode
        elif(len(seriesCode.strip())==0):
            seriesCode='xx'
        if(len(oldAppNum)==7):
            oldAppNum=oldAppNum[0:6]
        return seriesCode+oldAppNum       
            
    def extractXML4(self,xmlStr):      
        print '[Getting started to read xml into ElementTree...]'
        self.__ResetSQLVariables()
        btime=time.time()
        patentRoot=ET.fromstring(xmlStr)
        xmlStr = ""
        #patentRoot = iterparse(StringIO(xmlStr))
        #patentRoot=ET.ElementTree().parse('D:\PatentsData\PG_BD\haha.xml')
        print '[Finishing reading xml file into ElementTree, consuming time:{0}]'.format(time.time()-btime)
        print '[Getting started to parse XML and extract metadata...'
        btime=time.time()
        # regular info.
        for root in patentRoot.findall('us-patent-grant'):
            self.__init__()
            total = ""
            for claims in root.findall('claims'):
                for claim in claims.findall('claim'):
                    for total_claims in claim.findall('claim-text'): 
                        if total_claims.text:
                            total =total + "~~" + total_claims.text
                        for all_tags in total_claims.findall('.//'):
                            if all_tags.text:
                                total = total + " " + all_tags.text
            self.claims= total
            for r in root.findall('us-bibliographic-data-grant'):
                for pr in r.findall('publication-reference'):
                    for di in pr.findall('document-id'):
                        self.pubCountry=di.findtext('country')
                        self.pubNo=di.findtext('doc-number')
                        self.pubNo=self.returnNewNum(self.pubNo)
                        self.kind=di.findtext('kind')
                        self.pubDate=di.findtext('date')
                for ar in r.getiterator('application-reference'):
                    self.appType=ar.attrib['appl-type']
                    for di in ar.findall('document-id'):
                        self.appCountry=di.findtext('country')
                        self.appNo=di.findtext('doc-number')
                        self.appNoOrig=self.appNo
                        self.appDate=di.findtext('date')
                self.title=r.findtext('invention-title')
            #self.abstract=root.findtext('abstract')
            for abs in root.findall('abstract'):
                self.abstract=re.sub('<[^>]+>','',ET.tostring(abs)).strip()

            # ****** SQL Variables ********
            self.sql_grant.append([self.pubNo,self.__returnStr(self.title),
                                   self.__returnDate(self.pubDate),
                                   self.kind,
                                   self.seriesCode,
                                   self.__returnStr(self.abstract),
                                   self.__returnInt(self.claimsNum),
                                   self.__returnInt(self.drawingsNum),
                                   self.__returnInt(self.figuresNum),
                                   self.__returnStr(self.appNo),
                                   self.__returnStr(self.claims),
                                   self.__returnDate(self.appDate),
                                   self.appType,
                                   self.appNoOrig])

        print '===== GRANT ====='
        print len(self.sql_grant)
            #text=raw_input('press Y/y to continue!')
            #if(text=='Y' or text=='y'):continue
            #else:break
        print '[Finishing parsing XML to extract metadata, consuming time:{0}]'.format(time.time()-btime)

    def __returnElementText(self,xmlElement):
        if(ET.iselement(xmlElement)):
            elementStr=ET.tostring(xmlElement)
            return re.sub('<[^<]*>','',elementStr).strip()
        else:return ''

    def extractXML2(self,xmlStr):   
        """
        used for Patent Grant Bibliographic Data/XML Version 2.5 (Text Only)
        from 2002 - 2004
        A subset of the Patent Grant Data/XML (a.k.a., Grant Red Book) XML with 'B' tags
        """
        print 'Starting read xml.'
        self.__ResetSQLVariables()
        btime=time.time()
        patentRoot=ET.fromstring(xmlStr)
        print '[Finishing reading XML, Time:{0}]'.format(time.time()-btime)
        print 'Starting extract xml.'
        btime=time.time()
        for root in patentRoot.findall('PATDOC'): # us-patent-grant'):
            self.__init__()
            for r in root.findall('SDOBI'): #us-bibliographic-data-grant'):
                for B100 in r.findall('B100'): #PUBLICATION
                    self.pubNo=self.__returnElementText(B100.find('B110'))
                    self.pubNo=self.returnNewNum(self.pubNo)
                    self.kind=self.__returnElementText(B100.find('B130'))
                    self.pubDate=self.__returnElementText(B100.find('B140'))
                    self.pubCountry=self.__returnElementText(B100.find('B190'))
                for B200 in r.findall('B200'): # APPLICATION
                    self.appType=''
                    self.appCountry=''
                    self.appNo=self.__returnElementText(B200.find('B210'))
                    self.appNoOrig=self.appNo
                    self.appDate=self.__returnElementText(B200.find('B220'))
                    self.seriesCode=self.__returnElementText(B200.find('B211US'))
                for B500 in r.findall('B500'):
                    for B540 in B500.findall('B540'):
                        self.title=self.__returnElementText(B540) #TITLE
                    for B570 in B500.findall('B570'):
                        self.claimsNum=self.__returnElementText(B570.find('B577'))
                    for B590 in B500.findall('B590'):
                        for B595 in B590.findall('B595'):
                            self.drawingsNum=self.__returnElementText(B595)
                        for B596 in B590.findall('B596'):
                            self.figuresNum=self.__returnElementText(B596)
            total = ""
            for text in root.findall('SDOCL'):
                self.abstract=self.__returnElementText(text)
                for claims in text.findall('CL'):
                    total = total+ "~~"
                    for claim in claims.findall('CLM'):
                        for all_tags in claim.findall('.//'):
                            if all_tags.text:
                                total = total + " " + all_tags.text
            self.claims = total
            # ****** SQL Variables ********
            self.sql_grant.append([self.pubNo,self.__returnStr(self.title),self.__returnDate(self.pubDate),
                                   self.kind,self.seriesCode,self.__returnStr(self.abstract),self.__returnInt(self.claimsNum),
                                   self.__returnInt(self.drawingsNum),self.__returnInt(self.figuresNum),
                                   self.__returnStr(self.appNo),
                                   self.__returnStr(self.claims),
                                   self.__returnDate(self.appDate),
                                   self.appType,
                                   self.__returnStr(self.appNo)])

        print '===== GRANT ====='
        print len(self.sql_grant)
        print '[Finishing parsing XML to extract metadata, consuming time:{0}]'.format(time.time()-btime)
   
    def downloadZIP(self):
        print '- Starting download ZIP files.'
        st=time.time()
        sp=SourceParser.SourceParser()
        
        sp.getALLFormats()
        ls_xml4=sp.links_G_XML4  #396 412
        ls_xml2=sp.links_G_XML2 #157
        ls_xml24=sp.links_G_XML2_4 #52
        ls_aps=sp.links_G_APS #252 final 26
        for dLink in ls_xml4:
            exist_path=(os.getcwd()+'/ZIP_G/XML4/'+os.path.basename(dLink)).replace('\\','/')
            if(not os.path.exists(exist_path)):
               urllib.urlretrieve(dLink,exist_path)
               urllib.urlcleanup()
        for dLink in ls_xml2:
            exist_path=(os.getcwd()+'/ZIP_G/XML2/'+os.path.basename(dLink)).replace('\\','/')
            if(not os.path.exists(exist_path)):
                urllib.urlretrieve(dLink,exist_path)
                urllib.urlcleanup()
        for dLink in ls_xml24:
            exist_path=(os.getcwd()+'/ZIP_G/XML24/'+os.path.basename(dLink)).replace('\\','/')
            if(not os.path.exists(exist_path)):
                urllib.urlretrieve(dLink,exist_path)
                urllib.urlcleanup()
        for dLink in ls_aps:
            exist_path=(os.getcwd()+'/ZIP_G/APS/'+os.path.basename(dLink)).replace('\\','/')
            if(not os.path.exists(exist_path)):
                urllib.urlretrieve(dLink,exist_path)
                urllib.urlcleanup()
        print '[Downloaded ZIP files. Cost: {0}]'.format(time.time()-st)
		
    def writeCSV(self):
        print '- Starting write CSV files.'
        import csv
        st=time.time()
        self.f_grant=open(self.csvPath_grant,'ab')
        self.f_examiner=open(self.csvPath_examiner,'ab')
        self.f_agent=open(self.csvPath_agent,'ab')
        self.f_assignee=open(self.csvPath_assignee,'ab')
        self.f_inventor=open(self.csvPath_inventor,'ab')
        self.f_pubcit=open(self.csvPath_pubcit,'ab')
        self.f_gracit=open(self.csvPath_gracit,'ab')
        self.f_forpatcit=open(self.csvPath_forpatcit,'ab')
        self.f_nonpatcit=open(self.csvPath_nonpatcit,'ab')
        self.f_usclass=open(self.csvPath_usclass,'ab')
        self.f_intclass=open(self.csvPath_intclass,'ab')
        w_grant=csv.writer(self.f_grant,delimiter='\t',lineterminator='\n')
        w_grant.writerows(self.sql_grant)
        w_examiner=csv.writer(self.f_examiner,delimiter='\t',lineterminator='\n')
        w_examiner.writerows(self.sql_examiner)
        w_agent=csv.writer(self.f_agent,delimiter='\t',lineterminator='\n')
        w_agent.writerows(self.sql_agent)
        w_assignee=csv.writer(self.f_assignee,delimiter='\t',lineterminator='\n')
        w_assignee.writerows(self.sql_assignee)
        w_inventor=csv.writer(self.f_inventor,delimiter='\t',lineterminator='\n')
        w_inventor.writerows(self.sql_inventor)
        w_pubcit=csv.writer(self.f_pubcit,delimiter='\t',lineterminator='\n')
        w_pubcit.writerows(self.sql_pubcit)
        w_gracit=csv.writer(self.f_gracit,delimiter='\t',lineterminator='\n')
        w_gracit.writerows(self.sql_gracit)
        w_forpatcit=csv.writer(self.f_forpatcit,delimiter='\t',lineterminator='\n')
        w_forpatcit.writerows(self.sql_forpatcit)
        w_nonpatcit=csv.writer(self.f_nonpatcit,delimiter='\t',lineterminator='\n')
        w_nonpatcit.writerows(self.sql_nonpatcit)
        w_usclass=csv.writer(self.f_usclass,delimiter='\t',lineterminator='\n')
        w_usclass.writerows(self.sql_usclass)
        w_intclass=csv.writer(self.f_intclass,delimiter='\t',lineterminator='\n')
        w_intclass.writerows(self.sql_intclass)
        self.f_grant.close()
        self.f_examiner.close()
        self.f_agent.close()
        self.f_assignee.close()
        self.f_inventor.close()
        self.f_pubcit.close()
        self.f_gracit.close()
        self.f_forpatcit.close()
        self.f_nonpatcit.close()
        self.f_usclass.close()
        self.f_intclass.close()
        self.__ResetSQLVariables()
        print '[Written CSV files. Cost:{0}]'.format(time.time()-st)

    #write csv files for updating
    def writeCSV_update(self,suffix):
        print '- Starting write CSV files_update.'
        import csv
        st=time.time()
        self.f_grant=open(self.csvPath_grant+suffix,'ab')
        self.f_examiner=open(self.csvPath_examiner+suffix,'ab')
        self.f_agent=open(self.csvPath_agent+suffix,'ab')
        self.f_assignee=open(self.csvPath_assignee+suffix,'ab')
        self.f_inventor=open(self.csvPath_inventor+suffix,'ab')
        self.f_pubcit=open(self.csvPath_pubcit+suffix,'ab')
        self.f_gracit=open(self.csvPath_gracit+suffix,'ab')
        self.f_forpatcit=open(self.csvPath_forpatcit+suffix,'ab')
        self.f_nonpatcit=open(self.csvPath_nonpatcit+suffix,'ab')
        self.f_usclass=open(self.csvPath_usclass+suffix,'ab')
        self.f_intclass=open(self.csvPath_intclass+suffix,'ab')
        w_grant=csv.writer(self.f_grant,delimiter='\t',lineterminator='\n')
        w_grant.writerows(self.sql_grant)
        w_examiner=csv.writer(self.f_examiner,delimiter='\t',lineterminator='\n')
        w_examiner.writerows(self.sql_examiner)
        w_agent=csv.writer(self.f_agent,delimiter='\t',lineterminator='\n')
        w_agent.writerows(self.sql_agent)
        w_assignee=csv.writer(self.f_assignee,delimiter='\t',lineterminator='\n')
        w_assignee.writerows(self.sql_assignee)
        w_inventor=csv.writer(self.f_inventor,delimiter='\t',lineterminator='\n')
        w_inventor.writerows(self.sql_inventor)
        w_pubcit=csv.writer(self.f_pubcit,delimiter='\t',lineterminator='\n')
        w_pubcit.writerows(self.sql_pubcit)
        w_gracit=csv.writer(self.f_gracit,delimiter='\t',lineterminator='\n')
        w_gracit.writerows(self.sql_gracit)
        w_forpatcit=csv.writer(self.f_forpatcit,delimiter='\t',lineterminator='\n')
        w_forpatcit.writerows(self.sql_forpatcit)
        w_nonpatcit=csv.writer(self.f_nonpatcit,delimiter='\t',lineterminator='\n')
        w_nonpatcit.writerows(self.sql_nonpatcit)
        w_usclass=csv.writer(self.f_usclass,delimiter='\t',lineterminator='\n')
        w_usclass.writerows(self.sql_usclass)
        w_intclass=csv.writer(self.f_intclass,delimiter='\t',lineterminator='\n')
        w_intclass.writerows(self.sql_intclass)
        self.f_grant.close()
        self.f_examiner.close()
        self.f_agent.close()
        self.f_assignee.close()
        self.f_inventor.close()
        self.f_pubcit.close()
        self.f_gracit.close()
        self.f_forpatcit.close()
        self.f_nonpatcit.close()
        self.f_usclass.close()
        self.f_intclass.close()
        self.__ResetSQLVariables()
        print '[Written CSV files_update. Cost:{0}]'.format(time.time()-st)
	
    def loadCSV(self):
        print '- Starting load CSV files.'
        st=time.time()
        self.processor=MySQLProcessor.MySQLProcess()
        self.processor.connect()
        #self.processor.load("""SET @@GLOBAL.local_infile = 1;""")
        print self.processor.load("""SET foreign_key_checks = 0;""")

        print '***** GRANT *****'
        print self.processor.load("""LOAD DATA LOCAL INFILE '{filePath}'
        IGNORE INTO TABLE uspto_patents.GRANTS        FIELDS TERMINATED BY '\\t'        OPTIONALLY ENCLOSED BY '\"'        LINES TERMINATED BY '\\n';
        """.format(filePath=self.csvPath_grant.replace('\\','/')))

        print '***** EXAMINER *****'
        print self.processor.load("""LOAD DATA LOCAL INFILE '{filePath}'
        IGNORE INTO TABLE uspto_patents.EXAMINER_G        FIELDS TERMINATED BY '\\t'        OPTIONALLY ENCLOSED BY '\"'        LINES TERMINATED BY '\\n';
        """.format(filePath=self.csvPath_examiner.replace('\\','/')))

        print '***** AGENT *****'
        print self.processor.load("""LOAD DATA LOCAL INFILE '{filePath}'
        IGNORE INTO TABLE uspto_patents.AGENT_G      FIELDS TERMINATED BY '\\t'        OPTIONALLY ENCLOSED BY '\"'        LINES TERMINATED BY '\\n';
        """.format(filePath=self.csvPath_agent.replace('\\','/')))

        print '***** ASSIGNEE *****'
        print self.processor.load("""LOAD DATA LOCAL INFILE '{filePath}'
        IGNORE INTO TABLE uspto_patents.ASSIGNEE_G      FIELDS TERMINATED BY '\\t'        OPTIONALLY ENCLOSED BY '\"'        LINES TERMINATED BY '\\n';
        """.format(filePath=self.csvPath_assignee.replace('\\','/')))

        print '***** INVENTOR *****'
        print self.processor.load("""LOAD DATA LOCAL INFILE '{filePath}'
        IGNORE INTO TABLE uspto_patents.INVENTOR_G      FIELDS TERMINATED BY '\\t'        OPTIONALLY ENCLOSED BY '\"'        LINES TERMINATED BY '\\n';
        """.format(filePath=self.csvPath_inventor.replace('\\','/')))

        print '***** PUBCIT *****'
        print self.processor.load("""LOAD DATA LOCAL INFILE '{filePath}'
        IGNORE INTO TABLE uspto_patents.PUBCIT_G      FIELDS TERMINATED BY '\\t'        OPTIONALLY ENCLOSED BY '\"'        LINES TERMINATED BY '\\n';
        """.format(filePath=self.csvPath_pubcit.replace('\\','/')))

        print '***** GRACIT *****'
        print self.processor.load("""LOAD DATA LOCAL INFILE '{filePath}'
        IGNORE INTO TABLE uspto_patents.GRACIT_G      FIELDS TERMINATED BY '\\t'        OPTIONALLY ENCLOSED BY '\"'        LINES TERMINATED BY '\\n';
        """.format(filePath=self.csvPath_gracit.replace('\\','/')))

        print '***** FORPATCIT *****'
        print self.processor.load("""LOAD DATA LOCAL INFILE '{filePath}'
        IGNORE INTO TABLE uspto_patents.FORPATCIT_G      FIELDS TERMINATED BY '\\t'        OPTIONALLY ENCLOSED BY '\"'        LINES TERMINATED BY '\\n';
        """.format(filePath=self.csvPath_forpatcit.replace('\\','/')))

        print '***** NONPATCIT *****'
        print self.processor.load("""LOAD DATA LOCAL INFILE '{filePath}'
        IGNORE INTO TABLE uspto_patents.NONPATCIT_G      FIELDS TERMINATED BY '\\t'        OPTIONALLY ENCLOSED BY '\"'        LINES TERMINATED BY '\\n';
        """.format(filePath=self.csvPath_nonpatcit.replace('\\','/')))

        print '***** USCLASS *****'
        print self.processor.load("""LOAD DATA LOCAL INFILE '{filePath}'
        IGNORE INTO TABLE uspto_patents.USCLASS_G      FIELDS TERMINATED BY '\\t'        OPTIONALLY ENCLOSED BY '\"'        LINES TERMINATED BY '\\n';
        """.format(filePath=self.csvPath_usclass.replace('\\','/')))

        print '***** INTCLASS *****'
        print self.processor.load("""LOAD DATA LOCAL INFILE '{filePath}'
        IGNORE INTO TABLE uspto_patents.INTCLASS_G      FIELDS TERMINATED BY '\\t'        OPTIONALLY ENCLOSED BY '\"'        LINES TERMINATED BY '\\n';
        """.format(filePath=self.csvPath_intclass.replace('\\','/')))

        print self.processor.load("""SET foreign_key_checks = 1;""")
        self.processor.close()
        print '[Loaded CSV files. Time:{0}'.format(time.time()-st)

    #loda csv files _update    
    def loadCSV_update(self,suffix):
        print '- Starting load CSV files_update.'
        st=time.time()
        self.processor=MySQLProcessor.MySQLProcess()
        self.processor.connect()

        print self.processor.load("""SET foreign_key_checks = 0;""")

        print '***** GRANT *****'
        print self.processor.load("""LOAD DATA LOCAL INFILE '{filePath}'
        IGNORE INTO TABLE uspto_patents.GRANTS        FIELDS TERMINATED BY '\\t'        OPTIONALLY ENCLOSED BY '\"'        LINES TERMINATED BY '\\n';
        """.format(filePath=self.csvPath_grant.replace('\\','/')+suffix))

        print '***** EXAMINER *****'
        print self.processor.load("""LOAD DATA LOCAL INFILE '{filePath}'
        IGNORE INTO TABLE uspto_patents.EXAMINER_G        FIELDS TERMINATED BY '\\t'        OPTIONALLY ENCLOSED BY '\"'        LINES TERMINATED BY '\\n';
        """.format(filePath=self.csvPath_examiner.replace('\\','/')+suffix))

        print '***** AGENT *****'
        print self.processor.load("""LOAD DATA LOCAL INFILE '{filePath}'
        IGNORE INTO TABLE uspto_patents.AGENT_G      FIELDS TERMINATED BY '\\t'        OPTIONALLY ENCLOSED BY '\"'        LINES TERMINATED BY '\\n';
        """.format(filePath=self.csvPath_agent.replace('\\','/')+suffix))

        print '***** ASSIGNEE *****'
        print self.processor.load("""LOAD DATA LOCAL INFILE '{filePath}'
        IGNORE INTO TABLE uspto_patents.ASSIGNEE_G      FIELDS TERMINATED BY '\\t'        OPTIONALLY ENCLOSED BY '\"'        LINES TERMINATED BY '\\n';
        """.format(filePath=self.csvPath_assignee.replace('\\','/')+suffix))

        print '***** INVENTOR *****'
        print self.processor.load("""LOAD DATA LOCAL INFILE '{filePath}'
        IGNORE INTO TABLE uspto_patents.INVENTOR_G      FIELDS TERMINATED BY '\\t'        OPTIONALLY ENCLOSED BY '\"'        LINES TERMINATED BY '\\n';
        """.format(filePath=self.csvPath_inventor.replace('\\','/')+suffix))

        print '***** PUBCIT *****'
        print self.processor.load("""LOAD DATA LOCAL INFILE '{filePath}'
        IGNORE INTO TABLE uspto_patents.PUBCIT_G      FIELDS TERMINATED BY '\\t'        OPTIONALLY ENCLOSED BY '\"'        LINES TERMINATED BY '\\n';
        """.format(filePath=self.csvPath_pubcit.replace('\\','/')+suffix))

        print '***** GRACIT *****'
        print self.processor.load("""LOAD DATA LOCAL INFILE '{filePath}'
        IGNORE INTO TABLE uspto_patents.GRACIT_G      FIELDS TERMINATED BY '\\t'        OPTIONALLY ENCLOSED BY '\"'        LINES TERMINATED BY '\\n';
        """.format(filePath=self.csvPath_gracit.replace('\\','/')+suffix))

        print '***** FORPATCIT *****'
        print self.processor.load("""LOAD DATA LOCAL INFILE '{filePath}'
        IGNORE INTO TABLE uspto_patents.FORPATCIT_G      FIELDS TERMINATED BY '\\t'        OPTIONALLY ENCLOSED BY '\"'        LINES TERMINATED BY '\\n';
        """.format(filePath=self.csvPath_forpatcit.replace('\\','/')+suffix))

        print '***** NONPATCIT *****'
        print self.processor.load("""LOAD DATA LOCAL INFILE '{filePath}'
        IGNORE INTO TABLE uspto_patents.NONPATCIT_G      FIELDS TERMINATED BY '\\t'        OPTIONALLY ENCLOSED BY '\"'        LINES TERMINATED BY '\\n';
        """.format(filePath=self.csvPath_nonpatcit.replace('\\','/')+suffix))

        print '***** USCLASS *****'
        print self.processor.load("""LOAD DATA LOCAL INFILE '{filePath}'
        IGNORE INTO TABLE uspto_patents.USCLASS_G      FIELDS TERMINATED BY '\\t'        OPTIONALLY ENCLOSED BY '\"'        LINES TERMINATED BY '\\n';
        """.format(filePath=self.csvPath_usclass.replace('\\','/')+suffix))

        print '***** INTCLASS *****'
        print self.processor.load("""LOAD DATA LOCAL INFILE '{filePath}'
        IGNORE INTO TABLE uspto_patents.INTCLASS_G      FIELDS TERMINATED BY '\\t'        OPTIONALLY ENCLOSED BY '\"'        LINES TERMINATED BY '\\n';
        """.format(filePath=self.csvPath_intclass.replace('\\','/')+suffix))

        print self.processor.load("""SET foreign_key_checks = 1;""")
        self.processor.close()
        print '[Loaded CSV files_update. Time:{0}'.format(time.time()-st)

def partTen(bList):
    n=10
    m=len(bList)
    sList=[bList[0:m/n],bList[m/n:2*m/n],bList[2*m/n:3*m/n],bList[3*m/n:4*m/n],bList[4*m/n:5*m/n],bList[5*m/n:6*m/n],bList[6*m/n:7*m/n],bList[7*m/n:8*m/n],bList[8*m/n:9*m/n],bList[9*m/n:10*m/n]]
    return sList

def newfuncXML4(filePath):
    try:
        log=LogProcessor.LogProcess()
        fileName = os.path.basename(filePath)
        sp=SourceParser.SourceParser()
        xmlStr=sp.getXML4Content_DPL(filePath)
        g=GrantsParser()
        g.extractXML4(xmlStr)
        g.writeCSV()
        log.write(log.logPath_G,fileName+ ', Processed')
    except Exception, e:
        print e
        log.write(log.logPath_G,fileName + ', Failed')

def newfuncXML2(filePath):
    try:
        log=LogProcessor.LogProcess()
        fileName = os.path.basename(filePath)
        sp=SourceParser.SourceParser()
        xmlStr=sp.getXML2Content_DPL(filePath)
        g=GrantsParser()
        g.extractXML2(xmlStr)
        g.writeCSV()
        log.write(log.logPath_G,fileName+ ', Processed')
    except Exception, e:
        print e
        log.write(log.logPath_G,fileName + ', Failed')

def xml4file(filelist):
    for file in filelist:  
       newfuncXML4(file)

def xml2file(filelist):
    for file in filelist:
        #print file
        newfuncXML2(file)


if __name__=="__main__":
    g=GrantsParser()

    #download
    st=time.time()
    g.downloadZIP()
    print '== Downloading Cost: {0} =='.format(time.time()-st)
    
    #parse
    st=time.time()
    sp=SourceParser.SourceParser()
    sp.getALLFilePaths()
    ls_xml4=sp.files_G_XML4  #396
    ls_xml2=sp.files_G_XML2 #157
    ls_xml24=sp.files_G_XML24 #52
    ls_aps=sp.files_G_APS #252
    xml4file(ls_xml4)
    xml2file(ls_xml2)    
    print '== Parsing Cost:{0} =='.format(time.time()-st)

    #load
    st=time.time()
    g.loadCSV()
    print '== Loading Cost:{0} =='.format(time.time()-st)
