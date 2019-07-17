from __future__ import print_function # WalabotAPI works on both Python 2 an 3.
from sys import platform
from os import system
from imp import load_source
from os.path import join
from optparse import OptionParser
from threading import Timer
from threading import Thread
import scipy.io
import time

import atexit
import sys

if platform == 'win32':
	modulePath = join('C:/', 'Program Files', 'Walabot', 'WalabotSDK',
	'python', 'WalabotAPI.py')
elif platform.startswith('linux'):
	modulePath = join('/usr', 'share', 'walabot', 'python', 'WalabotAPI.py') 
wlbt = load_source('WalabotAPI', modulePath)
wlbt.Init()

def PrintSensorTargets(targets,confidence):
	system('cls' if platform == 'win32' else 'clear')
	if targets:
		for i, target in enumerate(targets):
			print(('Target #{}:\ntype: {}\nangleDeg: {}\nx: {}\ny: {}\nz: {}'+
			'\nwidth: {}\namplitude: {}\nconfidence: {}\n').format(i + 1, target.type,
			target.angleDeg, target.xPosCm, target.yPosCm, target.zPosCm,
			target.widthCm, target.amplitude,confidence))
	else:
		print('No Target Detected')
		
def record(fileName):
	# wlbt.SetArenaX - input parameters
	xArenaMin, xArenaMax, xArenaRes = -1, 1, 0.5
	# wlbt.SetArenaY - input parameters
	yArenaMin, yArenaMax, yArenaRes = -1, 1, 0.5
	# wlbt.SetArenaZ - input parameters
	zArenaMin, zArenaMax, zArenaRes = 15, 20, 0.5
	# Initializes walabot lib
	wlbt.Initialize()
	# 1) Connects: Establish communication with walabot.
	wlbt.ConnectAny()
	# 2) Configure: Set scan profile and arena
	# Set Profile - to Short-range.
	wlbt.SetProfile(wlbt.PROF_SHORT_RANGE_IMAGING)
	# Set arena by Cartesian coordinates, with arena resolution
	wlbt.SetArenaX(xArenaMin, xArenaMax, xArenaRes)
	wlbt.SetArenaY(yArenaMin, yArenaMax, yArenaRes)
	wlbt.SetArenaZ(zArenaMin, zArenaMax, zArenaRes)
	#SetAdvancedParameter(PARAM_DIELECTRIC_CONSTANT,value) r = 1-30 epsilon*r
	#PARAM_CONFIDENCE_FACTOR
	#
	# Walabot filtering disable
	# FILTER_TYPE_DERIVATIVE: Dynamic-imaging filter for the specific frequencies typical of breathing.
	#FILTER_TYPE_MTI: Moving Target Identification: standard dynamic-imaging filter:
	wlbt.SetDynamicImageFilter(wlbt.FILTER_TYPE_NONE)
	# 3) Start: Start the system in preparation for scanning.
	wlbt.Start()
	# calibrates scanning to ignore or reduce the signals
	wlbt.StartCalibration()
	while wlbt.GetStatus()[0] == wlbt.STATUS_CALIBRATING:
		wlbt.Trigger()

	

	global seconds
	seconds = 0
	def printTime():
		global seconds
		global t0
		seconds += 1
		print(('Time (seconds): {}').format(seconds))
		t0 = Timer(1, printTime)
		t0.start()

	t0 = Timer(1, printTime)
	startTime = None
	sizeX, sizeY, sizeZ = None,None,None
	frames = []	
	framepwrs = []

	def noInterrupt(fileName, sizeX, sizeY, sizeZ, framepwrs,fps):
		try:
			scipy.io.savemat(fileName, mdict={'radarData': frames, 'sizeX': sizeX, 'sizeY': sizeY, 'sizeZ': sizeZ,'maxPower': framepwrs,'fps': fps})
		finally:
			print("Done: num exporting to .mat \n")

	def exit_handler():
		fps = len(framepwrs) / (time.time() - startTime)
		t0.cancel()
		#Put the function in a thread, and wait for the thread to finish. Python threads cannot be interrupted except with a special C api.
		a = Thread(target=noInterrupt, args=(fileName, sizeX, sizeY, sizeZ, framepwrs,fps))
		a.start()
		a.join()
		
	atexit.register(exit_handler)
	t0.start()
	startTime = time.time()
	while True:
		#appStatus, calibrationProcess = wlbt.GetStatus()
		# 5) Trigger: Scan (sense) according to profile and record signals
		# to be available for processing and retrieval.
		wlbt.Trigger()
		# 6) Get action: retrieve the last completed triggered recording
		targets = wlbt.GetImagingTargets()
		confidence = wlbt.GetAdvancedParameter(wlbt.PARAM_CONFIDENCE_FACTOR)
		energy = wlbt.GetImageEnergy()
		imgMatrix, sizeX, sizeY, sizeZ, maxPower = wlbt.GetRawImage()
		frames.append(imgMatrix)
		framepwrs.append(maxPower)
		#rasterImage, _, _, sliceDepth, power = wlbt.GetRawImageSlice()
		# PrintSensorTargets(targets)
		#PrintSensorTargets(targets,confidence)
		# 7) Stop and Disconnect.
	wlbt.Stop()
	wlbt.Disconnect()
	wlbt.Clean()
	print('Terminate successfully')
	
if __name__ == '__main__':
	parser = OptionParser()
	parser.add_option(
		"-f",
		"--file",
		dest="fileName",
		help="file name to output",
		metavar="FILE")

	(options, args) = parser.parse_args()

	if not options.fileName:
		print("you have to specify the file name")
		sys.exit(1)

	record(options.fileName)