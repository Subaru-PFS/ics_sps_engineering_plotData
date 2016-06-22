from math import floor, ceil, log10
import numpy as np


def transformCoord2Log(display_coord, ax, ax2, inv=False):
    xmin, xmax = ax2.get_xlim()
    ymin, ymax = ax2.get_ylim()
    pix_ymin = int(ceil(ax2.transData.transform((xmin, ymin))[1]))
    pix_ymax = int(floor(ax2.transData.transform((xmax, ymax))[1]))
    pix_xmin = int(ceil(ax2.transData.transform((xmin, ymin))[0]))
    pix_xmax = int(floor(ax2.transData.transform((xmax, ymax))[0]))

    ax_xmin, ax_xmax = ax.get_ylim()
    ax_xmin = log10(ax_xmin)
    ax_xmax = log10(ax_xmax)
    slope = (ax_xmax - ax_xmin) / (pix_ymax - pix_ymin)
    offset = (ax_xmin + ax_xmax - slope * (pix_ymax + pix_ymin)) / 2

    ax_ymin, ax_ymax = ax.get_xlim()
    slope2 = (ax_ymax - ax_ymin) / (pix_xmax - pix_xmin)
    offset2 = (ax_ymin + ax_ymax - slope2 * (pix_xmax + pix_xmin)) / 2
    if not inv:
        time = display_coord[0] * slope2 + offset2
        res = 10 ** (display_coord[1] * slope + offset)
        return [time, res]
    else:
        if display_coord[1] > 0:
            pix_x = (display_coord[0] - offset2) / slope2
            pix_y = (log10(display_coord[1]) - offset) / slope
            return [pix_x, pix_y]
        return None


def dichot(x, array, ind_inf=0, ind_sup=None):
    if ind_sup is None:
        ind_sup = len(array) - 1
    if (ind_sup - ind_inf) == 1:
        if abs(array[ind_sup] - x) > abs(array[ind_inf] - x):
            return ind_inf
        else:
            return ind_sup
    else:
        if x < array[ind_inf + (ind_sup - ind_inf) / 2]:
            return dichot(x, array, ind_inf, (ind_inf + (ind_sup - ind_inf) / 2))
        else:
            return dichot(x, array, (ind_inf + (ind_sup - ind_inf) / 2), ind_sup)


def indFinder(t0, array):
    if t0 < array[0]:
        ind = 0
    elif t0 > array[-1]:
        ind = len(array) - 1
    else:
        ind = dichot(t0, array)
    return ind
