import sys, csv
for V in ["1.5.0a3","1.3.3post3"]:
    f = f"ilastik-{V}/03_tracking/mitocheck_94570_2D+t_01-53-volume-data_CSV-Table.csv.csv"
    n = list(csv.DictReader(open(f"{sys.argv[1]}/{f}"))); o = list(csv.DictReader(open(f"{sys.argv[2]}/{f}")))
    print(V, "identical after reordering columns by name:", n == o, "; rows differing:", sum(a!=b for a,b in zip(n,o)))
