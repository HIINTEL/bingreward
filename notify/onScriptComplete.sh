#!/usr/bin/env bash
# ./onScriptComplete [mail]

logFile="`dirname $0`/log.log"

# do nothing if there is no log file
if [ ! -s "$logFile" ] ; then
    if [ -f "$logFile" ] ; then
        rm "$logFile"
    fi

    exit 0
fi

if [ $# -eq 0 -o "$1" != "mail" ] ; then
    echo
    echo "Full log:"
    echo "---------"

    cat "$logFile"
else
    source "${LOCAL_CONFIG_DIR}/mailx.config.sh"

    SUBJECT="'$HOSTNAME' - Notify. BingRewards::onScriptComplete"

    env MAILRC=/dev/null from="${SENDER}" smtp-auth-user="${SENDER}" smtp-auth-password="${SENDER_PASSWORD}" \
    mailx -n \
        -S smtp-use-starttls \
        -S smtp-auth=login \
        -S smtp="$SMTP_SERVER" \
        -s "${SUBJECT}" "${RECEIVER}" < "$logFile"
fi

rm "$logFile"
