#!/usr/bin/python3
'''input: webtemplate in json format
output: depends on type of output
type_of_output     output
all                list of lists, one list for leaf. It contains id,name,path,flatpath,rmtype,inputs
flatpath           only the mapping webtemplate flatpath-> webtemplate path
composition        an example composition with all the fields filled with fake or default values
           '''
import json
import argparse
import random
import base64
from terminology import openterm
from datetime import datetime 

RMtypes=["CODE_PHRASE","DV_BOOLEAN","DV_CODED_TEXT","DV_COUNT","DV_DATE",
         "DV_DATE_TIME","DV_DURATION","DV_EHR_URI","DV_IDENTIFIER","DV_MULTIMEDIA",
         "DV_ORDINAL","DV_PARSABLE","DV_PROPORTION","DV_QUANTITY","DV_STATE","DV_TEXT",
         "DV_TIME","DV_URI","FEEDER_AUDIT","PARTICIPATION","PARTY_IDENTIFIED",
         "PARTY_PROXY","UID_BASED_ID","ARCHETYPED","OBJECT_REF","STRING","LINK",
         "ISM_TRANSITION"]


class RMError(Exception):
    def __init__(self,message="RM type not yet implemented"):
        self.message=message
        super().__init__(self.message) 

class RMIMPError(Exception):
    def __init__(self,message="RM type implementation has raised an error"):
        self.message=message
        super().__init__(self.message) 


def findallelementsinwt(wc,el,nodes):
    rm=el['rmType']
    if rm in RMtypes or rm.startswith("DV_INTERVAL<"):
        path=el['aqlPath']
        id=el['id']
        name=el['name']
        # if 'nodeId' in el:
        #     nodeid=el['nodeId']
        # else:
        #     nodeid=""
        if el['max']==-1:
            nodes.append(id+'[0]')
        else:
            nodes.append(id)   
        if 'inputs' in el:
            inputs=el['inputs']
        else:
            inputs=[]
        if 'children' in el:
               children=el['children']
        else:
               children=[]
        wc.append([id,name,path,"/".join(nodes),rm,inputs,children])
        return True
    elif rm in ['ITEM_TREE',"HISTORY"]:#path is not influenced by these
        if 'children' in el:
            for c in el['children']:
                added=findallelementsinwt(wc,c,nodes)
                if added:
                    nodes.pop()
            return False
        else:
            return False
    else:
        id=el['id']
        if 'name' in el:
                name=el['name']
        elif rm=='EVENT_CONTEXT':
                name='context'
        # if 'nodeId' in el:
        #     nodeid=el['nodeId']
        # else:
        #     nodeid=""
        path=el['aqlPath']
        if el['max']==-1:
            nodes.append(id+'[0]')
        else:
            nodes.append(id)
        if 'children' in el:
            for c in el['children']:
                added=findallelementsinwt(wc,c,nodes)
                if added:
                    nodes.pop()
            return True
        else:
            return True
        
def webtempconverter(webtemp):
        if 'webTemplate' in webtemp:
                wt=webtemp['webTemplate']['tree']['children']
                templatename=webtemp['webTemplate']['templateId']
        else:
                wt=webtemp['tree']['children']
                templatename=webtemp['templateId']
        mapping=[]
        for el in wt:
                wc=[]
                nodes=[]
                findallelementsinwt(wc,el,nodes)
                mapping.extend(wc)
        return mapping,templatename

skip_ids=['null_flavour','feeder_audit','uid',\
             'archetype_node_id','archetype_details','archetype_id',\
                'links','location' ]

