#!/bin/sh

cd ..
cd files/
FILE=./radius_control_backend.tar.gz
while true
  do
        if test -f "$FILE"; then
                pkill python
                mv radius_control_backend backup_radius_control_backend
                if [ "$(tar -xzvf radius_control_backend.tar.gz)" ]; then
                        chmod +x ./radius_control_backend/run.sh
                        ./radius_control_backend/run.sh < "$file" || {
                                pkill python
                                rm -rf radius_control_backend
                                mv backup_radius_control_backend radius_control_backend
                                rm radius_control_backend.tar.gz
                                chmod +x ./radius_control_backend/run.sh
                                sh ./radius_control_backend/run.sh
                                echo "run python problem" > log.txt
                        }
                        rm radius_control_backend.tar.gz
                        rm -rf backup_radius_control_backend
                        echo "succeed" > log.txt
                else
                        pkill python
                        rm -rf radius_control_backend
                        mv backup_radius_control_backend radius_control_backend
                        rm radius_control_backend.tar.gz
                        chmod +x ./radius_control_backend/run.sh
                        sh ./radius_control_backend/run.sh
                        echo "untar problem"  > log.txt
                fi