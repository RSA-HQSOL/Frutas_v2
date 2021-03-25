"""
Piccolo programma di prova della schede rele
"""
import PySimpleGUI as sg
import RPi.GPIO as GPIO

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

#Definisco la GUI 
sg.ChangeLookAndFeel('GreenTan')
layout=[
    [sg.Text('RELAYS ACTIVATOR', size=(35, 1), font=("Helvetica", 25))],
    [sg.Text("_"*100)],
    #Sezione comando manuale
    [sg.Text('COMMANDS',font=("Helvetica", 16))],
    [sg.Button('RelayJ2 ON',size=(15,3)), sg.Button('RelayJ2 OFF',size=(15,3))], 
    [sg.Button('RelayJ3 ON',size=(15,3)), sg.Button('RelayJ3 OFF',size=(15,3))], 
    [sg.Button('RelayJ4 ON',size=(15,3)), sg.Button('RelayJ4 OFF',size=(15,3))], 
    [sg.Button('RelayJ5 ON',size=(15,3)), sg.Button('RelayJ5 OFF',size=(15,3))],
    [sg.Text("_"*100)],
    [sg.Button('Quit program',size=(15,3))],
    [sg.T()],
]
#Creo la finestra di configurazione e comando 
window = sg.Window('HQSOL Srl - program by RSA lab', default_element_size=(40, 1)).Layout(layout)

#Loop che processa i comandi
while True:
    event, values = window.Read()
    if event== "Set Connection": break
    if event is None or event == 'Quit program':
        raise SystemExit("Program terminated")
   
    print("\n=============== ",event)

    if event == 'RelayJ2 ON': GPIO.output(J2,GPIO.HIGH)
    if event == 'RelayJ3 ON': GPIO.output(J3,GPIO.HIGH)
    if event == 'RelayJ4 ON': GPIO.output(J4,GPIO.HIGH)
    if event == 'RelayJ5 ON': GPIO.output(J5,GPIO.HIGH)

    if event == 'RelayJ2 OFF': GPIO.output(J2,GPIO.LOW)
    if event == 'RelayJ3 OFF': GPIO.output(J3,GPIO.LOW)
    if event == 'RelayJ4 OFF': GPIO.output(J4,GPIO.LOW)
    if event == 'RelayJ5 OFF': GPIO.output(J5,GPIO.LOW)