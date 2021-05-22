# -*- coding: utf-8; mode: python; indent-tabs-mode: t; tab-width:4 -*-
import sys, time, utils, math, os.path

from QtVersion import *
from PyQt5.QtWidgets import QTabWidget
import pyqtgraph as pg
import numpy as np
import eyes17.eyemath17 as em


class Expt(QWidget):
	TIMER = 50
	RPWIDTH = 300
	RPGAP = 4
	running = False
	
	VMIN = 0
	VMAX = 0.7
	VMAX2 = 5
	VSET = VMIN
	VSET2 = VMIN
	IMIN = 0
	IMAX = 5
	inputIMIN = 0
	inputIMAX = 7
	outputIMIN = 0
	outputIMAX = 5
	inputVMIN = 0
	inputVMAX = 0.5
	outputVMIN = 0
	outputVMAX = 5
	oldVoutput = 0
	STEP = 0.005	   # 50 mV
	STEP2 = 0.05
	data = [ [], [] ]
	currentTrace = None
	traces = []
	legends = []
	history = []		# Data store	
	trial = 0
	
	oldI_B = 0
	def __init__(self, device=None):
		QWidget.__init__(self)
		self.p = device										# connection to the device hardware 

		self.traceCols = utils.makeTraceColors()
		self.resultCols = utils.makeResultColors()
		
		self.tabs = QTabWidget()
		
		self.pwin = pg.PlotWidget()							# pyqtgraph window
		self.pwin.showGrid(x=True, y=True)					# with grid
		ax = self.pwin.getAxis('bottom')
		ax.setLabel(self.tr('Voltage V_BE (V)'))	
		ax = self.pwin.getAxis('left')
		ax.setLabel(self.tr('Current Ib (uA)'))
		self.pwin.disableAutoRange()
		self.pwin.setXRange(self.inputVMIN, self.inputVMAX)
		self.pwin.setYRange(self.inputIMIN, self.inputIMAX)
		self.pwin.hideButtons()								# Do not show the 'A' button of pg
		
		
		
		
		



		self.tab1 = QWidget()
		self.tab1.setAutoFillBackground(True)
		self.tab2 = QWidget()
		self.tab2.setAutoFillBackground(True)
		self.tabs.resize(300,200) 
 
        # Add tabs
		self.tabs.addTab(self.tab1,"INPUT")
		self.tabs.addTab(self.tab2,"OUTPUT")


		rW = QWidget()
		right = QVBoxLayout()							# right side vertical layout
		right.setAlignment(Qt.AlignTop)
		right.setSpacing(self.RPGAP)
		right.addWidget(self.tabs)
		rW.setLayout(right)
		
		rW.setFixedWidth(260)

		#------------------------------------------
		# INPUT TAB START
		#------------------------------------------
		T1 = QVBoxLayout()							
		T1.setAlignment(Qt.AlignTop)
		T1.setSpacing(self.RPGAP)
		#T1.setAlignment(right)
		
		H= QHBoxLayout()
		self.defaultInputChkBox = QCheckBox("Use Defaults")
		self.defaultInputChkBox.setChecked(True)
		self.defaultInputChkBox.stateChanged.connect(self.defaultInputChkBoxChanged)
		H.addWidget(self.defaultInputChkBox)
		T1.addLayout(H)

		H = QHBoxLayout()
		
		l = QLabel(text=self.tr('Enter V_CE Value'))
		l.setMaximumWidth(140)
		H.addWidget(l)
		self.V_C_USER = utils.lineEdit(40, 1.0, 6, None)
		H.addWidget(self.V_C_USER)
		l = QLabel(text=self.tr('V'))
		l.setMaximumWidth(10)
		H.addWidget(l)
		
		T1.addLayout(H)
		
		
		H = QHBoxLayout()
		
		l = QLabel(text=self.tr('Steps'))
		l.setMaximumWidth(140)
		H.addWidget(l)
		self.UserStep = QLineEdit()
		self.UserStep = utils.lineEdit(40, 0.005, 6, None)
		self.UserStep.setText("0.05")
		#self.UserStep.setDisabled(True)
		
		H.addWidget(self.UserStep)
		l = QLabel(text=self.tr('V'))
		l.setMaximumWidth(10)
		H.addWidget(l)
		T1.addLayout(H)

		

		

		H = QHBoxLayout()
		
		right.addLayout(H)

		self.startInputButton = QPushButton(self.tr("Start"))
		T1.addWidget(self.startInputButton)
		self.startInputButton.clicked.connect(self.startInput)	

	
	
		
		b = QPushButton(self.tr("Stop"))
		T1.addWidget(b)
		b.clicked.connect(self.stop)		
		
		b = QPushButton(self.tr("Clear Traces"))
		T1.addWidget(b)
		b.clicked.connect(self.clear)		

		
		

		if(self.trial >= 0):
			b = QPushButton(self.tr("Show Results"))
			T1.addWidget(b)
			b.clicked.connect(self.showdialogInput)	
			
		self.SaveButton = QPushButton(self.tr("Save Data"))
		self.SaveButton.clicked.connect(self.save_data)		
		T1.addWidget(self.SaveButton)

		H = QHBoxLayout()
		self.ResultsInput = QTextEdit()	
		self.ResultsInput.setMaximumWidth(self.RPWIDTH/2-5)
		H.addWidget(self.ResultsInput)
		T1.addLayout(H)
		self.tab1.layout = T1
		
		self.V_C_USER.setDisabled(True)
		self.UserStep.setDisabled(True)
		self.V_C_USER.setText("2")
		self.UserStep.setText("0.05")
		
		self.tab1.setLayout(self.tab1.layout)

		#----------------INPUT TAB ENDS---------------------------------

		#------------------------------------------
		# OUTPUT TAB START
		#------------------------------------------
		

		T2 = QVBoxLayout()							
		T2.setAlignment(Qt.AlignTop)
		T2.setSpacing(self.RPGAP)
		#T2.setAlignment(right)
		

		H = QHBoxLayout()
		
		H = QHBoxLayout()
		l = QLabel(text=self.tr('Vbase (via 100kOhm)'))
		l.setMaximumWidth(140)
		H.addWidget(l)
		self.VBtext = utils.lineEdit(40, 1.0, 6, None)
		H.addWidget(self.VBtext)
		l = QLabel(text=self.tr('V'))
		l.setMaximumWidth(10)
		H.addWidget(l)
		
		T2.addLayout(H)
		
		
		H = QHBoxLayout()
		
		

		

		

		
		
		
		 
		self.startOutputButton = QPushButton(self.tr("Start"))
		T2.addWidget(self.startOutputButton)
		self.startOutputButton.clicked.connect(self.startOutput)	

	
	
		
		b = QPushButton(self.tr("Stop"))
		T2.addWidget(b)
		b.clicked.connect(self.stop)		
		
		b = QPushButton(self.tr("Clear Traces"))
		T2.addWidget(b)
		b.clicked.connect(self.clear)		

		
		if(self.trial >= 0):
			b = QPushButton(self.tr("Show Results"))
			T2.addWidget(b)
			b.clicked.connect(self.showdialogOutput)	
			
		self.SaveButton = QPushButton(self.tr("Save Data"))
		self.SaveButton.clicked.connect(self.save_data)		
		T2.addWidget(self.SaveButton)

		H = QHBoxLayout()
		self.Results = QTextEdit()	
		self.Results.setMaximumWidth(self.RPWIDTH/2-5)
		H.addWidget(self.Results)
		T2.addLayout(H)
		self.tab2.layout = T2
		
		self.tab2.setLayout(self.tab2.layout)











		#------------------------end of right panel ----------------
		
		top = QHBoxLayout()
		top.addWidget(self.pwin)
		top.addWidget(rW)
		
		full = QVBoxLayout()
		full.addLayout(top)
		self.msgwin = QLabel(text='')
		full.addWidget(self.msgwin)
		
		self.setLayout(full)
		
		self.timer = QTimer()
		self.timer.timeout.connect(self.update)
		self.timer.start(self.TIMER)


		self.tabs.currentChanged.connect(self.onChange)
		#----------------------------- end of init ---------------
	
	
				
	def defaultInputChkBoxChanged(self):
		if self.defaultInputChkBox.isChecked() == True:
			self.V_C_USER.setDisabled(True)
			self.UserStep.setDisabled(True)
			self.V_C_USER.setText("2")
			self.UserStep.setText("0.05")
			print("Checked")
		else:
			print("Not Checked")
			self.V_C_USER.setDisabled(False)
			self.UserStep.setDisabled(False)
	

	def onChange(self,i):
		trial = 0
		print(trial)
		
		if(i == 0):
			print
			self.clear()
			ax = self.pwin.getAxis('left')
			ay = self.pwin.getAxis('bottom')
			ax.setLabel(self.tr('Current I_B(uA)'))
			ay.setLabel(self.tr('Voltage V_BE (V)'))
			
			self.pwin.disableAutoRange()
			self.pwin.setXRange(self.inputVMIN, self.inputVMAX)
			self.pwin.setYRange(self.inputIMIN, self.inputIMAX)
			# for k in self.legends:
			# 	self.pwin.removeItem(k)
			# for k in rpythoself.traces:
			# 	self.pwin.removeItem(k)
			# self.history = []
			# self.trial = 0
			
			self.msg(self.tr('Cleared Traces because Tab was switched'))
		if(i == 1):
			self.clear()
			ax = self.pwin.getAxis('left')
			ay = self.pwin.getAxis('bottom')
			ax.setLabel(self.tr('Current I_C(mA)'))
			ay.setLabel(self.tr('Voltage V_CE (V)'))
			
			self.pwin.disableAutoRange()
			self.pwin.setXRange(self.outputVMIN, self.outputVMAX)
			self.pwin.setYRange(self.outputIMIN, self.outputIMAX)
			# for k in self.legends:
			# 	self.pwin.removeItem(k)
			# for k in self.traces:
			# 	self.pwin.removeItem(k)
			# self.history = []
			# self.trial = 0
			#self.msg(self.tr('Cleared Traces because Tab was switched'))

	#UPDATE AND START FOR INPUT CHARACTERISTICS
	def showdialogInput(self):
		msg = QMessageBox()
		msg.setIcon(QMessageBox.Information)

		msg.setText("This is a message box")
		msg.setInformativeText("This is additional information")
		msg.setWindowTitle("MessageBox demo")
		msg.setDetailedText("The details are as follows:")
		msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
		#msg.buttonClicked.connect(msgbtn)
			
		retval = msg.exec_()
		#print "value of pressed message box button:", retval
			
	def msgbtn(i):
		print("X")#print "Button pressed is:",i.text()

	def updateInput(self):
		if self.running == False:
			self.startInputButton.setEnabled(True)
		
			return
		try:
			V_BB = self.p.set_pv2(self.VSET)	
			time.sleep(0.001)	
			V_BE = self.p.get_voltage('A2')		# voltage across the diode
		except:
			self.comerr()
			return 
		
		I_B = ((V_BB - V_BE)/100.0)*1000
		if(V_BE > 0): 	 		   # in mA, R= 1k
			self.data[0].append(V_BE)
			self.data[1].append(I_B)
		#print(V_BE,I_B)
			diffI_B = float(I_B) - self.oldI_B
			if(diffI_B > 0.1):
				self.ResultsInput.append("("+str(round(float(V_BE),2)) + "V, "+str(round(float(I_B),2))+"uA)")
				self.oldI_B = float(I_B)

		
		self.VSET += self.STEP
		if V_BE > self.VMAX or I_B > 6:
			self.running = False
			self.history.append(self.data)
			#self.history[0][0].insert(0,"Voltage(V)")
			#self.history[1][0].insert(0,"Current(uA)")

			self.traces.append(self.currentTrace)
			self.msg(self.tr('Completed plotting I-V'))

			l = pg.TextItem(text=self.V_ce_txt, color= self.resultCols[self.trial%5])
			l.setPos(V_BE,I_B)
			self.pwin.addItem(l)
			self.legends.append(l)
			print(self.trial)
			self.trial += 1
			self.startInputButton.setEnabled(True)
			return
		if self.index > 1:			  # Draw the line
			self.currentTrace.setData(self.data[0], self.data[1])
		self.index += 1

	def startInput(self):
		self.VSET = 0
		self.oldI_B = 0
		
		self.startInputButton.setDisabled(True)
		
		if self.running == True: 

			return
		VCE_USER = float(self.V_C_USER.text())
		STEP = self.UserStep.text()
		
		self.ResultsInput.setText("")
		try:
			
			self.p.set_pv1(0)
			self.p.set_pv2(0)
			i = 0
			currentA1 = self.p.get_voltage('A1')
			#print(type(VCE_USER))
			
			while(currentA1 <= VCE_USER):
			
					

				i +=1
				VccSteps = VCE_USER / 20
				print(VccSteps)
				currentA1 = self.p.get_voltage('A1')
				print(self.p.get_voltage('A1'),VccSteps*i)
				if(VccSteps*i > 5):
					print("Exceeded")
					self.running = False
					self.startInputButton.setDisabled(False)
					mBox = QMessageBox()
					mBox.setText("PV1 exceeded max voltage. Set lower V_CE")
					mBox.setWindowTitle("Error")
					mBox.setIcon(QMessageBox.Information)
					
					mBox.setStandardButtons(QMessageBox.Ok)
					mBox.exec_()

					return
				
				
				
				self.p.set_pv1(VccSteps*i)
				
				
			# 	i +=1 
		
		
		except:
			#print("Hello")
			self.startInputButton.setEnabled(True)
			self.comerr()
			return
		
		



		
		
		""" try:
			self.p.set_pv1(5.0)			# Collector to 5V
			self.p.set_pv2(vbset)		# Set base bias on PV2, via 100 KOhm series resistance
			vb = self.p.get_voltage('A2')    # base voltage
		except:
			self.comerr()
			return  """
		
		""" if vb < 0.5 or vb > 0.7:
			vb = 0.6 """
		
		#ibase = (vbset-vb)/100.0e-3    # uA
		self.V_ce_txt = 'V_CE = %5.3f V'%float(VCE_USER)
		self.running = True
		self.data = [ [], [] ]
		self.VSET = self.VMIN
		self.currentTrace = self.pwin.plot([0,0],[0,0], pen = self.traceCols[self.trial%5])
		self.index = 0
		self.msg(self.tr('Started'))
		self.timer = QTimer()
		
		self.timer.timeout.connect(self.updateInput)
		self.timer.start(self.TIMER)

	#-----------------------------------------------------------------	

	#UPDATE AND START FOR OUTPUT CHARACTERISTICS
	def showdialogOutput(self):
		msg = QMessageBox()
		msg.setIcon(QMessageBox.Information)

		msg.setText("This is a message box")
		msg.setInformativeText("This is additional information")
		msg.setWindowTitle("MessageBox demo")
		msg.setDetailedText("The details are as follows:")
		msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
		#msg.buttonClicked.connect(msgbtn)
			
		retval = msg.exec_()
		#print "value of pressed message box button:", retval
		

	def updateOutput(self):
		if self.running == False:
			return
		try:
			vs = self.p.set_pv1(self.VSET2)	
			time.sleep(0.001)	
			va = self.p.get_voltage('A1')		# voltage across the diode
		except:
			self.comerr()
			return 
		
		i = (vs-va)/1.0 	 
		#print(va,i)		   # in mA, R= 1k
		self.data2[0].append(va)
		self.data2[1].append(i)

		self.Results.append("("+str(round(float(va),2)) + "V, "+str(round(float(i),2))+"mA)")
		self.VSET2 += self.STEP2
		print(self.VSET2)
		if self.VSET2 > self.VMAX2:
			self.running = False
			self.history.append(self.data)
			self.traces.append(self.currentTrace)
			self.msg(self.tr('Completed plotting I-V'))
			
			l = pg.TextItem(text=self.ibtxt, color= self.resultCols[self.trial])
			l.setPos(va,i)
			self.pwin.addItem(l)
			self.legends.append(l)
			self.trial += 1
			
			print(self.trial)
			return
		if self.index > 1:			  # Draw the line
			self.currentTrace.setData(self.data2[0], self.data2[1])
		self.index += 1


	def startOutput(self):
		if self.running == True: return
		V_BASE = self.VBtext.text()
		
		self.VSET2 = 0
		STEP = self.UserStep.text()
		vbset = float(V_BASE)
		self.Results.setText("")
		print("vbset:",vbset)
		try:
			
			if vbset < .5 or vbset > 3.0:
				self.msg(self.tr('Base voltage should be from .5 to 3'))
				return
		except:
			self.msg(self.tr('Invalid Base voltage, should be from .5 to 3'))
			return
				
		try:
			self.p.set_pv1(0)
			self.p.set_pv2(0)
			self.p.set_pv1(5.0)
					# Collector to 5V
			
			self.p.set_pv2(vbset)		# Set base bias on PV2, via 100 KOhm series resistance
			
			vb = self.p.get_voltage('A2')    # base voltage
		except:
			self.comerr()
			return 
		
		if vb < 0.5 or vb > 0.7:
			vb = 0.6
		ibase = (vbset-vb)/100.0e-3    # uA
		self.ibtxt = 'Ib = %5.3f uA'%ibase
		self.running = True
		self.data2 = [ [], [] ]
		self.VSET = self.VMIN
		self.currentTrace = self.pwin.plot([0,0],[0,0], pen = self.traceCols[self.trial%5])
		self.index = 0
		self.msg(self.tr('Started'))
		self.timer = QTimer()
		self.timer.timeout.connect(self.updateOutput)
		self.timer.start(self.TIMER)


	#-----------------------------------------------------------------


	def stop(self):
		if self.running == False: return
		self.running = False
		self.history.append(self.data)
		self.traces.append(self.currentTrace)
		self.msg(self.tr('User Stopped'))
		self.startInputButton.setEnabled(True)

	def clear(self):
		self.ResultsInput.setText("")
		self.Results.setText("")
		for k in self.legends:
			self.pwin.removeItem(k)
		for k in self.traces:
			self.pwin.removeItem(k)
		self.history = []
		self.trial = 0
		self.msg(self.tr('Cleared Traces and Data'))
		
	def save_data(self):
		if self.history == []:
			self.msg(self.tr('No data to save'))
			return
		fn = QFileDialog.getSaveFileName()
		print(fn)
		if fn != '':
			#print(self.history)
			self.p.save(self.history, fn[0])
			self.msg(self.tr('Traces saved to ') + unicode(fn[0]))				
		
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
	
