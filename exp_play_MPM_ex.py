import taichi as ti
import taichi_glsl as ts
import numpy as np
import argparse
from config import mpmCFG, MaType


def parse_args():
    parser = argparse.ArgumentParser(description="Run which config")

    parser.add_argument("--cfg", help="configure file", type=str)
    args = parser.parse_args()
    cfg = None

    if args.cfg == "Jello-Fall-2D-ex":
        import config.config2D.Jello_Fall2D_ex
        cfg = config.config2D.Jello_Fall2D_ex
    # elif args.cfg == "Jello-Fall-3D":
    #     import config.config3D.Jello_Fall3D
    #     cfg = config.config3D.Jello_Fall3D
    return mpmCFG(cfg)


if __name__ == '__main__':
    m_cfg = parse_args()

    from Engine.MPM_solver import MPMSolver

    colors = np.array([0xED553B, 0x068587, 0xEEEEF0, 0xFFFF00], dtype=np.int32)
    scheme = MPMSolver(m_cfg)
    dim = m_cfg.dim
    scheme.materialize()


    # scheme.Layout.init_cube()

    def init_fall_cube():
        n_p = 0
        n_p += scheme.Layout.add_cube(l_b=ts.vecND(dim, 0.05),
                                      cube_size=ts.vecND(dim, 0.15),
                                      mat=MaType.liquid,
                                      density=2 ** m_cfg.dim,
                                      velocity=ts.vecND(dim, 0.0),
                                      color=colors[MaType.liquid]
                                      )

        n_p += scheme.Layout.add_cube(l_b=ts.vecND(dim, 0.3),
                                      cube_size=ts.vecND(dim, 0.15),
                                      mat=MaType.elastic,
                                      density=2 ** m_cfg.dim,
                                      velocity=ts.vecND(dim, 0.0),
                                      color=colors[MaType.elastic]
                                      )

        n_p += scheme.Layout.add_cube(l_b=ts.vecND(dim, 0.5),
                                      cube_size=ts.vecND(dim, 0.15),
                                      mat=MaType.sand,
                                      density=2 ** m_cfg.dim,
                                      velocity=ts.vecND(dim, 0.0),
                                      color=colors[MaType.sand]
                                      )

        n_p += scheme.Layout.add_cube(l_b=ts.vecND(dim, 0.7),
                                      cube_size=ts.vecND(dim, 0.15),
                                      mat=MaType.snow,
                                      density=2 ** m_cfg.dim,
                                      velocity=ts.vecND(dim, 0.0),
                                      color=colors[MaType.snow]
                                      )
        print(f'Add {n_p} particles ')


    init_fall_cube()

    gui = ti.GUI(m_cfg.profile_name, tuple(m_cfg.screen_res), fast_gui=False)
    paused = False

    while gui.running:
        if gui.get_event(ti.GUI.PRESS):
            e = gui.event
            if e.key == 'p':
                paused = not paused
            elif e.key == 'r':
                scheme.reset()
                init_fall_cube()

        if not paused:
            scheme.step()

        np_x = scheme.Layout.p_x.to_numpy()
        if m_cfg.dim == 2:
            screen_pos = np_x
        elif m_cfg.dim == 3:
            # screen_x = ((np_x[:, 0] + np_x[:, 2]) / 2 ** 0.5) - 0.2
            # screen_y = (np_x[:, 1])
            # screen_pos = np.stack([screen_x, screen_y], axis=-1)
            np_x -= 0.5

            phi, theta = np.radians(28), np.radians(32)
            x, y, z = np_x[:, 0], np_x[:, 1], np_x[:, 2]

            c, s = np.cos(phi), np.sin(phi)
            C, S = np.cos(theta), np.sin(theta)

            x, z = x * c + z * s, z * c - x * s
            u, v = x, y * C + z * S

            screen_pos = np.array([u, v]).swapaxes(0, 1) + 0.5

        gui.circles(screen_pos, radius=1.5, color=scheme.Layout.p_color.to_numpy())
        if not m_cfg.cfg.bool_save:
            gui.show()  # Change to gui.show(f'{frame:06d}.png') to write images to disk
        else:
            if scheme.curFrame < m_cfg.save_frame_length:
                import os

                os.makedirs(m_cfg.save_path, exist_ok=True)
                gui.show(os.path.join(m_cfg.save_path, f'{scheme.curFrame:06d}.png'))
            else:
                break

    ti.kernel_profiler_print()
