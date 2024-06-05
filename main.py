import json
from Modules import slicing

PATH_TO_SCENARIO = r"Scenarios/sc_1.json"

if __name__ == '__main__':
    with open(PATH_TO_SCENARIO) as f:
        scenario = json.loads(f.read())

    s = slicing.read_slicing(scenario)
    #s.describe()

    # NSFCA
    h1 = s.check_haesa1()
    h2 = s.check_haesa2()

    l = None
    if h1 and h2:
        print("Slicing Accepted.")
    else:
        l = s.check_laesa()
        if l:
            print("Overbooking analysis required.")
        else:
            print("Slicing can not be accepted.")

    print("\nDetailed Results:")
    print("HAESA1: " + ("Passed" if h1 else "Failed"))
    print("HAESA2: " + ("Passed" if h2 else "Failed"))
    if not(h1 and h2):
        print("LAESA: " + ("Passed" if l else "Failed"))
    print()
    s.detailed_results()


