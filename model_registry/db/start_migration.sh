#!/bin/bash

pgmigrate \
  --conn "postgresql://postgres:postgres@localhost:5432/model_registry" \
  -d migrations \
  --target latest \
  migrate