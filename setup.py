from pip._internal import main
from importlib.util import find_spec

imports = {"wx": "wxPython",
           "sql": "sql"}

print("""Checking Dependencies:
----------------------""")
for i in imports:
    print("\nChecking module '{}':".format(imports[i]))
    spec = find_spec(i)
    if spec is None:
        print("- Installing {}...".format(imports[i]))
        code = main(["install", imports[i], "-q", "-q"])
        if code != 0:
            print("- Failed! Code {}".format(code))
        else:
            print("- Done.")
    else:
        print("- Already installed.")


input("\nPress enter to close...")
