import sys
import os
sys.path.insert(0, os.path.abspath('.'))
import inspect
from src import calculations

print("Functions in calculations:")
for name in ['build_features_p1', 'build_features_p2', 'build_distress_target']:
    if hasattr(calculations, name):
        func = getattr(calculations, name)
        src = inspect.getsource(func)
        print(f"=== {name} ===")
        print(src)
