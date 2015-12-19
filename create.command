#!/bin/sh

cd $(dirname $0)

# do we have python3?
if [ 'XX' == 'XX'$(which python3) ]; then
	echo "-->  No python3"
	
	# do we have homebrew?
	if [ 'XX' == 'XX'$(which brew) ]; then
		echo "-->  No Homebrew, installing"
		ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
	fi
	
	echo "-->  Installing python3"
	brew install python3
fi

# run python script
python3 parse.py

echo
read -p "Press Return to Close"