def ismtransitionhandler(fpath,inputs,children):
        current={}
        #current_state codes from instruction_states
        ncs=len(openterm['instruction_states'])
        csc=random.randint(0,ncs-1)
        csvalue=openterm['instruction_states'][csc]['rubric']
        cscode=openterm['instruction_states'][csc]['id']
        csterm='openehr'
        current[fpath+'/current_state|code']=cscode
        current[fpath+'/current_state|value']=csvalue
        current[fpath+'/current_state|terminology']=csterm   
        #transition codes from instruction_transitions
        nt=len(openterm['instruction_transitions'])
        tc=random.randint(0,nt-1)
        tvalue=openterm['instruction_transitions'][tc]['rubric']
        tcode=openterm['instruction_transitions'][tc]['id']
        tterm='openehr'
        current[fpath+'/transition|code']=tcode
        current[fpath+'/transition|value']=tvalue
        current[fpath+'/transition|terminology']=tterm      
        #careflow_step code defined in template
        cacode='at0006'
        cavalue='transition'
        caterm='local'
        current[fpath+'/careflow_step|code']=cacode
        current[fpath+'/careflow_step|value']=cavalue
        current[fpath+'/careflow_step|terminology']=caterm  
        current[fpath+'/_reason:0']= "reason 1"
        listofchildren=[a['id'] for a in children]    
        if 'current_state' in listofchildren:
                cindex=listofchildren.index('current_state')
                cstate=children[cindex]
                if 'inputs' in cstate:
                        if 'list' in cstate['inputs'][0]:
                                inputs=cstate['inputs']  
                                llist=len(inputs[0]['list'])
                                num = random.randint(0, llist-1)
                                ccode=inputs[0]['list'][num]['value']
                                cvalue=inputs[0]['list'][num]['label']
                                listofallowedvalues=[a['rubric'] for a in openterm['instruction_states']]
                                listofallowedcodes=[a['id'] for a in openterm['instruction_states']]
                                if cvalue in listofallowedvalues and ccode in listofallowedcodes and listofallowedvalues.index(cvalue)==listofallowedcodes.index(ccode):
                                        current[fpath+'/current_state|code']=ccode
                                        current[fpath+'/current_state|value']=cvalue
                                        current[fpath+'/current_state|terminology']='openehr'                     
        if 'transition' in listofchildren:
                cindex=listofchildren.index('transition')
                ctran=children[cindex]                
                if 'inputs' in ctran:
                        if 'list' in ctran['inputs'][0]:
                                inputs=ctran['inputs']   
                                llist=len(inputs[0]['list'])
                                num = random.randint(0, llist-1)
                                ccode=inputs[0]['list'][num]['value']
                                cvalue=inputs[0]['list'][num]['label']
                                listofallowedvalues=[a['rubric'] for a in openterm['instruction_transitions']]
                                listofallowedcodes=[a['id'] for a in openterm['instruction_transitions']]
                                if cvalue in listofallowedvalues and ccode in listofallowedcodes and listofallowedvalues.index(cvalue)==listofallowedcodes.index(ccode):
                                        current[fpath+'/transition|code']=ccode
                                        current[fpath+'/transition|value']=cvalue
                                        current[fpath+'/transition|terminology']='openehr' 
        if 'careflow_step' in listofchildren:
                cindex=listofchildren.index('careflow_step')
                ccare=children[cindex]
                if 'inputs' in ccare:
                        if 'list' in ccare['inputs'][0]:
                                inputs=ccare['inputs']
                                ccode=inputs[0]['list'][0]['value']
                                cvalue=inputs[0]['list'][0]['label']
                                tvalue=inputs[0]['terminology']
                                current[fpath+'/careflow_step|code']=ccode
                                current[fpath+'/careflow_step|value']=cvalue
                                current[fpath+'/careflow_step|terminology']=tvalue 
        #Apparently only this transition is accepted at the time of coding this
        current[fpath+'/transition|code']="548"
        current[fpath+'/transition|value']='finish'
        current[fpath+'/transition|terminology']='openehr' 

        return current



def dvtexthandler(fpath,inputs):
        fp=fpath
        if fpath.endswith(':0'):
                endstring=":0"
                fp=fpath.rsplit(':0',1)[0]
        else:
                endstring=""
        current={}

               
        if len(inputs)==0:
                current[fp+endstring]='some text'
        else:
                # print(f'inputsssssssss={inputs}')
                if 'list' in inputs[0]:
                        llist=len(inputs[0]['list'])
                        num = random.randint(0, llist-1)
                        # print(f'num={num} llist-1={llist-1}')
                        current[fp+endstring]=inputs[0]['list'][num]['value']
                elif 'defaultValue' in inputs[0]:
                        current[fp+endstring]=inputs[0]['defaultValue']
                else:
                        current[fp+endstring]='some text'
        return current

def dvcodedtexthandler(fpath,inputs):
        current={}
        fp=fpath
        if fpath=='context/setting':
                nsetting=len(openterm['setting'])
                sc=random.randint(0,nsetting-1)
                svalue=openterm['setting'][sc]['rubric']
                scode=openterm['setting'][sc]['id']
                current[fpath+'|code']='238'
                current[fpath+'|value']='other care'
                current[fpath+'|terminology']='openehr'
                return current    
        elif fpath.endswith('/math_function'):
                nmath=len(openterm['event_math_function'])
                mc=random.randint(0,nmath-1)
                mvalue=openterm['event_math_function'][mc]['rubric']
                mcode=openterm['event_math_function'][mc]['id']
                current[fpath+'|code']=mcode
                current[fpath+'|value']=mvalue
                current[fpath+'|terminology']='openehr'
                return current                         
        # if fpath.endswith('[0]'):
        #         endstring="[0]"
        #         fp=fpath.rsplit('[0]',1)[0]
        # else:
        #         endstring=""

        if len(inputs)==0:
                current[fp+'|value']='some value'
                current[fp+'|code']='some code'
                current[fp+'|terminology']='local'
        else:   
                # print(f'fpath={fpath} inputs={inputs}')
                if 'list' in inputs[0]:
                        llist=len(inputs[0]['list'])
                        # print(llist)
                        num = random.randint(0, llist-1)
                        # print(num)
                        # print(f"aa={inputs[0]['list'][num]['value']}")
                        current[fp+'|code']=inputs[0]['list'][num]['value']
                        current[fp+'|value']=inputs[0]['list'][num]['label']
                        if 'terminology' in inputs[0]:
                                current[fp+'|terminology']=inputs[0]['terminology']
                        else:
                               current[fp+'|terminology']='openehr'
                elif 'defaultValue' in inputs[0]:
                        current[fp+'|code']=inputs[0]['defaultValue']
                        current[fp+'|value']='some text'
                        if 'terminology' in inputs[0]:
                                current[fp+'|terminology']=inputs[0]['terminology']
                        else:
                               current[fp+'|terminology']='openehr'
                else:
                        current[fp+'|value']='some value'
                        current[fp+'|code']='some code'
                        current[fp+'|terminology']='local'
        return current

