""" 
FRUTAS CONTROLLER
Programma controllore impianto FRUTAS
- Usa semplice Web Server creato con PySimpleGUIWeb
- Legge file di configurazione
- Fa loop infinito
- Nel loop legge la potenza degli inverter e ne fa la somma
- Se la somma è superiore a una certa soglia con isteresi, allora chiude un contatto
che a sua volta spegne il gruppo elettrogeno
"""
#import librerie di sistema 
import PySimpleGUI as sg
#import PySimpleGUIWeb as sg
import os
import datetime
import logging
import logging.handlers
import RPi.GPIO as GPIO

#import librerie mie
from inverterSE import *
from ClassRelay import *

#Definisco sampling time delle misure
DELTAT=5000

#Definisco parametri del relay
TRIGGER=10000
HYSTPLUS=1000
HYSTMINUS=0

#setting iniziale scheda relays
J2=4
J3=22
J4=6
J5=26
GPIO.setmode(GPIO.BCM)
GPIO.setup(J2,GPIO.OUT)
GPIO.setup(J3,GPIO.OUT)
GPIO.setup(J4,GPIO.OUT)
GPIO.setup(J5,GPIO.OUT)

#setup del logger
logger = logging.getLogger("main")
#handler a file rotativo
handler = logging.handlers.RotatingFileHandler(
 "frutas.log", mode='w', maxBytes=100000, backupCount=3)
handler.setLevel(logging.DEBUG)
#handler a console
ch=logging.StreamHandler()
ch.setLevel(logging.DEBUG)
#Definisco formattazione dei logger (uguale per entrambi)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s',
 datefmt='%Y-%m-%d %H:%M:%S')
handler.setFormatter(formatter)
ch.setFormatter(formatter)  
#Aggiungo gli handler al logger gli assegno il livello
logger.addHandler(handler)
logger.addHandler(ch)
logger.setLevel(logging.DEBUG)

logger.info("Program started")
#Setting del relè del gruppo elettrogeno
genset=relay(TRIGGER,HYSTPLUS,HYSTMINUS)

#Schermata di configurazione iniziale
#Verifica se esiste un file contenente l'ultimo path al file dati usato
dir=os.getcwd()
try:
    with open(dir+"/lastOpenedDataFile.txt") as f:
        lastOpenedDataFile=f.readline()
        f.closed
except IOError:
    lastOpenedDataFile=dir+"/frutas.conf"
#Definisco la GUI 
sg.ChangeLookAndFeel('GreenTan')
layout=[[sg.Image(dir+'/logo-HQSOL-100.png',size=(100,100)),
    sg.Text('  Frutas Genset Controller', size=(50, 1), font=("Helvetica", 25))],
    [sg.Text('Choose the file with the list of IP addresses', size=(40, 1))],
    [sg.Text('Open this file:', size=(11, 1), auto_size_text=False, justification='left'),
     sg.InputText(lastOpenedDataFile,size=(100,1),key='ConfigFile'), sg.FileBrowse()],     
    [sg.Submit(), sg.Quit()]]
#Attivo la GUI
window = sg.Window('HQSOL Srl - created by RSA lab',default_element_size=(40, 1)).Layout(layout)
#window = sg.Window('HQSOL Srl - created by RSA lab', layout, web_ip='localhost',web_port=8888, web_start_browser=True)
while True:
    button, values = window.Read()
    #Se non è stato scelto il file di configurazione allora esco
    if not values['ConfigFile']:
        sg.Popup("ERRORE", "Nessun file è stato scelto")
    if button == "Quit":
        logger.info("Program terminated while selecting configuration file")
        quit()
    else: 
        #Provo a leggere il file configurazione
        try:
            with open(values['ConfigFile']) as f:
                righe=f.readlines()
                f.closed
                IPlist=[]
                for IPinv in righe:
                    IPlist.append(IPinv.strip("\n"))
                window.close()
            break
        except IOError:
            logger.error("Configuration file invalid or missing")
            sg.Popup("ERRORE", "File non valido")

logger.info("Configurazione acquisita, inizio ciclo principale")

########################CICLO PRINCIPALE#####################
#Ho acquisito la configurazione, ora inizio il ciclo principale
t=0
invlist=[] #Lista che contiene gli inverter istanziati
for IPinv in IPlist:
    inv=InverterSETCP(p=IPinv)
    invlist.append(inv)

