#!/bin/bash

# Define source and destination directories
TS_SRC_DIR="static/ts"
JS_DEST_DIR="static/js"

# Ensure the destination directory exists
mkdir -p "$JS_DEST_DIR"

# Transpile all TypeScript files individually, without module exports
npx tsc --target ES6 --module esnext --outDir "$JS_DEST_DIR" --sourceMap false

echo "Transpilation complete. JavaScript files are in $JS_DEST_DIR"
