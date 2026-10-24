import sys, h5py, numpy as np, csv
new, old = sys.argv[1], sys.argv[2]
p = "ilastik-1.3.3post3/03_tracking/mitocheck_94570_2D+t_01-53-volume-data_"
R = lambda r: list(csv.reader(open(f"{r}/{p}CSV-Table.csv.csv")))
n, o = R(new), R(old)
print("cols only in new:", set(n[0])-set(o[0]), "only in old:", set(o[0])-set(n[0]), "same set:", set(n[0])==set(o[0]))
print("order differs at:", [(i,a,b) for i,(a,b) in enumerate(zip(n[0],o[0])) if a!=b][:5])
ids = {"labelimageId","trackId","lineageId","parentTrackId","mergerLabelId"}
keep = [c for c in o[0] if c not in ids]
def norm(T):
    h = T[0]; ix = [h.index(c) for c in keep]
    return sorted(tuple(r[i] for i in ix) for r in T[1:])
a, b = norm(n), norm(o)
print("rows identical (by column name, ids dropped):", a == b, "; differing rows:", sum(x!=y for x,y in zip(a,b)))
def numeq(a,b):
    bad=0
    for x,y in zip(a,b):
        if any(abs(float(u)-float(v))>1e-6*max(1,abs(float(v))) for u,v in zip(x,y) if u!=v): bad+=1
    return bad
print("rows differing beyond 1e-6 relative:", numeq(a,b))
# which frames have non-bijective Object-Identities mapping
ld = lambda r,s: h5py.File(f"{r}/{p}{s}.h5")["exported_data"][...,0]
A, B = ld(new,"Object-Identities"), ld(old,"Object-Identities")
for t in range(53):
    m = A[t]>0; pr = np.unique(np.stack([A[t][m],B[t][m]]),axis=1)
    ua, ca = np.unique(pr[0], return_counts=True); ub, cb = np.unique(pr[1], return_counts=True)
    if (ca>1).any() or (cb>1).any():
        bad = [(int(i)) for i in ua[ca>1]]
        print(f" frame {t}: new ids mapping to >1 old id: {bad}; px involved {int(np.isin(A[t],ua[ca>1]).sum())}")
