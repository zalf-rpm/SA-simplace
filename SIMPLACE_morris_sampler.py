from SALib.sample import morris as morris_pler
import csv
import os
from bs4 import BeautifulSoup
from copy import deepcopy
from collections import defaultdict
from datetime import datetime as dt
import pickle

basepath = os.path.dirname(os.path.abspath(__file__))

#read params to test
p_names = []
p_bounds = []
p_where = [] #position of "TB" param in array

# parameter sampling has a random component:
# unique files are generated each time the script is launched 
now = dt.now()
string_time = now.strftime("%Y-%m-%d_%H-%M-%S")

def SA_settings():
    'returns the problem and general settings fo SA'
        
    #params under SA
    with open(basepath + "/SA_config/user_SA_params.csv") as _:
        reader = csv.reader(_)
        next(reader, None) #skip header
        for row in reader:
            try:
                p_index = int(row[1])
            except:
                p_index = None
            p_name = row[0] if p_index == None else row[0] + "_where_" + str(p_index)            
            p_names.append(p_name)
            p_bounds.append([float(row[2]), float(row[3])])
            p_where.append(p_index)    

    problem = {
        'num_vars': len(p_names),
        'names': p_names,
        'bounds': p_bounds,
        'groups': None
    }

    settings = {
        "n_trajectories": 10,
        "optimal_trajectories": None,
        "n_levels": 4,
        "grid_jump": 2,
        "problem": problem
    }

    #dump the settings for later use in the analyzer
    file_settings = open(basepath + "/pickles/settings." + string_time + ".obj", "w") 
    pickle.dump(settings, file_settings)
    return settings

def sample(settings):
    print("sampling params...")
    
    # DEFINE MODEL INPUTS
    # problem (dict): The problem definition
    # N (int): The number of samples to generate
    # num_levels (int): The number of grid levels
    # grid_jump (int): The grid jump size
    # optimal_trajectories (int): The number of optimal trajectories to sample (between 2 and N)
    # local_optimization (bool):
    # Flag whether to use local optimization according to Ruano et al. (2012)
    # Speeds up the process tremendously for bigger N and num_levels.
    # Stating this variable to be true causes the function to ignore gurobi.
    # morris.sample(problem, N, num_levels, grid_jump, # optimal_trajectories=None, local_optimization=False)
    sample_params = morris_pler.sample(settings["problem"], settings["n_trajectories"], settings["n_levels"], settings["grid_jump"], optimal_trajectories=settings["optimal_trajectories"], local_optimization=False)

    #dump the sample for later use in the analyzer
    file_sample = open(basepath + "/pickles/sample." + string_time + ".obj", "w") 
    pickle.dump(sample_params, file_sample)

    print("simulation needed for SA: " + str(len(sample_params)))

    #write info file SA
    with open(basepath + "/samples/SA_runs_details." + string_time + ".csv", "wb") as _:
        writer = csv.writer(_)
        header = ["run_ID"] + [x for x in p_names]
        writer.writerow(header)
        for i in range(len(sample_params)):
            row = [i] + [x for x in sample_params[i]]
            writer.writerow(row)
        print("info file SA ready!")
        

    #write custom params file for simplace
    def custom_params(template_params, target_params):
        '''
        target params are expected to have the following structure:        
        target_params = {
        "SArun": {
            "table": None,
            "value": int
        },
        "TSUM1": {
            "table": None,
            "value": float or int
            },
        "SLATB": {
            "table": int,
            "value": float or int
            }
        }
        '''
        new_params = deepcopy(template_params)
        for param in new_params:
            p_name = param.attrs["id"]
            p_target = target_params.get(p_name)
            if p_target == None:
                print ("Warning: " + p_name + " found in the template but not targeted")
                exit()
            if p_target["table"] == None:
                param.string = str(p_target["value"])
            else:
                TB_vals = param.find_all("value")
                TB_vals[p_target["table"]].string= str(p_target["value"])
        return new_params

    #read template for customization    
    with open(basepath + "/SA_config/template_SA_params.xml") as _:
        soup = BeautifulSoup(_, "lxml")
    
    template_params = soup.find_all("parameter")
    template_names = [p["id"] for p in template_params]

    #data structure for new xml file
    cp_props = BeautifulSoup("<CropProperties></CropProperties>", features="lxml")
    cp_props_tag = cp_props.new_tag("CropProperties")

    for run_id, p_vals in enumerate(sample_params):
        sa_tag = cp_props.new_tag("SArun")
        
        target_params = defaultdict(dict)
        target_params["SArun"]["table"] = None
        target_params["SArun"]["value"] = run_id
        for idx, val in enumerate(p_vals):
            p_name = p_names[idx].split("_where_")[0]
            if p_name not in template_names:
                print("warning: " + p_name + " targeted but not in template")
                exit()
            target_params[p_name]["table"] = p_where[idx]
            target_params[p_name]["value"] = val
        run_pars = custom_params(template_params, target_params)
        for par in run_pars:
            sa_tag.append(par)
        cp_props_tag.append(sa_tag)
    
    #write 
    with open(basepath + "/samples/SA_params." + string_time + ".xml", "w") as _:
        _.write(cp_props_tag.prettify())
    print("Simplace SA params file ready!")

    return sample_params

def clean_folder(folder_path):
    #don't accidentally clean other stuff 
    can_delete = ["samples", "pickles"]
    if folder_path.split("/")[-1] in can_delete:
        for the_file in os.listdir(folder_path):
            file_path = os.path.join(folder_path, the_file)
            if os.path.isfile(file_path):
                os.unlink(file_path)

#!!!use the following only if you are sure you don't need the files anymore
clean_folder(basepath + "/samples")
clean_folder(basepath + "/pickles")
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
my_settings = SA_settings()
sample_params = sample(my_settings)
