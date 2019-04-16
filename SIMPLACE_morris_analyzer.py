from SALib.analyze import morris as morris_lyze
import numpy as np
import pandas as pd
import csv
import os
import pickle
from collections import defaultdict

basepath = os.path.dirname(os.path.abspath(__file__))

# custom settings ##########################
# out file to be analyzed 
target_file =  "Summary_out.csv"

# target var of the analysis
target_vars = ["Yield_HS_H_TAir"]

# unique identifier of sample and settings
string_time = "2019-04-12_16-05-16"
###########################################

# load objects created by the sampler
file_settings = open(basepath + "/pickles/settings." + string_time + ".obj", "r")
settings = pickle.load(file_settings)

file_sample = open(basepath + "/pickles/sample." + string_time + ".obj", "r")
sample_params = pickle.load(file_sample)

# data structure for calculated indices
# keys: var, date, index (mu/sigma); vals: index val
all_morris_indices = defaultdict(lambda: defaultdict(dict))

# load sim results
print("loading " + target_file)
sim_out = pd.read_csv(basepath + "/simplace_results/" + target_file, sep=',')

# ANALYZE
# SALib.analyze.morris.analyze(problem, X, Y, num_resamples=1000, conf_level=0.95, print_to_console=False, grid_jump=2, num_levels=4)
# problem (dict): The problem definition
# X (numpy.matrix): The NumPy matrix containing the model inputs
# Y (numpy.array): The NumPy array containing the model outputs
# num_resamples (int): The number of resamples used to compute the confidence intervals (default 1000)
# conf_level (float): The confidence interval level (default 0.95)
# print_to_console (bool): Print results directly to console (default False)
# grid_jump (int): The grid jump size, must be identical to the value passed to SALib.sample.morris.sample() (default 2)
# num_levels (int): The number of grid levels, must be identical to the value passed to SALib.sample.morris (default 4)

print("analyzing " + str(target_vars))
for t_var in target_vars:
    
    if "summary" in target_file.lower():
        'one output per run'
        date = None
        Y = np.empty([sample_params.shape[0]])
        for SArun in range(len(sample_params)):
            SArun_out = sim_out.loc[sim_out["SArun"] == SArun, t_var].values
            Y[SArun] = SArun_out[0]
        morris_indices = morris_lyze.analyze(settings["problem"], sample_params, Y, num_resamples=1000, conf_level=0.95, print_to_console=False, grid_jump=settings["grid_jump"], num_levels=settings["n_levels"])
        all_morris_indices[t_var][date] = morris_indices
    
    elif "daily" in target_file.lower():
        'one output per run and day'
        aaa=1
        #!TODO: decide how to manage missing dates (e.g., due to changed TSUMS, harvest may be anticipated!)

#write out file
out_morris_file = "Indices_" + target_file

with open(basepath + "/SA_indices/" + out_morris_file, "wb") as _:
    writer = csv.writer(_)
    idx_names = ["mu", "mu_star", "mu_star_conf", "sigma"]
    header = ["var", "date", "param"] + idx_names

    writer.writerow(header)

    for var, date_idxvals in all_morris_indices.iteritems():
        for date, idxvals in date_idxvals.iteritems():
            for p_id, p_name in enumerate(idxvals["names"]):
                row = [var, date, p_name]
                for idx in idx_names:
                    row.append(idxvals[idx][p_id])
                writer.writerow(row)

print(out_morris_file + " saved!")