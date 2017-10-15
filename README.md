# BingRewards

## Coverage Badge, Container Badge
[![Coverage Status](https://coveralls.io/repos/github/kenneyhe/BingRewards/badge.svg?branch=master)](https://coveralls.io/github/kenneyhe/BingRewards?branch=master) [![Codeship Status for kenneyhe/BingRewards](https://app.codeship.com/projects/b7d1b790-7558-0135-7442-16f51719268d/status?branch=master)](https://app.codeship.com/projects/244218)

## About
BingRewards is an automated point earning script that works with Bing.com to earn points that can be redeemed for giftcards.

## Requirements
Python 2.7+

## Running The Script
Copy *config.xml.dist* to *config.xml*  
Enter accounts in `<accounts>` section.  
Ensure `<events>` match accounts or are commented out.

Linux/Mac
```bash
$ cd path/to/bingrewards
$ ./main.py
```
Windows
```
> cd path\to\bingrewards
> python main.py
```
## Config

### General
betweenQueriesInterval: Number of seconds between queries  
betweenQueriesSalt: Random number of seconds added between queries  
betweenAccountsInterval Number of seconds between accounts  
betweenAccountsSalt Random number of seconds added between accounds  
addSearchesDesktop Number of extra desktop searches  
addSearchesDesktopSalt Random number of added desktop searches  
addSearchesMobile Number of extra mobile searches  
addSearchesMobileSalt Random number of added mobile searches  

### Accounts
You can have as many account tags as you need.  
**Note**: User-Agent fields are optional. If omitted a random User-Agent will be selected. Use caution when entering a custom User-Agent. If User-Agent is not associated with a common browser Bing! might flag you as a bot.  
**Note**: Two-Factor Authentication (2FA) is not supported.
```xml

<account type="Live" disabled="(true|false)">
    <login>email@example.org</login>
    <password>passwordhere</password>
    <ua_desktop><![CDATA[YOUR DESKTOP USER AGENT HERE]]></ua_desktop>
    <ua_mobile><![CDATA[YOUR MOBILE USER AGENT HERE]]></ua_mobile>
</account>
```

### Query Generators
- bing
- googleTrends
- wikipedia

### Events
onError: Defines what the script should do when an error occurs durring processing an account.  
onComplete: Defines how the script should behave when it completes processing an account.  
onScriptComplete: A special event which occurs only once when the script finishes executing.  
onScriptFailure: A special event which occurs only once and if the script fails with exception some time after successfully loading the config.

## Automating
FAAS support
```python

# openfaas deploying swarm and server at http://localhost:8080
docker swarm init
git clone https://github.com/openfaas/faas && \
    cd faas && \
    git checkout 0.6.5 && \
    ./deploy_stack.sh

# generate image and deploy
docker build -t kenney/bingreward .

faas-cli deploy -f compose.yml -replace=true

# wait less than a minute for port to be open
docker service ls

# if not HTTPS
openssl aes-256-cbc -e -in config.xml -k "${KEY}" | openssl enc -base64 > ~/config.enc
curl http://localhost:8080/function/bing --data-binary @$HOME/config.enc > output.txt

# test containers
``` bash
# send it to codeship
jet steps
```

# create only artifacts
python -m compileall .

# removal steps
# function name is service name
docker service rm bing

# cleanup
rm -rf faas

## References
- For more information, including how to use this, please, take a look at my blog post:
[here](http://sealemar.blogspot.com/2012/12/bing-rewards-automation.html)
- [here](https://github.com/openfaas/faas)
- To find out how to convert Bing! Rewards points to cash, read my second post in this series:
[here](http://sealemar.blogspot.com/2013/04/bing-rewards-points-to-cash.html)
- [Bing! Rewards Automation version 2.0](http://sealemar.blogspot.com/2013/06/bing-rewards-automation-version-2.html)
- [Bing! Rewards Automation version 3.0](http://sealemar.blogspot.com/2013/10/bing-rewards-automation-version-30.html) -- _added events support - notifications and retries_
- [Configuration for Bing! Rewards Automation script](http://sealemar.blogspot.com/2013/10/configuration-for-bing-rewards.html)
- [Bing! Rewards Automation script: Unix Cron](http://sealemar.blogspot.com/2013/10/bing-rewards-automation-script-unix-cron.html)
- [Troubleshooting guide](http://sealemar.blogspot.com/2014/06/troubleshooting-bing-rewards-automation.html)
