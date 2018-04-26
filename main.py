import matplotlib.pyplot as plt
from ctypes import *
import numpy as np
from matplotlib.widgets import  RectangleSelector
import matplotlib.patches as patch
import time
from scipy.interpolate import interp1d

inner_rectangle = None
outer_rectangle = None


class Coordinates:
    def __init__(self):
        self.x1 = None
        self.y1 = None
        self.x2 = None
        self.y2 = None


def setup_camera():
    global mydll
    global hCamera
    global pbyteraw
    global dwBufferSize
    global dwNumberOfByteTrans
    global dwFrameNo
    global dwMilliseconds
    global threshhold

    # create parameters for camera
    dwTransferBitsPerPixel = 1
    im_height = 1200
    im_width = 1600
    dwBufferSize = im_height * im_width
    dwNumberOfByteTrans = c_uint32()
    dwFrameNo = c_uint32()
    pbyteraw = np.zeros((im_height, im_width), dtype=np.uint8)
    dwMilliseconds = 3000
    # triggermode = 2049
    triggermode = 0

    # set threshold for background reduction
    threshhold = 0


    #  set up camera capture
    mydll = windll.LoadLibrary('StTrgApi.dll')
    hCamera = mydll.StTrg_Open()
    print('hCamera id:', hCamera)

    mydll.StTrg_SetTransferBitsPerPixel(hCamera, dwTransferBitsPerPixel)

    # mydll.StTrg_SetScanMode(hCamera, 16, 0, 0, 0, 0)
    mydll.StTrg_SetScanMode(hCamera, 0, 0, 0, 0, 0)
    mydll.StTrg_SetGain(hCamera, 0)
    mydll.StTrg_SetDigitalGain(hCamera, 64)

    # mydll.StTrg_GetClock(hCamera, pointer(pdwClockMode), pointer(pdwClock))
    # clock1 = pdwClock.value

    # pdwExposureValue = c_uint32()
    # mydll.StTrg_GetExposureClock(hCamera, pointer(pdwExposureValue))


    # ms = 0.2  # Exposure time
    ms = 200
    # mydll.StTrg_SetExposureClock(hCamera, 7363636)
    # mydll.StTrg_SetExposureClock(hCamera, 0)
    # mydll.StTrg_SetExposureMode(hCamera, 1)


    pdwClockMode = c_uint32()
    pdwClock = c_uint32()


    # mydll.StTrg_GetClock(hCamera, pointer(pdwClockMode), pointer(pdwClock))
    # print('pdwclock: ' + str(pdwClock.value))


    # mydll.StTrg_SetClock(hCamera, 2, 0)
    # mydll.StTrg_SetClock(hCamera, 0, 0)


    # mydll.StTrg_GetClock(hCamera, pointer(pdwClockMode), pointer(pdwClock))
    # print('pdwclock: ' + str(pdwClock.value))


    # mydll.StTrg_GetExposureClock(hCamera, pointer(pdwExposureValue))


    mydll.StTrg_SetTriggerMode(hCamera, triggermode)
    mydll.StTrg_SetTriggerTiming(hCamera, 0, 0)
    mydll.StTrg_SetIOPinDirection(hCamera, 0)
    mydll.StTrg_SetIOPinPolarity(hCamera, 0)
    mydll.StTrg_SetIOPinMode(hCamera, 0, 16)


def after_selection():
    global inner_rectangle
    global outer_rectangle
    # print('next')
    # print(coord.x1)
    # print(coord.y1)
    # print(coord.x2)
    # print(coord.x2)
    if inner_rectangle:
        # draw outer rectangle
        # print('coord', coord.x1)
        if coord.x1:
            outer_rectangle = Coordinates()
            outer_rectangle.x1 = coord.x1
            outer_rectangle.y1 = coord.y1
            outer_rectangle.x2 = coord.x2
            outer_rectangle.y2 = coord.y2

    else:
        # draw inner rectangle:
        if coord.x1:
            inner_rectangle = Coordinates()
            inner_rectangle.x1 = coord.x1
            inner_rectangle.y1 = coord.y1
            inner_rectangle.x2 = coord.x2
            inner_rectangle.y2 = coord.y2

    plt.close()