def dvbooleanhandler(fpath,inputs):
        current={}
        if len(inputs)==0:
                current[fpath]=True
        else:
                if 'list' in inputs[0]:
                        llist=len(inputs[0]['list'][0])
                        num = random.randint(0, llist-1)
                        current[fpath]=inputs[0]['list'][num]['value']
                elif 'defaultValue' in inputs[0]:
                        current[fpath]=inputs[0]['defaultValue']
                else:
                        current[fpath]=True
        return current

def dvdatehandler(fpath,inputs):
        current={}
        year=random.randint(1950,2025)
        month=random.randint(1,12)
        fmonth=f"{month:02d}"
        if month in [4,6,9,11]:
               day=random.randint(1,30)
        elif month==2:
               day=random.randint(1,28)
        else:
               day=random.randint(1,31)
        fday=f"{day:02d}" 
        fdate=str(year)+"-"+fmonth+"-"+fday
        if len(inputs)==0:
                current[fpath]=fdate
        else:
                if 'list' in inputs[0]:
                        llist=len(inputs[0]['list'][0])
                        num = random.randint(0, llist-1)
                        current[fpath]=inputs[0]['list'][num]['value']
                elif 'defaultValue' in inputs[0]:
                        current[fpath]=inputs[0]['defaultValue']
                else:
                        current[fpath]=fdate
        return current       

def dvdatetimehandler(fpath,inputs):
        current={}
        if fpath=='context/end_time':
               fpath='context/_end_time'
        year=random.randint(1950,2025)
        month=random.randint(1,12)
        fmonth=f"{month:02d}"
        if month in [4,6,9,11]:
               day=random.randint(1,30)
        elif month==2:
               day=random.randint(1,28)
        else:
               day=random.randint(1,31)
        fday=f"{day:02d}" 
        hour=random.randint(0,23)
        fhour=f"{hour:02d}" 
        minute=random.randint(0,59)
        fminute=f"{minute:02d}" 
        second=random.randint(0,59)
        fsecond=f"{second:02d}" 
        fdatetime=str(year)+"-"+fmonth+"-"+fday+"T"+fhour+":"+fminute+":"+fsecond+".00"
        if len(inputs)==0:
                current[fpath]=fdatetime
        else:
                if 'list' in inputs[0]:
                        llist=len(inputs[0]['list'][0])
                        num = random.randint(0, llist-1)
                        current[fpath]=inputs[0]['list'][num]['value']
                elif 'defaultValue' in inputs[0]:
                        current[fpath]=inputs[0]['defaultValue']
                else:
                        current[fpath]=fdatetime
        return current    
 
class ValidationError(Exception):
    def __init__(self,message="Error in evaluating Validation range"):
        self.message=message
        super().__init__(self.message) 


def valuefromvalidation(validation):
       if 'range' in validation:
                range=validation['range']
                if 'min' in range:
                        if range['minOp']==">=":
                                return range['min']
                        elif range['minOp']=='==':
                                return range['min']
                        else:
                                return range(['min']+1)                
       else:
              raise ValidationError(f'validation={validation}')

def dvdurationhandler(fpath,inputs):
        current={}
        years=random.randint(0,80)
        y=f"{years:02d}"+'Y'
        months=random.randint(0,11)
        mo=f"{months:02d}"+'M'
        weeks=random.randint(0,51)
        w=f"{weeks:02d}"+'W'
        days=random.randint(0,31)
        d=f"{days:02d}"+'D'
        hours=random.randint(0,23)
        h=f"{hours:02d}"+'H'
        minutes=random.randint(0,59)
        mi=f"{minutes:02d}"+'M'
        seconds=random.randint(0,59)
        s=f"{seconds:02d}"+'S'
        total='P'+y+mo+w+d+'T'+h+mi+s
        if len(inputs)==0:
                current[fpath]=total
        else:
                llist=len(inputs)
                num = random.randint(0, llist-1)
                if 'validation' in inputs[num]:
                       value=valuefromvalidation(inputs[0]['validation'])
                if inputs[num]["suffix"]=="year":
                        current[fpath]='P'+y
                elif inputs[num]["suffix"]=="month":
                        current[fpath]='P'+mo
                elif inputs[num]["suffix"]=="day":      
                        current[fpath]='P'+d
                elif inputs[num]["suffix"]=="week":
                        current[fpath]='P'+w
                elif inputs[num]["suffix"]=="hour":  
                        current[fpath]='PT'+h
                elif inputs[num]["suffix"]=="minute":
                        current[fpath]='PT'+mi
                elif inputs[num]["suffix"]=="seconds":    
                        current[fpath]='PT'+s
                elif 'defaultValue' in inputs[0]:
                        current[fpath]=inputs[0]['defaultValue']
                else:
                        current[fpath]=total
        return current    


