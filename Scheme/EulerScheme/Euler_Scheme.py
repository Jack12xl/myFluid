from Grid import collocatedGridData
import taichi as ti
import taichi_glsl as ts
import numpy as np
from config import VisualizeEnum, SceneEnum, SchemeType
from boundary import StdGridBoundaryConditionSolver
from config import PixelType
from abc import ABCMeta, abstractmethod
from GridEmitter import ForceEmitter
from utils import cmapper

@ti.data_oriented
class EulerScheme(metaclass=ABCMeta):
    def __init__(self, cfg, ):
        self.cfg = cfg
        self.grid = collocatedGridData(cfg)

        self.clr_bffr = ti.Vector.field(3, dtype=ti.float32, shape=cfg.res)
        self.advection_solver = self.cfg.advection_solver(cfg, self.grid)
        self.projection_solver = self.cfg.projection_solver(cfg, self.grid)

        self.boundarySolver = StdGridBoundaryConditionSolver(cfg, self.grid)
        self.emitters = cfg.Emitters
        self.mapper = cmapper()

    def advect(self, dt):
        self.advection_solver.advect(self.grid.v_pair.cur, self.grid.v_pair.cur, self.grid.v_pair.nxt,
                                     self.boundarySolver.collider_sdf_field, dt)
        self.advection_solver.advect(self.grid.v_pair.cur, self.grid.density_pair.cur, self.grid.density_pair.nxt,
                                     self.boundarySolver.collider_sdf_field, dt)
        self.grid.v_pair.swap()
        self.grid.density_pair.swap()

    def externalForce(self, ext_input, dt):
        # TODO
        if (self.cfg.SceneType == SceneEnum.MouseDragDye):
            # add impulse from mouse
            self.apply_mouse_input_and_render(self.grid.v_pair.cur, self.grid.density_pair.cur, ext_input, dt)
        elif (self.cfg.SceneType == SceneEnum.ShotFromBottom):
            #self.add_fixed_force_and_render(self.grid.v_pair.cur, dt)
            for emitter in self.emitters:
                emitter.stepEmitForce(
                    self.grid.v,
                    self.grid.density_bffr,
                    dt
                )

    def project(self):
        self.grid.calDivergence(self.grid.v_pair.cur, self.grid.v_divs)

        if self.cfg.curl_strength:
            self.grid.calVorticity(self.grid.v_pair.cur)
            self.enhance_vorticity()

        self.projection_solver.runPressure()
        self.projection_solver.runViscosity()

    @ti.kernel
    def enhance_vorticity(self):
        # ref: taichi official stable fluid
        # ref2: https://softologyblog.wordpress.com/2019/03/13/vorticity-confinement-for-eulerian-fluid-simulations/
        vf = ti.static(self.grid.v_pair.cur)
        vc = ti.static(self.grid.v_curl)
        for I in ti.grouped(vc.field):
            cl = vc.sample(I + ts.D.zy)
            cr = vc.sample(I + ts.D.xy)
            cb = vc.sample(I + ts.D.yz)
            ct = vc.sample(I + ts.D.yx)
            cc = vc.sample(I)
            force = ti.Vector([abs(ct) - abs(cb),
                               abs(cl) - abs(cr)]).normalized(1e-3)
            force *= self.cfg.curl_strength * cc
            vf[I] = ts.clamp( vf[I] + force * self.cfg.dt, -1e3, 1e3)

    @ti.kernel
    def vis_density(self, vf: ti.template()):
        ti.cache_read_only(vf.field)
        for I in ti.grouped(vf.field):
            self.clr_bffr[I] = ti.abs(vf[I])

    @ti.kernel
    def vis_v(self, vf: ti.template()):
        # velocity
        for I in ti.grouped(vf):
            v = ts.vec(vf[I].x, vf[I].y, 0.0)
            # self.clr_bffr[I] = ti.Vector([abs(v[0]), abs(v[1]), 0.0])
            self.clr_bffr[I] = 0.01 * v + ts.vec3(0.5)

    @ti.kernel
    def vis_v_mag(self, vf: ti.template()):
        # velocity magnitude
        for I in ti.grouped(vf):
            v_norm = vf[I].norm() * 0.004
            self.clr_bffr[I] = self.mapper.color_map(v_norm)


    @ti.kernel
    def vis_vd(self, vf: ti.template()):
        # divergence
        for I in ti.grouped(vf):
            v = ts.vec(vf[I], 0.0, 0.0)
            self.clr_bffr[I] = 0.1 * v + ts.vec3(0.5)

    @ti.kernel
    def vis_vt(self, vf: ti.template()):
        # visualize vorticity
        for I in ti.grouped(vf):
            v = ts.vec(vf[I], 0.0, 0.0)
            self.clr_bffr[I] = 0.03 * v + ts.vec3(0.5)

    @ti.kernel
    def apply_mouse_input_and_render(self, vf: ti.template(), dyef: ti.template(),
                                     imp_data: ti.ext_arr(),
                                     dt: ti.template()):

        for i, j in vf.field:
            mdir = ti.Vector([imp_data[0], imp_data[1]])
            omx, omy = imp_data[2], imp_data[3]
            # move to cell center
            dx, dy = (i + 0.5 - omx), (j + 0.5 - omy)
            d2 = dx * dx + dy * dy
            # ref: https://developer.download.nvidia.cn/books/HTML/gpugems/gpugems_ch38.html
            # apply the force
            factor = ti.exp(-d2 * self.cfg.inv_force_radius)
            momentum = mdir * self.cfg.f_strength * dt * factor

            vf[i, j] += momentum
            # add dye
            dc = dyef[i, j]
            # TODO what the hell is this?
            if mdir.norm() > 0.5:
                dc += ti.exp(-d2 * self.cfg.inv_dye_denom) * ti.Vector(
                    [imp_data[4], imp_data[5], imp_data[6]])
            dc *= self.cfg.dye_decay
            dyef[i, j] = dc

    @ti.kernel
    def add_fixed_force_and_render(self,
                                   vf: ti.template(),
                                   dt: ti.float32):
        for i, j in vf.field:
            den = self.grid.density_pair.cur[i, j]

            dx, dy = i + 0.5 - self.cfg.source_x, j + 0.5 - self.cfg.source_y
            d2 = dx * dx + dy * dy
            momentum = (self.cfg.direct_X_force * ti.exp(-d2 * self.cfg.inv_force_radius) - self.cfg.f_gravity) * dt
            vf[i, j] += momentum
            # vf[i, j] *= self.cfg.dye_decay
            den += ti.exp(- d2 * self.cfg.inv_force_radius) * self.cfg.fluid_color

            den *= self.cfg.dye_decay
            self.grid.density_pair.cur[i, j] = min(den, self.cfg.fluid_color)

    def render_frame(self):
        if self.cfg.VisualType == VisualizeEnum.Velocity:
            self.vis_v(self.grid.v_pair.cur.field)
        elif self.cfg.VisualType == VisualizeEnum.Density:
            self.vis_density(self.grid.density_pair.cur)
        elif self.cfg.VisualType == VisualizeEnum.Divergence:
            self.vis_vd(self.grid.v_divs.field)
        elif self.cfg.VisualType == VisualizeEnum.Vorticity:
            self.vis_vt(self.grid.v_curl.field)
        elif self.cfg.VisualType == VisualizeEnum.VelocityMagnitude:
            self.vis_v_mag(self.grid.v_pair.cur.field)

    @ti.kernel
    def emit(self):
        half_d = 30
        p = ts.vec(self.cfg.source_x, self.cfg.source_y)
        l_b = p - half_d
        r_u = p + half_d

        shape = ti.Vector(self.grid.v.shape)
        l_b = ts.clamp(l_b, 0, shape - 1)
        r_u = ts.clamp(r_u, 0, shape - 1)
        for I in ti.grouped(ti.ndrange( (l_b.x, r_u.x), (l_b.y, r_u.y) )):
            self.grid.v[I] = ts.vec(0.0, 300.0)
            self.grid.density_bffr[I] = 1.0 * self.cfg.fluid_color

    def step(self, ext_input: np.array):
        # self.emit()

        self.boundarySolver.step_update_sdfs(self.boundarySolver.colliders)
        self.boundarySolver.kern_update_marker()
        for colld in self.boundarySolver.colliders:
            colld.surfaceshape.update_transform(self.cfg.dt)
        # do advection projection here
        self.schemeStep(ext_input)

        self.boundarySolver.ApplyBoundaryCondition()

        self.render_frame()
        if len(self.boundarySolver.colliders):
            self.render_collider()

    @abstractmethod
    def schemeStep(self, ext_input: np.array):
        pass

    @ti.kernel
    def render_collider(self):
        for I in ti.grouped(self.clr_bffr):
            if self.boundarySolver.marker_field[I] == int(PixelType.Collider):
                for it in ti.static(range(len(self.boundarySolver.colliders))):
                    # clld = self.boundarySolver.colliders[0]
                    # TODO render function should be optimized
                    clld = self.boundarySolver.colliders[it]
                    if clld.is_inside_collider(I):
                        self.clr_bffr[I] = clld.color_at_world(I)

    def materialize(self):
        self.materialize_collider()
        self.materialize_emitter()

    def materialize_emitter(self):
        for emitter in self.emitters:
            emitter.kern_materialize()

    def materialize_collider(self):
        for collid in self.boundarySolver.colliders:
            collid.kern_materialize()

    def reset(self):
        self.grid.reset()
        self.clr_bffr.fill(ti.Vector([0, 0, 0]))
        self.boundarySolver.reset()