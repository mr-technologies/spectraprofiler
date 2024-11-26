#!/bin/bash
set -eEo pipefail
shopt -s failglob
trap 'echo "${BASH_SOURCE[0]}{${FUNCNAME[0]}}:${LINENO}: Error: command \`${BASH_COMMAND}\` failed with exit code $?"' ERR
cd "$(dirname "$0")"

echo "Installing dependencies..."
sudo apt update
sudo apt install -y \
	argyll \
	build-essential \
	curl \
	liblcms2-dev \
	libtiff-dev \
	python3-pil.imagetk \
	python3-pip
pip3 install --upgrade pip
pip3 install --upgrade colormath

mkdir dcamprof
cd dcamprof

echo "Downloading dcamprof-1.0.6.tar.bz2..."
curl -LO https://torger.se/anders/files/dcamprof-1.0.6.tar.bz2
echo "Unpacking..."
tar -xf dcamprof-1.0.6.tar.bz2
echo "Building..."
pushd dcamprof-1.0.6 > /dev/null
make
popd > /dev/null

echo "Copying necessary files..."
cp /usr/share/color/argyll/ref/ColorChecker.cht ../../res/layout.cht
ln -sf "$(which scanin)" ../../res/
cp dcamprof-1.0.6/dcamprof ../../res/
cp dcamprof-1.0.6/data-examples/cc24_ref-new.cie ../../res/reference.cie
cp dcamprof-1.0.6/data-examples/cc24-layout.json ../../res/layout.json

echo "Application dependencies (except for OpenCV) has been successfully installed."
echo "You can now remove ${PWD}."
