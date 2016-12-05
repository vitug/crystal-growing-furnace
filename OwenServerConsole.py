# -*- coding: cp1251 -*-
from TOwen import trm251
from TController import MySerial as Serial
from TController import Heater;
import time

#создаем последовательный порт
#COM = Serial.ComPort(0, 9600, timeout=1)
try:
    COM = Serial.ComPort(2, 9600, timeout=.3)#открываем COM1
except:
    raise Exception('Error openning port!')
    pass

heater = Heater.Heater(COM,0)
    
#COM.LoggingIsOn=True#включаем логирование в файл

pidReg=trm251.TRM251(COM,16);#настоящий порт
pidReg.Debug = True
#pidReg=trm251.TRM251(None,16);#тестовые данные
def Run():
    Temp=0;
    Power=0;        
    state=1
    counter=counterGetTemp=10
    lastPower=0;
    heater.FastMode=True    
    while 1==1:
        time.sleep(.1)
        if counter==counterGetTemp:#читаем температуру только один через 10
            Temp=pidReg.GetTemperature()
            counter=0
        else:
            counter=counter+1
        if state==1 or state==4:
            Power=pidReg.GetPower()
        else:
            Power=0;
        if  not Power==lastPower:   
            heater.SetPower(Power*10000)
            #currentPower=heater.GetPower()/100
            lastPower=Power
        print 'Temp={} Power={}'.format(Temp,Power)
       
        
Run()

        