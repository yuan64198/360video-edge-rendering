from server import *
import threading
from multiprocessing import Process

def main():
	#mode: 1=CR 2=TR 4=VPR
	for i in range(30):
		p = Server("140.114.89.208", 20000+i)
		p.start()
	for i in range(30):
		p.join()

if __name__ == "__main__":
	main()
