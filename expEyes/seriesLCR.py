# -*- coding: utf-8; mode: python; indent-tabs-mode: t; tab-width:4 -*-
from __future__ import print_function
import sys, time, utils, math, os.path

from QtVersion import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import pyqtgraph as pg
import numpy as np
import eyes17.eyemath17 as em
import matplotlib.pyplot as plt
import platform


class Expt(QWidget):
	TIMER = 50
	RPWIDTH = 300
	RPGAP = 4
	running = False
	MINDEL = 1			# minimum time between samples, in usecs
	MAXDEL = 1000
	
	FMIN = 1
	FMAX = 500
	FREQ = FMIN
	NSTEP = 25
	STEP = 10	  # 10 hz
	GMIN = 0.0		# filter amplitude Gain
	GMAX = 12
	Rload = 560.0
	data = [ [], [] ]
	currentTrace = None
	traces = []
	history = []		# Data store	
	sources = ['A1','A2','A3', 'MIC']
	trial = 0
	
	def __init__(self, device=None):
		QWidget.__init__(self)
		self.p = device										# connection to the device hardware 
		try:
			self.p.select_range('A1',4.0)
			self.p.select_range('A2',4.0)	
			self.p.configure_trigger(0, 'A1', 0)
		except:
			pass	

		self.traceCols = utils.makeTraceColors()
		
		self.pwin = pg.PlotWidget()							# pyqtgraph window
		self.pwin.showGrid(x=True, y=True)					# with grid
		ax = self.pwin.getAxis('bottom')
		ax.setLabel(self.tr('Frequency (Hz)'))	
		ax = self.pwin.getAxis('left')
		ax.setLabel(self.tr('Current (mA)'))
		self.pwin.disableAutoRange()
		self.pwin.setXRange(self.FMIN, self.FMAX)
		self.pwin.setYRange(self.GMIN, self.GMAX)
		self.pwin.hideButtons()								# Do not show the 'A' button of pg

		right = QVBoxLayout()							# right side vertical layout
		right.setAlignment(Qt.AlignTop)
		right.setSpacing(self.RPGAP)

		'''
		H = QHBoxLayout()
		l = QLabel(text=self.tr('Rload ='))
		l.setMaximumWidth(50)
		H.addWidget(l)
		self.LoadRes = utils.lineEdit(60, self.Rload, 6, None)
		H.addWidget(self.LoadRes)
		l = QLabel(text=self.tr('Ohm'))
		l.setMaximumWidth(40)
		H.addWidget(l)
		right.addLayout(H)
		'''

		H = QHBoxLayout()
		l = QLabel(text=self.tr('From'))
		l.setMaximumWidth(35)
		H.addWidget(l)
		self.AWGstart = utils.lineEdit(60, self.FMIN, 6, None)
		H.addWidget(self.AWGstart)
		l = QLabel(text=self.tr('to'))
		l.setMaximumWidth(20)
		H.addWidget(l)
		self.AWGstop = utils.lineEdit(60, self.FMAX, 6, None)
		H.addWidget(self.AWGstop)
		l = QLabel(text=self.tr('Hz'))
		l.setMaximumWidth(20)
		H.addWidget(l)
		right.addLayout(H)

		H = QHBoxLayout()
		l = QLabel(text=self.tr('R (in Ohms)'))
		l.setMaximumWidth(75)
		H.addWidget(l)
		self.uRes = utils.lineEdit(50, 50, 6, None)
		H.addWidget(self.uRes)
		right.addLayout(H)	

		H = QHBoxLayout()
		l = QLabel(text=self.tr('Number of Steps ='))
		l.setMaximumWidth(120)
		H.addWidget(l)
		self.NSTEPtext = utils.lineEdit(60, self.NSTEP, 6, None)
		H.addWidget(self.NSTEPtext)
		right.addLayout(H)

		H = QVBoxLayout()
		rightWidget = QWidget()
		rightWidget.setLayout(H)

		
		rightWidget = QWidget()

		rightLayout = QVBoxLayout()
		rightWidget.setLayout(rightLayout)

		annotate = QFormLayout()
		annotLabel = QLabel("Amplitude")
		
	
		annotate.addWidget(annotLabel)
		
		self.btn1 = QRadioButton("3V", rightWidget)
		self.btn2 = QRadioButton("1V", rightWidget)
		self.btn1.setChecked(True)
		
		btns = [self.btn1,self.btn2]
		
    
		for btn in btns:
		
			annotate.addWidget(btn)

		right.addLayout(annotate)

		

		b = QPushButton(self.tr("Start"))
		right.addWidget(b)
		b.clicked.connect(self.start)		
		
		self.FreqLabel = QLabel(self.tr("Frequency:.."))
		right.addWidget(self.FreqLabel)

		b = QPushButton(self.tr("Stop"))
		right.addWidget(b)
		b.clicked.connect(self.stop)		

		b = QPushButton(self.tr("Clear Traces"))
		right.addWidget(b)
		b.clicked.connect(self.clear)		

		self.SaveButton = QPushButton(self.tr("Save Data"))
		self.SaveButton.clicked.connect(self.save_data)		
		right.addWidget(self.SaveButton)
		
		self.SaveImageButton = QPushButton(self.tr("Save Image"))
		self.SaveImageButton.clicked.connect(self.save_image)		
		right.addWidget(self.SaveImageButton)

		#------------------------end of right panel ----------------
		
		top = QHBoxLayout()
		top.addWidget(self.pwin)
		top.addLayout(right)
		
		full = QVBoxLayout()
		full.addLayout(top)
		self.msgwin = QLabel(text='')
		full.addWidget(self.msgwin)
				
		self.setLayout(full)
		
		self.timer = QTimer()
		self.timer.timeout.connect(self.update)
		self.timer.start(self.TIMER)
		

		#----------------------------- end of init ---------------

	def verify_fit(self,y,y1):
		sum = 0.0
		for k in range(len(y)):
			sum += abs((y[k] - y1[k])/y[k])
		err = sum/len(y)
		if err > .5:
			return False
		else:
			return True
				
	def update(self):
		if self.running == False:
			return
		try:	
			fr=self.p.set_sine(self.FREQ)
		except:
			self.comerr()
			return 

		time.sleep(0.02)	
		self.TG = 1.e6/self.FREQ/50   # 50 points per wave
		self.TG = int(self.TG)//2 * 2
		NP = 500
		MAXTIME = 200000.  # .2 seconds
		if NP * self.TG > MAXTIME:
			NP = int(MAXTIME/self.TG)
		if NP % 2: NP += 1  # make it an even number
		ss = '%5.1f'%fr
		self.FreqLabel.setText(self.tr('Frequency = ') + ss + self.tr(' Hz'))
		if self.TG < self.MINDEL:
			self.TG = self.MINDEL
		elif self.TG > self.MAXDEL:
			self.TG = self.MAXDEL

		goodFit = False
		for k in range(20):	          # try 3 times
			try:
				t,v, tt,vv = p = self.p.capture2(NP, int(self.TG))	
				#print(p)
			except:
				self.comerr()
				return 
			try:
				fa = em.fit_sine(t,v)
			except:
				self.msg(self.tr('Fit failed'))
				fa = None
			if fa != None:
				if self.verify_fit(v,fa[0]) == False:	#compare trace with the fitted curve
					continue
				try:
					fb = em.fit_sine(tt,vv)
				except:
					self.msg(self.tr('Fit failed'))
					fb = None
				if fb != None:
					#if self.verify_fit(vv,fb[0]) == False:     
					#	continue
					self.data[0].append(fr)
					gain = abs(fb[1][0]) #/fa[1][0])
					print(gain/float(self.uRes.text()))
					
					self.data[1].append((gain/float(self.uRes.text()))*1000)
					if self.gainMax < gain:
						self.gainMax = gain
						self.peakFreq = fr
					goodFit = True
					break
		
		self.FREQ += self.STEP
		#if goodFit == False: return

		if self.FREQ > self.FMAX:
			print ('Done')
			self.running = False
			self.history.append(self.data)
			self.traces.append(self.currentTrace)
			im = self.gainMax/self.Rload * 1000
			self.msg(self.tr('completed'))
			return

		if self.index > 1:			  # Draw the line
			self.currentTrace.setData(self.data[0], self.data[1])
		self.index += 1


	def start(self):
		if self.running == True: return
		if(self.btn1.isChecked()):
			self.p.set_sine_amp(2) #2 -> 3V
		if(self.btn2.isChecked()):
			
			self.p.set_sine_amp(1) #2 -> 3V
		try:
			self.FMIN = float(self.AWGstart.text())
			self.FMAX = float(self.AWGstop.text())
			self.NSTEP = float(self.NSTEPtext.text())
		except:
			self.msg(self.tr('Invalid Frequency limits'))
			return
		
		self.pwin.setXRange(self.FMIN, self.FMAX)
		self.pwin.setYRange(self.GMIN, self.GMAX)
		self.STEP = (self.FMAX - self.FMIN)/ self.NSTEP

		try:	
			self.p.select_range('A1',4)
			self.p.select_range('A2',4)
		except:
			self.comerr()
			return 
		self.running = True
		self.data = [ [], [] ]
		self.FREQ = self.FMIN
		self.currentTrace = self.pwin.plot([0,0],[0,0], pen = self.traceCols[self.trial%5])
		self.index = 0
		self.trial += 1
		self.gainMax = 0.0

		
		self.msg(self.tr('Started'))


	def stop(self):
		if self.running == False: return
		self.running = False
		self.history.append(self.data)
		self.traces.append(self.currentTrace)
		im = self.gainMax/self.Rload * 1000
		self.msg(self.tr('user Stopped'))

	def clear(self):
		if self.running == True:
			self.msg(self.tr('Measurement in progress'))
			return
		for k in self.traces:
			self.pwin.removeItem(k)
		self.history = []
		self.trial = 0
		self.msg(self.tr('Cleared Traces and Data'))
		
	def save_data(self):
		if self.running == True:
			self.msg(self.tr('Measurement in progress'))
			return
		if self.history == []:
			self.msg(self.tr('No data to save'))
			return
		fn = QFileDialog.getSaveFileName()
		if fn != '':
			self.p.save(self.history, fn)
			self.msg(self.tr('Traces saved to ') + unicode(fn))
			
	def save_image(self):
		dialog = QFileDialog()
		dialog.setFileMode(QFileDialog.AnyFile)
		dialog.setFilter(QDir.Files)
		
		if dialog.exec_():
			file_name = dialog.selectedFiles()
			
		self.file_processing(file_name)
		
	def plot(self, X_values, Y_values):
		plt.figure(figsize=(7,6))
		plt.title("LCR Series Experiment")
		plt.xlabel("Frequency in Hz")
		plt.ylabel("Current in mA")
		plt.grid()
		for x, y in zip(X_values, Y_values):
			i_max = np.array(y).max()
			i_max_index = y.index(i_max)
			x1 = [x[i] for i in range(i_max_index+1)]
			x2 = [x[i] for i in range(i_max_index+1, len(x))]
			# assert (np.all(np.diff(x1) > 0))
			y1 =  [y[i] for i in range(i_max_index+1)]
			y2 = [y[i] for i in range(i_max_index+1, len(y))]
			y_val = i_max / math.sqrt(2)
			first = np.interp(y_val, y1, x1)
			y2.sort()
			x2.reverse()
			second = np.interp(y_val, y2, x2)
			plt.plot(x, y, label="f1= "+str(round(first, 3))+"Hz & f2= "+str(round(second, 3))+"Hz")
			plt.plot(first, y_val, "ro", markersize=3)
			plt.plot(second, y_val, "ro", markersize=3)
			plt.legend(loc='best', frameon=False, borderaxespad=0)
		if "Windows" in platform.platform():
			path = "C:\\"
		else:
			path = "~/Desktop"
		fn = QFileDialog.getSaveFileName(self, 'Saving Image', path)
		if "." in fn[0]:
			plt.savefig(fn[0])
		else:
			plt.savefig(fn[0]+".png")
			
	def file_processing(self, file_name):
		skip = True
		X_values = []
		Y_values = []
		x_values = []
		y_values = []
		if file_name[0].endswith('.txt'):
			try:
				with open(file_name[0], 'r') as f:
					Lines = f.readlines()
					for line in Lines:
						partition = line.partition("  ")
						if partition[0] == '\n':
							X_values.append(x_values)
							Y_values.append(y_values)
							x_values = []
							y_values = []
							skip = False
						else:
							x_values.append(float(partition[0]))
							y_values.append(float(partition[2]))
					else:
						if skip:
							X_values.append(x_values)
							Y_values.append(y_values)
							x_values = []
							y_values = []

					self.plot(X_values, Y_values)
					f.close()
			except Exception as e:
				buttonReply = QMessageBox.question(self, 'File Error', "Select the Right File!!!", QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Cancel)
				
		else:
			buttonReply = QMessageBox.question(self, 'File Error', "Only .txt files are allowed!", QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Cancel)
			pass
		
	def msg(self, m):
		self.msgwin.setText(self.tr(m))
		
	def comerr(self):
		self.msgwin.setText('<font color="red">' + self.tr('Error. Try Device->Reconnect'))

if __name__ == '__main__':
	import eyes17.eyes
	dev = eyes17.eyes.open()
	app = QApplication(sys.argv)

	# translation stuff
	lang=QLocale.system().name()
	t=QTranslator()
	t.load("lang/"+lang, os.path.dirname(__file__))
	app.installTranslator(t)
	t1=QTranslator()
	t1.load("qt_"+lang,
	        QLibraryInfo.location(QLibraryInfo.TranslationsPath))
	app.installTranslator(t1)

	mw = Expt(dev)
	mw.show()
	sys.exit(app.exec_())
	
