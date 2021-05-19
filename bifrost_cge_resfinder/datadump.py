from bifrostlib import common
from bifrostlib.datahandling import Sample
from bifrostlib.datahandling import SampleComponentReference
from bifrostlib.datahandling import SampleComponent
from bifrostlib.datahandling import Category
from typing import Dict
import os
import json

def extract_resistance(resistance: Category, results: Dict, component_name: str) -> None:
    file_name = "resfinder_results/std_format_under_development.json"
    file_key = common.json_key_cleaner(file_name)
    file_path = os.path.join(component_name, file_name)
    with open(file_path) as input:
        results_json = json.load(input)
    results[file_key]={}
    # first gather everything that has a phenotype
    items_with_phenotypes = {}
    for gene in results_json['genes'].keys():
        if len(results_json['genes'][gene]['phenotypes']) > 0:
            items_with_phenotypes[gene] = results_json['genes'][gene]
    for gene_variant in results_json['seq_variations'].keys():
        if len(results_json['seq_variations'][gene_variant]['phenotypes']) > 0:
            gene_names = results_json['seq_variations'][gene_variant]['genes']
            for i in gene_names:
                var_phenotypes = results_json['seq_variations'][gene_variant]['phenotypes']
                var_var = results_json['seq_variations'][gene_variant]['seq_var']
                gene_items = results_json['genes'][i]
                gene_items['phenotypes'] = var_phenotypes
                gene_items['seq_var'] = var_var
                items_with_phenotypes[i] = gene_items
    #for i in items_with_phenotypes.keys():
        #print(items_with_phenotypes[i])
    for gene in items_with_phenotypes.keys():
        #print(items_with_phenotypes[gene])
        gene_obj = items_with_phenotypes[gene]
        gene_dict = {}
        gene_dict['gene'] = gene_obj['name']
        gene_dict['phenotype'] = gene_obj['phenotypes']
        gene_dict['associated_variants'] = gene_obj.get('seq_var')
        print(gene_dict)
        resistance['summary']['genes'].append(gene_dict)
        
        report_dict = {}
        report_dict['gene'] = gene_obj['name']
        report_dict['coverage'] = gene_obj['coverage']
        report_dict['identity'] = gene_obj['identity']
        report_dict['associated_variants'] = gene_dict['associated_variants']
        resistance['report']['data'].append(report_dict)
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
                "report": {"data":[]}
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
