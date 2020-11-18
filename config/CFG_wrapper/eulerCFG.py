from .fluidCFG import FluidCFG
from utils import SetterProperty
from config.class_cfg import SceneEnum, VisualizeEnum, SchemeType, SimulateType
from projection import RedBlackGaussSedialProjectionSolver, JacobiProjectionSolver, ConjugateGradientProjectionSolver
import taichi as ti
from advection import MacCormackSolver

class EulerCFG(FluidCFG):
    """
    Hold property especially for Euler-based simulation
    """

    def __init__(self, cfg):
        super(EulerCFG, self).__init__(cfg)

        self.run_scheme = cfg.run_scheme
        self.VisualType = cfg.VisualType
        self.SceneType = cfg.SceneType

        # set these if simulate the gas
        self.GasAlpha = None
        self.GasBeta = None
        self.GasInitAmbientT = None
        self.GasMaxT = None
        self.SimType = cfg.SimType

        self.advection_solver = cfg.advection_solver
        self.projection_solver = cfg.projection_solver
        self.viscosity_coefficient = cfg.dynamic_viscosity_coefficient

        self.dye_decay = cfg.dye_decay
        self.curl_strength = cfg.curl_strength

    @property
    def SimType(self):
        return self._simulation_type

    @SimType.setter
    def SimType(self, T: SimulateType):
        self._simulation_type = T
        if T == SimulateType.Gas:
            self.GasAlpha = self.cfg.GasAlpha
            self.GasBeta = self.cfg.GasBeta
            self.GasInitAmbientT = self.cfg.GasInitAmbientT
            self.GasMaxT = self.cfg.GasMaxT

    @property
    def SceneType(self):
        return self._scene_type

    @SceneType.setter
    def SceneType(self, T: SceneEnum):
        self._scene_type = T
        if T == SceneEnum.MouseDragDye:
            self.force_radius = self.cfg.force_radius
            self.inv_force_radius = 1.0 / self.cfg.force_radius
            self.f_strength = self.cfg.f_strength
            self.inv_dye_denom = self.cfg.inv_dye_denom

    @property
    def advection_solver(self):
        return self._advection_solver

    @advection_solver.setter
    def advection_solver(self, solver):
        self._advection_solver = solver
        self.semi_order = self.cfg.semi_order
        if self._advection_solver == MacCormackSolver:
            self.macCormack_clipping = self.cfg.macCormack_clipping

    @property
    def projection_solver(self):
        return self._projection_solver

    @projection_solver.setter
    def projection_solver(self, solver):
        self._projection_solver = solver
        if self._projection_solver != ConjugateGradientProjectionSolver:

            self.p_jacobi_iters = self.cfg.p_jacobi_iters
            self.poisson_pressure_alpha = ti.static(- self.dx * self.dx)
            # 1 / 4 for 2D, 1 / 6 for 3D
            self.poisson_pressure_beta = ti.static(1.0 / (2 * self.dim))

            # viscosity
            self.viscosity_coefficient = self.cfg.dynamic_viscosity_coefficient

            # TODO currently hard code the viscosity to be same as pressure
            self.poisson_viscosity_alpha = self.poisson_pressure_alpha
            self.poisson_viscosity_beta = self.poisson_pressure_beta

        else:
            # TODO MGPCG
            pass

    @property
    def viscosity_coefficient(self):
        return self._viscosity_coefficient

    @viscosity_coefficient.setter
    def viscosity_coefficient(self, v):
        # GPU GEM
        self._viscosity_coefficient = v
        self.poisson_viscosity_alpha = self.dx * self.dx / (self.dt * self._viscosity_coefficient)
        self.poisson_viscosity_beta = 1.0 / (self.poisson_viscosity_alpha + 4)