import matplotlib.pyplot as plt
from ctypes import *
import numpy as np
from matplotlib.widgets import  RectangleSelector
import matplotlib.patches as patch
import random
import numpy as np
from deap import base
from deap import creator
from deap import tools
import time
from scipy.interpolate import interp1d
import os

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
    print('set dwBufferSize:', dwBufferSize)

    dwNumberOfByteTrans = c_uint32()
    # dwNumberOfByteTrans.value = 12 * dwBufferSize
    # dwNumberOfByteTrans.value = 0

    dwFrameNo = c_uint32()
    # pbyteraw = np.zeros((im_width, im_height), dtype=np.uint8)
    pbyteraw = np.zeros((im_height, im_width), dtype=np.uint8)
    dwMilliseconds = 3000
    # triggermode = 2049
    triggermode = 0
    threshhold = 0

    #  set up camera capture
    mydll = windll.LoadLibrary('StTrgApi.dll')
    hCamera = mydll.StTrg_Open()
    print('hCamera id:', hCamera)

    mydll.StTrg_SetTransferBitsPerPixel(hCamera, dwTransferBitsPerPixel)
    mydll.StTrg_SetScanMode(hCamera, 0, 0, 0, 0, 0)
    mydll.StTrg_SetGain(hCamera, 0)

    # mydll.StTrg_SetDigitalGain(hCamera, 64)
    mydll.StTrg_SetDigitalGain(hCamera, 64)

    mydll.StTrg_SetExposureClock(hCamera, 200000)
    mydll.StTrg_SetClock(hCamera, 0, 0)
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
        image = take_image()
        b.set_data(image)
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
        image = take_image()
        b.set_data(image)
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
    image = take_image()

    # print('Frame:' + str(dwFrameNo.value))


    # pbyteraw[:, :] = np.zeros(np.shape(pbyteraw))
    # pbyteraw[100:200, 100:200] = 10

    b = ax.imshow(image, cmap='jet')
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


def take_image():
    # print('image taken')
    mydll.StTrg_TakeRawSnapShot(hCamera, pbyteraw.ctypes.data_as(POINTER(c_int8)),
                                dwBufferSize, pointer(dwNumberOfByteTrans), pointer(dwFrameNo), dwMilliseconds)
    image = np.rot90(pbyteraw, 1)
    # print('max:', np.max(image))

    return image


def draw_inner_and_outer():
    global b
    fig, ax = plt.subplots(1)
    # take first image
    image = take_image()
    # print('Frame:' + str(dwFrameNo.value))
    b = ax.imshow(image, cmap='jet')
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


def get_p_number():
    return random.random() * 2 * np.pi


def params_to_daz(wl_send, phi_send):
    # print('sending to dazzler')
    home = os.getcwd()
    # print(home)
    os.chdir(r'\\CREOL-FAST-01\data')
    # print(os.getcwd())
    with open('pythonwavefile.txt', 'w') as file:
        file.write('phase=2\n#phase')
        file.write('first line')
        i = 0
        while i < len(wl_send):

            file.write('\n')
            file.write("{:.2f}".format(wl_send[i]))
            file.write('\t')
            file.write("{:.4f}".format(phi_send[i]))
            i += 1
    with open('requesttest.txt', 'w') as file:
        proj = r'C:\dazzler\data\pythonwavefile.txt'
        file.write(proj)
        time.sleep(0.05)
    os.chdir(home)
    time.sleep(1)


