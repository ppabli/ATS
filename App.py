import os
import json
import time
import sys
import threading

from Broker import Broker
from Thread import Thread
from Stock import Stock

import config


class App:

	def __init__(self):

		self.brokers = []
		self.threads = []

		self.cooldownCalls = 0
		self.cooldownTimestamp = time.time()

		if not os.path.exists("brokers.json"):

			with open("brokers.json", "w") as file:

				data = {}
				data["lastUpdateTimestamp"] = ""
				data["brokers"] = {}

				json.dump(data, file, indent = "\t")

		else:

			with open("brokers.json") as file:

				obj = json.load(file)

				if obj["brokers"]:

					print("Start loading brokers")

					for broker in obj["brokers"].values():

						self.checkCooldown(2)

						print(f"Loading broker: {broker['data']['symbol']} | {broker['data']['id']}")

						stockList = {}

						for key, value in broker["wallet"]["stock"].items():

							newStock = Stock(value["brokerID"], value["symbol"], value["buyPrice"], value["buyTimestamp"], id = value["id"])
							stockList[newStock.id] = (newStock)

						logList = {}

						for key, value in broker["log"].items():

							newStock = Stock(value["brokerID"], value["symbol"], value["buyPrice"], value["buyTimestamp"], value["sellPrice"], value["sellTimestamp"], value["id"])
							logList[newStock.id] = newStock

						b = Broker(broker["data"]["symbol"], broker["wallet"]["money"], stockList, logList, broker["data"]["lastTradeTimestamp"], broker["data"]["id"])

						self.brokers.append(b)

						t = Thread(self, b)

						self.threads.append(t)

					print("Finish loading brokers")

		self.options = {

			-1: {

				"description": "Exit"

			},
			0: {

				"description": "Display brokers",
				"function": self.displayBrokers,
				"cost": 0

			},
			1: {

				"description": "Add broker",
				"function": self.addBroker,
				"cost": 2

			},
			2: {

				"description": "Delete broker",
				"function": self.removeBroker,
				"cost": 0

			},
			3: {

				"description": "Start thread",
				"function": self.startThread,
				"cost": 0

			},
			4: {

				"description": "Stop thread",
				"function": self.stopThread,
				"cost": 0

			},
			5: {

				"description": "Start track",
				"function": self.startTrack,
				"cost": 0

			},
			6: {

				"description": "Stop track",
				"function": self.stopTrack,
				"cost": 0

			}

		}

	def run(self):

		while True:

			try:

				self.displayOptions()
				option = int(input("Enter option number: "))

				if option == -1:

					self.stopTrack()
					self.updateFile()
					break;

				else:

					if option in self.options.keys():

						self.checkCooldown(self.options[option]["cost"])

						self.options[option]["function"]()

					else:

						print("Invalid option")

			except:

				print("Invalid option")

	def checkCooldown(self, newCalls, animation = True):

		cooldown = False

		if self.cooldownCalls + newCalls > config.API_CALLS_MINUTE and time.time() - self.cooldownTimestamp < 60:

			cooldown = True
			totalTime = config.API_COOLDOWN_MINUTE - int(time.time() - self.cooldownTimestamp)

		elif self.cooldownCalls + newCalls > config.API_CALLS_HOUR and time.time() - self.cooldownTimestamp < 3600:

			cooldown = True
			totalTime = config.API_COOLDOWN_HOUR - int(time.time() - self.cooldownTimestamp)

		if cooldown:

			if animation:

				self.animation(totalTime, "Cooldown", eta = True, percentage = True)

			else:

				time.sleep(totalTime)

			self.cooldownCalls = 0
			self.cooldownTimestamp = time.time()

			self.checkCooldown(newCalls)

		else:

			self.cooldownCalls += newCalls

	def animation(self, duration = 60, startText = False, finalText = False, finishText = False, eta = False, etaText = False, percentage = False, percentageText = False):

		columns, rows = os.get_terminal_size()

		duration = round(duration * 1.00, 2)

		bar = "[]"

		ticks = columns - len(bar) - 2 #2 due to bar final space and -1 due to print whitespace

		if startText:

			ticks -= len(startText) + 1

		if finalText:

			ticks -= len(finalText) + 1

		if eta:

			if etaText:

				ticks -= len(etaText) + 2 + len(str(duration)) + 1

			else:

				ticks -= 5 + 2 + len(str(duration)) + 1

		if percentage:

			if percentageText:

				ticks -= len(percentageText) + 1 + 6

			else:

				ticks -= 6

		tickTime = duration / ticks

		bar = bar[0] + "_" * ticks + bar[-1]

		for x in range(1, ticks + 1):

			elements = []

			if startText:

				elements.append(startText)

			bar = bar[:x] + "+" + bar[x + 1:]
			elements.append(bar)

			if finalText:

				elements.append(finalText)

			if eta:

				if etaText:

					newText = f"{etaText} {round(duration - x * tickTime, 1)}s"
					elements.append(newText)

				else:

					newText = f"Time: {round(duration - x * tickTime, 1)}s"
					elements.append(newText)

			if percentage:

				if percentageText:

					newText = f"{percentageText} {round(x / ticks * 100, 1)}%"
					elements.append(newText)

				else:

					newText = f"{round(x / ticks * 100, 1)}%"
					elements.append(newText)

			print(" ".join(elements), end = "\r")

			time.sleep(tickTime)

		if finishText:

			print(f"\n{finishText}")

		else:

			print()

	def displayOptions(self):

		for option in self.options:

			print(f"{option if option == -1 else ' ' + str(option)} - {self.options[option]['description']}")

	def displayBrokers(self):

		print(f"Index\t\tB ID\t\tB Sym\t\tB Mon\t\tB St\t\tB LT\t\tT ID\t\tT Act\t\tT Tim")

		for index, (broker, thread) in enumerate(zip(list(self.brokers), list(self.threads))):

			print(f"{index}\t\t{broker.id}\t\t{broker.symbol}\t\t{round(broker.money, 2)}\t\t{len(broker.stock)}\t\t{int(broker.lastTradeTimestamp)}\t{thread.id}\t\t{thread.active}\t\t{int(thread.timestamp)}")

	def addBroker(self):

		try:

			symbol = input("Enter the symbol: ")
			money = float(input("Enter money: "))

			newBroker = Broker(symbol, money)
			newBroker.addBroker()

			self.brokers.append(newBroker)

			t = Thread(self, newBroker)

			self.threads.append(t)

		except ValueError:

			print("Invalid data type provided")

	def removeBroker(self):

		self.displayBrokers()

		try:

			index = int(input("Enter the broker index: "))

			if self.brokers[index]:

				broker = self.brokers[index]

				if self.threads[index].active:

					self.threads[index].stop()
					self.threads[index].join()

				broker.removeBroker();
				del self.brokers[index]
				del self.threads[index]

			else:

				print("Invalid index")

		except ValueError:

			print("Invalid data type provided")

	def updateFile(self):

		with open("brokers.json") as file:

			obj = json.load(file)

			for broker in self.brokers:

				stockList = {}

				for key, value in broker.stock.items():

					stockList[key] = value.__dict__

				logList = {}

				for key, value in broker.log.items():

					logList[key] = value.__dict__

				obj["brokers"][broker.id]["data"]["lastTradeTimestamp"] = broker.lastTradeTimestamp
				obj["brokers"][broker.id]["wallet"]["money"] = broker.money
				obj["brokers"][broker.id]["wallet"]["stock"] = stockList
				obj["brokers"][broker.id]["log"] = logList

			with open("brokers.json", "w", encoding = "utf8") as file:

				json.dump(obj, file, indent = "\t")

	def startThread(self):

		self.displayBrokers()

		try:

			index = int(input("Enter the broker index: "))

			self.startTrack(index)

		except ValueError:

			print("Invalid data type provided")

	def stopThread(self):

		self.displayBrokers()

		try:

			index = int(input("Enter the broker index: "))

			self.stopTrack(index)

		except ValueError:

			print("Invalid data type provided")

	def startTrack(self, index = None):

		if index != None:

			if self.threads[index]:

				if not self.threads[index].active:

					self.threads[index].start()

					print("Broker thread correctly started")

				else:

					print("Broker thread already started")

			else:

				print("Invalid index")

		else:

			for thread in self.threads:

				if not thread.active:

					thread.start()

					print(f"{thread.broker.id} thread activated")

	def stopTrack(self, index = None):

		if self.threads:

			if index != None:

				if self.threads[index]:

					if self.threads[index].active:

						self.threads[index].stop()
						self.threads[index].join()

						print("Broker thread correctly stopped")

					else:

						print("Broker thread already stopped")

				else:

					print("Invalid index")

			else:

				for thread in self.threads:

					if thread.active:

						thread.stop()
						thread.join()

						print(f"{thread.broker.id} thread stopped")