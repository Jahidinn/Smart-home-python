""" ** Code by Jahidin 2023 ** """

import telepot
from telepot.loop import MessageLoop
import os
import board
import RPi.GPIO as GPIO
from subprocess import call
from picamera import PiCamera
import adafruit_dht
import psutil
from threading import Thread
from gpiozero import Servo
from gpiozero.pins.pigpio import PiGPIOFactory
import datetime; import time; from time import sleep

#self message & instruction module
import message
import instruction
import alarm
import system

LDR = 23; PIR = 22; MQ135 = 24; firesensor = 25; rainsensor = 4; soilmoisturesensor = 17
set_input = [PIR, LDR, MQ135, firesensor, rainsensor, soilmoisturesensor]
GPIO.setup(set_input, GPIO.IN)

inner_light = 26; front_light = 19; top_light = 13
firefighting = 5; fan = 10; doorlock = 9; waterpump = 6; music = 11
set_output = [inner_light, front_light, top_light, firefighting, fan, doorlock, waterpump, music]
GPIO.setup(set_output, GPIO.OUT)

GPIO.setwarnings(False)  
GPIO.setmode(GPIO.BCM)

path=os.getenv("HOME")
camera = PiCamera()
camera.resolution = (640, 480)
camera.framerate = 25

for proc in psutil.process_iter():
    if proc.name()=='libgpiod_pulsein' or proc.name()=='libgpiod_pulsei':
        proc.kill()

alarm.systemOn()

factory = PiGPIOFactory()
window = Servo(18, pin_factory=factory)
window.min()

dhtDevice = adafruit_dht.DHT22(board.D27)
def tempHumidity():
    global temp, kelembaban, temperature_c, humidity
    while True:
        try:
            temperature_c = dhtDevice.temperature
            temperature_f = temperature_c * (9 / 5) + 32
            humidity = dhtDevice.humidity 
            temp = "Temperatur: {:.1f} F / {:.1f} C ".format(temperature_f, temperature_c)
            kelembaban = "Kelembaban Udara: {}% ".format(humidity)
        except RuntimeError as error:
            print(error.args[0])
            time.sleep(2.0)
            continue
        except Exception as error:
            dhtDevice.exit()
            raise error
        time.sleep(0.5) 

temperature_c = 0
tempSensorControl = 1
def tempControlSystem():
    fanSetPoint = 0
    while True:
        if tempSensorControl != 0 :
            if temperature_c < 23 :
                fanNew = 0
                if fanSetPoint != fanNew:
                    fanSetPoint = fanNew
                    acSystemOut(0)
                    notif = message.autoFanOff
                    autoNotification(notif)                        
            elif temperature_c > 26 :
                fanNew = 1
                if fanSetPoint != fanNew:
                    fanSetPoint = fanNew
                    acSystemOut(1)
                    notif = message.autoFanOn
                    autoNotification(notif)
        time.sleep(1)

humidity = 0, humSensorControl = 1
def humControlSystem(): 
    humiditySetPoint = 0
    while True:
        if humSensorControl != 0 :
            if humidity <= 69 :
                humidityNew = 0
                if  humiditySetPoint != humidityNew:
                    humiditySetPoint = humidityNew
                    notif = message.lessHumidity
                    autoNotification(notif)
                    windowControl(0)                      
            elif humidity >= 71 :
                humidityNew = 1
                if humiditySetPoint != humidityNew:
                    humiditySetPoint = humidityNew
                    notif = message.moreHumidity
                    autoNotification(notif)
                    windowControl(1)
        time.sleep(1)

ldrSensorControl = 1
def lightingSystem():
    lightSetPoint = 0
    while True:       
        LDRIN = GPIO.input(LDR)
        if ldrSensorControl != 0:
            if LDRIN == 1:
                light = LDRIN
                innerLight = light
                if light != lightSetPoint:
                    lightSetPoint = light
                    lightingOut(light)
                    notif = message.autoLightOn
                    autoNotification(notif)            
            elif LDRIN == 0:
                light = LDRIN
                innerLight = light
                if light != lightSetPoint:
                    lightSetPoint = light
                    lightingOut(light);innerLight = 0
                    notif = message.autoLightOff
                    autoNotification(notif)
        time.sleep(0.5)

