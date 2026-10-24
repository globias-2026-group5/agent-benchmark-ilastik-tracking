import sys, h5py, numpy as np, glob
new, old = sys.argv[1], sys.argv[2]
for V in ["1.3.3post3", "1.5.0a3"]:
    print("==", V)
    for src in ["Tracking-Result", "Object-Identities", "Merger-Result"]:
        f = f"ilastik-{V}/03_tracking/mitocheck_94570_2D+t_01-53-volume-data_{src}.h5"
        a = h5py.File(f"{new}/{f}")["exported_data"][...]; b = h5py.File(f"{old}/{f}")["exported_data"][...]
        d = a != b
        print(f"  {src}: differing px {d.sum()} of {a.size}; labelled-new {int((a>0).sum())} labelled-old {int((b>0).sum())}; same foreground mask: {np.array_equal(a>0,b>0)}")
        if src == "Tracking-Result" and d.any():
            pairs = np.unique(a[d].astype(np.int64)*1000000 + b[d], return_counts=True)
            top = sorted(zip(pairs[1], pairs[0]), reverse=True)[:8]
            print("   top (new,old,count):", [(int(p//1000000), int(p%1000000), int(c)) for c,p in top])
            print("   frames with diffs:", np.unique(np.nonzero(d)[0]).tolist()[:60])
    pr = []
    for part in ["part1", "part2"]:
        f = f"ilastik-{V}/02_pixel_classification/mitocheck_94570_2D+t_01-53-volume-data_Probabilities.{part}.h5"
        a = h5py.File(f"{new}/{f}")["exported_data"][...]; b = h5py.File(f"{old}/{f}")["exported_data"][...]
        pr.append((np.abs(a.astype(np.float64)-b).max(), int((a!=b).sum())))
    print("  Probabilities max abs diff / n differing values (part1, part2):", pr)
    csvf = f"ilastik-{V}/03_tracking/mitocheck_94570_2D+t_01-53-volume-data_CSV-Table.csv.csv"
    print("  CSV identical:", open(f"{new}/{csvf}","rb").read() == open(f"{old}/{csvf}","rb").read())
