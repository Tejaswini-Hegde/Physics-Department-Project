import sys, time, utils, math, os.path

from QtVersion import *

import sys, time, utils, math
import pyqtgraph as pg
import numpy as np
import eyes17.eyemath17 as em

class Expt(QWidget):
	TIMER = 50
	def __init__(self, device=None):
		QWidget.__init__(self)
		self.p = device		
		layout = QVBoxLayout()
		 


		H = QHBoxLayout()
		H.setContentsMargins(0,0,0,0)
		l = QLabel(text=self.tr('Enter Text'))
		l.setMaximumWidth(100)
		H.addWidget(l)
		self.inpText = utils.lineEdit(150, "", 6, None)
		self.inpText.textChanged.connect(self.updateBin)
		H.addWidget(self.inpText)	
		layout.addLayout(H)


		H = QHBoxLayout()
		H.setContentsMargins(0,0,0,0)
		l = QLabel(text=self.tr('Enter Delay'))
		l.setMaximumWidth(100)
		H.addWidget(l)
		self.delay = utils.lineEdit(150, "", 6, None)
	 
		H.addWidget(self.delay)	
		layout.addLayout(H)

		H = QHBoxLayout()
		H.setContentsMargins(0,0,0,0) 
		l = QLabel(text=self.tr('The binary representation is'))

		H.addWidget(l)
		self.binRep = QLabel("")
		
		H.addWidget(self.binRep)	
		layout.addLayout(H)

	 		

		H = QHBoxLayout()
		H.setSpacing(0)
		H.setContentsMargins(0,0,0,0)
		self.startInputButton = QPushButton(self.tr("Start"))
		self.startInputButton.clicked.connect(self.send)
		H.addWidget(self.startInputButton)
		layout.addLayout(H)
		
		H = QHBoxLayout()
		H.setContentsMargins(0,0,0,0) 
		l = QLabel(text=self.tr('Data received'))

		H.addWidget(l)
		self.binRepRec = QLabel("")
		
		H.addWidget(self.binRepRec)	
		layout.addLayout(H)

		H = QHBoxLayout()
		H.setContentsMargins(0,0,0,0) 
		l = QLabel(text=self.tr('String received:'))

		H.addWidget(l)
		self.recStr = QLabel("")
		
		H.addWidget(self.recStr)	
		layout.addLayout(H)

	 
		
		
		# full = QVBoxLayout()
		# full.addLayout(layout)
		# self.setLayout(full)
		self.timer = QTimer()
		self.timer.timeout.connect(self.update)
		self.timer.start(self.TIMER)
		self.setLayout(layout)
	def updateBin(self):
		print("Getting called")
		text = self.inpText.text()
		text = list(text)
		text = list(map(ord,text))
		text = list(map(bin,text))
		text = [a[2:] for a in text]
		self.binRep.setText(str(text))

	def send(self):
		outputTextBin = []
		self.startInputButton.setEnabled(False)
		ip = self.p.set_pv1(3)
		self.p.set_pv2(4)

		text = self.inpText.text()
		
		print("Input text" + text)
		outputText = ""
		textList = list(text)
		
		for i in textList:
			l = list(bin(ord(i)))[2:] #get rid of 0b
			recCharBin = ""
			print(l)
			for j in l:
				k = int(j)
				self.p.set_pv1(3*k)
				#read
				time.sleep(float(self.delay.text()))
				read = self.p.get_voltage('A2')
				#print(5*k, read)
				if(abs(read) >= 1):
					recCharBin = recCharBin + "1"
				else:
					recCharBin = recCharBin + "0"
			outputTextBin.append(recCharBin)
			recCharInt = int(recCharBin,2)

			recChar = chr(recCharInt)

			outputText += recChar
			#print(recChar)
			#outputText = outputText + chr(int(recChar,2))
		self.binRepRec.setText(str(outputTextBin))
		print(outputText)
		self.recStr.setText(outputText)
		self.startInputButton.setEnabled(True)

		