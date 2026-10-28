from cadgen import step, stl

from lib.design import B, base_part


@step(out="../STEP/b_base.step")
@stl(out="../STL/b_base.stl", mesh_tolerance=4e-4)
def b_base():
    return base_part(B)


if __name__ == "__main__":
    b_base()
