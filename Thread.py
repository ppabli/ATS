import threading
import time


class Thread(threading.Thread):

	counter = 0

	def __init__(self, app, broker, *args, **kwargs):

		super(Thread, self).__init__(*args, **kwargs)
		self.id = Thread.counter
		self.timestamp = time.time()
		self.active = False
		self.broker = broker
		self.app = app

		Thread.counter += 1

	def run(self):

		self.active = True

		while self.active:

			self.app.checkCooldown(1, False)
			self.broker.trade()

			i = 0
			while not self.stopFlag and i <= 60:

				i += 1
				time.sleep(1)

	def stop(self):

		self.active = False