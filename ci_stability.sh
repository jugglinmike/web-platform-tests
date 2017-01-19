set -e

hosts_fixup() {
    echo "travis_fold:start:hosts_fixup"
    echo "Rewriting hosts file"
    echo "## /etc/hosts ##"
    cat /etc/hosts
    sudo sed -i 's/^::1\s*localhost/::1/' /etc/hosts
    sudo sh -c 'echo "
127.0.0.1 web-platform.test
127.0.0.1 www.web-platform.test
127.0.0.1 www1.web-platform.test
127.0.0.1 www2.web-platform.test
127.0.0.1 xn--n8j6ds53lwwkrqhv28a.web-platform.test
127.0.0.1 xn--lve-6lad.web-platform.test
" >> /etc/hosts'
    echo "== /etc/hosts =="
    cat /etc/hosts
    echo "----------------"
    echo "travis_fold:end:hosts_fixup"
}

install_chrome() {
    channel=$1
    deb_archive=google-chrome-${channel}_current_amd64.deb
    wget https://dl.google.com/linux/direct/$deb_archive

    echo Before uninstallation:
    /usr/bin/google-chrome --version || true

    if sudo update-alternatives --list google-chrome; then
        sudo update-alternatives --remove-all google-chrome
    fi

    echo After uninstallation, before re-installation:
    /usr/bin/google-chrome --version || true

    # Installation will fail in cases where the package has unmet dependencies.
    # When this occurs, attempt to use the system package manager to fetch the
    # required packages and retry.
    if ! sudo dpkg --install $deb_archive; then
      sudo apt-get install --fix-broken
      sudo dpkg --install $deb_archive
    fi

    echo After installation:
    /usr/bin/google-chrome --version
}

test_stability() {
    python check_stability.py $PRODUCT
}

main() {
    hosts_fixup
    if [ $(echo $PRODUCT | grep '^chrome:') ]; then
       install_chrome $(echo $PRODUCT | grep --only-matching '\w\+$')
    fi
    test_stability
}

main
