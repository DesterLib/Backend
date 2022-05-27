#!/bin/bash

[ ! -d "bin" ] | mkdir -p "bin"

case "$(uname -s)" in
Darwin)
    url=$(curl -s https://api.github.com/repos/rclone/rclone/releases | grep browser_download_url | grep 'osx-amd64[.]zip' | head -n 1 | cut -d '"' -f 4)
    curl -o bin/rclone.zip -L "$url"
    unzip bin/rclone.zip -d bin/rclone-tmp
    mv bin/rclone-tmp/rclone-*-linux-osx/rclone bin/rclone
    rm -r bin/rclone-tmp bin/rclone.zip
    ;;
Linux)
    url=$(curl -s https://api.github.com/repos/rclone/rclone/releases | grep browser_download_url | grep 'linux-amd64[.]zip' | head -n 1 | cut -d '"' -f 4)
    curl -o bin/rclone.zip -L "$url"
    unzip bin/rclone.zip -d bin/rclone-tmp
    mv bin/rclone-tmp/rclone-*-linux-amd64/rclone bin/rclone
    rm -r bin/rclone-tmp bin/rclone.zip
    ;;
CYGWIN* | MINGW32* | MSYS* | MINGW*)
    url=$(curl -s https://api.github.com/repos/rclone/rclone/releases | grep browser_download_url | grep 'windows-amd64[.]zip' | head -n 1 | cut -d '"' -f 4)
    curl -o bin/rclone.zip -L "$url"
    powershell.exe Expand-Archive bin/rclone.zip bin/rclone-tmp -Force
    mv bin/rclone-tmp/rclone-*-windows-amd64/rclone.exe bin/rclone.exe
    rm -r bin/rclone-tmp bin/rclone.zip
    ;;
*)
    echo 'Unknow OS was used! Exiting.'
    exit 1
    ;;
esac
