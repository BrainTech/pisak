"""
Entry point for the PISAK admin panel application.
"""
from panel import Ui_MainWindow


class Panel(Ui_MainWindow):

    def setupUi(self, MainWindow):
        super().setupUi(MainWindow)
        self._connectAllSignals()

    def _connectAllSignals(self):
        self.checkBox_blog.toggled.connect(self.onCheckBox_blogToggled)
        self.checkBox_viewer.toggled.connect(self.onCheckBox_viewerToggled)
        self.checkBox_speller.toggled.connect(self.onCheckBox_spellerToggled)
        self.checkBox_symboler.toggled.connect(self.onCheckBox_symbolerToggled)
        self.checkBox_paint.toggled.connect(self.onCheckBox_paintToggled)
        self.checkBox_movie.toggled.connect(self.onCheckBox_movieToggled)
        self.checkBox_audio.toggled.connect(self.onCheckBox_audioToggled)
        self.checkBox_email.toggled.connect(self.onCheckBox_emailToggled)
        self.comboBox_input.currentIndexChanged[str].connect(self.onComboBox_inputCurrentIndexChanged)
        self.comboBox_skin.currentIndexChanged[str].connect(self.onComboBox_skinCurrentIndexChanged)
        self.horizontalSlider_volume.valueChanged.connect(self.onHorizontalSlider_volumeValueChanged)
        self.checkBox_sounds.toggled.connect(self.onCheckBox_soundsToggled)
        self.checkBox_buttonSoundSupport.toggled.connect(self.onCheckBox_buttonSoundSupportToggled)
        self.checkBox_textCase.toggled.connect(self.onCheckBox_textCaseToggled)
        self.horizontalSlider_cycleCount.valueChanged.connect(self.onHorizontalSlider_cycleCountValueChanged)
        self.horizontalSlider_interval.valueChanged.connect(self.onHorizontalSlider_intervalValueChanged)
        self.horizontalSlider_startUpLag.valueChanged.connect(self.onHorizontalSlider_startUpLagValueChanged)
        self.horizontalSlider_selectLag.valueChanged.connect(self.onHorizontalSlider_selectLagValueChanged)
        self.horizontalSlider_spriteTimeout.valueChanged.connect(self.onHorizontalSlider_spriteTimeoutValueChanged)
        self.comboBox_reactOn.currentIndexChanged[str].connect(self.onComboBox_reactOnCurrentIndexChanged)
        self.comboBox_selectSound.currentIndexChanged[str].connect(self.onComboBox_selectSoundCurrentIndexChanged)
        self.comboBox_scanSound.currentIndexChanged[str].connect(self.onComboBox_scanSoundCurrentIndexChanged)
        self.lineEdit_prediction1.textChanged.connect(self.onLineEdit_prediction1TextChanged)
        self.lineEdit_prediction2.textChanged.connect(self.onLineEdit_prediction2TextChanged)
        self.lineEdit_prediction3.textChanged.connect(self.onLineEdit_prediction3TextChanged)
        self.lineEdit_prediction4.textChanged.connect(self.onLineEdit_prediction4TextChanged)
        self.lineEdit_prediction5.textChanged.connect(self.onLineEdit_prediction5TextChanged)
        self.lineEdit_prediction6.textChanged.connect(self.onLineEdit_prediction6TextChanged)
        self.lineEdit_prediction7.textChanged.connect(self.onLineEdit_prediction7TextChanged)
        self.lineEdit_prediction8.textChanged.connect(self.onLineEdit_prediction8TextChanged)
        self.lineEdit_prediction9.textChanged.connect(self.onLineEdit_prediction9TextChanged)
        self.lineEdit_blogUsername.textChanged.connect(self.onLineEdit_blogUsernameTextChanged)
        self.lineEdit_blogPassword.textChanged.connect(self.onLineEdit_blogPasswordTextChanged)
        self.lineEdit_blogURL.textChanged.connect(self.onLineEdit_blogURLTextChanged)
        self.lineEdit_blogTitle.textChanged.connect(self.onLineEdit_blogTitleTextChanged)
        self.pushButton_blogTest.clicked.connect(self.onPushButton_blogTestClicked)
        self.lineEdit_followedBlog1.textChanged.connect(self.onLineEdit_followedBlog1TextChanged)
        self.pushButton_emailTest.clicked.connect(self.onPushButton_emailTestClicked)
        self.lineEdit_emailAddress.textChanged.connect(self.onLineEdit_emailAddressTextChanged)
        self.lineEdit_emailSentFolder.textChanged.connect(self.onLineEdit_emailSentFolderTextChanged)
        self.lineEdit_emailPassword.textChanged.connect(self.onLineEdit_emailPasswordTextChanged)
        self.lineEdit_emailIMAPServer.textChanged.connect(self.onLineEdit_emailIMAPServerTextChanged)
        self.lineEdit_emailPassword.textChanged.connect(self.onLineEdit_emailPasswordTextChanged)
        self.lineEdit_emailSMTPServer.textChanged.connect(self.onLineEdit_emailSMTPServerTextChanged)
        self.comboBox_emailPortIMAP.currentTextChanged.connect(self.onComboBox_emailPortIMAPCurrentTextChanged)
        self.comboBox_emailPortSMTP.currentTextChanged.connect(self.onComboBox_emailPortSMTPCurrentTextChanged)
        self.comboBox_spellerLayout.currentIndexChanged[str].connect(self.onComboBox_spellerLayoutCurrentIndexChanged)
        self.pushButton_abort.clicked.connect(self.onPushButton_abortClicked)
        self.pushButton_apply.clicked.connect(self.onPushButton_applyClicked)
        self.pushButton_ok.clicked.connect(self.onPushButton_okClicked)

    def onCheckBox_blogToggled(self, checked):
        pass

    def onCheckBox_viewerToggled(self, checked):
        pass

    def onCheckBox_spellerToggled(self, checked):
        pass

    def onCheckBox_symbolerToggled(self, checked):
        pass

    def onCheckBox_movieToggled(self, checked):
        pass

    def onCheckBox_audioToggled(self, checked):
        pass

    def onCheckBox_paintToggled(self, checked):
        pass

    def onCheckBox_emailToggled(self, checked):
        pass

    def onComboBox_inputCurrentIndexChanged(self, input_name):
        pass

    def onComboBox_skinCurrentIndexChanged(self, skin):
        pass

    def onHorizontalSlider_volumeValueChanged(self, value):
        pass

    def onCheckBox_soundsToggled(self, checked):
        pass

    def onCheckBox_buttonSoundSupportToggled(self, checked):
        pass

    def onCheckBox_textCaseToggled(self, checked):
        pass

    def onHorizontalSlider_cycleCountValueChanged(self, value):
        pass

    def onHorizontalSlider_intervalValueChanged(self, value):
        pass

    def onHorizontalSlider_startUpLagValueChanged(self, value):
        pass

    def onHorizontalSlider_selectLagValueChanged(self, value):
        pass

    def onHorizontalSlider_spriteTimeoutValueChanged(self, value):
        pass

    def onComboBox_reactOnCurrentIndexChanged(self, react_on):
        pass

    def onComboBox_selectSoundCurrentIndexChanged(self, select_sound):
        pass

    def onComboBox_scanSoundCurrentIndexChanged(self, scan_sound):
        pass

    def onLineEdit_prediction1TextChanged(self, text):
        pass

    def onLineEdit_prediction2TextChanged(self, text):
        pass

    def onLineEdit_prediction3TextChanged(self, text):
        pass

    def onLineEdit_prediction4TextChanged(self, text):
        pass

    def onLineEdit_prediction5TextChanged(self, text):
        pass

    def onLineEdit_prediction6TextChanged(self, text):
        pass

    def onLineEdit_prediction7TextChanged(self, text):
        pass

    def onLineEdit_prediction8TextChanged(self, text):
        pass

    def onLineEdit_prediction9TextChanged(self, text):
        pass

    def onLineEdit_blogUsernameTextChanged(self, username):
        pass

    def onLineEdit_blogPasswordTextChanged(self, password):
        pass

    def onLineEdit_blogURLTextChanged(self, url):
        pass

    def onLineEdit_blogTitleTextChanged(self, title):
        pass

    def onPushButton_blogTestClicked(self):
        pass

    def onLineEdit_followedBlog1TextChanged(self, blog):
        pass

    def onPushButton_emailTestClicked(self):
        pass

    def onLineEdit_emailAddressTextChanged(self, address):
        pass

    def onLineEdit_emailPasswordTextChanged(self, password):
        pass

    def onLineEdit_emailSentFolderTextChanged(self, folder):
        pass

    def onLineEdit_emailIMAPServerTextChanged(self, server):
        pass

    def onLineEdit_emailSMTPServerTextChanged(self, server):
        pass

    def onComboBox_emailPortIMAPCurrentTextChanged(self, port):
        pass

    def onComboBox_emailPortSMTPCurrentTextChanged(self, port):
        pass

    def onComboBox_spellerLayoutCurrentIndexChanged(self, layout):
        pass

    def onPushButton_abortClicked(self):
        pass

    def onPushButton_applyClicked(self):
        pass

    def onPushButton_okClicked(self):
        pass


if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication, QMainWindow

    app = QApplication(sys.argv)
    window = QMainWindow()
    ui = Panel()
    ui.setupUi(window)

    window.show()
    sys.exit(app.exec_())