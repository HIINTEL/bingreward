#!/usr/bin/env bash
# ./onScriptFailure [mail] "error message"

logFile="`dirname $0`/log.log"

# if the log file doens't exist, or is empty -> print something to it
if [ ! -s "$logFile" ] ; then
    echo "Empty log" > "$logFile"
fi

if [ $# -lt 2 -o "$1" != "mail" ] ; then
    echo
    echo "Full log:"
    echo "---------"

    echo "onScriptFailure: $1" >> "$logFile"

    cat "$logFile"

else
    echo "onScriptFailure: $2" >> "$logFile"

    source "${LOCAL_CONFIG_DIR}/mailx.config.sh"

    SUBJECT="'$HOSTNAME' - Alert! BingRewards::onScriptFailure"

    env MAILRC=/dev/null from="${SENDER}" smtp-auth-user="${SENDER}" smtp-auth-password="${SENDER_PASSWORD}" \
    mailx -n \
        -S smtp-use-starttls \
        -S smtp-auth=login \
        -S smtp="$SMTP_SERVER" \
        -s "${SUBJECT}" "${RECEIVER}" < "$logFile"
fi

rm "$logFile"
