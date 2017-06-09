#!/bin/bash
set -e

ROOT=$PWD

pip install -U tox codecov
cd tools
tox

if [ $TOXENV == "py27" ] || [ $TOXENV == "pypy" ]; then
  cd wptrunner
  tox

  cd $ROOT
  pip install --requirement tools/browserutils/requirements.txt
  python tools/browserutils/install.py firefox browser --destination $HOME
  python tools/browserutils/install.py firefox webdriver --destination $HOME/firefox --version v0.16.1
  export PATH=$HOME/firefox:$PATH

  cd $ROOT/resources/test
  geckodriver --version
  #tox
fi

cd $ROOT

#coverage combine tools tools/wptrunner
#codecov
