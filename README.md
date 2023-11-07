# real-time-number-plate-recognition-anpr

## execution

### setting up producer

- Go to [AWS](https://aws.amazon.com/) and login.
- Go to Kinesis Video Streams and create a video stream.
- Go to EC2 and launch a t2.small instance.
- SSH into the EC2 instance.
- Execute the following commands in the EC2 instance:

      sudo apt update

      git clone https://github.com/awslabs/amazon-kinesis-video-streams-producer-sdk-cpp.git

      mkdir -p amazon-kinesis-video-streams-producer-sdk-cpp/build

      cd amazon-kinesis-video-streams-producer-sdk-cpp/build

      sudo apt-get install libssl-dev libcurl4-openssl-dev liblog4cplus-dev libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev gstreamer1.0-plugins-base-apps gstreamer1.0-plugins-bad gstreamer1.0-plugins-good gstreamer1.0-plugins-ugly gstreamer1.0-tools

      sudo apt  install cmake

      sudo apt-get install g++

      sudo apt-get install build-essential
  
      cmake -DBUILD_GSTREAMER_PLUGIN=TRUE ..

      cmake .. -DBUILD_DEPENDENCIES=OFF -DBUILD_GSTREAMER_PLUGIN=ON

      make

      sudo make install

      cd ..

      export GST_PLUGIN_PATH=`pwd`/build

      export LD_LIBRARY_PATH=`pwd`/open-source/local/lib

  

      

### setting up consumer #1: object detection and tracking

### setting up consumer #2: visualization

