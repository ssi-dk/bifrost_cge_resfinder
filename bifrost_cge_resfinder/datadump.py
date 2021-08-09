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
    results[file_key] = results_json
    phenotypes = results_json['phenotypes']
    genes = results_json['genes']
    # collect phenotypes for genes
    phen_to_gene_map = {phen:[] for phen in phenotypes.keys()}
    for gene in genes.keys():
        gene_phenotype = genes[gene]["phenotypes"]
        if len(gene_phenotype) > 0:
            for phen in gene_phenotype:
                    phen_to_gene_map[phen].append(gene)
    for phenotype in phenotypes.keys():
        if phenotypes[phenotype]['resistant']==True:
            phen_dict = {"phenotype":phenotype}
            phen_dict['seq_variations'] = ", ".join(phenotypes[phenotype]['seq_variations'])
            phen_dict['genes'] = ", ".join([genes[i]['name'] for i in phen_to_gene_map[phenotype]])
            resistance['summary']['phenotypes'].append(phen_dict)
            # make a report with gene coverage and shit
            report_dict = {"phenotype":phenotype}
            report_seq_variations = phenotypes[phenotype]['seq_variations']
            seq_variation_dicts = [{"key":results_json['seq_variations'][i]['key'], 
                                   "seq_var":results_json['seq_variations'][i]['seq_var'],
                                   "genes": seq_variation_gene_object(results_json['seq_variations'][i]['genes'], results_json)} for i in report_seq_variations]
            report_dict["seq_variations"] = seq_variation_dicts
            report_dict['genes'] = []
            for gene_dict in [genes[i] for i in phen_to_gene_map[phenotype]]:
                key = gene_dict['key']
                name = gene_dict['name']
                coverage = gene_dict['coverage']
                identity = gene_dict['identity']
                report_dict['genes'].append({"key":key, "name":name, "coverage":coverage, "identity":identity})
            report_dict['amr_classes'] = phenotypes[phenotype]['amr_classes']
            resistance['report']['data'].append(report_dict)
    #print(resistance)
def seq_variation_gene_object(gene_list, resfinder_json):
    for gene in gene_list:
        key = resfinder_json['genes'][gene]['key']
        name = resfinder_json['genes'][gene]['name']
        coverage = resfinder_json['genes'][gene]['coverage']
        identity = resfinder_json['genes'][gene]['identity']
        return {"key":key, "name":name, "coverage":coverage, "identity":identity}

def datadump(samplecomponent_ref_json: Dict):
    samplecomponent_ref = SampleComponentReference(value=samplecomponent_ref_json)
    samplecomponent = SampleComponent.load(samplecomponent_ref)
    sample = Sample.load(samplecomponent.sample)
    resistance= samplecomponent.get_category("resistance")
    if resistance is None:
        resistance = Category(value={
                "name": "resistance",
                "component": {"id": samplecomponent["component"]["_id"], "name": samplecomponent["component"]["name"]},
                "summary": {"phenotypes":[]},
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
