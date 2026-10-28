from cadgen import step, stl

from lib.design import B, arm2_part


@step(out="../STEP/b_arm2.step")
@stl(out="../STL/b_arm2.stl", mesh_tolerance=4e-4)
def b_arm2():
    return arm2_part(B)


if __name__ == "__main__":
    b_arm2()
