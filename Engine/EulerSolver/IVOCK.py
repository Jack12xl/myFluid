from .Euler_Scheme import EulerScheme
import taichi as ti
import numpy as np


# ref IVOCK 2014, Dr Zhang Xinxin .etal
# need help on stretch and stream function(velocity from vorticity)

@ti.data_oriented
class IVOCK_EulerScheme(EulerScheme):
    def __init__(self, cfg):
        super().__init__(cfg)

    def advect(self, dt):
        pass

    def stretch(self, dt):
        pass

    def schemeStep(self, ext_input: np.array):

        # get omega_n
        self.grid.calCurl(self.grid.v_pair.cur, self.grid.curl_pair.cur)
        # TODO vorticity enhancement on vorticity

        if self.dim == 3:
            self.stretch(self.cfg.dt)
        # advect vorticity
        self.advection_solver.advect(self.grid.v_pair.cur,
                                     self.grid.curl_pair.cur,
                                     self.grid.curl_pair.nxt,
                                     self.cfg.dt)
        # advect velocity
        # after advection, u^tilde = v_pair.nxt
        for v_pair in self.grid.advect_v_pairs:
            self.advection_solver.advect(self.grid.v_pair.cur, v_pair.cur, v_pair.nxt,
                                         self.cfg.dt)

        self.grid.calCurl(self.grid.v_pair.nxt, self.grid.curl_pair.nxt)
        pass