#Definisco layout della schermata principale 
#Dati generali
layout=[
    [sg.Image(dir+'/logo-HQSOL-100.png',size=(100,100)),sg.Text('  Frutas Genset Controller', size=(50, 1), font=("Helvetica", 25))],
    [sg.Text('Number of inverters:'+str(len(IPlist)), size=(22, 1)),
     sg.Text('Timestamp='+str(datetime.datetime.now()),key='Timestamp')]
    ]
#Dati di ciascun inverter
i=1
for inv in invlist:
    layout.append([sg.Text('IP address:'+inv.IP, size=(22, 1)),
    sg.Text('Model='+str(inv.model),size=(13,1),key="Model"+str(i)),
    sg.Text('SN='+str(inv.SN),size=(20,1), key="SN"+str(i)),
    sg.Text("Power="+str(inv.Pac),size=(15,1),key="Pac"+str(i)),
    sg.Text("Opmode="+str(inv.mode),size=(20,1),key="opmode"+str(i)),
    sg.Text("Error="+str(inv.error),size=(20,1),key="error"+str(i)),
    sg.Text("cerror="+str(inv.cerror),size=(15,1),key="cerror"+str(i)),
    sg.Text("PlimFun="+str(inv.PlimFun),size=(15,1),key="PlimFun"+str(i))
    ])
    i=i+1
#Dati impianto
layout.append([
    sg.Text("Ptot=", size=(22,1),key="P"), 
    sg.Text("Genset=", size=(13,1),key="Genset"),
    sg.Text("Plant Status=", size=(22,1),key="status")
    ])
layout.append([sg.Quit()])

window = sg.Window('HQSOL Srl - created by RSA lab',default_element_size=(40, 1)).Layout(layout)

#Ciclo principale con timeout
while button!='Quit' and button != sg.WIN_CLOSED:
    button, values = window.Read(timeout=DELTAT)
    #Inizializzo valori impianto
    Pplant=0
    statusPlant="Normal"
    i=1
    window['Timestamp'].update("Timestamp="+str(datetime.datetime.now()))
    #Leggo i dati degli inverter
    for inv in invlist:
        if inv.model==None: 
            inv.getInfoModbus() #Se mnon era ancora riuscito a leggere le info
            window['Model'+str(i)].update("Model="+str(inv.model))
            window['SN'+str(i)].update("SN="+str(inv.SN))
        inv.getDataModbus_P()
        #Se non riesco a leggere un inverter, allora metto il plat in stato di warning
        if inv.cerror!=0:
            logger.warning("Failed to communicate with inverter Model="+str(inv.model)+" SN="+str(inv.SN)+" IP="+str(inv.IP))
            statusPlant="Warning"
            window["Pac"+str(i)].update("Power="+str(None))
            window["opmode"+str(i)].update("Opmode="+str(None))
            window["error"+str(i)].update("Error="+str(None))
            window["cerror"+str(i)].update("cerror="+str(inv.cerror))
            window["PlimFun"+str(i)].update("PlimFun="+str(inv.PlimFun))

        else: 
            Pplant=Pplant+inv.Pac
            #Anche se  in modalit Standby meeto il plant in warning
            if inv.mode=="Standby mode": statusPlant="Warning"
            #Stampo i dati dell'inverter
            window["Pac"+str(i)].update("Power="+str(inv.Pac))
            window["opmode"+str(i)].update("Opmode="+str(inv.mode))
            window["error"+str(i)].update("Error="+str(inv.error))
            window["cerror"+str(i)].update("cerror="+str(inv.cerror))
            window["PlimFun"+str(i)].update("PlimFun="+str(inv.PlimFun))
        i=i+1
        
    #Operazioni a livello di controllo impianto
    if statusPlant=="Normal":
        window["P"].update("Tot power="+str(Pplant))
        window["status"].update("Plant status=Normal")
        active=genset.trigger(Pplant)
        if active: 
            GPIO.output(J3,GPIO.HIGH)
            logger.info("P=%6.2f - Genset=ON" %Pplant)
            window["Genset"].update("Genset=ON")
        else: 
            GPIO.output(J3,GPIO.LOW)
            logger.info("P=%6.2f - Genset=OFF" %Pplant)
            window["Genset"].update("Genset=OFF")
    else:
        window["P"].update("Tot power="+str(None))
        window["status"].update("Plant status=Warning")
        active=0
        window["Genset"].update("Genset=OFF")
        GPIO.output(J3,GPIO.LOW)
        logger.warning("Genset=OFF")

#Chiusura del programma
window.close()
GPIO.output(J3,GPIO.LOW)
logger.info("Program terminated by user")
