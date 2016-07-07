#!/usr/bin/env bash
MOUNTER_UID=1000 # Change your mounter UID to be appropriate.
MOUNTER_PSK="a" # Change your PSK for the HMAC.

sudo python mounter.py $MOUNTER_PSK $MOUNTER_UID