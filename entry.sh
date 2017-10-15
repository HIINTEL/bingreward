#!bash -x
timestamp=`date +%s%N`
cat - | openssl base64 -d  | openssl aes-256-cbc -d -k "${KEY}" -out config.xml
# for debug env
echo "started"
python ./main.pyc
#cPickle.PicklingError: Can't pickle <type 'function'>: attribute lookup __builtin__.function failed
#python ./mpmain.pyc 1
echo "submitted"