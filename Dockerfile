# This is intended to run in Github Actions
# Arg can be set to dev for testing purposes
ARG BUILD_ENV="prod"
ARG NAME="bifrost_cge_resfinder"
ARG CODE_VERSION="unspecified"
ARG RESOURCE_VERSION="200811"
ARG MAINTAINER="kimn@ssi.dk"

# For dev build include testing modules via pytest done on github and in development.
# Watchdog is included for docker development (intended method) and should preform auto testing 
# while working on *.py files
#
# Test data is in bifrost_run_launcher:dev
#- Source code (development):start------------------------------------------------------------------
FROM ssidk/bifrost_run_launcher:dev as build_dev
ONBUILD ARG NAME
ONBUILD COPY . /${NAME}
ONBUILD WORKDIR /${NAME}
ONBUILD RUN \
    sed -i'' 's/<code_version>/'"${CODE_VERSION}"'/g' ${NAME}/config.yaml; \
    sed -i'' 's/<resource_version>/'"${RESOURCE_VERSION}"'/g' ${NAME}/config.yaml; \
    pip install -r requirements.dev.txt;
#- Source code (development):end--------------------------------------------------------------------

#- Source code (productopm):start-------------------------------------------------------------------
FROM continuumio/miniconda3:4.7.10 as build_prod
ONBUILD ARG NAME
ONBUILD WORKDIR ${NAME}
ONBUILD COPY ${NAME} ${NAME}
ONBUILD COPY setup.py setup.py
ONBUILD COPY requirements.txt requirements.txt
ONBUILD RUN \
    sed -i'' 's/<code_version>/'"${CODE_VERSION}"'/g' ${NAME}/config.yaml; \
    sed -i'' 's/<resource_version>/'"${RESOURCE_VERSION}"'/g' ${NAME}/config.yaml; \
    ls; \
    pip install -r requirements.txt
#- Source code (productopm):end---------------------------------------------------------------------

#- Use development or production to and add info: start---------------------------------------------
FROM build_${BUILD_ENV}
ARG NAME
LABEL \
    name=${NAME} \
    description="Docker environment for ${NAME}" \
    code_version="${CODE_VERSION}" \
    resource_version="${RESOURCE_VERSION}" \
    environment="${BUILD_ENV}" \
    maintainer="${MAINTAINER}"
#- Use development or production to and add info: end---------------------------------------------

#- Tools to install:start---------------------------------------------------------------------------
RUN \
    # For 'make' needed for kma
    apt-get update &&  apt-get install -y -qq --fix-missing \
        build-essential \
        zlib1g-dev; \
    pip install -q \
        cgecore==1.5.0 \
        tabulate==0.8.3 \
        biopython==1.74;
# KMA
WORKDIR /${NAME}/resources
RUN \
    git clone --branch 1.3.3 https://bitbucket.org/genomicepidemiology/kma.git && \
    cd kma && \
    make;
ENV PATH /${NAME}/resources/kma:$PATH
# Resfinder
WORKDIR /${NAME}/resources
RUN \
    git clone --branch 4.0 https://bitbucket.org/genomicepidemiology/resfinder.git
ENV PATH /${NAME}/resources/resfinder:$PATH
#- Tools to install:end ----------------------------------------------------------------------------

#- Additional resources (files/DBs): start ---------------------------------------------------------
# Resfinder DB from 2020/08/11
WORKDIR /${NAME}/resources
RUN \
    git clone https://git@bitbucket.org/genomicepidemiology/resfinder_db.git && \
    cd resfinder_db && \ 
    git checkout 147c602 && \
    python3 INSTALL.py kma_index;
#- Additional resources (files/DBs): end -----------------------------------------------------------

#- Set up entry point:start ------------------------------------------------------------------------
ENTRYPOINT ["python3", "-m", "bifrost_cge_resfinder"]
CMD ["python3", "-m", "bifrost_cge_resfinder", "--help"]
#- Set up entry point:end --------------------------------------------------------------------------
