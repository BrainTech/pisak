"""
Entry point for the PISAK admin panel application.
"""
import os

import configobj

from panel import Ui_MainWindow


CONFIG_DIR = os.path.join(os.path.expanduser('~'), '.pisak', 'configs')

if not os.path.isdir(CONFIG_DIR):
    os.makedirs(CONFIG_DIR)

CONFIG_PATH = os.path.join(CONFIG_DIR, 'main_config.ini')


class Panel(Ui_MainWindow):

    def __init__(self):
        super().__init__()
        self._cache = {}
        self._config = None

    def _apply_changes(self):
        self._config.update(self._cache)
        self._config.write()

    def _abort_changes(self):
        self._cache.clear()

    def _close(self):
        self.app.exit()

    def _load_config(self):
        self._config = configobj.ConfigObj(CONFIG_PATH, encoding='UTF-8')
        self._cache = self._config.copy()
        return self._config

    def _fill_in_forms(self):
        config = self._load_config()

        self.comboBox_input.setCurrentText(config['input'])
        self.comboBox_skin.setCurrentText(config['skin'])
        self.comboBox_reactOn.setCurrentText(config['scanning']['react_on'])
        self.horizontalSlider_volume.setValue(config.as_int('sound_effects_volume'))
        self.checkBox_sounds.setChecked(config.as_bool('sound_effects_enabled'))
        self.checkBox_buttonSoundSupport.setChecked(config.as_bool('read_button'))

        blog = config['blog']
        self.lineEdit_blogUsername.setText(blog['user_name'])
        self.lineEdit_blogPassword.setText(blog['password'])
        self.lineEdit_blogURL.setText(blog['address'])
        self.lineEdit_blogTitle.setText(blog['title'])

        email = config['email']
        self.lineEdit_emailAddress.setText(email['address'])
        self.lineEdit_emailPassword.setText(email['password'])
        self.lineEdit_emailSentFolder.setText(email['sent_folder'])
        self.lineEdit_emailIMAPServer.setText(email['IMAP_server'])
        self.lineEdit_emailSMTPServer.setText(email['SMTP_server'])
        self.comboBox_emailPortIMAP.setCurrentText(email['IMAP_port'])
        self.comboBox_emailPortSMTP.setCurrentText(email['SMTP_port'])

    def setupUi(self, MainWindow, app):
        super().setupUi(MainWindow)
        self.app = app
        self.mainWindow = MainWindow
        self._connect_all_signals()
        self._fill_in_forms()

    def _connect_all_signals(self):
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
        self._cache['available_apps']['blog'] = checked

    def onCheckBox_viewerToggled(self, checked):
        self._cache['available_apps']['viewer'] = checked

    def onCheckBox_spellerToggled(self, checked):
        self._cache['available_apps']['speller'] = checked

    def onCheckBox_symbolerToggled(self, checked):
        self._cache['available_apps']['symboler'] = checked

    def onCheckBox_movieToggled(self, checked):
        self._cache['available_apps']['movie'] = checked

    def onCheckBox_audioToggled(self, checked):
        self._cache['available_apps']['audio'] = checked

    def onCheckBox_paintToggled(self, checked):
        self._cache['available_apps']['paint'] = checked

    def onCheckBox_emailToggled(self, checked):
        self._cache['available_apps']['email'] = checked

    def onComboBox_inputCurrentIndexChanged(self, input_name):
        self._cache['input'] = input_name

    def onComboBox_skinCurrentIndexChanged(self, skin):
        self._cache['skin'] = skin

    def onHorizontalSlider_volumeValueChanged(self, value):
        self._cache['sound_effects_volume'] = value

    def onCheckBox_soundsToggled(self, checked):
        self._cache['sound_effects_enabled'] = checked

    def onCheckBox_buttonSoundSupportToggled(self, checked):
        self._cache['read_button'] = checked

    def onCheckBox_textCaseToggled(self, checked):
        self._cache['upper_case'] = checked

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
        self._cache['blog']['user_name'] = username

    def onLineEdit_blogPasswordTextChanged(self, password):
        self._cache['blog']['password'] = password

    def onLineEdit_blogURLTextChanged(self, url):
        self._cache['blog']['address'] = url

    def onLineEdit_blogTitleTextChanged(self, title):
        self._cache['blog']['title'] = title

    def onPushButton_blogTestClicked(self):
        pass

    def onLineEdit_followedBlog1TextChanged(self, blog):
        pass

    def onPushButton_emailTestClicked(self):
        pass

    def onLineEdit_emailAddressTextChanged(self, address):
        self._cache['email']['address'] = address

    def onLineEdit_emailPasswordTextChanged(self, password):
        self._cache['email']['password'] = password

    def onLineEdit_emailSentFolderTextChanged(self, folder):
        self._cache['email']['sent_folder'] = folder

    def onLineEdit_emailIMAPServerTextChanged(self, server):
        self._cache['email']['IMAP_server'] = server

    def onLineEdit_emailSMTPServerTextChanged(self, server):
        self._cache['email']['SMTP_server'] = server

    def onComboBox_emailPortIMAPCurrentTextChanged(self, port):
        self._cache['email']['IMAP_port'] = port

    def onComboBox_emailPortSMTPCurrentTextChanged(self, port):
        self._cache['email']['SMTP_port'] = port

    def onComboBox_spellerLayoutCurrentIndexChanged(self, layout):
        pass

    def onPushButton_abortClicked(self):
        self._abort_changes()
        self._close()

    def onPushButton_applyClicked(self):
        self._apply_changes()

    def onPushButton_okClicked(self):
        self._apply_changes()
        self._close()


if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication, QMainWindow

    app = QApplication(sys.argv)
    window = QMainWindow()
    ui = Panel()
    ui.setupUi(window, app)

    window.show()
    sys.exit(app.exec_())