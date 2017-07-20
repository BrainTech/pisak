#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
This experiment was created using PsychoPy2 Experiment Builder (v1.84.2+brain4),
    on Wed 19 Jul 2017 05:57:21 PM CEST
If you publish work using this script please cite the PsychoPy publications:
    Peirce, JW (2007) PsychoPy - Psychophysics software in Python.
        Journal of Neuroscience Methods, 162(1-2), 8-13.
    Peirce, JW (2009) Generating stimuli for neuroscience using PsychoPy.
        Frontiers in Neuroinformatics, 2:10. doi: 10.3389/neuro.11.010.2008
"""

from __future__ import absolute_import, division
from psychopy import locale_setup, gui, visual, core, data, event, logging, sound
from psychopy.constants import (NOT_STARTED, STARTED, PLAYING, PAUSED,
                                STOPPED, FINISHED, PRESSED, RELEASED, FOREVER)
import numpy as np  # whole numpy lib is available, prepend 'np.'
from numpy import (sin, cos, tan, log, log10, pi, average,
                   sqrt, std, deg2rad, rad2deg, linspace, asarray)
from numpy.random import random, randint, normal, shuffle
import os  # handy system and path functions
import sys  # to get file system encoding

# Ensure that relative paths start from the same directory as this script
_thisDir = os.path.dirname(os.path.abspath(__file__)).decode(sys.getfilesystemencoding())
os.chdir(_thisDir)

# Home directory for saving output data
from os.path import expanduser
_homeDir = expanduser("~")

# Store info about the experiment session
expName = 'budzikp'  # from the Builder filename that created this script
expInfo = {'participant':'', 'session':'001'}
dlg = gui.DlgFromDict(dictionary=expInfo, title=expName)
if dlg.OK == False:
    core.quit()  # user pressed cancel
expInfo['date'] = data.getDateStr()  # add a simple timestamp
expInfo['expName'] = expName

# Data file name stem = absolute path + name; later add .psyexp, .csv, .log, etc
filename = _homeDir + os.sep + u'data/%s_%s_%s' % (expInfo['participant'], expName, expInfo['date'])

# An ExperimentHandler isn't essential but helps with data saving
thisExp = data.ExperimentHandler(name=expName, version='',
    extraInfo=expInfo, runtimeInfo=None,
    originPath=None,
    savePickle=True, saveWideText=True,
    saveTags=True, dataFileName=filename)
# save a log file for detail verbose info
logFile = logging.LogFile(filename+'.log', level=logging.EXP)
logging.console.setLevel(logging.WARNING)  # this outputs to the screen, not a file

endExpNow = False  # flag for 'escape' or other condition => quit the exp

# Start Code - component code to be run before the window creation

# Setup the Window
win = visual.Window(
    size=(1920, 1080), fullscr=True, screen=0,
    allowGUI=False, allowStencil=False,
    monitor='testMonitor', color=[0,0,0], colorSpace='rgb',
    blendMode='avg', useFBO=True)
# store frame rate of monitor if we can measure it
expInfo['frameRate'] = win.getActualFrameRate()
if expInfo['frameRate'] != None:
    frameDur = 1.0 / round(expInfo['frameRate'])
else:
    frameDur = 1.0 / 60.0  # could not measure, so guess

# Initialize components for Routine "instr"
instrClock = core.Clock()
text = visual.TextStim(win=win, name='text',
    text='default text',
    font='Arial',
    pos=(0, 0), height=0.1, wrapWidth=None, ori=0, 
    color='white', colorSpace='rgb', opacity=1,
    depth=0.0);

# Initialize components for Routine "select"
selectClock = core.Clock()
image = visual.ImageStim(
    win=win, name='image',
    image='sin', mask=None,
    ori=0, pos=(-0.5, 0), size=(0.5, 0.8),
    color=[1,1,1], colorSpace='rgb', opacity=1,
    flipHoriz=False, flipVert=False,
    texRes=128, interpolate=True, depth=0.0)
image_2 = visual.ImageStim(
    win=win, name='image_2',
    image='sin', mask=None,
    ori=0, pos=(0.5, 0), size=(0.5, 0.8),
    color=[1,1,1], colorSpace='rgb', opacity=1,
    flipHoriz=False, flipVert=False,
    texRes=128, interpolate=True, depth=-1.0)
mouse = event.Mouse(win=win)
x, y = [None, None]
polygon = visual.Line(
    win=win, name='polygon',
    start=(-(2, 0.5)[0]/2.0, 0), end=(+(2, 0.5)[0]/2.0, 0),
    ori=90, pos=(0, 0),
    lineWidth=1, lineColor=[1,1,1], lineColorSpace='rgb',
    fillColor=[1,1,1], fillColorSpace='rgb',
    opacity=1, depth=-3.0, interpolate=True)

# Initialize components for Routine "eval"
evalClock = core.Clock()


polygon_2 = visual.Rect(
    win=win, name='polygon_2',
    width=(2, 2)[0], height=(2, 2)[1],
    ori=0, pos=[0,0],
    lineWidth=1, lineColor=[0.6,0.6,1], lineColorSpace='rgb',
    fillColor=[0.6,0.6,1], fillColorSpace='rgb',
    opacity=1, depth=-2.0, interpolate=True)
image_3 = visual.ImageStim(
    win=win, name='image_3',
    image='sin', mask=None,
    ori=0, pos=(-0.5, 0), size=(0.5, 0.8),
    color=[1,1,1], colorSpace='rgb', opacity=1,
    flipHoriz=False, flipVert=False,
    texRes=128, interpolate=True, depth=-3.0)
image_4 = visual.ImageStim(
    win=win, name='image_4',
    image='sin', mask=None,
    ori=0, pos=(0.5, 0), size=(0.5, 0.8),
    color=[1,1,1], colorSpace='rgb', opacity=1,
    flipHoriz=False, flipVert=False,
    texRes=128, interpolate=True, depth=-4.0)


# Create some handy timers
globalClock = core.Clock()  # to track the time since experiment started
routineTimer = core.CountdownTimer()  # to track time remaining of each (non-slip) routine 

# set up handler to look after randomisation of conditions etc
trials = data.TrialHandler(nReps=1, method='sequential', 
    extraInfo=expInfo, originPath=-1,
    trialList=data.importConditions('conditions.xlsx'),
    seed=None, name='trials')
thisExp.addLoop(trials)  # add the loop to the experiment
thisTrial = trials.trialList[0]  # so we can initialise stimuli with some values
# abbreviate parameter names if possible (e.g. rgb = thisTrial.rgb)
if thisTrial != None:
    for paramName in thisTrial.keys():
        exec(paramName + '= thisTrial.' + paramName)

for thisTrial in trials:
    currentLoop = trials
    # abbreviate parameter names if possible (e.g. rgb = thisTrial.rgb)
    if thisTrial != None:
        for paramName in thisTrial.keys():
            exec(paramName + '= thisTrial.' + paramName)
    
    # ------Prepare to start Routine "instr"-------
    t = 0
    instrClock.reset()  # clock
    frameN = -1
    continueRoutine = True
    # update component parameters for each repeat
    text.setTagParams({})
    text.setText("Wybierz obiekt:\n" + correct)
    text.setTagName('')
    key_resp_2 = event.BuilderKeyResponse()
    # keep track of which components have finished
    instrComponents = [text, key_resp_2]
    for thisComponent in instrComponents:
        if hasattr(thisComponent, 'status'):
            thisComponent.status = NOT_STARTED
    
    # -------Start Routine "instr"-------
    while continueRoutine:
        # get current time
        t = instrClock.getTime()
        frameN = frameN + 1  # number of completed frames (so 0 is the first frame)
        # update/draw components on each frame
        
        # *text* updates
        if t >= 0.0 and text.status == NOT_STARTED:
            # keep track of start time/frame for later
            text.tStart = t
            text.frameNStart = frameN  # exact frame index
            text.setAutoDraw(True)
        
        # *key_resp_2* updates
        if t >= 0.0 and key_resp_2.status == NOT_STARTED:
            # keep track of start time/frame for later
            key_resp_2.tStart = t
            key_resp_2.frameNStart = frameN  # exact frame index
            key_resp_2.status = STARTED
            # keyboard checking is just starting
            win.callOnFlip(key_resp_2.clock.reset)  # t=0 on next screen flip
            event.clearEvents(eventType='keyboard')
        if key_resp_2.status == STARTED:
            theseKeys = event.getKeys(keyList=['space'])
            
            # check for quit:
            if "escape" in theseKeys:
                endExpNow = True
            if len(theseKeys) > 0:  # at least one key was pressed
                key_resp_2.keys = theseKeys[-1]  # just the last key pressed
                key_resp_2.rt = key_resp_2.clock.getTime()
                # a response ends the routine
                continueRoutine = False
        
        # check if all components have finished
        if not continueRoutine:  # a component has requested a forced-end of Routine
            break
        continueRoutine = False  # will revert to True if at least one component still running
        for thisComponent in instrComponents:
            if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
                continueRoutine = True
                break  # at least one component has not yet finished
        
        # check for quit (the Esc key)
        if endExpNow or event.getKeys(keyList=["escape"]):
            core.quit()
        
        # refresh the screen
        if continueRoutine:  # don't flip if this routine is over or we'll get a blank screen
            win.flip()
    
    # -------Ending Routine "instr"-------
    for thisComponent in instrComponents:
        if hasattr(thisComponent, "setAutoDraw"):
            thisComponent.setAutoDraw(False)
    # check responses
    if key_resp_2.keys in ['', [], None]:  # No response was made
        key_resp_2.keys=None
    trials.addData('key_resp_2.keys',key_resp_2.keys)
    if key_resp_2.keys != None:  # we had a response
        trials.addData('key_resp_2.rt', key_resp_2.rt)
    # the Routine "instr" was not non-slip safe, so reset the non-slip timer
    routineTimer.reset()
    
    # ------Prepare to start Routine "select"-------
    t = 0
    selectClock.reset()  # clock
    frameN = -1
    continueRoutine = True
    # update component parameters for each repeat
    image.setImage(object1 + ".png")
    image.setTagParams({})
    image.setTagName('')
    image_2.setImage(object2 + ".png")
    image_2.setTagParams({})
    image_2.setTagName('')
    # setup some python lists for storing info about the mouse
    mouse.x = []
    mouse.y = []
    mouse.leftButton = []
    mouse.midButton = []
    mouse.rightButton = []
    mouse.time = []
    polygon.setTagParams({})
    polygon.setTagName('')
    # keep track of which components have finished
    selectComponents = [image, image_2, mouse, polygon]
    for thisComponent in selectComponents:
        if hasattr(thisComponent, 'status'):
            thisComponent.status = NOT_STARTED
    
    # -------Start Routine "select"-------
    while continueRoutine:
        # get current time
        t = selectClock.getTime()
        frameN = frameN + 1  # number of completed frames (so 0 is the first frame)
        # update/draw components on each frame
        
        # *image* updates
        if t >= 0.0 and image.status == NOT_STARTED:
            # keep track of start time/frame for later
            image.tStart = t
            image.frameNStart = frameN  # exact frame index
            image.setAutoDraw(True)
        
        # *image_2* updates
        if t >= 0.0 and image_2.status == NOT_STARTED:
            # keep track of start time/frame for later
            image_2.tStart = t
            image_2.frameNStart = frameN  # exact frame index
            image_2.setAutoDraw(True)
        # *mouse* updates
        if t >= 0.0 and mouse.status == NOT_STARTED:
            # keep track of start time/frame for later
            mouse.tStart = t
            mouse.frameNStart = frameN  # exact frame index
            mouse.status = STARTED
            event.mouseButtons = [0, 0, 0]  # reset mouse buttons to be 'up'
        if mouse.status == STARTED:  # only update if started and not stopped!
            buttons = mouse.getPressed()
            if sum(buttons) > 0:  # ie if any button is pressed
                x, y = mouse.getPos()
                mouse.x.append(x)
                mouse.y.append(y)
                mouse.leftButton.append(buttons[0])
                mouse.midButton.append(buttons[1])
                mouse.rightButton.append(buttons[2])
                mouse.time.append(selectClock.getTime())
                # abort routine on response
                continueRoutine = False
        
        # *polygon* updates
        if t >= 0.0 and polygon.status == NOT_STARTED:
            # keep track of start time/frame for later
            polygon.tStart = t
            polygon.frameNStart = frameN  # exact frame index
            polygon.setAutoDraw(True)
        
        # check if all components have finished
        if not continueRoutine:  # a component has requested a forced-end of Routine
            break
        continueRoutine = False  # will revert to True if at least one component still running
        for thisComponent in selectComponents:
            if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
                continueRoutine = True
                break  # at least one component has not yet finished
        
        # check for quit (the Esc key)
        if endExpNow or event.getKeys(keyList=["escape"]):
            core.quit()
        
        # refresh the screen
        if continueRoutine:  # don't flip if this routine is over or we'll get a blank screen
            win.flip()
    
    # -------Ending Routine "select"-------
    for thisComponent in selectComponents:
        if hasattr(thisComponent, "setAutoDraw"):
            thisComponent.setAutoDraw(False)
    # store data for trials (TrialHandler)
    if len(mouse.x): trials.addData('mouse.x', mouse.x[0])
    if len(mouse.y): trials.addData('mouse.y', mouse.y[0])
    if len(mouse.leftButton): trials.addData('mouse.leftButton', mouse.leftButton[0])
    if len(mouse.midButton): trials.addData('mouse.midButton', mouse.midButton[0])
    if len(mouse.rightButton): trials.addData('mouse.rightButton', mouse.rightButton[0])
    if len(mouse.time): trials.addData('mouse.time', mouse.time[0])
    # the Routine "select" was not non-slip safe, so reset the non-slip timer
    routineTimer.reset()
    
    # ------Prepare to start Routine "eval"-------
    t = 0
    evalClock.reset()  # clock
    frameN = -1
    continueRoutine = True
    routineTimer.add(2.000000)
    # update component parameters for each repeat
    from enum import Enum
    
    class Side(Enum):
        LEFT = 0
        RIGHT = 1
    
    class Answer:
        def __init__(self):
            self.side = None
            self.isCorrect = False
    
    ans = Answer()
    if (mouse.x[-1] <= 0):
        ans.side = Side.LEFT
    else:
        ans.side = Side.RIGHT
    
    if (str(correct) == str(object1)):
        corrSide = Side.LEFT
    else:
        corrSide = Side.RIGHT
    
    ans.isCorrect = ans.side == corrSide
    print(ans.isCorrect)
    if (ans.side == Side.LEFT):
        highlight_pos = (-1, 0)
    else:
        highlight_pos = (1, 0)
    polygon_2.setTagParams({})
    polygon_2.setPos(highlight_pos)
    polygon_2.setTagName('')
    image_3.setImage(object1 + ".png")
    image_3.setTagParams({})
    image_3.setTagName('')
    image_4.setImage(object2 + ".png")
    image_4.setTagParams({})
    image_4.setTagName('')
    
    # keep track of which components have finished
    evalComponents = [polygon_2, image_3, image_4]
    for thisComponent in evalComponents:
        if hasattr(thisComponent, 'status'):
            thisComponent.status = NOT_STARTED
    
    # -------Start Routine "eval"-------
    while continueRoutine and routineTimer.getTime() > 0:
        # get current time
        t = evalClock.getTime()
        frameN = frameN + 1  # number of completed frames (so 0 is the first frame)
        # update/draw components on each frame
        
        
        
        # *polygon_2* updates
        if t >= 0.0 and polygon_2.status == NOT_STARTED:
            # keep track of start time/frame for later
            polygon_2.tStart = t
            polygon_2.frameNStart = frameN  # exact frame index
            polygon_2.setAutoDraw(True)
        frameRemains = 0.0 + 2- win.monitorFramePeriod * 0.75  # most of one frame period left
        if polygon_2.status == STARTED and t >= frameRemains:
            polygon_2.setAutoDraw(False)
        
        # *image_3* updates
        if t >= 0.0 and image_3.status == NOT_STARTED:
            # keep track of start time/frame for later
            image_3.tStart = t
            image_3.frameNStart = frameN  # exact frame index
            image_3.setAutoDraw(True)
        frameRemains = 0.0 + 2- win.monitorFramePeriod * 0.75  # most of one frame period left
        if image_3.status == STARTED and t >= frameRemains:
            image_3.setAutoDraw(False)
        
        # *image_4* updates
        if t >= 0.0 and image_4.status == NOT_STARTED:
            # keep track of start time/frame for later
            image_4.tStart = t
            image_4.frameNStart = frameN  # exact frame index
            image_4.setAutoDraw(True)
        frameRemains = 0.0 + 2- win.monitorFramePeriod * 0.75  # most of one frame period left
        if image_4.status == STARTED and t >= frameRemains:
            image_4.setAutoDraw(False)
        
        
        # check if all components have finished
        if not continueRoutine:  # a component has requested a forced-end of Routine
            break
        continueRoutine = False  # will revert to True if at least one component still running
        for thisComponent in evalComponents:
            if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
                continueRoutine = True
                break  # at least one component has not yet finished
        
        # check for quit (the Esc key)
        if endExpNow or event.getKeys(keyList=["escape"]):
            core.quit()
        
        # refresh the screen
        if continueRoutine:  # don't flip if this routine is over or we'll get a blank screen
            win.flip()
    
    # -------Ending Routine "eval"-------
    for thisComponent in evalComponents:
        if hasattr(thisComponent, "setAutoDraw"):
            thisComponent.setAutoDraw(False)
    
    
    trials.addData('ans.isCorrect', ans.isCorrect)
    thisExp.nextEntry()
    
# completed 1 repeats of 'trials'




# these shouldn't be strictly necessary (should auto-save)
thisExp.saveAsWideText(filename+'.csv')
thisExp.saveAsPickle(filename)
thisExp.saveAsTags(filename+'.tag')
logging.flush()
# make sure everything is closed down
thisExp.abort()  # or data files will save again on exit
win.close()
core.quit()
