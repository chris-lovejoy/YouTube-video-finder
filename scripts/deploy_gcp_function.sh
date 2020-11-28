#!/bin/bash
# deploy_gcp_function.sh

# STEPS:
# auth cloud shell `gcloud auth list`
# config project `gcloud config set project <PROJECT_ID>`
# clone this repo, run this script
# run deploy_gcp_function.sh

set -euo pipefail

get_project_id() {
  # Find the project ID first by DEVSHELL_PROJECT_ID (in Cloud Shell)
  # and then by querying the gcloud default project.
  local project="${DEVSHELL_PROJECT_ID:-}"
  if [[ -z "$project" ]]; then
    project=$(gcloud config get-value project 2> /dev/null)
  fi
  if [[ -z "$project" ]]; then
    >&2 echo "No default project was found, and DEVSHELL_PROJECT_ID is not set."
    >&2 echo "Please use the Cloud Shell or set your default project by typing:"
    >&2 echo "gcloud config set project YOUR-PROJECT-NAME"
  fi
  echo "$project"
}

get_service_account() {
  echo "get_service_account: TBD"
}

main() {
  entry_point="main"
  function_name="youtube_playlist"

  # Read api key
  if [[ "$#" < 1 ]]; then
    >&2 echo "Youtube api key expected as parameter"
    exit 1
  fi

  api_key=$1

  echo "api_key: $api_key" > config_ext.yaml

  # Get our working project, or exit if it's not set.
#  local project_id="$(get_project_id)"
  local project_id="TEST_PROJECT_ID"
  if [[ -z "$project_id" ]]; then
    exit 1
  fi

  local service_account="$(get_service_account)"
  if [[ -z "$service_account" ]]; then
    exit 1
  fi

  >&2 echo "gcloud functions deploy $function_name \
    --entry-point=$entry_point \
    --runtime=python38 \
    --trigger-http \
    --max-instances=3"
}



#util.sh
# gcloud functions list
#
# get service_account(){
#   gcloud config get-value account
# }
#
# set -euo pipelfail
#
#
#
# git clone https://github.com/dravida/YouTube-video-finder.git
#

main "$@"
