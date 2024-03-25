from bifrostlib import common
from bifrostlib.datahandling import Sample
from bifrostlib.datahandling import SampleComponentReference
from bifrostlib.datahandling import SampleComponent
from bifrostlib.datahandling import Category
from typing import Dict
import os
import json
import re

def extract_resistance(resistance: Category, results: Dict, component_name: str, sample_name:str) -> None:
    file_name = f"resfinder_results/{sample_name}.json"
    file_key = common.json_key_cleaner(file_name)
    file_path = os.path.join(component_name, file_name)
    with open(file_path) as input:
        results_json = json.load(input)
    results[file_key] = results_json
    resfinder_summary = results_json['result_summary']
    resistance['summary'] = resfinder_summary
    phenotypes = results_json['phenotypes']
    seq_regions = results_json['seq_regions']
    seq_variations = results_json['seq_variations']
    #dbs = results_json['databases']
    #resistance['database_versions'] = {dbs[i]['database_name']:dbs[i]['database_version'] for i in dbs.keys()}
    resistance['resfinder_version'] = results_json['software_version']
    # collect items for resistant phenotypes
    resistant_phenotypes = [i for i in phenotypes.keys() if phenotypes[i]['amr_resistant'] == True]
    for phenotype_key in resistant_phenotypes:
        phenotype = phenotypes[phenotype_key]
        amr_classes = phenotype['amr_classes']
        seq_region_keys = phenotype['seq_regions']
        seq_variation_keys = phenotype['seq_variations']
        phenotype_dict = {
            "genes": {},
            "amr_classes": amr_classes
        }
        for seq_region in seq_region_keys:
            seq_region_obj = seq_regions[seq_region]
            gene_name = seq_region_obj['name']
            gene_dict = {'gene_id' : seq_region_obj.get('ref_id'), 
                         'identity' : seq_region_obj.get('identity'),
                         'ref_seq_length' : seq_region_obj.get('ref_seq_length'),
                         'alignment_length' : seq_region_obj.get('alignment_length'),
                         'phenotypes': seq_region_obj.get('phenotypes'),
                         'depth': seq_region_obj.get('depth'),
                         'contig': seq_region_obj.get('query_id'),
                         'contig_start_pos': seq_region_obj.get('query_start_pos'),
                         'contig_end_pos': seq_region_obj.get('query_end_pos'),
                         'notes': seq_region_obj.get('notes'),
                         'pmids': seq_region_obj.get('pmids'),
                         'ref_acc': seq_region_obj.get('ref_acc'),}
            phenotype_dict['genes'][gene_name] = gene_dict
        for seq_variation in seq_variation_keys:
            seq_variation_obj = seq_variations[seq_variation]
            seq_region_objs = [seq_regions[i] for i in seq_variation_obj['seq_regions']]
            gene_mutation_name = '_'.join([i['name'] for i in seq_region_objs]) + '_' + seq_variation_obj['seq_var']
            gene_dict = {'gene_id' : seq_variation_obj.get('ref_id'), 
                         'identity' : seq_variation_obj.get('identity'),
                         'ref_seq_length' : seq_variation_obj.get('ref_seq_length'),
                         'alignment_length' : seq_variation_obj.get('alignment_length'),
                         'phenotypes': seq_variation_obj.get('phenotypes'),
                         'depth': seq_variation_obj.get('depth'),
                         'contig': seq_region_obj.get('query_id'),
                         'contig_start_pos': seq_region_obj.get('query_start_pos'),
                         'contig_end_pos': seq_region_obj.get('query_end_pos'),
                         'notes': seq_variation_obj.get('notes'),
                         'pmids': seq_region_obj.get('pmids'),
                         'ref_acc': seq_region_obj.get('ref_acc'),}
            phenotype_dict['genes'][gene_mutation_name] = gene_dict

        resistance['report']['phenotypes'][phenotype_key] = phenotype_dict


def datadump(samplecomponent_ref_json: Dict):
    samplecomponent_ref = SampleComponentReference(value=samplecomponent_ref_json)
    samplecomponent = SampleComponent.load(samplecomponent_ref)
    sample = Sample.load(samplecomponent.sample)
    resistance = samplecomponent.get_category("resistance")
    sample_name = sample['name']
    #print(resistance) # it's the appending that's duplicated because resistance is not none
    #if resistance is None:
    resistance = Category(value={
            "name": "resistance",
            "component": {"id": samplecomponent["component"]["_id"], "name": samplecomponent["component"]["name"]},
            "summary": "",
            "report": {"phenotypes":{}}
        }
    )
    extract_resistance(resistance, samplecomponent["results"], samplecomponent["component"]["name"], sample_name)
    samplecomponent.set_category(resistance)
    sample_category = sample.get_category("resistance")
    if sample_category == None:
        sample.set_category(resistance)
    else:
        current_category_version = extract_digits_from_component_version(resistance['component']['name'])
        sample_category_version = extract_digits_from_component_version(sample_category['component']['name'])
        print(current_category_version, sample_category_version)
        if current_category_version >= sample_category_version:
            sample.set_category(resistance)
    common.set_status_and_save(sample, samplecomponent, "Success")
    
    with open(os.path.join(samplecomponent["component"]["name"], "datadump_complete"), "w+") as fh:
        fh.write("done")


def extract_digits_from_component_version(component_str):
    version_re = re.compile(".*__(v.*)__.*")
    version_group = re.match(version_re, component_str).groups()[0]
    version_digits = int("".join([i for i in version_group if i.isdigit()]))
    return version_digits
datadump(
    snakemake.params.samplecomponent_ref_json,
)
