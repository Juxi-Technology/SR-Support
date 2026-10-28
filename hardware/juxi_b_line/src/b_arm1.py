from cadgen import step, stl

from lib.design import B, arm1_part


@step(out="../STEP/b_arm1.step")
@stl(out="../STL/b_arm1.stl", mesh_tolerance=4e-4)
def b_arm1():
    return arm1_part(B)


if __name__ == "__main__":
    b_arm1()
