'''
Based on the original TW-700 plugin by Tom Wilson.
'''

eg.RegisterPlugin(
    name = "Epson TW-700 Projector",
    author = "Tom Wilson",
    version = "0.1.0",
    kind = "external",
    guid = "{f6cfb453-416b-4276-92ac-c58ffe98972b}",
    url = "",
    description = (''),
    canMultiLoad = True,
    createMacrosOnAdd = True,
)


# Now we import some other things we will need later
import new
import thread

# Define commands
# (name, title, description (same as title if None), command)
commandsList = (
(
(
    'Power',
    (
        ('Power On', 'Power on', None, 'PWR ON'),
        ('Power Off', 'Power off', None, 'PWR OFF'),
    )
),
(
    'Inputs',
    (
        ('Component', 'Component', None, 'SOURCE 10'),
        ('PC', 'PC', None, 'SOURCE 20'),
        ('HDMI', 'HDMI', None, 'SOURCE 30'),
    )
),
)
)

class EpsonTW700SerialAction(eg.ActionClass):
    
    def __call__(self):
        self.plugin.sendCommand(self.serialcmd)



class EpsonTW700SerialsetVolumeAbsolute(eg.ActionWithStringParameter):
    name='Set absolute volume'
    description='Sets the absolute volume'

    def __call__(self, volume):
        return self.plugin.setVolume(volume, False)

    def GetLabel(self, volume):
        return "Set Absolute Volume to %d" % volume
        
    def Configure(self, volume=-40):
        panel = eg.ConfigPanel(self)
        valueCtrl = panel.SpinIntCtrl(volume, min=-80.5, max=16.5)
        panel.AddLine("Set absolute volume to", valueCtrl)
        while panel.Affirmed():
            panel.SetResult(valueCtrl.GetValue())



class EpsonTW700SerialsetVolumeRelative(eg.ActionWithStringParameter):
    name='Set relative volume'
    description='Sets the relative volume'

    def __call__(self, volume):
        return self.plugin.setVolume(volume, True)

    def GetLabel(self, volume):
        return "Set Relative Volume to %d" % volume
        
    def Configure(self, volume=0):
        panel = eg.ConfigPanel(self)
        valueCtrl = panel.SpinIntCtrl(volume, min=-80.5, max=16.5)
        panel.AddLine("Set relative volume to", valueCtrl)
        while panel.Affirmed():
            panel.SetResult(valueCtrl.GetValue())



class EpsonTW700Serial(eg.PluginClass):
    def __init__(self):
        self.serial = None
        self.response = None

        for groupname, list in commandsList:
            group = self.AddGroup(groupname)
            for classname, title, desc, serial in list:
                if desc is None:
                    desc = title
                clsAttributes = dict(name=title, description=desc, serialcmd=serial)
                cls = new.classobj(classname, (EpsonTW700SerialAction,), clsAttributes)
                group.AddAction(cls)

            if (groupname == 'Volume'):
                group.AddAction(EpsonTW700SerialsetVolumeAbsolute)
                group.AddAction(EpsonTW700SerialsetVolumeRelative)


    def sendCommandSerial(self, cmd):
        if self.serial is None:
            return True

        # Send command
        cmd += '\r'
        self.serial.write(cmd)

        return True


    # Serial port reader
    def reader(self):
        line=""
        while self.readerkiller is False:
            ch=self.serial.read()
            if ch=='\r':
                continue;
            if ch=='\n':
                if line != "":
                    self.parseLine(line)
                    self.TriggerEvent(line)
                    line=""
            else:
                line+=ch

    def parseLine(self, line):
        if line.startswith("@MAIN:VOL="):
            self.volume = float(line.split("=")[1])
            print "The volume is now: %f" % self.volume

    def getResponseFloat(self):
        return float(self.response)


    def getResponseInt(self):
        self.PrintError(self.response)
        if (self.response[0] == '-' or self.response[0] == '+'):
            if not self.response[1:].isdigit():
                self.PrintError("Bad response")
                return None

        elif not self.response.isdigit():
            self.PrintError("Bad response")
            return None

        return int(self.response)


    def sendCommand(self, serialcmd):
        result = self.sendCommandSerial(serialcmd)
        return result


    def setVolume(self, volume, relative):

        if relative and self.volume is None:
            # can't set the relative volume if we don't know the current state...
            return

        if relative:
            volume = self.volume + volume

        if volume > 16.5:
            volume = 10
        elif volume < -80.5:
            volume = -80.5
        
        command = "@MAIN:VOL=%.1f" % (volume)
        self.sendCommandSerial(command)
        return volume


    def getInitialState(self):
        self.sendCommandSerial("@MAIN:VOL=?")


    def __start__(self, port=0):
        try:
            self.serial = eg.SerialPort(port)
            self.serial.baudrate = 9600
            self.serial.timeout = 0.5
            self.serial.setDTR(1)
            self.serial.setRTS(1)
            self.readerkiller = False
            thread.start_new_thread(self.reader,())

            self.getInitialState()
        except:
            self.PrintError("Unable to open serial port")


    def __stop__(self):
        self.readerkiller = True
        if self.serial is not None:
            self.serial.close()
            self.serial = None


    def Configure(self, port=0):
        portCtrl = None

        panel = eg.ConfigPanel(self)
        portCtrl = panel.SerialPortChoice(port)
        panel.AddLine("Port:", portCtrl)

        while panel.Affirmed():
            panel.SetResult(portCtrl.GetValue())
        

