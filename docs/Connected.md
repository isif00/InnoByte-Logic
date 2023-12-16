# Connected 
Connected is an AI powered tool for collaborative work.

## Features
**Connected** has many services to offer in order to  improve the quality of the users experience, were we give unique combinations between the simplicity and the effecency 


1. improving the time management ability to the workers by giving a modern calendar and task management system 

2. the ability to do meetings with the team

3. giving a detailed insights based on the meet content
    - the ability to extract all the required data from the meet, starting from the speakers and theire speech and the time stamp of each speaker

    - using the previous extracted data, allow us to use it in different use cases:
        - auto Ai generated pv
        - performance of the workers
    
    since we were able to extract the necessary data from the meets, using that data we will be able to use different AI models for aditional features, in the future .


## How it works
**Connected** is a web app currently, built with **React** and **Flask**.

### meeting transcription:
this is the main feature in our app and those are the three essential steps:
1. It extract audio path from given video file or YouTube link
    - we used movie.py for easy download

2. It generates speaker diarization (separating different speaker tracks) by using [`pyannote/speaker-diarization-3.0`](https://huggingface.co/pyannote/speaker-diarization-3.0) model
    - this model will generate RTTM file, this file will contain all the necessary data so we can pass to the next step. PS: RTTM files are not human readable

3. Next it generates transcription using [Open AI Whisper model](https://huggingface.co/openai/whisper-base.en). By default it uses Whisper `base.en` version but you can select other model sizes.
    - this OpenAi model will work on the generating the transcription using the RTTM file and generate a human readable file (.sub).
   
By default it uses Whisper `base` version but you can select other model sizes. The output is parsed and serialized in order to be returned in a form of json.
- example:
```json 
    [
        {
        "startingPart": "00.00.17"
        "finishPart": "00.00.59"
        "speaker": "Speaker1"
        "speech": "this is what Speaker1 said"
        },
        {
        "startingPart": "00.01.02"
        "finishPart": "00.02.59"
        "speaker": "Speaker2"
        "speech": "this is what Speaker2 said"
        }
    ] 
```
   