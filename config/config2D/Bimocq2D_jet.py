import taichi as ti
from config.class_cfg import SceneEnum, VisualizeEnum, SchemeType
import os
from utils import set_attribute_from_cfg, filterUpCase
import sys
import config.config2D.scene_config.scene_jit2D as scene_cfg
import config.euler_config
import math
from Emitter import ForceEmitter2, SquareEmitter
import taichi_glsl as ts
from config.class_cfg import SimulateType
from Grid import GRIDTYPE

debug = False

FILTER_TYPE = 'm_'
set_attribute_from_cfg(config.euler_config, sys.modules[__name__], FILTER_TYPE, _if_print=False)
set_attribute_from_cfg(scene_cfg, sys.modules[__name__], FILTER_TYPE, _if_print=False)
set_attribute_from_cfg(config.config2D.basic_config2D, sys.modules[__name__], FILTER_TYPE, _if_print=False)

#
v_grid_type = GRIDTYPE.Bimocq_GRID

SceneType = SceneEnum.Jet
VisualType = VisualizeEnum.Velocity

SimType = SimulateType.Gas
GasAlpha = 8.0
GasBeta = 2.0
GasInitAmbientT = 23.33
GasMaxT = 85.0

# run Scheme
run_scheme = SchemeType.Bimocq

blend_coefficient = 0.5
vel_remap_threshold = 0.8
sclr_remap_threshold = 0.8
vel_remap_frequency = 4
sclr_remap_frequency = 8

from advection import MacCormackSolver, RK_Order, SemiLagrangeSolver

advection_solver = SemiLagrangeSolver

from projection import RedBlackGaussSedialProjectionSolver, JacobiProjectionSolver
projection_solver = RedBlackGaussSedialProjectionSolver
p_jacobi_iters = 160
dye_decay = 0.99
semi_order = RK_Order.RK_3

# vorticity enhancement
curl_strength = 0.0

# collider
from geometry import Transform2, Velocity2

ti.init(arch=ti.gpu, debug=debug, kernel_profiler=True, )
# init should put before init ti.field

from geometry import RigidBodyCollider, Ball
Colliders = []
# Colliders.append(RigidBodyCollider(Ball(
#     transform=Transform2(translation=ti.Vector([300, 250]), localscale=16),
#     velocity=Velocity2(velocity_to_world=ti.Vector([0.0, -10.0]),angular_velocity_to_centroid=15.0))))
# Colliders.append(RigidBodyCollider(Ball(
#     transform=Transform2(translation=ti.Vector([150, 150]), localscale=8),
#     velocity=Velocity2(velocity_to_world=ti.Vector([0.0, 0.0]), angular_velocity_to_centroid=-5.0))))

res = [512, 512]

dt = 0.025
dx = 1.0 / res[0]

Emitters = []
# Emitters.append(ForceEmitter2(
#     t=Transform2(
#         translation=ti.Vector([300.0, 0.0]),
#         localscale=10000.0,
#         orientation=math.pi / 2.0
#     ),
#     v=Velocity2(),
#     fluid_color=fluid_color,
#     force_radius=res[0] / 3.0,
#     )
# )

Emitters.append(SquareEmitter(
    t=Transform2(
        translation=ti.Vector([res[0] // 2, res[0] // 10]),
        localscale=10.0,
        orientation=math.pi / 2.0
    ),
    v=Velocity2(),
    jet_v=ts.vec2(0.0, 0.3),
    jet_t=GasMaxT,
    fluid_color=fluid_color,
    v_grid_type=v_grid_type
    )
)


profile_name = '2D' + '-'\
                + 'x'.join(map(str, res)) + '-' \
                + str(VisualType) + '-' \
                + str(run_scheme) + '-' + "velRemap-" + str(vel_remap_threshold) + '-' + str(vel_remap_frequency) \
                + "-sclrRemap-" + str(sclr_remap_threshold) + "-" + str(sclr_remap_frequency) \
                + "-BlndCoeff-" + str(blend_coefficient) + "-" \
                + filterUpCase(projection_solver.__name__) + '-' \
                + str(p_jacobi_iters) + 'it-' \
                + 'dt-' + str(dt)

if Colliders:
    profile_name += '-Collider'
print(profile_name)

# save to video(gif)
bool_save = True

save_frame_length = 96
save_root = './tmp_result'
save_path = os.path.join(save_root, profile_name)
video_manager = ti.VideoManager(output_dir=save_path,
                                framerate=24,
                                automatic_build=False)
