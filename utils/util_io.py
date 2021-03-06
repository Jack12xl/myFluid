# import yaml
import numpy as np
import taichi as ti

from .helper_func import vec2_npf32


# def read_cfg( cfg_dir : str ):
#     with open(cfg_dir, "r") as ymlfile:
#         cfg = yaml.load(ymlfile, Loader=yaml.SafeLoader)
#     return cfg

def get_variable_from_module(module_name):
    module = globals().get(module_name, None)
    book = {}
    if module:
        book = {key: value for key, value in module.__dict__.iteritems() if
                not (key.startswith('__') or key.startswith('_'))}
    return book

def set_attribute_from_cfg(_module, _trgt_module, _filter:str, _if_print:bool = True):
    for k, v in _module.__dict__.items():
        if (k.startswith(_filter)):
            if (_if_print):
                print(k, v)
            _trgt_module.__dict__[k[len(_filter):]] = v
            # vars()[k[len(_filter):]] = v

def set_attribute_from_variable(_trgt_module, _variable_name:str, _obj, _if_print:bool = True):
    _trgt_module.__dict__[_variable_name] = _obj

class MouseDataGen(object):
    def __init__(self, cfg):
        self.prev_mouse = None
        self.prev_color = None
        self.cfg = cfg

    def __call__(self, gui):
        # [0:2]: normalized delta direction
        # [2:4]: current mouse xy
        # [4:7]: color
        mouse_data = np.array([0] * 8, dtype=np.float32)
        if gui.is_pressed(ti.GUI.LMB):
            mxy = vec2_npf32(gui.get_cursor_pos()) * self.cfg.screen_res
            if self.prev_mouse is None:
                self.prev_mouse = mxy
                # Set lower bound to 0.3 to prevent too dark colors
                self.prev_color = (np.random.rand(3) * 0.7) + 0.3
            else:
                mdir = mxy - self.prev_mouse
                mdir = mdir / (np.linalg.norm(mdir) + 1e-5)
                mouse_data[0], mouse_data[1] = mdir[0], mdir[1]
                mouse_data[2], mouse_data[3] = mxy[0], mxy[1]
                mouse_data[4:7] = self.prev_color
                self.prev_mouse = mxy
        else:
            self.prev_mouse = None
            self.prev_color = None
        return mouse_data


# @ti.kernel
# def copy_dynamic_nd(self, np_x: ti.ext_arr(), input_x: ti.template()):
#     for i in self.x:
#         for j in ti.static(range(self.dim)):
#             np_x[i, j] = input_x[i][j]
