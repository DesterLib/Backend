if [ ! -d "build" ]
then
    dir_name=$(pwd)
    current_folder="${dir_name%"${dir_name##*[!/]}"}"
    current_folder="${current_folder##*/}"
    current_folder=${current_folder:-/}  
    if [ "$current_folder" == "scripts" ]
    then
        echo -e "\e[31m[ERROR]: Please run this script from the root directory of the project.\e[0m"
        exit 1
    fi
    if [ ! -d "Frontend" ]
    then
        echo -e "\e[32m[INFO]: Cloning Frontend Respository.\e[0m"
        git clone https://github.com/DesterLib/Frontend >> /dev/null 2>&1
    else
        echo -e "\e[33m[WARNING]: Frontend source files already exists.\e[0m"
    fi
    cd Frontend
    echo -e "\e[32m[INFO]: Installing dependencies.\e[0m"
    npm install >> /dev/null 2>&1
    echo -e "\e[32m[INFO]: Building static files.\e[0m"
    npm run build >> /dev/null 2>&1
    mv build ../
    rm -rf Frontend
    echo -e "\e[32m[INFO]: Successfully genereated the build files.\e[0m"
else
    echo -e "\e[33m[WARNING]: build files already exists.\e[0m"
fi