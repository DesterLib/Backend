#!/bin/bash

case "$(uname -s)" in
Darwin)
    url=$(curl -s https://api.github.com/repos/rclone/rclone/releases | grep browser_download_url | grep 'osx-amd64[.]zip' | head -n 1 | cut -d '"' -f 4)
    curl -o scripts/rclone.zip -L "$url"
    unzip scripts/rclone.zip -d scripts/rclone-tmp
    mv scripts/rclone-tmp/rclone-*-linux-osx/rclone scripts/rclone
    rm -r scripts/rclone-tmp scripts/rclone.zip
    ;;
Linux)
    url=$(curl -s https://api.github.com/repos/rclone/rclone/releases | grep browser_download_url | grep 'linux-amd64[.]zip' | head -n 1 | cut -d '"' -f 4)
    curl -o scripts/rclone.zip -L "$url"
    unzip scripts/rclone.zip -d scripts/rclone-tmp
    mv scripts/rclone-tmp/rclone-*-linux-amd64/rclone scripts/rclone
    rm -r scripts/rclone-tmp scripts/rclone.zip
    ;;
CYGWIN* | MINGW32* | MSYS* | MINGW*)
    url=$(curl -s https://api.github.com/repos/rclone/rclone/releases | grep browser_download_url | grep 'windows-amd64[.]zip' | head -n 1 | cut -d '"' -f 4)
    curl -o scripts/rclone.zip -L "$url"
    powershell.exe Expand-Archive scripts/rclone.zip scripts/rclone-tmp -Force
    mv scripts/rclone-tmp/rclone-*-windows-amd64/rclone.exe scripts/rclone.exe
    rm -r scripts/rclone-tmp scripts/rclone.zip
    ;;
*)
    echo 'Unknow OS was used! Exiting.'
    ;;
esac
