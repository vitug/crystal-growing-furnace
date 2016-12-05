# -*- coding: cp1251 -*-
from TOwen import trm251
from TController import MySerial as Serial
from TController import Heater;
import thread as threadModule
import time
import wx
import wx.lib.newevent
import sys
import traceback
from datetime import datetime

#создаем последовательный порт
try:
    #COM = Serial.ComPort(2, 9600, timeout=.3)#открываем COM1
    COM = Serial.ComPort(0, 9600, timeout=.3)#открываем COM1
except:
    raise Exception('Error openning port!')

# This creates a new Event class and a EVT binder function
(UpdateBarEvent, EVT_UPDATE_INFO) = wx.lib.newevent.NewEvent()

#чтение данных происходит в этом потоке
class PidRegulatorThread:
    def __init__(self, win):
        self.win = win
        self.Temp = 0.0
        self.Power = 0.0
        self.running=False
        self.keepGoing = False
        self.manualMode = False
        self.manualPower = 0.0
        self.pidReg=trm251.TRM251(COM,16);
        #self.pidReg=trm251.TRM251(None,16);
        self.heater = Heater.Heater(COM,0)
        #self.heater.ShowMessages=True    
        self.fileName = ''
        
    def Start(self):        
        if not self.running:
            self.keepGoing = self.running = True
            threadModule.start_new_thread(self.Run, ())

    def Stop(self):
        self.keepGoing = False

    def IsRunning(self):
        return self.running
        
    def WriteLog(self, Time):
        log = open(self.fileName,'a')
        log.write('{}\t{}\t{}\n'.format(Time,self.Temp,self.Power))        
        log.close()
        log = open('graph.dat','a')
        log.write('{}\t{}\n'.format(Time,self.Temp))        
        log.close()        
        
    def InitLog(self):        
        self.fileName='log\\regulation_log_'+time.strftime('%Y%m%d %H%M%S')+'.dat'
        log = open(self.fileName,'w')
        log.close()
        log = open('graph.dat','w')
        log.close()                    
        
    def MakeOverCurrent(self):
        self.heater.CorrectionFactor = 0.855
        self.heater.SetPower(10000)
        time.sleep(.1)
        self.heater.CorrectionFactor = 0.85
        self.heater.SetPower(10000)        
        self.running = False
       
    def Run(self):        
        self.Temp=0;
        self.Power=0;        
        state=1
        counter = counterGetTemp = 10
        lastPower = 0;
        self.heater.FastMode = True
        currentPower=0
        error=''
        self.InitLog()
        self.heater.PowerOn()
        StartTime=time.time()
        #self.MakeOverCurrent()
        while self.keepGoing:
            try:                
                if counter==counterGetTemp:#читаем температуру только один через 10
                    self.Temp=self.pidReg.GetTemperature()
                    counter=0
                    #print '{}:: temp: {}'.format(datetime.now(),self.Temp);                    
                else:
                    counter=counter+1
                if state==1 or state==4:
                    if not self.manualMode:
                        self.Power = self.pidReg.GetPower()
                    else:
                        #ручной режим
                        self.Power = self.manualPower
                else:
                    self.Power=0;
                #if  not self.Power==lastPower:   
                self.heater.SetPower(self.Power*10000)
                currentPower=self.heater.GetPower()/100
                lastPower=self.Power
                #пишем лог
                CurrentTime=time.time()
                FromStartTime=CurrentTime-StartTime                
                self.WriteLog(FromStartTime)
                #print '{}:: power: {} '.format(datetime.now(),self.Power);                    
            except:
                error='Ошибка в цикле регулирования!'
                test_file=open('pid_log.txt','a')
                test_file.write('Error information '+time.asctime()+'\r')
                traceback.print_exc(None,test_file)
                test_file.close()  
            if self.manualMode: 
                modeName = 'ручн.'
            else:
                modeName = 'авт.'    
            evt = UpdateBarEvent(Power = self.Power, Temp = self.Temp, currPower=currentPower, Error=error, ModeName = modeName)
            wx.PostEvent(self.win, evt)
            if not self.manualMode:
                time.sleep(.1)
            else:
                time.sleep(5)
            error=''
        self.heater.FastMode = False    
        self.running = False
        
    def PowerOff(self):       
        self.heater.SetPower(0)        
        self.heater.PowerOff()


