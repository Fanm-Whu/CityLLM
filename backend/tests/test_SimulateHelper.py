from src.algorithms import predictLandFuncPixel, predictPopulation
from typing import List

def vPrintList(AllLandFuncPixelsListn: List[int]):
        print(f"[{AllLandFuncPixelsListn[0]},{AllLandFuncPixelsListn[1]},{AllLandFuncPixelsListn[2]},{AllLandFuncPixelsListn[3]}]")

def testLand():
    AllLandFunc2025SlowPixels = predictLandFuncPixel(2025, 0)
    AllLandFunc2025NaturalPixels = predictLandFuncPixel(2025, 1)
    AllLandFunc2025FastPixels = predictLandFuncPixel(2025, 2)
    AllLandFunc2030SlowPixels = predictLandFuncPixel(2030, 0)
    AllLandFunc2030NaturalPixels = predictLandFuncPixel(2030, 1)
    AllLandFunc2030FastPixels = predictLandFuncPixel(2030, 2)
    vPrintList(AllLandFunc2025SlowPixels)
    vPrintList(AllLandFunc2025NaturalPixels)
    vPrintList(AllLandFunc2025FastPixels)
    vPrintList(AllLandFunc2030SlowPixels)
    vPrintList(AllLandFunc2030NaturalPixels)
    vPrintList(AllLandFunc2030FastPixels)


def testPop():
    Pop2025 = predictPopulation(2025)
    Pop2030 = predictPopulation(2030)
    print(Pop2025)
    print(Pop2030)

if __name__ == "__main__":
    #testLand()
    testPop()