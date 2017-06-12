#!/bin/bash
set -e

ROOT=$PWD

pip install -U tox codecov
cd tools

if [ $TOXENV == "py27" ] || [ $TOXENV == "pypy" ]; then

  cd $ROOT
  pip install --requirement tools/browserutils/requirements.txt
  python tools/browserutils/install.py firefox browser --destination $HOME
  python tools/browserutils/install.py firefox webdriver --destination $HOME/firefox
  export PATH=$HOME/firefox:$PATH

  cd $ROOT/resources/test
  tail -F geckodriver.log & tox
fi