def dvurihandler(fpath,inputs):
        current={}
        if len(inputs)==0:
                current[fpath]='https://www.example.com/example'
        else:
                if 'list' in inputs[0]:
                        llist=len(inputs[0]['list'][0])
                        num = random.randint(0, llist-1)
                        current[fpath]=inputs[0]['list'][num]['value']
                elif 'defaultValue' in inputs[0]:
                        current[fpath]=inputs[0]['defaultValue']
                else:
                        current[fpath]='https://www.example.com/example'
        return current    

def dvcounthandler(fpath,inputs):
       current={}
       current[fpath]=random.randint(1,100)
       return current

def dvehrurihandler(fpath,inputs):
        current={}
        if len(inputs)==0:
                current[fpath]='ehr://0a924490-5e72-49e3-847a-4347af2fa456'
        else:
                if 'list' in inputs[0]:
                        llist=len(inputs[0]['list'][0])
                        num = random.randint(0, llist-1)
                        current[fpath]=inputs[0]['list'][num]['value']
                elif 'defaultValue' in inputs[0]:
                        current[fpath]=inputs[0]['defaultValue']
                else:
                        current[fpath]='ehr://0a924490-5e72-49e3-847a-4347af2fa456'
        return current                         

def dvintervalhandler(fpath,inputs,rmtype2):
        current={}
        current[fpath+'|lower_included']=True
        current[fpath+'|upper_included']=True
        subfunction=function_caller(rmtype2)
        loweruppercomparison=0
        #current[fpath+"/lower"]
        a=subfunction(**{'fpath':fpath,'inputs':inputs})
        while loweruppercomparison==0:     
                #current[fpath+"/upper"]
                b=subfunction(**{'fpath':fpath,'inputs':inputs})
                loweruppercomparison=rmcompare(a,b,rmtype2)
                if loweruppercomparison<0:#lower<upper
                        for aa in a:
                               current[fpath+"/lower"+aa.split(fpath)[1]]=a[aa]
                        for bb in b:
                               current[fpath+"/upper"+bb.split(fpath)[1]]=b[bb]
                        return current
                elif loweruppercomparison>0:#lower>upper
                        aa=a
                        a=b
                        b=aa
                        for aa in a:
                               current[fpath+"/lower"+aa.split(fpath)[1]]=a[aa]
                        for bb in b:
                               current[fpath+"/upper"+bb.split(fpath)[1]]=b[bb]                        
                        return current

def rmcompare(a,b,rmtype):
        if rmtype=='DV_COUNT':
                avalue=a[next(iter(a))]
                bvalue=b[next(iter(b))]
                if avalue<bvalue:
                     return -1
                elif avalue>bvalue:
                     return 1
                else:
                     return 0
        elif rmtype=='DV_QUANTITY':
                akey=next((key for key in a if key.endswith('magnitude')), None)
                if akey==None:
                       raise RMIMPError('DV_QUANTITY')
                avalue=a[akey]
                bkey=next((key for key in b if key.endswith('magnitude')), None)
                if bkey==None:
                       raise RMIMPError('DV_QUANTITY')
                bvalue=b[bkey]                
                if avalue<bvalue:
                     return -1
                elif avalue>bvalue:
                     return 1
                else:
                     return 0                              
        elif rmtype=='DV_DATE':
                adate=next(iter(a.values()))
                bdate=next(iter(b.values()))
                avalue = datetime.strptime(adate, "%Y-%m-%d")
                bvalue = datetime.strptime(bdate, "%Y-%m-%d")              
                if avalue<bvalue:
                     return -1
                elif avalue>bvalue:
                     return 1
                else:
                     return 0                
        elif rmtype=='DV_DATE_TIME':
                adate=next(iter(a.values()))
                bdate=next(iter(b.values()))
                avalue = datetime.strptime(adate, "%Y-%m-%dT%H:%M:%S.%f")
                bvalue = datetime.strptime(bdate, "%Y-%m-%dT%H:%M:%S.%f")           
                if avalue<bvalue:
                     return -1
                elif avalue>bvalue:
                     return 1
                else:
                     return 0   
        elif rmtype=='DV_TIME':
                adate=next(iter(a.values()))
                bdate=next(iter(b.values()))
                avalue = datetime.strptime(adate, "%H:%M:%S")
                bvalue = datetime.strptime(bdate, "%H:%M:%S")             
                if avalue<bvalue:
                     return -1
                elif avalue>bvalue:
                     return 1
                else:
                     return 0
        elif rmtype=='DV_DURATION':
                adur=next(iter(a.values()))
                bdur=next(iter(b.values()))
                avalue=parseduration(adur)
                bvalue=parseduration(bdur)
                if avalue<bvalue:
                     return -1
                elif avalue>bvalue:
                     return 1
                else:
                     return 0               
        else:
               raise RMError(rmtype)                                

