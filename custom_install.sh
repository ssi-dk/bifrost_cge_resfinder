#!/bin/bash
#Script executes these command with some safeguards in place in case it fails:
#git clone https://git@bitbucket.org/genomicepidemiology/mlst_db.git
#cd mlst_db
#git checkout 5e385d4
#python3 INSTALL.py kma_index

ENV_NAME=$1

RFDB_GIT_REPO_PATH=https://git@bitbucket.org/genomicepidemiology/resfinder_db.git
RFDB_GIT_CHECKOUT_BRANCH=resfinder-4.3.2

PFDB_GIT_REPO_PATH=https://bitbucket.org/genomicepidemiology/pointfinder_db/
PFDB_GIT_CHECKOUT_BRANCH=resfinder-4.3.2

DFDB_GIT_REPO_PATH=https://bitbucket.org/genomicepidemiology/disinfinder_db/
DFDB_GIT_CHECKOUT_BRANCH=resfinder-4.3.2

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd $SCRIPT_DIR # avoiding small edge case where bashrc sourcing changes your directory

function exit_function() {
  echo "to rerun use the command:"
  echo "bash -i $SCRIPT_DIR/custom_install.sh $ENV_NAME"
  exit 1
}

CONDA_BASE=$(conda info --base)
source $CONDA_BASE/etc/profile.d/conda.sh

if ! (conda env list | grep "$ENV_NAME")
then
  echo "conda environment specified is not found"
  exit_function
else
  conda activate $ENV_NAME
fi

RESOURCES="$SCRIPT_DIR/resources"
if test -d "$RESOURCES/resfinder_db"
then
  echo "$RESOURCES/resfinder_db" already exists, if you want to overwrite, please remove old database folder
  echo "You can use:"
  echo "rm -rf $RESOURCES/resfinder_db"
  exit_function
fi
if test -d "$RESOURCES/pointfinder_db"
then
  echo "$RESOURCES/pointfinder_db" already exists, if you want to overwrite, please remove old database folder
  echo "You can use:"
  echo "rm -rf $RESOURCES/pointfinder_db"
  exit_function
fi
if test -d "$RESOURCES/disinfinder_db"
then
  echo "$RESOURCES/disinfinder_db" already exists, if you want to overwrite, please remove old database folder
  echo "You can use:"
  echo "rm -rf $RESOURCES/disinfinder_db"
  exit_function
fi

if test -d "$RESOURCES"
then
  cd $RESOURCES
  git --version
  GIT_IS_AVAILABLE=$?
  if [ $GIT_IS_AVAILABLE -eq 0 ]
  then
    echo "#################Cloning the resfinder db git repo"
    if ! git clone --branch $RFDB_GIT_CHECKOUT_BRANCH $RFDB_GIT_REPO_PATH
    then
      echo >&2 "git clone command failed"
      exit_function
    else
      cd resfinder_db
      DB_FOLDER=$(pwd)
      echo "export CGE_RESFINDER_RESGENE_DB=$DB_FOLDER" >> $CONDA_PREFIX/etc/conda/activate.d/env_vars.sh
      echo "unset CGE_RESFINDER_RESGENE_DB" >> $CONDA_PREFIX/etc/conda/deactivate.d/env_vars.sh
      echo "#######Installing resfinder database with KMA"
      if ! python3 INSTALL.py kma_index
      then
        echo >&2 "python3 INSTALL.py kma_index command failed"
        exit_function
      else
        echo "resfinder db successfully downloaded and installed"
        cd ..
      fi
    fi

    echo "#################Cloning the pointfinder db git repo"
    if ! git clone --branch $PFDB_GIT_CHECKOUT_BRANCH $PFDB_GIT_REPO_PATH
    then
      echo >&2 "git clone command failed"
      exit_function
    else
      cd pointfinder_db
      DB_FOLDER=$(pwd)
      echo "export CGE_RESFINDER_RESPOINT_DB=$DB_FOLDER" >> $CONDA_PREFIX/etc/conda/activate.d/env_vars.sh
      echo "unset CGE_RESFINDER_RESPOINT_DB" >> $CONDA_PREFIX/etc/conda/deactivate.d/env_vars.sh
      echo "#################Installing pointfinder database with KMA"
      if ! python3 INSTALL.py kma_index
      then
        echo >&2 "python3 INSTALL.py kma_index command failed"
        exit_function
      else
        echo "pointfinder db successfully downloaded and installed"
        cd ..
      fi
    fi

    echo "#################Cloning the distinfinder db git repo"
    if ! git clone --branch $DFDB_GIT_CHECKOUT_BRANCH $DFDB_GIT_REPO_PATH
    then
      echo >&2 "git clone command failed"
      exit_function
    else
      cd disinfinder_db
      DB_FOLDER=$(pwd)
      echo "export CGE_DISINFINDER_DB=$DB_FOLDER" >> $CONDA_PREFIX/etc/conda/activate.d/env_vars.sh
      echo "unset CGE_DISINFINDER_DB" >> $CONDA_PREFIX/etc/conda/deactivate.d/env_vars.sh
      echo "#################Installing disinfinder database with KMA"
      if ! python3 INSTALL.py kma_index
      then
        echo >&2 "python3 INSTALL.py kma_index command failed"
        exit_function
      else
        echo "disinfinder db successfully downloaded and installed"
        cd ..
      fi
    fi
  else
    echo "git is not installed"
    echo "you can try activating the conda env for this tool"
    exit_function
  fi
else
  echo "resources folder is expected in the script directory"
  exit_function
fi