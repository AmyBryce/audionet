#! /usr/bin/env bash

: ${PROJECT:="audionet"}
VIRTUALENV_DIR=".virtualenv"

# If we already have a virtual environment activated,
# bail out and advise the user to deactivate.
OLD_VIRTUAL_ENV="${VIRTUAL_ENV}"
if [ "${OLD_VIRTUAL_ENV}" != "" ]; then
  echo "************************************************************************"
  echo "Please deactivate your current virtual environment in order to continue!"
  echo "$ deactivate"
  echo "************************************************************************"
  exit 1
fi

if [[ "$OSTYPE" == "darwin"* ]]; then
    brew install libav
    PYTORCH_URL="http://download.pytorch.org/whl/torch-0.3.0.post4-cp36-cp36m-macosx_10_7_x86_64.whl"
    FFMPEG_PATH="${HOME}/Library/Application Support/imageio/ffmpeg/ffmpeg.osx"
else
    PYTORCH_URL="http://download.pytorch.org/whl/cu90/torch-0.3.0.post4-cp36-cp36m-linux_x86_64.whl"
    FFMPEG_PATH="${HOME}/.imageio/ffmpeg/ffmpeg.linux64"
fi

rm -rf ${VIRTUALENV_DIR}
python3.6 -m venv --prompt ${PROJECT} ${VIRTUALENV_DIR}
source ${VIRTUALENV_DIR}/bin/activate
pip install ${PYTORCH_URL}
pip install -r requirements.txt

python -c "import imageio; imageio.plugins.ffmpeg.download()"
cat > "${VIRTUALENV_DIR}/bin/ffmpeg" << EOF
#!/usr/bin/env bash
"${FFMPEG_PATH}" \${@}
EOF
chmod a+x "${FFMPEG_PATH}"
chmod a+x "${VIRTUALENV_DIR}/bin/ffmpeg"

# Print some info about the sucess of the installation.
echo ""
echo "Setup complete!"
echo ""
echo "To begin working, simply activate your virtual"
echo "environment and deactivate it when you are done."
echo ""
echo "    $ source activate"
echo "    $ python ..."
echo "    $ deactivate"
echo ""
