#-*- coding: cp1251 -*-
import math,time
     
class Heater(object):
    def __init__(self, SerialPort, Address):		
        self.SerialPort = SerialPort
        self.convertObject = convert()
        self.CurrentPowerWatts=float(0)
        self.FastMode=False;
        self.SlowModeStep=float(10);#��� �������� ������
        self.FastModeStep=float(50);#��� �������� ������		
        self.ZeroCompensation=float(0);#������������� ����
        #self.MaxPower=3300#������������ �������� 3300 �� 1000 ��.
        #self.CorrectionFactor=0.9#����� �� ������� ���������� �������� �������� ����� ����������
        self.CorrectionFactor=.98#����� �� ������� ���������� �������� �������� ����� ����������
        self.MaxPower=10000#������������ �������� 
        self.ShowMessages=False
        self.PowerControlMode=0;#0-������� �������������, 1-���������� �� ����������
        self.isPowerOn=False; #������ ������� (�������� �������)
        self.isOvenPowerOn=False; #������� ����
        self.Address=Address;#����� ����������� ���� �� 0 �� 7 (�������� �� �����)
        self.PowerDelay=.03#�������� ����� ���������� ���������� �������� ��������, �� ������ ���� ������ ��� 0,02 �������
    
    #������ ��������� ��������	
    def SetPowerWatts(self, PowerInWatts):
        self.GetState()
        if not self.isOvenPowerOn:#��� ���������� � ���� ������� ����
            raise 'Oven network is off!!!'
        if not self.isPowerOn:#�� ������� �������, �������� � ������, ���� ���� ���������� �������� � ���� ����		
            self.PowerOn()
        #������ ��������� ����
        NewPower=PowerInWatts+self.ZeroCompensation
        #����������, ������������� ��������
        self.CurrentPowerWatts=PowerInWatts
        #������� ���������
        if self.ShowMessages:
            print "Power="+str(NewPower)		
        #������ ��������
        u=self.convertObject.ConvertWatts(NewPower)
        u = round(u,0)
        #print u
        u=long(u)
        #print u
        a = self.WriteStringToPort(self.make_string_2_set_power(u))
        #print self.GetPowerValue();
        # result=self.buffer2Power()
        # if result[0]:
            #self.CurrentPowerWatts=result[1]
        # else:
            # self.CurrentPowerWatts=0	
        return a
        
    def make_string_2_set_power(self,u):
        #string = '\x02'+ chr((u&long('ff00',16))>>8)+chr((u&long('ff',16)))
        string = chr(self.Address)+'\x02'+ chr((u&long('ff',16)))+chr((u&long('ff00',16))>>8)
        return string
        
    def SetCurrentPowerOFF(self,CurrentPower):
        self.CurrentPowerWatts=CurrentPower
        
    #��������� �������� ��������. �������� ������, ������ ���������� � ���������� ������	
    def SetPower(self, u, PowerInWatts=True):#If WattPercent=True, it means that power in Watts, else in Percents
        SerialPort = self.SerialPort
        
        self.CurrentPowerWatts=self.GetPower()
        
        if PowerInWatts:
            PowerEndPoint=float(u)
        else:
            PowerEndPoint=float(self.convertObject.ConvertPercentsToWatts(u))
            
        #������ ��������� 
        PowerEndPoint=self.CorrectionFactor*PowerEndPoint
        
        #��������� �� ���������� ������
        if PowerEndPoint>self.MaxPower:
            PowerEndPoint=self.MaxPower
            
        PowerCurrent=self.CurrentPowerWatts			
        
        if self.FastMode:
            PowerStep=self.FastModeStep;
        else:
            PowerStep=self.SlowModeStep;
            
        if PowerCurrent>PowerEndPoint:
            PowerStep=-PowerStep					
        
        while abs(PowerCurrent-PowerEndPoint)>abs(PowerStep):
            PowerCurrent=PowerCurrent+PowerStep	
            result=self.SetPowerWatts(PowerCurrent)
            if not result:
                print 'Error setting power',result[1]
                return result			
            time.sleep(self.PowerDelay)
            
        self.SetPowerWatts(PowerEndPoint)
            
        return (True,'')
    
    #������ ������ �� ���-����� � ����������� � �������� ��������
    def buffer2power(self):		
        #ticks=self.convertObject.MaxCounterValue-self.GetPowerValue()*100		
        ticks=float(self.convertObject.MaxCounterValue-self.GetPowerValue())		
        #print 'ticks=',ticks		
        time=ticks/self.convertObject.Freq/0.01#����� � ��������
        return self.convertObject.PowerInWatts(time*math.pi)
    
    def GetPower(self):		
        return self.buffer2power()
    
    def GetState(self):
        result=self.SerialPort.write(chr(self.Address)+'\x04\x00\x00',self.GetState)	
        if not result:
            raise 'GetState::Error write to port!'
        (flag,charFromPort)=self.SerialPort.read(4,self.GetState)
        #print charFromPort
        if not flag:
            raise 'GetState::Error read from port!'
        if len(charFromPort)<4:
            raise 'GetState::less than 4 bytes recieved!'			
        self.isPowerOn=ord(charFromPort[3])==1
        self.isOvenPowerOn=ord(charFromPort[2])==1
        #self.CurrentPowerWatts=result[1]
    
    #������ �������� �������� (��������) �� ���������������	
    def GetPowerValue(self):		
        result=self.SerialPort.write(chr(self.Address)+'\x03\x00\x00',self.GetPowerValue)	
        if not result:
            raise 'GetPowerValue::Error write to port!'
            
        (flag,charFromPort)=self.SerialPort.read(4,self.GetPowerValue)		
        if not flag:
            raise 'GetPowerValue::Error read from port!'
        if len(charFromPort)<4:
            raise 'GetPowerValue::less than 4 bytes recieved!'				
        #self.CurrentPowerWatts=result[1]
        return long(ord(charFromPort[3]))*256+ord(charFromPort[2])
        
    def WriteStringToPortBak(self,str):
        for i in range(len(str)):
            charToPort=str[i]
            self.SerialPort.write(charToPort, self.WriteStringToPort)
            (flag,charFromPort)=self.SerialPort.read(1,self.WriteStringToPort)
            #print charFromPort
            if not flag:
                raise 'Error occured when recieving data from heater port!'
            if charFromPort=='':
                raise 'No data are recieved from heater port!'
            if charToPort!=charFromPort:	
                raise 'Wrong data are recieved from heater port!'
        return True
        
    def WriteStringToPort(self,str):
        #print str
        self.SerialPort.write(str, self.WriteStringToPort)
        (flag,charFromPort)=self.SerialPort.read(len(str),self.WriteStringToPort)
        if not flag:
            raise 'Error occured when recieving data from heater port!'
        if charFromPort=='':
            raise 'No data are recieved from heater port!'
        # if str!=charFromPort:	
        # raise 'Wrong data are recieved from heater port!'		
        return True
                        
    def PowerOn(self):
        a = self.WriteStringToPort(chr(self.Address)+'\x01'+chr(120)+'\x01')	
        #isPowerOn=True;
        
    def PowerOff(self):
        a = self.WriteStringToPort(chr(self.Address)+'\x01\x00\x00')	
        #isPowerOn=False;

