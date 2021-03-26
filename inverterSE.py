'''
Created on 4 dic 2019

@author: Raffaele Salutari - HQSOL SRL - La Spezia

v3 21/03/2021: ora le classi specifiche per inverter SE sono stato spostate nel file 
inverterSE.py

v2: inverterSE e inverterSETCP ora usano i dati letti per inizializzare l'oggetto inverter. 
Quindi ora unico parametro della classe è indirizzo modbus o indirizzo ip
Se non riescono a leggere mettono null invece di valori predefiniti

'''
#Modulo contenente classi e metodi degli inverter fotovoltaici EDM SE

from inverter import *
import logging
from typing import NoReturn
import minimalmodbus as mb                      #For access via modbus over RS485 connection
from pyModbusTCP.client import ModbusClient     #For access via modbus over TCP connection

MAIN="main"
SERVER_PORT = 502                               #Standard port for TCP server

############## FUNZIONI UTILITA ################
#Converte una lista di registri a 16 bit in una stringa. 
#Utile quando leggo da modbus TCP un insieme di registri che contengono una informazione alfanumerca codificata ASCII
def reg2str(regs):
    str=""
    for reg in regs:
        if (reg>>8 &0xFF) != 0: str=str+chr(reg>>8 &0xFF)
        if (reg&0xFF) != 0: str=str+chr(reg&0xFF)
    return str

#Legge registri inverter SE
def getDataSE(inverter,key):
    logger=logging.getLogger(MAIN+".InverterSETCP.getDataSE")
    logger.setLevel(logging.DEBUG)
    if not inverter.is_open(): #Se comunicazione non è aperta prova ad aprirle
        if not inverter.open(): #Se non ci riesce ritorna errore
                inverter.cerror=2
                logger.warning("Failed to open comm with inverter IP="+inverter.IP)
    inverter.cerror=0
    inverter.regs=inverter.read_holding_registers(inverter.RT[key][0],inverter.RT[key][1])
    if inverter.regs!=None: 
        #Lettura andata a buon fine
        if key=="mode":
            return inverter.modeTable[inverter.regs[0]]
        if key=="model" or key=="SN" or key=="modbusVers" or key=="swVers" or key=="swBuild":
            return reg2str(inverter.regs)
        return inverter.regs[inverter.RT[key][1]-1]/10**inverter.RT[key][2]
    else: 
        #Errore lettura; gestisco il log ed esco con error=4
        inverter.cerror=4 
        logger.warning("Failed to read Pac from inverter"+inverter.IP)
        return None

############## CLASSI SPECIFICHE INVERTER SE ################
#Classe che modella il protocollo MODBUS degli inverter SE
class OEM_SE:
    "This class maps the MODBUS protocol registers of SE inverters in python dictionary"
    def __init__(self):
        #MODBUS registers
        self.Info={"model":[0x1A00,8], "SN":[0x1A10,8], "modbusVers":[0x1A18,1], "swVers":[0x1A1C,3],"swBuild":[0x1A23,3],"mpptNum":[0x1A3B,1,0],
        "Vnom":[0x1A44,1,1],"Fnom":[0x1A45,1,2],"Pnom":[0x1A46,1,0],"Pmax":[0x1A46,1,0],"phNum":[0x1A48,1,0]}
        self.RT={"VacA":[0x1001,1,1],"VacB":[0x1006,1,1],"VacC":[0x100B,1,1],"IacA":[0x1002,1,2],"IacB":[0x1007,1,2],"IacC":[0x100C,1,2],
            "PacA":[0x1003,2,1], "PacB":[0x1008,2,1],"PacC":[0x100D,2,1],"FacA":[0x1005,1,2],"FacB":[0x100A,1,2],"FacC":[0x100F,1,2],
            "V1":[0x1010,1,1],"I1":[0x1011,1,2],"P1":[0x1012,2,1],"V2":[0x1014,1,1],"I2":[0x1015,1,2],"P2":[0x1016,2,1],
            "V3":[0x1018,1,1],"I3":[0x1019,1,2],"P3":[0x101A,2,1],"V4":[0x103E,1,1],"I4":[0x103F,1,2],"P4":[0x1040,2,1],
            "Tint":[0x101C,1,0],"mode":[0x101D,1],"error":[0x101E,2],"Pac":[0x1037,2,1],"Qac":[0x1039,2,1],"PFac":[0x103D,1,3],
            "VgridA":[0x131A,1,1],"VgridB":[0x131B,1,1],"VgridC":[0x131C,1,1],"IgridA":[0x131D,2,2],"IgridB":[0x131D,1,2],"IgridC":[0x1321,1,2],"PgridA":[0x1300,2,1],"PgridB":[0x1302,2,1],"PgridC":[0x1304,2,1],
            "VloadA":[0x1323,1,1],"VloadB":[0x1324,1,1],"VloadC":[0x1325,1,1],"IloadA":[0x1326,2,2],"IloadB":[0x1328,2,2],"IloadC":[0x132A,2,2],"PloadA":[0x130A,2,1],"PloadB":[0x130C,2,1],"PloadC":[0x130E,2,1],
            "IinvA":[0x132C,2,2],"IinvB":[0x132E,2,2],"IinvC":[0x1330,2,2],"PinvA":[0x1312,2,1],"PinvB":[0x1314,2,1],"PinvC":[0x1316,2,1]
            }
        self.modeTable={0x00:"Initial mode", 0x01:"Standby mode", 0x03:"Online mode", 0x05:"Fault mode", 0x09:"Shutdown mode"}

