#!bash -x
timestamp=`date +%s%N`
numproc=3
cat - | openssl base64 -d  | openssl aes-256-cbc -d -k "${KEY}" -out config.xml
# for debug env
python -B main.pyc