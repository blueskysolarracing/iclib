from iclib.bno055 import BNO055, Register

def main():
    BNO055.reset()
    BNO055.write(Register.OPR_MODE, 1)
    test_var = BNO055.read(Register.OPR_MODE)
    print(test_var)