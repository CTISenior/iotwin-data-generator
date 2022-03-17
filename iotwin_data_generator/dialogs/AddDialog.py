#!/usr/bin/python3

import sys
import logging
import json

from connectors.client import Client
from utils.setting import Setting
import utils.helper as Helper
import utils.gui_helper as GUIHelper

from PySide2.QtWidgets import (
   QFormLayout,
   QComboBox,
   QVBoxLayout,
   QWidget,
   QLabel,
   QLineEdit,
   QCheckBox,
   QTabWidget,
   QSpinBox,
   QHBoxLayout,
   QGridLayout,
   QDialogButtonBox,
   QPushButton

)
from PySide2.QtCore import (
    Qt,
    QSize
)  


class AddDialog(QTabWidget):
   def __init__(self, MainWindow, parent = None):
      super(AddDialog, self).__init__(parent)
      self.left = 250
      self.top = 250
      self.width = 450
      self.height = 450
      self.setGeometry(self.left, self.top, self.width, self.height)

      self.MainWindow = MainWindow

      #self.setFixedSize(QSize(self.width, self.height))
      self.setWindowTitle("Add New Device")
      
      layout = QVBoxLayout()
      self.setLayout(layout)

      tabs = QTabWidget()
      
      tabs.addTab(self.tab1_UI(), "Thread")
      tabs.addTab(self.tab2_UI(), "Custom")
      
      self.button_box = QDialogButtonBox(
         QDialogButtonBox.Ok | QDialogButtonBox.Close,
         Qt.Horizontal,
         self
      )

      self.button_box.accepted.connect(self.add_device)
      self.button_box.rejected.connect(self.close)

      self.deviceStatus = QLabel()
      self.deviceStatus.setText('')

      layout2 = QHBoxLayout()

      layout.addWidget(tabs)
      layout2.addWidget(self.deviceStatus)
      layout2.addWidget(self.button_box)
      layout.addLayout(layout2)

      self.logger = logging.getLogger('main')
      self.logger.debug('AddDialog created')

   def tab1_UI(self):
      self.tab1 = QWidget()

      tab1_boxLayout = QVBoxLayout()
      tab1_formLayout = QFormLayout()

      self.deviceSN = QLineEdit(self)
      tab1_formLayout.addRow("SN*:", self.deviceSN)

      self.deviceName = QLineEdit(self)
      tab1_formLayout.addRow("Type/Name*:", self.deviceName)
      self.deviceModel = QLineEdit(self)
      tab1_formLayout.addRow("Model*:", self.deviceModel)
      self.deviceToken = QLineEdit(self)
      self.deviceToken.setEnabled(False)
      tab1_formLayout.addRow("Token:", self.deviceToken)
      

      self.keyValueBoxList = []
      for i in range(5): # 5 key-value rows
         keyValueBox = GUIHelper.create_key_value_fields(i)
         self.keyValueBoxList.append(keyValueBox)

      for i in range(len(self.keyValueBoxList)):
         keyComboBox, valueSpinBox, valueTypeBox, checkBox = GUIHelper.get_keyValueBox_widgets(self.keyValueBoxList[i])

         checkBox.toggled.connect(keyComboBox.setEnabled)
         checkBox.toggled.connect(valueSpinBox.setEnabled)
         checkBox.toggled.connect(valueTypeBox.setEnabled)

         tab1_formLayout.addRow(f'Key-{str(i+1)}:', self.keyValueBoxList[i])


      self.interval = QSpinBox(self)
      self.interval.setRange(1, 100)
      tab1_formLayout.addRow(QLabel("Interval(sec):"), self.interval)

      self.protocol = QComboBox(self)
      self.protocol.addItem("MQTT")
      self.protocol.addItem("HTTP")
      tab1_formLayout.addRow(QLabel("Protocol:"), self.protocol)

      self.secBox = QCheckBox("")
      self.secBox.setEnabled(False)
      tab1_formLayout.addRow(QLabel("Secure:"), self.secBox)
      self.secBox.stateChanged.connect(self.click_secure)

      
      tab1_formLayout.setSpacing(10)
      tab1_boxLayout.addLayout(tab1_formLayout)
      self.tab1.setLayout(tab1_boxLayout)

      return self.tab1

   def clickBox(state,keyComboBox):
      keyComboBox.setEnabled(True)

   def click_secure():
      print('secure')

   def add_device(self):
      protocol = self.protocol.currentText().lower()
      sensorType = self.deviceName.text()
      sensorModel = self.deviceModel.text()
      deviceSN = self.deviceSN.text()
      interval = int(self.interval.value())

      #next -> gettings keys from settings.json/settings.yaml file
      dataObj = {
         "serialNumber": deviceSN,
         "sensorType": sensorType,
         "sensorModel": sensorModel,
         "accessToken": "",
         "keyValue": [],
         "protocol": protocol,
         "thread": True,
         "interval": interval
      }

      fieldsToValidate = [
         deviceSN,
         sensorType,
         sensorModel
      ]


      invalidEditField = True
      invalidKeyField = True
      for field in fieldsToValidate:
         invalidEditField = Helper.validate_field(field)
         if(not invalidEditField):
            break


      key_list = []
      for i in range(len(self.keyValueBoxList)):
         keyComboBox, valueSpinBox, valueTypeBox, checkBox = GUIHelper.get_keyValueBox_widgets(self.keyValueBoxList[i])

         if checkBox.isChecked():
            key = keyComboBox.currentText()
            value = int(valueSpinBox.text())
            value_type = valueTypeBox.currentText()
            
            obj = {
               "key": key,
               "initValue": value,
               "valueType": value_type
            }

            key_list.append(key)

            dataObj["keyValue"].append(obj)
            
            if(not Helper.validate_field(key)):
               invalidKeyField = False
               

      if (
         not invalidEditField or 
         not invalidKeyField
      ):
         err = 'Invalid input! (Min: 3 and Max: 30 characters)'
         self.deviceStatus.setText(err)
         GUIHelper.show_message_box(
            self, 
            msg = err,
            title = 'Warning!',
            msgType = 'warning'
         )
         return


      checkDuplicatedKeys = Helper.check_duplicated_keys(key_list)
      if checkDuplicatedKeys: #same keys are invalid
         err = 'Duplicated keys!'
         self.deviceStatus.setText(err)
         GUIHelper.show_message_box(
            self, 
            msg = err,
            title = 'Warning!',
            msgType = 'warning'
         )
         return

         
      status = Helper.check_device_exist(deviceSN)
      if status == False:
         Helper.update_json(dataObj)
         self.deviceStatus.setText(f'Added!')
         self.MainWindow.display_devices() ## refresh content
         GUIHelper.show_message_box(
            self, 
            msg = f'New device added: [{deviceSN} - {protocol}]',
            title = 'Success'
         )
         #self.logger.debug(f'New device added: [{deviceSN} - {protocol}]')
      else:
         err = 'DeviceSN already exists!'
         self.deviceStatus.setText(err)
         GUIHelper.show_message_box(
            self, 
            msg = f'{err}: [{deviceSN} - {protocol}]',
            title = 'Warning!',
            msgType = 'warning'
         )
         #self.logger.warning(f'Device already exists!: [{deviceSN} - {protocol}]')



########################################### tab 2 ###########################################
   def tab2_UI(self):
      self.tab2 = QWidget()
      tab2_boxLayout = QVBoxLayout()
      tab2_formLayout = QFormLayout()
      
      tab2_formLayout.setSpacing(10)
      
      tab2_boxLayout.addLayout(tab2_formLayout)
      self.tab2.setLayout(tab2_boxLayout)

      return self.tab2


###############################################################################

   def closeEvent(self, event):
      self.MainWindow.display_devices()
      self.logger.warning(f'AddDialog closed')