def parseduration(duration):
        #P12Y10M08W01DT02W01D00H01M03S
        total=0
        duration=duration.split('P')[1]
        if 'Y' in duration:
                years=duration.split('Y')[0]
                total=total+int(years)*31536000
                duration=duration.split('Y')[1]
        if 'M' in duration and duration.find('M',1)<duration.find('T'):
                months=duration.split('M',1)[0]
                total=total+int(months)*2628000
                duration=duration.split('M',1)[1]
        if 'W' in duration:
                weeks=duration.split('W')[0]
                total=total+int(weeks)*606461
                duration=duration.split('W')[1]
        if 'D' in duration:
                days=duration.split('D')[0]
                total=total+int(days)*86400
                duration=duration.split('D')[1]
        if 'T' in duration:
                duration=duration.split('T')[1]
                if 'H' in duration:
                        hours=duration.split('H')[0]
                        total=total+int(hours)*3600
                        duration=duration.split('H')[1]
                if 'M' in duration:
                        minutes=duration.split('M')[0]
                        total=total+int(minutes)*60
                        duration=duration.split('M')[1]
                if 'S' in duration:
                        seconds=duration.split('S')[0]
                        total=total+int(seconds)
                return total
        else:
               return total


def dvidentifierhandler(fpath,inputs):
        current={}
        id=random.randint(1,100)
        current[fpath+'|id']='id'+str(id)
        current[fpath+'|issuer']='Mr Black'
        current[fpath+'|assigner']='Mr Right'
        current[fpath+'|type']='some type'
        # if len(inputs)==0:
        #         id=random.randint(1,100)
        #         current[fpath+'|id']='id'+str(id)
        #         current[fpath+'|issuer']='Mr Black'
        #         current[fpath+'|assigner']='Mr Right'
        #         current[fpath+'|type']='some type'
        # else:
                # if 'list' in inputs[0]:
                #         llist=len(inputs[0]['list'][0])
                #         num = random.randint(0, llist-1)
                #         current[fpath'|id']=inputs[0]['list'][num]['id']
                #         current[fpath+'|issuer']=inputs[0]['list'][num]['issuer']
                #         current[fpath+'|assigner']=inputs[0]['list'][num]['assigner']
                #         current[fpath+'|type']=inputs[0]['list'][num]['type']
                # elif 'defaultValue' in inputs[0]:
                #         current[fpath]=inputs[0]['defaultValue']
                # else:
                #         current[fpath+'|id']='id'+str(id)
                #         current[fpath+'|issuer']='Mr Black'
                #         current[fpath+'|assigner']='Mr Right'
                #         current[fpath+'|type']='some type'
        return current             

def dvmultimediahandler(fpath,inputs):
        current={}
        mediachoices=["image/cgm","image/gif","image/png","image/tiff","image/jpeg",
                      "video/BT656","video/CelB","video/JPEG","video/H261",
                      "video/H263","video/H263-1998","video/H263-2000","video/MPV",
                      "video/quicktime","audio/DVI4","audio/G722","audio/G723",
                      "audio/G726-16","audio/G726-24","audio/G726-32","audio/G726-40",
                      "audio/G728","audio/L8","audio/L16","audio/LPC","audio/G729",
                      "audio/G729D","audio/G729E","audio/mpeg","audio/mpeg4-generic",
                      "audio/L20","audio/L24"]
        mediatype=random.choice(mediachoices)
        current[fpath+'|mediatype']=mediatype
        current[fpath+'|size']=500
        datamessage="123456"
        databytes=datamessage.encode('ascii')
        databytes64=base64.b64encode(databytes)
        datamessagebase64= databytes64.decode('ascii')
        current[fpath+'|data']=datamessagebase64
        # if len(inputs)==0:
        #         mediatype=random.choice(mediachoices)
        #         current[fpath+'|mediatype']=mediatype
        #         current[fpath+'|size']=500
        #         current[fpath+'|data']="123456"
        # else:
        #         if 'list' in inputs[0]:
        #                 llist=len(inputs[0]['list'][0])
        #                 num = random.randint(0, llist-1)
        #                 current[fpath'|id']=inputs[0]['list'][num]['id']
        #                 current[fpath+'|issuer']=inputs[0]['list'][num]['issuer']
        #                 current[fpath+'|assigner']=inputs[0]['list'][num]['assigner']
        #                 current[fpath+'|type']=inputs[0]['list'][num]['type']
        #         # elif 'defaultValue' in inputs[0]:
        #         #         current[fpath]=inputs[0]['defaultValue']
        #         else:
        #                 mediatype=random.choice(mediachoices)
        #                 current[fpath+'|mediatype']=mediatype
        #                 current[fpath+'|size']=500
        #                 current[fpath+'|data']="123456"
        return current             

def dvordinalhandler(fpath,inputs):
        current={}
        current[fpath+'|value']="ordinal value"
        current[fpath+'|code']='ordinal code'
        current[fpath+'|ordinal']=random.randint(1,10)
        return current

