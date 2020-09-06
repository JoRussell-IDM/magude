import os
import numpy as np
import pandas as pd

from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from dtk.generic.climate import set_climate_constant

from simtools.SetupParser import SetupParser
from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory
from simtools.ModBuilder import  ModFn, ModBuilder

# from malaria.reports.MalariaReport import add_patient_report, add_survey_report, add_summary_report
from malaria.reports.MalariaReport import add_malaria_transmission_report

from dtk.interventions.input_EIR import add_InputEIR
from dtk.interventions.habitat_scale import scale_larval_habitats
# General --------------------------------------------------------------------------------------------------------

years = 5 # length of simulation, in years
num_seeds = 1
report_start =63
exp_name = f'test_Magude_burnin_1core_halfpop_halfhabitat_halfbirth'

# Setup ----------------------------------------------------------------------------------------------------------
# config_path = os.path.join('.', 'inputs','config.json')
# cb = DTKConfigBuilder.from_files(config_path)

config_path = os.path.join(os.getcwd(),'inputs','config.json')
cb = DTKConfigBuilder.from_files(config_path)

cb.update_params({

    "Population_Scale_Type": "FIXED_SCALING",
    "x_Base_Population":0.5,
    "x_Birth":0.5,
    "Num_Cores": 1,
    "Enable_Malaria_CoTransmission": 1,
    "Max_Individual_Infections": 10,
    "Number_Basestrains": 1,
    "Number_Substrains": 0,
    "Incubation_Period_Distribution": "CONSTANT_DISTRIBUTION",
    "Serialization_Precision": "REDUCED"

})


#Experimental Design -------------------------------------------------------------------------------------------------
def sweep_larval_habitat(cb, scale_factor) :
    cb.update_params({"x_Temporary_Larval_Habitat": scale_factor })
    return { 'larval_habitat_multiplier' : scale_factor}
def scale_linear_spline_max_habitat(cb, scale_factor):
    df = pd.DataFrame({'LINEAR_SPLINE': [scale_factor]})
    scale_larval_habitats(cb, df)
    # for species_params in cb.get_param("Vector_Species_Params"):
    #     habitats = species_params["Larval_Habitat_Types"]
    #     scaled_habitats = habitats.copy()
    #     scaled_habitats["LINEAR_SPLINE"]["Max_Larval_Capacity"] = habitats["LINEAR_SPLINE"][
    #                                                                   "Max_Larval_Capacity"] * scale_factor
    #     species_params["Larval_Habitat_Types"] = scaled_habitats

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
add_malaria_transmission_report(cb, duration = (2)*365, start = 365*report_start)

builder = ModBuilder.from_list(
    [
            [

                ModFn(scale_linear_spline_max_habitat, scale_factor=habitat_multiplier),
                ModFn(DTKConfigBuilder.set_param,'Run_Number',seed)

            ]
        for habitat_multiplier in [0.5]#np.linspace(0.1, 1, 10)
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
