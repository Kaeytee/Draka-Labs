import subprocess
import sys
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time
import os

##This codebase initialises the hot reload for the application it is basically like running the main.py naa 

class RestartHandler(FileSystemEventHandler):
	def __init__(self, command):
		self.command = command
		self.process = None
		self.start_server ()
		
	def start_server(self):
		if self.process:
			self.process.terminate()
			self.process.wait()
		self.process = subprocess.Popen([sys.executable, "main.py"])

	def on_any_event(self, event):
		if event.src_path.endswith(".py"):
			print(f"Detected change in {event.src_path}, restarting server...")
			self.start_server()

if __name__ == "__main__":
	path=os.path.dirname(os.path.abspath(__file__))
	event_handler= RestartHandler([sys.executable, "main.py"])
	observer = Observer()
	observer.schedule(event_handler, path=path, recursive=True)
	observer.start()
	print("Watching for changes... Press Ctrl+C to exit.")
	try:
		while True:
			time.sleep(1)
	except KeyboardInterrupt:
		observer.stop()
	observer.join()
	if event_handler.process:
		event_handler.process.terminate()
		