########################################################################

#Classe che modella inverter SE con accesso MODBUS via TCP
#Usa la libreria pyModbusTCP
class InverterSETCP(Inverter,OEM_SE,ModbusClient):
    
    #Setto il logger che è derivato da quello usato nel main
    logger=logging.getLogger(MAIN+".InverterSETCP")
    logger.setLevel(logging.DEBUG)

    def __init__(self,p="localhost"):
        logger=logging.getLogger(MAIN+".InverterSETCP.__init__")
        logger.setLevel(logging.DEBUG)
        Inverter.__init__(self)
        OEM_SE.__init__(self)
        try: 
            ModbusClient.__init__(self,p,port=SERVER_PORT)
            self.IP=p
            self.cerror=0
        except ValueError:
            logger.error("Init inverter non riuscito p="+p)
            self.IP=""
            self.cerror=1

#-------------------------------------------------------------------        
    
    def getInfoModbus(self):
        logger=logging.getLogger(MAIN+".InverterSETCP.getInfoModbus")
        logger.setLevel(logging.DEBUG)
        if not self.is_open(): #Se comunicazione non è aperta prova ad aprirle
            if not self.open(): #Se non ci riesce ritorna errore
                self.cerror=2
                logger.warning("Failed to open comm with inverter IP="+self.IP)
                #print("Failed to read inverter IP="+self.IP)
                return        
        #if self.is_open(): #Se la comunicazione è aperta fa la lettura
        #la comunicazione è aperta, provo a leggere 
        self.regs=self.read_holding_registers(self.Info["model"][0],self.Info["model"][1]); print(self.regs)
        if self.regs!=None: #L'inverter risponde, leggo tutto
            self.model=reg2str(self.regs)
            self.regs=self.read_holding_registers(self.Info["SN"][0],self.Info["SN"][1]); self.SN=reg2str(self.regs)
            self.regs=self.read_holding_registers(self.Info["modbusVers"][0],self.Info["modbusVers"][1]); self.modbusVers=reg2str(self.regs)
            self.regs=self.read_holding_registers(self.Info["swVers"][0],self.Info["swVers"][1]); self.swVers=reg2str(self.regs) 
            self.regs=self.read_holding_registers(self.Info["swBuild"][0],self.Info["swBuild"][1]); self.swBuild=reg2str(self.regs)
            self.regs=self.read_holding_registers(self.Info["mpptNum"][0],self.Info["mpptNum"][1]); self.mpptNum=self.regs[self.Info["mpptNum"][1]-1]/10**self.Info["mpptNum"][2] 
            self.regs=self.read_holding_registers(self.Info["phNum"][0],self.Info["phNum"][1]); self.phNum=self.regs[self.Info["phNum"][1]-1]/10**self.Info["phNum"][2] 
            self.regs=self.read_holding_registers(self.Info["Vnom"][0],self.Info["Vnom"][1]); self.Vnom=self.regs[self.Info["Vnom"][1]-1]/10**self.Info["Vnom"][2] 
            self.regs=self.read_holding_registers(self.Info["Fnom"][0],self.Info["Fnom"][1]); self.Fnom=self.regs[self.Info["Fnom"][1]-1]/10**self.Info["Fnom"][2] 
            self.regs=self.read_holding_registers(self.Info["Pnom"][0],self.Info["Pnom"][1]); self.Pnom=self.regs[self.Info["Pnom"][1]-1]/10**self.Info["Pnom"][2] 
            self.regs=self.read_holding_registers(self.Info["Pmax"][0],self.Info["Pmax"][1]); self.Pmax=self.regs[self.Info["Pmax"][1]-1]/10**self.Info["Pmax"][2]             
            logger.info("Read info of inverter IP="+self.IP)
            self.cerror=0
        else: #L'inverter non risponde, torno errore
            self.cerror=4
            logger.warning("Failed to read inverter info IP="+self.IP)

    #----------------------------
    def getDataModbus(self):
        
        logger=logging.getLogger(MAIN+".InverterSETCP.getDataModbus")
        logger.setLevel(logging.DEBUG)

        #Leggo tensioni e correnti e potenze di fase 
        self.VacA=getDataSE(self,"VacA")
        self.IacA=getDataSE(self,"IacA")
        self.PacA=getDataSE(self,"PacA")
        self.FacA=getDataSE(self,"FacA")
        if self.phNum==3:
            self.VacB=getDataSE(self,"IacB")
            self.IacC=getDataSE(self,"IacC")
            self.PacB=getDataSE(self,"PacB")
            self.FacB=getDataSE(self,"FacB")
            self.VacC=getDataSE(self,"VacC")
            self.IacC=getDataSE(self,"IacC")
            self.PacC=getDataSE(self,"PacC")
            self.FacC=getDataSE(self,"FacC")
        #Leggo potenze totali singolo inverter   
        self.Pac=getDataSE(self,"Pac")
        self.Qac=getDataSE(self,"Qac")
        self.PFac=getDataSE(self,"PFac")

        #Leggo tensioni e correnti e potenze di fase 
        self.VgridA=getDataSE(self,"VgridA")
        self.IgridA=getDataSE(self,"IgridA")
        self.PgridA=getDataSE(self,"PgridA")
        if self.phNum==3:
            self.VgridB=getDataSE(self,"IgridB")
            self.IgridC=getDataSE(self,"IgridC")
            self.PgridB=getDataSE(self,"PgridB")
            self.VgridC=getDataSE(self,"VgridC")
            self.IgridC=getDataSE(self,"IgridC")
            self.PgridC=getDataSE(self,"PgridC")

        #Leggo tensioni e correnti e potenze di fase 
        self.VloadA=getDataSE(self,"VloadA")
        self.IloadA=getDataSE(self,"IloadA")
        self.PloadA=getDataSE(self,"PloadA")
        if self.phNum==3:
            self.VloadB=getDataSE(self,"IloadB")
            self.IloadC=getDataSE(self,"IloadC")
            self.PloadB=getDataSE(self,"PloadB")
            self.VloadC=getDataSE(self,"VloadC")
            self.IloadC=getDataSE(self,"IloadC")
            self.PloadC=getDataSE(self,"PloadC")

        #Leggo valori tensioni e correnti di ingresso
        self.V1=getDataSE(self,"V1")
        self.I1=getDataSE(self,"I1")
        if self.mpptNum > 1:
            self.V2=getDataSE(self,"V2")
            self.I2=getDataSE(self,"I2")
            if self.mpptNum>2:
                self.V3=getDataSE(self,"V3")
                self.I3=getDataSE(self,"I3")
                self.V4=getDataSE(self,"V4")
                self.I4=getDataSE(self,"I4")

            #Leggo altri valori
            self.Tint=getDataSE(self,"Tint")
            self.opmode=getDataSE(self,"mode")
            self.error=getDataSE(self,"error")

            logger.info("Read data of inverter IP="+self.IP)

    #-----------------------------------------------------

    def getDataModbus_P(self):
        logger=logging.getLogger(MAIN+".InverterSETCP.getDataModbus_P")
        logger.setLevel(logging.DEBUG)
        
        self.Pac=getDataSE(self,"Pac")
        self.PgridA=getDataSE(self,"PgridA")
        self.PloadA=getDataSE(self,"PloadA")
        self.PinvA=getDataSE(self,"PinvA")
        self.mode=getDataSE(self,"mode")
        logger.info("Read data of inverter IP="+self.IP)

