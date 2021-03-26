'''
Created on 4 dic 2019

@author: Raffaele Salutari - HQSOL SRL - La Spezia

v3: 21/03/2021: ora in questo file ci sono solo le classi che definisono
gli inverter in astratto

v2: inverterSE e inverterSETCP ora usano i dati letti per inizializzare l'oggetto inverter. 
Quindi ora unico parametro della classe è indirizzo modbus o indirizzo ip
Se non riescono a leggere mettono null invece di valori predefiniti

'''
#Modulo contenente classi e metodi degli inverter fotovoltaici EDM SE

#======================================================================================

#Classe generica inverter
class Inverter:
    "This is the most abstract model of an inverter"
    def __init__(self, mppt=1, phases=1 ):
        #identifiers of the inverter
        self.model=None
        self.SN=None
        self.modbusVers=None
        self.swVers=None
        self.swBuild=None
        #inverter status
        self.temp=None
        self.mode=None
        self.error=None
        self.Etoday=None
        self.Etot=None
        self.Ttot=None
        #rating variables
        self.Vnom=None
        self.Fnom=None
        self.Pnom=None
        self.Pmax=None
        #DC data
        self.mpptNum=mppt
        self.V1=self.V2=self.V3=self.V4=None
        self.I1=self.I2=self.I3=self.I4=None
        #AC data
        self.phNum=phases
        self.Pac=self.Qac=None
        self.PFac=None
        self.VacA=self.VacB=self.VacC=None
        self.IacA=self.IacB=self.IacC=None
        self.FacA=self.FacB=self.FacC=None
        self.PacA=self.PacB=self.PacC=None
        # Grid data (read by EM if present)
        self.VgridA=self.VgridB=self.VgridC=None
        self.IgridA=self.IgridB=self.IgridC=None
        self.PgridA=self.PgridB=self.PgridC=None
        # Load data (read by EM if present)
        self.VloadA=self.VloadB=self.VloadC=None
        self.IloadA=self.IloadB=self.IloadC=None
        self.PloadA=self.PloadB=self.PloadC=None
        # All inverter data (if present)
        self.IinvA=self.IinvB=self.IinvC=None
        self.PinvA=self.PinvB=self.PinvC=None

#--------------------    
    def printInfo(self):
        print("Model=",self.model," Serial=", self.SN, " SW version=", self.swVers, " SW build=", self.swBuild)
        print("Vnom=", self.Vnom," Fnom=",self.Fnom," Pnom=",self.Pnom," Pmax=",self.Pmax)
        print("mpptNum=",self.mpptNum," phNum=",self.phNum)
        self.printStatus()
#--------------------
    def printStatus(self):
        print("Mode=",self.opmode," Error=", self.error, " Temperature=", self.temp)
#--------------------
    def printYield(self):
        print("Etoday=",self.Etoday," Etotal=", self.Etot, " Time total=", self.Ttot)
#--------------------
    def printData(self):
        print("V1=    %6.2f"%self.V1,"V    I1=  %6.2f"%self.I1,"A    ",end='')
        if self.mpptNum>1:
            print("V2=    %6.2f"%self.V2,"V    I2=  %6.2f"%self.I2,"A")
            if self.mpptNum>2: print("V3=    %6.2f"%self.V3,"V    I3=%6.2f"%self.I3,"A    V4=%6.2f"%self.V4,"V    I4=%6.2f"%self.I4,"A    ")
        else: print()
        print("PacA=  %6.1f"%self.PacA,"W    VacA=  %6.2f"%self.VacA,"V    IacA=%6.2f"%self.IacA,"A    FacA=%4.1f"%self.FacA,"Hz")
        print("PgridA=%6.1f"%self.PgridA,"W    VgridA=%6.2f"%self.VgridA,"V    IgridA=%6.2f"%self.IgridA,"A")
        print("PloadA=%6.1f"%self.PloadA,"W    VloadA=%6.2f"%self.VloadA,"V    IloadA=%6.2f"%self.IloadA,"A")
        print("PinvA= %6.1f"%self.PinvA,"W    IinvA= %6.2f"%self.IinvA,"A")
        if self.phNum==3:
            print("PacB=  %6.1f"%self.PacB,"W    VacB=  %6.2f"%self.VacB,"V    IacB=%6.2f"%self.IacB,"B    FacB=%4.1f"%self.FacB,"Hz")
            print("PgridB=%6.1f"%self.PgridB,"W    VgridB=%6.2f"%self.VgridB,"V    IgridB=%6.2f"%self.IgridB,"A")
            print("PloadB=%6.1f"%self.PloadB,"W    VloadB=%6.2f"%self.VloadB,"V    IloadB=%6.2f"%self.IloadB,"A")
            print("PinvB= %6.1f"%self.PinvB,"W    IinvB= %6.2f"%self.IinvB,"A")
            print("PacC=  %6.1f"%self.PacC,"W    VacC=  %6.2f"%self.VacC,"V    IacC=%6.2f"%self.IacC,"A    FacC=%4.1f"%self.FacC,"Hz")
            print("PgridC=%6.1f"%self.PgridC,"W    VgridC=%6.2f"%self.VgridC,"V    IgridC=%6.2f"%self.IgridC,"A")
            print("PloadC=%6.1f"%self.PloadC,"W    VloadC=%6.2f"%self.VloadC,"V    IloadC=%6.2f"%self.IloadC,"A")
            print("PinvC= %6.1f"%self.PinvC,"W    IinvC= %6.2f"%self.IinvC,"A")
        print("Pac=   %6.1f"%self.Pac,"W    Qac= %6.2f"%self.Qac,"VA     PFac=%6.2f"%self.PFac)