def download_rclone() -> str:
    import os
    import re
    import shutil
    import pathlib
    import zipfile
    import platform
    import requests

    if shutil.which("rclone"):
        print("rclone is already installed")
        return shutil.which("rclone")
    if platform.machine() in ("AMD64", "x86_64"):
        architecture = "amd64"
    elif "arm" in platform.machine():
        architecture = "arm64"
    elif "386" in platform.machine():
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
    reg = f"{platform.uname()[0].lower()}\\-{re.escape(architecture)}.*\\.zip$"
    try:
        dl_url = [
            x.get("browser_download_url")
            for x in requests.get("https://api.github.com/repos/rclone/rclone/releases")
            .json()[0]
            .get("assets")
            if re.findall(reg, x.get("name"))
        ][0]
    except BaseException:
        exit(
            f"FAILED to download a suitable version for your system platform - '{platform.platform()}'\n\n Please download a suitable rclone release for your OS from 'https://github.com/rclone/rclone/releases' and extract it to '{bin_dir}' folder."
        )
    file_name = dl_url.split("/")[-1]
    print(f"Downloading '{file_name}'...")
    get_response = requests.get(dl_url, stream=True)
    with open(file_name, "wb") as f:
        for chunk in get_response.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)
    with zipfile.ZipFile(file_name, "r") as zip_ref:
        zfile = [
            zfile.filename
            for zfile in zip_ref.infolist()
            if not zfile.filename.endswith(("txt", "1", "html"))
            and zfile.external_attr == 32
        ][0]
        with zip_ref.open(zfile) as zf, open(
            f"{bin_dir}/{zfile.split('/')[-1]}", "wb"
        ) as f:
            print(f"Extracting '{zfile}'")
            shutil.copyfileobj(zf, f)
    os.remove(file_name)
    return f"{bin_dir}/{zfile.split('/')[-1]}"


if __name__ == "__main__":
    download_rclone()
