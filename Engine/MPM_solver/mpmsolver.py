import taichi as ti
import taichi_glsl as ts
import numpy as np
from abc import ABCMeta, abstractmethod
from config.CFG_wrapper import mpmCFG, MaType
from utils import Vector, Float
from DataLayout.MPM import mpmLayout

"""
ref : 
    taichi elements
    mpm2d.py
"""


@ti.data_oriented
class MPMSolver(metaclass=ABCMeta):
    def __init__(self, cfg: mpmCFG):
        self.cfg = cfg

        self.dim = cfg.dim

        self.Layout = mpmLayout(cfg)
        self.curFrame = 0
        pass

    def materialize(self):
        # initial the ti.field
        self.Layout.materialize()
        self.Layout.init_cube()

    def substep(self, dt: Float):
        # self.print_property(34)
        self.Layout.G2zero()
        # self.print_property(35)
        self.Layout.P2G(dt)
        # self.print_property(37)
        self.Layout.G_Normalize_plus_Gravity(dt)
        # self.print_property(39)
        self.Layout.G_boundary_condition()
        # self.print_property(41)
        self.Layout.G2P(dt)
        # self.print_property(43)

    @ti.kernel
    def print_property(self, prefix: ti.template(), v:ti.template()):
        p_x = ti.static(self.Layout.p_x)
        for P in p_x:
            print(prefix, v[P])
            # assert(ts.isnan(p_x[P][0]))
            # assert (ts.isnan(p_x[P][1]))
            # print(p_x[P])

    def step(self, print_stat=False):
        """
        Call once in each frame
        :return:
        """
        # TODO change dt
        T = 0.0
        sub_dt = self.cfg.substep_dt

        # while T < self.cfg.dt:
        #     if T + sub_dt > self.cfg.dt:
        #         sub_dt = self.cfg.dt - T
        #
        #     self.substep(sub_dt)

        # print(self.cfg.dt // sub_dt)
        for _ in range(int(self.cfg.dt // sub_dt)):
            self.substep(sub_dt)

        if print_stat:
            ti.kernel_profiler_print()
            try:
                ti.memory_profiler_print()
            except:
                pass
            print(f'num particles={self.Layout.n_particles[None]}')
        self.curFrame += 1
        # print("frame {}".format(self.curFrame))

    def reset(self):
        """
        restart the whole process
        :return:
        """
        # TODO
        self.Layout.init_cube()

        self.curFrame = 0

    # def add_cube(self,
    #              l_b: Vector,
    #              cube_size: Vector,
    #              mat: MaType,
    #              color=0xFFFFFF,
    #              sample_density=None,
    #              velocity=None):
    #     if sample_density is None:
    #         sample_density = 2 ** self.dim
    #
    #     vol = 1
    #     for d in range(self.dim):
    #         vol *= cube_size[d]
    #     num_new_particles = int(sample_density * vol / self.cfg.dx ** self.dim + 1)
    #     assert self.Layout.n_particles[
    #                None] + num_new_particles <= self.cfg.max_n_particle
    #
    #     self.Layout.source_bound[0] = l_b
    #     self.Layout.source_bound[1] = cube_size
    #
    #     if velocity is None:
    #         self.Layout.source_velocity[None] = ts.vecND(self.dim, 0.0)
    #     else:
    #         self.Layout.source_velocity[None] = velocity
    #
    #     self.Layout.n_particles[None] += num_new_particles
