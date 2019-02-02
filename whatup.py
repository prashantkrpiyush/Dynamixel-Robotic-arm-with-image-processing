import numpy as np
import cv2 as cv

ex = 0
why = 0


def coordinates(event, x, y, flags, param):
    if event == cv.EVENT_FLAG_LBUTTON:
        global ex
        global why
        ex = x
        why = y
        print("x=", x, "y=", y)


def udharja():
    global ex
    global why
    area = []
    avarea = []
    kernel = np.ones((5, 5), np.uint8)
    cap = cv.VideoCapture(1)
    ret, im = cap.read()
    ex = 0
    why = 0
    test = (0, 0)
    # cv.imshow("size",im)
    # cv.waitKey()
    # cv.destroyAllWindows()

    u = 116
    v = 87
    lower_color = np.array([0, u - 30, v - 30])
    upper_color = np.array([255, u + 30, v + 30])
    while True:

        # Take each frame
        _, frame = cap.read()
        hsv = cv.cvtColor(frame, cv.COLOR_BGR2YUV)
        mask = cv.inRange(hsv, lower_color, upper_color)
        res = cv.bitwise_and(frame, frame, mask=mask)
        thresh = cv.Canny(res, 100, 200)
        im3, contours1, hierarchy = cv.findContours(
            thresh, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE
        )
        cv.drawContours(thresh, contours1, -1, (0, 0, 255), 3)
        for i in range(len(contours1)):
            area.append(cv.contourArea(contours1[i]))
        (m, n), radius = cv.minEnclosingCircle(contours1[0])
        center = (int(m), int(n))
        r = int(radius)
        for i in range(len(contours1)):
            # avarea.append(cv.contourArea(contours1[i]))
            (m, n), radius = cv.minEnclosingCircle(contours1[i])
            if radius > r:
                center = (int(m), int(n))
                r = int(radius)
                ind = i
        (m, n), radius = cv.minEnclosingCircle(contours1[ind])
        center = (int(m), int(n))
        if test != center:
            cv.circle(frame, center, int(radius), (0, 255, 0), 2)

        test = center
        cv.imshow("im3", frame)
        cv.setMouseCallback("im3", coordinates)
        if cv.waitKey(30) == 27:
            break
    print("x=", center[0], "y=", center[1])
    print(
        "x=",
        round((center[0] - 332) * (0.0854)),
        "y=",
        round((422 - center[1]) * (0.0854)),
    )
    print("to" + "\n", "x=", ex, "y=", why)
    print("x=", (ex - 332) * (0.0854), "y=", (422 - why) * (0.0854))
    thex = round((ex - 332) * (0.0854))
    they = round((422 - why) * (0.0854))
    axe = round((center[0] - 332) * (0.0854))
    bhai = round((422 - center[1]) * (0.0854))
    rad = int(radius * (0.0854))
    return axe, bhai, thex, they

