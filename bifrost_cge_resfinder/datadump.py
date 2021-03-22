from bifrostlib import common
from bifrostlib.datahandling import Sample
from bifrostlib.datahandling import SampleComponentReference
from bifrostlib.datahandling import SampleComponent
from bifrostlib.datahandling import Category
from typing import Dict
import os


def extract_resistance(resistance: Category, results: Dict, component_name: str) -> None:
    file_name = "resfinder_results/pheno_table.txt"
    file_key = common.json_key_cleaner(file_name)
    file_path = os.path.join(component_name, file_name)
    with open(file_path) as input:
        lines = input.readlines()
    results[file_key]={}
    for line in lines:
        if not line.startswith('#') and len(line.strip()) > 0:
            line = line.split()
            resistance['summary']['genes'].append({
                'name':line[0],
                'phenotype':line[2]
            })
    results[file_key]['genes'] = resistance['summary']['genes']


def datadump(samplecomponent_ref_json: Dict):
    samplecomponent_ref = SampleComponentReference(value=samplecomponent_ref_json)
    samplecomponent = SampleComponent.load(samplecomponent_ref)
    sample = Sample.load(samplecomponent.sample)
    resistance= samplecomponent.get_category("resistance")
    if resistance is None:
        resistance = Category(value={
                "name": "resistance",
                "component": {"id": samplecomponent["component"]["_id"], "name": samplecomponent["component"]["name"]},
                "summary": {"genes":[]},
                "report": {}
            }
        )
    extract_resistance(resistance, samplecomponent["results"], samplecomponent["component"]["name"])
    samplecomponent.set_category(resistance)
    sample.set_category(resistance)
    common.set_status_and_save(sample, samplecomponent, "Success")
    
    with open(os.path.join(samplecomponent["component"]["name"], "datadump_complete"), "w+") as fh:
        fh.write("done")

datadump(
    snakemake.params.samplecomponent_ref_json,
)
