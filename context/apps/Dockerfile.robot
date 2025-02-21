FROM ras_base:ras_local AS builder

RUN apt-get install lsb-release wget gnupg curl -y
RUN wget https://packages.osrfoundation.org/gazebo.gpg -O /usr/share/keyrings/pkgs-osrf-archive-keyring.gpg
RUN echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/pkgs-osrf-archive-keyring.gpg] http://packages.osrfoundation.org/gazebo/ubuntu-stable $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/gazebo-stable.list > /dev/null
RUN apt-get update
RUN apt-get install -y ignition-fortress

RUN pip install awsiotsdk

RUN mkdir -p /ras_robot_app

RUN apt update && apt install -y inetutils-ping
RUN apt install wget unzip -y
RUN pip install xArm-Python-SDK

USER ras
RUN python3 -m pip install flask pyftpdlib paho-mqtt opencv-contrib-python==4.7.0.72 numpy==1.21.5
USER root

RUN apt install software-properties-common -y && \ 
    apt-add-repository ppa:mosquitto-dev/mosquitto-ppa -y && \
    apt-get update &&  apt install mosquitto -y

RUN  apt install ros-humble-rclpy-message-converter -y 

RUN echo "source /ras_robot_app/scripts/env.sh" >> /etc/bash.bashrc

CMD ["sleep", "infinity"]
