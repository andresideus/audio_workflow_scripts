# Setup
for f6-import command wrapper, add to ~/.bashrc
```bash
#f6 import wrapper
export AUDIO_WORKFLOW_SCRIPTS_DIR="$HOME/Google Drive/My Drive/audio_production/audio_workflow_scripts/"
alias f6-import="cd \"$AUDIO_WORKFLOW_SCRIPTS_DIR\" && ./run_process_audio_files.sh && cd - > /dev/null"
```
and 
```bash
source ~/.bashrc
```

# Notes
- google cloud project name: aia-process-audio-files
- key json file is in lastpass
