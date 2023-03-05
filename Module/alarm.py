from gpiozero import Buzzer
from time import sleep
from threading import Thread

buzzer = Buzzer(21)
#System on beep
def systemOn():
    buzzer.on()
    sleep(0.1)
    buzzer.off()
    sleep(0.1)
    buzzer.on()
    sleep(0.1)
    buzzer.off()
    sleep(0.1)
    buzzer.on()
    sleep(0.1)
    buzzer.off()
    
#Fire Alarm buzzer (danger!)
def fireAlarm(fire):
    if fire == 1 :
        buzzer.on()
        sleep(0.5)
        buzzer.off()
        sleep(0.2)
        buzzer.on()
        sleep(0.5)
        buzzer.off()
        sleep(0.2)
        buzzer.on()
        sleep(0.5)
    else:
        buzzer.off()

#Gs alarm buzzer (danger!)
def gasAlarm(gas):
    if gas ==1 :
         buzzer.on()
         sleep(0.15)
         buzzer.off()
         sleep(1)
         buzzer.on()
         sleep(0.15)
         buzzer.off()
         sleep(1)
    else :
        buzzer.off()

#Music on Buzzer
def musicNotif(music):
    if music ==1 :
         buzzer.on()
         sleep(1)
         buzzer.off()
    else :
        buzzer.off()

#Motion alarm
def motionAlarm():
    if motion ==1 :
         buzzer.on()
         sleep(0.15)
         buzzer.off()
         sleep(0.15)
         buzzer.on()
         sleep(0.15)
         buzzer.off()
         sleep(0.15)
    else :
        buzzer.off()