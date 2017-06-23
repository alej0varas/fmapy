===================================
 (BETA) Free Music Archive Player
===================================

THANKS to http://freemusicarchive.org/ for the music!

Only tested on ubuntu 15.10 XD
Requires libsmpeg0: apt install libsmpeg0

Run
===

You need Python3.
Install the requirements and run.
::

   $ pip install -r requirements.txt

::

   $ FMA_API_KEY=<YOUR FMA KEY> python3 cli.py


Get your key from https://freemusicarchive.org/api/agreement (yes, you need an account in FMA).


Usage
::

   r - play random genre :sunglasses:
   g - choose gender(parent)
   s - search gender(all)
   n - next
   f - favourite song
   h - hate song
   p - pause/unpause
   i - toggle: play all/new (default is to play all)
   o - toggle: all/instrumental (default is to play all)
   q - quit