class MyFrame(wx.Frame):
    """
    This is MyFrame.  It just shows a few controls on a wxPanel,
    and has a simple menu.
    """
    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, -1, title,
                          pos=(150, 150), size=(350, 400))

        # Create the menubar
        menuBar = wx.MenuBar()

        # and a menu 
        menu = wx.Menu()

        id_poweroff=1
        # add an item to the menu, using \tKeyName automatically
        # creates an accelerator, the third param is some help text
        # that will show up in the statusbar
        menu.Append(id_poweroff, "Вы&ключить печь\tAlt-Z", "Занулить мощность на нагревателях")
        menu.Append(wx.ID_EXIT, "В&ыход\tAlt-X", "Выйти из программы регулирования")

        # bind the menu event to an event handler
        self.Bind(wx.EVT_MENU, self.OnPowerOff, id=id_poweroff)
        self.Bind(wx.EVT_MENU, self.OnTimeToClose, id=wx.ID_EXIT)	

        # and put the menu on the menubar
        menuBar.Append(menu, "&Файл")
        self.SetMenuBar(menuBar)

        self.CreateStatusBar()
        

        # Now create the Panel to put the other controls on.
        panel = wx.Panel(self)

        # and a few controls
        textTemp = wx.StaticText(panel, -1, 'Температура:0')
        textTemp.SetFont(wx.Font(14, wx.SWISS, wx.NORMAL, wx.BOLD))
        textTemp.SetSize(textTemp.GetBestSize())
        self.Temp=textTemp;
        textPower = wx.StaticText(panel, -1, 'Мощность:0')
        textPower.SetFont(wx.Font(14, wx.SWISS, wx.NORMAL, wx.BOLD))
        textPower.SetSize(textPower.GetBestSize())
        self.Power=textPower;
        textTime = wx.StaticText(panel, -1, '')
        textTime.SetFont(wx.Font(14, wx.SWISS, wx.NORMAL, wx.BOLD))
        textTime.SetSize(textTime.GetBestSize())
        self.Time=textTime;
        
        self.btnStart = wx.Button(panel, -1, "Старт")
        self.btnStop = wx.Button(panel, -1, "Остановить регулирование")
        self.btnPowerOff = wx.Button(panel, -1, "Выключить питание")
        self.btnStop.Disable()

        # bind the button events to handlers
        self.Bind(wx.EVT_BUTTON, self.OnStart, self.btnStart)
        self.Bind(wx.EVT_BUTTON, self.OnStop, self.btnStop)
        self.Bind(wx.EVT_BUTTON, self.OnPowerOff, self.btnPowerOff)
        
        self.thread=PidRegulatorThread(self)
        
        self.Bind(EVT_UPDATE_INFO, self.OnUpdate)

        self.slider = wx.Slider(
            panel, 100, 25, 1, 100, (10, 280), (250, -1), 
            wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS 
            )

        self.slider.SetTickFreq(5, 1)
        
        power=self.GetCurrentPower()
        self.slider.SetValue(power)        

        self.slider.Bind(wx.EVT_SCROLL_CHANGED, self.onSliderChanged)        
        
        # Use a sizer to layout the controls, stacked vertically and with
        # a 10 pixel border around each
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(textTemp, 0, wx.ALL, 10)
        sizer.Add(textPower, 0, wx.ALL, 10)
        sizer.Add(textTime, 0, wx.ALL, 10)
        #panel.SetSizer(sizer)

        #sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.btnStart, 0, wx.ALL, 10)
        sizer.Add(self.btnStop, 0, wx.ALL, 10)
        sizer.Add(self.btnPowerOff, 0, wx.ALL, 10)
        #sizer.Add(self.slider, 0, wx.ALL, 10)
        panel.SetSizer(sizer)
        panel.Layout()
        
        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow) 
        self.OnStart(wx.EVT_CLOSE)
    
    def GetCurrentPower(self):
        power=self.thread.heater.GetPower()/100
        return power
        
    def onSliderChanged(self, evt):
        #self.log.write('changed: %d' % evt.EventObject.GetValue())
        print 'changed: %d' % evt.EventObject.GetValue()
        self.thread.Stop()
        self.WaitForStopping()
        newPower = evt.EventObject.GetValue() * 100 #получили мощность в ваттах
        self.thread.heater.SetPower(newPower)
        power = self.GetCurrentPower() #мощность в процентах
        self.slider.SetValue(power)
        self.thread.manualMode = True
        self.thread.manualPower = float(newPower) / 10000
        self.thread.Start()
        print power
        
    def OnStart(self, evt):       
        #print "Starting thread!"
        self.btnStart.SetLabel('Процесс регулирования запущен!');
        self.btnStart.SetSize(self.btnStart.GetBestSize())        
        self.btnStop.Enable()
        self.btnStart.Disable()
        self.slider.Disable()
        self.thread.manualMode = False
        self.thread.manualPower = 0
        self.thread.Start()

    def OnStop(self, evt):
        #print "Stopping thread!"
        self.btnStart.SetLabel('Старт');
        self.btnStart.SetSize(self.btnStart.GetBestSize())                
        self.btnStart.Enable()
        self.btnStop.Disable()
        self.slider.Enable()
        self.thread.Stop()
        self.WaitForStopping()
        
    def OnUpdate(self, evt):
        #self.graph.SetValue(evt.barNum, evt.value)
        #self.graph.Refresh(False)        
        self.Temp.SetLabel('Температура: {0:.2f}'.format(evt.Temp))
        self.Power.SetLabel('Мощность: {0:.2f}({1})'.format(evt.Power, evt.ModeName))
        if evt.Error=='':
            self.Time.SetLabel('{}'.format(datetime.now()))
        else:
            self.Time.SetLabel(evt.Error)
        self.slider.SetValue(evt.currPower)
        pass

    def WaitForStopping(self):
        running = True
        while running:
            running = self.thread.IsRunning()
            time.sleep(0.1)

    def OnCloseWindow(self, evt):
        busy = wx.BusyInfo("Останавливаем процесс регулирования...")
        wx.Yield()
        self.thread.Stop()
        self.WaitForStopping()
        self.Destroy()  
        
    def OnTimeToClose(self, evt):
        print "See you later!"
        self.Close() 

    def OnPowerOff(self,evt):       
        busy = wx.BusyInfo("Останавливаем процесс регулирования...")
        wx.Yield()
        self.thread.Stop()
        running = True
        while running:
            running = self.thread.IsRunning()
            time.sleep(0.1)
        busy = wx.BusyInfo("Снижаем мощность до нуля...")
        wx.Yield()
        self.thread.PowerOff()
        power = self.GetCurrentPower() #мощность в процентах
        self.slider.SetValue(power)
	

class MyApp(wx.App):
    def OnInit(self):
        # Redirect stdou/stderr
        sys.stderr = open("wx_stderr.log", "w")
        sys.stdout = open("wx_stdout.log", "w")

        
        # Do the inits      
        frame = MyFrame(None, "Регулятор")
        self.SetTopWindow(frame)
        frame.Show(True)
	#self.OnStart('qq'):       
        return True
        

app = MyApp(redirect=True,filename="wxlogfile.log")
#app = MyApp(redirect=True)
#app = MyApp()
app.MainLoop()

        