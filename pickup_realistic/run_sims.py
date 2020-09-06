import os
import numpy as np
import pandas as pd
from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from dtk.generic.climate import set_climate_constant

from simtools.SetupParser import SetupParser
from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory
from simtools.ModBuilder import ModFn, ModBuilder

# from malaria.reports.MalariaReport import add_patient_report, add_survey_report, add_summary_report
from malaria.reports.MalariaReport import add_malaria_transmission_report

from dtk.interventions.input_EIR import add_InputEIR
from dtk.interventions.habitat_scale import scale_larval_habitats

# General --------------------------------------------------------------------------------------------------------

years = 12  # length of simulation, in years
num_seeds = 1
report_start = 0
exp_name = f'Magude_realistic_sweep_EIR_sweep_importation_TradeoffRange'

# Setup ----------------------------------------------------------------------------------------------------------
# config_path = os.path.join('.', 'inputs','config.json')
# cb = DTKConfigBuilder.from_files(config_path)

config_path = os.path.join(os.getcwd(), 'inputs', 'config.json')
cb = DTKConfigBuilder.from_files(config_path, campaign_name=os.path.join(os.getcwd(), 'inputs', 'campaign.json'))

cb.update_params({
    "Num_Cores": 1,
    "logLevel_default": "WARNING",
    "Simulation_Duration": years * 365,
    "Enable_Malaria_CoTransmission": 1,
    "Max_Individual_Infections": 10,
    "Number_Basestrains": 1,
    "Number_Substrains": 0,
    "Incubation_Period_Distribution": "CONSTANT_DISTRIBUTION",
    "Serialized_Population_Path": r"\\internal.idm.ctr\IDM\Home\jorussell\output\test_Magude_burnin_1core_20200814_193104\296\3aa\bb6\2963aabb-64de-ea11-a2c6-c4346bcb1557\output",
    "Serialized_Population_Filenames": ['state-19710.dtk'],#['state-19710-000.dtk', 'state-19710-001.dtk'],
    "SerializationMask_Node_Read": 16
})


# cb.update_params({
#    "Serialized_Population_Path": "//internal.idm.ctr/IDM/home/jsuresh/input/Magude_Core_Geography_Example/old_ento/",
#    'Serialized_Population_Filenames': ['state-00000-000.dtk', 'state-00000-001.dtk']
# })

# Experimental Design -------------------------------------------------------------------------------------------------
def sweep_larval_habitat(cb, scale_factor):
    cb.update_params({"x_Temporary_Larval_Habitat": scale_factor})
    return {'larval_habitat_multiplier': scale_factor}


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


def scale_migration_rate(cb, scale_factor):
    modded_scale_factor = scale_factor+0.03
    cb.update_params({"x_Regional_Migration": modded_scale_factor})
    return {'regional_migration_scaling': modded_scale_factor}


# Reporting -----------------------------------------------------------------------------------------------------------
# add_summary_report(cb,
#                    start = 365*report_start,
#                    description='Annual_Report',
#                    interval = 365,
#                    nreports = 1,
#                    age_bins = [2, 10, 125],
#                    parasitemia_bins = [0, 50, 200, 500, 2000000]
#                    )
from malaria.reports.MalariaReport import add_filtered_spatial_report, add_event_counter_report, add_filtered_report
from dtk.utils.reports.VectorReport import add_human_migration_report

add_filtered_spatial_report(cb, channels=["Population", "True_Prevalence"])
add_malaria_transmission_report(cb, duration=(years - report_start) * 365, start=365 * report_start)
add_human_migration_report(cb)
regional_EIR_node_label = 100000
add_filtered_report(cb, nodes=[regional_EIR_node_label], description='Work')

builder = ModBuilder.from_list(
    [
        [
            ModFn(scale_linear_spline_max_habitat, scale_factor=habitat_multiplier),
            ModFn(scale_migration_rate, scale_factor=migration_multiplier),
            ModFn(DTKConfigBuilder.set_param, 'Run_Number', seed)
        ]
        for habitat_multiplier in [0.6,0.7,0.8,0.9,1]#np.linspace(0.1, 1, 10)
        for migration_multiplier in [0.05,0.075,0.1]#np.logspace(-3, -0.8, 10)
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
