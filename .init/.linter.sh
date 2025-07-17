#!/bin/bash
cd /home/kavia/workspace/code-generation/note-keeper-3c7766d6/backend_notes_api
source venv/bin/activate
flake8 .
LINT_EXIT_CODE=$?
if [ $LINT_EXIT_CODE -ne 0 ]; then
  exit 1
fi

