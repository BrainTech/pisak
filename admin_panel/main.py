"""
Entry point for the PISAK admin panel application.
"""
import os

import configobj
from PyQt5 import QtWidgets
from PyQt5.QtCore import QRegularExpression
from PyQt5.QtGui import QRegularExpressionValidator

from pisak.dirs import HOME_PISAK_CONFIGS, HOME_MAIN_CONFIG, RES_MAIN_CONFIG
from pisak.blog import config as blog_utils
from pisak.email.config import Config as email_utils
from pisak import email as email_app, blog as blog_app
from pisak.loc import CONFIG_MAPS as MAPS

from panel import Ui_MainWindow


if not os.path.isdir(HOME_PISAK_CONFIGS):
    os.makedirs(HOME_PISAK_CONFIGS)


class Panel(Ui_MainWindow):

    def __init__(self):
        super().__init__()
        self._cache = {}
        self._config = None
        self._followed_blogs = []

    def _apply_changes(self):
        self._config.update(self._cache)
        with open(HOME_MAIN_CONFIG, 'wb') as file:
            self._config.write(file)

    def _abort_changes(self):
        self._cache.clear()

    def _close(self):
        self.app.exit()

    def _load_config(self):
        self._config = configobj.ConfigObj(RES_MAIN_CONFIG, encoding='UTF-8')
        home_config = configobj.ConfigObj(HOME_MAIN_CONFIG, encoding='UTF-8')
        self._config.merge(home_config)
        self._cache = self._config.copy()
        return self._config

    def _fill_in_forms(self):
        config = self._load_config()

        self.comboBox_input.setCurrentText(MAPS['INPUT'][config['input']])
        self.comboBox_skin.setCurrentText(MAPS['SKIN'][config['skin']])
        self.comboBox_reactOn.setCurrentText(MAPS['REACT_ON'][config['scanning']['react_on']])
        self.horizontalSlider_volume.setValue(config.as_int('sound_effects_volume'))
        self.checkBox_sounds.setChecked(config.as_bool('sound_effects_enabled'))
        self.checkBox_buttonSoundSupport.setChecked(config.as_bool('sound_support_enabled'))
        self.checkBox_speechSynthesis.setChecked(config.as_bool('speech_synthesis'))
        self.horizontalSlider_spriteTimeout.setValue(config['PisakSprite'].as_int('timeout'))
        self.comboBox_spellerLayout.setCurrentText(MAPS['SPELLER_LAYOUT'][config['speller']['layout']])
        self.checkBox_textCase.setChecked(config.as_bool('upper_case'))

        blog = config['blog']
        self.lineEdit_blogUsername.setText(blog['user_name'])
        self.lineEdit_blogPassword.setText(blog_utils.decrypt_password(blog['password']))
        self.lineEdit_blogURL.setText(blog['address'])
        self.lineEdit_blogTitle.setText(blog['title'])

        email = config['email']
        self.lineEdit_emailAddress.setText(email['address'])
        self.lineEdit_emailPassword.setText(email_utils.decrypt_password(email['password']))
        self.lineEdit_emailSentFolder.setText(email['sent_folder'])
        self.lineEdit_emailIMAPServer.setText(email['IMAP_server'])
        self.lineEdit_emailSMTPServer.setText(email['SMTP_server'])
        self.comboBox_emailPortIMAP.setCurrentText(email['IMAP_port'])
        self.comboBox_emailPortSMTP.setCurrentText(email['SMTP_port'])

        available_apps = config['available_apps']
        self.checkBox_speller.setChecked(available_apps.as_bool('speller'))
        self.checkBox_symboler.setChecked(available_apps.as_bool('symboler'))
        self.checkBox_viewer.setChecked(available_apps.as_bool('viewer'))
        self.checkBox_audio.setChecked(available_apps.as_bool('audio'))
        self.checkBox_movie.setChecked(available_apps.as_bool('movie'))
        self.checkBox_paint.setChecked(available_apps.as_bool('paint'))
        self.checkBox_blog.setChecked(available_apps.as_bool('blog'))
        self.checkBox_email.setChecked(available_apps.as_bool('email'))
        self.checkBox_budzik.setChecked(available_apps.as_bool('budzik'))
        self.checkBox_exitButton.setChecked(available_apps.as_bool('exit_button'))

        scanning = config['PisakRowStrategy']
        self.horizontalSlider_cycleCount.setValue(scanning.as_int('max_cycle_count'))
        self.horizontalSlider_interval.setValue(scanning.as_int('interval'))
        self.horizontalSlider_startUpLag.setValue(scanning.as_int('start_up_lag'))
        self.horizontalSlider_selectLag.setValue(scanning.as_int('select_lag'))

        sound_effects = config['sound_effects']
        self.comboBox_scanSound.setCurrentText(sound_effects['scanning'])
        self.comboBox_selectSound.setCurrentText(sound_effects['selection'])

        prediction = config['prediction']
        self.lineEdit_prediction1.setText(prediction['first'])
        self.lineEdit_prediction2.setText(prediction['second'])
        self.lineEdit_prediction3.setText(prediction['third'])
        self.lineEdit_prediction4.setText(prediction['fourth'])
        self.lineEdit_prediction5.setText(prediction['fifth'])
        self.lineEdit_prediction6.setText(prediction['sixth'])
        self.lineEdit_prediction7.setText(prediction['seventh'])
        self.lineEdit_prediction8.setText(prediction['eighth'])
        self.lineEdit_prediction9.setText(prediction['ninth'])

        followed_blogs = config['followed_blogs']
        for idx, blog in enumerate(followed_blogs.values()):
            self._add_followed_blog(idx, blog)

    def _add_followed_blog(self, idx, blog=''):
        line_edit = QtWidgets.QLineEdit(blog)
        line_edit.alias = 'blog' + str(idx)
        attr_name = 'lineEdit_followedBlog' + str(idx)
        setattr(self, attr_name, line_edit)
        self._followed_blogs.append(line_edit)
        self.gridLayout_followedBlogs.addWidget(line_edit)
        line_edit.textChanged.connect(lambda blog: self.onLineEdit_followedBlogTextChanged(line_edit, blog))
        return line_edit

    def setupUi(self, MainWindow, app):
        super().setupUi(MainWindow)
        self.app = app
        self.mainWindow = MainWindow
        self._connect_all_signals()
        self._fill_in_forms()

        digit_regexp = QRegularExpression('^([1-9][0-9]*)*')
        digit_validator = QRegularExpressionValidator(digit_regexp)
        self.comboBox_emailPortIMAP.setValidator(digit_validator)
        self.comboBox_emailPortSMTP.setValidator(digit_validator)

    def _connect_all_signals(self):
        self.checkBox_blog.toggled.connect(self.onCheckBox_blogToggled)
        self.checkBox_viewer.toggled.connect(self.onCheckBox_viewerToggled)
        self.checkBox_speller.toggled.connect(self.onCheckBox_spellerToggled)
        self.checkBox_symboler.toggled.connect(self.onCheckBox_symbolerToggled)
        self.checkBox_paint.toggled.connect(self.onCheckBox_paintToggled)
        self.checkBox_movie.toggled.connect(self.onCheckBox_movieToggled)
        self.checkBox_audio.toggled.connect(self.onCheckBox_audioToggled)
        self.checkBox_email.toggled.connect(self.onCheckBox_emailToggled)
        self.checkBox_budzik.toggled.connect(self.onCheckBox_budzikToggled)
        self.checkBox_exitButton.toggled.connect(self.onCheckBox_exitButtonToggled)
        self.comboBox_input.currentIndexChanged[str].connect(self.onComboBox_inputCurrentIndexChanged)
        self.comboBox_skin.currentIndexChanged[str].connect(self.onComboBox_skinCurrentIndexChanged)
        self.horizontalSlider_volume.valueChanged.connect(self.onHorizontalSlider_volumeValueChanged)
        self.checkBox_sounds.toggled.connect(self.onCheckBox_soundsToggled)
        self.checkBox_buttonSoundSupport.toggled.connect(self.onCheckBox_buttonSoundSupportToggled)
        self.checkBox_speechSynthesis.toggled.connect(self.onCheckBox_speechSynthesis)
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
        self.pushButton_addFollowedBlog.clicked.connect(self.onPushButton_addFollowedBlogClicked)
        self.pushButton_emailTest.clicked.connect(self.onPushButton_emailTestClicked)
        self.lineEdit_emailAddress.textChanged.connect(self.onLineEdit_emailAddressTextChanged)
        self.lineEdit_emailSentFolder.textChanged.connect(self.onLineEdit_emailSentFolderTextChanged)
        self.lineEdit_emailPassword.textChanged.connect(self.onLineEdit_emailPasswordTextChanged)
        self.lineEdit_emailIMAPServer.textChanged.connect(self.onLineEdit_emailIMAPServerTextChanged)
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

    def onCheckBox_budzikToggled(self, checked):
        self._cache['available_apps']['budzik'] = checked

    def onCheckBox_exitButtonToggled(self, checked):
        self._cache['available_apps']['exit_button'] = checked

    def onCheckBox_movieToggled(self, checked):
        self._cache['available_apps']['movie'] = checked

    def onCheckBox_audioToggled(self, checked):
        self._cache['available_apps']['audio'] = checked

    def onCheckBox_paintToggled(self, checked):
        self._cache['available_apps']['paint'] = checked

    def onCheckBox_emailToggled(self, checked):
        self._cache['available_apps']['email'] = checked

    def onComboBox_inputCurrentIndexChanged(self, input_name):
        self._cache['input'] = MAPS['INPUT'][input_name]

    def onComboBox_skinCurrentIndexChanged(self, skin):
        self._cache['skin'] = MAPS['SKIN'][skin]

    def onHorizontalSlider_volumeValueChanged(self, value):
        self._cache['sound_effects_volume'] = value
        self.label_volumeCounter.setText(str(value))

    def onCheckBox_soundsToggled(self, checked):
        self._cache['sound_effects_enabled'] = checked

    def onCheckBox_buttonSoundSupportToggled(self, checked):
        self._cache['sound_support_enabled'] = checked

    def onCheckBox_speechSynthesis(self, checked):
        self._cache['speech_synthesis'] = checked

    def onCheckBox_textCaseToggled(self, checked):
        self._cache['upper_case'] = checked

    def onHorizontalSlider_cycleCountValueChanged(self, value):
        self._cache['PisakRowStrategy']['max_cycle_count'] = value
        self._cache['PisakArbitraryOrderStrategy']['max_cycle_count'] = value
        self.label_cycleCountCounter.setText(str(value))

    def onHorizontalSlider_intervalValueChanged(self, value):
        self._cache['PisakRowStrategy']['interval'] = value
        self._cache['PisakArbitraryOrderStrategy']['interval'] = value
        self.label_intervalCounter.setText(str(round(value/1000, 2)))

    def onHorizontalSlider_startUpLagValueChanged(self, value):
        self._cache['PisakRowStrategy']['start_up_lag'] = value
        self._cache['PisakArbitraryOrderStrategy']['start_up_lag'] = value
        self.label_startUpLagCounter.setText(str(round(value/1000, 2)))

    def onHorizontalSlider_selectLagValueChanged(self, value):
        self._cache['PisakRowStrategy']['select_lag'] = value
        self._cache['PisakArbitraryOrderStrategy']['select_lag'] = value
        self.label_selectLagCounter.setText(str(round(value/1000, 2)))

    def onHorizontalSlider_spriteTimeoutValueChanged(self, value):
        self._cache['PisakSprite']['timeout'] = value
        self.label_spriteTimeoutCounter.setText(str(round(value/1000, 2)))

    def onComboBox_reactOnCurrentIndexChanged(self, react_on):
        self._cache['scanning']['react_on'] = MAPS['REACT_ON'][react_on]

    def onComboBox_selectSoundCurrentIndexChanged(self, select_sound):
        self._cache['sound_effects']['selection'] = select_sound
        self._cache['select_sound_enabled'] = bool(select_sound)

    def onComboBox_scanSoundCurrentIndexChanged(self, scan_sound):
        self._cache['sound_effects']['scanning'] = scan_sound
        self._cache['scan_sound_enabled'] = bool(scan_sound)

    def onLineEdit_prediction1TextChanged(self, text):
        self._cache['prediction']['first'] = text

    def onLineEdit_prediction2TextChanged(self, text):
        self._cache['prediction']['second'] = text

    def onLineEdit_prediction3TextChanged(self, text):
        self._cache['prediction']['third'] = text

    def onLineEdit_prediction4TextChanged(self, text):
        self._cache['prediction']['fourth'] = text

    def onLineEdit_prediction5TextChanged(self, text):
        self._cache['prediction']['fifth'] = text

    def onLineEdit_prediction6TextChanged(self, text):
        self._cache['prediction']['sixth'] = text

    def onLineEdit_prediction7TextChanged(self, text):
        self._cache['prediction']['seventh'] = text

    def onLineEdit_prediction8TextChanged(self, text):
        self._cache['prediction']['eighth'] = text

    def onLineEdit_prediction9TextChanged(self, text):
        self._cache['prediction']['ninth'] = text

    def onLineEdit_blogUsernameTextChanged(self, username):
        self._cache['blog']['user_name'] = username

    def onLineEdit_blogPasswordTextChanged(self, password):
        self._cache['blog']['password'] = blog_utils.encrypt_password(password)

    def onLineEdit_blogURLTextChanged(self, url):
        self._cache['blog']['address'] = url

    def onLineEdit_blogTitleTextChanged(self, title):
        self._cache['blog']['title'] = title

    def _test_feedback(self, app, conf, feedback_label, utils):
        conf['password'] = utils.decrypt_password(conf['password'])
        resp, msg = app.test(conf)
        feedback_label.setText(msg)
        feedback_label.setStyleSheet('color: {}'.format('green' if resp else 'red'))

    def onPushButton_blogTestClicked(self):
        self._test_feedback(
            blog_app, self._cache['blog'].copy(), self.label_blogTest, blog_utils)

    def onLineEdit_followedBlogTextChanged(self, line_edit, blog):
        self._cache['followed_blogs'][line_edit.alias] = blog

    def onPushButton_addFollowedBlogClicked(self):
        idx = len(self._followed_blogs)
        line_edit = self._add_followed_blog(idx)
        line_edit.textChanged.connect(lambda blog: self.onLineEdit_followedBlogTextChanged(line_edit, blog))

    def onPushButton_emailTestClicked(self):
        self._test_feedback(
            email_app, self._cache['email'].copy(), self.label_emailTest, email_utils)

    def onLineEdit_emailAddressTextChanged(self, address):
        self._cache['email']['address'] = address

    def onLineEdit_emailPasswordTextChanged(self, password):
        self._cache['email']['password'] = email_utils.encrypt_password(password)

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
        self._cache['speller']['layout'] = MAPS['SPELLER_LAYOUT'][layout]

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
