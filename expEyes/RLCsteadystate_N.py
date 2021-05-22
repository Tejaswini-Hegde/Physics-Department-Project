# -*- coding: utf-8; mode: python; indent-tabs-mode: t; tab-width:4 -*-
import sys, time, utils, math, os.path

from QtVersion import *

import sys, time, utils, math
import pyqtgraph as pg
import numpy as np
import eyes17.eyemath17 as em


class Expt(QWidget):
	outF = []
	outI = []
	TIMER = 50
	loopCounter = 0
	AWGmin = 1
	AWGmax = 5000
	AWGval = 150
	waveindex = 0
	wgainindex = 2
	
	RPVspacing = 2											# Right panel Widget spacing
	RPWIDTH = 350
	LABW = 60
	inputError = True
	# Scope parameters
	MAXCHAN = 5
	timeData    = [None]*MAXCHAN
	voltData    = [None]*MAXCHAN
	voltDataFit = [None]*MAXCHAN
	traceWidget = [None]*MAXCHAN
	traceWidgetF= [None]*MAXCHAN
	fitResWidget= [None]*MAXCHAN
	fitFine     = [0]*MAXCHAN
	Amplitude   = [0]*MAXCHAN
	Frequency   = [0]*MAXCHAN
	Phase       = [0]*MAXCHAN
	rangeVals   = [4]*MAXCHAN			# selected value of range
	rangeTexts  = ['4 V']*MAXCHAN		# selected value of range
	scaleLabs   = [None]*MAXCHAN		# display fullscale value inside pg
	phasorPlot = None
	phasorTraces = [None]*5

	MAXRES = 7	# Number of results to show
	resLabs     = [None]*MAXRES
	Results     = [None]*MAXRES
	MINV = -4.0
	MAXV = 4.0
	#sources = ['A1','A2','A3', 'MIC']
	#chanpens = ['y','g','r','m','c']     #pqtgraph pen colors

	tbvals = [0.500, 1.0, 2.0, 5.0, 10.0, 20.0, 50.0, 100.0, 200.0]	# allowed mS/div values
	NP = 500			# Number of samples
	TG = 1				# Number of channels
	MINDEL = 1			# minimum time between samples, in usecs
	MAXDEL = 1000
	delay = MINDEL		# Time interval between samples
	TBval = 4			# timebase list index
	Trigindex = 0
	Triglevel = 0
	legends = []
	#resCols = ['w','y','g','r','w','m','c']

	def __init__(self, device=None):
		QWidget.__init__(self)
		self.p = device			
		print(self.p)				# connection to the device hardware 
		try:
			self.p.select_range('A1',8.0)
			self.p.select_range('A2',8.0)
			self.p.configure_trigger(1, 'A2', 0)
			self.p.set_sine(self.AWGval)
		except:
			pass	

		self.traceCols = utils.makeTraceColors()
		self.traceColsFit = utils.makeFitTraceColors()
		self.resCols = utils.makeResultColors()
		print(self.resCols)
		
		self.pwin = pg.PlotWidget()							# pyqtgraph window
		
		self.pwin.showGrid(x=True, y=True)					# with grid
		for k in range(self.MAXCHAN):						# pg textItem to show the voltage scales
			self.scaleLabs.append(pg.TextItem(text='OK'))
		ax = self.pwin.getAxis('bottom')
		ax.setLabel(self.tr('Freq (Hz)'))	
		ax = self.pwin.getAxis('left')
		ax.setLabel(self.tr('Current'))

		self.set_timebase(self.TBval)
		self.pwin.disableAutoRange()
		self.pwin.setXRange(0, self.tbvals[self.TBval]*10)
		self.pwin.setYRange(self.MINV, self.MAXV)
		self.pwin.hideButtons()									# Do not show the 'A' button of pg

		for ch in range(self.MAXCHAN):							# initialize the pg trace widgets
			self.traceWidget[ch] = self.pwin.plot([0,0],[0,0], pen = self.traceCols[ch])
			#x=pg.mkPen(self.chanpens[ch], width=.5, style=Qt.DashLine) 
			self.traceWidgetF[ch] = self.pwin.plot([0,0],[0,0], pen = self.traceColsFit[ch])

		right = QVBoxLayout()									# right side vertical layout
		right.setAlignment(Qt.AlignTop)
		right.setSpacing(self.RPVspacing)

		#Results
		for k in range(self.MAXRES):						# pg textItem to show the Results
			self.resLabs[k] = pg.TextItem()
			self.pwin.addItem(self.resLabs[k])

		H = QHBoxLayout()
		l = QLabel(text=self.tr('Timebase'))
		l.setMaximumWidth(60)
		H.addWidget(l)
		self.TBslider = utils.slider(0, 8, self.TBval, 200, self.set_timebase)
		H.addWidget(self.TBslider)
		right.addLayout(H)
	
		self.SaveButton = QPushButton(self.tr("Save Data"))
		self.SaveButton.clicked.connect(self.save_data)		
		right.addWidget(self.SaveButton)		
		
		l = QLabel(text='<font color="blue">'+self.tr('Impedance Calculator'))
		right.addWidget(l)

		H = QHBoxLayout()
		l = QLabel(text=self.tr('F start(in Hz)'))
		l.setMaximumWidth(100)
		H.addWidget(l)
		self.sFreq = utils.lineEdit(50, "", 6, None)
		H.addWidget(self.sFreq)	
		right.addLayout(H)
		
		H = QHBoxLayout()
		l = QLabel(text=self.tr('F End(in Hz)'))
		l.setMaximumWidth(100)
		H.addWidget(l)
		self.eFreq = utils.lineEdit(50, "", 6, None)
		
		H.addWidget(self.eFreq)		

		right.addLayout(H)

		H = QHBoxLayout()
		l = QLabel(text=self.tr('# Intervals'))
		l.setMaximumWidth(100)
		H.addWidget(l)
		self.intervals = utils.lineEdit(50, "", 6, None)
		H.addWidget(self.intervals)		
		right.addLayout(H)


		
		
		H = QHBoxLayout()
		l = QLabel(text=self.tr('C (in uF)'))
		l.setMaximumWidth(50)
		H.addWidget(l)
		self.uCap = utils.lineEdit(50, 1, 6, None)
		H.addWidget(self.uCap)
		l = QLabel(text=self.tr('R (in Ohms)'))
		l.setMaximumWidth(75)
		H.addWidget(l)
		self.uRes = utils.lineEdit(50, 1000, 6, None)
		H.addWidget(self.uRes)
		right.addLayout(H)	
		
		H = QHBoxLayout()
		self.steps = QLabel()
		self.steps.setMaximumWidth(300)
		self.steps.setText("In Steps of:")
		H.addWidget(self.steps)
		self.intervals.textChanged.connect(self.updateStep)
		self.eFreq.textChanged.connect(self.updateStep)
		self.sFreq.textChanged.connect(self.updateStep)
		self.uCap.textChanged.connect(self.updateStep)
		self.uRes.textChanged.connect(self.updateStep)
		right.addLayout(H)

				
		b=QPushButton(self.tr('Start'))
		b.clicked.connect(self.calc)		
		right.addWidget(b)
		self.uResult =QLabel(text='')
		right.addWidget(self.uResult)
		
		#------------------------end of right panel ----------------
		
		top = QHBoxLayout()
		top.addWidget(self.pwin)
		top.addLayout(right)
		
		full = QVBoxLayout()
		full.addLayout(top)
		self.msgwin = QLabel(text=self.tr('messages'))
		full.addWidget(self.msgwin)
				
		self.setLayout(full)
		self.timer = QTimer()
		self.timer.timeout.connect(self.update)
		self.timer.start(self.TIMER)
		
		
		#----------------------------- end of init ---------------
	def updateStep(self):
		mStep = 0
		self.inputError = True
		print(self.eFreq.text())
		print(self.sFreq.text())
		s = int(self.sFreq.text())
		e = int(self.eFreq.text())
		if(s >= e):
			self.steps.setText("End freq should be greater than start")
			return

		if(self.intervals.text() == ""):
			self.steps.setText("Set interval!")
			return

		if(self.uCap.text() == ""):
			self.steps.setText("Set Capacitor Value!")
			return
			
		if(self.uRes.text() == ""):
			self.steps.setText("Set Resistor Value!")
			return


		self.inputError = False
		mStep = (int(self.eFreq.text()) - int(self.sFreq.text()) ) / int(self.intervals.text())
		self.steps.setText("Interval of " + str(mStep) + "Hz")
		return mStep

	def verify_fit(self,y,y1):
		sum = 0.0
		for k in range(len(y)):
			sum += abs((y[k] - y1[k])/y[k])
		err = sum/len(y)
		if err/sum > 0.01:
			self.msg(self.tr('Curve fitting result rejected'))
			return False
		else:
			return True

	""" def update(self):
		if self.Pause.isChecked() == True: return
		try:
			if self.VLC.isChecked() == True:
				self.timeData[0], self.voltData[0],\
				self.timeData[1], self.voltData[1],\
				self.timeData[2], self.voltData[2],\
				self.timeData[3], self.voltData[3] = self.p.capture4(self.NP, self.TG)

				self.timeData[4] = self.timeData[0]			
				self.voltData[3] = self.voltData[2] - self.voltData[0]   # voltage across C				
				self.voltData[4] = self.voltData[1] - self.voltData[2]   # voltage across L
				self.voltData[2] = self.voltData[1] - self.voltData[0]   # voltage across LC	
			else:
				self.timeData[0], self.voltData[0],\
				self.timeData[1], self.voltData[1] = self.p.capture2(self.NP, self.TG)
				self.timeData[2] = self.timeData[0]			
				self.voltData[2] = self.voltData[0] - self.voltData[1]   # voltage across LC
		except:
			self.comerr()
			return

		for ch in range(3):
			self.traceWidget[ch].setData(self.timeData[ch], self.voltData[ch])
			try:
				fa = em.fit_sine(self.timeData[ch],self.voltData[ch])
			except Exception as err:
				print("fit_sine error:", err)	
			if fa != None:
				self.traceWidgetF[ch].setData(self.timeData[ch], fa[0])
				if self.verify_fit(self.voltData[ch], fa[0]) == False:
					return
				self.voltDataFit[ch] = fa[0]
				self.Amplitude[ch] = (fa[1][0])
				self.Frequency[ch] = fa[1][1]*1000
				self.Phase[ch] = fa[1][2] * 180/em.pi
				self.fitFine[ch] = 1
			else:
				self.msg(self.tr('Data Analysis Error'))
				return
		phaseDiff = (self.Phase[0] - self.Phase[1])
	
		if self.VLC.isChecked() == True:
			for ch in range(3,5):
				self.traceWidget[ch].setData(self.timeData[ch], self.voltData[ch])
				try:
					fa = em.fit_sine(self.timeData[ch],self.voltData[ch])
				except Exception as err:
					print("fit_sine error:", err)	
				if fa != None:
					self.traceWidgetF[ch].setData(self.timeData[ch], fa[0])
					if self.verify_fit(self.voltData[ch], fa[0]) == False:
						return
					self.voltDataFit[ch] = fa[0]
					self.Amplitude[ch] = (fa[1][0])
					self.Frequency[ch] = fa[1][1]*1000
					self.Phase[ch] = fa[1][2] * 180/em.pi
					self.fitFine[ch] = 1
				else:
					self.msg(self.tr('Data Analysis Error'))
					return			
		
		for k in range(self.MAXRES): self.Results[k] = ''
		
		self.Results[0] = unicode(self.tr('Vtotal (A1) = %5.2f V')) %(self.Amplitude[0])
		self.Results[1] = unicode(self.tr('Vr (A2) = %5.2f V')) %(self.Amplitude[1])
		self.Results[2] = unicode(self.tr('Vlc (A2-A1) = %5.2f V')) %(self.Amplitude[2])

		self.Results[5] = unicode(self.tr('F = %5.1f Hz')) %(self.Frequency[0])
		self.Results[6] = unicode(self.tr('Phase Diff = %5.1f deg')) %phaseDiff

		if self.VLC.isChecked() == True:
			self.Results[3] = unicode(self.tr('Vc (A3-A1) = %5.2f V')) %(self.Amplitude[3])
			self.Results[4] = unicode(self.tr('Vl (A2-A3) = %5.2f V')) %(self.Amplitude[4])
		else:
			self.Results[3] = ''
			self.Results[4] = ''

		for k in range(5):
			self.pwin.removeItem(self.resLabs[k])
			self.resLabs[k] = pg.TextItem(text=self.Results[k],	color= self.resCols[k%5])
			self.resLabs[k].setPos(0, -4 +0.3*k)
			self.pwin.addItem(self.resLabs[k])
		
		for k in range(5,7):
			self.pwin.removeItem(self.resLabs[k])
			self.resLabs[k] = pg.TextItem(text=self.Results[k],	color= self.resCols[k%5])
			self.resLabs[k].setPos(0, 4 -0.3*(k-5))
			self.pwin.addItem(self.resLabs[k])
		

		if self.fitFine[0] == 1 and self.fitFine[1] == 1 and self.fitFine[2] == 1:
			self.draw_phasor() """
		# End of update



		


		
	def calc(self):
		
		if(self.inputError):
			self.uResult.setText(self.tr('Invalid Input in some field'))
			return

		try:
			print("Inside calc")
			
			C = float(self.uCap.text())*1e-6
			R = float(self.uRes.text())
			intervals = float(self.intervals.text())
			start = int(self.sFreq.text())
			end = int(self.eFreq.text())
			print(C,R,intervals,start,end)
			
			#mStep = self.updateStep()
			mStep = 10
			
			print("mStep: " + str(mStep))
			output = []
			#self.p.set_sine_amp(2)
			
			for i in range(start, end, mStep):
				#print(i)
				#print(self.p)
				f = self.p.set_sine(i)
				time.sleep(0.2)
			
				#print("set sine")
				volt = self.p.get_voltage('A1')
				current = volt / R
				data = (f, current, volt)
				plot = pg.TextItem(text=str(current), color='y')
				plot.setPos(f, current)
				self.legends.append(plot)
				self.pwin.addItem(plot)
				print((f, volt))
				output.append(data)
				
			#print(output)




		except:
			print("Error")
			print(traceback.format_exc())
			self.uResult.setText(self.tr('Invalid Input in some field'))
	
	def save_data(self):
		self.timer.stop()
		fn = QFileDialog.getSaveFileName()
		if fn != '':
			dat = []
			if self.VLC.isChecked() == True:
				nc = 5
			else:
				nc = 3
			for ch in range(nc):
					dat.append( [self.timeData[ch], self.voltData[ch] ])
			self.p.save(dat,fn)
			self.msg(self.tr('Traces saved to ') +unicode(fn))
		self.timer.start(self.TIMER)		
			
	def set_timebase(self, tb):
		self.TBval = tb
		self.pwin.setXRange(0, self.tbvals[self.TBval]*10)
		msperdiv = self.tbvals[int(tb)]				#millisecs / division
		totalusec = msperdiv * 1000 * 10.0  	# total 10 divisions
		self.TG = int(totalusec/self.NP)
		if self.TG < self.MINDEL:
			self.TG = self.MINDEL
		elif self.TG > self.MAXDEL:
			self.TG = self.MAXDEL

	


		
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
	
