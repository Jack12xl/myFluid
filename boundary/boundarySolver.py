import taichi as ti
import taichi_glsl as ts
from abc import ABCMeta, abstractmethod
from DataLayout.Euler import collocatedGridData
from utils import Vector, Matrix
from config import PixelType
from geometry import Collider
from typing import List
from Grid import CellGrid
from Emitter import SquareEmitter


# ref : https://github.com/JYLeeLYJ/Fluid-Engine-Dev-on-Taichi/blob/master/src/python/Eulerian_method.py
class GridBoudaryConditionSolver(metaclass=ABCMeta):
    """
    solve boundary condition and manager C
    """

    def __init__(self, cfg, grid: collocatedGridData):
        self.cfg = cfg
        self.grid = grid

        self.collider_sdf_field = CellGrid(ti.field(dtype=ti.f32, shape=self.cfg.res), cfg.dim,
                                           dx=ts.vecND(self.cfg.dim, self.cfg.dx),
                                           o=ts.vecND(self.cfg.dim, 0.0))
        self.collider_velocity_field = CellGrid(ti.Vector.field(cfg.dim, dtype=ti.f32, shape=self.cfg.res), cfg.dim,
                                                dx=ts.vecND(self.cfg.dim, self.cfg.dx),
                                                o=ts.vecND(self.cfg.dim, 0.0))
        self.collider_marker_field = CellGrid(ti.field(dtype=ti.int32, shape=self.cfg.res), cfg.dim,
                                              dx=ts.vecND(self.cfg.dim, self.cfg.dx),
                                              o=ts.vecND(self.cfg.dim, 0.0))

        self.marker_field = CellGrid(ti.field(dtype=ti.i32, shape=self.cfg.res), cfg.dim,
                                     dx=ts.vecND(self.cfg.dim, self.cfg.dx),
                                     o=ts.vecND(self.cfg.dim, 0.0))
        self.marker_bffr_field = CellGrid(ti.field(dtype=ti.i32, shape=self.cfg.res), cfg.dim,
                                          dx=ts.vecND(self.cfg.dim, self.cfg.dx),
                                          o=ts.vecND(self.cfg.dim, 0.0))
        self.colliders = self.cfg.Colliders

    @ti.kernel
    def kern_update_marker(self):
        # TODO support more type
        for I in ti.grouped(self.marker_field.field):
            if self.collider_sdf_field[I] <= 0.0:
                # in collider
                self.marker_field[I] = int(PixelType.Collider)
            else:
                self.marker_field[I] = int(PixelType.Liquid)

    def step_update_sdfs(self, colliders: List[Collider]):
        self.collider_sdf_field.fill(1e8)
        self.collider_velocity_field.fill(ts.vecND(self.cfg.dim, 0.0))
        for idx, cllider in enumerate(colliders):
            self.kern_update_collid(idx, cllider)


    @ti.kernel
    def kern_update_collid(self, idx: ti.int32, collid: ti.template()):
        """
        update the sdf and velocity
        :param idx:
        :param collid:
        :return:
        """
        sdf = ti.static(self.collider_sdf_field)
        vf = ti.static(self.collider_velocity_field)
        cmf = ti.static(self.collider_marker_field)
        for I in ti.grouped(sdf.field):
            if collid.is_inside_collider(I):
                cmf[I] = idx
                sdf[I] = ti.min(sdf[I], collid.implicit_surface.signed_distance(I))
                vf[I] = collid.surfaceshape.velocity_at_world_point(I)

    def ApplyBoundaryCondition(self):
        if self.colliders:
            self.kernBoundaryCondition()

    @ti.kernel
    def updateEmitterMark(self, emitter: ti.template()):
        # TODO support multiple shape emitter
        l_b = emitter.t.translation - emitter.t.localScale
        r_u = emitter.t.translation + emitter.t.localScale

        shape = ti.Vector(self.cfg.res)

        l_b = ts.clamp(l_b, 0, shape - 1)
        r_u = ts.clamp(r_u, 0, shape - 1)

        bbox = [(int(l_b[i]), int(r_u[i]) + 1) for i in range(len(l_b))]
        for I in ti.grouped(ti.ndrange(*bbox)):
            self.marker_field[I] = int(PixelType.Emitter)

    @abstractmethod
    def kernBoundaryCondition(self):
        pass

    @abstractmethod
    def reset(self):
        pass


@ti.data_oriented
class StdGridBoundaryConditionSolver(GridBoudaryConditionSolver):
    def __init__(self, cfg, grid: collocatedGridData):
        super(StdGridBoundaryConditionSolver, self).__init__(cfg, grid)

    @ti.kernel
    def kernBoundaryCondition(self):
        # no flux
        # slip
        for I in ti.grouped(self.grid.v.field):
            if self.collider_sdf_field[I] < ti.static(0.0):
                collider_vel = self.collider_velocity_field[I]
                vel = self.grid.v[I]

                collid_idx = self.collider_marker_field[I]
                normal = ti.Vector([0.0, 0.0])
                for i in ti.static(range(len(self.colliders))):
                    if i == collid_idx:
                        normal = self.colliders[i].surfaceshape.closest_normal(I)
                # normal = self.colliders[collid_idx].surfaceshape.closest_normal(I)
                # normal = self.colliders[0].surfaceshape.closest_normal(I)

                if normal.norm() > 0:
                    vel_r = vel - collider_vel
                    self.grid.v[I] = vel_r - vel_r.dot(normal) * normal
                else:
                    self.grid.v[I] = collider_vel

    @ti.pyfunc
    def reset(self):
        for collid in self.colliders:
            collid.reset()