pirSensorControl = 0
def motionDetectionSystem():
    global securityStatus
    motionSetPoint = 0 
    while True:
        PIRIN = GPIO.input(PIR)
        if pirSensorControl != 0:
            securityStatus = message.securityMode1
            if PIRIN == 0:
                motion = PIRIN
                if motion != motionSetPoint:
                    notif = message.noMotion
                    autoNotification(notif)
                    motionSetPoint = motion   
            elif PIRIN == 1:
                motion = PIRIN
                if motion != motionSetPoint:
                    motionSetPoint = motion
                    notif = message.motion
                    autoNotification(notif)
                    sendVideo(chat_id)
        else :
            securityStatus = message.securityMode0
        time.sleep(0.5)

#airquality
aqSensorControl = 1
def airQualitySystem():
    global airQuality
    airQualitySetPoint = 1
    while True:
        MQIN = GPIO.input(MQ135)
        if aqSensorControl != 0 :
            if MQIN == 0 :
                airQuality = MQIN
                alarm.gasAlarm(1)
                if airQuality != airQualitySetPoint:
                    airQualitySetPoint = airQuality
                    notif = message.poorAirQuality
                    autoNotification(notif)
                    acSystemOut(1)
                    windowControl(1)

            elif MQIN == 1:
                airQuality = MQIN
                alarm.gasAlarm(0)
                if airQuality != airQualitySetPoint:
                    airQualitySetPoint = airQuality
                    notif = message.goodAirQuality
                    autoNotification(notif)
                    windowControl(0)
                    acSystemOut(0)
        time.sleep(0.5)

fireSensorControl = 1
def fireFightingSystem():
    fireSetPoint = 1
    while True:
        FIREIN = GPIO.input(firesensor)
        if fireSensorControl != 0 :
            if FIREIN == 1:
                fire = FIREIN
                alarm.fireAlarm(0)
                if fire != fireSetPoint:
                    fireSetPoint = fire
                    notif = message.noFire
                    autoNotification(notif)
                    fireFightingOut(0)
                        
            elif FIREIN == 0:
                fire = FIREIN
                alarm.fireAlarm(1)
                if fire != fireSetPoint:
                    fireSetPoint = fire
                    notif = message.fire
                    autoNotification(notif)
                    fireFightingOut(1)
        time.sleep(0.5)

def rainAlertSystem():
    global rain
    rainSetPoint = 0
    while True:
        RAININ = GPIO.input(rainsensor)
        if RAININ == 1:
            rain = RAININ
            if rain != rainSetPoint:
                rainSetPoint = rain
                notif = message.noRain
                autoNotification(notif)
            
        elif RAININ == 0:
            rain = RAININ
            if rain != rainSetPoint:
                rainSetPoint = rain
                notif = message.rain
                autoNotification(notif)
        time.sleep(0.5)

def irigationSystem():
    global soil
    soilSetPoint = 0
    while True :
        SOILIN = GPIO.input(soilmoisturesensor)
        if SOILIN == 0:
            soil = SOILIN
            if soil != soilSetPoint:
                soilSetPoint = soil
                notif = message.drySoil
                autoNotification(notif)
                
        elif SOILIN == 1:
            soil = SOILIN
            if soil != soilSetPoint:
                soilSetPoint = soil
                notif = message.moistSoil
                autoNotification(notif)
        time.sleep(1)

# def checkConnection():

def timeControlSystem():
    while True:
        now = datetime.datetime.now().time()
        if now.hour == 6 and now.minute == 0  :
            notif = message.morningNotif
            autoNotification(notif)
            doorLock(0)
            
        elif now.hour == 20 and now.minute == 0 :
            notif = message.timeToLock
            goodNight = message.nightNotif
            autoNotification(notif)
            autoNotification(goodNight)
            doorLock(1)
            
        time.sleep(30)

