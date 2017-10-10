#!bash -x
timestamp=`date +%s%N`
numproc=3
cat - > ./$timestamp.xml
cat ./$timestamp.xml
#touch config.xml
#python main.pyc -v -f config.xml
python main.pyc -v -f $timestamp.xml