def dvparsablehandler(fpath,inputs):
        current={}
        current[fpath+'|value']="parsable value"
        current[fpath+'|formalism']='some formalism'
        return current

def dvproportionhandler(fpath,inputs):
        current={}
        current[fpath+'|numerator']="21.53"
        current[fpath+'|denominator']='100'
        current[fpath+'|type']='0'
        current[fpath+'|precision']=3
        return current

def dvquantityhandler(fpath,inputs):
        current={}
        quantity=random.randint(1,100)
        current[fpath+'|magnitude']=quantity
        current[fpath+'|unit']='l/min'
        return current                        

def dvtimehandler(fpath,inputs):
        current={}
        hours=random.randint(1,23)
        if hours<10:
                hours="0"+str(hours)
        else:
                hours=str(hours)
        minutes=random.randint(0,59)
        if minutes<10:
                minutes="0"+str(minutes)
        else:
                minutes=str(minutes)               
        seconds=random.randint(0,59)
        if seconds<10:
                seconds="0"+str(seconds)
        else:
                seconds=str(seconds)          
        current[fpath]=hours+":"+minutes+":"+seconds
        return current                   

def partyrefhandler(fpath,inputs):
        current={}
        idnumber=random.randint(1,10000)
        current[fpath+'_type']="PARTY_REF"
        current[fpath+'|id']=idnumber+'::ehr-system::1'      
        current[fpath+'|namespace']="myehr"
        current[fpath+'|type']="PARTY"

def partyproxyhandler(id,fpath,inputs):
        #can be party identified, party self, party related
        fp=fpath
        if id=='provider':
                fp=fp.replace(id,'_provider')       
        choice=random.randint(1,3)
        if choice==1:
               return partyidentifiedhandler(id,fp,inputs)
        elif choice==2:
               return partyselfhandler(id,fp,inputs)
        else:
               return partyrelatedhandler(id,fp,inputs)
        # current={}
        # idnumber=random.randint(1,10000)
        # current[fpath+'|id']='id'+str(idnumber)
        # current[fpath+'|id_scheme']='idscheme'
        # current[fpath+'|namespace']='mycompany'
        # current[fpath+'|name']='name'
        # return current

def partyidentifiedhandler(id,fpath,inputs):
        fp=fpath
        if id=='health_care_facility':
               fp=fp.replace(id,'_health_care_facility')
        current={}
        idnumber=random.randint(1,10000)
#        current[fp+'|_type']='PARTY_IDENTIFIED'
        current[fp+'|name']='name'
        #identifiers
        current[fp+'|id']='id'+str(idnumber)
        current[fp+'|id_scheme']='id_scheme'
        current[fp+'|id_namespace']='ACME'
        return current       

def partyselfhandler(id,fpath,inputs):
        fp=fpath
        current={}
        current[fp+'|_type']='PARTY_SELF'
        return current    

def partyrelatedhandler(id,fpath,inputs):
        '''relationship source https://specifications.openehr.org/releases/1.0.1/architecture/terminology.pdf'''
        fp=fpath
        current={}
        current[fp+'|_type']='PARTY_RELATED'
        current[fp+'|name']='John Doe'
        numavailablerelationship=len(openterm['subject_relationship'])
        cr=random.randint(0,numavailablerelationship-1)
        cr_value=openterm['subject_relationship'][cr]['rubric']
        cr_code=openterm['subject_relationship'][cr]['id']
        current[fp+'/relationship|value']=cr_value
        current[fp+'/relationship|code']=cr_code
        current[fp+'/relationship|terminology']='openehr'
        return current  

def participationhandler(fpath,inputs):
        current={}
        if len(fpath.split('/'))==2 and fpath.startswith('context/'):
                fpath='context/_participation:0'
        else:
                return current
        idnumber=random.randint(1,10000)
        current[fpath+'|id']=str(idnumber)
        function=random.choice(["requester","performer"])
        nmodes=len(openterm['participation_mode'])
        cm=random.randint(0,nmodes-1)
        cmode=openterm['participation_mode'][cm]['rubric']
        current[fpath+'|function']=function
        current[fpath+'|mode']=cmode
        current[fpath+'|name']='Dr Black'
        return current 

def objectrefhandler(id,fpath,inputs):
        fp=fpath
        if fpath.endswith('[0]'):
                endstring="[0]"
                fp=fpath.rsplit('[0]',1)[0]
        else:
                endstring=""          
        current={}
        idnumber=random.randint(1,10000)
        if id=='workflow_id':
               newid='_work_flow_id'
               fp=fp.replace(id,newid)
        elif id=='guideline_id':
               newid='_guideline_id'
               fp=fp.replace(id,newid) 

        current[fp+'|id'+endstring]='id'+str(idnumber)
        current[fp+'|id_scheme'+endstring]='idscheme'
        current[fp+'|namespace'+endstring]='mycompany'
        current[fp+'|type'+endstring]='id type'
        return current