#������������ �������� 10000 ����		
class convert(object): #��������� ����� ��� ��������� ������� � �����
    def __init__(self):
        self.R=4.84 #�������������
        #self.Freq=7372800 #������� ������
        self.Freq= 6553600 #������� ������
        self.MaxCounterValue=2**16-1 #������������ ���������� ������ ��������
        self.U0=311.127#����������� �������� ���������� ����
        self.error = 0.000001
        self.t2=math.pi
        self.t1=0
        
    def Coef(self):#��������� ������������� ������� ����� � ����������� 
        C = self.MaxCounterValue/(self.Freq*0.01)
        return C
        
    def PowerInWatts(self,t):
        #t-����� � ��������
        P = 0.5*(self.U0**2)*(-math.cos(math.pi-t)*math.sin(math.pi-t)+math.pi-t)/(self.R*math.pi)
        return P
        
    def ConvertTimeToTacts(self,time):
        Tacts = (time*self.MaxCounterValue)/(self.Coef()*math.pi)
        return Tacts

    def ConvertPercentsToWatts(PowerInPercents):
        P = (PowerInPercents*self.PowerInWatts(0))/100
        return P
        
    def ConvertPercents(self, SetPowerInPercents):
        #t is the delay time  in radians 
        print "SetPowerInPercents="+str(SetPowerInPercents)
               
              
        TMaxRadian=self.Coef()*math.pi
        MinPowerInPercents=(self.PowerInWatts(TMaxRadian)/self.PowerInWatts(0))*100
        
        if SetPowerInPercents<MinPowerInPercents:
            SetPowerInPercents=MinPowerInPercents
            print "the value is replaced by"+str(SetPowerInPercents)
                              
        SetPowerInWatts = self.ConvertPercentsToWatts(SetPowerInPercents)
         
        t = self.Bisec(self.error,self.t1,self.t2,SetPowerInWatts)
        #x = self.ConvertTimeToTacts(t)
        x = self.MaxCounterValue-self.ConvertTimeToTacts(t)
        return x
    
        
    def ConvertWatts(self, SetPowerInWatts):#���������� ���������� ������ ����������� ��� ������� ����������
        #������ ��������
        #t is the delay time  in radians 
        #if self.ShowMessages:
        #	print "Power="+str(SetPowerInWatts)
             
        TMaxRadian=self.Coef()*math.pi
        MinPowerInWatts=self.PowerInWatts(TMaxRadian)
                
        if SetPowerInWatts<MinPowerInWatts: #���� �������� ������ ���������� ���������, ���������� �����������						
            return 0
        
        t = self.Bisec(self.error,self.t1,self.t2,SetPowerInWatts)		
        #x = self.ConvertTimeToTacts(t)
        x = self.MaxCounterValue-self.ConvertTimeToTacts(t)
        return x
       
    def Bisec(self,error,t1,t2,SetPowerInWatts):
        
        if abs(SetPowerInWatts-self.PowerInWatts(0))<1:
           return 0
        while 1:
            
            t=((t2-t1)/2)+t1
            Power = self.PowerInWatts(t)-SetPowerInWatts
            PP2 = (self.PowerInWatts(t)-SetPowerInWatts)*(self.PowerInWatts(t2)-SetPowerInWatts)
            PP1 = (self.PowerInWatts(t)-SetPowerInWatts)*(self.PowerInWatts(t1)-SetPowerInWatts)
                            
            if Power==0:
                break
            if abs(t2-t1)<error:
                break
            elif PP2<0:
                t1=t
            elif PP1<0:
                t2=t
        return t
