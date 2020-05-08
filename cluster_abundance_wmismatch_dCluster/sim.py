import pickle, argparse
import numpy as np
import scanpy as sc
import paths, simulation

# argument parsing
parser = argparse.ArgumentParser()
parser.add_argument('--causal-dset-file')
parser.add_argument('--causal-clustering', type=str)
parser.add_argument('--dset')
parser.add_argument('--simname')
parser.add_argument('--method')
parser.add_argument('--index', type=int)
parser.add_argument('--noise-level', type=float) #in units of std dev of noiseless phenotype
args = parser.parse_args()

print('\n\n****')
print(args)
print('****\n\n')

# read data
data = sc.read(paths.simdata + args.dset + '.h5ad')
sampleXmeta = data.uns['sampleXmeta']
causaldata = sc.read(args.causal_dset_file)
causalsm = causaldata.uns['sampleXmeta'].loc[sampleXmeta.index]

# simulate phenotype
np.random.seed(args.index)
nclusters = len(causaldata.obs[args.causal_clustering].unique())
clusters = np.array([args.causal_clustering+'_'+str(i) for i in range(nclusters)])
Ys = causalsm[clusters].values.T
#exclude clusters with big outliers
ltmean = (Ys <= Ys.mean(axis=1)[:,None]).mean(axis=1)
Ys = Ys[ltmean <= 0.7]
print(Ys.shape)
print(clusters[ltmean <= 0.7])
Yvar = np.std(Ys, axis=1)
noiselevels = args.noise_level * Yvar
noise = np.random.randn(*Ys.shape) * noiselevels[:,None]
Ys = Ys + noise

# do analysis
res = simulation.simulate(
    args.method,
    data,
    Ys,
    sampleXmeta.batch.values,
    sampleXmeta.C.values,
    None,
    None)
res['clusterids'] = np.arange(nclusters)[ltmean <= 0.7]

# write results
outfile = paths.simresults(args.dset, args.simname) + str(args.index) + '.p'
print('writing', outfile)
pickle.dump(res, open(outfile, 'wb'))
print('done')
