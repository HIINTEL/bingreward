FROM python:2.7.14-alpine
# Following label schema convention described at http://label-schema.org/rc1/
LABEL \
  org.label-schema.schema-version="2.0" \
  org.label-schema.name="BingRewards" \
  org.label-schema.vcs-url="http://github.com/sealemar/BingRewards" \
  org.label-schema.description="an automated point earning script that works with Bing.com to earn points to redeemed giftcards." \
  org.label-schema.docker.cmd="faas-cli deploy -f compose.yml -replace=true" \
  org.label-schema.docker.maintainer="Kenney He <kenneyhe@gmail.com>"

RUN apk --no-cache add bash mailx openssl

WORKDIR /bin

# can pass http_proxy
EXPOSE 8080
ENV http_proxy      ""
ENV https_proxy     ""
ADD requirements.txt /bin/
RUN pip install -r requirements.txt
COPY *py   /bin/
ADD pkg/    /bin/pkg/
ADD pkg/queryGenerators/ /bin/pkg/queryGenerators/
RUN python -m compileall /bin
RUN find /bin/ ! -name \*pyc -exec rm {} \;
COPY entry.sh   /bin
ADD https://github.com/openfaas/faas/releases/download/v0.5-alpha/fwatchdog /usr/bin
RUN chmod +x /usr/bin/fwatchdog /bin/entry.sh
ENV fprocess="/bin/entry.sh"
CMD ["fwatchdog"]