def codephrasehandler(id,fpath,inputs):
        current={}
        if id=='language':
              current[fpath+'|code']='en'
              current[fpath+'|terminology']='ISO_639-1'
        elif id=='encoding':
                current[fpath+'|code']='UTF-8'
                current[fpath+'|terminology']='IANA_character-sets'
        elif id=='territory':
                current[fpath+'|code']='IT'
                current[fpath+'|terminology']='ISO_3166-1'
        elif fpath=='/category' or fpath=='/category/defining_code':
                current[fpath+'|code']='433'
                current[fpath+'|terminology']='openehr'
                current[fpath+'|value']='event'
        else:
                if len(inputs)==0:
                        current[fpath+'|code']='code'
                        current[fpath+'|terminology']='local'
                else:
                        if 'list' in inputs[0]:
                                llist=len(inputs[0]['list'])
                                num = random.randint(0, llist-1)
                                current[fpath+'|code']=inputs[0]['list'][num]['value']
                                current[fpath+'|value']=inputs[0]['list'][num]['label']
                                current[fpath+'|terminology']=inputs[0]['list'][num]['label']         
                        else:
                               raise RMError(f'codephrase not understood {fpath}')
        return current

def assignmolteplicity(composition,rows,last,blast,opath,id,opath2id):
        if 'analyte_result' in opath:
                print(f'opath={opath} opath2id={opath2id}')
        if opath in opath2id:
                rows_corrected={}
                if last.endswith(':0'):
                        found=True
                        i=0
                        rzero=next(iter(rows))
                        rzerosplit=rzero.rsplit(':0',1)
                        while found:
                                if rzero not in composition:
                                        found=False   
                                else:
                                        i+=1
                                        rzero=rzerosplit[0]+":"+str(i)+rzerosplit[1]
                        for r in rows:
                                rold=r.rsplit(':0',1)
                                rnew=rold[0]+":"+str(i)+rold[1]
                                rows_corrected[rnew]=rows[r]
                elif blast.endswith(':0'):
                        # if blast=='any_event:0' or blast=='monitoring_interval:0':
                        #         return rows
                        i=0
                        rzero=next(iter(rows))
                        rzerosplit=rzero.rsplit(':0',1)
                        rzerobase=rzerosplit[0]
                        found=True
                        rzerobasetocheck=rzerobase+':0'
                        # print(f'rzerobasetocheck={rzerobasetocheck}')
                        while found:
                                found=False
                                for c in composition:
                                        if c.startswith(rzerobasetocheck):
                                                found=True
                                                i+=1
                                                rzerobasetocheck=rzerobase+':'+str(i)
                                                # print(f'rzerobasetocheck={rzerobasetocheck}')                                        
                
                        for r in rows:
                                rsplit=r.rsplit(':0',1)
                                rnew=rsplit[0]+':'+str(i)+rsplit[1]
                                rows_corrected[rnew]=rows[r]
                else:
                        rows_corrected=rows
        else:
                rows_corrected=rows
        return rows_corrected
       
def function_caller(rmtype):
        if rmtype=="DV_TEXT":
                return dvtexthandler
        elif rmtype=="DV_CODED_TEXT":
                return dvcodedtexthandler
        elif rmtype=="DV_BOOLEAN":
                return dvbooleanhandler
        elif rmtype=="DV_DATE":
                return dvdatehandler
        elif rmtype=="DV_DATE_TIME":
                return dvdatetimehandler 
        elif rmtype=="DV_DURATION":
                return dvdurationhandler
        elif rmtype=="DV_URI":
                return dvurihandler
        elif rmtype=="DV_EHR_URI":
                return dvehrurihandler
        elif rmtype=="DV_IDENTIFIER":
                return dvidentifierhandler
        elif rmtype=="DV_MULTIMEDIA":
                return dvmultimediahandler
        elif rmtype=="DV_ORDINAL":
                return dvordinalhandler
        elif rmtype=="DV_PARSABLE":
                return dvparsablehandler
        elif rmtype=="DV_PROPORTION":
                return dvproportionhandler
        elif rmtype=="DV_QUANTITY":
                return dvquantityhandler
        elif rmtype=="DV_STATE":
                print(f'DV_STATE ignored. EHRBase does not currently support it')
                return "DV_STATE"
        elif rmtype=="DV_TIME":
                return dvtimehandler
        elif rmtype=="PARTY_PROXY":
                return partyproxyhandler
        elif rmtype=="PARTY_IDENTIFIED":
                return partyidentifiedhandler
        elif rmtype=="PARTY_SELF":
                return partyselfhandler
        elif rmtype=="PARTY_RELATED":
                return partyrelatedhandler
        elif rmtype=="PARTY_REF":
                return partyrefhandler                         
        elif rmtype=="PARTICIPATION":
                return participationhandler
        elif rmtype=="OBJECT_REF":
                return objectrefhandler  
        elif rmtype=="CODE_PHRASE":
                return codephrasehandler    
        elif rmtype=="DV_COUNT":
                return dvcounthandler
        elif rmtype=='ISM_TRANSITION':
               return ismtransitionhandler                
        elif rmtype.startswith("DV_INTERVAL<"):
                return dvintervalhandler
        else:
                raise RMError(f'RM={rmtype} not implemented yet')         


