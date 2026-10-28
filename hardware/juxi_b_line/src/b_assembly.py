from cadgen import step

from b_arm1 import b_arm1
from b_arm2 import b_arm2
from b_base import b_base
from lib.design import B, assembly


@step(out="../STEP/b_assembly.step")
def b_ptk7465_assembly():
    return assembly(B, b_base(), b_arm1(), b_arm2())


if __name__ == "__main__":
    b_ptk7465_assembly()
