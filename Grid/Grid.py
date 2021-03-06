import taichi as ti
import taichi_glsl as ts
from abc import ABCMeta, abstractmethod
from .Sampler import LinearSampler2D, LinearSampler3D
from enum import Enum, IntEnum


class GRIDTYPE(IntEnum):
    CELL_GRID = 0
    FACE_GRID = 1
    Bimocq_GRID = 2

    def __init__(self, *args):
        super().__init__()
        self.map = ['UniformGrid', 'MacGrid', 'MacGrid']

    def __str__(self):
        return self.map[self.value]


@ti.data_oriented
class Grid(metaclass=ABCMeta):
    """
    the abstract class for the wrapper
     that stores the data
    """

    def __init__(self,
                 dim,
                 dx=ts.vec3(1.0),
                 o=ts.vec3(0.0)):
        """

        :param dim:  dimension of the grid, expected to be 2 or 3
        :param dx:  the physical length of a cell
        :param o: offset on grid
        """
        assert (dim == dx.n)
        assert (dim == o.n)

        self.dim = dim
        # should not be zero
        # or too small
        self.dx = dx
        self.inv_dx = 1.0 / self.dx
        self.o = o

        self.GRID_TYPE = None

        self._sampler = None
        if dim == 2:
            self._sampler = LinearSampler2D()
        elif dim == 3:
            self._sampler = LinearSampler3D()
        else:
            raise NotImplemented

    @abstractmethod
    def __getitem__(self, I):
        pass

    @abstractmethod
    def __setitem__(self, I, value):
        # actually this would never be called in kernel
        # since Taichi would always call this.__getitem__().assign()
        pass

    # @property
    # def shape(self):
    #     pass

    @abstractmethod
    def fill(self, value):
        pass

    @ti.pyfunc
    def getW(self, G):
        """
        get world position from Grid Coordinate
        :param G:
        :return:
        """
        return (G + self.o) * self.dx

    @ti.pyfunc
    def getG(self, W):
        """

        :param W: physical position
        :return:
        """
        return W * self.inv_dx - self.o

    @abstractmethod
    def interpolate(self, P):
        """
        self explained, mainly called in advection
        :param P:
        :return:
        """
        pass

    @abstractmethod
    def copy(self, src):
        """
        copy src data to myself
        :param src:
        :return:
        """
        pass

    @abstractmethod
    def subself(self, src):
        """
        self = src - self
        helper for Bimocq
        :param src:
        :return:
        """
        pass

    # @abstractmethod
    # def clampPos(self, P):
    #     """
    #     clamp world pos and output clamped space
    #     mainly used in Bimocq
    #     :param P: world pos
    #     :return:
    #     """
    #     pass

    @ti.func
    def GisNearBoundary(self, g, howNear):
        """
        Assume g is cell center
        :param g:
        :param howNear:
        note: Taichi use -1 as True
        :return:
        """
        # print("<", g, ts.vecND(self.dim, howNear), g < ts.vecND(self.dim, howNear))
        # print(">", g, ti.Vector(self.shape) - howNear, g >= ti.Vector(self.shape) - howNear)
        return ((g < ts.vecND(self.dim, howNear)).sum() > 0) or ((g >= ti.Vector(self.shape) - howNear).sum() > 0)

    @ti.func
    def WisNearBoundary(self, w, howNear):
        """
        whether a World pos is  near the out boundary
        assume cell in the middle
        :param w: position in World
        :param howNear:
        :return:
        """
        g = ti.cast((w - self.o) / self.dx, ti.i32)
        return self.GisNearBoundary(g, howNear)