def evalOneMax(individual):
    # the goal ('fitness') function to be maximized
    # print('\n EVALUATING \n')

    # calculate phi_send
    phi_nodes = individual[:]
    phi_func = interp1d(wavelength_nodes, phi_nodes, kind='cubic')
    # print('individual: ', individual)
    # print('wavelength nodes: ', wavelength_nodes)

    # send parameters to dazzler
    params_to_daz(wl_send=wavelength, phi_send=phi_func(wavelength))

    # take image
    image = take_image()

    # calculate ratio
    inner = image[int(inner_rectangle.y1):int(inner_rectangle.y2), int(inner_rectangle.x1):int(inner_rectangle.x2)]
    outer = image[int(outer_rectangle.y1):int(outer_rectangle.y2), int(outer_rectangle.x1):int(outer_rectangle.x2)]
    ratio = inner.sum() / outer.sum()

    # plot image
    ax2.cla()
    ax2.plot(wavelength, phi_func(wavelength))
    ax2.set_title('Applied Phase')
    ax2.yaxis.tick_right()
    ax2.yaxis.set_label_position("right")
    ax2.set_ylabel('phi [rad]')
    ax2.set_xlabel('wavelength [nm]')
    ax2.set_xlim(lambdamin, lambdamax)
    ax1.cla()
    ax1.imshow(image, cmap='jet')
    ax1.set_title('Camera Image')
    ax1.set_ylabel('y pixel')
    ax1.set_xlabel('x pixel')
    ax1.text(0, 100, 'Ratio: ' + str(np.round(ratio, 5)), color='black', backgroundcolor='yellow')
    ax1.add_patch(patch.Rectangle((inner_rectangle.x1, inner_rectangle.y1),
                                 inner_rectangle.x2 - inner_rectangle.x1,
                                 inner_rectangle.y2 - inner_rectangle.y1,
                                 linewidth=2, edgecolor='r', facecolor='none'))
    ax1.add_patch(patch.Rectangle((outer_rectangle.x1, outer_rectangle.y1),
                                 outer_rectangle.x2 - outer_rectangle.x1,
                                 outer_rectangle.y2 - outer_rectangle.y1,
                                 linewidth=2, edgecolor='y', facecolor='none'))

    plt.show()
    plt.pause(0.001)
    return ratio,
    # return sum(individual),


def setup_ga():
    global toolbox
    global creator

    creator.create("FitnessMax", base.Fitness, weights=(1.0,))
    creator.create("Individual", list, fitness=creator.FitnessMax)

    toolbox = base.Toolbox()

    # Attribute generator
    #                      define 'attr_bool' to be an attribute ('gene')
    #                      which corresponds to integers sampled uniformly
    #                      from the range [0,1] (i.e. 0 or 1 with equal
    #                      probability)
    # toolbox.register("attr_bool", random.randint, 0, 10)
    toolbox.register("attr_bool", get_p_number)

    # Structure initializers
    #                         define 'individual' to be an individual
    #                         consisting of 100 'attr_bool' elements ('genes')
    toolbox.register("individual", tools.initRepeat, creator.Individual,
                     toolbox.attr_bool, number_of_nodes)

    # define the population to be a list of individuals
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)

    # ----------
    # Operator registration
    # ----------
    # register the goal / fitness function
    toolbox.register("evaluate", evalOneMax)

    # register the crossover operator
    toolbox.register("mate", tools.cxTwoPoint)

    # register a mutation operator with a probability to
    # flip each attribute/gene of 0.05
    toolbox.register("mutate", tools.mutShuffleIndexes, indpb=0.2)


    # operator for selecting individuals for breeding the next
    # generation: each individual of the current generation
    # is replaced by the 'fittest' (best) of three individuals
    # drawn randomly from the current generation.
    toolbox.register("select", tools.selTournament, tournsize=3)


