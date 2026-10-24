import sys, h5py, numpy as np, csv
new, old = sys.argv[1], sys.argv[2]
p = "ilastik-1.3.3post3/03_tracking/mitocheck_94570_2D+t_01-53-volume-data_"
ld = lambda r,s: h5py.File(f"{r}/{p}{s}.h5")["exported_data"][...,0]
A, B, M = ld(new,"Object-Identities"), ld(old,"Object-Identities"), ld(new,"Merger-Result")
d = A != B
print("Object-Identities differing px:", int(d.sum()), "; of these inside Merger-Result>0:", int((d & (M>0)).sum()))
T, To = ld(new,"Tracking-Result"), ld(old,"Tracking-Result")
o = (T!=To) & ~(((T==117)&(To==118))|((T==118)&(To==117)))
print("Tracking-Result diffs beyond 117/118 swap inside merger pixels:", int((o&(M>0)).sum()), "of", int(o.sum()))
def rows(r):
    R = list(csv.reader(open(f"{r}/{p}CSV-Table.csv.csv"))); h=R[0]; return h, R[1:]
for r in (new, old):
    h, R = rows(r); i = h.index("mergerLabelId"); print(r[:8], "objects with mergerLabelId!=0:", sum(x[i] not in ("0","0.0") for x in R))
