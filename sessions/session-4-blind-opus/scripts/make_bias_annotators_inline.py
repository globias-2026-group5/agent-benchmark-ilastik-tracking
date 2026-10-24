import sys; sys.path.insert(0,'scripts')
import make_annotators as ma, numpy as np, h5py
ma.OUT = ma.ROOT/'projects_bias'
raw=h5py.File(ma.RAW,'r')['volume/data'][...,0]
st=ma.STYLES['A3_bright_only']
for seed,name,frames in [(31,'A3b_bright_only',[5,30]),(32,'A3c_bright_only',[15,40])]:
    rng=np.random.default_rng(seed); lf={t:ma.annotate(raw[t],st,rng) for t in frames}
    ma.write_project(name,lf,raw.shape); print(name,frames)