def run_ga():
    # random.seed(64)

    # create an initial population of 300 individuals (where
    # each individual is a list of integers)
    pop = toolbox.population(n=population_num)

    # CXPB  is the probability with which two individuals
    #       are crossed
    #
    # MUTPB is the probability for mutating an individual
    CXPB, MUTPB, MUTPB2 = 0.2, 0.2, 0.5
    # CXPB, MUTPB, MUTPB2 = 0, 0, 1


    print("Start of evolution")

    # Evaluate the entire population
    # print(pop)
    fitnesses = list(map(toolbox.evaluate, pop))
    for ind, fit in zip(pop, fitnesses):
        # print(ind)
        # print(fit)
        ind.fitness.values = fit
    # print('initial population: ', pop)
    # for ind in pop:
    #     print(max(ind))
    print("  Evaluated %i individuals" % len(pop))

    # Extracting all the fitnesses of
    fits = [ind.fitness.values[0] for ind in pop]

    # Variable keeping track of the number of generations
    g = 0

    # Begin the evolution
    # while max(fits) < 100 and g < 100:
    while g <= generations:
        # A new generation
        g = g + 1
        print("-- Generation %i --" % g)

        # Select the next generation individuals
        offspring = toolbox.select(pop, len(pop))
        # Clone the selected individuals
        offspring = list(map(toolbox.clone, offspring))

        # Apply crossover and mutation on the offspring
        for child1, child2 in zip(offspring[::2], offspring[1::2]):

            # cross two individuals with probability CXPB
            if random.random() < CXPB:
                toolbox.mate(child1, child2)

                # fitness values of the children
                # must be recalculated later
                del child1.fitness.values
                del child2.fitness.values

        for mutant in offspring:

            # mutate an individual with probability MUTPB
            if random.random() < MUTPB:
                toolbox.mutate(mutant)
                del mutant.fitness.values

        for mutant in offspring:

            # mutate an individual with probabililty MUTPB2
            if random.random() < MUTPB2:
                tools.mutGaussian(mutant, mu=0.0, sigma=0.2, indpb=0.2)
                del mutant.fitness.values


        # print('offspring : ', offspring)

        # Evaluate the individuals with an invalid fitness
        invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
        # print('invalid ind: ', invalid_ind)
        fitnesses = map(toolbox.evaluate, invalid_ind)
        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit

        print("  Evaluated %i individuals" % len(invalid_ind))

        # The population is entirely replaced by the offspring
        pop[:] = offspring

        # Gather all the fitnesses in one list and print the stats
        fits = [ind.fitness.values[0] for ind in pop]

        length = len(pop)
        mean = sum(fits) / length
        sum2 = sum(x * x for x in fits)
        std = abs(sum2 / length - mean ** 2) ** 0.5

        print("  Min %s" % min(fits))
        print("  Max %s" % max(fits))
        print("  Avg %s" % mean)
        print("  Std %s" % std)

    print("-- End of (successful) evolution --")

    best_ind = tools.selBest(pop, 1)[0]
    print("Best individual is %s, %s" % (best_ind, best_ind.fitness.values))


if __name__ == '__main__':
    # genetic algorithm parameters
    write_dazzler = True
    number_of_nodes = 20
    wavelength_points = 300
    lambdamin = 670
    lambdamax = 930
    population_num = 5
    generations = 100


    setup_camera()
    get_rectangle()
    get_rectangle()
    draw_inner_and_outer()

    fig, (ax1, ax2) = plt.subplots(ncols=2, figsize=(8,4))
    plt.ion()
    wavelength_nodes = np.linspace(lambdamin, lambdamax, number_of_nodes)
    wavelength = np.linspace(lambdamin, lambdamax, wavelength_points)

    setup_ga()
    run_ga()







# while True:
#
#     # take first image
#     image = take_image()
#     inner = image[int(inner_rectangle.y1):int(inner_rectangle.y2), int(inner_rectangle.x1):int(inner_rectangle.x2)]
#     outer = image[int(outer_rectangle.y1):int(outer_rectangle.y2), int(outer_rectangle.x1):int(outer_rectangle.x2)]
#     ratio = inner.sum() / outer.sum()
#
#     ax1.cla()
#     ax1.imshow(image, cmap='jet')
#     ax1.set_title('Camera Image')
#     ax1.set_ylabel('y pixel')
#     ax1.set_xlabel('x pixel')
#     ax1.text(0, 100, 'Ratio: ' + str(np.round(ratio, 5)), color='black', backgroundcolor='yellow')
#
#     # add rectangle patches
#     ax1.add_patch(patch.Rectangle((inner_rectangle.x1, inner_rectangle.y1),
#                                  inner_rectangle.x2 - inner_rectangle.x1,
#                                  inner_rectangle.y2 - inner_rectangle.y1,
#                                  linewidth=2, edgecolor='r', facecolor='none'))
#
#     ax1.add_patch(patch.Rectangle((outer_rectangle.x1, outer_rectangle.y1),
#                                  outer_rectangle.x2 - outer_rectangle.x1,
#                                  outer_rectangle.y2 - outer_rectangle.y1,
#                                  linewidth=2, edgecolor='y', facecolor='none'))
#
#     phi_nodes = 2 * np.pi * np.random.rand(number_of_nodes)
#
#     f = interp1d(wavelength_nodes, phi_nodes, kind='cubic')
#
#     ax2.cla()
#     ax2.plot(wavelength, f(wavelength))
#     ax2.set_title('Applied Phase')
#     ax2.yaxis.tick_right()
#     ax2.yaxis.set_label_position("right")
#     ax2.set_ylabel('phi [rad]')
#     ax2.set_xlabel('wavelength [nm]')
#     # ax2.set_ylim(0, 2.2 * np.pi)
#     ax2.set_xlim(lambdamin, lambdamax)
#
#
#     plt.show()
#     plt.pause(0.001)
#     time.sleep(1)











