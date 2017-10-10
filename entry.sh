#!bash -x
timestamp=`date +%s%N`
numproc=3
cat - > ./$timestamp.xml
# use secret key to descript stdin
openssl aes-256-cbc -d -in ./$timestamp.xml -k "${KEY}" > config.xml
python main.pyc -v -f config.xml