import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Suppress TensorFlow warnings

import cv2
import re
from cvzone.HandTrackingModule import HandDetector

# Button Class
class Button:
    def __init__(self, pos, width, height, value):
        self.pos = pos
        self.width = width
        self.height = height
        self.value = value

    def draw(self, img):
        cv2.rectangle(img, self.pos, (self.pos[0] + self.width, self.pos[1] + self.height),
                      (225, 225, 225), cv2.FILLED)
        cv2.rectangle(img, self.pos, (self.pos[0] + self.width, self.pos[1] + self.height),
                      (50, 50, 50), 3)
        cv2.putText(img, self.value, (self.pos[0] + 30, self.pos[1] + 70),
                    cv2.FONT_HERSHEY_PLAIN, 2, (50, 50, 50), 2)

    def checkClick(self, x, y, img):
        if self.pos[0] < x < self.pos[0] + self.width and self.pos[1] < y < self.pos[1] + self.height:
            # Highlight on click
            cv2.rectangle(img, (self.pos[0] + 3, self.pos[1] + 3),
                          (self.pos[0] + self.width - 3, self.pos[1] + self.height - 3),
                          (255, 255, 255), cv2.FILLED)
            cv2.putText(img, self.value, (self.pos[0] + 25, self.pos[1] + 80),
                        cv2.FONT_HERSHEY_PLAIN, 5, (0, 0, 0), 5)
            return True
        return False

# Evaluation Function with percentage logic
def safeEval(expr):
    # Allow numbers, ., +, -, *, /, %, parentheses and spaces
    if not re.fullmatch(r"[0-9\.\+\-\*/%\(\) ]+", expr):
        return "Error"
    try:
        # Case 1: A%B  -> (A/100)*B   (percentage of B)
        expr = re.sub(r'(\d+(\.\d+)?)%(\d+(\.\d+)?)', r'(\1/100*\3)', expr)

        # Case 2: Single number with % -> (num/100)
        expr = re.sub(r'(\d+(\.\d+)?)%(?!\d)', r'(\1/100)', expr)

        result = str(eval(expr))
        if result.endswith(".0"):
            result = result[:-2]
        return result
    except ZeroDivisionError:
        return "Divide by 0"
    except:
        return "Error"

# Setup webcam and hand detector
cap = cv2.VideoCapture(0)  # Change to 1 if your camera index is 1
cap.set(3, 1280)
cap.set(4, 720)

detector = HandDetector(detectionCon=0.8, maxHands=1)

# Buttons layout (including % button, clear C, backspace BS)
buttonListValues = [
    ['7', '8', '9', '*'],
    ['4', '5', '6', '-'],
    ['1', '2', '3', '+'],
    ['0', '/', '.', '='],
    ['C', 'BS', '%']
]

buttonList = []
for y in range(len(buttonListValues)):
    for x in range(len(buttonListValues[y])):
        xpos = x * 100 + 800
        ypos = y * 100 + 150
        buttonList.append(Button((xpos, ypos), 100, 100, buttonListValues[y][x]))

# Variables
myEquation = ''
delayCounter = 0

while True:
    success, img = cap.read()
    if not success:
        break

    img = cv2.flip(img, 1)
    hands, img = detector.findHands(img, flipType=False)

    # Display Screen
    cv2.rectangle(img, (800, 50), (1200, 150), (225, 225, 225), cv2.FILLED)
    cv2.rectangle(img, (800, 50), (1200, 150), (50, 50, 50), 3)
    cv2.putText(img, myEquation, (810, 120), cv2.FONT_HERSHEY_PLAIN, 3, (50, 50, 50), 3)

    # Draw Buttons
    for button in buttonList:
        button.draw(img)

    # Draw your name on UI
    cv2.putText(img, "Anupam", (910, 650), cv2.FONT_HERSHEY_PLAIN, 2, (0, 100, 255), 3)

    # Hand Interaction for clicks
    if hands:
        lmList = hands[0]['lmList']
        thumb_tip = lmList[4][:2]
        index_tip = lmList[8][:2]

        x, y = index_tip
        length, info, img = detector.findDistance(thumb_tip, index_tip, img, color=(255, 0, 255), scale=4)

        # Visual feedback
        cv2.line(img, thumb_tip, index_tip, (0, 0, 255), 6)
        mid_x, mid_y = info[4:]
        cv2.circle(img, (mid_x, mid_y), 12, (0, 255, 0), cv2.FILLED)

        # Detect click on button when fingers close
        if length < 50 and delayCounter == 0:
            for button in buttonList:
                if button.checkClick(x, y, img):
                    val = button.value
                    if val == '=':
                        myEquation = safeEval(myEquation)
                    elif val == 'C':
                        myEquation = ''
                    elif val == 'BS':
                        myEquation = myEquation[:-1]
                    else:
                        myEquation += val
                    delayCounter = 1

    # Delay to avoid multiple clicks
    if delayCounter != 0:
        delayCounter += 1
        if delayCounter > 10:
            delayCounter = 0

    # Show window
    cv2.imshow("Virtual Calculator", img)
    if cv2.waitKey(1) == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