def toggle_selector(event):
    # print(' Key pressed.')
    if event.key in ['p'] and toggle_selector.rs.active:
        # print(' RectangleSelector deactivated.')
        toggle_selector.rs.set_active(False)
        toggle_selector.rs.set_visible(False)
        after_selection()

    if event.key in ['r'] and toggle_selector.rs.active:
        mydll.StTrg_TakeRawSnapShot(hCamera, pbyteraw.ctypes.data_as(POINTER(c_int8)), dwBufferSize, pointer(dwNumberOfByteTrans), pointer(dwFrameNo), dwMilliseconds)
        pbyteraw[pbyteraw < threshhold] = 0
        b.set_data(pbyteraw)
        # print('new image')
        # print('Frame:' + str(dwFrameNo.value))
        plt.pause(0.001)


def goodorbad(event):
    global inner_rectangle
    global outer_rectangle

    if event.key in ['y']:
        # print('good')
        plt.close()

    if event.key in ['n']:
        # print('bad')
        plt.close()
        inner_rectangle = None
        outer_rectangle = None
        get_rectangle()
        get_rectangle()
        draw_inner_and_outer()

    if event.key in ['r']:
        # print('refrsh')
        mydll.StTrg_TakeRawSnapShot(hCamera, pbyteraw.ctypes.data_as(POINTER(c_int8)), dwBufferSize, pointer(dwNumberOfByteTrans), pointer(dwFrameNo), dwMilliseconds)
        pbyteraw[pbyteraw < threshhold] = 0
        b.set_data(pbyteraw)
        # print('new image')
        # print('Frame:' + str(dwFrameNo.value))
        plt.pause(0.001)


def line_select_callback(eclick, erelease):

    global coord
    x1, y1 = eclick.xdata, eclick.ydata
    x2, y2 = erelease.xdata, erelease.ydata
    # print('x1: ' + str(x1) + ' y1: ' + str(y1))
    # print('x2: ' + str(x2) + ' y2: ' + str(y2))
    coord.x1 = x1
    coord.x2 = x2
    coord.y1 = y1
    coord.y2 = y2


def get_rectangle():
    global coord
    global b

    coord = Coordinates()

    fig, ax = plt.subplots(1)

    # take first image
    mydll.StTrg_TakeRawSnapShot(hCamera, pbyteraw.ctypes.data_as(POINTER(c_int8)),
                                dwBufferSize, pointer(dwNumberOfByteTrans), pointer(dwFrameNo), dwMilliseconds)

    # print('Frame:' + str(dwFrameNo.value))
    pbyteraw[pbyteraw < threshhold] = 0

    # pbyteraw[:, :] = np.zeros(np.shape(pbyteraw))
    # pbyteraw[100:200, 100:200] = 10

    b = ax.imshow(pbyteraw, cmap='jet')
    if inner_rectangle:
        # print("draw inner rectangle")
        # print('inner_rectangle:', inner_rectangle)
        ax.add_patch(patch.Rectangle((inner_rectangle.x1, inner_rectangle.y1),
                                     inner_rectangle.x2-inner_rectangle.x1,
                                     inner_rectangle.y2-inner_rectangle.y1,
                                     linewidth=2, edgecolor='r', facecolor='none'))
        ax.text(0, 100, 'Draw the OUTER rectangle, then press [p] to continue\n'
                       'Press [r] to refresh image', color='black', backgroundcolor='yellow')
    else:
        ax.text(0, 100, 'Draw the INNER rectangle, then press [p] to continue\n'
                       'Press [r] to refresh image', color='black', backgroundcolor='yellow')


    toggle_selector.rs = RectangleSelector(ax, line_select_callback,
                           drawtype='box', useblit=False, button=[1],
                           minspanx=5, minspany=5, spancoords='pixels',
                           interactive=True)



    plt.connect('key_press_event', toggle_selector)
    plt.show()


