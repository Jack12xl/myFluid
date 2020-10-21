import taichi as ti
import taichi_glsl as ts
from basic_types import Vector, Float
from abc import ABCMeta, abstractmethod
from utils import lerp

@ti.data_oriented
class DataGrid(metaclass=ABCMeta):
    '''
    the abstract class to store data,
    a wrapper for ti.field

    '''
    def __init__(self,
                 data_field:ti.template()):
        self._field = data_field
        #TODO currently borrow from taichi_glsl
        self._sampler = None

    @ti.pyfunc
    def __getitem__(self, I):
        return self.field[I]

    @ti.pyfunc
    def __setitem__(self, I, value):
        self.field[I] = value

    @property
    @ti.pyfunc
    def shape(self):
        return self._field.shape

    @property
    @ti.pyfunc
    def field(self):
        return self._field

    @ti.pyfunc
    def bilerp(self, P):
        '''
        use bilinear to sample on position P(could be float)
        :param P:
        :return:
        '''
        #TODO support 3D
        # t_P = P - 0.5
        # iu, iv = ti.floor(t_P.x), ti.floor(t_P.y)
        # fu, fv = t_P.x - iu, t_P.y - iv
        #
        # a = ts.sample(self.field, ts.vec(iu + 0.5, iv + 0.5))
        # b = ts.sample(self.field, ts.vec(iu + 1.5, iv + 0.5))
        # c = ts.sample(self.field, ts.vec(iu + 0.5, iv + 1.5))
        # d = ts.sample(self.field, ts.vec(iu + 1.5, iv + 1.5))
        #
        # return lerp(lerp(a, b, fu), lerp(c, d, fu), fv)
        return ts.bilerp(self.field, P)

    @ti.pyfunc
    def sample(self, I):
        return ts.sample(self.field, I)

    @ti.pyfunc
    def sample_minmax(self, P):
        I = int(P)
        x = ts.fract(P)
        y = 1 - x

        a = ts.sample(self.field, I + ts.D.xx) * x.x * x.y
        b = ts.sample(self.field, I + ts.D.xy) * x.x * y.y
        c = ts.sample(self.field, I + ts.D.yy) * y.x * y.y
        d = ts.sample(self.field, I + ts.D.yx) * y.x * x.y

        return min(a, b, c, d), max(a, b, c, d)

    @ti.pyfunc
    def fill(self, value):
        self.field.fill(value)
