# bifrost_cge_resfinder

This component is used to detect chromosomal resistance mutations and antimicrobial resistance (AMR) genes. The component is limited to a predefined set of species native to the utilized tool (described later). 

## Requirements
- The component detects the genes or chromosomal mutations that mediate antimicrobial resistance using the tool [ResFinder](https://github.com/cadms/resfinder).
- The versions are described in the [environment.yaml](https://github.com/ssi-dk/bifrost_cge_resfinder/blob/master/environment.yml)
- The ResFinder tool performs species-specific analysis to optimize organism-specific results on a defined set of [organisms](https://github.com/cadms/resfinder?tab=readme-ov-file#usage). If the dataset is uploaded assemblies (filtered from [component](https://github.com/ssi-dk/bifrost_assembly_qc)), the provided species is used as an option for the tool, whereas the *de novo* generated assembly data (created from [component](https://github.com/ssi-dk/bifrost_assemblatron/tree/master)) utilizes the species determined from another [component](https://github.com/ssi-dk/bifrost_whats_my_species).

## Download
```bash
git clone https://github.com/ssi-dk/bifrost_cge_resfinder.git
cd bifrost_cge_resfinder
git submodule init
git submodule update
bash install.sh -i LOCAL
conda activate bifrost_cge_resfinder_vx.x.x
export BIFROST_INSTALL_DIR='/your/path/'
BIFROST_DB_KEY="/your/key/here/" python -m bifrost_cge_resfinder -h
```
## Run the snakemake analysis
Each component can be run on each sample individually using one snakemake command, replacing the string passed to the **--config sample_name=" "** with the appropriate dataset name. The provided **component_name=** takes as an argument *<component_name>__<version_number>*. The component name aligns with the GitHub repo name, which is structured like *bifrost_<component_name>* (e.g. *bifrost_assemblatron* -> component name *assemblatron*), and the version number aligns with the current [GitHub tag](https://github.com/ssi-dk/bifrost_cge_resfinder/tags) / or conda environment [version](https://github.com/ssi-dk/bifrost_cge_resfinder/blob/master/setup.py) (e.g. *v.2.3.0*) defined during the bifrost component setup. 
```bash
snakemake -p --nolock --cores 5 -s <github_path>/pipeline.smk --config sample_name="insert sample name" component_name=cge_resfinder__v2.3.0 --rerun-incomplete
```

## Analysis
The resfinder command is defined in the [pipeline](https://github.com/ssi-dk/bifrost_cge_resfinder/blob/master/bifrost_cge_resfinder/pipeline.smk), using the parameters *-q -e -l -y*
defined in ([fastp documentation](https://github.com/OpenGene/fastp?tab=readme-ov-file#all-options)).

Once trimmed, the rule *rule greater_than_min_reads_check* checks if the trimmed sequence reads have more than the defined 10000 reads to ensure enough data for additional analysis through other components. If the trimmed sequence reads have a lower amount, the dataset will be discarded and remain unused for further analysis.

        run_resfinder.py \
            -ifa {input.contig} \
            -o $outdir \
            --acquired \
            -db_res {params.resfinder_db} \
            --disinfectant -db_disinf {params.disinfinder_db} \
            --point -db_point {params.pointfinder_db} \
            -s "{params.species}" \
            -j $outdir/{params.sample_name}.json \
            1> {log.out_file} 2> {log.err_file}

        run_resfinder.py --version > {output.tool_version} 2>&1