########################################

#Classe che modella inverter SE con accesso MODBUS su RS485
#Usa la libreria MinimalModBus
class InverterSE(Inverter,OEM_SE,mb.Instrument):
    def __init__(self,mppt=1,phases=1,p="COM4",b=19200,a=1):
        Inverter.__init__(self,mppt,phases)
        OEM_SE.__init__(self)
        #All'oggetto Inverter vengono aggiunti i valori p,b,a,cerror
        try:
            mb.Instrument.__init__(self,p,a)
            self.serial.baudrate=b #Necessario perché il constructor di mb.Instrument setta il baudrate a 19200
            self.cerror=0
        except IOError:
            print("Errore apertura comunicazione inverter")
            self.cerror=1
    
    #----------------------------------------
    
    def getInfoModbus(self):
        try:
            self.serial.timeout  = 0.2
            self.model=     self.read_string(self.Info["model"][0], self.Info["model"][1])
            self.SN=        self.read_string(self.Info["SN"][0], self.Info["SN"][1])
            self.modbusVers=self.read_register(self.Info["modbusVers"][0], self.Info["modbusVers"][1])
            self.swVers=    self.read_string(self.Info["swVers"][0], self.Info["swVers"][1])
            self.swBuild=   self.read_string(self.Info["swBuild"][0], self.Info["swBuild"][1])
            self.mpptNum=   self.read_register(self.Info["mpptNum"][0], self.Info["mpptNum"][2])
            self.phNum=     self.read_register(self.Info["phNum"][0], self.Info["phNum"][2]) 
            self.Vnom =     self.read_register(self.Info["Vnom"][0],self.Info["Vnom"][2])
            self.Fnom =     self.read_register(self.Info["Fnom"][0],self.Info["Fnom"][2])
            self.Pnom  =    self.read_register(self.Info["Pnom"][0],self.Info["Pnom"][2])
            self.Pmax  =    self.read_register(self.Info["Pmax"][0],self.Info["Pmax"][2])
            #self.serial.close()
            self.cerror=0
        except IOError:
            print("Errore lettura inverter")
            self.cerror=2

    #----------------------------------------

    def getDataModbus(self):
        try:
            self.serial.timeout  = 0.2
            
            #Leggo tensioni e correnti di fase singolo inverter
            self.VacA =self.read_register(self.RT["VacA"][0],self.RT["VacA"][2])
            self.IacA =self.read_register(self.RT["IacA"][0],self.RT["IacA"][2])
            self.PacA  =self.read_long(self.RT["PacA"][0])/10**self.RT["PacA"][2]
            self.FacA  =self.read_register(self.RT["FacA"][0],self.RT["FacA"][2])
            if self.phNum==3:
                self.VacB =self.read_register(self.RT["VacB"][0],self.RT["VacB"][2])
                self.IacB =self.read_register(self.RT["IacB"][0],self.RT["IacB"][2])
                self.PacB =self.read_long(self.RT["PacA"][0])/10**self.RT["PacB"][2]
                self.FacB =self.read_register(self.RT["FacB"][0],self.RT["FacB"][2])
                self.VacC =self.read_register(self.RT["VacC"][0],self.RT["VacC"][2])
                self.IacC =self.read_register(self.RT["IacC"][0],self.RT["IacC"][2])
                self.PacC =self.read_long(self.RT["PacC"][0])/10**self.RT["PacC"][2]
                self.FacC =self.read_register(self.RT["FacC"][0],self.RT["FacC"][2])
            
            #Leggo potenze totali singolo inverter
            self.Pac  =self.read_long(self.RT["Pac"][0])/10**self.RT["Pac"][2]
            self.Qac  =self.read_long(self.RT["Qac"][0],signed=True)/10**self.RT["Qac"][2]
            self.PFac =self.read_register(self.RT["PFac"][0],self.RT["PFac"][2],signed=True)
            
            #Leggo tensioni e correnti e potenze di fase della rete (se misurata da Energy Meter esterno)
            self.VgridA = self.read_register(self.RT["VgridA"][0], self.RT["VgridA"][2])
            self.IgridA = self.read_register(self.RT["IgridA"][0], self.RT["IgridA"][2])
            self.PgridA = self.read_long(self.RT["PgridA"][0])/10**self.RT["PgridA"][2]
            if self.phNum==3:
                self.VgridB = self.read_register(self.RT["VgridB"][0], self.RT["VgridB"][2])
                self.IgridB = self.read_register(self.RT["IgridB"][0], self.RT["IgridB"][2])
                self.PgridB = self.read_long(self.RT["PgridB"][0])/10**self.RT["PgridB"][2]

                self.VgridC = self.read_register(self.RT["VgridC"][0], self.RT["VgridC"][2])
                self.IgridC = self.read_register(self.RT["IgridC"][0], self.RT["IgridC"][2])
                self.PgridC = self.read_long(self.RT["PgridC"][0])/10**self.RT["PgridC"][2]
            
            #Leggo tensioni e correnti e potenze di fase del carico(se misurata da Energy Meter esterno)
            self.VloadA = self.read_register(self.RT["VloadA"][0], self.RT["VloadA"][2])
            self.IloadA = self.read_register(self.RT["IloadA"][0], self.RT["IloadA"][2])
            self.PloadA = self.read_long(self.RT["PloadA"][0])/10**self.RT["PloadA"][2]
            if self.phNum==3:
                self.VloadB = self.read_register(self.RT["VloadB"][0], self.RT["VloadB"][2])
                self.IloadB = self.read_register(self.RT["IloadB"][0], self.RT["IloadB"][2])
                self.PloadB = self.read_long(self.RT["PloadB"][0])/10**self.RT["PloadB"][2]

                self.VloadC = self.read_register(self.RT["VloadC"][0], self.RT["VloadC"][2])
                self.IloadC = self.read_register(self.RT["IloadC"][0], self.RT["IloadC"][2])
                self.PloadC = self.read_long(self.RT["PloadC"][0])/10**self.RT["PloadC"][2]            

            #Leggo tensioni e correnti e potenze di fase di tutti gi inverter (se misurata da Energy Meter esterno)
            self.VinvA = self.read_register(self.RT["VinvA"][0], self.RT["VinvA"][2])
            self.IinvA = self.read_register(self.RT["IinvA"][0], self.RT["IinvA"][2])
            self.PinvA = self.read_long(self.RT["PinvA"][0])/10**self.RT["PinvA"][2]
            if self.phNum==3:
                self.VinvB = self.read_register(self.RT["VinvB"][0], self.RT["VinvB"][2])
                self.IinvB = self.read_register(self.RT["IinvB"][0], self.RT["IinvB"][2])
                self.PinvB = self.read_long(self.RT["PinvB"][0])/10**self.RT["PinvB"][2]

                self.VinvC = self.read_register(self.RT["VinvC"][0], self.RT["VinvC"][2])
                self.IinvC = self.read_register(self.RT["IinvC"][0], self.RT["IinvC"][2])
                self.PinvC = self.read_long(self.RT["PinvC"][0])/10**self.RT["PinvC"][2]                 
            
            #Leggo tensioni e correnti di ingresso
            self.V1   =self.read_register(self.RT["V1"][0],  self.RT["V1"][2])
            self.I1   =self.read_register(self.RT["I1"][0],  self.RT["I1"][2])
            if self.mpptNum > 1:
                self.V2   =self.read_register(self.RT["V2"][0],  self.RT["V2"][2])
                self.I2   =self.read_register(self.RT["I2"][0],  self.RT["I2"][2])
                if self.mpptNum>2:
                    self.V3   =self.read_register(self.RT["V3"][0],  self.RT["V3"][2])
                    self.I3   =self.read_register(self.RT["I3"][0],  self.RT["I3"][2])
                    self.V4   =self.read_register(self.RT["V4"][0],  self.RT["V4"][2])
                    self.I4   =self.read_register(self.RT["I4"][0],  self.RT["I4"][2])
            #self.serial.close()
            self.cerror=0
        except IOError:
            print("Errore lettura inverter")
            self.cerror=2

    #----------------------------------------

    def getDataModbus_P(self):
        try:
            self.serial.timeout  = 0.2
            self.Pac  =self.read_long(self.RT["Pac"][0])/10**self.RT["Pac"][2]
            #print(self.Pac)
            #self.serial.close()
            self.cerror=0
        except IOError:
            print("Errore lettura inverter")
            self.cerror=2

    #----------------------------------------

    def setPoutModbus(self,Pout):
        try: 
            self.serial.timeout  = 0.2
            Pcom=int(Pout/self.Pmax*100)
            if Pcom>100: Pcom=100
            self.write_register(12293,Pcom,functioncode=6)
            #self.serial.close()
            self.cerror=0
        except IOError:
            print("Errore scrittura inverter")
            self.cerror=3

