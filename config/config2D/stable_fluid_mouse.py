from config.class_cfg import SceneEnum, VisualizeEnum, SchemeType
from utils import set_attribute_from_cfg, filterUpCase
import sys
import scene_config.mouse_drag_config as scene_cfg
import config.euler_config as default_cfg
import taichi as ti

debug = False
ti.init(arch=ti.gpu, debug=debug,kernel_profiler=True)

FILTER_TYPE = 'm_'
set_attribute_from_cfg(default_cfg, sys.modules[__name__], FILTER_TYPE, _if_print=False)
set_attribute_from_cfg(scene_cfg, sys.modules[__name__], FILTER_TYPE, _if_print=False)
SceneType = SceneEnum.MouseDragDye
VisualType = VisualizeEnum.Density
# run Scheme
# run_scheme = SchemeType.Advection_Projection
run_scheme = SchemeType.Advection_Reflection

from advection import SemiLagrangeOrder, MacCormackSolver
advection_solver = MacCormackSolver
semi_order = SemiLagrangeOrder.RK_3

from projection import RedBlackGaussSedialProjectionSolver
projection_solver = RedBlackGaussSedialProjectionSolver
p_jacobi_iters = 30
dye_decay = 0.99

curl_strength = 14.0

Colliders = []
Emitters = []

profile_name = str(res[0]) + 'x' + str(res[1]) + '-' \
               + str(VisualType) + '-' \
               + str(run_scheme) + '-' \
               + filterUpCase(advection_solver.__name__) + '-' \
               + filterUpCase(projection_solver.__name__) + '-' \
               + str(p_jacobi_iters) + 'it-' \
               + 'RK' + str(int(semi_order)) + '-' \
               + 'curl' + str(curl_strength) + '-' \
               + 'dt-' + str(dt)

print(profile_name)
# save to video(gif)
bool_save = False
