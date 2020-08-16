import time
import hashlib

class Stock:

	def __init__(self, brokerID, symbol, buyPrice, buyTimestamp, sellPrice = False, sellTimestamp = False):

		self.id = hashlib.md5(str(time.time()).encode()).hexdigest()
		self.brokerID = brokerID
		self.symbol = symbol
		self.buyPrice = buyPrice
		self.sellPrice = sellPrice
		self.buyTimestamp = buyTimestamp
		self.sellTimestamp = sellTimestamp