import time

class Stock:

	counter = 0

	def __init__(self, brokerID, symbol, buyPrice, buyTimestamp, sellPrice = False, sellTimestamp = False, id = False):

		self.id = id or Stock.counter

		self.brokerID = brokerID

		self.symbol = symbol

		self.buyPrice = buyPrice
		self.buyTimestamp = buyTimestamp

		self.sellPrice = sellPrice
		self.sellTimestamp = sellTimestamp

		Stock.counter += 1