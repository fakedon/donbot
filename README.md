# donbot
Make life automatically.

## How to install
Python 3.5+ required

`git clone https://github.com/fakedon/donbot.git`

`pip install -r requirements.txt`

download geckodriver from https://github.com/mozilla/geckodriver/releases and install

if you want use telegram notification, set telegram config at utils/telegram.cfg, you can find help info at https://github.com/LonamiWebs/Telethon

## Install with Docker
1. Install docker
2. git clone https://github.com/fakedon/donbot.git
3. modify the config files under ./cfg/
3. cd donbot && docker build -t donbot .
4. docker run -it --shm-size=1024m -p 5910:5901 -p 6910:6901 -e VNC_PW=yourpassword donbot bash

More info about this docker, read [https://github.com/ConSol/docker-headless-vnc-container](https://github.com/ConSol/docker-headless-vnc-container)

## How to use
`python run.py OPTIONS`
### Options
```
-t --task empty          if you set this option, this will just run an empty firefox instance

# you can use yes y true t or 1 for YES, and no n false f or 0 for NO.

Ameb
# Run am autoview and eb autoview in one firefox
-c --config default.cfg#2
-b --cron YES or NO      if you use linux cron function to control python run.py OPTIONS, choose YES, Default no
-d --duration INT        time to restart firefox, Default random time between 2 and 4 hours
-w --wait INT            time to check run status, Default 180

Am_emu
# Run am manual view
-c --config default.cfg#1
-d --duration INT        time to restart next time view, default value is random time between 3 and 4 hours
-m --max_click INT       max clicks per time, Default 999, if you set max_click=-1, random int between 30 and 50 will be choosed every time
-e --skip svf            skip which view mod, s for website, v for youtube, f for facebook, if no facebook account info setted in the config, facebook will skipped whether you set f or not
-q --close YES or NO     whether close firefox when this time view finished, Default False
-p --cashout YES or NO   auto request payment or not, Default True

Eb_emu
# Check eb mail
-c --config default.cfg#3
-s --solo YES or NO      whether this task run with other tasks in one firefox, Default True
-b --cron YES or NO      if you use linux cron function to control python run.py OPTIONS, choose YES, Default False
-d --duration INT        time to restart next time view, Defalt 24 hours

Bing
# Get Bing reward
# put the search words under dir mess/bingkeywords, one keyword per line
-c --config default.cfg#5
-q --close YES or NO     whether close firefox when this time view finished, Default False
```

### Bash
```
cat > run.sh << 'EOF'
#!/bin/sh
screen -dmS task1 python run.py -c 1
screen -dmS task2 python run.py -c default.cfg#2 -q 1
screen -dmS task3 python run.py -c default.cfg#3
screen -dmS task4 python run.py -c bing.cfg#1

EOF
chmod +x run.sh
./run.sh
```
