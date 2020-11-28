# Deploy as a Google Cloud Function

## Intro


## To do before following these instructions
The steps below assume
* You have created a project on Google Cloud Platform (GCP), do the following
* A Youtube API Key has been generated following Chris's instructions in the README.md
* The Cloud Functions API is enabled

## Steps
1. Open a Cloud Shell Terminal and authorize
  ```gcloud auth list```

2. Select the correct project if it is not already selected
  ```gcloud config set project [PROJECT_ID]```

3. Clone this repo
    ``` git clone --single-branch --branch gcp --depth 1 https://github.com/dravida/YouTube-video-finder```

4. Deploy a gcp function providing a function name and api_key

  ```chmod u+x deploy_gcp_function.sh```

  ```deploy_gcp_function.sh [function-name] --api_key=your-key ```
