from pisak import signals

@signals.registered_handler("budzik/answer_yes")
def answer_yes(text_box):
    '''
    Scroll the text field up.
    '''
    text_box.set_text("Wybrałeś TAK")

@signals.registered_handler("budzik/answer_no")
def answer_no(text_box):
    '''
    Scroll the text field up.
    '''
    text_box.set_text("Wybrałeś NIE")
