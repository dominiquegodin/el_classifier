# IMPORT PACKAGES AND FUNCTIONS
import numpy           as np
import multiprocessing as mp
import time, os, sys, h5py
from   argparse  import ArgumentParser
from   functools import partial
from   utils     import presample, merge_presamples, get_dataset, shuffle_sample


# OPTIONS
parser = ArgumentParser()
parser.add_argument( '--n_e'        , default = None , type=float )
parser.add_argument( '--n_tasks'    , default = 10   , type=int   )
parser.add_argument( '--n_files'    , default = None , type=int   )
parser.add_argument( '--output_file', default = 'e-ID.h5'         )
parser.add_argument( '--sampling'   , default = 'ON'              )
parser.add_argument( '--merging'    , default = 'OFF'             )
parser.add_argument( '--shuffling'  , default = 'OFF'             )
parser.add_argument( '--eta_region' , default = 'barrel'          )
args = parser.parse_args()


if args.shuffling == 'ON':
    data_files = get_dataset()
    args.output_dir = 'outputs/test'
    for n in np.arange(1):
        shuffle_sample(args.output_dir, data_files, index=n)
    #arguments = [(args.output_dir, data_files, index) for index in np.arange(10)]
    #processes = [mp.Process(target=shuffle_sample, args=arg) for arg in arguments]
    #for job in processes: job.start()
    #for job in processes: job.join()
    sys.exit()


# DATASET
if args.eta_region == 'barrel_old': data_path = '/opt/tmp/godin/e-ID_data/2019-06-20/0.0-1.3'
if args.eta_region == 'barrel'    : data_path = '/opt/tmp/godin/e-ID_data/2020-05-08/0.0-1.3'
if args.eta_region == 'gap'       : data_path = '/opt/tmp/godin/e-ID_data/2020-05-08/1.3-1.6'
if args.eta_region == 'endcap'    : data_path = '/opt/tmp/godin/e-ID_data/2020-05-08/1.6-2.5'
if not os.path.isdir(data_path+'/'+'output'): os.mkdir(data_path+'/'+'output')
output_dir = data_path+'/'+'output'
data_files = [data_path+'/'+h5_file for h5_file in os.listdir(data_path) if '.h5' in h5_file]
data_files = sorted(data_files)[0:max(1,args.n_files) if args.n_files != None else len(data_files)]


# MERGING FILES/ NO PRESAMPLING
if args.sampling == 'OFF':
    if args.merging == 'ON': print(); merge_presamples(output_dir, args.output_file)
    sys.exit()


# TEMPORARY
'''
data = h5py.File(data_files[0], 'r')
for key in data: print( key, len(data[key]['eventNumber']) )
for key, val in data['train'].items(): print(key, val.shape)
for key, val in data['train'].items():
    if val.ndim > 1: print(key, val.shape, np.sum(np.abs(val)))
sys.exit()
n_e = 0
for file in data_files:
    data = h5py.File(file, 'r')
    n_e += sum([len(data[key]['eventNumber']) for key in data])
sys.exit()
'''


# ELECTRONS VARIABLES
images  =  ['em_barrel_Lr0'   , 'em_barrel_Lr1'   , 'em_barrel_Lr2'   , 'em_barrel_Lr3'                   ,
            'em_endcap_Lr0'   , 'em_endcap_Lr1'   , 'em_endcap_Lr2'   , 'em_endcap_Lr3'                   ,
            'lar_endcap_Lr0'  , 'lar_endcap_Lr1'  , 'lar_endcap_Lr2'  , 'lar_endcap_Lr3'                  ,
            'tile_barrel_Lr1' , 'tile_barrel_Lr2' , 'tile_barrel_Lr3' , 'tile_gap_Lr1'                    ]
tracks  =  ['tracks_pt'       , 'tracks_phi'      , 'tracks_eta'      , 'tracks_d0'        , 'tracks_z0'  ,
            'p_tracks_pt'     , 'p_tracks_phi'    , 'p_tracks_eta'    , 'p_tracks_d0'      , 'p_tracks_z0',
            'p_tracks_charge' , 'p_tracks_vertex' , 'p_tracks_chi2'   , 'p_tracks_ndof'    ,
            'p_tracks_pixhits', 'p_tracks_scthits', 'p_tracks_trthits', 'p_tracks_sigmad0'                ]
scalars =  ['p_truth_pt'      , 'p_truth_phi'     , 'p_truth_eta'     , 'p_truth_E'        , 'p_truth_e'  ,
            'p_et_calo'       , 'p_pt_track'      , 'p_EoverP'        , 'p_Eratio'         , 'p_phi'      ,
            'p_eta'           , 'p_e'             , 'p_Rhad'          , 'p_Rphi'           , 'p_Reta'     ,
            'p_d0'            , 'p_d0Sig'         , 'p_sigmad0'       , 'p_dPOverP'        , 'p_f1'       ,
            'p_f3'            , 'p_weta2'         , 'p_TRTPID'        , 'p_deltaEta1'      , 'p_LHValue'  ,
            'p_chi2'          , 'p_ndof'          , 'p_ECIDSResult'   , 'p_wtots1'         , 'p_EptRatio' ,
            'correctedAverageMu', 'p_deltaPhiRescaled2'                                                   ]
integers = ['p_truthType'     , 'p_TruthType'     , 'p_iffTruth'      , 'p_nTracks'        , 'p_charge'   ,
            'mcChannelNumber' , 'eventNumber'     , 'p_LHTight'       , 'p_LHMedium'       , 'p_LHLoose'  ,
            'p_truthOrigin'   , 'p_TruthOrigin'   , 'p_numberOfSCTHits', 'p_numberOfInnermostPixelHits'   ,
            'p_firstEgMotherTruthType', 'p_firstEgMotherTruthOrigin'                                      ]


# REMOVING TEMPORARY FILES (if any)
h5_files = [h5_file for h5_file in os.listdir(output_dir) if 'e-ID_' in h5_file]
for h5_file in h5_files: os.remove(output_dir+'/'+h5_file)


# STARTING SAMPLING AND COLLECTING DATA
n_tasks = min(mp.cpu_count(), args.n_tasks)
max_e   = [len(h5py.File(h5_file,'r')[key]['eventNumber'])
           for h5_file in data_files for key in h5py.File(h5_file,'r')]
n_e = min(int(args.n_e), sum(max_e)) if args.n_e != None else sum(max_e)
n_e = np.int_(np.round(np.array(max_e)*min(1,n_e/sum(max_e)))) // n_tasks * n_tasks
print('\nSTARTING ELECTRONS COLLECTION (', '\b'+str(sum(n_e)), end=' ', flush=True)
print('electrons from', len(data_files),'files, using', n_tasks,'threads):')
pool  = mp.Pool(n_tasks); sum_e = 0; index = 0
for h5_file in data_files:
    for file_key in h5py.File(h5_file,'r'):
        batch_size = n_e[index]//n_tasks; start_time = time.time()
        print('Collecting', format(str(n_e[index]),'>7s'), 'e from:', h5_file.split('/')[-1], end=' ')
        print(format('['+file_key+']','7s'), end=' ... ', flush=True)
        func_args = (h5_file, output_dir, batch_size, sum_e, images, tracks, scalars, integers, file_key)
        sample = pool.map(partial(presample, *func_args), np.arange(n_tasks))
        sum_e += batch_size; index += 1
        print('(', '\b'+format(time.time() - start_time,'.1f'), '\b'+' s)')
pool.close(); pool.join(); print()


# MERGING FILES
if args.merging=='ON': merge_presamples(output_dir, args.output_file)
