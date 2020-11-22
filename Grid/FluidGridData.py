import taichi as ti
import taichi_glsl as ts
from abc import ABCMeta, abstractmethod
from config import EulerCFG
from utils import bufferPair, Vector, Matrix
from .CellGrid import CellGrid

@ti.data_oriented
class FluidGridData(metaclass=ABCMeta):
    """
    The abstract class for different grid type
    (cellcentered, facecentered)
    Contains data
    """

    def __init__(self, cfg: EulerCFG):
        self.cfg = cfg
        self.dim = cfg.dim

        self.calVorticity = None
        if self.dim == 2:
            self.calVorticity = self.calVorticity2D
        elif self.dim == 3:
            self.calVorticity = self.calVorticity3D

        # the distance between two neighbour when calculating divergence, vorticity
        self.inv_d = None
        # specific to grid type
        self.v = None
        self.new_v = None
        self.tmp_v = None

        # velocity divergence
        self.v_divs = CellGrid(ti.field(dtype=ti.f32, shape=cfg.res), cfg.dim, dx=ts.vecND(self.dim, self.cfg.dx),
                               o=ts.vecND(self.dim, 0.0))
        # velocity vorticity
        if self.dim == 2:
            self.v_curl = CellGrid(ti.field(dtype=ti.f32, shape=cfg.res), cfg.dim, dx=ts.vecND(self.dim, self.cfg.dx),
                                   o=ts.vecND(self.dim, 0.0))
        elif self.dim == 3:
            self.v_curl = CellGrid(ti.Vector.field(cfg.dim, dtype=ti.f32, shape=cfg.res), cfg.dim,
                                   dx=ts.vecND(self.dim, self.cfg.dx), o=ts.vecND(self.dim, 0.0))

        self.p = CellGrid(ti.field(dtype=ti.f32, shape=cfg.res), cfg.dim, dx=ts.vecND(self.dim, self.cfg.dx),
                          o=ts.vecND(self.dim, 0.0))
        self.new_p = CellGrid(ti.field(dtype=ti.f32, shape=cfg.res), cfg.dim, dx=ts.vecND(self.dim, self.cfg.dx),
                              o=ts.vecND(self.dim, 0.0))
        # here density is just for visualization, which does not involve in calculation
        self.density_bffr = CellGrid(ti.Vector.field(3, dtype=ti.f32, shape=cfg.res), cfg.dim,
                                     dx=ts.vecND(self.dim, self.cfg.dx), o=ts.vecND(self.dim, 0.0))
        self.new_density_bffr = CellGrid(ti.Vector.field(3, dtype=ti.f32, shape=cfg.res), cfg.dim,
                                         dx=ts.vecND(self.dim, self.cfg.dx), o=ts.vecND(self.dim, 0.0))
        # temperature
        self.t = CellGrid(ti.Vector.field(1, dtype=ti.f32, shape=cfg.res), cfg.dim, dx=ts.vecND(self.dim, self.cfg.dx),
                          o=ts.vecND(self.dim, 0.0))
        self.t_bffr = CellGrid(ti.Vector.field(1, dtype=ti.f32, shape=cfg.res), cfg.dim,
                               dx=ts.vecND(self.dim, self.cfg.dx), o=ts.vecND(self.dim, 0.0))
        self.t_ambient = ti.field(dtype=ti.f32, shape=[])

        self.v_pair = None
        self.p_pair = None
        self.density_pair = None
        self.t_pair = None
        # Used for advection velocity self
        # store each velocity dimension component if staggered grid
        # store velocity field for uniform grid
        self.advect_v_pairs = []

    @abstractmethod
    def calDivergence(self, vf: ti.template(), vd: ti.template()):
        """
        self-explained
        :param vf: field
        :param vd: field divergence
        :return:
        """
        pass

    @abstractmethod
    def calVorticity2D(self, vf: Matrix):
        pass

    @abstractmethod
    def calVorticity3D(self, vf: Matrix):
        pass

    @abstractmethod
    def subtract_gradient_pressure(self):
        pass

    @abstractmethod
    def materialize(self):
        """
        init some variable, especially for
        ti.field, since after materialize Taichi
        can not add more ti.field
        :return:
        """
        pass

    @abstractmethod
    def reset(self):
        """
        reset to initial time
        :return:
        """
        pass
