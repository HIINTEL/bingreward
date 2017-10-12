FROM kenney/bingreward:latest
# Following label schema convention described at http://label-schema.org/rc1/
LABEL \
  org.label-schema.schema-version="2.0" \
  org.label-schema.name="BingRewards" \
  org.label-schema.vcs-url="http://github.com/sealemar/BingRewards" \
  org.label-schema.description="an automated point earning script that works with Bing.com to earn points to redeemed giftcards." \
  org.label-schema.docker.cmd="faas-cli deploy -f compose.yml -replace=true" \
  org.label-schema.docker.maintainer="Kenney He <kenneyhe@gmail.com>"


WORKDIR /bin

# can pass http_proxy
EXPOSE 8080
ENV http_proxy      ""
ENV https_proxy     ""

ADD . /bin/test/
RUN python -m compileall /bin/
RUN find /bin/test ! -name \*pyc -exec rm {} \;
ADD requirements.txt /bin/
ADD https://raw.githubusercontent.com/kenneyhe/BingRewards/master/config.xml.dist /bin/config.xml
RUN pip install -r requirements.txt