def handleMessage(msg):
    global innerLight, frontLight, topLight, temperature_cc, humidityy, humSensorControl
    global pirSensorControl, ldrSensorControl, fireSensorControl, aqSensorControl, tempSensorControl
    id = msg['chat']['id']; chat_id = id
    command = msg['text'];
    print ('Command ' + command + ' from chat id' + str(id));
    print(id)
    
    if (command == instruction.photo or command == instruction.foto):
        print ("Taking picture…");
        sendPhoto(id)
    elif (command == instruction.video or command == instruction.vid):
        sendVideo(id)
        print ("Taking video…");  
    #Temp
    elif (command == instruction.reqTemperature or command == instruction.temp):
        bot.sendMessage(id, temp)
    #Humidity
    elif (command == instruction.reqHumidity or command == instruction.hum):
        bot.sendMessage(id, kelembaban)

    #inside light
    elif (command == instruction.light1On or command == instruction.innerLightOn or command == instruction.L131):
        innerLight = 1
        lightingOut(innerLight)
        bot.sendMessage(id, message.manualLightOn)
    elif (command == instruction.light1Off or command == instruction.innerLightOff or command == instruction.L130):
        innerLight = 0
        lightingOut(innerLight)
        bot.sendMessage(id, message.manualLightOff)
   
    #front light
    elif (command == instruction.light2On or command == instruction.frontLightOn or command == instruction.L231):
        frontLight = 1
        lightingOut2(frontLight)
        bot.sendMessage(id, message.manualLightOn2)
    elif (command ==instruction.light2Off or command == instruction.frontLightOff or command == instruction.L230):
        frontLight = 0
        lightingOut2(frontLight)
        bot.sendMessage(id, message.manualLightOff2)
        
    #top light
    elif (command == instruction.light3On or command == instruction.topLightOn or command == instruction.L331):
        topLight = 1
        lightingOut3(topLight)
        bot.sendMessage(id, message.manualLightOn3)
    elif (command ==instruction.light3Off or command == instruction.topLightOff or command == instruction.L330):
        topLight = 0
        lightingOut3(topLight)
        bot.sendMessage(id, message.manualLightOff3)
    
    #window
    elif (command == instruction.openWindow or command == instruction.ow):
        window_msg = 1
        windowControl(window_msg)
        bot.sendMessage(id, message.openWindow)
    elif (command == instruction.closeWindow or command == instruction.cw):
        window_msg = 0
        windowControl(window_msg)
        bot.sendMessage(id, message.closeWindow)
    
    #fan / AC
    elif (command == instruction.fanOn or command == instruction.fan1):
        kipas = 1
        acSystemOut(kipas)
        bot.sendMessage(id, message.fanOn)
    elif (command == instruction.fanOff or command == instruction.fan0):
        kipas = 0
        acSystemOut(kipas)
        bot.sendMessage(id, message.fanOff)
    
    #Fire fighting
    elif (command == instruction.fireFon or command == instruction.fireF_1):
        fire = 1
        fireFightingOut(fire)
        bot.sendMessage(id, message.fireFon)
    elif (command == instruction.fireFoff or command == instruction.fireF_0):
        fire = 0
        fireFightingOut(fire)
        bot.sendMessage(id, message.fireFoff)
    
    #Door lock
    elif (command == instruction.lockTheDoor or command == instruction.lock1):
        lock = 1
        doorLock(lock)
        bot.sendMessage(id, message.lockedDoor)
    elif (command == instruction.unLock or command == instruction.lock0):
        lock = 0
        doorLock(lock)
        bot.sendMessage(id, message.unLockedDoor)
    
    #Water pump
    elif (command == instruction.waterPumpOn or command == instruction.wp1):
        pump = 1
        waterPump(pump)
        bot.sendMessage(id, message.waterPumpOn)
    elif (command == instruction.waterPumpOff or command == instruction.wp0):
        pump = 0
        waterPump(pump)
        bot.sendMessage(id, message.waterPumpOff)

    #Music on 
    elif (command == instruction.musicOn or command == instruction.music1):
        musik = 1
        musicOut(musik)
        alarm.musicNotif(1)
        bot.sendMessage(id, message.musicOn)
    elif (command == instruction.musicOff or command == instruction.music0):
        musik = 0
        musicOut(musik)
        bot.sendMessage(id, message.musicOff)
        
    #Home monitoring
    elif (command == instruction.homeMonitoring or command == instruction.homeMonitoring2):
        lightingMonitoring(id)
        homeMonitoring(id)

    #LightMonitoring
    elif (command == instruction.lightMonitoring or command == instruction.lighting):
        lightingMonitoring(id)
    
    #weather monioring
    elif (command == instruction.weather or command == instruction.weather2):
        if rain == 1:
            cuaca = message.sunnyWeather
        else:
            cuaca = message.rainyWeather
        bot.sendMessage(id, cuaca)
    
    #Soil moisture
    elif (command == instruction.soilMoisture or command == instruction.soilMoisture2):
        if soil == 1:
            soilMoisture = message.drySoil
        else:
            soilMoisture = message.moistSoil   
        bot.sendMessage(id, soilMoisture)
    
    #Air quality monitoring
    elif (command == instruction.airQuality or command == instruction.airQuality2):
        if airQuality == 1:
            airQualityStatus = message.goodAirQuality
        else:
            airQualityStatus = message.poorAirQuality   
        bot.sendMessage(id, airQualityStatus)

    #Sensor control
    
    #motion sensor control (switch mode)
    elif (command == instruction.pirOn or command == instruction.pirOn2):
        pirSensorControl = 1
        autoNotification(message.motionSensorOn)
    elif (command == instruction.pirOff or command == instruction.pirOff2):
        pirSensorControl = 0
        autoNotification(message.motionSensorOff)

    #LDR sensor control (switch mode)
    elif (command == instruction.ldrControlOn or command == instruction.ldrControlOn2):
        ldrSensorControl = 1
        autoNotification(message.ldrSensorOn)
        print (ldrSensorControl)
    elif (command == instruction.ldrControlOff or command == instruction.ldrControlOff2):
        ldrSensorControl = 0
        autoNotification(message.ldrSensorOff)

    # elif (command == instruction.fireControlOn or command == instruction.fireControlOn2):
    #     fireSensorControl = 1
    #     autoNotification(message.fireSensorOn)
    # elif (command == instruction.fireControlOff or command == instruction.fireControlOff2):
    #     fireSensorControl = 0
    #     autoNotification(message.fireSensorOff)

    #Air quality sensor (switch mode)
    elif (command == instruction.aqControlOn or command == instruction.aqControlOn2):
        aqSensorControl = 1
        autoNotification(message.aqSensorOn)
    elif (command == instruction.aqControlOff or command == instruction.aqControlOff2):
        aqSensorControl = 0
        autoNotification(message.aqSensorOff)

    #Temperature & humidity sensor control (Switch mode)
    elif (command == instruction.tempAutoMode or command == instruction.tempAutoMode2):
        tempSensorControl = 1
        autoNotification(message.tempSensorOn)
    elif (command == instruction.tempManualMode or command == instruction.tempManualMode2):
        tempSensorControl = 0
        autoNotification(message.tempSensorOff)
    elif (command == instruction.humidityAutoMode or command == instruction.humidityAutoMode2):
        humSensorControl = 1
        autoNotification(message.humSensorOn)
    elif (command == instruction.humidityManualMode or command == instruction.humidityManualMode2):
        humSensorControl = 0
        autoNotification(message.humSensorOff)

    #repair command
    elif (command == instruction.repairSystem):
        system.repair
        bot.sendMessage(id, message.repaired)

    #not found command
    else:
        bot.sendMessage(id, message.notFound)

