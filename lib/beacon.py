class Device(object):
    	def __init__(self, addr=None, rssi=None, counter= None, battery=None,temperature=None, raw=None, comment=None):
		self.addr = addr
		self.rssi = rssi
		self.counter = counter
		self.battery = battery
		self.temperature = temperature
		self.raw = raw
		self.comment = comment

class DeviceFilter(object):
    	def __init__(self, addr=None, rssi=None, counter= None, timestamp=None, rawMac=None):
		self.addr = addr
		self.rssi = rssi
		self.counter = counter
		self.timestamp = timestamp
		self.rawMac = rawMac

class DeviceBuzzer(object):
    	def __init__(self, addr=None, timestamp=None):
		self.addr = addr
		self.timestamp = timestamp

class DeviceReport(object):
    	def __init__(self, addr=None, timestamp=None):
		self.addr = addr
		self.timestamp = timestamp