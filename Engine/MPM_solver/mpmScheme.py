import taichi as ti
import taichi_glsl as ts
from abc import ABCMeta, abstractmethod
from config.CFG_wrapper import mpmCFG
from utils import Vector, Float
from DataLayout.MPM import mpmLayout

"""
ref : 
    taichi elements
    mpm2d.py
"""



@ti.data_oriented
class mpmScheme(metaclass=ABCMeta):
    def __init__(self, cfg: mpmCFG):
        self.cfg = cfg

        self.dim = cfg.dim

        self.Layout = mpmLayout(cfg)
        self.curFrame = 0
        pass

    def materialize(self):
        # initial the ti.field
        self.Layout.materialize()
        pass

    def substep(self, dt: Float):
        self.Layout.grid2zero()


        pass

    def step(self):
        for _ in range(int(2e-3 // self.cfg.dt)):
            self.substep(self.cfg.dt)
        self.curFrame += 1

    def reset(self):
        """
        restart the whole process
        :return:
        """
        self.materialize()
        self.curFrame = 0