#Window control function
def windowControl(window_msg):
    global windowStatus
    if window_msg == 0 :
        window.min()
        windowStatus = message.windowCloseCondition
        sleep(2)
    elif window_msg == 1 :
        window.max ()
        windowStatus = message.windowOpenCondition
        sleep(2)
    
# Door Control
# def doorControl(door_msg):
#     if door_msg == 0 :
#         door.min()
#         sleep(2)
#     elif door_msg == 1 :
#         door.max ()
#         sleep(2)

#Camera system function
def sendPhoto(id):
    global camera
    camera.start_preview()
    camera.capture(path + '/pic.jpg',resize=(640,480))
    time.sleep(2)
    camera.stop_preview()
    bot.sendPhoto(id, open(path + '/pic.jpg', 'rb'))
    print ("photo sended");
    
def sendVideo(id):
    filename = "./video_" + (time.strftime("%y%b%d_%H%M%S"))
    camera.start_recording(filename + ".h264")
    sleep(5)
    camera.stop_recording()
    command = "MP4Box -add " + filename + '.h264' + " " + filename + '.mp4'
    print(command)
    call([command], shell=True)
    bot.sendVideo(id, video = open(filename + '.mp4', 'rb'))
    bot.sendMessage(id, 'video is sended!')

#Notification function
def autoNotification(notif):
    id = chat_id
    bot.sendMessage(id, notif)

