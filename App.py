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
		self.threads = list()

		self.cooldownCalls = 0
		self.cooldownTimestamp = time.time()

		if not os.path.exists("brokers.json"):

			with open('brokers.json', 'w') as file:

				data = {}
				data["lastUpdateTimestamp"] = ""
				data["brokers"] = {}

				json.dump(data, file, indent = "\t")

		else:

			print("Start loading brokers")

			with open('brokers.json') as file:

				obj = json.load(file)

				for broker in obj['brokers'].values():

					self.checkCooldown(3)

					print(f"Loading broker: {broker['data']['symbol']} | {broker['data']['id']}")

					stock = []

					for x, index in enumerate(broker["wallet"]["stock"]):

						newStock = Stock(broker["wallet"]["stock"][index]["brokerID"], broker["wallet"]["stock"][index]["symbol"], broker["wallet"]["stock"][index]["buyPrice"], broker["wallet"]["stock"][index]["buyTimestamp"])
						stock.append(newStock)

					log = []

					for x, index in enumerate(broker["log"]):

						newStock = Stock(broker["wallet"]["stock"][index]["brokerID"], broker["wallet"]["stock"][index]["symbol"], broker["wallet"]["stock"][index]["buyPrice"], broker["wallet"]["stock"][index]["buyTimestamp"], broker["wallet"]["stock"][index]["sellPrice"] or False, broker["wallet"]["stock"][index]["sellTimestamp"] or False)
						log.append(newStock)

					b = Broker(broker["data"]["symbol"], broker["wallet"]["money"], stock, log, broker["data"]["id"])

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
				"cost": 3

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

			print(' '.join(elements), end = "\r")

			time.sleep(tickTime)

		if finishText:

			print(f"\n{finishText}")

		else:

			print()

	def displayOptions(self):

		for option in self.options:

			print(f'{option} - {self.options[option]["description"]}')

	def displayBrokers(self):

		print(f"Index{' ' * (12 - len('Index'))}B ID{' ' * (12 - len('B ID'))}B Symbol{' ' * (12 - len('B Symbol'))}B Money{' ' * (12 - len('B Money'))}B Stock{' ' * (12 - len('B Stock'))}T ID{' ' * (12 - len('T ID'))}T Active{' ' * (12 - len('T Active'))}T Time{' ' * (12 - len('T Time'))}")

		for index, (broker, thread) in enumerate(zip(list(self.brokers), list(self.threads))):

			print(f"{index}\t{broker.id}\t{broker.symbol}\t{int(broker.money)}\t{len(broker.stock)}\t{thread.id}\t{thread.active}\t{int(thread.timestamp)}")

	def addBroker(self):

		try:

			symbol = input("Enter the symbol: ")
			money = float(input("Enter money: "))

			newBroker = Broker(symbol, money)
			newBroker.addBroker()

			self.brokers.append(newBroker)

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
				del self.broker[index]

				print("Broker correctly removed")

			else:

				print("Invalid index")

		except ValueError:

			print("Invalid data type provided")

	def startThread(self):

		self.displayBrokers()

		try:

			index = int(input("Enter the broker index: "))

			if self.threads[index]:

				if not self.threads[index].active:

					print("Broker thread correctly started")

				else:

					print("Broker thread already started")

			else:

				print("Invalid index")

		except ValueError:

			print("Invalid data type provided")

	def stopThread(self):

		self.displayBrokers()

		try:

			index = int(input("Enter the broker index: "))

			if self.threads[index]:

				if self.threads[index].active:

					print("Broker thread correctly stopped")

				else:

					print("Broker thread already stopped")

			else:

				print("Invalid index")

		except ValueError:

			print("Invalid data type provided")

	def startTrack(self):

		for thread in self.threads:

			thread.start()
			print(f"{thread.broker.id} thread activated")

	def stopTrack(self):

		if self.threads:

			for thread in self.threads:

				if thread.active:

					thread.stop()
					thread.join()
					print(f"{thread.broker.id} thread stopped")