def createcomposition(output):
        #output id,name,path,flatpath,rmtype,inputs,children
        composition={}
        opath2id={}
        
        for o in output:
                id=o[0]
                id=id.replace("[0]",":0")
                if id.endswith(':0'):
                       idc=id.rsplit(':0',1)[0]
                else:
                       idc=id
                if idc in skip_ids:
                       continue
                name=o[1]
                opath=o[2]
                fpath=o[3]
                fpath=fpath.replace("[0]",":0")
                inputs=o[5]
                children=o[6]
                rmtype=o[4]
                fsplit=fpath.split('/')
                last=fpath.split('/')[-1]
                if len(fsplit)>1:
                        blast=fpath.split('/')[-2]
                else:   
                       blast="NNNNNNNNNNNNNNNNNN"                
                # print(f'fpath={fpath}')
                if id=='name' and fpath.endswith('/name'):
                       continue
                elif id=='value' and fpath.endswith('/value'):
                        fpath=fpath.rsplit('/value',1)[0]

                function=function_caller(rmtype)
                parameters={}
                parameters['fpath']=fpath
                parameters['inputs']=inputs
                if rmtype in ['PARTY_PROXY','PARTY_IDENTIFIED','PARTY_SELF','PARTY_RELATED','OBJECT_REF','CODE_PHRASE']:
                        parameters['id']=id
                if rmtype=='ISM_TRANSITION':
                        parameters['children']=children
                if rmtype.startswith("DV_INTERVAL<"):
                        parameters['rmtype2']=rmtype.split("<")[1].split('>')[0]
                rows=function(**parameters)
                if not rows:
                       continue
                rows_corrected=assignmolteplicity(composition,rows,last,blast,opath,id,opath2id)
                composition.update(rows_corrected)
                if opath in opath2id:
                        # print('-------------------')
                        # print(f'1opath={opath} id={id}')
                        # print(f'1opath2id={opath2id}')
                        oop=opath2id[opath]
                        oop.extend(id)
                        opath2id[opath]=oop
                        # print(f'1after opath2id[opath]={opath2id[opath]}')
                else:
                        # print('=========================')
                        # print(f'2opath={opath} id={id}')
                        opath2id[opath]=[id]
                
        #remove final :0 from composition
        compositionfinal={}
        for c in composition:
                if c.endswith(':0'):
                        cnew=c.rsplit(':0',1)[0]
                        compositionfinal[cnew]=composition[c]
                else:
                        compositionfinal[c]=composition[c]
        return composition

def main():
        parser = argparse.ArgumentParser()
        parser.add_argument('--inputfile',help='EHRBase webtemplate filename',default='webtemplate.json')
        parser.add_argument('--outputfile',help='output file',default='output')
        parser.add_argument('--type_of_output',help='type of output',default='all',choices=['all','flatpath','composition'])

        args=parser.parse_args()
        if(args.inputfile==None):
                print('input file not specified')
                exit(1)
        else:
                inputfile=args.inputfile
        
        if(args.outputfile==None):
                print('output file not specified')
                exit(1)
        else:
                outputfile=args.outputfile
        
        outputtype=args.type_of_output
        print(f'inputfile={inputfile}, outputfile={outputfile}, outputtype={outputtype}')
        
        #read the input file
        with open(inputfile) as f:
                webtemplatestring=f.read()
        nohash=webtemplatestring.replace("#","%23")
        webtemplate=json.loads(nohash)
        # print(f"{json.dumps(json.loads(nohash),sort_keys=True, indent=1, separators=(',', ': '))}")

        #parse the webtemplate
        #output is a list of lists
        #each list contains the following elements
        #id,name,path,flatpath,rmtype,inputs
        output,templatename=webtempconverter(webtemplate)
        print(f'templatename={templatename}')
        templatename=templatename.lower()

        #write the output to a file
        if outputtype=='all':
                with open(outputfile,'w') as f:
                        index=0
                        for o in output:
                                index+=1
                                f.write(str(index)+") "+", ".join(map(str,o))+ "\n")
        elif outputtype=='flatpath':
                flatdict={}
                for o in output:
                        if o[3] not in flatdict:
                                flatdict[o[3]]=o[2]
                        else:
                                old=flatdict[o[3]]
                                if type(old)==list:
                                        old.append(o[2])
                                        flatdict[o[3]]=old
                                else:
                                        flatdict[o[3]]=[old,o[2]]
                flatwithtemplateid={}
                for f in flatdict:
                        fwith=templatename+'/'+f
                        flatwithtemplateid[fwith]=flatdict[f]
                      
                with open(outputfile,'w') as f:
                        json.dump(flatwithtemplateid,f,indent=2)
        else:
                composition=createcomposition(output)
                compositionwithtemplateid={}
                for f in composition:
                        fwith=templatename+'/'+f
                        compositionwithtemplateid[fwith]=composition[f]                       
                with open(outputfile,'w') as f:
                        json.dump(compositionwithtemplateid,f,indent=2)   


if __name__ == '__main__':
    main()