def draw_inner_and_outer():
    global b
    fig, ax = plt.subplots(1)
    # take first image
    mydll.StTrg_TakeRawSnapShot(hCamera, pbyteraw.ctypes.data_as(POINTER(c_int8)),
                                dwBufferSize, pointer(dwNumberOfByteTrans), pointer(dwFrameNo), dwMilliseconds)

    # print('Frame:' + str(dwFrameNo.value))
    pbyteraw[pbyteraw < threshhold] = 0
    b = ax.imshow(pbyteraw, cmap='jet')
    if inner_rectangle:
        ax.add_patch(patch.Rectangle((inner_rectangle.x1, inner_rectangle.y1),
                                     inner_rectangle.x2 - inner_rectangle.x1,
                                     inner_rectangle.y2 - inner_rectangle.y1,
                                     linewidth=2, edgecolor='r', facecolor='none'))
    if outer_rectangle:
        ax.add_patch(patch.Rectangle((outer_rectangle.x1, outer_rectangle.y1),
                                     outer_rectangle.x2 - outer_rectangle.x1,
                                     outer_rectangle.y2 - outer_rectangle.y1,
                                     linewidth=2, edgecolor='y', facecolor='none'))

    # print('final thing')
    ax.text(0, 1100, 'INNER', color='r', backgroundcolor='white')
    ax.text(0, 1180, 'OUTER', color='y', backgroundcolor='white')

    # print('final thing')
    ax.text(0, 100, 'Press [y] to continue\n'
                    'Press [n] to start over\n'
                    'Press [r] to refresh image', color='black', backgroundcolor='yellow')
    plt.connect('key_press_event', goodorbad)
    plt.show()

# genetic algorithm parameters
number_of_nodes = 20
wavelength_points = 300
lambdamin = 700
lambdamax = 900


setup_camera()
get_rectangle()
get_rectangle()
draw_inner_and_outer()

fig, (ax1, ax2) = plt.subplots(ncols=2, figsize=(8,4))
plt.ion()
plots_initialized = False
axis2_set = False
wavelength_nodes = None
wavelength = None
while True:
    if not plots_initialized:
        # setup plots
        wavelength_nodes = np.linspace(lambdamin, lambdamax, number_of_nodes)
        wavelength = np.linspace(lambdamin, lambdamax, wavelength_points)
        plots_initialized = True

    # take first image
    mydll.StTrg_TakeRawSnapShot(hCamera, pbyteraw.ctypes.data_as(POINTER(c_int8)),
                                dwBufferSize, pointer(dwNumberOfByteTrans), pointer(dwFrameNo), dwMilliseconds)

    inner = pbyteraw[int(inner_rectangle.y1):int(inner_rectangle.y2), int(inner_rectangle.x1):int(inner_rectangle.x2)]
    outer = pbyteraw[int(outer_rectangle.y1):int(outer_rectangle.y2), int(outer_rectangle.x1):int(outer_rectangle.x2)]
    ratio = inner.sum() / outer.sum()

    # # noise reduction
    # pbyteraw[pbyteraw < threshhold] = 0
    ax1.cla()
    ax1.imshow(pbyteraw, cmap='jet')
    ax1.set_title('Camera Image')
    ax1.text(0, 100, 'Ratio: ' + str(np.round(ratio, 5)), color='black', backgroundcolor='yellow')

    # add rectangle patches
    ax1.add_patch(patch.Rectangle((inner_rectangle.x1, inner_rectangle.y1),
                                 inner_rectangle.x2 - inner_rectangle.x1,
                                 inner_rectangle.y2 - inner_rectangle.y1,
                                 linewidth=2, edgecolor='r', facecolor='none'))

    ax1.add_patch(patch.Rectangle((outer_rectangle.x1, outer_rectangle.y1),
                                 outer_rectangle.x2 - outer_rectangle.x1,
                                 outer_rectangle.y2 - outer_rectangle.y1,
                                 linewidth=2, edgecolor='y', facecolor='none'))

    phi_nodes = 2 * np.pi * np.random.rand(number_of_nodes)

    f = interp1d(wavelength_nodes, phi_nodes, kind='cubic')

    ax2.cla()
    ax2.plot(wavelength, f(wavelength))
    ax2.set_title('Applied Phase')
    ax2.yaxis.tick_right()
    ax2.yaxis.set_label_position("right")
    ax2.set_ylabel('phi [rad]')
    ax2.set_xlabel('wavelength [nm]')
    # ax2.set_ylim(0, 2.2 * np.pi)
    ax2.set_xlim(lambdamin, lambdamax)


    plt.show()
    plt.pause(0.001)
    time.sleep(1)











