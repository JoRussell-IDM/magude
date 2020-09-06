import os
import numpy as np
from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from dtk.generic.climate import set_climate_constant

from simtools.SetupParser import SetupParser
from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory
from simtools.ModBuilder import  ModFn, ModBuilder

# from malaria.reports.MalariaReport import add_patient_report, add_survey_report, add_summary_report
from malaria.reports.MalariaReport import add_malaria_transmission_report

from dtk.interventions.input_EIR import add_InputEIR

# General --------------------------------------------------------------------------------------------------------

years = 7 # length of simulation, in years
num_seeds = 5
report_start = 0
exp_name = f'Magude_7year_sweep_importation'

# Setup ----------------------------------------------------------------------------------------------------------
# config_path = os.path.join('.', 'inputs','config.json')
# cb = DTKConfigBuilder.from_files(config_path)

config_path = os.path.join(os.getcwd(),'inputs','config.json')
cb = DTKConfigBuilder.from_files(config_path)

cb.update_params({
    "logLevel_default": "WARNING",
    "Simulation_Duration": years*365,
    "Enable_Malaria_CoTransmission": 1,
    "Max_Individual_Infections": 10,
    "Number_Basestrains": 1,
    "Number_Substrains": 0,
    "Incubation_Period_Distribution": "CONSTANT_DISTRIBUTION",
    "Serialized_Population_Path":  r"\\internal.idm.ctr\IDM\Home\jorussell\output\test_Magude_burnin_2core_20200819_230035\404\7e9\d26\4047e9d2-6fe2-ea11-a2c6-c4346bcb1557\output",
    "Serialized_Population_Filenames": ['state-19710-000.dtk', 'state-19710-001.dtk']
})




# cb.update_params({
#    "Serialized_Population_Path": "//internal.idm.ctr/IDM/home/jsuresh/input/Magude_Core_Geography_Example/old_ento/",
#    'Serialized_Population_Filenames': ['state-00000-000.dtk', 'state-00000-001.dtk']
# })

#Experimental Design -------------------------------------------------------------------------------------------------
def sweep_larval_habitat(cb, scale_factor) :
    cb.update_params({"x_Temporary_Larval_Habitat": scale_factor })
    return { 'larval_habitat_multiplier' : scale_factor}

def scale_linear_spline_max_habitat(cb,scale_factor):
    for species_params in cb.get_param("Vector_Species_Params"):
        habitats = species_params["Larval_Habitat_Types"]
        scaled_habitats = habitats.copy()
        scaled_habitats["LINEAR_SPLINE"]["Max_Larval_Capacity"] = habitats["LINEAR_SPLINE"][
                                                                      "Max_Larval_Capacity"] * scale_factor
        species_params["Larval_Habitat_Types"] = scaled_habitats
    return {'larval_habitat_multiplier': scale_factor}



#Reporting -----------------------------------------------------------------------------------------------------------
# add_summary_report(cb,
#                    start = 365*report_start,
#                    description='Annual_Report',
#                    interval = 365,
#                    nreports = 1,
#                    age_bins = [2, 10, 125],
#                    parasitemia_bins = [0, 50, 200, 500, 2000000]
#                    )
add_malaria_transmission_report(cb, duration = (years-report_start)*365, start = 365*report_start)

builder = ModBuilder.from_list(
    [
            [
                ModFn(scale_linear_spline_max_habitat, scale_factor = habitat_multiplier),
                ModFn(DTKConfigBuilder.set_param,'Run_Number',seed)
            ]
        for habitat_multiplier in np.logspace(-2, 0, 10)
        for seed in range(num_seeds)
    ]
)



# Run args
run_sim_args = {'config_builder': cb,
                'exp_name': exp_name,
                'exp_builder': builder
                }

if __name__ == "__main__":

    if not SetupParser.initialized:
        SetupParser.init('HPC')

    exp_manager = ExperimentManagerFactory.init()
    exp_manager.run_simulations(**run_sim_args)
    exp_manager.wait_for_finished(verbose=True)
    assert (exp_manager.succeeded())
