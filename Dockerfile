FROM nishidayuya/docker-vagrant-ubuntu:16.04
# Following label schema convention described at http://label-schema.org/rc1/
LABEL \
    org.label-schema.schema-version="1.0" \
    org.label-schema.name="BingRewards" \
    org.label-schema.vcs-url="http://github.com/sealemar/BingRewards" \
    org.label-schema.description="BingRewards is an automated point earning script that works with Bing.com to earn points that can be redeemed for giftcards." \
    org.label-schema.docker.cmd="docker run -it --rm -v ${PWD}/config.xml:/usr/src/app/config.xml kenney/bingreward  " \
    org.label-schema.docker.maintainer="Kenney He <kenneyhe@gmail.com>"

RUN apt-get update
RUN apt-get upgrade -y
RUN apt-get install -y python-pip
RUN pip install --upgrade pip
COPY . /usr/src/app
RUN find . -iname \*pyc -exec rm {} \;
WORKDIR /usr/src/app
RUN cp config.xml.dist config.xml
RUN chmod og-r config.xml
RUN pip install -r requirements.txt

CMD ["python", "mpmain.py", "3"]
