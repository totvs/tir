#!/bin/bash

# TIR documentation generator (Linux/Unix version)
# Equivalent to the create_docs.cmd script

echo "-------------------------"
echo "TIR documentation generator"
echo "-------------------------"

# Go to the root directory
cd "$(dirname "$0")/.."

echo "Installing Sphinx Module..."
echo "-------------------------"
pip install sphinx

echo "-------------------------"
echo "Installing Sphinx HTML Theme..."
echo "-------------------------"
pip install sphinx-rtd-theme

echo "-------------------------"
echo "Installing TIR dependencies for documentation..."
echo "-------------------------"
pip install beautifulsoup4 numpy pandas python-dateutil pytz selenium six enum34 requests opencv-python

echo "-------------------------"
echo "Creating Documentation..."
echo "-------------------------"
cd doc_files
make clean
make html
cd ..

echo "-------------------------"
echo "Copying documentation to docs folder..."
echo "-------------------------"
rm -rf docs/*
cp -r doc_files/build/html/* docs/
touch docs/.nojekyll

echo "------------------------------------------------------------------------------------"
echo "Documentation created successfully!"
echo "Website located at ./doc_files/build/html/index.html"
echo "Documentation also copied to ./docs/index.html for GitHub Pages compatibility"
echo "------------------------------------------------------------------------------------"