#Light monitoring function
def lightingMonitoring(id):
    if innerLight ==1 and frontLight == 1 and topLight == 1 :
        status = message.allOn
    elif innerLight == 0 and frontLight == 0 and topLight == 0 :
        status = message.allOff
    elif  innerLight == 1 and frontLight == 0 and topLight == 0 :
        status = message.innerLightOn
    elif  innerLight == 0 and frontLight == 1 and topLight == 0 :
        status = message.frontLightOn
    elif  innerLight == 0 and frontLight == 0 and topLight == 1 :
        status = message.topLightOn
    elif  innerLight == 0 and frontLight == 1 and topLight == 1 :
        status = message.innerLightOff
    elif  innerLight == 1 and frontLight == 0 and topLight == 1 :
        status = message.frontLightOff
    elif  innerLight == 1 and frontLight == 1 and topLight == 0 :
        status = message.topLightOff
    bot.sendMessage(id, status)

#Home monitoring
def homeMonitoring(id):
    global fanControl, lockCondition, fireCondition, pumpCondition, musicCondition
    newL = instruction.newLine
    if fanControl == 1 :
        fanStatus = message.fanOnCondition
    elif fanControl == 0 :
        fanStatus = message.fanOffCondition
    elif lockCondition == 1 :
        doorStatus = message.lockedDoorCondition
    elif lockCondition == 0 :
        doorStatus = message.unlockedDoorCondition
    elif fireCondition == 1 :
        fireStatus = message.fireOnCondition
    elif fireCondition == 0 :
        fireStatus = message.fireOffCondition
    elif pumpCondition == 1 :
        pumpStatus = message.waterPumpOnCondition
    elif pumpCondition == 0 :
        pumpStatus = message.waterPumpOffCondition
    elif musicCondition == 1 :
        musikStatus = message.musicOnCondition
    elif musicCondition == 0 :
        musikStatus = message.musicOffCondition
    bot.sendMessage(id, fanStatus + newL + doorStatus+ newL + fireStatus + newL + pumpStatus)
    bot.sendMessage(id, windowStatus + newL + musikStatus)
    bot.sendMessage(id, securityStatus)

#Output control function
def lightingOut(innerLightCondition):
    GPIO.output(inner_light, innerLightCondition) 
def lightingOut2(frontLightCondition):
    GPIO.output(front_light, frontLightCondition) 
def lightingOut3(topLightCondition):
    GPIO.output(top_light, topLightCondition)

def acSystemOut(fanControl):
    GPIO.output(fan, fanControl)  
def fireFightingOut(fireCondition):
    GPIO.output(firefighting, fireCondition)  
def doorLock(lockCondition):
    GPIO.output(doorlock, lockCondition)
def waterPump(pumpCondition):
    GPIO.output(waterpump, pumpCondition)
def musicOut(musicCondition):
    GPIO.output(music, musicCondition)

#bot API
global chat_id; chat_id = 1262139307
bot = telepot.Bot('1457000855:AAGBTjDZZ4lLE0CAS4FS7GpooeXCJtH_Kug');
bot.message_loop(handleMessage);
print ("Listening to bot messages….");

#Start
if __name__ == '__main__':
    Thread(target = tempHumidity).start()
    Thread(target = lightingSystem).start() 
    Thread(target = airQualitySystem).start()
    Thread(target = fireFightingSystem).start()
    Thread(target = motionDetectionSystem).start()
    Thread(target = rainAlertSystem).start()
    Thread(target = irigationSystem).start()
    Thread(target = tempControlSystem).start()
    Thread(target = humControlSystem).start()
    Thread(target = timeControlSystem).start()
    
#End Script