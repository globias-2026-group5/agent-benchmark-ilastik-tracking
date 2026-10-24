import sys, h5py, numpy as np, csv
new, old = sys.argv[1], sys.argv[2]
p = "ilastik-1.3.3post3/03_tracking/mitocheck_94570_2D+t_01-53-volume-data_"
q = "ilastik-1.5.0a3/03_tracking/mitocheck_94570_2D+t_01-53-volume-data_"
ld = lambda r,f,s: h5py.File(f"{r}/{f}{s}.h5")["exported_data"][...,0]
# Object-Identities: per frame is new->old a bijection?
a, b = ld(new,p,"Object-Identities"), ld(old,p,"Object-Identities")
nonbij = 0
for t in range(a.shape[0]):
    m = a[t] > 0
    pairs = np.unique(np.stack([a[t][m], b[t][m]]), axis=1)
    if len(np.unique(pairs[0])) != pairs.shape[1] or len(np.unique(pairs[1])) != pairs.shape[1]: nonbij += 1
print("Object-Identities 1.3.3 new vs committed: frames where id mapping is NOT one-to-one:", nonbij)
# Tracking-Result: where do 53/65 swaps sit?
tn, to = ld(new,p,"Tracking-Result"), ld(old,p,"Tracking-Result")
d = tn != to
sw = d & ~(((tn==117)&(to==118))|((tn==118)&(to==117)))
print("Tracking-Result diffs other than 117<->118 swap:", int(sw.sum()), "frames", np.unique(np.nonzero(sw)[0]).tolist())
# after undoing 117<->118, compare regenerated 1.3.3 with regenerated 1.5
tn2 = tn.copy(); tn2[tn==117]=118; tn2[tn==118]=117
t5 = ld(new,q,"Tracking-Result")
print("regenerated 1.3.3 (117/118 swapped back) vs regenerated 1.5: differing px", int((tn2!=t5).sum()), "(committed comparison: 161)")
print("committed 1.3.3 vs committed 1.5: differing px", int((to!=ld(old,q,"Tracking-Result")).sum()))
# CSV: compare as multisets of rows ignoring id columns
def rows(r):
    R = list(csv.reader(open(f"{r}/{p}CSV-Table.csv.csv")))
    return R[0], R[1:]
hn, rn = rows(new); ho, ro = rows(old)
print("CSV header same:", hn == ho, "rows", len(rn), len(ro))
idcols = [i for i,h in enumerate(hn) if any(k in h.lower() for k in ["id","labelimage"])]
print("id-like columns:", [hn[i] for i in idcols])
strip = lambda R: sorted(tuple(x for i,x in enumerate(r) if i not in idcols) for r in R)
print("CSV rows identical after dropping id columns:", strip(rn) == strip(ro))
