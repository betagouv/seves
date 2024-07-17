#!/bin/bash

set -e # exit if any command has a non-zero exit status
set -u # consider unset variables as errors
set -o pipefail # prevents errors in a pipeline from being masked

for file in $(find . -name "*.html" -not -path "./venv/*"); do
  djhtml --check "$file"
done

exit 0