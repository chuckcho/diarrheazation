# Diarrheazation

A "quick" and "dirty" tool for diarization, hence the name.

## Requirements
1. [SimpleDER](https://github.com/wq2012/SimpleDER)

Run `pip3 install -r requirementx.txt` to install requirements.

## Usage
1. Convert Azure STT results by running `python3 convert_azure_to_diar.py azure_stt_results.json azure_diar.json`
2. Run evaluation by `python3 der.py gt_diar.json azure_diar.json` where `gt_diar.json` is a ground-truth diarization file

## An example
1. Run:
```
python3 convert_azure_to_diar.py sample/kip_with_speakers.json sample/kip_diar.json
```
2. Run (note that this GT diarization is a made-up example hence inaccurate. it's there for an illustration purpose):
```
python3 der.py sample/kip_gt_diar.json sample/kip_diar.json
```
3. The above should yield a caculated DER of 0.07 or 7%.
