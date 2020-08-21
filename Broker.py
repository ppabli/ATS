import requests
import json
import pandas as pd
import time
import math
import os

import config
from Stock import Stock


class Broker:

	def __init__(self, symbol, money, stock = {}, log = {}, lastTradeTimestamp = 0, id = False):

		try:

			symbol = symbol.upper()

			url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey={config.API_KEY}"
			response = requests.get(url)
			data = response.json()[list(response.json().keys())[0]]

			if data == symbol:

				with open("brokers.json") as file:

					obj = json.load(file)
					counter = 0

					for key in list(obj["brokers"].keys()):

						if key.split("_")[0] == symbol:

							counter += 1

				self.id = id or f"{symbol}_{str(counter)}"
				self.symbol = symbol
				self.lastTradeTimestamp = lastTradeTimestamp

				self.money = float(money)
				self.stock = stock

				self.log = log

				self.dailyData = None
				self.generalData = None

				self.obtainGeneralData()

			else:

				raise Exception("Invalid symbol provided")

		except ValueError:

			print("Invalid data type provided")

	def obtainDailyData(self):

		dailyURL = f"https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={self.symbol}&interval=1min&apikey={config.API_KEY}&outputsize=full"

		dailyResponse = requests.get(dailyURL)

		dailyData = dailyResponse.json()[list(dailyResponse.json().keys())[1]]

		finalDailyData = []

		for value in dailyData.values():

			finalDailyData.append([value["1. open"], value["2. high"], value["3. low"], value["4. close"], value["5. volume"], None])

		dailyDF = pd.DataFrame(data = finalDailyData, columns = [

			"1. open",
			"2. high",
			"3. low",
			"4. close",
			"5. volume",
			"index"

		], dtype = float)

		dailyDF["index"] = list(dailyData.keys())
		dailyDF["index"] = pd.to_datetime(dailyDF["index"])
		dailyDF.set_index(dailyDF["index"], inplace = True)

		# print(len(dailyDF.loc[(dailyDF["index"].dt.month == 8) & (dailyDF["index"].dt.day == 4)]))

		self.dailyData = dailyDF

	def obtainGeneralData(self):

		generalURL = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={self.symbol}&apikey={config.API_KEY}&outputsize=full"

		generalResponse = requests.get(generalURL)

		generalData = generalResponse.json()[list(generalResponse.json().keys())[1]]

		finalGeneralData = []

		for value in generalData.values():

			finalGeneralData.append([value["1. open"], value["2. high"], value["3. low"], value["4. close"], value["5. volume"], None])

		generalDF = pd.DataFrame(data = finalGeneralData, columns = [

			"1. open",
			"2. high",
			"3. low",
			"4. close",
			"5. volume",
			"index"

		], dtype = float)

		generalDF["index"] = list(generalData.keys())
		generalDF["index"] = pd.to_datetime(generalDF["index"])
		generalDF.set_index(generalDF["index"], inplace = True)

		# print(len(generalDF.loc[(generalDF["index"].dt.month == 8) & (generalDF["index"].dt.day == 4)]))

		self.generalData = generalDF

	def addBroker(self):

		with open("brokers.json") as file:

			obj = json.load(file)

			if not self.id in obj["brokers"]:

				obj["brokers"][self.id] = {}

				obj["brokers"][self.id]["data"] = {

					"id": self.id,
					"symbol": self.symbol,
					"lastTradeTimestamp": self.lastTradeTimestamp

				}

				obj["brokers"][self.id]["wallet"] = {

					"money": self.money,
					"stock": self.stock

				}

				obj["brokers"][self.id]["log"] = self.log

				obj["lastUpdateTimestamp"] = time.time()

				with open("brokers.json", "w", encoding = "utf8") as file:

					json.dump(obj, file, indent = "\t")

					print("Broker added correctly")

			else:

				print("Broker already exists")

	def removeBroker(self):

		with open("brokers.json") as file:

			obj = json.load(file)

			if self.id in obj["brokers"]:

				del obj["brokers"][self.id]
				obj["lastUpdateTimestamp"] = time.time()

				with open("brokers.json", "w", encoding = "utf8") as file:

					json.dump(obj, file, indent = "\t")

					print("Broker removed correctly")

			else:

				print("Broker do not exists")

	def trade(self):

		self.lastTradeTimestamp = time.time()

		self.obtainDailyData()

		self.sell()
		self.buy()

	def buy(self):

		actualPrice = self.dailyData["2. high"][0]

		dailyMean = self.dailyData["2. high"].mean()
		generalMean = self.generalData["2. high"].mean()

		if actualPrice < dailyMean:

			amount = math.trunc(self.money / actualPrice)
			self.money -= amount * actualPrice

			for x in range(0, amount):

				stock = Stock(self.id, self.symbol, actualPrice, time.time())

				self.stock[stock.id] = stock
				self.log[stock.id] = stock

	def sell(self):

		if self.stock:

			stockCopy = self.stock.copy()

			for key, stock in stockCopy.items():

				stockPrice = stock.buyPrice

				actualPrice = self.dailyData["2. high"][0]

				dailyMean = self.dailyData["2. high"].mean()
				generalMean = self.generalData["2. high"].mean()

				if actualPrice > stockPrice:

					stock.sellPrice = actualPrice
					stock.sellTimestamp = time.time()

					self.money += actualPrice
					del self.stock[stock.id]
					self.log[stock.id] = stock