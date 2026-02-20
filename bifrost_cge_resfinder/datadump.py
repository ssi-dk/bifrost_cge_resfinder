from bifrostlib import common
from bifrostlib.datahandling import Sample
from bifrostlib.datahandling import SampleComponentReference
from bifrostlib.datahandling import SampleComponent
from bifrostlib.datahandling import Category
from typing import Dict
import os
import json
import re


def cat_region_data(property, seq_region_objs):
    return "/".join((str(seq_region_obj.get(property)) for seq_region_obj in seq_region_objs))


def extract_resistance(resistance: Category, results: Dict, component_name: str, sample_name: str) -> Dict:
    """
    Extracts full ResFinder JSON into samplecomponent.results
    AND populates the resistance Category (phenotype report).
    Returns the full results_json so the caller can also build
    the trimmed Sample-level category.
    """
    file_name = f"resfinder_results/{sample_name}.json"
    file_key = common.json_key_cleaner(file_name)
    file_path = os.path.join(component_name, file_name)

    with open(file_path) as input:
        results_json = json.load(input)

    # Store full JSON in samplecomponent.results
    results[file_key] = results_json

    # Fill category summary
    resistance["summary"] = results_json["result_summary"]
    resistance["resfinder_version"] = results_json["software_version"]

    phenotypes = results_json["phenotypes"]
    seq_regions = results_json["seq_regions"]
    seq_variations = results_json["seq_variations"]

    # Build phenotype report
    resistant_phenotypes = [
        i for i in phenotypes.keys()
        if phenotypes[i]["amr_resistant"] is True
    ]

    for phenotype_key in resistant_phenotypes:
        phenotype = phenotypes[phenotype_key]
        amr_classes = phenotype["amr_classes"]
        seq_region_keys = phenotype["seq_regions"]
        seq_variation_keys = phenotype["seq_variations"]

        phenotype_dict = {
            "genes": {},
            "amr_classes": amr_classes
        }

        # Add gene hits
        for seq_region in seq_region_keys:
            seq_region_obj = seq_regions[seq_region]
            gene_name = seq_region_obj["name"]

            gene_dict = {
                "gene_id": seq_region_obj.get("ref_id"),
                "identity": seq_region_obj.get("identity"),
                "ref_seq_length": seq_region_obj.get("ref_seq_length"),
                "alignment_length": seq_region_obj.get("alignment_length"),
                "phenotypes": seq_region_obj.get("phenotypes"),
                "depth": seq_region_obj.get("depth"),
                "contig": seq_region_obj.get("query_id"),
                "contig_start_pos": seq_region_obj.get("query_start_pos"),
                "contig_end_pos": seq_region_obj.get("query_end_pos"),
                "notes": seq_region_obj.get("notes"),
                "pmids": seq_region_obj.get("pmids"),
                "ref_acc": seq_region_obj.get("ref_acc"),
                "grade": seq_region_obj.get("grade"),
            }

            phenotype_dict["genes"][gene_name] = gene_dict

        # Add mutations
        for seq_variation in seq_variation_keys:
            seq_variation_obj = seq_variations[seq_variation]
            seq_region_objs = [seq_regions[i] for i in seq_variation_obj["seq_regions"]]

            gene_mutation_name = (
                "_".join([i["name"] for i in seq_region_objs])
                + "_"
                + seq_variation_obj["seq_var"]
            )

            gene_dict = {
                "gene_id": seq_variation_obj.get("ref_id"),
                "identity": cat_region_data("identity", seq_region_objs),
                "ref_seq_length": cat_region_data("ref_seq_length", seq_region_objs),
                "alignment_length": cat_region_data("alignment_length", seq_region_objs),
                "phenotypes": seq_variation_obj.get("phenotypes"),
                "depth": cat_region_data("depth", seq_region_objs),
                "contig": cat_region_data("query_id", seq_region_objs),
                "contig_start_pos": cat_region_data("query_start_pos", seq_region_objs),
                "contig_end_pos": cat_region_data("query_end_pos", seq_region_objs),
                "notes": seq_variation_obj.get("notes"),
                "pmids": seq_variation_obj.get("pmids"),
                "ref_acc": cat_region_data("ref_acc", seq_region_objs),
                "grade": cat_region_data("grade", seq_region_objs),
            }

            phenotype_dict["genes"][gene_mutation_name] = gene_dict

        resistance["report"]["phenotypes"][phenotype_key] = phenotype_dict

    return results_json


def extract_digits_from_component_version(component_str):
    version_re = re.compile(r".*__v(\d+\.\d+\.\d+)(__)?.*")
    version_group = re.match(version_re, component_str).groups()[0]
    version_digits = tuple(int(i) for i in version_group.split(".") if i.isdigit())
    return version_digits


def datadump(samplecomponent_id: str):
    samplecomponent_ref = SampleComponentReference(_id=samplecomponent_id)
    samplecomponent = SampleComponent.load(samplecomponent_ref)
    sample = Sample.load(samplecomponent.sample)

    sample_name = sample["name"]

    # Build resistance category for samplecomponent
    resistance = Category(
        value={
            "name": "resistance",
            "component": {
                "id": samplecomponent["component"]["_id"],
                "name": samplecomponent["component"]["name"],
            },
            "summary": "",
            "report": {"phenotypes": {}},
        }
    )

    # Extract full JSON + phenotype report
    results_json = extract_resistance(
        resistance,
        samplecomponent["results"],
        samplecomponent["component"]["name"],
        sample_name,
    )

    # Store full category in samplecomponent
    samplecomponent.set_category(resistance)

    # ---- Build trimmed Sample-level category ----
    trimmed_resistance = Category(
        value={
            "name": "resistance",
            "component": {
                "id": samplecomponent["component"]["_id"],
                "name": samplecomponent["component"]["name"],
            },
            "summary": {
                "databases": results_json.get("databases", {}),
                "seq_regions": results_json.get("seq_regions", {}),
                "seq_variations": results_json.get("seq_variations", {}),
                "phenotypes": results_json.get("phenotypes", {}),
            },
            "report": {},
        }
    )

    # ---- Version-aware overwrite logic ----
    existing = sample.get_category("resistance")
    if existing is None:
        sample.set_category(trimmed_resistance)
    else:
        current_version = extract_digits_from_component_version(
            resistance["component"]["name"]
        )
        existing_version = extract_digits_from_component_version(
            existing["component"]["name"]
        )
        if current_version >= existing_version:
            sample.set_category(trimmed_resistance)

    # Save everything
    common.set_status_and_save(sample, samplecomponent, "Success")

    # Completion flag
    with open(
        os.path.join(samplecomponent["component"]["name"], "datadump_complete"),
        "w+",
    ) as fh:
        fh.write("done")


# Snakemake call
datadump(
    snakemake.params.samplecomponent_id,
)
