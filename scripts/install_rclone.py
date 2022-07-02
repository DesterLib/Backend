import logging
logger = logging.getLogger("rclone_installer")


def download_rclone() -> str:
    import os
    import shutil
    import pathlib
    import zipfile
    import platform
    import requests

    if shutil.which("rclone"):
        logger.warning("rclone is already installed")
        return shutil.which("rclone")
    os_type = platform.machine().lower()
    if os_type in ("amd64", "x86_64"):
        architecture = "amd64"
    elif os_type in ("aarch64", "arm64"):
        architecture = "arm64"
    elif  os_type in ("arm", "armv7l"):
        architecture = "arm"
    elif os_type in ("i386", "i686", "i86", "x86", "86"):
        architecture = "386"
    else:
        architecture = platform.uname()[4].lower()
    bin_dir = (
        os.path.join(os.getcwd(), "bin")
        if not os.getcwd().lower().endswith("scripts")
        else os.path.join(pathlib.Path(os.getcwd()).parent.absolute(), "bin")
    )
    if not os.path.isdir(bin_dir):
        os.mkdir(bin_dir)
    os_name = platform.uname()[0].lower()
    if os.path.exists(os.path.join(bin_dir, f"rclone{'.exe' if os_name == 'windows' else ''}")):
        logger.warning("rclone is present in the bin directory")
        return os.path.join(bin_dir, f"rclone{'.exe' if os_name == 'windows' else ''}")
    try:
        dl_url = f"https://downloads.rclone.org/rclone-current-{os_name}-{architecture}.zip"
        print(f"Downloading rclone from {dl_url}")
    except BaseException:
        logger.error("Couldn't install rclone")
        exit(
            f"FAILED to download a suitable version for your system platform - '{platform.platform()}'\n\n Please download a suitable rclone release for your OS from 'https://rclone.org' and extract it to '{bin_dir}' folder."
        )
    file_name = dl_url.split("/")[-1]
    logger.info(f"Downloading '{file_name}'...")
    get_response = requests.get(dl_url, stream=True)
    with open(file_name, "wb") as f:
        for chunk in get_response.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)
    with zipfile.ZipFile(file_name, "r") as zip_ref:
        zfile = [
            zfile.filename
            for zfile in zip_ref.infolist()
            if not zfile.filename.endswith(("txt", "1", "html")) and not zfile.is_dir()
        ][0]
        with zip_ref.open(zfile) as zf, open(
            f"{bin_dir}/{zfile.split('/')[-1]}", "wb"
        ) as f:
            logger.info(f"Extracting '{zfile}'")
            shutil.copyfileobj(zf, f)
    os.remove(file_name)
    return f"{bin_dir}/{zfile.split('/')[-1]}"


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )
    download_rclone()
